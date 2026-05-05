from __future__ import annotations

import os
from pathlib import Path


def is_hashem_chat_enabled() -> bool:
    value = os.getenv("HASHEM_CHAT_ENABLED", "true").strip().lower()
    return value not in {"0", "false", "no", "off"}


def get_hashem_default_role() -> str:
    role = os.getenv("HASHEM_DEFAULT_ROLE", "supervisor").strip().lower()
    return role or "supervisor"


def get_hashem_project_path() -> Path:
    configured = os.getenv("HASHEM_PROJECT_PATH", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()

    return (
        Path(__file__).resolve().parents[2]
        / "MediNote-4DS7-hashem"
        / "MediNote-4DS7-hashem"
    )
