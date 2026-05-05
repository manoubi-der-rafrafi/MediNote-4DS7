from __future__ import annotations

from datetime import datetime
from typing import Any

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
            date_occasion=_parse_nullable_date(payload.get("date_occasion")),
            date_publication=_parse_nullable_date(payload.get("date_publication")),
        )
        session.add(row)
        session.flush()
        session.refresh(row)
        return row


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
