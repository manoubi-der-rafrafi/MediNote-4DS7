"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           VITAL-AGENT v4 — PROMPT ENGINE (REWRITTEN)                        ║
║  Techniques appliquées :                                                     ║
║  • Step-Back Prompting      → abstraction avant réponse (↑36% précision)    ║
║  • Chain-of-Note (CoN)      → ancrage strict aux données récupérées          ║
║  • RAG-Strict Grounding     → interdit toute donnée hors contexte fourni     ║
║  • Chain-of-Verification    → auto-vérification avant sortie finale          ║
║  • Dynamic Negative Guards  → contraintes spécifiques par intent             ║
║  • Rich Markdown Schemas    → sorties belles, lisibles, structurées          ║
║  Sources :                                                                   ║
║  - PromptHub (2025) — Step-Back + CoVe                                       ║
║  - Galileo AI (2024) — Chain-of-Note RAG                                     ║
║  - MachinelearningMastery (2025) — Format control anti-hallucination         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT v4 — Identité + Règles RAG-strict + Grounding
# Technique : Chain-of-Note + RAG Strict Grounding
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
Tu es **VITAL-AGENT v4**, conseiller en intelligence commerciale pour Laboratoires Vital (marché tunisien parapharmacie / compléments / soins / pédiatrie).

━━━ RÈGLES ABSOLUES — ANTI-HALLUCINATION ━━━

**R1 · ANCRAGE DONNÉES**
Chaque affirmation doit être traceable à un produit du contexte fourni.
Si une donnée est absente du contexte → écris explicitement : `[donnée non disponible]`
JAMAIS inventer de chiffres, noms, scores ou tendances.

**R2 · RÉPONSE CIBLÉE**
Réponds UNIQUEMENT à ce qui est demandé. Zéro hors-sujet, zéro remplissage.

**R3 · INTERPRÉTATION, PAS RECOPIE**
Tu interprètes les métriques en signaux business. Tu ne récites pas les scores bruts.

**R4 · FORMAT RICHE OBLIGATOIRE**
Utilise toujours : titres Markdown `##`, tableaux `|---|`, gras `**`, émojis de statut.
Chaque produit cité = raison chiffrée + action concrète. Réponse max ~450 mots.

**R5 · DOUTE → SIGNALE-LE**
Si le contexte est insuffisant → commence par : `⚠️ Données partielles —` puis réponds avec ce qui est disponible.

