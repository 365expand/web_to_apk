from typing import Dict, List, Optional
from app.core.config import settings
from app.modules.apk_builder.interface import BuildEngine


class EngineManager:
    def __init__(self):
        self._engines: Dict[str, BuildEngine] = {}

    def register(self, engine: BuildEngine) -> None:
        self._engines[engine.name.lower()] = engine

    def get_engine(self, name: Optional[str] = None) -> BuildEngine:
        target = (name or settings.DEFAULT_BUILD_ENGINE).lower()
        if target not in settings.enabled_engines_list:
            raise ValueError(f"Build engine '{target}' is disabled.")
        if target not in self._engines:
            raise ValueError(f"Build engine '{target}' is not registered.")
        return self._engines[target]

    def list_enabled_engines(self) -> List[str]:
        return [name for name in self._engines.keys() if name in settings.enabled_engines_list]


engine_manager = EngineManager()
