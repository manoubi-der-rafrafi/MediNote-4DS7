from __future__ import annotations

import importlib.util
import sys
from functools import lru_cache
from pathlib import Path
from types import ModuleType

from .config import get_hashem_project_path


class HashemModuleLoadError(RuntimeError):
    pass


def _load_module(module_name: str, module_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise HashemModuleLoadError(
            f"Impossible de charger le module Hashem depuis {module_path}."
        )

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def load_hashem_orchestrator_module() -> ModuleType:
    project_path = get_hashem_project_path()
    orchestrator_path = project_path / "orchestrator.py"
    if not orchestrator_path.exists():
        raise HashemModuleLoadError(
            f"Le fichier Hashem est introuvable: {orchestrator_path}"
        )

    return _load_module("hashem_orchestrator_bridge", orchestrator_path)
