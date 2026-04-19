from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class DataFiles:
    vital_catalogue: Path
    vital_encoded: Path
    reviews_analysis: Path
    reviews_clean: Path
    holidays: Path


@dataclass(slots=True)
class OutputFiles:
    posts_dataset: Path
    profils_csv: Path
    profils_json: Path
    fetes_mapping_json: Path
    rag_index: Path
    snapshot_json: Path


@dataclass(slots=True)
class Settings:
    project_root: Path
    data_dir: Path
    raw_data_dir: Path
    processed_data_dir: Path
    output_dir: Path
    docs_dir: Path
    files: DataFiles
    outputs: OutputFiles
    mistral_api_key: str | None = None
    hf_api_key: str | None = None
    gemini_api_key: str | None = None


def build_settings(project_root: Path) -> Settings:
    _load_local_env(project_root / ".env")

    data_dir = project_root / "data"
    raw_data_dir = data_dir / "raw"
    processed_data_dir = data_dir / "processed"
    output_dir = project_root / "outputs"
    docs_dir = project_root / "docs"

    for folder in (data_dir, raw_data_dir, processed_data_dir, output_dir, docs_dir):
        folder.mkdir(parents=True, exist_ok=True)

    files = DataFiles(
        vital_catalogue=_resolve_existing_file(
            project_root,
            raw_data_dir,
            "VITAL_data_cleaned_with_images.xlsx",
        ),
        vital_encoded=_resolve_existing_file(
            project_root,
            raw_data_dir,
            "VITAL_data_encoded.xlsx",
        ),
        reviews_analysis=_resolve_existing_file(
            project_root,
            raw_data_dir,
            "Vital_Products_Reviews_Analysis.xlsx",
        ),
        reviews_clean=_resolve_existing_file(
            project_root,
            raw_data_dir,
            "vital_reviews_clean.xlsx",
        ),
        holidays=_resolve_existing_file(
            project_root,
            raw_data_dir,
            "Global_Holidays_2025_2035_with_TN (3).csv",
        ),
    )

    outputs = OutputFiles(
        posts_dataset=output_dir / "dataset_posts.json",
        profils_csv=processed_data_dir / "profil_produits_final.csv",
        profils_json=processed_data_dir / "profils_mistral.json",
        fetes_mapping_json=processed_data_dir / "fetes_mapping.json",
        rag_index=processed_data_dir / "faiss_vital.index",
        snapshot_json=output_dir / "pipeline_snapshot.json",
    )

    return Settings(
        project_root=project_root,
        data_dir=data_dir,
        raw_data_dir=raw_data_dir,
        processed_data_dir=processed_data_dir,
        output_dir=output_dir,
        docs_dir=docs_dir,
        files=files,
        outputs=outputs,
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        hf_api_key=os.getenv("HF_API_KEY") or os.getenv("HF_TOKEN"),
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
    )


def _resolve_existing_file(project_root: Path, preferred_dir: Path, filename: str) -> Path:
    preferred_path = preferred_dir / filename
    root_path = project_root / filename
    if preferred_path.exists():
        return preferred_path
    if root_path.exists():
        return root_path
    return preferred_path


def _load_local_env(env_path: Path) -> None:
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
