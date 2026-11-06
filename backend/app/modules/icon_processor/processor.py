import io
import os
from pathlib import Path
from typing import Tuple, Union
from PIL import Image, ImageDraw, ImageOps

# Prevent decompression bomb DOS attacks
Image.MAX_IMAGE_PIXELS = 10_000_000

DENSITY_SIZES = {
    "mipmap-mdpi": 48,
    "mipmap-hdpi": 72,
    "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144,
    "mipmap-xxxhdpi": 192
}

ADAPTIVE_FG_SIZES = {
    "mipmap-mdpi": 108,
    "mipmap-hdpi": 162,
    "mipmap-xhdpi": 216,
    "mipmap-xxhdpi": 324,
    "mipmap-xxxhdpi": 432
}


class IconValidationError(ValueError):
    pass


def validate_and_load_icon(icon_data: Union[bytes, str, Path], max_size_mb: int = 5) -> Image.Image:
    """
    Validates and decodes the icon using Pillow.
    - Limits byte size
    - Caps pixel count
    - Verifies format is PNG, JPEG, or WEBP
    - Verifies dimensions are at least 192x192
    - Enforces 1:1 aspect ratio
    """
    if isinstance(icon_data, (str, Path)):
        p = Path(icon_data)
        if not p.is_file():
            raise IconValidationError(f"Icon file not found: {icon_data}")
        file_size = p.stat().st_size
        if file_size > max_size_mb * 1024 * 1024:
            raise IconValidationError(f"Icon file size exceeds {max_size_mb}MB limit ({file_size} bytes).")
        with open(p, "rb") as f:
            raw_bytes = f.read()
    else:
        raw_bytes = icon_data
        if len(raw_bytes) > max_size_mb * 1024 * 1024:
            raise IconValidationError(f"Icon file size exceeds {max_size_mb}MB limit ({len(raw_bytes)} bytes).")

    try:
        img = Image.open(io.BytesIO(raw_bytes))
        img.verify()  # verify integrity
        # Re-open after verify() as recommended by Pillow documentation
        img = Image.open(io.BytesIO(raw_bytes))
    except Exception as e:
        raise IconValidationError(f"Invalid image file: {str(e)}")

    if img.format not in ("PNG", "JPEG", "WEBP"):
        raise IconValidationError(f"Unsupported image format: {img.format}. Allowed: PNG, JPG, WEBP.")

    width, height = img.size
    if width < 192 or height < 192:
        raise IconValidationError(f"Icon dimensions too small ({width}x{height}px). Minimum required is 192x192px.")

    # Require roughly square (within 3% tolerance)
    diff = abs(width - height)
    max_dim = max(width, height)
    if (diff / max_dim) > 0.03:
        raise IconValidationError(f"Icon must have a 1:1 square aspect ratio (received {width}x{height}px).")

    # If slightly non-square within tolerance, center-crop to exact square
    if width != height:
        target_size = min(width, height)
        left = (width - target_size) // 2
        top = (height - target_size) // 2
        img = img.crop((left, top, left + target_size, top + target_size))

    return img.convert("RGBA")


def make_round_icon(image: Image.Image, size: int) -> Image.Image:
    """Creates a circular masked icon with high-quality anti-aliasing."""
    # Supersample mask for crisp edge
    scale = 4
    high_size = size * scale
    mask = Image.new("L", (high_size, high_size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, high_size - 1, high_size - 1), fill=255)
    mask = mask.resize((size, size), Image.Resampling.LANCZOS)

    resized_img = image.resize((size, size), Image.Resampling.LANCZOS)
    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.paste(resized_img, (0, 0), mask)
    return output


def make_adaptive_foreground(image: Image.Image, canvas_size: int) -> Image.Image:
    """
    Creates an adaptive launcher foreground icon.
    Adaptive icons have a canvas of 108dp with a 72dp safe zone in the center
    (representing 66.6% of the canvas).
    """
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    # 72 / 108 = 0.6667 safe zone
    icon_dim = int(canvas_size * 0.6667)
    resized_icon = image.resize((icon_dim, icon_dim), Image.Resampling.LANCZOS)
    offset = (canvas_size - icon_dim) // 2
    canvas.paste(resized_icon, (offset, offset), resized_icon)
    return canvas


def process_icon_for_android(icon_data: Union[bytes, str, Path], res_dir: Path, output_dir: Path) -> Path:
    """
    Processes the icon and outputs all Android mipmap variants and the 512x512 store icon.
    Returns the path to the 512x512 store icon.
    """
    base_image = validate_and_load_icon(icon_data)
    
    # 1. Generate mipmap variants into res directory
    for density, size in DENSITY_SIZES.items():
        density_dir = res_dir / density
        density_dir.mkdir(parents=True, exist_ok=True)
        
        # Standard launcher icon
        square_icon = base_image.resize((size, size), Image.Resampling.LANCZOS)
        square_icon.save(density_dir / "ic_launcher.png", format="PNG", optimize=True)
        
        # Round launcher icon
        round_icon = make_round_icon(base_image, size)
        round_icon.save(density_dir / "ic_launcher_round.png", format="PNG", optimize=True)
        
        # Adaptive foreground icon
        fg_size = ADAPTIVE_FG_SIZES[density]
        fg_icon = make_adaptive_foreground(base_image, fg_size)
        fg_icon.save(density_dir / "ic_launcher_foreground.png", format="PNG", optimize=True)

    # 2. Generate 512x512 store icon
    output_dir.mkdir(parents=True, exist_ok=True)
    store_icon_path = output_dir / "icon-512.png"
    store_icon = base_image.resize((512, 512), Image.Resampling.LANCZOS)
    store_icon.save(store_icon_path, format="PNG", optimize=True)
    
    return store_icon_path