━━━ LÉGENDE MÉTRIQUES ━━━
| Score | Interprétation |
|---|---|
| opportunity ≥ 7 | 🏆 Opportunité exceptionnelle |
| opportunity 5–6 | 🟢 Bon potentiel |
| opportunity < 4 | (ignorer sauf focus produit) |
| risk ≥ 7 | 🔴 Alerte critique |
| risk 5–6 | 🟠 Surveillance requise |
| momentum ≥ +0.4 | 🚀 Locomotive — forte accélération |
| momentum +0.2–+0.4 | 📈 Dynamique positive |
| momentum < 0 | 📉 Décélération — signal d'alerte |
| lifecycle = Croissance | 🌱 Phase idéale pour investir |
| lifecycle = Déclin | ⚰️ Envisager repositionnement |
| stock = rupture | 📦 Perte de CA immédiate |
| concurrence = faible | 🏁 Terrain libre |
""".strip()


# ─────────────────────────────────────────────────────────────────────────────
# INTENT DETECTION — granulaire, multi-signal
# ─────────────────────────────────────────────────────────────────────────────

INTENT_KEYWORDS = {
    'opportunity': [
        'opportunité', 'opportunites', 'meilleur', 'potentiel', 'top', 'performer',
        'à investir', 'développer', 'locomotive', 'fort momentum', 'investissement',
        'prioriser', 'priorité', 'croissance forte', 'dynamique forte'
    ],
    'risk': [
        'risque', 'danger', 'alerte', 'menace', 'surveiller', 'déclin',
        'decline', 'problème', 'faiblesse', 'vulnérable', 'critique',
        'substitution', 'concurrent fort', 'perte'
    ],
    'stock': [
        'rupture', 'stock', 'disponib', 'indisponible', 'approvisionnement',
        'manque', 'out of stock', 'réapprovisionnement'
    ],
    'product': [
        'profil', 'fiche', 'analyse', 'détail', 'ce produit', 'parle-moi de',
        'dis-moi', 'approfondis', 'zoom sur', 'focus sur'
    ],
    'gamme': [
        'gamme', 'ligne', 'famille', 'portfolio', 'collection', 'range'
    ],
    'commercial': [
        'prix', 'promo', 'remise', 'tarif', 'coût', 'budget', 'discount',
        'promotion', 'compétitif', 'positionnement prix', 'marge'
    ],
    'clinical': [
        'indication', 'composition', 'ingrédient', 'actif', 'forme',
        'comprimé', 'gélule', 'thérapeutique', 'posologie', 'contre-indication'
    ],
    'trend': [
        'tendance', 'trend', 'croissance', 'marché', 'dynamique', 'évolution',
        'secteur', 'catégorie', 'émergent'
    ],
    'momentum': [
        'momentum', 'vélocité', 'accélération', 'moteur', 'locomotive', 'vitesse'
    ],
    'comparison': [
        'compare', 'comparaison', 'versus', 'vs', 'différence entre',
        'lequel est', 'meilleur entre'
    ],
}

def detect_intent(query: str) -> str:
    q = query.lower()
    for intent in ['stock', 'clinical', 'commercial', 'product',
                   'gamme', 'risk', 'opportunity', 'momentum',
                   'trend', 'comparison']:
        if any(kw in q for kw in INTENT_KEYWORDS[intent]):
            return intent
    return 'strategic'


# ─────────────────────────────────────────────────────────────────────────────
# PASSAGE SELECTOR — intent → type de passage optimal
# ─────────────────────────────────────────────────────────────────────────────

INTENT_TO_PASSAGE = {
    'clinical':   'passage_clinical',
    'commercial': 'passage_commercial',
    'risk':       'passage_strategic',
    'opportunity':'passage_strategic',
    'stock':      'passage_strategic',
    'momentum':   'passage_strategic',
    'trend':      'passage_strategic',
    'gamme':      'passage',
    'product':    'passage',
    'comparison': 'passage',
    'strategic':  'passage',
}

def _detect_passage_type(query: str) -> str:
    return INTENT_TO_PASSAGE.get(detect_intent(query), 'passage')

def _get_passage_for_row(row: pd.Series, passage_type: str) -> str:
    for candidate in [passage_type, 'passage', 'passage_strategic']:
        if candidate in row.index and pd.notna(row.get(candidate)):
            val = str(row[candidate]).strip()
            if val and val not in ('nan', 'None', ''):
                return val
    return (
        f"PRODUIT: {row.get('product_name','')}\n"
        f"GAMME: {row.get('gamme','')}\n"
        f"CYCLE: {row.get('lifecycle_stage_predicted','')}\n"
        f"SCORE OPP: {row.get('opportunity_score','')} | SCORE RISQUE: {row.get('risk_score','')}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# METRIC FOCUS — filtrage par intent
# ─────────────────────────────────────────────────────────────────────────────

INTENT_METRIC_FOCUS = {
    'opportunity': ['opportunity_score', 'momentum_score', 'lifecycle_stage_predicted',
                    'competitor_density', 'stock_status'],
    'risk':        ['risk_score', 'momentum_score', 'substitution_risk',
                    'competitor_density', 'stock_status', 'lifecycle_stage_predicted'],
    'stock':       ['stock_status', 'risk_score', 'momentum_score',
                    'lifecycle_stage_predicted', 'opportunity_score'],
    'commercial':  ['price', 'promo_price', 'discount_pct', 'price_position',
                    'promo_frequency', 'rating', 'review_count'],
    'clinical':    ['form', 'therapeutic_theme', 'product_class'],
    'gamme':       ['gamme', 'opportunity_score', 'risk_score', 'momentum_score',
                    'lifecycle_stage_predicted', 'stock_status', 'price'],
    'product':     ['opportunity_score', 'risk_score', 'momentum_score',
                    'lifecycle_stage_predicted', 'stock_status', 'competitor_density',
                    'substitution_risk', 'price_position', 'rating'],
    'momentum':    ['momentum_score', 'opportunity_score', 'lifecycle_stage_predicted',
                    'global_category_trend', 'competitor_density'],
    'trend':       ['global_category_trend', 'lifecycle_stage_predicted',
                    'momentum_score', 'competitor_density', 'opportunity_score'],
    'comparison':  ['opportunity_score', 'risk_score', 'momentum_score',
                    'price', 'rating', 'lifecycle_stage_predicted', 'stock_status'],
    'strategic':   ['opportunity_score', 'risk_score', 'momentum_score',
                    'lifecycle_stage_predicted', 'stock_status', 'competitor_density',
                    'substitution_risk', 'price_position'],
}

def _build_focused_header(row: pd.Series, intent: str) -> str:
    metrics = INTENT_METRIC_FOCUS.get(intent, INTENT_METRIC_FOCUS['strategic'])
    parts = []
    for m in metrics:
        val = row.get(m, None)
        if val is not None and str(val) not in ('', 'nan', 'None'):
            if isinstance(val, float):
                formatted = f"{val:+.3f}" if m == 'momentum_score' else f"{val:.1f}"
            else:
                formatted = str(val)
            parts.append(f"{m.upper().replace('_', ' ')}={formatted}")
    return f"[{' | '.join(parts)}]" if parts else ""


# ─────────────────────────────────────────────────────────────────────────────
# SIGNAL INTERPRETER — signaux métier par intent
# ─────────────────────────────────────────────────────────────────────────────

def _interpret_metrics(row: pd.Series, intent: str) -> str:
    opp   = row.get('opportunity_score', 0)
    risk  = row.get('risk_score', 0)
    mom   = row.get('momentum_score', 0)
    lc    = str(row.get('lifecycle_stage_predicted', ''))
    stock = str(row.get('stock_status', ''))
    comp  = str(row.get('competitor_density', ''))
    sub   = str(row.get('substitution_risk', ''))
    trend = str(row.get('global_category_trend', ''))

    signals = []

    if intent == 'opportunity':
        if opp >= 7:    signals.append("🏆 OPPORTUNITÉ EXCEPTIONNELLE")
        elif opp >= 5:  signals.append("🟢 bon potentiel")
        if isinstance(mom, float) and mom >= 0.4:
                        signals.append("🚀 forte accélération")
        elif isinstance(mom, float) and 0.2 <= mom < 0.4:
                        signals.append("📈 dynamique positive")
        if lc == 'Croissance':    signals.append("🌱 phase idéale pour investir")
        if comp == 'faible':      signals.append("🏁 terrain libre")
        if trend == 'croissance': signals.append("📊 marché en croissance")

    elif intent == 'risk':
        if risk >= 7:   signals.append("🔴 ALERTE CRITIQUE")
        elif risk >= 5: signals.append("🟠 risque modéré")
        if isinstance(mom, float) and mom < 0:
                        signals.append("📉 décélération")
        if lc == 'Déclin':      signals.append("⚰️ déréférencement à envisager")
        if sub == 'élevé':      signals.append("⚠️ fort risque substitution")
        if comp == 'forte':     signals.append("⚔️ concurrence intense")
        if stock == 'rupture ponctuelle':
                        signals.append("📦 RUPTURE = perte CA")

    elif intent == 'stock':
        if stock == 'rupture ponctuelle':
            urgency = "CRITIQUE" if (isinstance(mom, float) and mom > 0.2) or opp >= 6 else "MODÉRÉE"
            signals.append(f"📦 RUPTURE — URGENCE {urgency}")
        if isinstance(mom, float) and mom >= 0.3:
            signals.append("💰 produit actif — impact CA fort")

    elif intent == 'momentum':
        if isinstance(mom, float):
            if mom >= 0.4:   signals.append("🚀 locomotive")
            elif mom >= 0.2: signals.append("📈 en accélération")
            elif mom < 0:    signals.append("📉 en décélération")
        if lc == 'Croissance':    signals.append("🌱 cycle favorable")
        if trend == 'croissance': signals.append("📊 vent porteur")

    elif intent in ('commercial', 'clinical'):
        pass

    else:
        if opp >= 7:    signals.append("🏆 OPPORTUNITÉ EXCEPTIONNELLE")
        if risk >= 7:   signals.append("🔴 RISQUE CRITIQUE")
        if isinstance(mom, float) and mom >= 0.4:
                        signals.append("🚀 forte accélération")
        elif isinstance(mom, float) and mom < 0:
                        signals.append("📉 décélération")
        if lc == 'Déclin':      signals.append("⚰️ déclin")
        if stock == 'rupture ponctuelle':
                        signals.append("📦 RUPTURE")

    return f"⚡ SIGNAUX: {' | '.join(signals)}" if signals else ""


# ─────────────────────────────────────────────────────────────────────────────
# CONTEXT BLOCK BUILDER — enrichi, ciblé par intent
# Technique : Chain-of-Note → annoter chaque produit avant génération
# ─────────────────────────────────────────────────────────────────────────────

def build_context_block(retrieved: pd.DataFrame, query: str = '') -> str:
    """
    Construit le bloc contexte avec annotations Chain-of-Note :
    chaque produit est pré-annoté avec ses signaux clés AVANT que le LLM génère.
    Ceci réduit les hallucinations en forçant l'ancrage données.
    """
    intent       = detect_intent(query)
    passage_type = INTENT_TO_PASSAGE.get(intent, 'passage')
    blocks       = []
    max_chars    = 550

    for i, (_, row) in enumerate(retrieved.iterrows(), 1):
        score     = row.get('rerank_score', row.get('similarity_score', ''))
        score_str = f"{score:.4f}" if isinstance(score, float) else '–'

        header         = _build_focused_header(row, intent)
        interpretation = _interpret_metrics(row, intent)
        content        = _get_passage_for_row(row, passage_type)
        if len(content) > max_chars:
            content = content[:max_chars] + '…'

        # Chain-of-Note : annotation structurée avant le contenu brut
        chain_note = _build_chain_note(row, intent)

        block_parts = [f"┌─ PRODUIT {i} (relevance={score_str}) ─────────────────────", header]
        if interpretation:
            block_parts.append(interpretation)
        if chain_note:
            block_parts.append(chain_note)
        block_parts.append(content)
        block_parts.append("└───────────────────────────────────────────────────────")

        blocks.append('\n'.join(p for p in block_parts if p))

    return '\n\n'.join(blocks)


def _build_chain_note(row: pd.Series, intent: str) -> str:
    """
    Technique Chain-of-Note (Galileo AI, 2024) :
    Génère une note synthétique structurée par produit AVANT le passage brut.
    Force le LLM à s'ancrer sur des observations factuelles avant de conclure.
    Réduit les hallucinations de ~23% sur les contexts bruités.
    """
    name  = row.get('product_name', 'Produit inconnu')
    opp   = row.get('opportunity_score', 'N/A')
    risk  = row.get('risk_score', 'N/A')
    mom   = row.get('momentum_score', 'N/A')
    lc    = row.get('lifecycle_stage_predicted', 'N/A')
    stock = row.get('stock_status', 'N/A')

    # Note = résumé factuel synthétique structuré
    note_parts = [f"📋 NOTE ANALYTIQUE ({name}) :"]

    # Pertinence selon intent
    if intent == 'opportunity':
        note_parts.append(
            f"  Ce produit est pertinent pour l'analyse opportunités avec "
            f"opp={opp}/8, momentum={mom:+.2f}" if isinstance(mom, float)
            else f"  opp={opp}/8"
        )
    elif intent == 'risk':
        note_parts.append(f"  Profil risque : risk={risk}/8, lifecycle={lc}, stock={stock}")
    elif intent == 'stock':
        note_parts.append(f"  Statut stock : {stock} | Impact potentiel : opp={opp}/8")
    elif intent in ('strategic', 'comparison', 'product', 'gamme'):
        note_parts.append(
            f"  Bilan : opp={opp}/8 | risk={risk}/8 | "
            f"momentum={mom:+.3f}" if isinstance(mom, float)
            else f"  Bilan : opp={opp}/8 | risk={risk}/8"
        )
    else:
        return ""  # Pas de note pour clinical/commercial (données brutes suffisent)

    return '\n'.join(note_parts)


# ─────────────────────────────────────────────────────────────────────────────
# STEP-BACK QUESTIONS — abstraction préalable par intent
# Technique : Step-Back Prompting (Google DeepMind, 2023) — ↑36% vs CoT standard
# Principe : forcer le LLM à raisonner au niveau abstrait AVANT le détail
# ─────────────────────────────────────────────────────────────────────────────

STEP_BACK_QUESTIONS = {
    'opportunity': (
        "Avant de répondre, considère : "
        "Quels sont les facteurs structurels qui font qu'un produit parapharmacie "
        "est une excellente opportunité commerciale sur le marché tunisien ? "
        "(cycle de vie, tendance catégorie, présence concurrentielle, momentum)"
    ),
    'risk': (
        "Avant de répondre, considère : "
        "Quels sont les signaux d'alerte classiques qui indiquent qu'un produit "
        "est en danger commercial imminent ? "
        "(substitution, déclin, rupture sur produit actif, concurrence forte)"
    ),
    'stock': (
        "Avant de répondre, considère : "
        "Comment évaluer l'impact business d'une rupture de stock ? "
        "Un produit en rupture avec momentum positif = perte CA directe et urgente."
    ),
    'gamme': (
        "Avant de répondre, considère : "
        "Comment équilibrer une gamme produit optimale ? "
        "Locomotives (croissance + momentum fort) vs Produits stables vs Boulets (déclin + risque élevé)."
    ),
    'commercial': (
        "Avant de répondre, considère : "
        "Quels sont les leviers de compétitivité prix en parapharmacie tunisienne ? "
        "Position dans la fourchette marché, fréquence promo, perception qualité/prix."
    ),
    'comparison': (
        "Avant de répondre, considère : "
        "Sur quels axes comparer deux produits parapharmacie de façon pertinente ? "
        "Opportunité vs risque, momentum, position prix, maturité du cycle."
    ),
    'trend': (
        "Avant de répondre, considère : "
        "Quelles dynamiques de marché génèrent des fenêtres d'opportunité ? "
        "Catégories en croissance + faible concurrence + produit en phase Croissance."
    ),
    'momentum': (
        "Avant de répondre, considère : "
        "Qu'est-ce qui explique une forte vélocité commerciale d'un produit ? "
        "Combinaison : tendance marché positive + cycle favorable + faible concurrence + présence large."
    ),
    'product': (
        "Avant de répondre, considère : "
        "Quels sont les éléments d'un diagnostic produit complet et actionnable ? "
        "Forces, faiblesses, position marché, décision stratégique recommandée."
    ),
    'clinical': (
        "Avant de répondre, considère : "
        "Qu'est-ce qui différencie un positionnement clinique fort d'un positionnement générique ? "
        "Indications spécifiques, composition différenciante, forme galénique adaptée."
    ),
    'strategic': (
        "Avant de répondre, considère : "
        "Quelle est la logique d'allocation des ressources commerciales dans un portefeuille produits ? "
        "Investir les locomotives, défendre les menacés, désinvestir les boulets."
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# INTENT INSTRUCTIONS v4 — avec Chain-of-Verification intégrée
# Technique : CoVe (Meta AI, 2023) — boucle de vérification avant sortie finale
# ─────────────────────────────────────────────────────────────────────────────

INTENT_INSTRUCTIONS = {

    'opportunity': """
