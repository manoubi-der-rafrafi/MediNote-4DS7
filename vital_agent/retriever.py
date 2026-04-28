import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import math
import re
from typing import Optional
from vital_agent.logging_utils import safe_print as print


# ─────────────────────────────────────────────────────────────────────────────
# BM25 — implémentation pure Python (zéro dépendance externe)
# ─────────────────────────────────────────────────────────────────────────────

class BM25:
    """
    BM25 Okapi — sparse retrieval précis sur noms de produits,
    termes cliniques exacts, références gamme.
    k1=1.5, b=0.75 (valeurs standard industrie).
    """
    def __init__(self, corpus: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b  = b
        self.tokenize = lambda text: re.findall(r'\w+', text.lower())

        tokenized = [self.tokenize(doc) for doc in corpus]
        self.N    = len(tokenized)
        self.avgdl = sum(len(d) for d in tokenized) / max(self.N, 1)

        # TF par document
        self.tf = []
        for doc in tokenized:
            freq: dict[str, int] = {}
            for token in doc:
                freq[token] = freq.get(token, 0) + 1
            self.tf.append(freq)

        # IDF
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
                tf = freq.get(token, 0)
                dl = sum(freq.values())
                numerator   = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
                scores[i]  += idf * numerator / denominator

        top_idx = np.argsort(scores)[::-1][:top_k]
        return top_idx, scores[top_idx]


# ─────────────────────────────────────────────────────────────────────────────
# RRF — Reciprocal Rank Fusion
# Fusionne les listes BM25 et TF-IDF sans dépendre des valeurs absolues de score
# ─────────────────────────────────────────────────────────────────────────────

def reciprocal_rank_fusion(
    ranked_lists: list[np.ndarray],
    k: int = 60
) -> tuple[np.ndarray, np.ndarray]:
    """
    Fusionne N listes de rangs (indices) via RRF.
    k=60 est la valeur canonique recommandée par Cormack et al. (2009).
    Retourne (indices triés par score RRF desc, scores RRF).
    """
    scores: dict[int, float] = {}
    for ranked in ranked_lists:
        for rank, idx in enumerate(ranked, start=1):
            scores[idx] = scores.get(idx, 0.0) + 1.0 / (k + rank)

    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    indices = np.array([i for i, _ in sorted_items])
    rrf_scores = np.array([s for _, s in sorted_items])
    return indices, rrf_scores


# ─────────────────────────────────────────────────────────────────────────────
# CROSS-ENCODER LÉGER — reranking contextuel sans modèle externe
# Utilise les signaux métier pour rescorer le top-k final
# ─────────────────────────────────────────────────────────────────────────────

class BusinessReranker:
    """
    Reranker métier : ajuste le score final en fonction de signaux business.
    Compatible avec n'importe quel retriever en amont.
    Signal prioritaire : intent détecté dans la query.
    """

    INTENT_BOOSTS = {
        # intent → {colonne: valeur → bonus}
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
            'stock_status':              {'rupture ponctuelle': +0.20},
        },
        'premium': {
            'price_position':            {'prix élevé': +0.15},
            'rating':                    None,  # traité à part
        },
        'entrée de gamme': {
            'price_position':            {'prix bas': +0.15},
        },
        'bien noté': {
            'rating':                    None,  # traité à part
        },
    }

    def rerank(self, df: pd.DataFrame, query: str, base_scores: np.ndarray) -> pd.DataFrame:
        q = query.lower()
        scores = base_scores.copy().astype(float)

        # Détection d'intent
        for intent, field_map in self.INTENT_BOOSTS.items():
            if intent in q:
                for col, val_map in field_map.items():
                    if col == 'rating':
                        # boost proportionnel à la note
                        if col in df.columns:
                            scores += (df[col].fillna(4.0).values - 3.0) * 0.03
                    elif col in df.columns and val_map:
                        for val, bonus in val_map.items():
                            mask = df[col].str.lower() == val.lower()
                            scores[mask] += bonus

        # Boost universel : momentum_score
        if 'momentum_score' in df.columns:
            scores += df['momentum_score'].fillna(0).values * 0.08

        # Boost review_count (popularité) — log-normalisé
        if 'review_count' in df.columns:
            max_reviews = df['review_count'].max() or 1
            scores += (np.log1p(df['review_count'].fillna(0).values) /
                       np.log1p(max_reviews)) * 0.04

        df = df.copy()
        df['rerank_score'] = scores
        return df.sort_values('rerank_score', ascending=False)


