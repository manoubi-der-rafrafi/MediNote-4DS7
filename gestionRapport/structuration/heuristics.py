import re

from .schemas import PointFortStructured
from .text_utils import cleanup_text, normalize_text, sentence_case


def extract_field_value(
    text_brut: str,
    aliases: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> str | None:
    normalized_values = {normalize_text(value): value for value in allowed_values}

    for raw_line in text_brut.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        normalized_line = normalize_text(line)
        if ":" not in normalized_line:
            continue

        key, raw_value = normalized_line.split(":", 1)
        if key.strip() not in aliases:
            continue

        candidate = raw_value.strip(" .;-")
        if candidate in normalized_values:
            return normalized_values[candidate]

        for normalized_value, canonical_value in normalized_values.items():
            if candidate == normalized_value:
                return canonical_value

    return None


def infer_mouvement(text: str) -> str:
    if re.search(r"\b(pas de mouvement|aucun mouvement|sans mouvement|absence de mouvement)\b", text):
        return "aucun"
    if re.search(r"\bmouvement\b.*\btres faible\b|\btres faible\b.*\bmouvement\b", text):
        return "tres_faible"
    if re.search(r"\bmouvement\b.*\b(remarquable|tres fort|tres forte|tres important)\b|\btres fort\b.*\bmouvement\b", text):
        return "tres_forte"
    if re.search(r"\bmouvement\b.*\bfaible\b|\bfaible\b.*\bmouvement\b", text):
        return "faible"
    if re.search(r"\bmouvement\b.*\bmoyen\b|\bmoyen\b.*\bmouvement\b", text):
        return "moyen"
    if re.search(r"\bmouvement\b.*\b(fort|important)\b|\bbon mouvement\b|\bfort\b.*\bmouvement\b", text):
        return "forte"
    return "non_precise"


def infer_potentiel(text: str) -> str:
    if re.search(r"\b(aucun potentiel|pas de potentiel|potentiel nul)\b", text):
        return "aucun"
    if re.search(r"\bpotentiel(?: est)? faible\b|\bfaible\b.*\bpotentiel\b", text):
        return "faible"
    if re.search(r"\bpotentiel(?: est)? moyen\b|\bmoyen\b.*\bpotentiel\b|\bbon potentiel\b", text):
        return "moyen"
    if re.search(r"\bpotentiel(?: est)? (fort|forte|important)\b|\bforte?\b.*\bpotentiel\b", text):
        return "forte"
    return "non_precise"


def infer_conseil(text: str) -> str:
    if re.search(r"\b(aucun conseil|pas de conseil|sans conseil)\b", text):
        return "aucun"
    if re.search(r"\bconseil(?: est)? (tres )?faible\b|\bfaible\b.*\bconseil\b", text):
        return "faible"
    if re.search(r"\bconseil(?: est)? moyen\b|\bmoyen\b.*\bconseil\b|\bbon conseil\b", text):
        return "moyen"
    if re.search(r"\bconseil(?: est)? fort\b|\bfort conseil\b|\btres bon conseil\b", text):
        return "forte"
    return "non_precise"


def infer_personnel_attitude(text: str) -> str:
    if re.search(
        r"\b(accueil|acceuil|personnel|personnels|preparateurs|preparatrices)\b.*\b(chaleureux|chaleureuse|gentil|gentille|sympa|souriant|aimable|cooperatif|cooperative|tolerant|tolerante|positif|positive)\b",
        text,
    ):
        return "positive"
    if re.search(
        r"\b(accueil|acceuil|personnel|personnels|preparateurs|preparatrices)\b.*\b(froid|mauvais|desagreable|negatif|negative|hostile)\b",
        text,
    ):
        return "negative"
    return "non_precise"


def infer_emplacement_proximite(text: str) -> str:
    patterns = (
        ("cabinets", r"\b(pres|proche|a cote)\b.*\bcabinet[s]?\b|\bcabinet[s]?\b"),
        ("cabines", r"\b(pres|proche|a cote)\b.*\bcabine[s]?\b|\bcabine[s]?\b"),
        ("dispensaire", r"\b(pres|proche|a cote)\b.*\bdispensaire\b|\bdispensaire\b"),
        ("hopital", r"\b(pres|proche|a cote)\b.*\bh\s*o?\s*pital\b|\bh\s*o?\s*pital\b"),
        ("centre_ville", r"\bcentre ville\b"),
        ("usines", r"\b(pres|proche|a cote)\b.*\busine[s]?\b|\busine[s]?\b"),
        ("salle_de_sport", r"\bsalle de sport[s]?\b"),
        ("marche", r"\b(pres|proche|a cote)\b.*\bmarche\b|\bmarche\b"),
    )

    for value, pattern in patterns:
        if re.search(pattern, text):
            return value

    if re.search(r"\bemplacement\b|\bpres de\b|\bproche\b|\ba cote\b", text):
        return "autre"

    return "non_precise"


def build_local_text_corrige(text_brut: str, result: PointFortStructured) -> str:
    phrases: list[str] = []
    proximity_labels = {
        "cabinets": "pres des cabinets",
        "cabines": "pres des cabines",
        "dispensaire": "pres du dispensaire",
        "hopital": "pres de l'hopital",
        "centre_ville": "au centre-ville",
        "usines": "pres des usines",
        "salle_de_sport": "pres d'une salle de sport",
        "marche": "pres du marche",
        "autre": "bien situe",
    }

    if result.mouvement != "non_precise":
        phrases.append(f"Le mouvement est {result.mouvement}.")
    if result.potentiel != "non_precise":
        phrases.append(f"Le potentiel est {result.potentiel}.")
    if result.conseil != "non_precise":
        phrases.append(f"La qualite du conseil est {result.conseil}.")
    if result.emplacement_proximite != "non_precise":
        label = proximity_labels.get(result.emplacement_proximite, result.emplacement_proximite)
        phrases.append(f"L'emplacement est {label}.")
    if result.personnel_attitude != "non_precise":
        phrases.append(f"L'attitude du personnel est {result.personnel_attitude}.")
    if result.stock_disponibilite != "non_precise":
        phrases.append(f"Le stock est {result.stock_disponibilite}.")
    if result.aucun_point_fort == "oui":
        phrases.append("Aucun point fort n'est mentionne.")

    if phrases:
        return " ".join(phrases)

    cleaned = cleanup_text(text_brut)
    if not cleaned:
        return "Aucun point fort n'est precise."

    if not cleaned.endswith((".", "!", "?")):
        cleaned = f"{cleaned}."

    return sentence_case(cleaned)


def classify_point_fort_locally(text_brut: str) -> PointFortStructured:
    normalized_text = normalize_text(text_brut)

    result = PointFortStructured(
        text_corrige="",
        mouvement="non_precise",
        potentiel="non_precise",
        conseil="non_precise",
        emplacement_proximite="non_precise",
        emplacement_qualite="non_precise",
        personnel_attitude="non_precise",
        mise_en_place="non_precise",
        invitations="non_precise",
        stock_disponibilite="non_precise",
        type_pharmacie="non_precise",
        eligibilite_animation="non_precise",
        aucun_point_fort="non",
    )

    result.mouvement = extract_field_value(
        text_brut,
        ("mouvement",),
        ("aucun", "tres_faible", "faible", "moyen", "forte", "tres_forte", "non_precise"),
    ) or result.mouvement
    if result.mouvement == "non_precise":
        result.mouvement = infer_mouvement(normalized_text)

    result.potentiel = extract_field_value(
        text_brut,
        ("potentiel",),
        ("aucun", "faible", "moyen", "forte", "non_precise"),
    ) or result.potentiel
    if result.potentiel == "non_precise":
        result.potentiel = infer_potentiel(normalized_text)

    result.conseil = extract_field_value(
        text_brut,
        ("conseil",),
        ("aucun", "faible", "moyen", "forte", "non_precise"),
    ) or result.conseil
    if result.conseil == "non_precise":
        result.conseil = infer_conseil(normalized_text)

    result.emplacement_proximite = extract_field_value(
        text_brut,
        ("emplacement", "emplacement_proximite", "proximite"),
        (
            "cabinets",
            "cabines",
            "dispensaire",
            "hopital",
            "centre_ville",
            "usines",
            "salle_de_sport",
            "marche",
            "autre",
            "non_precise",
        ),
    ) or result.emplacement_proximite
    if result.emplacement_proximite == "non_precise":
        result.emplacement_proximite = infer_emplacement_proximite(normalized_text)

    result.emplacement_qualite = extract_field_value(
        text_brut,
        ("emplacement_qualite", "qualite_emplacement"),
        ("adequat", "inadequat", "non_precise"),
    ) or result.emplacement_qualite

    result.personnel_attitude = extract_field_value(
        text_brut,
        ("personnel", "personnel_attitude", "attitude_personnel", "attitude"),
        ("positive", "negative", "positive_et_negative", "non_precise"),
    ) or result.personnel_attitude
    if result.personnel_attitude == "non_precise":
        result.personnel_attitude = infer_personnel_attitude(normalized_text)

    result.mise_en_place = extract_field_value(
        text_brut,
        ("mise_en_place", "mise en place"),
        ("absente", "faible", "moyenne", "forte", "non_precise"),
    ) or result.mise_en_place

    result.invitations = extract_field_value(
        text_brut,
        ("invitations", "invitation"),
        ("non_distribuees", "distribuees", "non_precise"),
    ) or result.invitations

    result.stock_disponibilite = extract_field_value(
        text_brut,
        ("stock", "stock_disponibilite"),
        ("rupture", "faible", "important", "non_precise"),
    ) or result.stock_disponibilite

    result.type_pharmacie = extract_field_value(
        text_brut,
        ("type_pharmacie", "type pharmacie"),
        (
            "pharmacie_de_conseil",
            "pharmacie_de_passage",
            "pharmacie_de_nuit",
            "pharmacie_de_convention",
            "quartier_populaire",
            "autre",
            "non_precise",
        ),
    ) or result.type_pharmacie

    result.eligibilite_animation = extract_field_value(
        text_brut,
        ("eligibilite_animation", "eligibilite", "animation"),
        (
            "favorable",
            "a_revoir",
            "defavorable",
            "ne_merite_pas_animation",
            "non_precise",
        ),
    ) or result.eligibilite_animation

    if re.search(r"\b(aucun point fort|rien a signaler|pas de point fort)\b", normalized_text):
        result.aucun_point_fort = "oui"

    result.text_corrige = build_local_text_corrige(text_brut, result)
    return result
