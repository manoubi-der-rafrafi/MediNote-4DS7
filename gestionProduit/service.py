from __future__ import annotations

import re
import traceback
import unicodedata
from typing import Any

from vital_agent.agent import VitalAgent


class ProductServiceError(RuntimeError):
    pass


_PM_PATTERNS = [
    "product manager",
    "product management",
    "gestion de produit",
    "gestion produit",
    "roadmap",
    "mvp",
    "backlog",
    "user stories",
    "user story",
]

_SECTION_ALIASES = {
    "context": {"contexte", "context"},
    "problem": {"probleme", "probleme a resoudre", "problem"},
    "objective": {"objectif", "objectif business", "objective"},
    "users": {"utilisateurs", "utilisateurs cibles", "personas"},
    "constraints": {"contraintes", "constraints"},
}


def _normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9 ]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _is_product_management_request(user_request: str) -> bool:
    text = _normalize(user_request)
    return any(pattern in text for pattern in _PM_PATTERNS)


def _section_key(label: str) -> str | None:
    normalized = _normalize(label)
    for key, aliases in _SECTION_ALIASES.items():
        if normalized in aliases:
            return key
    return None


def _extract_sections(user_request: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current_key: str | None = None

    for raw_line in user_request.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        match = re.match(r"^([^:]{1,80})\s*:\s*(.*)$", line)
        if match:
            key = _section_key(match.group(1))
            if key:
                current_key = key
                sections.setdefault(current_key, [])
                inline_value = match.group(2).strip()
                if inline_value:
                    sections[current_key].append(inline_value)
                continue

        if current_key:
            sections[current_key].append(line)

    return {key: "\n".join(value).strip() for key, value in sections.items()}


def _first_sentence(text: str, fallback: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return fallback
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    return parts[0].strip() or fallback


def _detect_personas(user_request: str) -> list[tuple[str, str, str]]:
    normalized = _normalize(user_request)
    candidates = [
        (
            "Responsable commercial",
            "Identifier les produits a pousser et suivre les priorites terrain.",
            "Vision claire des opportunites, risques et actions commerciales.",
        ),
        (
            "Chef produit",
            "Piloter le cycle de vie produit et arbitrer les ameliorations.",
            "Donnees centralisees, alertes et priorisation fiable.",
        ),
        (
            "Direction",
            "Decider vite sur les investissements, arbitrages et retraits.",
            "Synthese strategique et indicateurs de decision.",
        ),
    ]

    detected = [
        persona
        for persona in candidates
        if _normalize(persona[0]) in normalized
    ]
    return detected or candidates


def _build_table(headers: list[str], rows: list[list[str]]) -> str:
    header = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join(["---"] * len(headers)) + " |"
    body = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header, separator, *body])


