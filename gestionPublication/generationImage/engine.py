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


IMAGE_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/135.0.0.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}


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
        image_request = request.Request(
            image_url,
            headers={
                **IMAGE_REQUEST_HEADERS,
                "Referer": f"{parsed_url.scheme}://{parsed_url.netloc}/",
            },
        )
        with request.urlopen(image_request, timeout=60) as response:
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
    overlay_text: dict[str, str] | None = None,
) -> dict[str, str]:
    background = _build_background(prompt)
    composed = _compose_final_image(
        background,
        product_image,
        selected_product,
        context,
        overlay_text=overlay_text,
    )

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


def _compose_final_image(
    background,
    product_image,
    selected_product: dict[str, Any],
    context: dict[str, Any],
    overlay_text: dict[str, str] | None = None,
):
    Image, _, _, _ = _get_pillow_modules()

    canvas = background.copy().convert("RGBA")
    canvas = _enhance_center_background(canvas)

    product = product_image.copy()
    product.thumbnail((360, 360))
    product = _add_soft_product_glow(product)

    x = (IMAGE_SIZE[0] - product.size[0]) // 2
    y = 160
    _draw_product_stage(canvas, x, y, product.size)
    canvas.alpha_composite(product, (x, y))
    _draw_marketing_text_overlay(canvas, selected_product, context, overlay_text=overlay_text)

    return canvas.convert("RGB")


def _enhance_center_background(background):
    Image, ImageDraw, ImageFilter, _ = _get_pillow_modules()

    mask = Image.new("L", IMAGE_SIZE, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((250, 110, 774, 648), fill=210)
    mask = mask.filter(ImageFilter.GaussianBlur(54))

    spotlight = Image.new("RGBA", IMAGE_SIZE, (0, 0, 0, 0))
    spotlight_draw = ImageDraw.Draw(spotlight)
    spotlight_draw.ellipse((225, 88, 799, 700), fill=(255, 255, 255, 52))
    spotlight = spotlight.filter(ImageFilter.GaussianBlur(64))

    base = background.copy()
    lifted_center = Image.new("RGBA", IMAGE_SIZE, (245, 248, 252, 0))
    lifted_center.putalpha(mask)
    base.alpha_composite(lifted_center)
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


def _draw_marketing_text_overlay(
    canvas,
    selected_product: dict[str, Any],
    context: dict[str, Any],
    overlay_text: dict[str, str] | None = None,
) -> None:
    _, ImageDraw, _, _ = _get_pillow_modules()

    overlay_copy = _build_overlay_copy(selected_product, context, overlay_text=overlay_text)
    title = overlay_copy["title"]
    subtitle = overlay_copy["subtitle"]
    badge = overlay_copy["badge"]

    title_font = _get_font(58, bold=True)
    subtitle_font = _get_font(24, bold=False)
    badge_font = _get_font(22, bold=True)

    measure_layer = ImageDraw.Draw(canvas)
    max_text_width = IMAGE_SIZE[0] - 180
    title_lines = _wrap_text(measure_layer, title, title_font, max_text_width)
    subtitle_lines = (
        _wrap_text(measure_layer, subtitle, subtitle_font, max_text_width)
        if subtitle
        else []
    )

    draw = ImageDraw.Draw(canvas)
    text_x = 72
    text_y = 72
    subtitle_gap = 14 if subtitle_lines else 0

    if badge:
        badge_box = measure_layer.textbbox((0, 0), badge, font=badge_font)
        badge_height = badge_box[3] - badge_box[1]
        _draw_text_with_shadow(
            draw,
            (text_x, text_y),
            badge,
            badge_font,
            fill=(245, 185, 84, 255),
            shadow=(28, 36, 48, 140),
        )
        text_y += badge_height + 18

    _draw_multiline_with_shadow(
        draw,
        (text_x, text_y),
        title_lines,
        title_font,
        line_spacing=10,
        fill=(255, 248, 236, 255),
        shadow=(28, 36, 48, 150),
    )
    text_y += _get_multiline_height(measure_layer, title_lines, title_font, 10) + subtitle_gap

    if subtitle_lines:
        _draw_multiline_with_shadow(
            draw,
            (text_x, text_y),
            subtitle_lines,
            subtitle_font,
            line_spacing=8,
            fill=(238, 242, 247, 245),
            shadow=(28, 36, 48, 130),
        )


def _build_overlay_copy(
    selected_product: dict[str, Any],
    context: dict[str, Any],
    overlay_text: dict[str, str] | None = None,
) -> dict[str, str]:
    occasion = str(context.get("occasion") or "").strip()
    occasion_type = str(context.get("occasion_type") or "").strip().lower()
    normalized_occasion = occasion.lower()

    if occasion_type == "periode_examens":
        title = "Examens"
        subtitle = ""
    elif normalized_occasion == "ramadan":
        title = "Ramadan"
        subtitle = ""
    elif occasion_type == "saison":
        title = _format_title_case(occasion)
        subtitle = ""
    else:
        title = _format_title_case(occasion or "Vital")
        subtitle = ""

    computed = {
        "badge": "VITAL",
        "title": title,
        "subtitle": subtitle,
    }
    if overlay_text:
        computed.update(
            {
                key: value
                for key, value in overlay_text.items()
                if isinstance(value, str) and value.strip()
            }
        )
    return computed


def _format_title_case(value: str) -> str:
    words = [part for part in str(value).replace("_", " ").split() if part]
    return " ".join(word[:1].upper() + word[1:] for word in words) or "Vital"


def _wrap_text(draw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current = words[0]

    for word in words[1:]:
        candidate = f"{current} {word}"
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word

    lines.append(current)
    return lines


def _get_multiline_height(draw, lines: list[str], font, line_spacing: int) -> int:
    total = 0
    for index, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        total += bbox[3] - bbox[1]
        if index < len(lines) - 1:
            total += line_spacing
    return total


def _draw_text_with_shadow(draw, position, text: str, font, fill, shadow) -> None:
    x, y = position
    draw.text((x + 2, y + 2), text, font=font, fill=shadow)
    draw.text((x, y), text, font=font, fill=fill)


def _draw_multiline_with_shadow(
    draw,
    position,
    lines: list[str],
    font,
    line_spacing: int,
    fill,
    shadow,
) -> None:
    x, y = position
    for line in lines:
        _draw_text_with_shadow(draw, (x, y), line, font=font, fill=fill, shadow=shadow)
        bbox = draw.textbbox((0, 0), line, font=font)
        y += (bbox[3] - bbox[1]) + line_spacing


def _slugify(value: str) -> str:
    import re

    lowered = str(value).strip().lower()
    lowered = re.sub(r"[^a-z0-9]+", "_", lowered)
    return lowered.strip("_") or "publication"
