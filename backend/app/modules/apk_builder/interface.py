from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from pydantic import BaseModel, Field


class BuildRequest(BaseModel):
    build_id: str
    website_url: str
    app_name: str
    icon_bytes: Optional[bytes] = None
    icon_path: Optional[Path] = None
    package_name: Optional[str] = None
    version_code: int = 1
    version_name: str = "1.0.0"
    engine: str = "webview"

    model_config = {"arbitrary_types_allowed": True}


class BuildResult(BaseModel):
    build_id: str
    engine: str
    status: str  # "completed" or "failed"
    apk_path: Optional[Path] = None
    aab_path: Optional[Path] = None
    keystore_path: Optional[Path] = None
    bundle_zip_path: Optional[Path] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    build_duration_seconds: float = 0.0

    model_config = {"arbitrary_types_allowed": True}


class BuildEngine(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the engine (e.g. 'webview', 'twa')."""
        pass

    @abstractmethod
    def build(
        self,
        request: BuildRequest,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> BuildResult:
        """Executes the build pipeline."""
        pass
