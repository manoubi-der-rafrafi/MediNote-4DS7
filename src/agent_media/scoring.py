from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import pandas as pd

from .calendar_utils import SAISONS_MAPPING
from .mappings import THEME_TO_IND, normalize_theme


@dataclass(slots=True)
class ScoringEngine:
    df_encoded: pd.DataFrame
    df_profils: pd.DataFrame
    fetes_mapping: dict[str, dict[str, Any]]

    def scorer_produit_pour_fete(self, nom_produit: str, nom_fete: str) -> float:
        match = self.df_encoded[self.df_encoded["product_name"] == nom_produit]
        if match.empty:
            return 0.0

        row = match.iloc[0]
        fete_info = self.fetes_mapping.get(nom_fete, {})
        fete_lower = normalize_theme(nom_fete)
        score = 0.0
        max_score = 0.0

        for theme in fete_info.get("themes", []):
            normalized = normalize_theme(str(theme))
            for ind in THEME_TO_IND.get(normalized, []):
                max_score += 3
                if ind in self.df_encoded.columns and row.get(ind) == 1:
                    score += 3
            col = f"therapeutic_theme_{normalized.replace('-', '_').replace(' ', '_')}"
            max_score += 2
            if col in self.df_encoded.columns and row.get(col) == 1:
                score += 2

        max_score += 2
        note = row.get("rating")
        if pd.notna(note):
            if float(note) >= 4.0:
                score += 2
            elif float(note) >= 3.0:
                score += 1

        indications = f"{row.get('indications', '')} {row.get('points_positifs', '')}".lower()
        theme_prod = normalize_theme(str(row.get("therapeutic_theme", "")))
        prod_name = normalize_theme(str(nom_produit))
        if any(word in fete_lower for word in ["eid", "aid", "ramadan", "mawlid", "sacrifice", "fete"]):
            max_score += 6
            if any(term in indications for term in ["digestion", "estomac", "foie", "repas", "viande", "ballonnement"]):
                score += 6
            if any(term in theme_prod for term in ["digestif", "energie", "immunite", "vitamine"]):
                score += 4
            if any(term in prod_name for term in ["eosine", "bebe", "cord", "ombilical", "fessier"]):
                score -= 3

        if max_score == 0:
            max_score = 10
            if any(term in theme_prod for term in ["digestif", "energie", "immunite"]):
                score += 5

        return round((score / max_score) * 10, 1)

    def top_produits_pour_fete(self, nom_fete: str, top_k: int = 5) -> pd.DataFrame:
        fete_info = self.fetes_mapping.get(nom_fete, {})
        if fete_info.get("type") == "institutionnel":
            return pd.DataFrame()

        scores: list[dict[str, Any]] = []
        for _, row in self.df_profils.iterrows():
            value = self.scorer_produit_pour_fete(str(row["produit"]), nom_fete)
            scores.append(
                {
                    "produit": row["produit"],
                    "score": value,
                    "theme": row["theme"],
                    "note": row["note"],
                    "points_positifs": row["points_positifs"],
                    "verdict": row["verdict"],
                    "url_image": row["url_image"],
                }
            )
        result = pd.DataFrame(scores).sort_values("score", ascending=False)
        return result[result["score"] > 0].head(top_k)

    def scorer_produit_pour_saison(self, nom_produit: str, nom_saison: str) -> float:
        match = self.df_encoded[self.df_encoded["product_name"] == nom_produit]
        if match.empty:
            return 0.0

        row = match.iloc[0]
        saison_info = SAISONS_MAPPING.get(nom_saison, {})
        score = 0.0
        max_score = 0.0
        for theme in saison_info.get("themes", []):
            normalized = normalize_theme(str(theme))
            for ind in THEME_TO_IND.get(normalized, []):
                max_score += 3
                if ind in self.df_encoded.columns and row.get(ind) == 1:
                    score += 3
            col = f"therapeutic_theme_{normalized.replace('-', '_').replace(' ', '_')}"
            max_score += 2
            if col in self.df_encoded.columns and row.get(col) == 1:
                score += 2

        max_score += 2
        note = row.get("rating")
        if pd.notna(note):
            if float(note) >= 4.0:
                score += 2
            elif float(note) >= 3.0:
                score += 1

        if max_score == 0:
            max_score = 10
            theme_prod = normalize_theme(str(row.get("therapeutic_theme", "")))
            if any(term in theme_prod for term in ["digestif", "energie", "immunite", "vitamines"]):
                score += 4
        return round((score / max_score) * 10, 1)

    def top_produits_pour_saison(self, nom_saison: str, top_k: int = 5) -> pd.DataFrame:
        scores: list[dict[str, Any]] = []
        for _, row in self.df_profils.iterrows():
            value = self.scorer_produit_pour_saison(str(row["produit"]), nom_saison)
            scores.append(
                {
                    "produit": row["produit"],
                    "score": value,
                    "theme": row["theme"],
                    "note": row["note"],
                    "points_positifs": row["points_positifs"],
                    "verdict": row["verdict"],
                    "url_image": row["url_image"],
                }
            )
        result = pd.DataFrame(scores).sort_values("score", ascending=False)
        return result[result["score"] > 0].head(top_k)

    def calendrier_mensuel(self, df_tn: pd.DataFrame, mois: int | None = None, annee: int | None = None) -> dict[str, Any]:
        today = date.today()
        month = mois or today.month
        year = annee or today.year
        fetes_mois = df_tn[(df_tn["Date"].dt.month == month) & (df_tn["year"] == year)].copy()
        lignes_fetes: list[dict[str, Any]] = []
        for _, fete in fetes_mois.iterrows():
            fete_nom = str(fete["Holiday_Name"])
            fete_info = self.fetes_mapping.get(fete_nom, {})
            top1 = self.top_produits_pour_fete(fete_nom, top_k=1)
            lignes_fetes.append(
                {
                    "date": str(fete["Date"])[:10],
                    "fete": fete_nom,
                    "type": fete_info.get("type", "?"),
                    "produit_recommande": None if top1.empty else top1.iloc[0]["produit"],
                    "score": None if top1.empty else float(top1.iloc[0]["score"]),
                }
            )
        return {"mois": month, "annee": year, "fetes": lignes_fetes}
