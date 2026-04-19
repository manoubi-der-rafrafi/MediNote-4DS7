from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import pandas as pd


@dataclass(slots=True)
class HolidayContext:
    categorie: str
    necessite_produit_vital: bool
    style_visuel: str
    pic_vente: str
    saison: str


def get_season_and_peak(month: int | None) -> tuple[str, str]:
    if month in (12, 1, 2):
        return "hiver", "immunite, anti-rhume, vitamine d, energie"
    if month in (3, 4, 5):
        return "printemps", "allergies, detox, vitamines, energie"
    if month in (6, 7, 8):
        return "ete", "hydratation, protection solaire, energie"
    if month in (9, 10, 11):
        return "automne", "rentree scolaire, immunite, anti-fatigue"
    return "annuel", "bien-etre general"


def classifier_fete(holiday_name: str, local_name: str = "", date_str: Any = "") -> HolidayContext:
    name_lower = f"{holiday_name} {local_name}".lower()

    institutionnel_keywords = [
        "martyrs",
        "revolution",
        "14 janvier",
        "independance",
        "20 mars",
        "25 juillet",
        "fete du travail",
        "republique",
        "evacuation",
        "fete de la femme",
        "women",
        "republic day",
        "independence day",
        "revolution day",
    ]
    if any(keyword in name_lower for keyword in institutionnel_keywords):
        return HolidayContext(
            categorie="institutionnel",
            necessite_produit_vital=False,
            style_visuel="style officiel elegant, drapeau tunisien, ambiance patriotique sobre",
            pic_vente="image corporate uniquement",
            saison="non_applicable",
        )

    religieux_keywords = [
        "ramadan",
        "aid",
        "fetr",
        "adha",
        "mouloud",
        "achoura",
        "isra",
        "miraj",
        "eid",
        "mawlid",
    ]
    if any(keyword in name_lower for keyword in religieux_keywords):
        return HolidayContext(
            categorie="religieuse",
            necessite_produit_vital=True,
            style_visuel="ambiance sacree, lanternes, tons dores, lumiere chaleureuse",
            pic_vente="digestion, immunite, energie",
            saison="non_applicable",
        )

    month = None
    if date_str:
        parsed = pd.to_datetime(date_str, errors="coerce")
        if not pd.isna(parsed):
            month = int(parsed.month)
    saison, pic = get_season_and_peak(month)
    return HolidayContext(
        categorie="saisonniere_sante",
        necessite_produit_vital=True,
        style_visuel=f"ambiance {saison} Tunisie, {pic}",
        pic_vente=pic,
        saison=saison,
    )


def build_fetes_mapping(df_tn: pd.DataFrame) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for _, row in df_tn.iterrows():
        holiday_name = str(row["Holiday_Name"])
        local_name = str(row.get("Local_Name", "") or "")
        info = classifier_fete(holiday_name, local_name, row.get("Date", ""))
        mapping[holiday_name] = {
            "type": info.categorie,
            "categorie": info.categorie,
            "necessite_produit_vital": info.necessite_produit_vital,
            "themes": [part.strip() for part in info.pic_vente.split(",") if part.strip()],
            "style_visuel": info.style_visuel,
            "date": str(row.get("Date", "")),
            "saison": info.saison,
            "ton": _default_ton(info.categorie),
            "horaire": _default_horaire(info.categorie),
            "message_institutionnel": _message_institutionnel(holiday_name),
            "contexte_sante": _contexte_sante(info.categorie, info.pic_vente),
            "emoji": _emoji_for_category(info.categorie),
        }
    return mapping


