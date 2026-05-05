from __future__ import annotations

import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
MUSIC_GENERATION_DIR = BASE_DIR / "music_generation" / "music_generation"


def main() -> int:
    if str(MUSIC_GENERATION_DIR) not in sys.path:
        sys.path.insert(0, str(MUSIC_GENERATION_DIR))

    try:
        from src.musicgen_generator import DEFAULT_MODEL_NAME
    except Exception as exc:
        print(f"[PRELOAD] status=failed reason=module_import_error details={exc}")
        return 1

    try:
        from transformers import AutoProcessor, MusicgenForConditionalGeneration
    except Exception as exc:
        print(
            "[PRELOAD] status=failed reason=missing_dependencies "
            f"details={exc}"
        )
        print("Installez d'abord les dependances: pip install -r requirements.txt")
        return 1

    print(f"[PRELOAD] status=start model={DEFAULT_MODEL_NAME}")
    try:
        AutoProcessor.from_pretrained(DEFAULT_MODEL_NAME)
        MusicgenForConditionalGeneration.from_pretrained(DEFAULT_MODEL_NAME)
    except Exception as exc:
        print(f"[PRELOAD] status=failed reason=download_or_load_error details={exc}")
        return 1

    print("[PRELOAD] status=success")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
