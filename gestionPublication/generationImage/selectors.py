from __future__ import annotations

import calendar
import difflib
from datetime import date
from functools import lru_cache
from typing import Any

from .config import (
    ANALYSIS_DATA_PATH,
    ANALYSIS_DATA_CSV_PATH,
    ENCODED_DATA_PATH,
    ENCODED_DATA_CSV_PATH,
    HOLIDAYS_DATA_PATH,
    REVIEWS_DATA_PATH,
    REVIEWS_DATA_CSV_PATH,
    VITAL_DATA_PATH,
    VITAL_DATA_CSV_PATH,
    ensure_required_data_files,
    get_pandas_module,
    has_excel_dependencies,
)


class ImageGenerationContextError(RuntimeError):
    pass


THEME_TO_IND = {
    "digestion": [
        "indication_digestion",
        "indication_estomac",
        "indication_foie",
        "therapeutic_theme_digestif",
        "indication_ballonnement",
    ],
    "estomac": [
        "indication_estomac",
        "indication_digestion",
        "therapeutic_theme_digestif",
    ],
    "foie": ["indication_foie", "therapeutic_theme_digestif"],
    "energie": [
        "indication_energie",
        "indication_fatigue",
        "therapeutic_theme_energie",
        "indication_fer",
        "indication_vitamine_b",
    ],
    "fatigue": [
        "indication_fatigue",
        "indication_energie",
        "therapeutic_theme_energie",
    ],
    "immunite": [
        "indication_immunite",
        "therapeutic_theme_immunite",
        "indication_vitamine_c",
        "indication_zinc",
    ],
    "stress": [
        "indication_stress",
        "indication_anxiete",
        "therapeutic_theme_stress",
    ],
    "sommeil": ["indication_sommeil", "therapeutic_theme_stress"],
    "anti fatigue": [
        "indication_fatigue",
        "indication_energie",
        "therapeutic_theme_energie",
    ],
    "hydratation": [
        "indication_hydratation",
        "therapeutic_theme_dermatologie",
    ],
    "protection solaire": [
        "indication_soleil",
        "therapeutic_theme_dermatologie",
    ],
    "allergies": ["indication_allergie", "therapeutic_theme_allergie"],
    "vitamines": [
        "indication_vitamine_c",
        "indication_vitamine_d",
        "indication_vitamine_b",
        "therapeutic_theme_vitamines",
    ],
}


FETES_MAPPING = {
    "New Year's Day": {
        "occasion_type": "fete",
        "themes": ["energie", "immunite", "vitamines"],
        "saison": "hiver",
        "style_visuel": "new year premium wellness celebration",
    },
    "Revolution Day": {
        "occasion_type": "fete",
        "themes": ["vitamines"],
        "saison": "hiver",
        "style_visuel": "patriotic premium brand poster",
    },
    "Independence Day": {
        "occasion_type": "fete",
        "themes": ["vitamines"],
        "saison": "printemps",
        "style_visuel": "patriotic premium brand poster",
    },
    "Martyrs' Day": {
        "occasion_type": "fete",
        "themes": ["vitamines"],
        "saison": "printemps",
        "style_visuel": "solemn patriotic premium brand poster",
    },
    "Ramadan": {
        "occasion_type": "fete",
        "themes": ["digestion", "energie", "immunite"],
        "saison": "printemps",
        "style_visuel": "Ramadan premium festive Tunisian atmosphere",
    },
    "Eid al-Fitr": {
        "occasion_type": "fete",
        "themes": ["digestion", "energie", "immunite"],
        "saison": "printemps",
        "style_visuel": "Eid al-Fitr premium festive Tunisian atmosphere",
    },
    "Eid al-Adha": {
        "occasion_type": "fete",
        "themes": ["digestion", "energie", "immunite"],
        "saison": "ete",
        "style_visuel": "Eid al-Adha premium festive Tunisian atmosphere",
    },
    "Islamic New Year": {
        "occasion_type": "fete",
        "themes": ["energie", "vitamines"],
        "saison": "ete",
        "style_visuel": "Islamic new year premium elegant campaign",
    },
    "Republic Day": {
        "occasion_type": "fete",
        "themes": ["vitamines"],
        "saison": "ete",
        "style_visuel": "patriotic premium brand poster",
    },
    "Mawlid": {
        "occasion_type": "fete",
        "themes": ["digestion", "energie", "vitamines"],
        "saison": "automne",
        "style_visuel": "Mawlid premium festive Tunisian atmosphere",
    },
    "Valentine's Day": {
        "occasion_type": "fete",
        "themes": ["energie", "vitamines"],
        "saison": "hiver",
        "style_visuel": "romantic premium wellness campaign, elegant red and white atmosphere",
    },
    "Mother's Day": {
        "occasion_type": "fete",
        "themes": ["energie", "vitamines", "immunite"],
        "saison": "printemps",
        "style_visuel": "motherhood celebration, warm family atmosphere, premium floral campaign",
    },
    "Father's Day": {
        "occasion_type": "fete",
        "themes": ["energie", "vitamines"],
        "saison": "ete",
        "style_visuel": "fatherhood celebration, elegant masculine premium atmosphere",
    },
    "Tunisian Women's Day": {
        "occasion_type": "fete",
        "themes": ["energie", "vitamines"],
        "saison": "ete",
        "style_visuel": "celebration of Tunisian women, elegant patriotic premium campaign",
    },
}


