from __future__ import annotations

import json
from typing import Any
from urllib import request

from .config import get_mistral_api_key
from .selectors import get_product_profile


MISTRAL_CHAT_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_MODEL_NAME = "mistral-large-latest"


def generate_social_posts(
    context: dict[str, Any],
    selected_product: dict[str, Any],
) -> dict[str, str]:
    profile = get_product_profile(str(selected_product.get("produit") or ""))

    facebook_post = _generate_single_post(
        platform="Facebook",
        context=context,
        selected_product=selected_product,
        profile=profile,
    )
    instagram_post = _generate_single_post(
        platform="Instagram",
        context=context,
        selected_product=selected_product,
        profile=profile,
    )

    return {
        "facebook": facebook_post,
        "instagram": instagram_post,
        "default": instagram_post or facebook_post,
    }


def _generate_single_post(
    platform: str,
    context: dict[str, Any],
    selected_product: dict[str, Any],
    profile: dict[str, Any] | None,
) -> str:
    api_key = get_mistral_api_key()
    if not api_key:
        return _build_fallback_post(platform, context, selected_product, profile)

    prompt = _build_mistral_prompt(platform, context, selected_product, profile)
    body = json.dumps(
        {
            "model": MISTRAL_MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.75,
        }
    ).encode("utf-8")
    chat_request = request.Request(
        MISTRAL_CHAT_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(chat_request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
        content = (
            payload.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        generated = _normalize_post_text(content)
        if generated:
            return generated
    except Exception:
        pass

    return _build_fallback_post(platform, context, selected_product, profile)


def _build_mistral_prompt(
    platform: str,
    context: dict[str, Any],
    selected_product: dict[str, Any],
    profile: dict[str, Any] | None,
) -> str:
    occasion = str(context.get("occasion") or "").strip()
    occasion_type = str(context.get("occasion_type") or "").strip().lower()
    product_name = str(selected_product.get("produit") or "").strip()

    lengths = {
        "Facebook": "120-150 mots",
        "Instagram": "70-90 mots + emojis pertinents + hashtags",
        "LinkedIn": "150-200 mots, ton professionnel",
    }

    period_label = occasion if occasion else "cette periode"
    context_label = _marketing_context_label(context)

    indications = _short_text((profile or {}).get("indications"), 220)
    composition = _short_text((profile or {}).get("composition"), 200)
    positive_points = _short_text((profile or {}).get("points_positifs"), 260)
    verdict = _short_text((profile or {}).get("verdict"), 140)
    negative_points = _short_text((profile or {}).get("points_negatifs"), 180)

    return f"""
Tu es le responsable marketing de Vital Laboratories Tunisie.
Tu rediges des posts sociaux naturels, professionnels et credibles, jamais trop commerciaux.

=== CONTEXTE ===
Periode / occasion : {period_label}
Type : {occasion_type}
Contexte sante lie : {context_label}
Ton a adopter : chaleureux, premium, naturel, adapte au public tunisien
Plateforme : {platform}

=== PROFIL PRODUIT ===
Nom : {product_name}
Indications : {indications}
Ingredients / composition : {composition}
Avis ou points positifs : {positive_points}
Verdict general : {verdict}
A ne jamais mentionner : {negative_points}

=== CONSIGNE ===
Ecris un post {platform} naturel et convaincant.
Longueur cible : {lengths.get(platform, "120 mots")}

STRUCTURE OBLIGATOIRE :
1. Accroche liee au contexte sante de la periode, sans commencer par le nom du produit
2. Transition naturelle entre l'occasion et le besoin
3. Presentation du produit comme solution concrete, avec au moins un benefice reel ou un ingredient cle
4. Call to action doux
5. Hashtags adaptes a Vital et au contexte

REGLES :
- Francais naturel, simple et elegant
- Mentionne la marque Vital naturellement
- Ne fais aucune promesse medicale exageree
- N'invente pas d'informations
- Pas de titre, pas d'introduction meta, pas de JSON
- Commence directement par le texte du post
""".strip()


def _build_fallback_post(
    platform: str,
    context: dict[str, Any],
    selected_product: dict[str, Any],
    profile: dict[str, Any] | None,
) -> str:
    occasion = str(context.get("occasion") or "").strip()
    product_name = str(selected_product.get("produit") or "Vital").strip()
    context_label = _marketing_context_label(context)
    benefit = _first_meaningful_chunk((profile or {}).get("indications")) or context_label
    composition = _first_meaningful_chunk((profile or {}).get("composition"))
    verdict = _first_meaningful_chunk((profile or {}).get("verdict"))

    opening = {
        "Facebook": (
            f"Pendant {occasion or 'cette periode'}, prendre soin de son equilibre compte encore plus. "
            f"Vital met {product_name} en avant pour accompagner {context_label}."
        ),
        "Instagram": (
            f"{occasion or 'Cette periode'} est souvent synonyme de rythme charge. "
            f"{product_name} accompagne naturellement {context_label}."
        ),
    }.get(
        platform,
        f"{occasion or 'Cette periode'} est un bon moment pour prendre soin de soi avec Vital."
    )

    details = [f"{product_name} aide a soutenir {benefit}."]
    if composition:
        details.append(f"Sa composition met en avant {composition}.")
    if verdict:
        details.append(f"Ce qui ressort le plus: {verdict}.")

    closing = {
        "Facebook": "Disponible dans l'univers Vital pour une communication sante plus claire et rassurante.",
        "Instagram": "A decouvrir dans l'univers Vital. #Vital #BienEtre #Sante #Tunisie",
    }.get(platform, "A decouvrir dans l'univers Vital.")

    return " ".join([opening, *details, closing]).strip()


def _marketing_context_label(context: dict[str, Any]) -> str:
    occasion_type = str(context.get("occasion_type") or "").strip().lower()
    occasion = str(context.get("occasion") or "").strip()

    if occasion_type == "periode_examens":
        return "la concentration, la clarte mentale et le confort au quotidien"
    if occasion_type == "saison":
        if occasion.lower() == "ete":
            return "l'energie, le confort et le bien-etre pendant l'ete"
        if occasion.lower() == "printemps":
            return "la vitalite et le confort pendant le printemps"
        if occasion.lower() == "hiver":
            return "le soutien du bien-etre pendant l'hiver"
        if occasion.lower() == "automne":
            return "l'equilibre et la vitalite pendant l'automne"
    if "ramadan" in occasion.lower():
        return "le confort digestif et l'equilibre pendant Ramadan"
    if "eid" in occasion.lower() or "aid" in occasion.lower():
        return "le confort et la legerete pendant les repas de fete"
    return f"les besoins lies a {occasion}" if occasion else "le bien-etre au quotidien"


def _normalize_post_text(value: Any) -> str:
    text = str(value or "").strip()
    text = text.replace("\r\n", "\n").strip()
    return text


def _short_text(value: Any, limit: int) -> str:
    cleaned = " ".join(str(value or "").split())
    if not cleaned:
        return ""
    return cleaned[:limit].rstrip(" ,;:.")


def _first_meaningful_chunk(value: Any) -> str:
    cleaned = _short_text(value, 180)
    if not cleaned:
        return ""
    for separator in (";", ".", ","):
        if separator in cleaned:
            head = cleaned.split(separator, 1)[0].strip()
            if head:
                return head
    return cleaned
