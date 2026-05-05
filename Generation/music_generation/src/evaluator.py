from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = ROOT_DIR / "outputs"
METADATA_PATH = OUTPUTS_DIR / "generated_music_metadata.csv"
REPORT_PATH = OUTPUTS_DIR / "evaluation_report.csv"


STYLE_FIELDS = ["target_mood", "genre", "instruments", "tempo"]
PROMPT_TERMS = ["instrumental", "tempo", "no vocals", "social media"]


def _has_value(value: object) -> bool:
    return bool(str(value).strip()) and str(value).strip().lower() != "nan"


def style_coverage_score(row: pd.Series) -> float:
    covered = sum(1 for field in STYLE_FIELDS if _has_value(row.get(field, "")))
    return round(covered / len(STYLE_FIELDS), 3)


def prompt_completeness_score(prompt: str, row: pd.Series) -> float:
    prompt_lower = str(prompt).lower()
    checks = [
        _has_value(row.get("holiday_name", "")) and str(row["holiday_name"]).lower() in prompt_lower,
        _has_value(row.get("product_theme", "")) and str(row["product_theme"]).lower() in prompt_lower,
        _has_value(row.get("target_mood", "")) and str(row["target_mood"]).lower() in prompt_lower,
        _has_value(row.get("genre", "")) and str(row["genre"]).lower() in prompt_lower,
    ]
    checks.extend(term in prompt_lower for term in PROMPT_TERMS)
    return round(sum(checks) / len(checks), 3)


def generated_file_exists(path_value: object) -> bool:
    path = str(path_value).strip()
    return bool(path) and path.lower() != "nan" and Path(path).exists()


def evaluate_metadata(metadata_path: Path = METADATA_PATH, report_path: Path = REPORT_PATH) -> pd.DataFrame:
    if not metadata_path.exists():
        raise FileNotFoundError(f"No metadata file found at {metadata_path}")

    metadata = pd.read_csv(metadata_path)
    rows: List[Dict[str, object]] = []
    for _, row in metadata.iterrows():
        prompt = str(row.get("prompt", ""))
        coverage = style_coverage_score(row)
        completeness = prompt_completeness_score(prompt, row)
        file_exists = generated_file_exists(row.get("audio_path", ""))
        rows.append(
            {
                "run_id": row.get("run_id", ""),
                "holiday_name": row.get("holiday_name", ""),
                "product_theme": row.get("product_theme", ""),
                "style_source": row.get("style_source", ""),
                "style_coverage_score": coverage,
                "prompt_completeness_score": completeness,
                "generated_file_exists": file_exists,
                "overall_score": round((coverage + completeness + float(file_exists)) / 3, 3),
            }
        )

    report = pd.DataFrame(rows)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(report_path, index=False)
    return report


def print_report(report: pd.DataFrame) -> None:
    if report.empty:
        print("No generated music rows to evaluate.")
        return
    print(report.to_string(index=False))
    print(f"\nSaved evaluation report to: {REPORT_PATH}")


if __name__ == "__main__":
    print_report(evaluate_metadata())