SAISONS_MAPPING = {
    "Periode Bac & Examens": {
        "occasion_type": "periode_examens",
        "themes": ["stress", "energie", "sommeil", "anti fatigue"],
        "saison": "printemps",
        "style_visuel": "exam period premium academic wellness atmosphere",
    },
    "hiver": {
        "occasion_type": "saison",
        "themes": ["immunite", "vitamines"],
        "saison": "hiver",
        "style_visuel": "winter health protection premium atmosphere",
    },
    "printemps": {
        "occasion_type": "saison",
        "themes": ["allergies", "vitamines"],
        "saison": "printemps",
        "style_visuel": "spring vitality premium atmosphere",
    },
    "ete": {
        "occasion_type": "saison",
        "themes": ["hydratation", "protection solaire", "energie"],
        "saison": "ete",
        "style_visuel": "summer wellness premium atmosphere",
    },
    "automne": {
        "occasion_type": "saison",
        "themes": ["immunite", "energie"],
        "saison": "automne",
        "style_visuel": "autumn wellness premium atmosphere",
    },
}


FETE_ALIASES = {
    "eid al fitr": "Eid al-Fitr",
    "aid el fitr": "Eid al-Fitr",
    "aid fitr": "Eid al-Fitr",
    "aid sghir": "Eid al-Fitr",
    "eid al adha": "Eid al-Adha",
    "aid el adha": "Eid al-Adha",
    "aid adha": "Eid al-Adha",
    "aid kbir": "Eid al-Adha",
    "ramadan": "Ramadan",
    "ramadhan": "Ramadan",
    "ramadhon": "Ramadan",
    "ramdhan": "Ramadan",
    "ramdane": "Ramadan",
    "ramadan karim": "Ramadan",
    "mawlid": "Mawlid",
    "mouled": "Mawlid",
    "moulid": "Mawlid",
    "new year": "New Year's Day",
    "new years day": "New Year's Day",
    "revolution day": "Revolution Day",
    "independence day": "Independence Day",
    "martyrs day": "Martyrs' Day",
    "republic day": "Republic Day",
    "islamic new year": "Islamic New Year",
    "saint valentin": "Valentine's Day",
    "st valentin": "Valentine's Day",
    "valentin": "Valentine's Day",
    "valentine": "Valentine's Day",
    "valentine s day": "Valentine's Day",
    "fete des meres": "Mother's Day",
    "fete de la mere": "Mother's Day",
    "mothers day": "Mother's Day",
    "mother s day": "Mother's Day",
    "fete des peres": "Father's Day",
    "fete du pere": "Father's Day",
    "fathers day": "Father's Day",
    "father s day": "Father's Day",
    "fete de la femme tunisienne": "Tunisian Women's Day",
    "journee de la femme tunisienne": "Tunisian Women's Day",
    "tunisian womens day": "Tunisian Women's Day",
}


MANUAL_FETE_DATE_RESOLVERS = {
    "Valentine's Day": lambda year: date(year, 2, 14),
    "Mother's Day": lambda year: _last_weekday_of_month(year, 5, calendar.SUNDAY),
    "Father's Day": lambda year: _nth_weekday_of_month(year, 6, calendar.SUNDAY, 3),
    "Tunisian Women's Day": lambda year: date(year, 8, 13),
}