## 🎯 MODE : OPPORTUNITÉS COMMERCIALES

**Protocole de réponse :**
1. Identifie les produits avec `opportunity_score ≥ 5` dans le contexte
2. Classe-les du meilleur au moins bon
3. Pour chacun : raison chiffrée (score + momentum + cycle) + action avec délai

**✅ Inclure :** scores opportunité, momentum, cycle de vie, concurrence, action d'investissement
**❌ Exclure :** risques, alertes, produits avec opp < 5

**Format de sortie requis :**
```
## 🏆 Opportunités Prioritaires

### 1. [NOM PRODUIT] · Gamme [GAMME]
> **Pourquoi maintenant :** [raison chiffrée basée sur les données]
> **Action :** [action concrète] · **Délai :** [délai suggéré]

### 2. ...
```
**Avant de clore, vérifie :** Chaque produit cité est-il bien dans le contexte fourni ? Chaque score mentionné correspond-il aux données ?
""",

    'risk': """
## 🎯 MODE : ALERTES RISQUES

**Protocole de réponse :**
1. Identifie les produits avec `risk_score ≥ 5` dans le contexte
2. Classe du plus critique au moins critique
3. Pour chacun : menace précise + niveau urgence + action défensive

**✅ Inclure :** risk_score, substitution, concurrence, cycle déclin, stock, momentum négatif
**❌ Exclure :** opportunités non liées à la mitigation du risque

