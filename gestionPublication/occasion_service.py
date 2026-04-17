import csv
from datetime import date, datetime
from pathlib import Path
from typing import Any

from hijridate import Gregorian, Hijri


BASE_DIR = Path(__file__).resolve().parents[2]
PRODUCTS_CSV_PATH = BASE_DIR / "produit" / "data" / "articles_occasions_brouillon.csv"


class OccasionServiceError(RuntimeError):
    pass


def last_sunday_of_may(year: int) -> date:
    current = date(year, 5, 31)
    while current.weekday() != 6:
        current = current.replace(day=current.day - 1)
    return current


def third_sunday_of_june(year: int) -> date:
    current = date(year, 6, 1)
    while current.weekday() != 6:
        current = current.replace(day=current.day + 1)
    return current.replace(day=current.day + 14)


def to_date(hijri_year: int, hijri_month: int, hijri_day: int) -> date:
    gregorian = Hijri(hijri_year, hijri_month, hijri_day).to_gregorian()
    return date(gregorian.year, gregorian.month, gregorian.day)


def infer_season(target_date: date) -> str:
    month = target_date.month
    if month in (12, 1, 2):
        return "hiver"
    if month in (3, 4, 5):
        return "printemps"
    if month in (6, 7, 8):
        return "ete"
    return "automne"


def build_occasions(reference_date: date | None = None) -> list[dict[str, Any]]:
    today = reference_date or date.today()
    occasions: list[dict[str, Any]] = []

    for year in (today.year, today.year + 1):
        occasions.extend(
            [
                {"occasion": "saint_valentin", "date_occasion": date(year, 2, 14)},
                {"occasion": "fete_meres", "date_occasion": last_sunday_of_may(year)},
                {"occasion": "fete_peres", "date_occasion": third_sunday_of_june(year)},
                {"occasion": "fete_femme_tunisienne", "date_occasion": date(year, 8, 13)},
                {"occasion": "preparation_examens", "date_occasion": date(year, 5, 15)},
                {"occasion": "saison_examens", "date_occasion": date(year, 6, 10)},
            ]
        )

    current_hijri_year = Gregorian(today.year, today.month, today.day).to_hijri().year
    for hijri_year in range(current_hijri_year, current_hijri_year + 3):
        occasions.extend(
            [
                {"occasion": "ras_el_am_hijri", "date_occasion": to_date(hijri_year, 1, 1)},
                {"occasion": "achoura", "date_occasion": to_date(hijri_year, 1, 10)},
                {"occasion": "mouled", "date_occasion": to_date(hijri_year, 3, 12)},
                {"occasion": "ramadan", "date_occasion": to_date(hijri_year, 9, 1)},
                {"occasion": "aid_el_fitr", "date_occasion": to_date(hijri_year, 10, 1)},
                {"occasion": "aid_el_adha", "date_occasion": to_date(hijri_year, 12, 10)},
            ]
        )

    return occasions


class OccasionService:
    def __init__(self, products_csv_path: Path | None = None) -> None:
        self.products_csv_path = products_csv_path or PRODUCTS_CSV_PATH

    def get_next_occasion_with_product(
        self,
        reference_date: date | None = None,
    ) -> dict[str, Any]:
        today = reference_date or date.today()
        future_occasions = [
            item for item in build_occasions(today) if item["date_occasion"] >= today
        ]
        if not future_occasions:
            raise OccasionServiceError("Aucune occasion future n'a ete trouvee.")

        closest = min(future_occasions, key=lambda item: item["date_occasion"])
        season = infer_season(closest["date_occasion"])
        product = self._select_product_for_occasion(closest["occasion"], season)

        return {
            "occasion": closest["occasion"],
            "date_occasion": closest["date_occasion"].isoformat(),
            "saison": season,
            "date_actuelle": today.isoformat(),
            **product,
        }

    def _load_products(self) -> list[dict[str, str]]:
        if not self.products_csv_path.exists():
            raise OccasionServiceError(
                f"Le fichier produits est introuvable: {self.products_csv_path}"
            )

        with self.products_csv_path.open(encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            return [row for row in reader]

    def _select_product_for_occasion(self, occasion: str, season: str) -> dict[str, str]:
        matching_rows = [
            row
            for row in self._load_products()
            if row.get("occasion") == occasion and row.get("saison") in (season, "toutes")
        ]
        if not matching_rows:
            raise OccasionServiceError(
                f"Aucun produit n'a ete trouve pour l'occasion '{occasion}' et la saison '{season}'."
            )

        deduplicated: dict[str, dict[str, str]] = {}
        for row in sorted(
            matching_rows,
            key=lambda item: (
                -self._safe_int(item.get("score_priorite")),
                str(item.get("code_article", "")),
            ),
        ):
            code_article = row.get("code_article", "")
            if code_article and code_article not in deduplicated:
                deduplicated[code_article] = row

        best_row = next(iter(deduplicated.values())) if deduplicated else matching_rows[0]
        produit = best_row.get("nom_article_corrige") or best_row.get("nom_article") or ""

        return {
            "code_article": best_row.get("code_article", ""),
            "produit": produit,
            "produit_source": best_row.get("nom_article", ""),
            "product_url": best_row.get("product_url", ""),
            "image_url": best_row.get("image_url", ""),
            "score_priorite": str(best_row.get("score_priorite", "")),
        }

    @staticmethod
    def _safe_int(value: str | None) -> int:
        try:
            return int(float(value or "0"))
        except (TypeError, ValueError):
            return 0