def _build_product_management_response(user_request: str) -> str:
    sections = _extract_sections(user_request)
    context = sections.get("context", "")
    problem = sections.get("problem", "")
    objective = sections.get("objective", "")
    constraints = sections.get("constraints", "")

    product_summary = _first_sentence(
        context,
        "Application web de gestion et d'analyse du portefeuille produit.",
    )
    problem_summary = _first_sentence(
        problem,
        "Les decisions produit sont difficiles a prioriser faute de vision centralisee.",
    )
    objective_summary = _first_sentence(
        objective,
        "Construire un MVP qui centralise les donnees produit et aide a prioriser les actions.",
    )
    constraint_summary = (
        re.sub(r"\s+", " ", constraints).strip()
        or "MVP simple, utilisable rapidement, avec recommandations concretes."
    )
    personas = _detect_personas(user_request)

    persona_rows = [[name, need, value] for name, need, value in personas]
    needs_rows = [
        ["Centraliser", "Consulter une fiche produit unique avec indicateurs cles.", "Reduire les fichiers disperses."],
        ["Prioriser", "Savoir quels produits pousser, surveiller, ameliorer ou retirer.", "Concentrer les efforts sur les bons produits."],
        ["Alerter", "Voir les produits a risque ou en rupture.", "Agir avant perte commerciale."],
        ["Decider", "Disposer d'une synthese claire pour les arbitrages.", "Accelerer les decisions management."],
    ]
    mvp_rows = [
        ["Tableau de bord produit", "Vue des produits avec score opportunite, risque et momentum.", "Must"],
        ["Fiche produit", "Details, statut, indicateurs, historique et recommandations.", "Must"],
        ["Priorisation automatique", "Classement des produits par action recommandee.", "Must"],
        ["Alertes risques", "Detection des ruptures, declins et produits a surveiller.", "Must"],
        ["Recherche et filtres", "Filtrer par gamme, statut, score, risque ou opportunite.", "Should"],
        ["Export synthese", "Exporter les priorites pour reunion ou reporting.", "Should"],
    ]
    out_of_scope_rows = [
        ["Prevision avancee par IA", "A garder apres validation du MVP et qualite des donnees."],
        ["Workflow complet de validation", "Utile plus tard pour les grandes equipes."],
        ["Integration ERP/CRM complexe", "A traiter apres stabilisation du modele de donnees."],
        ["Application mobile native", "Non prioritaire si l'usage principal est bureau."],
    ]
    story_rows = [
        ["Responsable commercial", "voir les produits a fort potentiel", "preparer les actions de vente prioritaires"],
        ["Chef produit", "identifier les produits a risque", "decider s'il faut ameliorer, repositionner ou retirer"],
        ["Direction", "consulter une synthese des priorites", "arbitrer rapidement les investissements"],
        ["Utilisateur metier", "filtrer les produits par gamme et statut", "trouver rapidement les cas importants"],
        ["Manager", "exporter un recapitulatif", "partager les priorites en reunion"],
    ]
    backlog_rows = [
        ["P0", "Importer et normaliser les donnees produit", "Base necessaire au MVP"],
        ["P0", "Afficher le tableau de bord produit", "Premier ecran de pilotage"],
        ["P0", "Calculer les scores opportunite/risque/momentum", "Priorisation exploitable"],
        ["P0", "Afficher les recommandations par produit", "Aide directe a la decision"],
        ["P1", "Ajouter filtres, recherche et tri", "Usage quotidien plus rapide"],
        ["P1", "Creer les alertes risques et ruptures", "Reaction metier plus rapide"],
        ["P2", "Exporter la synthese", "Support reporting et comite"],
    ]
    roadmap_rows = [
        ["Phase 1 - MVP", "Centralisation donnees, dashboard, fiches produit, scores de base.", "Produit utilisable par l'equipe."],
        ["Phase 2 - Decision", "Alertes, recommandations, filtres avances, export.", "Priorisation plus fiable."],
        ["Phase 3 - Industrialisation", "Historique, integrations, previsions, workflows.", "Passage a l'echelle."],
    ]

    return "\n\n".join(
        [
            "## 1. Resume du produit\n"
            f"{product_summary} Le produit vise a donner une vision claire du portefeuille et des actions prioritaires.",
            "## 2. Probleme et objectif\n"
            f"**Probleme :** {problem_summary}\n\n"
            f"**Objectif business :** {objective_summary}\n\n"
            f"**Contraintes prises en compte :** {constraint_summary}",
            "## 3. Personas\n" + _build_table(["Persona", "Besoin principal", "Valeur attendue"], persona_rows),
            "## 4. Besoins utilisateurs\n" + _build_table(["Besoin", "Description", "Impact"], needs_rows),
            "## 5. Fonctionnalites MVP\n" + _build_table(["Fonctionnalite", "Description", "Priorite"], mvp_rows),
            "## 6. Fonctionnalites hors MVP\n" + _build_table(["Fonctionnalite", "Pourquoi plus tard"], out_of_scope_rows),
            "## 7. User stories\n"
            + _build_table(["En tant que", "Je veux", "Afin de"], story_rows),
            "## 8. Backlog priorise\n" + _build_table(["Priorite", "Item", "Raison"], backlog_rows),
            "## 9. Roadmap en 3 phases\n" + _build_table(["Phase", "Contenu", "Resultat attendu"], roadmap_rows),
            "## 10. Recommandations finales\n"
            "- Commencer par un MVP centre sur le dashboard, les fiches produit et la priorisation.\n"
            "- Eviter les integrations complexes avant validation de l'usage par les equipes metier.\n"
            "- Definir des seuils simples pour classer les produits : pousser, surveiller, ameliorer, retirer.\n"
            "- Tester le MVP avec un petit groupe : responsable commercial, chef produit et direction.",
        ]
    )


class ProductService:
    def __init__(self) -> None:
        self._agent: VitalAgent | None = None

    def handle(
        self,
        user_request: str,
        classification_result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        is_product_management = _is_product_management_request(user_request)
        if is_product_management:
            answer = _build_product_management_response(user_request)
        else:
            try:
                answer = self._get_agent().ask(user_request)
            except Exception as exc:
                print("[ProductService] VitalAgent failed:")
                traceback.print_exc()
                raise ProductServiceError(
                    f"{exc.__class__.__name__}: {exc}"
                ) from exc

        action = ""
        if isinstance(classification_result, dict):
            action = str(classification_result.get("action", "")).strip()

        return {
            "status": "success",
            "action": "product_management" if is_product_management else action or "product_query",
            "response": answer,
        }

    def _get_agent(self) -> VitalAgent:
        if self._agent is None:
            self._agent = VitalAgent()
        return self._agent