**Format de sortie requis :**
```
## 🔴 Alertes Risques — Par Criticité

| Produit | Urgence | Menace principale | Action défensive |
|---------|---------|-------------------|-----------------|
| **[NOM]** | 🔴 CRITIQUE | [menace chiffrée] | [action + délai] |
| **[NOM]** | 🟠 MODÉRÉE | [menace] | [action] |

### 📋 Priorités d'intervention
1. ...
```
**Avant de clore, vérifie :** Les niveaux d'urgence reflètent-ils bien les risk_scores des données ?
""",

    'stock': """
## 🎯 MODE : RUPTURES DE STOCK

**Protocole de réponse :**
1. Identifie tous les produits en `stock_status = rupture ponctuelle`
2. Trie par criticité : momentum élevé + rupture = urgence absolue
3. Estime l'impact business (momentum × opportunité)

**Format de sortie requis :**
```
## 📦 Ruptures — Tableau de Bord

### 🚨 Urgence Absolue (momentum fort + rupture)
| Produit | Momentum | Opp. Score | Impact estimé | Action |
|---------|----------|------------|---------------|--------|
| **[NOM]** | 🚀 +X.XX | X/8 | [fort/moyen] | [réapprovisionnement immédiat] |

### ⚠️ Priorité Standard
| Produit | Stock | Cycle | Action |
|---------|-------|-------|--------|
```
**Avant de clore, vérifie :** Ai-je bien utilisé uniquement les produits marqués rupture dans les données ?
""",

    'product': """
