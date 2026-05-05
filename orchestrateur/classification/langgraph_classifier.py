from __future__ import annotations

from typing import Any


class LangGraphClassifier:
    def __init__(self, legacy_service: Any) -> None:
        self.legacy_service = legacy_service
        self._graph = None
        self.last_failure_reason: str | None = None

    def classify(
        self,
        *,
        user_request: str,
        report_text: str | None = None,
    ) -> dict[str, Any] | None:
        graph = self._get_graph()
        if graph is None:
            self.last_failure_reason = self.last_failure_reason or "langgraph_unavailable"
            return None

        result = graph.invoke(
            {
                "user_request": user_request,
                "report_text": report_text,
            }
        )
        if not isinstance(result, dict):
            self.last_failure_reason = "invalid_graph_result"
            return None
        self.last_failure_reason = result.get("failure_reason")
        classification = result.get("classification")
        if isinstance(classification, dict):
            self.last_failure_reason = None
            return classification
        return None

    def _get_graph(self) -> Any | None:
        if self._graph is not None:
            return self._graph

        try:
            from langgraph.graph import END, START, StateGraph
        except Exception as exc:
            self.last_failure_reason = f"langgraph_unavailable:{exc.__class__.__name__}"
            return None

        from .state import ClassificationState

        graph = StateGraph(ClassificationState)
        graph.add_node("classify_request", self._classify_request)
        graph.add_edge(START, "classify_request")
        graph.add_edge("classify_request", END)
        self._graph = graph.compile()
        return self._graph

    def _classify_request(self, state: dict[str, Any]) -> dict[str, Any]:
        user_request = str(state.get("user_request", "")).strip()
        if not user_request:
            return {
                "classification": None,
                "failed": True,
                "failure_reason": "empty_request",
            }

        classifiers = (
            self.legacy_service._try_local_report_deletion_classification,
            self.legacy_service._try_local_report_classification,
            self._try_report_database_field_query,
            self._try_publication_database_field_query,
            self.legacy_service._try_local_conversation_database_classification,
            self.legacy_service._try_local_publication_classification,
            self.legacy_service._try_local_product_classification,
        )
        for classifier in classifiers:
            result = classifier(user_request)
            if result is not None:
                return {
                    "classification": result,
                    "failed": False,
                    "failure_reason": None,
                }

        if self.legacy_service._looks_like_product_management_request(user_request):
            return {
                "classification": {
                    "intent": "produit",
                    "action": "product_management",
                },
                "failed": False,
                "failure_reason": None,
            }

        return {
            "classification": None,
            "failed": True,
            "failure_reason": "no_langgraph_match",
        }

    def _try_report_database_field_query(
        self,
        user_request: str,
    ) -> dict[str, Any] | None:
        normalized = self.legacy_service._normalize_text(user_request)
        query_markers = (
            "combien",
            "liste",
            "lister",
            "quels",
            "quelles",
            "montre",
            "affiche",
            "donne",
            "show",
            "list",
            "count",
            "how many",
            "statistique",
            "stats",
            "analyse",
        )
        report_field_markers = (
            "point fort",
            "points forts",
            "structured_reports",
            "text corrige",
            "texte corrige",
            "raw text",
            "potentiel",
            "personnel",
            "emplacement",
            "stock",
            "conseil",
            "mise en place",
            "mouvement",
            "rapport structure",
            "rapports structures",
        )

        if not any(marker in normalized for marker in query_markers):
            return None
        if not any(marker in normalized for marker in report_field_markers):
            return None

        return {
            "intent": "rapport",
            "action": "query_database",
            "response_language": self.legacy_service._detect_response_language(
                user_request
            ),
            "db_scope": {"tables": ["structured_reports"]},
            "user_question": user_request.strip(),
            "query_kind": self.legacy_service._infer_query_kind(normalized),
        }

    def _try_publication_database_field_query(
        self,
        user_request: str,
    ) -> dict[str, Any] | None:
        normalized = self.legacy_service._normalize_text(user_request)
        query_markers = (
            "combien",
            "tout",
            "tous",
            "toute",
            "toutes",
            "liste",
            "lister",
            "quels",
            "quelles",
            "information",
            "informations",
            "informaiton",
            "informaitons",
            "montre",
            "affiche",
            "donne",
            "je veux",
            "veux",
            "tableau",
            "show",
            "list",
            "all",
            "info",
            "information",
            "informations",
            "table",
            "count",
            "how many",
            "historique",
            "dernier",
            "derniere",
            "generes",
            "generees",
            "generated",
        )
        publication_markers = (
            "publication",
            "publications",
            "post",
            "posts",
            "media",
            "medias",
            "contenu genere",
            "contenus generes",
            "generation image",
            "generations images",
            "generation video",
            "generations videos",
            "generated_images",
            "generated_videos",
            "saved files",
            "fichiers generes",
            "asset",
            "assets",
        )

        if not any(marker in normalized for marker in query_markers):
            return None
        if not any(marker in normalized for marker in publication_markers):
            return None

        media_scope = self.legacy_service._resolve_publication_media_scope(normalized)
        if media_scope == "missing":
            has_generic_media_request = any(
                marker in normalized
                for marker in (
                    "publication",
                    "publications",
                    "post",
                    "posts",
                    "media",
                    "medias",
                    "contenu genere",
                    "contenus generes",
                    "asset",
                    "assets",
                )
            )
            if has_generic_media_request:
                media_scope = "both"

        tables: list[str] = []
        if media_scope == "image":
            tables = ["generated_images"]
        elif media_scope == "video":
            tables = ["generated_videos"]
        elif media_scope == "both":
            tables = ["generated_images", "generated_videos"]

        return {
            "intent": "publication",
            "action": "query_database",
            "response_language": self.legacy_service._detect_response_language(
                user_request
            ),
            "media_scope": media_scope,
            "db_scope": {"tables": tables},
            "user_question": user_request.strip(),
            "query_kind": self.legacy_service._infer_query_kind(normalized),
        }
