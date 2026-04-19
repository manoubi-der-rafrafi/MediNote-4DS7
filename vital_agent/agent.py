"""
VITAL-AGENT v4 — Architecture Lazy-Load + Intent-Gate
══════════════════════════════════════════════════════
CHANGEMENTS MAJEURS (v3 → v4)
─────────────────────────────
AVANT (v3) :
  __init__ → load_data() → calcul scores/passages → VitalRetriever (index TF-IDF/BM25)
  → PUIS question posée
  Problème : tout le pipeline tourne au démarrage, avant toute interaction.

APRÈS (v4) :
  __init__ → RIEN (juste config)
  ask(query) →
    1. detect_intent(query)        ← GRATUIT, zéro calcul
    2a. Si intent == 'chat'         → réponse conversationnelle directe (pas de data)
    2b. Si intent business valide   → _ensure_data_loaded() en lazy
    3. _route(query)               → retrieval ciblé
    4. LLM generation

  _ensure_data_loaded() est idempotent : charge une seule fois, met en cache.
  Avantage intégration : les membres upstream n'ont pas à attendre le chargement
  des données pour les requêtes conversationnelles.
"""

from __future__ import annotations

import pandas as pd
from vital_agent.prompt   import format_prompt, build_context_block, detect_intent
from vital_agent.llm      import load_llm


# ─────────────────────────────────────────────────────────────────────────────
# INTENT CONVERSATIONNEL — requêtes sans données
# ─────────────────────────────────────────────────────────────────────────────

# Mots-clés qui signalent une interaction sociale / non-business
_CHAT_PATTERNS: list[str] = [
    'bonjour', 'bonsoir', 'salut', 'hello', 'hi ', 'hey ',
    'merci', 'thank', 'au revoir', 'bye', 'à bientôt',
    "qu'est-ce que tu", "qui es-tu", "comment tu", "tu peux",
    "aide-moi", "aide moi", "help me", "c'est quoi",
    "comment ça va", "ça va", "vas-tu",
    "?",   # question courte sans mot-clé business
]

# Intents business reconnus (définis dans prompt.py)
_BUSINESS_INTENTS: set[str] = {
    'opportunity', 'risk', 'stock', 'product',
    'gamme', 'commercial', 'clinical', 'trend',
    'momentum', 'comparison', 'strategic',
}

def _is_chat_query(query: str, intent: str) -> bool:
    """
    Renvoie True si la requête est conversationnelle / non-business.
    Critères :
      - intent == 'strategic' (fallback de detect_intent) ET query très courte (< 6 mots)
      - OU présence d'un pattern chat explicite
      - OU query de moins de 3 mots sans mot-clé business
    """
    q    = query.lower().strip()
    words = q.split()

    # Très court sans aucun mot-clé business → probablement du chat
    if len(words) <= 2:
        return True

    # Pattern conversationnel explicite
    if any(pat in q for pat in _CHAT_PATTERNS):
        return True

    # detect_intent retourne 'strategic' comme fallback pour tout ce qui n'est pas reconnu.
    # Si c'est strategic MAIS que la query ne contient pas de signal business clair → chat.
    if intent == 'strategic' and len(words) < 6:
        business_signals = [
            'produit', 'gamme', 'vital', 'stock', 'vente', 'marché',
            'analyse', 'stratégie', 'risque', 'opportunité', 'portefeuille',
            'chiffre', 'ventes', 'prix', 'pharmacie', 'parapharmacie',
            'concurrent', 'catégorie', 'référence',
        ]
        if not any(sig in q for sig in business_signals):
            return True

    return False


# ─────────────────────────────────────────────────────────────────────────────
# RÉPONSES CONVERSATIONNELLES — sans appel LLM externe (instantané)
# ─────────────────────────────────────────────────────────────────────────────