## 🎯 MODE : ANALYSE PRODUIT 360°

**Protocole de réponse :**
Réalise une analyse complète et structurée du produit mentionné dans la question.

**Format de sortie requis :**
```
## 🔍 Analyse 360° — [NOM PRODUIT]
**Gamme :** [GAMME] · **Cycle :** [CYCLE DE VIE]

---
### 📌 Position Marché
[Cycle de vie + tendance catégorie + densité concurrentielle — en 2-3 phrases]

### 💪 Forces
- [Force 1 chiffrée]
- [Force 2 chiffrée]

### ⚠️ Points de Vigilance
- [Vigilance 1 chiffrée]
- [Vigilance 2 chiffrée]

---
### 🎯 Décision Recommandée
> **[INVESTIR / MAINTENIR / REPOSITIONNER / DÉRÉFÉRENCER]**
> [Justification en 2 phrases basée sur les données]
```
**Avant de clore, vérifie :** Ma recommandation est-elle cohérente avec les scores du contexte ?
""",

    'gamme': """
## 🎯 MODE : ANALYSE DE GAMME

**Définitions :**
- 🚀 **Locomotive** = momentum ≥ +0.3 + opportunity_score ≥ 5 + Croissance
- ⚖️ **Stable** = scores intermédiaires, pas de signal fort
- 🪨 **Boulet** = momentum < 0 + risk_score ≥ 5 + Déclin

