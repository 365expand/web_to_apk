import io
from pathlib import Path
import pytest
from PIL import Image

from app.modules.apk_builder.validators import (
    generate_package_name,
    sanitize_package_name_override,
    validate_package_name,
    validate_version_code,
    validate_version_name,
)
from app.modules.icon_processor.processor import (
    IconValidationError,
    process_icon_for_android,
    validate_and_load_icon,
)


def test_package_name_generator():
    assert generate_package_name("https://www.my-shop.com") == "com.myshop.app"
    assert generate_package_name("https://sub.store.example.org/path") == "org.example.store.sub.app"
    # Starting with digit
    assert generate_package_name("https://360view.com") == "com.p360view.app"
    assert generate_package_name("https://365expand.com") == "com.p365expand.app"
    # Reserved Java keyword
    assert generate_package_name("https://int.com") == "com.pkg_int.app"


def test_sanitize_package_name_override():
    # User entered domain starting with digits
    assert sanitize_package_name_override("com.365expand.app") == "com.p365expand.app"
    # User entered keyword segment
    assert sanitize_package_name_override("com.class.app") == "com.pkg_class.app"
    # Valid untouched
    assert sanitize_package_name_override("com.myshop.app") == "com.myshop.app"


def test_package_name_validator():
    # Valid
    ok, err = validate_package_name("com.myshop.app")
    assert ok is True and err is None

    # Invalid uppercase
    ok, err = validate_package_name("com.MyShop.app")
    assert ok is False and "lowercase" in err

    # Too short (< 2 segments)
    ok, err = validate_package_name("myshop")
    assert ok is False and "at least two segments" in err

    # Blocked prefix
    ok, err = validate_package_name("com.example.app")
    assert ok is False and "com.example" in err

    ok, err = validate_package_name("com.android.app")
    assert ok is False and "com.android" in err

    # Segment starting with digit or invalid char
    ok, err = validate_package_name("com.1shop.app")
    assert ok is False

    # Reserved keyword as segment
    ok, err = validate_package_name("com.class.app")
    assert ok is False and "reserved" in err


def test_version_validators():
    assert validate_version_code(1) == 1
    assert validate_version_code(15) == 15
    with pytest.raises(ValueError):
        validate_version_code(0)
    with pytest.raises(ValueError):
        validate_version_code(-5)

    assert validate_version_name("1.0.0") == "1.0.0"
    assert validate_version_name("2.5.1-beta") == "2.5.1-beta"
    with pytest.raises(ValueError):
        validate_version_name("invalid name with spaces!")


def test_icon_processor_validation(tmp_path):
    # 1. Valid 256x256 square PNG
    img = Image.new("RGBA", (256, 256), (33, 150, 243, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    valid_bytes = buf.getvalue()

    loaded = validate_and_load_icon(valid_bytes)
    assert loaded.size == (256, 256)

    # 2. Reject dimensions < 192px
    small_img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
    buf = io.BytesIO()
    small_img.save(buf, format="PNG")
    with pytest.raises(IconValidationError, match="too small"):
        validate_and_load_icon(buf.getvalue())

    # 3. Reject non-square (aspect ratio != 1:1)
    non_square = Image.new("RGBA", (400, 200), (0, 255, 0, 255))
    buf = io.BytesIO()
    non_square.save(buf, format="PNG")
    with pytest.raises(IconValidationError, match="1:1 square aspect ratio"):
        validate_and_load_icon(buf.getvalue())

    # 4. Generate Android mipmap density variants & 512x512 store icon
    res_dir = tmp_path / "res"
    out_dir = tmp_path / "out"
    store_icon = process_icon_for_android(valid_bytes, res_dir, out_dir)

    assert store_icon.exists()
    assert Image.open(store_icon).size == (512, 512)

    # Verify mipmap directories
    densities = ["mipmap-mdpi", "mipmap-hdpi", "mipmap-xhdpi", "mipmap-xxhdpi", "mipmap-xxxhdpi"]
    for d in densities:
        d_path = res_dir / d
        assert (d_path / "ic_launcher.png").exists()
        assert (d_path / "ic_launcher_round.png").exists()
        assert (d_path / "ic_launcher_foreground.png").exists()

