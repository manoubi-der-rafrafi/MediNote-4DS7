import os
from functools import lru_cache
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = Path(__file__).resolve().parent / "ranim data"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"

VITAL_DATA_PATH = DATA_DIR / "VITAL_data_cleaned_with_images.xlsx"
ENCODED_DATA_PATH = DATA_DIR / "VITAL_data_encoded.xlsx"
ANALYSIS_DATA_PATH = DATA_DIR / "Vital_Products_Reviews_Analysis.xlsx"
REVIEWS_DATA_PATH = DATA_DIR / "vital_reviews_clean.xlsx"
HOLIDAYS_DATA_PATH = DATA_DIR / "Global_Holidays_2025_2035_with_TN (3) (1).csv"
VITAL_DATA_CSV_PATH = DATA_DIR / "VITAL_data_cleaned_with_images.csv"
ENCODED_DATA_CSV_PATH = DATA_DIR / "VITAL_data_encoded.csv"
ANALYSIS_DATA_CSV_PATH = DATA_DIR / "Vital_Products_Reviews_Analysis.csv"
REVIEWS_DATA_CSV_PATH = DATA_DIR / "vital_reviews_clean.csv"

HF_IMAGE_MODEL_NAME = "black-forest-labs/FLUX.1-schnell"
IMAGE_OUTPUT_FILENAME = "generated_image.png"
METADATA_FILENAME = "metadata.json"
IMAGE_SIZE = (1024, 1024)


class ImageGenerationConfigError(RuntimeError):
    pass


def get_hf_api_key() -> str:
    api_key = os.getenv("HF_API_KEY") or os.getenv("HF_TOKEN")
    if not api_key or not api_key.strip():
        raise ImageGenerationConfigError(
            "La variable d'environnement HF_API_KEY ou HF_TOKEN est absente ou vide."
        )
    return api_key.strip()


def get_mistral_api_key() -> str | None:
    api_key = os.getenv("MISTRAL_API_KEY")
    return api_key.strip() if api_key and api_key.strip() else None


def get_gemini_api_key() -> str | None:
    api_key = os.getenv("GEMINI_API_KEY")
    return api_key.strip() if api_key and api_key.strip() else None


@lru_cache(maxsize=1)
def get_pandas_module():
    try:
        import pandas as pd
    except ImportError as exc:
        raise ImageGenerationConfigError(
            "Le module pandas est requis pour la generation d'image."
        ) from exc
    return pd


def has_excel_dependencies() -> bool:
    try:
        import openpyxl  # noqa: F401
    except ImportError:
        return False
    return True


def ensure_required_data_files() -> None:
    missing = [
        str(path)
        for path in (HOLIDAYS_DATA_PATH,)
        if not path.exists()
    ]
    excel_or_csv_groups = (
        (VITAL_DATA_PATH, VITAL_DATA_CSV_PATH),
        (ENCODED_DATA_PATH, ENCODED_DATA_CSV_PATH),
        (ANALYSIS_DATA_PATH, ANALYSIS_DATA_CSV_PATH),
        (REVIEWS_DATA_PATH, REVIEWS_DATA_CSV_PATH),
    )
    for excel_path, csv_path in excel_or_csv_groups:
        if not excel_path.exists() and not csv_path.exists():
            missing.append(f"{excel_path} ou {csv_path}")
    if missing:
        raise ImageGenerationConfigError(
            "Fichiers de donnees image introuvables: " + ", ".join(missing)
        )
