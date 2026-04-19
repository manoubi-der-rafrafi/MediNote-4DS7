import os
import pandas as pd
import numpy as np

# Resolve path relative to this file's directory
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(_BASE_DIR, "NEW_vital_data_enriched_UPDATED.xlsx")

# ─────────────────────────────────────────────────────────────────────────────
# PASSAGE BUILDER — 4 passages spécialisés par produit
# Chaque passage cible un angle de recherche différent → profondeur maximale
# ─────────────────────────────────────────────────────────────────────────────

def build_clinical_passage(row) -> str:
    """Passage clinique : composition, indications, contre-indications, forme."""
    parts = [
        f"PRODUIT: {row.get('product_name', '')}",
        f"CLASSE: {row.get('product_class', '')}",
        f"FORME GALÉNIQUE: {row.get('form', '')}",
        f"THÈME THÉRAPEUTIQUE: {row.get('therapeutic_theme', '')}",
        f"INDICATIONS: {str(row.get('indications', ''))[:400]}",
        f"CONTRE-INDICATIONS: {str(row.get('contraindications', ''))[:300]}",
        f"COMPOSITION: {str(row.get('composition', ''))[:400]}",
        f"DÉFINITION: {str(row.get('product_definition', ''))[:300]}",
    ]
    return '\n'.join([p for p in parts if p.split(': ', 1)[-1].strip() not in ['', 'nan', 'None']])


def build_commercial_passage(row) -> str:
    """Passage commercial : prix, promo, présence, gamme, tendance."""
    discount_pct = 0.0
    try:
        p, pp = float(row.get('price', 0)), float(row.get('promo_price', 0))
        if p > 0:
            discount_pct = round((p - pp) / p * 100, 1)
    except (ValueError, TypeError):
        pass

    price_band = "premium" if float(row.get('price', 0)) > 30 else \
                 "mid-range" if float(row.get('price', 0)) > 12 else "entrée de gamme"

    parts = [
        f"PRODUIT: {row.get('product_name', '')}",
        f"GAMME: {row.get('gamme', '')}",
        f"PRIX: {row.get('price', '')} TND  |  PRIX PROMO: {row.get('promo_price', '')} TND",
        f"REMISE PROMO: {discount_pct}%",
        f"SEGMENT PRIX: {price_band}",
        f"FRÉQUENCE PROMO: {row.get('promo_frequency', '')}",
        f"PRÉSENCE MARCHÉ: {row.get('presence_count', '')} points",
        f"NOTE CLIENT: {row.get('rating', '')} / 5  |  AVIS: {row.get('review_count', '')}",
        f"FOURCHETTE MARCHÉ: {row.get('price_min', '')} – {row.get('price_max', '')} TND",
    ]
    return '\n'.join([p for p in parts if p.split(': ', 1)[-1].strip() not in ['', 'nan', 'None', '0.0%']])


def build_strategic_passage(row) -> str:
    """Passage stratégique : cycle de vie, concurrence, risques, opportunités."""
    parts = [
        f"PRODUIT: {row.get('product_name', '')}",
        f"GAMME: {row.get('gamme', '')}",
        f"STOCK: {row.get('stock_status', '')}",
        f"TENDANCE CATÉGORIE: {row.get('global_category_trend', '')}",
        f"DENSITÉ CONCURRENTIELLE: {row.get('competitor_density', '')}",
        f"RISQUE SUBSTITUTION: {row.get('substitution_risk', '')}",
        f"CYCLE DE VIE: {row.get('lifecycle_stage_predicted', '')}",
        f"SCORE OPPORTUNITÉ: {row.get('opportunity_score', '')} / 8",
        f"SCORE RISQUE: {row.get('risk_score', '')} / 8",
        f"MOMENTUM SCORE: {row.get('momentum_score', '')}",
    ]
    return '\n'.join([p for p in parts if p.split(': ', 1)[-1].strip() not in ['', 'nan', 'None']])


def build_full_passage(row) -> str:
    """Passage complet enrichi — utilisé pour TF-IDF et BM25."""
    parts = [
        f"PRODUIT: {row.get('product_name', '')}",
        f"GAMME: {row.get('gamme', '')}  |  CLASSE: {row.get('product_class', '')}",
        f"THÈME THÉRAPEUTIQUE: {row.get('therapeutic_theme', '')}",
        f"FORME: {row.get('form', '')}",
        f"PRIX: {row.get('price', '')} TND  |  PRIX PROMO: {row.get('promo_price', '')} TND",
        f"FRÉQUENCE PROMO: {row.get('promo_frequency', '')}",
        f"NOTE: {row.get('rating', '')} / 5  |  AVIS: {row.get('review_count', '')} reviews",
        f"PRÉSENCE MARCHÉ: {row.get('presence_count', '')} points",
        f"STOCK: {row.get('stock_status', '')}",
        f"TENDANCE MARCHÉ: {row.get('global_category_trend', '')}",
        f"DENSITÉ CONCURRENTIELLE: {row.get('competitor_density', '')}",
        f"RISQUE SUBSTITUTION: {row.get('substitution_risk', '')}",
        f"CYCLE DE VIE: {row.get('lifecycle_stage_predicted', '')}",
        f"INDICATIONS: {str(row.get('indications', ''))[:350]}",
        f"COMPOSITION: {str(row.get('composition', ''))[:300]}",
        f"DESCRIPTION: {str(row.get('description', ''))[:300]}",
    ]
    return '\n'.join([p for p in parts if p.split(': ', 1)[-1].strip() not in ['', 'nan', 'None']])


