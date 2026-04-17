from typing import Any


def get_fete_visual_prompt(fete_nom: str, fete_info: dict[str, Any]) -> str:
    nom = fete_nom.lower()

    if "eid al-adha" in nom or "aid el adha" in nom or "adha" in nom:
        return (
            "Eid al-Adha celebration in Tunisia, sheep symbolism, family feast, "
            "warm golden festive atmosphere, subtle Tunisian decoration"
        )
    if "eid al-fitr" in nom or "aid el fitr" in nom or "fitr" in nom:
        return (
            "Eid al-Fitr celebration in Tunisia, joyful family atmosphere, pastries, "
            "elegant festive decoration, warm premium lighting"
        )
    if "ramadan" in nom:
        return (
            "Ramadan atmosphere in Tunisia, lanterns, crescent moon, iftar ambiance, "
            "warm night lighting, premium elegant composition"
        )
    if "mawlid" in nom or "mouled" in nom:
        return (
            "Mawlid celebration in Tunisia, traditional sweets, spiritual festive ambiance, "
            "warm refined gold and blue tones"
        )
    if "new year's day" in nom:
        return (
            "New year wellness campaign, clean premium celebration atmosphere, "
            "fresh elegant light, subtle festive details"
        )
    if "martyrs" in nom:
        return (
            "Solemn patriotic remembrance, Tunisian flag colors, dignified atmosphere, "
            "premium clean composition"
        )
    if "independence" in nom or "republic" in nom or "revolution" in nom:
        return (
            "Tunisian national celebration, national pride, flags waving, "
            "festive patriotic mood, elegant premium composition"
        )
    return str(fete_info.get("style_visuel", "festive Tunisian atmosphere"))


def get_saison_visual_prompt(nom_saison: str, saison_info: dict[str, Any]) -> str:
    nom = nom_saison.lower()
    base_style = (
        "ultra professional Instagram pharmaceutical advertisement background, "
        "high-end healthcare campaign, elegant premium atmosphere, "
        "clean composition, soft cinematic lighting, shallow depth of field"
    )

    if "bac" in nom or "exam" in nom or "examen" in nom:
        return (
            f"{base_style}, focused study atmosphere, academic desk elements, "
            "stress relief, mental clarity, energy support, soft blue tones"
        )
    if "hiver" in nom or "winter" in nom:
        return (
            f"{base_style}, winter health theme, immunity, cozy warm lighting, "
            "subtle frost background, soft blue white palette"
        )
    if "ete" in nom or "summer" in nom:
        return (
            f"{base_style}, summer wellness theme, heat protection, hydration, energy boost, "
            "bright clean sunlight, fresh vibrant tones"
        )
    if "printemps" in nom or "spring" in nom:
        return (
            f"{base_style}, spring health theme, renewal, vitality, freshness, "
            "soft green pastel tones, natural light"
        )
    if "automne" in nom or "autumn" in nom or "fall" in nom:
        return (
            f"{base_style}, autumn wellness theme, gentle warm tones, transition season, "
            "comfort and vitality atmosphere"
        )
    return (
        f"{base_style}, "
        f"{saison_info.get('style_visuel', 'premium pharmaceutical aesthetic')}"
    )


def build_image_prompt(
    context: dict[str, Any],
    selected_product: dict[str, Any],
) -> str:
    occasion_type = str(context.get("occasion_type", "")).strip().lower()
    if occasion_type == "fete":
        visual_style = get_fete_visual_prompt(context["occasion"], context)
    else:
        visual_style = get_saison_visual_prompt(context["occasion"], context)

    return (
        f"{visual_style}, premium pharmaceutical advertising background for Vital, "
        f"luxury social media campaign for {selected_product['produit']}, "
        "minimal elegant decor, clean negative space in the center, "
        "soft blurred background, product area intentionally empty, "
        "background only, no product, no bottle, no box, no packaging, no packshot, "
        "no label, no brand text, no readable text, no typography, no watermark, "
        "no collage, no duplicate object, no fruit in foreground, no flowers in foreground, "
        "no water splash crossing the center, no central object."
    )
