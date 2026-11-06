import argparse
import secrets
import sys
import time
from pathlib import Path

from app.core.logging import setup_logging, logger
from app.modules.apk_builder.interface import BuildRequest
from app.modules.apk_builder.webview.engine import WebViewEngine
from app.modules.storage.local import LocalStorage


def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="WebToAPK WebView Engine CLI")
    parser.add_argument("--url", required=True, help="Website URL to wrap")
    parser.add_argument("--name", required=True, help="Application display name")
    parser.add_argument("--icon", required=True, help="Path to 1:1 app icon image")
    parser.add_argument("--package", default=None, help="Optional package name override (e.g. com.myshop.app)")
    parser.add_argument("--version-code", type=int, default=1, help="Android versionCode (default: 1)")
    parser.add_argument("--version-name", default="1.0.0", help="Android versionName (default: 1.0.0)")
    parser.add_argument("--out-dir", default=None, help="Directory to copy final artifacts to")

    args = parser.parse_args()

    icon_path = Path(args.icon)
    if not icon_path.exists():
        logger.error(f"Icon file not found: {args.icon}")
        sys.exit(1)

    build_id = secrets.token_urlsafe(16)
    print(f"\n=======================================================")
    print(f" WebToAPK V1 Build CLI (Build ID: {build_id})")
    print(f"=======================================================")
    print(f" URL:          {args.url}")
    print(f" App Name:     {args.name}")
    print(f" Icon:         {args.icon}")
    print(f" Package:      {args.package or '(auto-generated)'}")
    print(f" Version:      {args.version_name} (code: {args.version_code})")
    print(f"=======================================================\n")

    request = BuildRequest(
        build_id=build_id,
        website_url=args.url,
        app_name=args.name,
        icon_path=icon_path,
        package_name=args.package,
        version_code=args.version_code,
        version_name=args.version_name,
        engine="webview"
    )

    def on_progress(step: str, pct: int):
        print(f"[{pct:3d}%] Step: {step}")

    storage = LocalStorage()
    engine = WebViewEngine(storage=storage)
    
    start_time = time.time()
    result = engine.build(request, progress_callback=on_progress)
    duration = time.time() - start_time

    if result.status == "completed":
        print("\n================ BUILD SUCCESSFUL ================")
        print(f" Total time:     {duration:.2f} seconds")
        print(f" APK Path:       {result.apk_path}")
        print(f" AAB Path:       {result.aab_path}")
        print(f" Keystore Path:  {result.keystore_path}")
        print(f" Bundle ZIP:     {result.bundle_zip_path}")
        print(f" Package Name:   {result.metadata.get('package_name')}")
        print(f" SHA-256 Cert:   {result.metadata.get('sha256')}")
        print("==================================================\n")
        sys.exit(0)
    else:
        print("\n================ BUILD FAILED ================")
        print(f" Error: {result.error}")
        print("==============================================\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

