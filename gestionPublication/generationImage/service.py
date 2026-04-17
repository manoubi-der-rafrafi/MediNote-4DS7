from __future__ import annotations

from datetime import date, datetime
from typing import Any

from .engine import (
    ImageGenerationPersistenceError,
    download_product_reference,
    generate_marketing_image,
    prepare_output_dir,
    write_metadata,
)
from .prompts import build_image_prompt
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
            "description_post": self._build_description_post(context, selected_product),
        }

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
            )
        )
        result["saved_files"] = saved_files
        write_metadata(output_dir, result)
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
    def _build_description_post(
        context: dict[str, Any],
        selected_product: dict[str, Any],
    ) -> str:
        occasion = context["occasion"]
        product = selected_product["produit"]
        occasion_type = context["occasion_type"]

        if occasion_type == "periode_examens":
            return (
                f"Vital met {product} en avant pour accompagner la periode des examens "
                "avec un univers visuel clair, premium et adapte aux reseaux sociaux."
            )

        if occasion_type == "saison":
            return (
                f"Publication image Vital pour la saison {occasion}, construite autour du produit "
                f"{product} avec un angle marketing coherent."
            )

        return (
            f"Publication image Vital pour {occasion}, basee sur le produit {product} "
            "et sur la methode de selection issue du notebook."
        )