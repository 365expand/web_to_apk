import ipaddress
import os
import socket
from pathlib import Path
from typing import List, Optional, Set
from urllib.parse import urlparse, urlunparse

from fastapi import Request
from app.core.config import settings
from app.core.logging import logger

# Cloud metadata IP (AWS, GCP, Azure, DigitalOcean, Alibaba, etc.)
CLOUD_METADATA_IP = ipaddress.ip_address("169.254.169.254")

# Carrier-Grade NAT (CGNAT) 100.64.0.0/10
CGNAT_NETWORK = ipaddress.ip_network("100.64.0.0/10")


class SecurityValidationError(ValueError):
    pass


def get_client_ip(request: Request) -> str:
    """
    Extracts the client IP address. Respects X-Forwarded-For only if TRUST_PROXY is True.
    """
    if settings.TRUST_PROXY:
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            # First IP in the comma-separated chain is the client
            client_ip = x_forwarded_for.split(",")[0].strip()
            return client_ip
    
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


def load_domain_blocklist(blocklist_path: Path) -> Set[str]:
    """Loads lowercase domains from blocklist file."""
    if not blocklist_path.exists():
        return set()
    blocked = set()
    with open(blocklist_path, "r", encoding="utf-8") as f:
        for line in f:
            clean = line.strip().lower()
            if clean and not clean.startswith("#"):
                blocked.add(clean)
    return blocked


def is_ip_blocked(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Checks if IP is private, loopback, link-local, multicast, CGNAT or cloud metadata."""
    if ip == CLOUD_METADATA_IP:
        return True
    if ip.is_loopback:
        return True
    if ip.is_private:
        return True
    if ip.is_link_local:
        return True
    if ip.is_multicast:
        return True
    if ip.is_reserved:
        return True
    if ip.is_unspecified:
        return True
    if isinstance(ip, ipaddress.IPv4Address) and ip in CGNAT_NETWORK:
        return True
    return False


def validate_and_clean_url(url_string: str) -> str:
    """
    Validates website URL against SSRF, IP literal, private networking, and blocklists.
    Returns cleaned canonical URL with credentials stripped.
    """
    if not url_string:
        raise SecurityValidationError("URL cannot be empty.")

    if len(url_string) > 2048:
        raise SecurityValidationError("URL length exceeds maximum limit of 2048 characters.")

    parsed = urlparse(url_string.strip())

    # 1. Scheme validation: only http or https
    if parsed.scheme.lower() not in ("http", "https"):
        raise SecurityValidationError("URL scheme must be http or https.")

    # 2. Port validation: only 80, 443 or default
    port = parsed.port
    if port is not None:
        if parsed.scheme.lower() == "http" and port != 80:
            raise SecurityValidationError("Non-standard ports are not allowed for HTTP (only port 80).")
        if parsed.scheme.lower() == "https" and port != 443:
            raise SecurityValidationError("Non-standard ports are not allowed for HTTPS (only port 443).")

    hostname = parsed.hostname
    if not hostname:
        raise SecurityValidationError("URL must contain a valid domain name.")

    hostname_clean = hostname.lower().strip()

    # 3. Reject localhost and local development domains
    if hostname_clean in ("localhost", "127.0.0.1", "::1"):
        raise SecurityValidationError("Access to localhost is prohibited.")

    if hostname_clean.endswith((".local", ".localhost", ".internal", ".lan", ".test", ".invalid", ".onion")):
        raise SecurityValidationError("Access to internal, local, or test domains is prohibited.")

    # 4. Reject IP literals directly in the hostname (e.g. http://192.168.1.1)
    is_literal = False
    try:
        literal_ip = ipaddress.ip_address(hostname_clean)
        is_literal = True
    except ValueError:
        pass

    if is_literal:
        raise SecurityValidationError(f"Direct IP addresses ({hostname_clean}) are prohibited. Provide a valid domain name.")

    # 5. Check domain blocklist
    blocked_domains = load_domain_blocklist(settings.BLOCKLIST_PATH)
    for blocked in blocked_domains:
        if hostname_clean == blocked or hostname_clean.endswith(f".{blocked}"):
            raise SecurityValidationError(
                f"The domain '{hostname_clean}' is blocked due to security or brand abuse policies."
            )

    # 6. DNS resolution check (resolve all addresses and verify none are private or restricted)
    try:
        addr_info = socket.getaddrinfo(hostname_clean, None)
    except socket.gaierror as e:
        raise SecurityValidationError(f"Unable to resolve domain '{hostname_clean}': {e.strerror}")

    resolved_ips: List[ipaddress.IPv4Address | ipaddress.IPv6Address] = []
    for entry in addr_info:
        sockaddr = entry[4]
        ip_str = sockaddr[0]
        try:
            ip_obj = ipaddress.ip_address(ip_str)
            resolved_ips.append(ip_obj)
        except ValueError:
            continue

    if not resolved_ips:
        raise SecurityValidationError(f"Could not resolve any valid IP addresses for '{hostname_clean}'.")

    for ip in resolved_ips:
        if is_ip_blocked(ip):
            logger.warning(f"SSRF blocked: Domain {hostname_clean} resolved to restricted IP: {ip}")
            raise SecurityValidationError(
                f"Domain resolves to a restricted internal or private IP address ({ip}). Access denied."
            )

    # 7. Strip credentials (username / password) from URL
    netloc_clean = hostname_clean
    if port is not None and ((parsed.scheme.lower() == "http" and port != 80) or (parsed.scheme.lower() == "https" and port != 443)):
        netloc_clean = f"{hostname_clean}:{port}"

    clean_parsed = parsed._replace(netloc=netloc_clean)
    return urlunparse(clean_parsed)
