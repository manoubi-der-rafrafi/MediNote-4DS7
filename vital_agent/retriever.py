import numpy as np
import pandas as pd
import faiss
import math
import re
from typing import Optional
from sentence_transformers import SentenceTransformer
from vital_agent.logging_utils import safe_print as print

# ─────────────────────────────────────────────────────────────────────────────
# EMBEDDING MODEL — partagé par tous les index FAISS
# ─────────────────────────────────────────────────────────────────────────────

_EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")   # 384-dim, léger & efficace

def _embed(texts: list[str]) -> np.ndarray:
    """Retourne un array float32 normalisé (L2) — requis pour cosine via FAISS IndexFlatIP."""
    vecs = _EMBED_MODEL.encode(texts, batch_size=64, show_progress_bar=False,
                               convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(vecs)
    return vecs


def _build_faiss_index(texts: list[str]) -> tuple[faiss.IndexFlatIP, np.ndarray]:
    """Construit un index FAISS Inner-Product (= cosine sur vecteurs normalisés)."""
    vecs = _embed(texts)
    dim  = vecs.shape[1]
    idx  = faiss.IndexFlatIP(dim)
    idx.add(vecs)
    return idx, vecs


# ─────────────────────────────────────────────────────────────────────────────
# BM25 — inchangé (sparse retrieval)
# ─────────────────────────────────────────────────────────────────────────────

class BM25:
    def __init__(self, corpus: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b  = b
        self.tokenize = lambda text: re.findall(r'\w+', text.lower())

        tokenized  = [self.tokenize(doc) for doc in corpus]
        self.N     = len(tokenized)
        self.avgdl = sum(len(d) for d in tokenized) / max(self.N, 1)

        self.tf = []
        for doc in tokenized:
            freq: dict[str, int] = {}
            for token in doc:
                freq[token] = freq.get(token, 0) + 1
            self.tf.append(freq)

        df_count: dict[str, int] = {}
        for freq in self.tf:
            for token in freq:
                df_count[token] = df_count.get(token, 0) + 1
        self.idf: dict[str, float] = {}
        for token, df in df_count.items():
            self.idf[token] = math.log((self.N - df + 0.5) / (df + 0.5) + 1)

    def score(self, query: str, top_k: int = 20) -> tuple[np.ndarray, np.ndarray]:
        tokens = self.tokenize(query)
        scores = np.zeros(self.N)
        for token in tokens:
            if token not in self.idf:
                continue
            idf = self.idf[token]
            for i, freq in enumerate(self.tf):
                tf  = freq.get(token, 0)
                dl  = sum(freq.values())
                num = tf * (self.k1 + 1)
                den = tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
                scores[i] += idf * num / den

        top_idx = np.argsort(scores)[::-1][:top_k]
        return top_idx, scores[top_idx]


# ─────────────────────────────────────────────────────────────────────────────
# RRF — inchangé
# ─────────────────────────────────────────────────────────────────────────────

def reciprocal_rank_fusion(
    ranked_lists: list[np.ndarray], k: int = 60
) -> tuple[np.ndarray, np.ndarray]:
    scores: dict[int, float] = {}
    for ranked in ranked_lists:
        for rank, idx in enumerate(ranked, start=1):
            scores[idx] = scores.get(idx, 0.0) + 1.0 / (k + rank)

    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return (np.array([i for i, _ in sorted_items]),
            np.array([s for _, s in sorted_items]))


# ─────────────────────────────────────────────────────────────────────────────
# BUSINESS RERANKER — inchangé
# ─────────────────────────────────────────────────────────────────────────────

class BusinessReranker:
    INTENT_BOOSTS = {
        'opportunité': {
            'lifecycle_stage_predicted': {'Croissance': +0.15, 'Introduction': +0.10},
            'global_category_trend':     {'croissance': +0.10},
            'competitor_density':        {'faible': +0.08},
        },
        'risque': {
            'substitution_risk':         {'élevé': +0.12, 'modéré': +0.05},
            'lifecycle_stage_predicted': {'Déclin': +0.10},
            'competitor_density':        {'forte': +0.10},
        },
        'stock': {
            'stock_status': {'rupture ponctuelle': +0.20},
        },
        'premium': {
            'price_position': {'prix élevé': +0.15},
            'rating': None,
        },
        'entrée de gamme': {
            'price_position': {'prix bas': +0.15},
        },
        'bien noté': {
            'rating': None,
        },
    }

    def rerank(self, df: pd.DataFrame, query: str, base_scores: np.ndarray) -> pd.DataFrame:
        q      = query.lower()
        scores = base_scores.copy().astype(float)

        for intent, field_map in self.INTENT_BOOSTS.items():
            if intent in q:
                for col, val_map in field_map.items():
                    if col == 'rating':
                        if col in df.columns:
                            scores += (df[col].fillna(4.0).values - 3.0) * 0.03
                    elif col in df.columns and val_map:
                        for val, bonus in val_map.items():
                            mask = df[col].str.lower() == val.lower()
                            scores[mask] += bonus

        if 'momentum_score' in df.columns:
            scores += df['momentum_score'].fillna(0).values * 0.08

        if 'review_count' in df.columns:
            max_reviews = df['review_count'].max() or 1
            scores += (np.log1p(df['review_count'].fillna(0).values) /
                       np.log1p(max_reviews)) * 0.04

        df = df.copy()
        df['rerank_score'] = scores
        return df.sort_values('rerank_score', ascending=False)


# ─────────────────────────────────────────────────────────────────────────────
# VITAL RETRIEVER — FAISS remplace TF-IDF
# Pipeline : BM25 (sparse) + FAISS (dense) → RRF → BusinessReranker
# ─────────────────────────────────────────────────────────────────────────────

class VitalRetriever:
    def __init__(self, df: pd.DataFrame):
        self.df       = df.reset_index(drop=True)
        self.reranker = BusinessReranker()

        passages = df['passage'].tolist()

        print("⏳ Construction des index FAISS (embeddings)...")

        # Index FAISS principal (passage complet)
        self.faiss_index, self.faiss_vecs = _build_faiss_index(passages)

        # Index FAISS clinique
        self.faiss_clinical, _ = _build_faiss_index(df['passage_clinical'].tolist())

        # Index FAISS commercial
        self.faiss_commercial, _ = _build_faiss_index(df['passage_commercial'].tolist())

        # BM25 sur passage complet
        self.bm25 = BM25(passages)

        # BM25 léger sur noms / gamme
        name_passages = [
            f"{r.get('product_name','')} {r.get('gamme','')} {r.get('therapeutic_theme','')}"
            for _, r in df.iterrows()
        ]
        self.bm25_names = BM25(name_passages, k1=1.2, b=0.5)

        print(f"✅ VitalRetriever FAISS : {len(df)} produits | dim={self.faiss_vecs.shape[1]}")
        print(f"   BM25 OK | RRF + BusinessReranker actifs")

    # ── Recherche FAISS ───────────────────────────────────────────────────────

    def _faiss_search(self, index: faiss.IndexFlatIP, query: str, top_k: int) -> np.ndarray:
        q_vec = _embed([query])
        _, indices = index.search(q_vec, top_k)
        return indices[0]

    # ── OUTIL 1 : recherche hybride principale ────────────────────────────────

    def retrieve_products(
        self,
        query: str,
        top_k: int = 8,
        candidate_k: int = 30,
        intent: Optional[str] = None,
    ) -> pd.DataFrame:
        q_lower = query.lower()

        is_clinical   = any(w in q_lower for w in [
            'indication', 'composition', 'ingrédient', 'actif', 'contre',
            'forme', 'comprimé', 'gélule', 'sirop', 'crème', 'huile'
        ])
        is_commercial = any(w in q_lower for w in [
            'prix', 'promo', 'remise', 'moins cher', 'économique', 'premium',
            'présence', 'gamme', 'marché'
        ])

        # Sparse
        bm25_idx,  _ = self.bm25.score(query, top_k=candidate_k)
        bm25n_idx, _ = self.bm25_names.score(query, top_k=candidate_k)

        # Dense (FAISS)
        faiss_idx = self._faiss_search(self.faiss_index, query, candidate_k)

        ranked_lists = [bm25_idx, bm25n_idx, faiss_idx]

        if is_clinical:
            ranked_lists.append(self._faiss_search(self.faiss_clinical, query, candidate_k))

        if is_commercial:
            ranked_lists.append(self._faiss_search(self.faiss_commercial, query, candidate_k))

        # RRF fusion
        fused_idx, rrf_scores = reciprocal_rank_fusion(ranked_lists)

        unique_idx  = fused_idx[:candidate_k]
        base_scores = rrf_scores[:candidate_k]

        candidates  = self.df.iloc[unique_idx].copy()
        candidates['similarity_score'] = base_scores

        # Business reranker
        reranked = self.reranker.rerank(candidates, query, base_scores)
        result   = reranked.head(top_k).copy()
        result['similarity_score'] = result['rerank_score']
        return result

    # ── OUTIL 2 : filtre multi-critères ──────────────────────────────────────

    def filter_by_metric(
        self,
        lifecycle:  Optional[str] = None,
        stock:      Optional[str] = None,
        risk:       Optional[str] = None,
        trend:      Optional[str] = None,
        competitor: Optional[str] = None,
        gamme:      Optional[str] = None,
        price_max:  Optional[float] = None,
        min_rating: Optional[float] = None,
        sort_by:    str = 'opportunity_score',
        top_k:      int = 10,
    ) -> pd.DataFrame:
        df = self.df.copy()
        if lifecycle:  df = df[df['lifecycle_stage_predicted'].str.lower() == lifecycle.lower()]
        if stock:      df = df[df['stock_status'].str.lower()              == stock.lower()]
        if risk:       df = df[df['substitution_risk'].str.lower()         == risk.lower()]
        if trend:      df = df[df['global_category_trend'].str.lower()     == trend.lower()]
        if competitor: df = df[df['competitor_density'].str.lower()        == competitor.lower()]
        if gamme:      df = df[df['gamme'].str.lower().str.contains(gamme.lower())]
        if price_max is not None: df = df[df['price'] <= price_max]
        if min_rating is not None: df = df[df['rating'] >= min_rating]
        if sort_by in df.columns:
            df = df.sort_values(sort_by, ascending=False)
        return df.head(top_k)

    # ── OUTIL 3 : top opportunités ────────────────────────────────────────────

    def get_top_opportunities(self, top_k: int = 10, min_momentum: float = 0.0) -> pd.DataFrame:
        df = self.df.copy()
        if min_momentum > 0:
            df = df[df['momentum_score'] >= min_momentum]
        df['composite_opp'] = (
            df['opportunity_score'] * 0.6 +
            df['momentum_score'].clip(0, 1) * 8 * 0.4
        )
        return (df.nlargest(top_k, 'composite_opp')
                  [['product_name', 'gamme', 'therapeutic_theme',
                    'opportunity_score', 'risk_score', 'momentum_score',
                    'lifecycle_stage_predicted', 'global_category_trend',
                    'competitor_density', 'stock_status', 'price', 'rating']])

    # ── OUTIL 4 : alertes risque ──────────────────────────────────────────────

    def get_risk_alerts(self, top_k: int = 10) -> pd.DataFrame:
        df = self.df.copy()
        df['composite_risk'] = (
            df['risk_score'] * 0.6 +
            df['momentum_score'].clip(-1, 0).abs() * 8 * 0.4
        )
        return (df.nlargest(top_k, 'composite_risk')
                  [['product_name', 'gamme', 'risk_score', 'momentum_score',
                    'substitution_risk', 'stock_status',
                    'lifecycle_stage_predicted', 'competitor_density',
                    'price_position', 'discount_pct']])

    # ── OUTIL 5 : profil complet d'un produit ────────────────────────────────

    def get_product_profile(self, product_name: str) -> pd.DataFrame:
        mask = self.df['product_name'].str.lower().str.contains(
            product_name.lower(), regex=False
        )
        cols = [
            'product_name', 'gamme', 'product_class', 'form', 'therapeutic_theme',
            'price', 'promo_price', 'discount_pct', 'price_position',
            'rating', 'review_count', 'presence_count',
            'stock_status', 'global_category_trend', 'competitor_density',
            'substitution_risk', 'lifecycle_stage_predicted',
            'opportunity_score', 'risk_score', 'momentum_score',
            'indications', 'composition'
        ]
        available = [c for c in cols if c in self.df.columns]
        return self.df[mask][available]

    # ── OUTIL 6 : analyse par gamme ──────────────────────────────────────────

    def analyze_gamme(self, gamme: str, top_k: int = 10) -> pd.DataFrame:
        mask = self.df['gamme'].str.lower().str.contains(gamme.lower(), regex=False)
        df   = self.df[mask].copy()
        return (df.sort_values('momentum_score', ascending=False)
                  [['product_name', 'opportunity_score', 'risk_score', 'momentum_score',
                    'lifecycle_stage_predicted', 'stock_status', 'price', 'rating']]
                  .head(top_k))

    # ── OUTIL 7 : produits similaires ────────────────────────────────────────

    def get_similar_products(self, product_name: str, top_k: int = 6) -> pd.DataFrame:
        mask = self.df['product_name'].str.lower().str.contains(
            product_name.lower(), regex=False
        )
        if not mask.any():
            return pd.DataFrame()

        ref_idx  = self.df[mask].index[0]
        ref_vec  = self.faiss_vecs[ref_idx:ref_idx+1]
        _, indices = self.faiss_index.search(ref_vec, top_k + 1)
        top_idx  = [i for i in indices[0] if i != ref_idx][:top_k]

        result = self.df.iloc[top_idx].copy()
        sims   = (ref_vec @ self.faiss_vecs[top_idx].T).flatten()
        result['similarity_score'] = sims
        return result[['product_name', 'gamme', 'therapeutic_theme',
                        'lifecycle_stage_predicted', 'price', 'similarity_score']]
