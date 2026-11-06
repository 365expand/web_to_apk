import os
import shutil
import subprocess
import time
import uuid
import zipfile
from pathlib import Path
from typing import Callable, Optional
from xml.sax.saxutils import escape as xml_escape

from app.core.config import settings
from app.core.logging import logger
from app.modules.apk_builder.interface import BuildEngine, BuildRequest, BuildResult
from app.modules.apk_builder.validators import (
    generate_package_name,
    sanitize_package_name_override,
    validate_package_name,
    validate_version_code,
    validate_version_name,
)
from app.modules.icon_processor.processor import process_icon_for_android
from app.modules.signing.keystore import (
    format_keystore_info_txt,
    generate_keystore,
    generate_strong_password,
    get_certificate_fingerprints,
)
from app.modules.storage.local import LocalStorage


class WebViewEngine(BuildEngine):
    @property
    def name(self) -> str:
        return "webview"

    def __init__(self, storage: Optional[LocalStorage] = None):
        self.storage = storage or LocalStorage()
        self.template_dir = settings.TEMPLATES_DIR / "webview"

    def build(
        self,
        request: BuildRequest,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> BuildResult:
        start_time = time.time()
        build_id = request.build_id
        workspace = settings.TEMP_DIR / f"workspace_{build_id}_{uuid.uuid4().hex[:8]}"

        def update_progress(step: str, pct: int):
            if progress_callback:
                progress_callback(step, pct)

        try:
            update_progress("validating", 10)
            logger.info(f"[{build_id}] Starting build with WebView engine for URL: {request.website_url}")

            # 1. Validate / generate package name
            pkg_name = request.package_name
            if not pkg_name:
                pkg_name = generate_package_name(request.website_url)
            else:
                pkg_name = sanitize_package_name_override(pkg_name)
            
            is_valid, err_msg = validate_package_name(pkg_name)
            if not is_valid:
                raise ValueError(f"Invalid package name '{pkg_name}': {err_msg}")

            v_code = validate_version_code(request.version_code)
            v_name = validate_version_name(request.version_name)

            # 2. Setup isolated workspace
            update_progress("preparing", 20)
            if workspace.exists():
                shutil.rmtree(workspace, ignore_errors=True)
            
            # Copy template to workspace (exclude build and .gradle from root if any)
            shutil.copytree(
                self.template_dir,
                workspace,
                ignore=shutil.ignore_patterns(".gradle", "build", ".idea", "*.apk", "*.aab")
            )

            # Ensure local.properties points to ANDROID_HOME
            local_props = workspace / "local.properties"
            sdk_escaped = settings.ANDROID_HOME.replace("\\", "\\\\").replace(":", "\\:")
            local_props.write_text(f"sdk.dir={sdk_escaped}\n", encoding="utf-8")

            # 3. Process icon into template resources
            update_progress("preparing", 30)
            res_dir = workspace / "app" / "src" / "main" / "res"
            out_icon_dir = workspace / "outputs"
            out_icon_dir.mkdir(parents=True, exist_ok=True)

            icon_input = request.icon_bytes if request.icon_bytes is not None else request.icon_path
            if not icon_input:
                raise ValueError("No icon provided for APK build.")

            store_icon_path = process_icon_for_android(icon_input, res_dir, out_icon_dir)

            # 4. Generate fresh keystore per build
            update_progress("preparing", 40)
            keystore_dir = workspace / "keystore"
            keystore_dir.mkdir(parents=True, exist_ok=True)
            keystore_path = keystore_dir / "release.jks"
            key_alias = f"alias_{build_id[:8]}"
            key_password = generate_strong_password(24)

            generate_keystore(
                keystore_path=keystore_path,
                alias=key_alias,
                password=key_password
            )

            fingerprints = get_certificate_fingerprints(
                keystore_path=keystore_path,
                alias=key_alias,
                password=key_password
            )

            # 5. Execute Gradle build (both assembleRelease and bundleRelease)
            update_progress("building", 50)
            gradle_bin = "gradlew.bat" if os.name == "nt" else "./gradlew"
            gradle_executable = workspace / gradle_bin
            if not os.name == "nt":
                os.chmod(gradle_executable, 0o755)

            # XML-escape app name for Android manifest/resources
            escaped_app_name = xml_escape(request.app_name, entities={"'": "\\'", '"': '\\"'})

            # Build command args
            gradle_args = [
                str(gradle_executable),
                "assembleRelease",
                "bundleRelease",
                f"-PappName={escaped_app_name}",
                f"-PappUrl={request.website_url}",
                f"-PapplicationId={pkg_name}",
                f"-PversionCode={v_code}",
                f"-PversionName={v_name}",
                f"-PreleaseKeyStore={str(keystore_path)}",
                f"-PreleaseKeyAlias={key_alias}",
                f"-PreleaseStorePassword={key_password}",
                f"-PreleaseKeyPassword={key_password}",
                "--console=plain",
                "--stacktrace"
            ]

            env = os.environ.copy()
            if settings.JAVA_HOME:
                env["JAVA_HOME"] = settings.JAVA_HOME
            if settings.ANDROID_HOME:
                env["ANDROID_HOME"] = settings.ANDROID_HOME

            logger.info(f"[{build_id}] Running Gradle build invocation...")
            gradle_start = time.time()
            
            build_proc = subprocess.run(
                gradle_args,
                cwd=str(workspace),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=settings.BUILD_TIMEOUT_SECONDS
            )

            gradle_duration = time.time() - gradle_start
            logger.info(f"[{build_id}] Gradle completed in {gradle_duration:.2f}s with exit code {build_proc.returncode}")

            if build_proc.returncode != 0:
                # Sanitize password from logs/errors
                clean_err = build_proc.stdout + "\n" + build_proc.stderr
                clean_err = clean_err.replace(key_password, "********")
                # Grab last 25 lines of output for clean diagnostics
                tail_err = "\n".join(clean_err.strip().splitlines()[-25:])
                raise RuntimeError(f"Gradle build failed (code {build_proc.returncode}):\n{tail_err}")

            # 6. Locate and verify outputs
            update_progress("packaging", 80)
            apk_path = workspace / "app" / "build" / "outputs" / "apk" / "release" / "app-release.apk"
            aab_path = workspace / "app" / "build" / "outputs" / "bundle" / "release" / "app-release.aab"

            if not apk_path.exists():
                raise FileNotFoundError(f"Generated APK not found at {apk_path}")
            if not aab_path.exists():
                raise FileNotFoundError(f"Generated AAB not found at {aab_path}")

            # Verify APK using apksigner
            apksigner_bin = settings.resolve_apksigner()
            verify_res = subprocess.run(
                [apksigner_bin, "verify", "--verbose", str(apk_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            if verify_res.returncode != 0:
                raise RuntimeError(f"APK signature verification failed: {verify_res.stderr or verify_res.stdout}")

            # 7. Create keystore-info.txt and bundle zip
            update_progress("packaging", 90)
            keystore_info_txt = format_keystore_info_txt(
                package_name=pkg_name,
                alias=key_alias,
                store_password=key_password,
                key_password=key_password,
                sha1=fingerprints["sha1"],
                sha256=fingerprints["sha256"]
            )
            keystore_info_path = out_icon_dir / "keystore-info.txt"
            keystore_info_path.write_text(keystore_info_txt, encoding="utf-8")

            bundle_zip_path = out_icon_dir / "bundle.zip"
            with zipfile.ZipFile(bundle_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(apk_path, "app-release.apk")
                zf.write(aab_path, "app-release.aab")
                zf.write(keystore_path, "keystore.jks")
                zf.write(keystore_info_path, "keystore-info.txt")
                zf.write(store_icon_path, "icon-512.png")

            # 8. Save artifacts to persistent storage
            saved_apk = self.storage.save_file(build_id, "app-release.apk", apk_path)
            saved_aab = self.storage.save_file(build_id, "app-release.aab", aab_path)
            saved_bundle = self.storage.save_file(build_id, "bundle.zip", bundle_zip_path)
            saved_keystore = self.storage.save_file(build_id, "keystore.jks", keystore_path)
            self.storage.save_file(build_id, "keystore-info.txt", keystore_info_path)
            self.storage.save_file(build_id, "icon-512.png", store_icon_path)

            total_duration = time.time() - start_time
            update_progress("completed", 100)
            logger.info(f"[{build_id}] Build successfully completed in {total_duration:.2f}s")

            return BuildResult(
                build_id=build_id,
                engine=self.name,
                status="completed",
                apk_path=saved_apk,
                aab_path=saved_aab,
                keystore_path=saved_keystore,
                bundle_zip_path=saved_bundle,
                metadata={
                    "package_name": pkg_name,
                    "version_code": v_code,
                    "version_name": v_name,
                    "app_name": request.app_name,
                    "website_url": request.website_url,
                    "sha1": fingerprints["sha1"],
                    "sha256": fingerprints["sha256"],
                    "gradle_duration_seconds": round(gradle_duration, 2)
                },
                build_duration_seconds=round(total_duration, 2)
            )

        except Exception as e:
            total_duration = time.time() - start_time
            logger.error(f"[{build_id}] Build failed: {str(e)}", exc_info=True)
            return BuildResult(
                build_id=build_id,
                engine=self.name,
                status="failed",
                error=str(e),
                build_duration_seconds=round(total_duration, 2)
            )
        finally:
            # Clean up isolated workspace (always, also on failure)
            shutil.rmtree(workspace, ignore_errors=True)

