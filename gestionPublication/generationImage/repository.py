from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import text

from db.models import GeneratedImage
from db.session import session_scope


def save_generated_image(payload: dict[str, Any]) -> GeneratedImage:
    saved_files = payload.get("saved_files")
    if not isinstance(saved_files, dict):
        raise ValueError("Le payload image ne contient pas 'saved_files'.")

    image_path = str(saved_files.get("image_file", "")).strip()
    prompt_image = str(payload.get("prompt_image", "")).strip()
    description_post = str(payload.get("description_post", "")).strip()

    if not image_path or not prompt_image or not description_post:
        raise ValueError(
            "Le payload image est incomplet pour la sauvegarde BDD."
        )

    with session_scope() as session:
        _ensure_generated_images_audio_columns(session)
        row = GeneratedImage(
            image_path=image_path,
            prompt_image=prompt_image,
            description_post=description_post,
            accepted=False,
            occasion=_clean_nullable_string(payload.get("occasion")),
            occasion_type=_clean_nullable_string(payload.get("occasion_type")),
            generation_mode=_clean_nullable_string(payload.get("generation_mode")),
            produit=_clean_nullable_string(payload.get("produit")),
            product_url=_clean_nullable_string(payload.get("product_url")),
            image_url=_clean_nullable_string(payload.get("image_url")),
            audio_path=_clean_nullable_string(payload.get("audio_path")),
            audio_url=_clean_nullable_string(payload.get("audio_url")),
            audio_generation_status=_clean_nullable_string(payload.get("audio_generation_status")),
            audio_error=_clean_nullable_string(payload.get("audio_error")),
            music_prompt=_clean_nullable_string(payload.get("music_prompt")),
            date_occasion=_parse_nullable_date(payload.get("date_occasion")),
            date_publication=_parse_nullable_date(payload.get("date_publication")),
        )
        session.add(row)
        session.flush()
        session.refresh(row)
        return row


def _ensure_generated_images_audio_columns(session) -> None:
    statements = (
        "ALTER TABLE generated_images ADD COLUMN audio_path TEXT NULL",
        "ALTER TABLE generated_images ADD COLUMN audio_url TEXT NULL",
        "ALTER TABLE generated_images ADD COLUMN audio_generation_status VARCHAR(100) NULL",
        "ALTER TABLE generated_images ADD COLUMN audio_error TEXT NULL",
        "ALTER TABLE generated_images ADD COLUMN music_prompt TEXT NULL",
    )
    required_columns = {
        "audio_path",
        "audio_url",
        "audio_generation_status",
        "audio_error",
        "music_prompt",
    }

    existing_rows = session.execute(text("SHOW COLUMNS FROM generated_images")).mappings().all()
    existing_columns = {
        str(row.get("Field", "")).strip().lower()
        for row in existing_rows
    }
    if required_columns.issubset(existing_columns):
        return

    for statement in statements:
        try:
            session.execute(text(statement))
        except Exception:
            continue


def _clean_nullable_string(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _parse_nullable_date(value: Any):
    cleaned = _clean_nullable_string(value)
    if cleaned is None:
        return None
    return datetime.strptime(cleaned, "%Y-%m-%d").date()