SAISONS_MAPPING: dict[str, dict[str, Any]] = {
    "Hiver - Immunite & Grippe": {
        "type": "saisonniere",
        "debut": (12, 1),
        "fin": (2, 28),
        "themes": ["immunite", "anti-rhume", "vitamine d", "energie"],
        "pic_vente": "immunite, vitamine c, zinc, fer",
        "style_visuel": "winter Tunisia, warm interior, tea, family warmth",
        "ton": "chaleureux et rassurant",
        "horaire": "19h00",
        "contexte_sante": "Le froid affaiblit les defenses naturelles et la fatigue s'installe.",
        "saison": "hiver",
        "emoji": "HIVER",
    },
    "Rentree Scolaire": {
        "type": "saisonniere",
        "debut": (9, 1),
        "fin": (9, 30),
        "themes": ["immunite", "energie", "anti-fatigue", "vitamines"],
        "pic_vente": "immunite, energie, concentration",
        "style_visuel": "back to school Tunisia, warm autumn light, school supplies",
        "ton": "dynamique et encourageant",
        "horaire": "18h00",
        "contexte_sante": "La rentree fatigue les enfants et les parents. L'immunite est sollicitee.",
        "saison": "rentree",
        "emoji": "RENTREE",
    },
    "Periode Bac & Examens": {
        "type": "saisonniere",
        "debut": (5, 15),
        "fin": (6, 30),
        "themes": ["stress", "energie", "sommeil", "anti-fatigue"],
        "pic_vente": "stress, concentration, energie, sommeil",
        "style_visuel": "students studying, books, warm desk lamp, calm atmosphere",
        "ton": "encourageant et bienveillant",
        "horaire": "20h00",
        "contexte_sante": "Le stress des examens epuise les etudiants. Le sommeil et la concentration sont critiques.",
        "saison": "examens",
        "emoji": "EXAMENS",
    },
    "Printemps - Allergies & Detox": {
        "type": "saisonniere",
        "debut": (3, 20),
        "fin": (5, 14),
        "themes": ["allergies", "detox", "vitamines", "energie"],
        "pic_vente": "allergies, detox, vitamines printanieres",
        "style_visuel": "spring Tunisia, flowers, fresh air, green nature",
        "ton": "frais et positif",
        "horaire": "17h30",
        "contexte_sante": "Le printemps declenche les allergies et favorise les cures bien-etre.",
        "saison": "printemps",
        "emoji": "PRINTEMPS",
    },
    "Ete - Hydratation & Energie": {
        "type": "saisonniere",
        "debut": (7, 1),
        "fin": (8, 31),
        "themes": ["hydratation", "energie", "protection solaire"],
        "pic_vente": "hydratation, energie, vitalite",
        "style_visuel": "summer Tunisia, sunshine, refreshing colors",
        "ton": "dynamique et estival",
        "horaire": "18h30",
        "contexte_sante": "La chaleur fatigue, deshydrate et baisse l'energie en fin de journee.",
        "saison": "ete",
        "emoji": "ETE",
    },
    "Pre-Ramadan - Preparation Corps": {
        "type": "saisonniere",
        "debut": (2, 15),
        "fin": (2, 28),
        "themes": ["energie", "digestion", "fer", "immunite"],
        "pic_vente": "preparation jeune, energie, fer",
        "style_visuel": "preparation Ramadan Tunisia, warm golden light",
        "ton": "spirituel et bienveillant",
        "horaire": "19h00",
        "contexte_sante": "Preparer son corps avant le jeune aide a mieux vivre la transition.",
        "saison": "pre_ramadan",
        "emoji": "RAMADAN",
    },
    "Fin d'Annee - Fatigue & Bilan": {
        "type": "saisonniere",
        "debut": (11, 15),
        "fin": (11, 30),
        "themes": ["anti-fatigue", "energie", "immunite", "stress"],
        "pic_vente": "anti-fatigue, bilan de sante, immunite automne",
        "style_visuel": "autumn Tunisia, falling leaves, cozy atmosphere",
        "ton": "reflexif et motivant",
        "horaire": "18h00",
        "contexte_sante": "La fin d'annee epuise, avec un pic de stress et de fatigue.",
        "saison": "automne",
        "emoji": "AUTOMNE",
    },
}


def prochaine_fete(df_tn: pd.DataFrame, today: date | None = None) -> pd.Series | None:
    today_ts = pd.Timestamp(today or date.today())
    futures = df_tn[df_tn["Date"] >= today_ts].sort_values("Date")
    if futures.empty:
        return None
    return futures.iloc[0]


def saisons_actives_ce_mois(mois: int | None = None, annee: int | None = None) -> list[tuple[str, dict[str, Any]]]:
    current = date.today()
    month = mois or current.month
    year = annee or current.year
    active: list[tuple[str, dict[str, Any]]] = []
    for name, info in SAISONS_MAPPING.items():
        start_month, start_day = info["debut"]
        end_month, end_day = info["fin"]
        start = date(year, start_month, start_day)
        end = date(year + 1, end_month, end_day) if end_month < start_month else date(year, end_month, end_day)
        probe = date(year, month, 15)
        if start <= probe <= end:
            active.append((name, info))
    return active


def _default_ton(category: str) -> str:
    if category == "institutionnel":
        return "solennel, chaleureux et sincere"
    if category == "religieuse":
        return "respectueux, familial et rassurant"
    return "professionnel et chaleureux"


def _default_horaire(category: str) -> str:
    if category == "religieuse":
        return "19h30"
    if category == "institutionnel":
        return "10h00"
    return "18h00"


def _message_institutionnel(holiday_name: str) -> str:
    return f"Vital Laboratories rend hommage a l'esprit de {holiday_name} avec respect et unite."


def _contexte_sante(category: str, peak: str) -> str:
    if category == "institutionnel":
        return "Communication corporate sans mise en avant produit."
    if category == "religieuse":
        return f"Periode sensible ou les besoins en {peak} deviennent plus visibles."
    return f"Campagne sante liee a la periode avec focus sur {peak}."


def _emoji_for_category(category: str) -> str:
    if category == "institutionnel":
        return "INSTITUTIONNEL"
    if category == "religieuse":
        return "RELIGIEUX"
    return "SAISON"