def _normalize_text(value: str) -> str:
    return (
        str(value)
        .lower()
        .replace("Ã©", "e")
        .replace("Ã¨", "e")
        .replace("Ãª", "e")
        .replace("Ã ", "a")
        .replace("Ã»", "u")
        .replace("Ã®", "i")
        .replace("Ã¯", "i")
        .replace("Ã´", "o")
        .replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("à", "a")
        .replace("ù", "u")
        .replace("û", "u")
        .replace("î", "i")
        .replace("ï", "i")
        .replace("ô", "o")
        .replace("'", " ")
        .replace("-", " ")
        .strip()
    )


def _last_weekday_of_month(year: int, month: int, weekday: int) -> date:
    last_day = calendar.monthrange(year, month)[1]
    candidate = date(year, month, last_day)
    while candidate.weekday() != weekday:
        candidate = date(year, month, candidate.day - 1)
    return candidate


def _nth_weekday_of_month(year: int, month: int, weekday: int, occurrence: int) -> date:
    candidate = date(year, month, 1)
    while candidate.weekday() != weekday:
        candidate = date(year, month, candidate.day + 1)
    day_value = candidate.day + (occurrence - 1) * 7
    return date(year, month, day_value)


def _manual_holiday_date(holiday_name: str, reference_date: date) -> date | None:
    if holiday_name == "Ramadan":
        datasets = _load_data()
        df_tn = datasets["df_tn"]
        eid_matches = df_tn[
            df_tn["Holiday_Name"].astype(str).str.strip() == "Eid al-Fitr"
        ].sort_values("Date")
        future_eids = eid_matches[eid_matches["Date"].dt.date >= reference_date]
        selected = future_eids.iloc[0] if len(future_eids) > 0 else None
        if selected is None and len(eid_matches) > 0:
            selected = eid_matches.iloc[0]
        if selected is not None:
            return selected["Date"].date().fromordinal(
                selected["Date"].date().toordinal() - 29
            )

    resolver = MANUAL_FETE_DATE_RESOLVERS.get(holiday_name)
    if resolver is None:
        return None

    target = resolver(reference_date.year)
    if target < reference_date:
        target = resolver(reference_date.year + 1)
    return target


def _build_holiday_context(holiday_name: str, reference_date: date) -> dict[str, Any]:
    datasets = _load_data()
    df_tn = datasets["df_tn"]
    matches = df_tn[df_tn["Holiday_Name"].astype(str).str.strip() == holiday_name].sort_values(
        "Date"
    )
    future_matches = matches[matches["Date"].dt.date >= reference_date]
    selected = future_matches.iloc[0] if len(future_matches) > 0 else None
    if selected is None and len(matches) > 0:
        selected = matches.iloc[0]

    manual_date = _manual_holiday_date(holiday_name, reference_date)
    if selected is None and manual_date is None:
        raise ImageGenerationContextError(
            "Occasion reconnue mais absente du calendrier disponible: "
            f"{holiday_name}. Ajoutez-la au mapping ou au calendrier source."
        )

    info = dict(FETES_MAPPING[holiday_name])
    occasion_date = (
        selected["Date"].date()
        if selected is not None
        else manual_date
    )
    return {
        "occasion": holiday_name,
        "occasion_type": "fete",
        "date_occasion": occasion_date.isoformat(),
        "date_actuelle": reference_date.isoformat(),
        "saison": info.get("saison") or _infer_season(occasion_date),
        **info,
    }


def _resolve_holiday_name(normalized_query: str) -> str | None:
    holiday_name = FETE_ALIASES.get(normalized_query)
    if holiday_name is not None:
        return holiday_name

    for candidate in FETES_MAPPING:
        normalized_candidate = _normalize_text(candidate)
        if normalized_query and (
            normalized_query in normalized_candidate or normalized_candidate in normalized_query
        ):
            return candidate

    choices = list(FETE_ALIASES.keys()) + [_normalize_text(name) for name in FETES_MAPPING]
    fuzzy_matches = difflib.get_close_matches(normalized_query, choices, n=1, cutoff=0.78)
    if not fuzzy_matches:
        return None

    fuzzy_value = fuzzy_matches[0]
    return FETE_ALIASES.get(fuzzy_value, next(
        (
            candidate
            for candidate in FETES_MAPPING
            if _normalize_text(candidate) == fuzzy_value
        ),
        None,
    ))


