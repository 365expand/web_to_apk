import os
import re
import secrets
import string
import subprocess
from pathlib import Path
from typing import Dict, Tuple

from app.core.config import settings
from app.core.logging import logger


def generate_strong_password(length: int = 32) -> str:
    """Generates a cryptographically strong random password for keystores (alphanumeric for CLI safety)."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_keystore(
    keystore_path: Path,
    alias: str,
    password: str,
    dname: str = "CN=WebToAPK, OU=Mobile, O=App, C=US",
    validity_days: int = 10000
) -> None:
    """
    Generates a new Android signing keystore using keytool.
    RSA 2048-bit key, 10000 days validity.
    """
    keytool_bin = settings.resolve_keytool()
    
    cmd = [
        keytool_bin,
        "-genkeypair",
        "-v",
        "-keystore", str(keystore_path),
        "-alias", alias,
        "-keyalg", "RSA",
        "-keysize", "2048",
        "-validity", str(validity_days),
        "-storepass", password,
        "-keypass", password,
        "-dname", dname,
        "-storetype", "JKS"
    ]
    
    # We do NOT log command arguments to prevent exposing passwords
    logger.info(f"Generating new signing keystore for alias: {alias}")
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False
    )
    
    if result.returncode != 0:
        # Scrub password if it accidentally leaked into stderr
        safe_stderr = result.stderr.replace(password, "********")
        raise RuntimeError(f"Failed to generate keystore: {safe_stderr}")


def get_certificate_fingerprints(keystore_path: Path, alias: str, password: str) -> Dict[str, str]:
    """
    Extracts SHA-1 and SHA-256 certificate fingerprints using keytool -list -v.
    """
    keytool_bin = settings.resolve_keytool()
    cmd = [
        keytool_bin,
        "-list",
        "-v",
        "-keystore", str(keystore_path),
        "-alias", alias,
        "-storepass", password
    ]
    
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False
    )
    
    if result.returncode != 0:
        safe_err = result.stderr.replace(password, "********")
        raise RuntimeError(f"Failed to read certificate fingerprints: {safe_err}")

    output = result.stdout
    sha1_match = re.search(r"SHA1:\s*([A-Fa-f0-9:]+)", output)
    sha256_match = re.search(r"SHA256:\s*([A-Fa-f0-9:]+)", output)
    
    sha1 = sha1_match.group(1).strip() if sha1_match else "UNKNOWN"
    sha256 = sha256_match.group(1).strip() if sha256_match else "UNKNOWN"
    
    return {
        "sha1": sha1,
        "sha256": sha256
    }


def format_keystore_info_txt(
    package_name: str,
    alias: str,
    store_password: str,
    key_password: str,
    sha1: str,
    sha256: str,
    validity_days: int = 10000
) -> str:
    """
    Formats the keystore-info.txt file included in the bundle.
    """
    return f"""================================================================================
ANDROID KEYSTORE & SIGNING CREDENTIALS
================================================================================
Package Name:    {package_name}
Key Alias:       {alias}
Store Password:  {store_password}
Key Password:    {key_password}
Validity:        {validity_days} days
Certificate SHA-1:
{sha1}

Certificate SHA-256:
{sha256}

================================================================================
IMPORTANT WARNING:
================================================================================
If you lose this keystore file, you will NEVER be able to update your app on 
Google Play or on users' devices. Store this file and these passwords in a safe,
permanent backup location immediately.

With Google Play App Signing, this keystore serves as your Upload Key.
================================================================================
"""