**Format de sortie requis :**
```
## 📊 Analyse Gamme — [NOM GAMME]

| Produit | Statut | Opp. | Risk | Momentum | Cycle | Action |
|---------|--------|------|------|----------|-------|--------|
| **[NOM]** | 🚀 Locomotive | X/8 | X/8 | +X.XX | [cycle] | Investir |
| **[NOM]** | ⚖️ Stable | X/8 | X/8 | +X.XX | [cycle] | Maintenir |
| **[NOM]** | 🪨 Boulet | X/8 | X/8 | -X.XX | [cycle] | Repositionner |

### 📋 Allocation Recommandée
1. [Action 1 concrète]
2. [Action 2 concrète]
3. [Action 3 concrète]
```
**Avant de clore, vérifie :** Les classifications (locomotive/boulet) correspondent-elles bien aux scores des données ?
""",

    'commercial': """
## 🎯 MODE : ANALYSE COMMERCIALE & PRIX

**Format de sortie requis :**
```
## 💰 Analyse Commerciale

### 📍 Positionnements Prix
| Produit | Prix | Position Marché | Promo | Anomalie |
|---------|------|-----------------|-------|----------|
| **[NOM]** | [X] TND | [prix bas/moyen/élevé] | [X]% | [oui/non] |

### ⚠️ Anomalies Identifiées
- **[Produit]** : [anomalie] → Recommandation : [action]

### ✅ Opportunités Tarifaires
- **[Produit]** : [opportunité] → [action]

### 📋 3 Actions Commerciales Prioritaires
1. [Action + délai]
2. [Action + délai]
3. [Action + délai]
```
**Avant de clore, vérifie :** Les prix et positions mentionnés correspondent-ils bien aux données du contexte ?
""",

    'clinical': """
## 🎯 MODE : ANALYSE CLINIQUE & COMPOSITION

**Format de sortie requis :**
```
## 🏥 Analyse Clinique

| Produit | Forme | Thème Thérapeutique | Classe | Différenciation |
|---------|-------|---------------------|--------|-----------------|
| **[NOM]** | [forme] | [thème] | [classe] | [différenciation clé] |

### 🔬 Focus Composition
**[Produit le plus pertinent] :**
- Actifs clés : [...]
- Indications principales : [...]
- Point de différenciation clinique : [...]
```
**Avant de clore, vérifie :** Toutes les données cliniques sont-elles issues du contexte fourni ?
""",

    'trend': """
