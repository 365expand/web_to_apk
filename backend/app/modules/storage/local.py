import shutil
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.modules.storage.interface import StorageInterface


class LocalStorage(StorageInterface):
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir) if base_dir else settings.STORAGE_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_build_dir(self, build_id: str) -> Path:
        build_dir = self.base_dir / build_id
        build_dir.mkdir(parents=True, exist_ok=True)
        return build_dir

    def save_file(self, build_id: str, filename: str, src_path: Path) -> Path:
        target_dir = self._get_build_dir(build_id)
        target_path = target_dir / filename
        shutil.copy2(src_path, target_path)
        return target_path

    def get_file_path(self, build_id: str, filename: str) -> Optional[Path]:
        target_path = self.base_dir / build_id / filename
        if target_path.exists() and target_path.is_file():
            return target_path
        return None

    def delete_build_files(self, build_id: str) -> None:
        target_dir = self.base_dir / build_id
        if target_dir.exists() and target_dir.is_dir():
            shutil.rmtree(target_dir, ignore_errors=True)

    def build_exists(self, build_id: str) -> bool:
        target_dir = self.base_dir / build_id
        return target_dir.exists() and target_dir.is_dir()