# ─────────────────────────────────────────────────────────────────────────────
# VITAL RETRIEVER — architecture hybride complète
# ─────────────────────────────────────────────────────────────────────────────

class VitalRetriever:
    """
    Pipeline de retrieval avancé :
    1. BM25 (sparse)    → précision sur termes exacts, noms, gammes
    2. TF-IDF (dense)   → sémantique, synonymes, descriptions longues
    3. RRF fusion       → combine les deux listes sans biais de score absolu
    4. BusinessReranker → ajustement final par signaux métier + intent
    """

    def __init__(self, df: pd.DataFrame):
        self.df       = df.reset_index(drop=True)
        self.reranker = BusinessReranker()

        passages = df['passage'].tolist()

        # Index TF-IDF principal (passage complet)
        self.tfidf = TfidfVectorizer(
            analyzer='word', ngram_range=(1, 3),
            min_df=1, max_features=25000, sublinear_tf=True
        )
        self.tfidf_matrix = self.tfidf.fit_transform(passages)

        # Index TF-IDF clinique (indications, composition)
        clinical_passages = df['passage_clinical'].tolist()
        self.tfidf_clinical = TfidfVectorizer(
            analyzer='word', ngram_range=(1, 2),
            min_df=1, max_features=15000, sublinear_tf=True
        )
        self.tfidf_clinical_matrix = self.tfidf_clinical.fit_transform(clinical_passages)

        # Index TF-IDF commercial (prix, gamme)
        commercial_passages = df['passage_commercial'].tolist()
        self.tfidf_commercial = TfidfVectorizer(
            analyzer='word', ngram_range=(1, 2),
            min_df=1, max_features=10000, sublinear_tf=True
        )
        self.tfidf_commercial_matrix = self.tfidf_commercial.fit_transform(commercial_passages)

        # BM25 sur passage complet
        self.bm25 = BM25(passages)

        # BM25 léger sur noms de produits + gamme (précision maximale)
        name_passages = [
            f"{r.get('product_name','')} {r.get('gamme','')} {r.get('therapeutic_theme','')}"
            for _, r in df.iterrows()
        ]
        self.bm25_names = BM25(name_passages, k1=1.2, b=0.5)

        print(f"✅ VitalRetriever Hybride : {len(df)} produits")
        print(f"   TF-IDF : {self.tfidf_matrix.shape[1]} features | BM25 OK | RRF + Reranker actifs")

    # ── OUTIL 1 : recherche hybride principale ───────────────────────────────
    def retrieve_products(
        self,
        query: str,
        top_k: int = 8,
        candidate_k: int = 30,
        intent: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Pipeline complet :
        BM25(full) + BM25(names) + TF-IDF(full) + TF-IDF(clinical si médical)
        → RRF fusion → BusinessReranker → top_k final.
        """
        q_lower = query.lower()

        # Détection intent pour choisir les indices
        is_clinical    = any(w in q_lower for w in [
            'indication', 'composition', 'ingrédient', 'actif', 'contre',
            'forme', 'comprimé', 'gélule', 'sirop', 'crème', 'huile'
        ])
        is_commercial  = any(w in q_lower for w in [
            'prix', 'promo', 'remise', 'moins cher', 'économique', 'premium',
            'présence', 'gamme', 'marché'
        ])

        # ── Sparse retrieval (BM25) ──
        bm25_idx,  _  = self.bm25.score(query, top_k=candidate_k)
        bm25n_idx, _  = self.bm25_names.score(query, top_k=candidate_k)

        # ── Dense retrieval (TF-IDF) ──
        q_vec          = self.tfidf.transform([query])
        sim_full       = cosine_similarity(q_vec, self.tfidf_matrix).flatten()
        tfidf_idx      = np.argsort(sim_full)[::-1][:candidate_k]

        ranked_lists   = [bm25_idx, bm25n_idx, tfidf_idx]

        # Passages spécialisés selon intent
        if is_clinical:
            q_clin    = self.tfidf_clinical.transform([query])
            sim_clin  = cosine_similarity(q_clin, self.tfidf_clinical_matrix).flatten()
            clin_idx  = np.argsort(sim_clin)[::-1][:candidate_k]
            ranked_lists.append(clin_idx)

        if is_commercial:
            q_com    = self.tfidf_commercial.transform([query])
            sim_com  = cosine_similarity(q_com, self.tfidf_commercial_matrix).flatten()
            com_idx  = np.argsort(sim_com)[::-1][:candidate_k]
            ranked_lists.append(com_idx)

        # ── RRF fusion ──
        fused_idx, rrf_scores = reciprocal_rank_fusion(ranked_lists)

        # Prendre les top candidate_k uniques
        unique_idx  = fused_idx[:candidate_k]
        base_scores = rrf_scores[:candidate_k]

        candidates  = self.df.iloc[unique_idx].copy()
        candidates['similarity_score'] = base_scores

        # ── Business Reranker ──
        reranked = self.reranker.rerank(candidates, query, base_scores)
        result   = reranked.head(top_k).copy()
        result['similarity_score'] = result['rerank_score']
        return result

    # ── OUTIL 2 : filtre multi-critères ─────────────────────────────────────
    def filter_by_metric(
        self,
        lifecycle:   Optional[str] = None,
        stock:       Optional[str] = None,
        risk:        Optional[str] = None,
        trend:       Optional[str] = None,
        competitor:  Optional[str] = None,
        gamme:       Optional[str] = None,
        price_max:   Optional[float] = None,
        min_rating:  Optional[float] = None,
        sort_by:     str = 'opportunity_score',
        top_k:       int = 10
    ) -> pd.DataFrame:
        """
        Filtre enrichi avec tri configurable et filtres numériques.
        sort_by : 'opportunity_score' | 'risk_score' | 'momentum_score' | 'rating'
        """
        df = self.df.copy()
        if lifecycle:   df = df[df['lifecycle_stage_predicted'].str.lower() == lifecycle.lower()]
        if stock:       df = df[df['stock_status'].str.lower()              == stock.lower()]
        if risk:        df = df[df['substitution_risk'].str.lower()         == risk.lower()]
        if trend:       df = df[df['global_category_trend'].str.lower()     == trend.lower()]
        if competitor:  df = df[df['competitor_density'].str.lower()        == competitor.lower()]
        if gamme:       df = df[df['gamme'].str.lower().str.contains(gamme.lower())]
        if price_max is not None:
            df = df[df['price'] <= price_max]
        if min_rating is not None:
            df = df[df['rating'] >= min_rating]

        if sort_by in df.columns:
            df = df.sort_values(sort_by, ascending=False)

        return df.head(top_k)

    # ── OUTIL 3 : top opportunités ───────────────────────────────────────────
    def get_top_opportunities(self, top_k: int = 10, min_momentum: float = 0.0) -> pd.DataFrame:
        """
        Retourne les meilleures opportunités avec filtre momentum optionnel.
        Tri composite : opportunity_score * 0.6 + momentum_score * 0.4
        """
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

    # ── OUTIL 4 : alertes risque ─────────────────────────────────────────────
    def get_risk_alerts(self, top_k: int = 10) -> pd.DataFrame:
        """
        Alertes risque enrichies avec momentum négatif comme signal prioritaire.
        """
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

    # ── OUTIL 5 : profil complet d'un produit ───────────────────────────────
    def get_product_profile(self, product_name: str) -> pd.DataFrame:
        """
        Retourne le profil 360° d'un produit (recherche partielle insensible à la casse).
        Inclut tous les passages spécialisés.
        """
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
        """
        Analyse complète d'une gamme : tri par momentum pour identifier
        les produits moteurs vs les produits à risque dans la même gamme.
        """
        mask = self.df['gamme'].str.lower().str.contains(gamme.lower(), regex=False)
        df   = self.df[mask].copy()
        return (df.sort_values('momentum_score', ascending=False)
                  [['product_name', 'opportunity_score', 'risk_score', 'momentum_score',
                    'lifecycle_stage_predicted', 'stock_status', 'price', 'rating']]
                  .head(top_k))

    # ── OUTIL 7 : produits similaires ───────────────────────────────────────
    def get_similar_products(self, product_name: str, top_k: int = 6) -> pd.DataFrame:
        """
        Trouve les produits les plus similaires à un produit donné.
        Utilise le TF-IDF sur le passage complet.
        """
        mask = self.df['product_name'].str.lower().str.contains(
            product_name.lower(), regex=False
        )
        if not mask.any():
            return pd.DataFrame()

        ref_idx  = self.df[mask].index[0]
        ref_vec  = self.tfidf_matrix[ref_idx]
        sims     = cosine_similarity(ref_vec, self.tfidf_matrix).flatten()
        sims[ref_idx] = 0  # exclure le produit lui-même
        top_idx  = np.argsort(sims)[::-1][:top_k]

        result   = self.df.iloc[top_idx].copy()
        result['similarity_score'] = sims[top_idx]
        return result[['product_name', 'gamme', 'therapeutic_theme',
                        'lifecycle_stage_predicted', 'price', 'similarity_score']]
