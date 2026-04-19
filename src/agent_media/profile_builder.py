from __future__ import annotations

import json

import pandas as pd

from .data_loader import LoadedData


def trouver_analyse(nom: str, df_analyse: pd.DataFrame) -> pd.Series | None:
    for mot in nom.split():
        if len(mot) <= 4:
            continue
        match = df_analyse[df_analyse["Produit"].str.contains(mot, case=False, na=False, regex=False)]
        if not match.empty:
            return match.iloc[0]
    return None


def trouver_avis(nom: str, df_avis_clean: pd.DataFrame) -> list[str]:
    avis: list[str] = []
    for mot in nom.split():
        if len(mot) <= 4:
            continue
        matches = df_avis_clean[
            df_avis_clean["Produit"].str.contains(mot, case=False, na=False, regex=False)
        ]["Commentaire"].tolist()
        avis.extend(matches)
    return list(dict.fromkeys(avis))[:5]


def construire_profils(data: LoadedData) -> pd.DataFrame:
    profils: list[dict[str, object]] = []
    for _, row in data.vital.iterrows():
        nom = str(row["product_name"])
        analyse = trouver_analyse(nom, data.analysis)
        avis = trouver_avis(nom, data.reviews_clean)
        profils.append(
            {
                "produit": nom,
                "gamme": row.get("gamme", ""),
                "theme": row.get("therapeutic_theme", ""),
                "forme": row.get("form_clean", ""),
                "prix": row.get("price"),
                "note": row.get("rating"),
                "indications": row.get("indications", ""),
                "composition": row.get("composition", ""),
                "description": row.get("description", ""),
                "posologie": row.get("usage_instructions", ""),
                "contre_indications": row.get("contraindications", ""),
                "points_positifs": analyse["Points_Positifs"] if analyse is not None else "",
                "points_negatifs": analyse["Points_Negatifs"] if analyse is not None else "",
                "verdict": analyse["Verdict_Final"] if analyse is not None else "",
                "note_intelligente": analyse["Note_Intelligente_Sur_5"] if analyse is not None else None,
                "avis_clients": avis,
                "url_image": row.get("url_image"),
                "url_product": row.get("url_product"),
                "lifecycle": row.get("lifecycle_stage", ""),
            }
        )
    df_profils = pd.DataFrame(profils)
    df_profils["texte_rag"] = df_profils.apply(construire_texte_rag, axis=1)
    return df_profils


def construire_texte_rag(row: pd.Series) -> str:
    avis_str = " | ".join(row["avis_clients"][:3]) if row["avis_clients"] else ""
    return (
        f"Produit: {row['produit']}\n"
        f"Gamme: {row['gamme']}\n"
        f"Theme: {row['theme']}\n"
        f"Indications: {row['indications']}\n"
        f"Composition: {row['composition']}\n"
        f"Points positifs: {row['points_positifs']}\n"
        f"Verdict: {row['verdict']}\n"
        f"Avis clients: {avis_str}"
    )


def profils_to_json_ready(df_profils: pd.DataFrame) -> list[dict[str, object]]:
    data: list[dict[str, object]] = []
    for _, row in df_profils.iterrows():
        data.append(
            {
                "produit": row["produit"],
                "gamme": row["gamme"],
                "theme": row["theme"],
                "indications": row["indications"],
                "composition": row["composition"],
                "points_positifs": row["points_positifs"],
                "points_negatifs": row["points_negatifs"],
                "verdict": row["verdict"],
                "note": float(row["note"]) if pd.notna(row["note"]) else None,
                "url_image": row.get("url_image"),
                "url_product": row.get("url_product"),
                "avis_clients": row["avis_clients"][:3],
            }
        )
    return data


def profils_to_csv_frame(df_profils: pd.DataFrame) -> pd.DataFrame:
    frame = df_profils.copy()
    frame["avis_clients"] = frame["avis_clients"].apply(json.dumps)
    return frame
