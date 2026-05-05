from __future__ import annotations

from datetime import date, datetime
from typing import Any

from .copywriter import generate_social_posts
from .engine import (
    ImageGenerationPersistenceError,
    download_product_reference,
    generate_marketing_image,
    prepare_output_dir,
    write_metadata,
)
from .prompts import build_image_prompt
from .repository import save_generated_image
from .selectors import (
    ImageGenerationContextError,
    detect_exam_period,
    detect_next_occasion,
    resolve_given_occasion,
    select_product_for_context,
)


class ImageGenerationRequestValidationError(RuntimeError):
    pass


class ImageGenerationService:
    def handle(self, payload: dict[str, Any]) -> dict[str, Any]:
        media_type = str(payload.get("media_type", "image")).strip().lower()
        generation_mode = str(payload.get("generation_mode", "")).strip().lower()

        if media_type != "image":
            raise ImageGenerationRequestValidationError(
                "Le service image attend media_type='image'."
            )

        if generation_mode not in {"next_occasion", "exam_period", "given_occasion"}:
            raise ImageGenerationRequestValidationError(
                "generation_mode doit etre 'next_occasion', 'exam_period' ou 'given_occasion'."
            )

        reference_date = self._parse_reference_date(payload.get("date"))
        context = self._resolve_context(
            generation_mode=generation_mode,
            occasion=payload.get("occasion"),
            reference_date=reference_date,
        )
        selected_product = select_product_for_context(context)
        social_posts = generate_social_posts(context, selected_product)
        preferred_platform = self._resolve_preferred_platform(payload)

        result: dict[str, Any] = {
            "status": "success",
            "intent": "publication",
            "type_publication": "image",
            "generation_mode": generation_mode,
            "occasion": context["occasion"],
            "occasion_type": context["occasion_type"],
            "date_occasion": context["date_occasion"],
            "date_publication": context["date_actuelle"],
            "saison": context["saison"],
            "produit": selected_product["produit"],
            "produit_source": selected_product["produit"],
            "product_url": selected_product.get("product_url") or "",
            "image_url": selected_product.get("url_image") or "",
            "description_post": social_posts.get(preferred_platform) or social_posts["default"],
            "publication_posts": {
                "facebook": social_posts.get("facebook", ""),
                "instagram": social_posts.get("instagram", ""),
                "preferred_platform": preferred_platform,
            },
        }
        overlay_text = self._extract_overlay_text(payload)
        if overlay_text:
            result["image_overlay"] = overlay_text

        output_dir = prepare_output_dir(result)
        product_image, reference_files = download_product_reference(output_dir, selected_product)
        prompt = build_image_prompt(context, selected_product)
        result["prompt_image"] = prompt

        saved_files = write_metadata(output_dir, result)
        saved_files.update(reference_files)
        saved_files.update(
            generate_marketing_image(
                output_dir=output_dir,
                prompt=prompt,
                product_image=product_image,
                selected_product=selected_product,
                context=context,
                overlay_text=overlay_text,
            )
        )
        result["saved_files"] = saved_files
        write_metadata(output_dir, result)

        try:
            save_generated_image(result)
        except Exception as exc:
            raise ImageGenerationPersistenceError(
                f"Echec de la sauvegarde des metadonnees image en BDD: {exc}"
            ) from exc

        return result

    @staticmethod
    def _resolve_context(
        generation_mode: str,
        occasion: Any,
        reference_date: date | None,
    ) -> dict[str, Any]:
        if generation_mode == "next_occasion":
            return detect_next_occasion(reference_date)
        if generation_mode == "exam_period":
            return detect_exam_period(reference_date)
        return resolve_given_occasion(str(occasion or ""), reference_date)

    @staticmethod
    def _parse_reference_date(raw_date: Any) -> date | None:
        if raw_date is None:
            return None
        try:
            return datetime.strptime(str(raw_date).strip(), "%Y-%m-%d").date()
        except ValueError as exc:
            raise ImageGenerationRequestValidationError(
                "Le champ 'date' doit etre au format YYYY-MM-DD lorsqu'il est fourni."
            ) from exc

    @staticmethod
    def _resolve_preferred_platform(payload: dict[str, Any]) -> str:
        platform = str(payload.get("platform") or payload.get("preferred_platform") or "").strip().lower()
        if platform in {"facebook", "instagram"}:
            return platform
        return "instagram"

    @staticmethod
    def _extract_overlay_text(payload: dict[str, Any]) -> dict[str, str] | None:
        overlay_text: dict[str, str] = {}
        for source_key, target_key in (
            ("overlay_badge", "badge"),
            ("overlay_title", "title"),
            ("overlay_subtitle", "subtitle"),
        ):
            value = payload.get(source_key)
            if isinstance(value, str) and value.strip():
                overlay_text[target_key] = value.strip()

        return overlay_text or None
