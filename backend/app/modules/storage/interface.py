from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class StorageInterface(ABC):
    @abstractmethod
    def save_file(self, build_id: str, filename: str, src_path: Path) -> Path:
        """Stores a file for a specific build."""
        pass

    @abstractmethod
    def get_file_path(self, build_id: str, filename: str) -> Optional[Path]:
        """Gets local path to a stored file (or downloads to temp if remote)."""
        pass

    @abstractmethod
    def delete_build_files(self, build_id: str) -> None:
        """Deletes all artifacts associated with a build."""
        pass

    @abstractmethod
    def build_exists(self, build_id: str) -> bool:
        """Checks if files for a build exist."""
        pass