def _supported_occasion_examples() -> str:
    examples = [
        "Ramadan",
        "Eid al-Fitr",
        "Eid al-Adha",
        "Mawlid",
        "Mother's Day",
        "Father's Day",
        "Valentine's Day",
        "Tunisian Women's Day",
        "Periode Bac & Examens",
        "hiver",
        "printemps",
        "ete",
        "automne",
    ]
    return ", ".join(examples)


@lru_cache(maxsize=1)
def _load_data() -> dict[str, Any]:
    ensure_required_data_files()
    pd = get_pandas_module()
    excel_available = has_excel_dependencies()

    def read_notebook_table(excel_path, csv_path):
        if csv_path.exists():
            return pd.read_csv(csv_path)
        if excel_available and excel_path.exists():
            return pd.read_excel(excel_path)
        if excel_path.exists():
            raise ImageGenerationContextError(
                "Le fichier de donnees existe seulement en Excel, mais openpyxl est absent: "
                f"{excel_path.name}. Generez d'abord le CSV de secours correspondant."
            )
        raise ImageGenerationContextError(
            "Fichier de donnees introuvable pour la methode notebook: "
            f"{excel_path.name} / {csv_path.name}."
        )

    df_vital = read_notebook_table(VITAL_DATA_PATH, VITAL_DATA_CSV_PATH)
    df_encoded = read_notebook_table(ENCODED_DATA_PATH, ENCODED_DATA_CSV_PATH)
    df_analyse = read_notebook_table(ANALYSIS_DATA_PATH, ANALYSIS_DATA_CSV_PATH)
    df_avis = read_notebook_table(REVIEWS_DATA_PATH, REVIEWS_DATA_CSV_PATH)
    df_holidays = pd.read_csv(HOLIDAYS_DATA_PATH)
    df_holidays["Date"] = pd.to_datetime(df_holidays["Date"])
    df_tn = df_holidays[df_holidays["Country"].astype(str).str.upper() == "TN"].copy()

    def trouver_analyse(nom: str):
        for mot in str(nom).split():
            if len(mot) <= 4:
                continue
            match = df_analyse[
                df_analyse["Produit"].astype(str).str.contains(
                    mot, case=False, na=False, regex=False
                )
            ]
            if len(match) > 0:
                return match.iloc[0]
        return None

    def trouver_avis(nom: str) -> list[str]:
        avis: list[str] = []
        for mot in str(nom).split():
            if len(mot) <= 4:
                continue
            matches = df_avis[
                df_avis["Produit"].astype(str).str.contains(
                    mot, case=False, na=False, regex=False
                )
            ]["Commentaire"].tolist()
            avis.extend(matches)
        return list(dict.fromkeys(str(item) for item in avis if str(item).strip()))[:5]

    profils = []
    for _, row in df_vital.iterrows():
        nom = str(row.get("product_name", "")).strip()
        if not nom:
            continue
        analyse = trouver_analyse(nom)
        profils.append(
            {
                "produit": nom,
                "theme": row.get("therapeutic_theme", ""),
                "note": row.get("rating"),
                "indications": row.get("indications", ""),
                "composition": row.get("composition", ""),
                "description": row.get("description", ""),
                "points_positifs": analyse["Points_Positifs"] if analyse is not None else "",
                "points_negatifs": analyse["Points_Negatifs"] if analyse is not None else "",
                "verdict": analyse["Verdict_Final"] if analyse is not None else "",
                "avis_clients": trouver_avis(nom),
                "url_image": row.get("url_image"),
                "url_product": row.get("url_product"),
            }
        )

    df_profils = pd.DataFrame(profils)
    return {
        "pd": pd,
        "df_encoded": df_encoded,
        "df_tn": df_tn,
        "df_profils": df_profils,
    }


def _infer_season(target_date: date) -> str:
    if target_date.month in (12, 1, 2):
        return "hiver"
    if target_date.month in (3, 4, 5):
        return "printemps"
    if target_date.month in (6, 7, 8):
        return "ete"
    return "automne"


