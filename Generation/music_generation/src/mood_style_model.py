from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
import warnings

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

try:
    from .preprocess_holidays import STYLE_MAPPING_PATH, OccasionContext, load_style_mapping
except ImportError:
    from preprocess_holidays import STYLE_MAPPING_PATH, OccasionContext, load_style_mapping


ROOT_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT_DIR / "models"
MOOD_MODEL_PATH = MODELS_DIR / "target_mood_classifier.joblib"
GENRE_MODEL_PATH = MODELS_DIR / "genre_classifier.joblib"


@dataclass(frozen=True)
class StylePrediction:
    target_mood: str
    genre: str
    instruments: str
    tempo: str
    prompt_style: str
    source: str


def _training_text(df: pd.DataFrame) -> pd.Series:
    return (
        df["occasion_type"].fillna("")
        + " "
        + df["holiday_name"].fillna("")
        + " "
        + df["product_theme"].fillna("")
        + " "
        + df["prompt_style"].fillna("")
    )


def _make_classifier() -> Pipeline:
    return Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )


def train_models(
    mapping_path: Path = STYLE_MAPPING_PATH,
    mood_model_path: Path = MOOD_MODEL_PATH,
    genre_model_path: Path = GENRE_MODEL_PATH,
) -> Dict[str, Path]:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    mapping = load_style_mapping(mapping_path)
    text = _training_text(mapping)

    mood_model = _make_classifier()
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="The number of unique classes is greater than 50%")
        mood_model.fit(text, mapping["target_mood"])
    joblib.dump(mood_model, mood_model_path)

    genre_model = _make_classifier()
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="The number of unique classes is greater than 50%")
        genre_model.fit(text, mapping["genre"])
    joblib.dump(genre_model, genre_model_path)

    return {"mood": mood_model_path, "genre": genre_model_path}


def _load_or_train(path: Path, label: str) -> Pipeline:
    if not path.exists():
        train_models()
    return joblib.load(path)


def _normalize(value: str) -> str:
    return value.strip().lower()


def find_mapping_match(context: OccasionContext, mapping: pd.DataFrame) -> Optional[pd.Series]:
    holiday = _normalize(context.holiday_name)
    theme = _normalize(context.product_theme)

    exact = mapping[
        (mapping["holiday_name"].str.lower() == holiday)
        & (mapping["product_theme"].str.lower() == theme)
    ]
    if not exact.empty:
        return exact.iloc[0]

    holiday_only = mapping[mapping["holiday_name"].str.lower() == holiday]
    if not holiday_only.empty:
        return holiday_only.iloc[0]

    fuzzy_theme = mapping[
        mapping["holiday_name"].str.lower().apply(lambda value: value in holiday or holiday in value)
        & (mapping["product_theme"].str.lower() == theme)
    ]
    if not fuzzy_theme.empty:
        return fuzzy_theme.iloc[0]

    fuzzy_holiday = mapping[
        mapping["holiday_name"].str.lower().apply(lambda value: value in holiday or holiday in value)
    ]
    if not fuzzy_holiday.empty:
        return fuzzy_holiday.iloc[0]

    type_words = set(_normalize(context.occasion_type).replace(",", " ").split())
    for _, row in mapping.iterrows():
        mapped_type = set(_normalize(row["occasion_type"]).replace(",", " ").split())
        if type_words.intersection(mapped_type) and _normalize(row["product_theme"]) == theme:
            return row

    return None


def predict_style(context: OccasionContext, mapping_path: Path = STYLE_MAPPING_PATH) -> StylePrediction:
    mapping = load_style_mapping(mapping_path)
    matched = find_mapping_match(context, mapping)
    if matched is not None:
        return StylePrediction(
            target_mood=matched["target_mood"],
            genre=matched["genre"],
            instruments=matched["instruments"],
            tempo=matched["tempo"],
            prompt_style=matched["prompt_style"],
            source="mapping",
        )

    mood_model = _load_or_train(MOOD_MODEL_PATH, "target_mood")
    genre_model = _load_or_train(GENRE_MODEL_PATH, "genre")
    text = [context.model_text]

    mood = str(mood_model.predict(text)[0])
    genre = str(genre_model.predict(text)[0])
    genre_rows = mapping[mapping["genre"].str.lower() == genre.lower()]
    reference = genre_rows.iloc[0] if not genre_rows.empty else mapping.iloc[0]

    return StylePrediction(
        target_mood=mood,
        genre=genre,
        instruments=reference["instruments"],
        tempo=reference["tempo"],
        prompt_style="",
        source="ml_classifier",
    )
