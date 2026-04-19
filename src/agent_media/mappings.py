from __future__ import annotations

THEME_TO_IND = {
    "digestion": [
        "indication_digestion",
        "indication_estomac",
        "indication_foie",
        "therapeutic_theme_digestif",
        "indication_ballonnement",
    ],
    "estomac": ["indication_estomac", "indication_digestion", "therapeutic_theme_digestif"],
    "foie": ["indication_foie", "therapeutic_theme_digestif"],
    "energie": [
        "indication_energie",
        "indication_fatigue",
        "therapeutic_theme_energie",
        "indication_fer",
        "indication_vitamine_b",
    ],
    "fatigue": ["indication_fatigue", "indication_energie", "therapeutic_theme_energie"],
    "fer": ["indication_fer", "therapeutic_theme_carence"],
    "immunite": [
        "indication_immunite",
        "therapeutic_theme_immunite",
        "indication_vitamine_c",
        "indication_zinc",
    ],
    "anti-rhume": ["indication_rhume", "indication_immunite", "therapeutic_theme_immunite"],
    "vitamine d": ["indication_vitamine_d", "therapeutic_theme_immunite"],
    "vitamines": [
        "indication_vitamine_c",
        "indication_vitamine_d",
        "indication_vitamine_b",
        "therapeutic_theme_vitamines",
    ],
    "vitamine_c": ["indication_vitamine_c", "therapeutic_theme_vitamines"],
    "stress": ["indication_stress", "indication_anxiete", "therapeutic_theme_stress"],
    "sommeil": ["indication_sommeil", "therapeutic_theme_stress"],
    "anxiete": ["indication_anxiete", "therapeutic_theme_stress"],
    "hydratation": ["indication_hydratation", "therapeutic_theme_dermatologie"],
    "protection solaire": ["indication_soleil", "therapeutic_theme_dermatologie"],
    "allergies": ["indication_allergie", "therapeutic_theme_allergie"],
    "detox": ["indication_detox", "indication_foie", "therapeutic_theme_digestif"],
    "bien-etre general": ["therapeutic_theme_bien_etre", "indication_energie"],
    "anti-fatigue": ["indication_fatigue", "indication_energie", "therapeutic_theme_energie"],
    "rentree scolaire": ["indication_immunite", "indication_energie", "therapeutic_theme_immunite"],
}


def normalize_theme(value: str) -> str:
    return (
        value.lower()
        .replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("à", "a")
        .replace("ù", "u")
        .replace("ï", "i")
        .replace("î", "i")
        .replace("ô", "o")
    )
