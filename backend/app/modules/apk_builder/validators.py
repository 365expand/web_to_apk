import re
from typing import Optional, Tuple
from urllib.parse import urlparse

JAVA_KEYWORDS = {
    "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
    "class", "const", "continue", "default", "do", "double", "else", "enum",
    "extends", "final", "finally", "float", "for", "goto", "if", "implements",
    "import", "instanceof", "int", "interface", "long", "native", "new",
    "package", "private", "protected", "public", "return", "short", "static",
    "strictfp", "super", "switch", "synchronized", "this", "throw", "throws",
    "transient", "try", "void", "volatile", "while",
    # Kotlin keywords
    "as", "fun", "in", "is", "object", "typealias", "val", "var", "when",
    "by", "constructor", "delegate", "dynamic", "field", "file", "init",
    "param", "property", "receiver", "setparam", "where"
}


def generate_package_name(url: str) -> str:
    """
    Auto-generate package name from website URL.
    e.g. 'https://www.my-shop.com' -> 'com.myshop.app'
    """
    parsed = urlparse(url)
    host = parsed.netloc or parsed.path
    # Strip port if present
    if ":" in host:
        host = host.split(":")[0]
    
    host = host.lower().strip()
    if host.startswith("www."):
        host = host[4:]
    
    raw_segments = [s for s in host.split(".") if s]
    if not raw_segments:
        return "com.webtoapk.app"

    # Reverse segments (e.g. my-shop.com -> com.my-shop)
    reversed_segments = list(reversed(raw_segments))
    
    sanitized_segments = []
    for seg in reversed_segments:
        # Strip all invalid characters
        clean = re.sub(r"[^a-z0-9_]", "", seg)
        if not clean:
            clean = "pkg"
        # If segment starts with digit, prefix with 'p'
        if clean[0].isdigit():
            clean = f"p{clean}"
        # If segment is a reserved keyword, prefix 'pkg_'
        if clean in JAVA_KEYWORDS:
            clean = f"pkg_{clean}"
        sanitized_segments.append(clean)
    
    # Append .app unless the last segment already is app
    if sanitized_segments[-1] != "app":
        sanitized_segments.append("app")
        
    pkg = ".".join(sanitized_segments)
    
    # Ensure at least 2 segments
    if len(sanitized_segments) < 2:
        pkg = f"com.{pkg}"
        
    # Blocked prefix protection
    if pkg.startswith("com.example") or pkg.startswith("com.android"):
        pkg = f"app.{pkg}"
        
    return pkg[:150]


def validate_package_name(package_name: str) -> Tuple[bool, Optional[str]]:
    """
    Validates Android package name according to Android specification:
    - Lowercase only
    - >= 2 segments
    - Each segment matches [a-z][a-z0-9_]*
    - <= 150 characters
    - Cannot use com.example.* or com.android.*
    - Segments cannot be Java/Kotlin keywords
    """
    if not package_name:
        return False, "Package name cannot be empty."
    
    if len(package_name) > 150:
        return False, "Package name cannot exceed 150 characters."
        
    if package_name != package_name.lower():
        return False, "Package name must be completely lowercase."
        
    if package_name.startswith("com.example.") or package_name == "com.example":
        return False, "Package name cannot use the 'com.example' namespace."
        
    if package_name.startswith("com.android.") or package_name == "com.android":
        return False, "Package name cannot use the 'com.android' namespace."

    segments = package_name.split(".")
    if len(segments) < 2:
        return False, "Package name must contain at least two segments (e.g., com.myshop.app)."
        
    segment_pattern = re.compile(r"^[a-z][a-z0-9_]*$")
    for seg in segments:
        if not seg:
            return False, "Package name contains an empty segment."
        if not segment_pattern.match(seg):
            return False, (
                f"Invalid segment '{seg}': Each segment must start with a letter "
                "and contain only lowercase letters, digits, or underscores."
            )
        if seg in JAVA_KEYWORDS:
            return False, f"Segment '{seg}' is a reserved Java/Kotlin keyword."
            
    return True, None


def validate_version_code(version_code: Optional[int]) -> int:
    if version_code is None:
        return 1
    if not isinstance(version_code, int) or version_code < 1:
        raise ValueError("Version code must be an integer greater than or equal to 1.")
    return version_code


def validate_version_name(version_name: Optional[str]) -> str:
    if not version_name:
        return "1.0.0"
    v_clean = version_name.strip()
    if not v_clean or len(v_clean) > 32:
        raise ValueError("Version name must be between 1 and 32 characters.")
    if not re.match(r"^[a-zA-Z0-9.\-_+]+$", v_clean):
        raise ValueError("Version name contains invalid characters.")
    return v_clean
