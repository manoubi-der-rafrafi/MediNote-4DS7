from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
HOLIDAYS_PATH = DATA_DIR / "Global_Holidays_2025_2035_with_TN.csv"
STYLE_MAPPING_PATH = DATA_DIR / "music_style_mapping.csv"


@dataclass(frozen=True)
class OccasionContext:
    holiday_name: str
    product_theme: str
    occasion_type: str
    country: str
    year: Optional[int]
    date: str
    local_name: str
    description: str

    @property
    def model_text(self) -> str:
        return " ".join(
            [
                self.holiday_name,
                self.local_name,
                self.occasion_type,
                self.product_theme,
                self.description,
            ]
        ).strip()


def _clean_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def load_holidays(path: Path = HOLIDAYS_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    expected = {"Country", "Year", "Date", "Holiday_Name", "Local_Name", "Type", "Description"}
    missing = expected.difference(df.columns)
    if missing:
        raise ValueError(f"Holiday dataset missing columns: {sorted(missing)}")
    for column in ["Country", "Date", "Holiday_Name", "Local_Name", "Type", "Description"]:
        df[column] = df[column].fillna("").astype(str).str.strip()
    return df


def load_style_mapping(path: Path = STYLE_MAPPING_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    expected = {
        "occasion_type",
        "holiday_name",
        "product_theme",
        "target_mood",
        "instruments",
        "tempo",
        "genre",
        "prompt_style",
    }
    missing = expected.difference(df.columns)
    if missing:
        raise ValueError(f"Style mapping dataset missing columns: {sorted(missing)}")
    for column in expected:
        df[column] = df[column].fillna("").astype(str).str.strip()
    return df


def find_holiday(
    holiday_query: str,
    holidays: pd.DataFrame,
    country: Optional[str] = None,
    year: Optional[int] = None,
) -> pd.Series:
    query = holiday_query.strip().lower()
    candidates = holidays.copy()

    if country:
        candidates = candidates[candidates["Country"].str.lower() == country.strip().lower()]
    if year:
        candidates = candidates[candidates["Year"] == int(year)]

    exact = candidates[candidates["Holiday_Name"].str.lower() == query]
    if exact.empty:
        exact = candidates[candidates["Local_Name"].str.lower() == query]
    if not exact.empty:
        return exact.iloc[0]

    contains = candidates[
        candidates["Holiday_Name"].str.lower().str.contains(query, regex=False)
        | candidates["Local_Name"].str.lower().str.contains(query, regex=False)
    ]
    if not contains.empty:
        return contains.iloc[0]

    all_matches = holidays[
        holidays["Holiday_Name"].str.lower().str.contains(query, regex=False)
        | holidays["Local_Name"].str.lower().str.contains(query, regex=False)
    ]
    if not all_matches.empty:
        return all_matches.iloc[0]

    raise ValueError(f"No holiday found for query: {holiday_query!r}")


def build_occasion_context(
    holiday: str,
    product_theme: str,
    country: Optional[str] = None,
    year: Optional[int] = None,
    holidays_path: Path = HOLIDAYS_PATH,
) -> OccasionContext:
    holidays = load_holidays(holidays_path)
    row = find_holiday(holiday, holidays, country=country, year=year)
    return OccasionContext(
        holiday_name=_clean_text(row["Holiday_Name"]),
        product_theme=product_theme.strip().lower(),
        occasion_type=_clean_text(row["Type"]),
        country=_clean_text(row["Country"]),
        year=int(row["Year"]) if not pd.isna(row["Year"]) else None,
        date=_clean_text(row["Date"]),
        local_name=_clean_text(row["Local_Name"]),
        description=_clean_text(row["Description"]),
    )

