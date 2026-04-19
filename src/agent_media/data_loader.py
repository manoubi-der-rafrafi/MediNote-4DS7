from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd

from .config import Settings


TEXT_COLUMNS = [
    "product_name",
    "therapeutic_theme",
    "gamme",
    "indications",
    "composition",
    "description",
    "usage_instructions",
]


@dataclass(slots=True)
class LoadedData:
    vital: pd.DataFrame
    encoded: pd.DataFrame
    analysis: pd.DataFrame
    reviews: pd.DataFrame
    reviews_clean: pd.DataFrame
    holidays: pd.DataFrame
    tunisian_holidays: pd.DataFrame


class DataLoader:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def load_all(self) -> LoadedData:
        vital = pd.read_excel(self.settings.files.vital_catalogue)
        encoded = pd.read_excel(self.settings.files.vital_encoded)
        analysis = pd.read_excel(self.settings.files.reviews_analysis)
        reviews = pd.read_excel(self.settings.files.reviews_clean)
        holidays = pd.read_csv(self.settings.files.holidays)

        reviews_clean = reviews[reviews["Commentaire"].apply(est_utilisable)].copy()
        reviews_clean.reset_index(drop=True, inplace=True)

        for column in TEXT_COLUMNS:
            if column in vital.columns:
                vital[column] = vital[column].apply(nettoyer)

        tunisian_holidays = holidays[holidays["Country"] == "TN"].copy()
        if "Date" in tunisian_holidays.columns:
            tunisian_holidays["Date"] = pd.to_datetime(tunisian_holidays["Date"])
            tunisian_holidays["month"] = tunisian_holidays["Date"].dt.month
            tunisian_holidays["day"] = tunisian_holidays["Date"].dt.day
            tunisian_holidays["year"] = tunisian_holidays["Date"].dt.year

        return LoadedData(
            vital=vital,
            encoded=encoded,
            analysis=analysis,
            reviews=reviews,
            reviews_clean=reviews_clean,
            holidays=holidays,
            tunisian_holidays=tunisian_holidays,
        )

    def summary(self, data: LoadedData) -> dict[str, int]:
        return {
            "catalogue_produits": len(data.vital),
            "produits_avec_image": int(data.vital.get("url_image", pd.Series(dtype=object)).notna().sum()),
            "produits_encodes": len(data.encoded),
            "analyses": len(data.analysis),
            "avis_bruts": len(data.reviews),
            "avis_utilisables": len(data.reviews_clean),
            "fetes_tunisie": len(data.tunisian_holidays),
        }


def est_utilisable(texte: object) -> bool:
    if pd.isna(texte):
        return False
    texte_clean = re.sub(r"[^\w\s]", "", str(texte)).strip()
    return len(texte_clean) >= 5


def nettoyer(texte: object) -> str:
    if pd.isna(texte):
        return ""
    return str(texte).strip()