def detect_next_occasion(reference_date: date | None = None) -> dict[str, Any]:
    datasets = _load_data()
    pd = datasets["pd"]
    df_tn = datasets["df_tn"]
    today = pd.Timestamp(reference_date or date.today())
    future_holidays = df_tn[df_tn["Date"] >= today].sort_values("Date")

    for _, row in future_holidays.iterrows():
        holiday_name = str(row["Holiday_Name"]).strip()
        if holiday_name not in FETES_MAPPING:
            continue
        return _build_holiday_context(holiday_name, today.date())

    raise ImageGenerationContextError("Aucune prochaine occasion compatible n'a ete trouvee.")


def detect_exam_period(reference_date: date | None = None) -> dict[str, Any]:
    today = reference_date or date.today()
    target_year = today.year if today <= date(today.year, 5, 15) else today.year + 1
    target_date = date(target_year, 5, 15)
    info = dict(SAISONS_MAPPING["Periode Bac & Examens"])
    return {
        "occasion": "Periode Bac & Examens",
        "occasion_type": "periode_examens",
        "date_occasion": target_date.isoformat(),
        "date_actuelle": today.isoformat(),
        "saison": info.get("saison", "printemps"),
        **info,
    }


def resolve_given_occasion(
    occasion_query: str,
    reference_date: date | None = None,
) -> dict[str, Any]:
    if not occasion_query or not str(occasion_query).strip():
        raise ImageGenerationContextError(
            "Une occasion doit etre fournie pour generation_mode=given_occasion."
        )

    normalized = _normalize_text(occasion_query)
    today = reference_date or date.today()

    if any(keyword in normalized for keyword in ("examen", "exam", "bac")):
        return detect_exam_period(today)

    if "saison en cours" in normalized or "current season" in normalized:
        current_season = _infer_season(today)
        info = dict(SAISONS_MAPPING[current_season])
        return {
            "occasion": current_season,
            "occasion_type": "saison",
            "date_occasion": today.isoformat(),
            "date_actuelle": today.isoformat(),
            "saison": current_season,
            **info,
        }

    for season_name, season_info in SAISONS_MAPPING.items():
        if _normalize_text(season_name) != normalized:
            continue
        info = dict(season_info)
        return {
            "occasion": season_name,
            "occasion_type": info.get("occasion_type", "saison"),
            "date_occasion": today.isoformat(),
            "date_actuelle": today.isoformat(),
            "saison": info.get("saison", season_name),
            **info,
        }

    holiday_name = _resolve_holiday_name(normalized)

    if holiday_name is None:
        raise ImageGenerationContextError(
            "Occasion non reconnue pour la generation d'image: "
            f"{occasion_query}. Exemples supportes: {_supported_occasion_examples()}"
        )

    return _build_holiday_context(holiday_name, today)


def _get_profile_row(product_name: str):
    df_profils = _load_data()["df_profils"]
    match = df_profils[df_profils["produit"] == product_name]
    return match.iloc[0] if len(match) > 0 else None


def _score_product_for_fete(product_name: str, fete_name: str) -> float:
    datasets = _load_data()
    df_encoded = datasets["df_encoded"]
    profile = _get_profile_row(product_name)
    match = df_encoded[df_encoded["product_name"] == product_name]
    if len(match) == 0 or profile is None:
        return 0.0

    row = match.iloc[0]
    fete_info = FETES_MAPPING.get(fete_name, {})
    score = 0.0
    max_score = 0.0

    for theme in fete_info.get("themes", []):
        normalized_theme = _normalize_text(theme)
        for indicator in THEME_TO_IND.get(normalized_theme, []):
            max_score += 3
            if indicator in df_encoded.columns and row.get(indicator) == 1:
                score += 3
        theme_col = f"therapeutic_theme_{normalized_theme.replace(' ', '_')}"
        max_score += 2
        if theme_col in df_encoded.columns and row.get(theme_col) == 1:
            score += 2

    max_score += 2
    try:
        note_value = float(profile.get("note"))
    except (TypeError, ValueError):
        note_value = None
    if note_value is not None:
        score += 2 if note_value >= 4.0 else 1 if note_value >= 3.0 else 0

    indications = (
        f"{profile.get('indications', '')} {profile.get('points_positifs', '')}"
    ).lower()
    product_theme = str(profile.get("theme", "")).lower()
    product_name_lower = product_name.lower()
    fete_lower = fete_name.lower()

    if any(word in fete_lower for word in ("eid", "aid", "ramadan", "mawlid", "fete")):
        max_score += 6
        if any(
            keyword in indications
            for keyword in ("digestion", "estomac", "foie", "repas", "viande", "ballonnement")
        ):
            score += 6
        if any(keyword in product_theme for keyword in ("digestif", "energie", "immunite", "vitamine")):
            score += 4
        if any(
            keyword in product_name_lower
            for keyword in ("eosine", "bebe", "cord", "ombilical", "fessier")
        ):
            score -= 3

    if "ramadan" in fete_lower:
        max_score += 6
        if any(
            keyword in product_name_lower or keyword in indications
            for keyword in (
                "antiacide",
                "acicalm",
                "phytodigest",
                "digestion",
                "digest",
                "estomac",
                "ballonnement",
                "menthe",
            )
        ):
            score += 6
        if any(
            keyword in product_name_lower
            for keyword in ("minceur", "coupe faim", "laxatif", "vitalax")
        ):
            score -= 4

    if max_score == 0:
        max_score = 10
        if any(keyword in product_theme for keyword in ("digestif", "energie", "immunite")):
            score += 5

    return round((score / max_score) * 10, 1)