def _chat_response(query: str) -> str:
    """
    Répond aux requêtes conversationnelles sans charger les données ni appeler le LLM.
    Gère les salutations, remerciements, et questions vagues sur le système.
    """
    q = query.lower().strip()

    if any(w in q for w in ['bonjour', 'bonsoir', 'salut', 'hello', 'hi', 'hey']):
        return (
            "Bonjour ! Je suis **VITAL-AGENT v4**, votre assistant en intelligence commerciale "
            "pour le portefeuille Vital. 🧠\n\n"
            "Je peux vous aider à :\n"
            "- 🌟 Identifier les **meilleures opportunités** de votre catalogue\n"
            "- ⚠️  Détecter les **produits à risque** ou en rupture de stock\n"
            "- 📊 Analyser une **gamme** ou un **produit spécifique**\n"
            "- 📈 Évaluer les **tendances marché** et le momentum commercial\n\n"
            "Posez-moi une question sur vos produits pour commencer !"
        )

    if any(w in q for w in ['merci', 'thank', 'parfait', 'super', 'génial', 'excellent']):
        return "Avec plaisir ! N'hésitez pas si vous avez d'autres questions sur votre portefeuille. 🤝"

    if any(w in q for w in ['au revoir', 'bye', 'à bientôt', 'bonne journée', 'bonne soirée']):
        return "Au revoir ! Bonne continuation dans vos analyses. 👋"

    if any(w in q for w in ["qui es-tu", "c'est quoi", "qu'est-ce", "tu peux", "comment tu"]):
        return (
            "Je suis **VITAL-AGENT v4**, un assistant d'intelligence commerciale spécialisé "
            "dans l'analyse du portefeuille Vital (parapharmacie, compléments, soins, pédiatrie — "
            "marché tunisien).\n\n"
            "Je combine analyse des données produits, scoring d'opportunités/risques et "
            "recommandations stratégiques.\n\n"
            "**Exemples de questions :**\n"
            "> *« Quelles sont vos meilleures opportunités ? »*\n"
            "> *« Quels produits sont en rupture de stock ? »*\n"
            "> *« Analyse la gamme Bébé »*"
        )

    if any(w in q for w in ['ça va', 'comment vas', 'comment tu vas']):
        return (
            "Tout système opérationnel ! 🟢 Prêt à analyser votre portefeuille.\n"
            "Que souhaitez-vous explorer ?"
        )

    # Réponse générique pour une requête vague non reconnue
    return (
        f"⚠️ **Votre question n'est pas assez spécifique** pour que je puisse vous aider efficacement.\n\n"
        f"Vous avez demandé : *« {query} »*\n\n"
        "Pourriez-vous préciser ce que vous recherchez ? Par exemple :\n"
        "- **Opportunités :** *« Quels produits ont le meilleur potentiel de croissance ? »*\n"
        "- **Risques :** *« Quels produits sont en danger ? »*\n"
        "- **Stock :** *« Y a-t-il des ruptures de stock urgentes ? »*\n"
        "- **Gamme :** *« Analyse la gamme [nom] »*\n"
        "- **Produit :** *« Profil de [nom du produit] »*\n"
        "- **Tendances :** *« Quelles catégories sont en croissance ? »*"
    )


# ─────────────────────────────────────────────────────────────────────────────
# VITAL AGENT v4 — Lazy-Load + Intent-Gate
# ─────────────────────────────────────────────────────────────────────────────

