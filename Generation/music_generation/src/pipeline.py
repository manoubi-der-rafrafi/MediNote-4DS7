from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

import pandas as pd

try:
    from .evaluator import evaluate_metadata
    from .mood_style_model import predict_style, train_models
    from .musicgen_generator import generate_audio_with_musicgen, is_musicgen_available
    from .preprocess_holidays import build_occasion_context
    from .prompt_generator import generate_music_prompt
except ImportError:
    from evaluator import evaluate_metadata
    from mood_style_model import predict_style, train_models
    from musicgen_generator import generate_audio_with_musicgen, is_musicgen_available
    from preprocess_holidays import build_occasion_context
    from prompt_generator import generate_music_prompt


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = ROOT_DIR / "outputs"
METADATA_PATH = OUTPUTS_DIR / "generated_music_metadata.csv"


def _append_metadata(row: dict, metadata_path: Path = METADATA_PATH) -> None:
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame([row])
    if metadata_path.exists():
        existing = pd.read_csv(metadata_path)
        frame = pd.concat([existing, frame], ignore_index=True)
    frame.to_csv(metadata_path, index=False)


def run_pipeline(
    holiday: str,
    product_theme: str,
    duration: int = 15,
    country: Optional[str] = None,
    year: Optional[int] = None,
    prompt_only: bool = False,
) -> dict:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    train_models()

    context = build_occasion_context(holiday, product_theme, country=country, year=year)
    style = predict_style(context)
    prompt = generate_music_prompt(context, style, duration)

    audio_path = None
    generation_status = "prompt_only_requested" if prompt_only else "musicgen_not_installed"
    if not prompt_only and is_musicgen_available():
        audio_path = generate_audio_with_musicgen(
            prompt=prompt,
            holiday_name=context.holiday_name,
            product_theme=context.product_theme,
            duration=duration,
        )
        generation_status = "audio_generated" if audio_path else "musicgen_failed"

    row = {
        "run_id": uuid4().hex,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "holiday_name": context.holiday_name,
        "local_name": context.local_name,
        "country": context.country,
        "year": context.year,
        "date": context.date,
        "occasion_type": context.occasion_type,
        "product_theme": context.product_theme,
        "target_mood": style.target_mood,
        "genre": style.genre,
        "instruments": style.instruments,
        "tempo": style.tempo,
        "style_source": style.source,
        "duration_seconds": duration,
        "prompt": prompt,
        "audio_path": str(audio_path) if audio_path else "",
        "generation_status": generation_status,
    }
    _append_metadata(row)
    evaluate_metadata()
    return row

