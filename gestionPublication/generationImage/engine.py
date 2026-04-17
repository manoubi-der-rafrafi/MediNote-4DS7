from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any
from urllib import request
from urllib.error import HTTPError
from urllib.parse import urlparse

from .config import (
    HF_IMAGE_MODEL_NAME,
    IMAGE_OUTPUT_FILENAME,
    IMAGE_SIZE,
    METADATA_FILENAME,
    OUTPUT_DIR,
    ImageGenerationConfigError,
    get_hf_api_key,
)


class ImageGenerationRequestError(RuntimeError):
    pass


class ImageGenerationPersistenceError(RuntimeError):
    pass


def download_product_reference(
    output_dir: Path,
    selected_product: dict[str, Any],
) -> tuple[Any, dict[str, str]]:
    image_url = str(selected_product.get("url_image") or "").strip()
    if not image_url:
        raise ImageGenerationRequestError(
            f"L'URL de l'image produit est vide pour {selected_product['produit']}."
        )

    parsed_url = urlparse(image_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ImageGenerationRequestError(
            f"L'URL de l'image produit est invalide pour {selected_product['produit']}: {image_url}"
        )

    Image, _, _, _ = _get_pillow_modules()

    try:
        with request.urlopen(image_url, timeout=60) as response:
            payload = response.read()
    except HTTPError as exc:
        raise ImageGenerationRequestError(
            f"L'URL de l'image produit est inaccessible ({exc.code}) pour {selected_product['produit']}."
        ) from exc
    except Exception as exc:
        raise ImageGenerationRequestError(
            f"L'URL de l'image produit est invalide ou inaccessible pour {selected_product['produit']}: {exc}"
        ) from exc

    try:
        original = Image.open(io.BytesIO(payload)).convert("RGBA")
    except Exception as exc:
        raise ImageGenerationRequestError(
            f"L'image officielle du produit {selected_product['produit']} est invalide ou illisible."
        ) from exc

    processed = _remove_white_background(original)
    reference_path = output_dir / "product_reference.png"
    try:
        processed.save(reference_path, format="PNG")
    except Exception as exc:
        raise ImageGenerationPersistenceError(
            f"Echec de la sauvegarde de l'image produit: {exc}"
        ) from exc

    return processed, {"product_reference_file": str(reference_path)}


def _get_numpy_module():
    try:
        import numpy as np
    except ImportError as exc:
        raise ImageGenerationConfigError(
            "Le module numpy est requis pour la composition d'image."
        ) from exc
    return np


def _get_pillow_modules():
    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageFont
    except ImportError as exc:
        raise ImageGenerationConfigError(
            "Le module Pillow est requis pour la composition d'image."
        ) from exc
    return Image, ImageDraw, ImageFilter, ImageFont


def _get_font(size: int, bold: bool = False):
    _, _, _, ImageFont = _get_pillow_modules()
    font_candidates = []
    if bold:
        font_candidates.extend(
            [
                r"C:\Windows\Fonts\arialbd.ttf",
                r"C:\Windows\Fonts\segoeuib.ttf",
            ]
        )
    else:
        font_candidates.extend(
            [
                r"C:\Windows\Fonts\arial.ttf",
                r"C:\Windows\Fonts\segoeui.ttf",
            ]
        )

    for candidate in font_candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def _get_hf_client_class():
    try:
        from huggingface_hub import InferenceClient
    except ImportError as exc:
        raise ImageGenerationConfigError(
            "Le module huggingface_hub est requis pour la generation d'image."
        ) from exc
    return InferenceClient


def prepare_output_dir(result: dict[str, Any]) -> Path:
    safe_occasion = _slugify(result["occasion"])
    safe_mode = _slugify(result["generation_mode"])
    output_dir = OUTPUT_DIR / f'{result["date_occasion"]}_{safe_occasion}_{safe_mode}'

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        raise ImageGenerationPersistenceError(
            f"Echec de la preparation du dossier image: {exc}"
        ) from exc

    return output_dir


def write_metadata(output_dir: Path, payload: dict[str, Any]) -> dict[str, str]:
    metadata_path = output_dir / METADATA_FILENAME
    try:
        metadata_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as exc:
        raise ImageGenerationPersistenceError(
            f"Echec de la sauvegarde des metadonnees image: {exc}"
        ) from exc

    return {
        "output_dir": str(output_dir),
        "metadata_json": str(metadata_path),
    }


def generate_marketing_image(
    output_dir: Path,
    prompt: str,
    product_image,
    selected_product: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, str]:
    background = _build_background(prompt)
    composed = _compose_final_image(background, product_image, selected_product, context)

    image_path = output_dir / IMAGE_OUTPUT_FILENAME
    try:
        composed.save(image_path, format="PNG")
    except Exception as exc:
        raise ImageGenerationPersistenceError(
            f"Echec de la sauvegarde du fichier image: {exc}"
        ) from exc

    return {"image_file": str(image_path)}


def _build_background(prompt: str):
    Image, _, _, _ = _get_pillow_modules()

    try:
        InferenceClient = _get_hf_client_class()
        client = InferenceClient(provider="hf-inference", api_key=get_hf_api_key())
        generated = client.text_to_image(
            prompt=prompt,
            model=HF_IMAGE_MODEL_NAME,
            width=IMAGE_SIZE[0],
            height=IMAGE_SIZE[1],
        )
        if generated is not None:
            return generated.convert("RGBA")
    except Exception as exc:
        raise ImageGenerationRequestError(
            f"Echec de la generation du fond via Hugging Face: {exc}"
        ) from exc

    raise ImageGenerationRequestError(
        "Hugging Face n'a retourne aucun visuel pour le fond de l'image."
    )


def _remove_white_background(image):
    np = _get_numpy_module()
    Image, _, _, _ = _get_pillow_modules()

    rgba = np.array(image.convert("RGBA"))
    red = rgba[:, :, 0]
    green = rgba[:, :, 1]
    blue = rgba[:, :, 2]
    alpha = rgba[:, :, 3]

    white_mask = (red > 245) & (green > 245) & (blue > 245)
    alpha[white_mask] = 0
    rgba[:, :, 3] = alpha
    return Image.fromarray(rgba, mode="RGBA")


def _compose_final_image(background, product_image, selected_product: dict[str, Any], context: dict[str, Any]):
    Image, _, _, _ = _get_pillow_modules()

    canvas = background.copy().convert("RGBA")
    canvas = _soften_center_background(canvas)

    product = product_image.copy()
    product.thumbnail((360, 360))
    product = _add_soft_product_glow(product)

    x = (IMAGE_SIZE[0] - product.size[0]) // 2
    y = 160
    _draw_product_stage(canvas, x, y, product.size)
    canvas.alpha_composite(product, (x, y))

    return canvas.convert("RGB")


def _soften_center_background(background):
    Image, ImageDraw, ImageFilter, _ = _get_pillow_modules()

    blurred = background.filter(ImageFilter.GaussianBlur(14))
    mask = Image.new("L", IMAGE_SIZE, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((250, 90, 774, 642), fill=220)
    mask = mask.filter(ImageFilter.GaussianBlur(40))
    base = Image.composite(blurred, background, mask)

    spotlight = Image.new("RGBA", IMAGE_SIZE, (0, 0, 0, 0))
    spotlight_draw = ImageDraw.Draw(spotlight)
    spotlight_draw.ellipse((235, 70, 789, 670), fill=(255, 255, 255, 72))
    spotlight = spotlight.filter(ImageFilter.GaussianBlur(48))
    base.alpha_composite(spotlight)
    return base


def _draw_product_stage(canvas, x: int, y: int, product_size: tuple[int, int]) -> None:
    Image, ImageDraw, ImageFilter, _ = _get_pillow_modules()

    stage = Image.new("RGBA", IMAGE_SIZE, (0, 0, 0, 0))
    stage_draw = ImageDraw.Draw(stage)
    stage_draw.ellipse(
        (x - 48, y + product_size[1] - 10, x + product_size[0] + 48, y + product_size[1] + 74),
        fill=(20, 25, 35, 68),
    )
    stage = stage.filter(ImageFilter.GaussianBlur(26))
    canvas.alpha_composite(stage)


def _add_soft_product_glow(product):
    Image, _, ImageFilter, _ = _get_pillow_modules()

    glow = Image.new("RGBA", product.size, (0, 0, 0, 0))
    alpha = product.getchannel("A")
    glow.putalpha(alpha)
    glow = glow.filter(ImageFilter.GaussianBlur(18))
    glow_layer = Image.new("RGBA", product.size, (255, 255, 255, 0))
    glow_layer.putalpha(glow.getchannel("A"))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(14))

    composed = Image.new("RGBA", product.size, (0, 0, 0, 0))
    composed.alpha_composite(glow_layer)
    composed.alpha_composite(product)
    return composed


def _slugify(value: str) -> str:
    import re

    lowered = str(value).strip().lower()
    lowered = re.sub(r"[^a-z0-9]+", "_", lowered)
    return lowered.strip("_") or "publication"