def _score_product_for_saison(product_name: str, season_name: str) -> float:
    datasets = _load_data()
    df_encoded = datasets["df_encoded"]
    profile = _get_profile_row(product_name)
    match = df_encoded[df_encoded["product_name"] == product_name]
    if len(match) == 0 or profile is None:
        return 0.0

    row = match.iloc[0]
    season_info = SAISONS_MAPPING.get(season_name, {})
    score = 0.0
    max_score = 0.0

    for theme in season_info.get("themes", []):
        normalized_theme = _normalize_text(theme)
        for indicator in THEME_TO_IND.get(normalized_theme, []):
            max_score += 3
            if indicator in df_encoded.columns and row.get(indicator) == 1:
                score += 3
        theme_col = f"therapeutic_theme_{normalized_theme.replace(' ', '_')}"
        max_score += 2
        if theme_col in df_encoded.columns and row.get(theme_col) == 1:
            score += 2

    max_score += 2
    try:
        note_value = float(profile.get("note"))
    except (TypeError, ValueError):
        note_value = None
    if note_value is not None:
        score += 2 if note_value >= 4.0 else 1 if note_value >= 3.0 else 0

    if max_score == 0:
        max_score = 10
        product_theme = str(profile.get("theme", "")).lower()
        if any(keyword in product_theme for keyword in ("digestif", "energie", "immunite", "vitamines")):
            score += 4

    return round((score / max_score) * 10, 1)


def select_product_for_context(context: dict[str, Any]) -> dict[str, Any]:
    datasets = _load_data()
    df_profils = datasets["df_profils"]
    occasion_type = str(context.get("occasion_type", "")).strip().lower()
    scores = []

    for _, row in df_profils.iterrows():
        product_name = row["produit"]
        if occasion_type == "fete":
            score = _score_product_for_fete(product_name, context["occasion"])
        else:
            score = _score_product_for_saison(product_name, context["occasion"])

        scores.append(
            {
                "produit": product_name,
                "score": score,
                "theme": row.get("theme"),
                "note": row.get("note"),
                "points_positifs": row.get("points_positifs"),
                "verdict": row.get("verdict"),
                "url_image": row.get("url_image"),
                "product_url": row.get("url_product"),
            }
        )

    ranked = sorted(
        scores,
        key=lambda item: (
            item["score"],
            _product_preference_bonus(item, context),
            _safe_float(item.get("note")),
        ),
        reverse=True,
    )
    best = next((item for item in ranked if item["score"] > 0), ranked[0] if ranked else None)
    if best is None:
        raise ImageGenerationContextError("Aucun produit n'a ete classe pour cette occasion.")
    return best


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _product_preference_bonus(item: dict[str, Any], context: dict[str, Any]) -> float:
    product_name = str(item.get("produit", "")).lower()
    occasion = str(context.get("occasion", "")).lower()
    bonus = 0.0

    if str(context.get("occasion_type", "")).strip().lower() == "fete" and "ramadan" in occasion:
        if any(keyword in product_name for keyword in ("antiacide", "acicalm", "phytodigest", "menthe")):
            bonus += 3.0
        if any(keyword in product_name for keyword in ("minceur", "coupe faim", "laxatif", "vitalax")):
            bonus -= 3.0

    if item.get("url_image"):
        bonus += 0.2
    if item.get("product_url"):
        bonus += 0.2
    return bonus