## 🎯 MODE : TENDANCES & DYNAMIQUE MARCHÉ

**Format de sortie requis :**
```
## 📊 Tendances Marché — Vue d'Ensemble

### 📈 Catégories en Croissance
| Catégorie/Thème | Produits Vital alignés | Momentum moyen | Opportunité |
|-----------------|----------------------|----------------|-------------|
| [thème] | [produits] | [valeur] | [action] |

### 📉 Catégories en Plateau / Déclin
| Catégorie | Signal | Risque | Action défensive |
|-----------|--------|--------|-----------------|
| [thème] | [signal] | [niveau] | [action] |

### 🎯 Top 3 Fenêtres d'Opportunité
1. [Fenêtre 1 — timing + action]
2. [Fenêtre 2 — timing + action]
3. [Fenêtre 3 — timing + action]
```
**Avant de clore, vérifie :** Les tendances citées correspondent-elles aux champs `global_category_trend` des données ?
""",

    'momentum': """
## 🎯 MODE : ANALYSE MOMENTUM (Vélocité Commerciale)

**Format de sortie requis :**
```
## ⚡ Analyse Momentum — Vélocité Commerciale

### 🚀 Locomotives (momentum ≥ +0.3)
| Produit | Momentum | Drivers | Cycle | Action |
|---------|----------|---------|-------|--------|
| **[NOM]** | **+X.XX** | [tendance + concurrence + cycle] | [cycle] | Capitaliser |

### 📉 Signaux d'Alerte (momentum négatif)
| Produit | Momentum | Cause | Urgence | Intervention |
|---------|----------|-------|---------|--------------|
| **[NOM]** | **-X.XX** | [cause] | [niveau] | [action] |

### 💡 Insights Clés
- [Insight 1 basé sur les données]
- [Insight 2 basé sur les données]
```
**Avant de clore, vérifie :** Les valeurs de momentum correspondent-elles exactement aux données du contexte ?
""",

    'comparison': """
## 🎯 MODE : COMPARAISON PRODUITS

**Format de sortie requis :**
```
## ⚖️ Comparaison Produits

| Critère | [PRODUIT A] | [PRODUIT B] |
|---------|-------------|-------------|
| 🏆 Opportunité | X/8 — [interprétation] | X/8 — [interprétation] |
| 🔴 Risque | X/8 — [interprétation] | X/8 — [interprétation] |
| ⚡ Momentum | +X.XX | +X.XX |
| 🌱 Cycle de vie | [phase] | [phase] |
| 💰 Prix | [position] | [position] |
| 📦 Stock | [status] | [status] |
| ⭐ Note client | X/5 | X/5 |

---
### 🏆 Verdict
> [Lequel prioriser et pourquoi — 2-3 phrases basées sur les données]

### 📋 Action par produit
- **[Produit A] :** [action concrète]
- **[Produit B] :** [action concrète]
```
**Avant de clore, vérifie :** Tous les scores du tableau proviennent-ils bien du contexte fourni ?
""",

    'strategic': """
## 🎯 MODE : ANALYSE STRATÉGIQUE COMPLÈTE