class VitalAgent:
    """
    Agent stateless avec chargement paresseux des données.

    Lifecycle :
      1. __init__       → config uniquement, ZÉRO calcul lourd
      2. ask(query)     → detect_intent → si chat : réponse directe
                                        → si business : _ensure_data_loaded()
                                                        → route → context → LLM
    """

    def __init__(self, data_path: str | None = None):
        self._data_path = data_path          # path optionnel, pas encore lu
        self._df        = None               # chargé en lazy
        self._retriever = None               # instancié après _df
        self._llm       = None               # chargé en lazy

        print("✅ VitalAgent v4 prêt — Mode lazy-load (données chargées à la première question business).\n")

    # ─────────────────────────────────────────────────────────────────────────
    # LAZY INIT — appelé uniquement si une question business est détectée
    # ─────────────────────────────────────────────────────────────────────────

    def _ensure_data_loaded(self) -> None:
        """Charge données + index + LLM une seule fois, idempotent."""
        if self._df is not None:
            return  # déjà chargé

        # Import ici pour éviter tout import au démarrage
        from vital_agent.data_loader import load_data
        from vital_agent.retriever   import VitalRetriever

        print("⏳ Chargement des données et construction des index (première requête business)...")
        self._df        = load_data(self._data_path) if self._data_path else load_data()
        self._retriever = VitalRetriever(self._df)
        self._llm       = load_llm()
        print("✅ Pipeline business prêt.\n")

    # ─────────────────────────────────────────────────────────────────────────
    # PROPERTIES — accès sûr après lazy-load
    # ─────────────────────────────────────────────────────────────────────────

    @property
    def df(self) -> pd.DataFrame:
        self._ensure_data_loaded()
        return self._df

    @property
    def retriever(self):
        self._ensure_data_loaded()
        return self._retriever

    # ─────────────────────────────────────────────────────────────────────────
    # ROUTING — sélection de l'outil de retrieval
    # (inchangé fonctionnellement, opère après lazy-load)
    # ─────────────────────────────────────────────────────────────────────────

    def _route(self, query: str) -> pd.DataFrame:
        q = query.lower()

        # ── Profil produit spécifique ──
        if any(w in q for w in ['profil', 'fiche', 'détail', 'analyse', 'ce produit']):
            for _, row in self._df.iterrows():
                name = str(row.get('product_name', '')).lower()
                if name and name in q:
                    print(f"🔧 Outil : get_product_profile ({row['product_name']})")
                    return self._retriever.get_product_profile(row['product_name'])

        # ── Analyse gamme ──
        if any(w in q for w in ['gamme', 'ligne', 'famille']):
            for _, row in self._df.drop_duplicates('gamme').iterrows():
                gamme_val = str(row.get('gamme', '')).lower()
                if gamme_val and gamme_val in q:
                    print(f"🔧 Outil : analyze_gamme ({row['gamme']})")
                    return self._retriever.analyze_gamme(row['gamme'])

        # ── Ruptures / stock ──
        if any(w in q for w in ['rupture', 'stock', 'disponib', 'indisponible']):
            print("🔧 Outil : filter_by_metric (stock=rupture ponctuelle)")
            return self._retriever.filter_by_metric(
                stock='rupture ponctuelle',
                sort_by='risk_score',
                top_k=8
            )

        # ── Déclin ──
        if any(w in q for w in ['déclin', 'decline', 'vieillissant', 'obsolète']):
            print("🔧 Outil : filter_by_metric (lifecycle=Déclin)")
            return self._retriever.filter_by_metric(
                lifecycle='Déclin',
                sort_by='risk_score',
                top_k=8
            )

        # ── Opportunités ──
        if any(w in q for w in ['opportunité', 'meilleur', 'potentiel', 'top', 'performer']):
            min_mom = 0.1 if 'fort' in q or 'haute' in q else 0.0
            print(f"🔧 Outil : get_top_opportunities (min_momentum={min_mom})")
            return self._retriever.get_top_opportunities(top_k=8, min_momentum=min_mom)

        # ── Risques / alertes ──
        if any(w in q for w in ['risque', 'danger', 'alerte', 'menace', 'surveiller']):
            print("🔧 Outil : get_risk_alerts")
            return self._retriever.get_risk_alerts(top_k=8)

        # ── Croissance / tendance ──
        if any(w in q for w in ['croissance', 'tendance', 'trend', 'dynamique']):
            print("🔧 Outil : filter_by_metric (trend=croissance)")
            return self._retriever.filter_by_metric(
                trend='croissance',
                sort_by='momentum_score',
                top_k=8
            )

        # ── Momentum fort ──
        if any(w in q for w in ['momentum', 'vélocité', 'moteur', 'locomotive']):
            print("🔧 Outil : filter (momentum > 0.3)")
            df = self._df[self._df['momentum_score'] >= 0.3].copy()
            return df.nlargest(8, 'momentum_score')

        # ── Default : recherche hybride ──
        print("🔧 Outil : retrieve_products (Hybrid BM25+TF-IDF+RRF+Reranker)")
        return self._retriever.retrieve_products(query, top_k=8)

    # ─────────────────────────────────────────────────────────────────────────
    # ASK — point d'entrée principal
    # ─────────────────────────────────────────────────────────────────────────

    def ask(self, query: str, verbose: bool = False) -> str:
        """
        Traite une question utilisateur.

        Pipeline :
          1. detect_intent(query)      → INSTANTANÉ, sans données
          2a. Si chat/vague            → réponse conversationnelle directe
          2b. Si business              → _ensure_data_loaded() [lazy, 1 seule fois]
                                         → _route() → build_context → LLM

        Chaque appel est indépendant — aucune mémoire entre les questions.
        """
        print(f'\n{"─"*60}')
        print(f'❓ {query}')
        print(f'{"─"*60}')

        # ── Étape 1 : Détection d'intent (sans données) ───────────────────
        intent = detect_intent(query)
        print(f"🎯 Intent détecté : {intent}")

        # ── Étape 2 : Gate conversationnel ────────────────────────────────
        if _is_chat_query(query, intent):
            print("💬 Mode : interaction conversationnelle (aucun chargement de données)")
            return _chat_response(query)

        # ── Étape 3 : Lazy-load données (uniquement si business) ──────────
        self._ensure_data_loaded()

        # ── Étape 4 : Retrieval ───────────────────────────────────────────
        retrieved = self._route(query)

        if verbose:
            score_col = (
                'rerank_score'     if 'rerank_score'     in retrieved.columns else
                'similarity_score' if 'similarity_score' in retrieved.columns else None
            )
            print('\n📦 Produits récupérés :')
            for _, row in retrieved.iterrows():
                s         = row.get(score_col, '') if score_col else ''
                score_str = f"{s:.4f}" if isinstance(s, float) else '–'
                mom       = row.get('momentum_score', '')
                mom_str   = f"{mom:+.2f}" if isinstance(mom, float) else '–'
                print(
                    f"   → {row['product_name']:40s} | score={score_str} | "
                    f"momentum={mom_str} | opp={row.get('opportunity_score','?')}/8 | "
                    f"risk={row.get('risk_score','?')}/8"
                )

        # ── Étape 5 : Construction contexte + prompt ─────────────────────
        context = build_context_block(retrieved, query=query)
        prompt  = format_prompt(user_query=query, context=context)

        # ── Étape 6 : Génération LLM ──────────────────────────────────────
        print('🤖 Génération ...')
        return self._llm(prompt)