# ─────────────────────────────────────────────────────────────────────────────
# SCORING ENRICHI — opportunity, risk, momentum
# ─────────────────────────────────────────────────────────────────────────────

def opportunity_score(row) -> int:
    s = 0
    if row.get('global_category_trend')     == 'croissance':                  s += 2
    if row.get('competitor_density')        == 'faible':                      s += 2
    if row.get('lifecycle_stage_predicted') in ['Introduction', 'Croissance']: s += 2
    if row.get('stock_status')              == 'en stock':                    s += 1
    if pd.notna(row.get('rating')) and row.get('rating', 0) >= 4.0:           s += 1
    return s


def risk_score(row) -> int:
    s = 0
    if row.get('substitution_risk')         == 'élevé':                        s += 2
    if row.get('competitor_density')        == 'forte':                        s += 2
    if row.get('lifecycle_stage_predicted') in ['Déclin', 'Maturité']:         s += 2
    if row.get('stock_status')              == 'rupture ponctuelle':           s += 1
    if pd.notna(row.get('rating')) and row.get('rating', 5) < 3.0:            s += 1
    return s


def momentum_score(row) -> float:
    """
    Score composite [-1, +1] qui capture la 'vélocité commerciale' d'un produit.
    Combine tendance marché, cycle de vie, présence, note client et concurrence.
    """
    s = 0.0
    # Tendance catégorie
    trend_map = {'croissance': +0.3, 'plateau': 0.0}
    s += trend_map.get(str(row.get('global_category_trend', '')).lower(), 0.0)
    # Cycle de vie
    lc_map = {'Introduction': +0.1, 'Croissance': +0.3, 'Maturité': 0.0, 'Déclin': -0.3}
    s += lc_map.get(str(row.get('lifecycle_stage_predicted', '')).strip(), 0.0)
    # Présence marché (normalisée 2–6)
    try:
        presence_norm = (float(row.get('presence_count', 3)) - 2) / 4  # 0..1
        s += presence_norm * 0.15
    except (ValueError, TypeError):
        pass
    # Note client
    try:
        rating = float(row.get('rating', 4.0))
        s += (rating - 3.0) / 2.0 * 0.1  # -0.05 à +0.1
    except (ValueError, TypeError):
        pass
    # Concurrence
    comp_map = {'faible': +0.1, 'moyenne': 0.0, 'forte': -0.2}
    s += comp_map.get(str(row.get('competitor_density', '')).lower(), 0.0)
    # Substitution
    sub_map = {'faible': +0.05, 'modéré': 0.0, 'élevé': -0.15}
    s += sub_map.get(str(row.get('substitution_risk', '')).lower(), 0.0)

    return round(max(-1.0, min(1.0, s)), 3)


def price_competitiveness(row) -> str:
    """Catégorise la position prix du produit par rapport à sa fourchette marché."""
    try:
        price     = float(row.get('price', 0))
        price_min = float(row.get('price_min', price))
        price_max = float(row.get('price_max', price))
        if price_max == price_min:
            return 'unique'
        position = (price - price_min) / (price_max - price_min)
        if position <= 0.33:
            return 'prix bas'
        elif position <= 0.66:
            return 'prix moyen'
        else:
            return 'prix élevé'
    except (ValueError, TypeError, ZeroDivisionError):
        return 'inconnu'


# ─────────────────────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────────────────────

def load_data(path: str = DATA_PATH) -> pd.DataFrame:
    df = pd.read_excel(path)

    # Normalisation des colonnes texte
    str_cols = [
        'product_class', 'stock_status', 'competitor_density',
        'substitution_risk', 'global_category_trend', 'lifecycle_stage_predicted',
        'promo_frequency', 'gamme', 'form', 'therapeutic_theme', 'product_name'
    ]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    df['product_class']             = df['product_class'].str.title()
    df['stock_status']              = df['stock_status'].str.lower()
    df['competitor_density']        = df['competitor_density'].str.lower()
    df['substitution_risk']         = df['substitution_risk'].str.lower()
    df['global_category_trend']     = df['global_category_trend'].str.lower()

    # Scores
    df['opportunity_score'] = df.apply(opportunity_score, axis=1)
    df['risk_score']        = df.apply(risk_score, axis=1)
    df['momentum_score']    = df.apply(momentum_score, axis=1)
    df['price_position']    = df.apply(price_competitiveness, axis=1)

    # Remise promo calculée
    df['discount_pct'] = ((df['price'] - df['promo_price']) / df['price'].replace(0, np.nan) * 100).round(1).fillna(0)

    # 4 passages spécialisés + passage complet
    df['passage_clinical']   = df.apply(build_clinical_passage,   axis=1)
    df['passage_commercial'] = df.apply(build_commercial_passage,  axis=1)
    df['passage_strategic']  = df.apply(build_strategic_passage,   axis=1)
    df['passage']            = df.apply(build_full_passage,        axis=1)  # passage principal

    print(f"✅ Dataset chargé : {len(df)} produits | {len(df.columns)} colonnes")
    print(f"   Scores : opportunity [0-8], risk [0-8], momentum [-1,+1]")
    return df