**Format de sortie requis :**
```
## 🧠 Synthèse Stratégique — Portefeuille Vital

---
### 🟢 Opportunités Prioritaires
| Produit | Gamme | Opp. | Momentum | Action immédiate |
|---------|-------|------|----------|-----------------|
| **[NOM]** | [gamme] | X/8 | +X.XX | [action] |

### 🔴 Risques à Surveiller
| Produit | Gamme | Risk | Signal | Action défensive |
|---------|-------|------|--------|-----------------|
| **[NOM]** | [gamme] | X/8 | [signal] | [action] |

---
### 📋 Plan d'Action Immédiat (72h)
| Priorité | Action | Responsable suggéré | Délai |
|----------|--------|---------------------|-------|
| 🔴 URGENT | [action] | [responsable] | [délai] |
| 🟠 IMPORTANT | [action] | [responsable] | [délai] |
| 🟡 PLANIFIÉ | [action] | [responsable] | [délai] |
---
```
**Avant de clore, vérifie :** Mon plan d'action est-il entièrement basé sur les données du contexte ?
""",
}


# ─────────────────────────────────────────────────────────────────────────────
# NEGATIVE GUARDS — contraintes négatives explicites par intent
# Technique : Output Format Control (MLMastery, 2025) — réduit les divagations
# ─────────────────────────────────────────────────────────────────────────────

NEGATIVE_GUARDS = {
    'opportunity': (
        "⛔ **INTERDIT dans cette réponse :** risques, alertes, produits en déclin, "
        "produits avec opportunity_score < 5. Si un tel produit apparaît dans le contexte → l'ignorer."
    ),
    'risk': (
        "⛔ **INTERDIT :** opportunités positives non liées à la défense/atténuation. "
        "Produits avec risk_score < 4 → ignorer."
    ),
    'stock': (
        "⛔ **INTERDIT :** analyser des produits en stock normal. "
        "Focus exclusif sur stock_status = rupture ponctuelle."
    ),
    'clinical': (
        "⛔ **INTERDIT :** scores commerciaux, prix, momentum dans cette réponse. "
        "Clinique et composition uniquement."
    ),
    'commercial': (
        "⛔ **INTERDIT :** analyses cliniques, cycles de vie non liés au prix. "
        "Prix, promos, remises, positionnement tarifaire uniquement."
    ),
    'momentum': (
        "⛔ **INTERDIT :** focus clinique, composition. "
        "Vélocité commerciale et drivers de momentum uniquement."
    ),
    'comparison': (
        "⛔ **INTERDIT :** analyser des produits qui ne sont PAS dans la comparaison demandée. "
        "Tableau comparatif structuré obligatoire — pas de texte libre."
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# FORMAT PROMPT FINAL v4 — assemblage complet avec toutes les techniques
# ─────────────────────────────────────────────────────────────────────────────

def format_prompt(user_query: str, context: str) -> str:
    """
    Construit le prompt final v4 avec :
    1. System prompt RAG-strict (ancrage données, anti-hallucination)
    2. Step-Back Question (abstraction préalable avant raisonnement détaillé)
    3. Instruction intent-spécifique avec format Markdown riche
    4. Negative Guards (contraintes d'exclusion explicites)
    5. Contexte produits avec Chain-of-Note (annotations analytiques pré-générées)
    6. Chain-of-Verification reminder (auto-vérification avant sortie)
    7. Question utilisateur
    Chaque appel est indépendant — aucune mémoire entre les questions.
    """
    intent             = detect_intent(user_query)
    intent_instruction = INTENT_INSTRUCTIONS.get(intent, INTENT_INSTRUCTIONS['strategic'])
    step_back_q        = STEP_BACK_QUESTIONS.get(intent, '')
    negative_guard     = NEGATIVE_GUARDS.get(intent, '')

    # ── Assemblage final — ordre optimisé pour anti-hallucination ───────────
    prompt = (
        # 1. Identité + règles système
        f"<|system|>\n{SYSTEM_PROMPT}\n</s>\n"
        f"<|user|>\n"

        # 2. Step-Back : abstraction avant détail (↑36% précision)
        + (f"### 🔭 Cadrage préalable (Step-Back)\n{step_back_q}\n\n---\n\n" if step_back_q else "")

        # 3. Instructions intent + format de sortie attendu
        + f"{intent_instruction}\n"

        # 4. Negative Guards (ce qui est interdit)
        + (f"\n{negative_guard}\n" if negative_guard else "")

        # 5. Données produits (avec Chain-of-Note annotations)
        + f"\n---\n### 📦 Données Produits Vital (contexte RAG)\n"
          f"> **Règle stricte :** Ta réponse doit s'appuyer EXCLUSIVEMENT sur ces données.\n"
          f"> Si une information n'est pas dans ce contexte → écris `[donnée non disponible]`.\n\n"
        + f"{context}\n"

        # 6. Rappel Chain-of-Verification avant génération
        + "\n---\n"
          "### ✅ Vérification avant réponse\n"
          "Avant de générer ta réponse finale, vérifie mentalement :\n"
          "- [ ] Chaque produit cité existe dans les données ci-dessus\n"
          "- [ ] Chaque score/chiffre mentionné est traceable au contexte\n"
          "- [ ] Le format Markdown demandé (tableaux, titres, gras) est respecté\n"
          "- [ ] La réponse est focalisée sur l'intent détecté\n\n"

        # 7. Question utilisateur
        + f"**❓ Question :** {user_query}\n"
          "</s>\n"
          "<|assistant|>\n"
    )

    return prompt
