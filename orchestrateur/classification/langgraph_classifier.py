from __future__ import annotations

from collections import defaultdict
from typing import Any

from .example_repository import load_recent_examples


KEYWORD_GROUPS: dict[str, tuple[str, ...]] = {
    "music_recommendation": (
        "musique",
        "music",
        "audio",
        "song",
        "songs",
        "soundtrack",
        "background music",
        "fond sonore",
        "recommande",
        "recommend",
    ),
    "rapport": (
        "rapport",
        "report",
        "structurer",
        "structure",
        "analyser",
        "analyse",
        "corriger",
        "corrige",
        "traiter",
        "traite",
        "resumer",
        "resume",
    ),
    "rapport_delete": (
        "delete",
        "remove",
        "supprimer",
        "supprime",
        "supprimez",
        "effacer",
        "efface",
        "effacez",
    ),
    "rapport_query": (
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
        "structured_reports",
        "text corrige",
        "texte corrige",
        "raw text",
    ),
    "publication": (
        "publication",
        "publications",
        "post",
        "posts",
        "image",
        "images",
        "photo",
        "photos",
        "visuel",
        "visuels",
        "affiche",
        "video",
        "videos",
        "vdo",
        "reel",
        "media",
        "medias",
    ),
    "publication_query": (
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
        "historique",
        "generated",
        "generated_images",
        "generated_videos",
        "asset",
        "assets",
    ),
    "publication_generation": (
        "prochaine occasion",
        "occasion la plus proche",
        "prochaine fete",
        "prochain evenement",
        "next event",
        "upcoming event",
        "examen",
        "examens",
        "exam",
        "bac",
        "revision",
    ),
}


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
        graph.add_node("extract_keywords", self._extract_keywords)
        graph.add_node("load_historical_examples", self._load_historical_examples)
        graph.add_node("classify_request", self._classify_request)
        graph.add_edge(START, "extract_keywords")
        graph.add_edge("extract_keywords", "load_historical_examples")
        graph.add_edge("load_historical_examples", "classify_request")
        graph.add_edge("classify_request", END)
        self._graph = graph.compile()
        return self._graph

    def _extract_keywords(self, state: dict[str, Any]) -> dict[str, Any]:
        user_request = str(state.get("user_request", "")).strip()
        normalized = self.legacy_service._normalize_text(user_request)
        keyword_hits: dict[str, list[str]] = {}
        for group_name, keywords in KEYWORD_GROUPS.items():
            matches = [keyword for keyword in keywords if keyword in normalized]
            if matches:
                keyword_hits[group_name] = matches
        return {"keyword_hits": keyword_hits}

    def _load_historical_examples(self, state: dict[str, Any]) -> dict[str, Any]:
        user_request = str(state.get("user_request", "")).strip()
        if not user_request:
            return {"historical_examples": []}

        keyword_hits = state.get("keyword_hits") or {}
        relevant_keywords = {
            keyword
            for matches in keyword_hits.values()
            for keyword in matches
            if len(keyword.strip()) >= 4
        }
        if not relevant_keywords:
            return {"historical_examples": []}

        examples = []
        try:
            historical_examples = load_recent_examples(limit=250)
        except Exception as exc:
            self.last_failure_reason = f"historical_examples_unavailable:{exc.__class__.__name__}"
            return {"historical_examples": []}

        for example in historical_examples:
            normalized_text = self.legacy_service._normalize_text(example.user_text)
            shared_keywords = sorted(
                keyword for keyword in relevant_keywords if keyword in normalized_text
            )
            if not shared_keywords:
                continue
            score = len(shared_keywords)
            if example.intent == "rapport" and "rapport" in shared_keywords:
                score += 1
            if example.intent == "publication" and any(
                keyword in shared_keywords
                for keyword in ("publication", "image", "video", "media", "post", "music", "audio")
            ):
                score += 1
            examples.append(
                {
                    "user_text": example.user_text,
                    "intent": example.intent,
                    "action": example.action,
                    "created_at": example.created_at,
                    "shared_keywords": shared_keywords,
                    "score": score,
                }
            )

        examples.sort(
            key=lambda item: (
                int(item.get("score", 0)),
                len(item.get("shared_keywords") or []),
                str(item.get("created_at") or ""),
            ),
            reverse=True,
        )
        return {"historical_examples": examples[:5]}

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
            self.legacy_service._try_local_music_recommendation_classification,
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

        example_based = self._classify_from_historical_examples(state)
        if example_based is not None:
            return {
                "classification": example_based,
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

    def _classify_from_historical_examples(
        self,
        state: dict[str, Any],
    ) -> dict[str, Any] | None:
        examples = state.get("historical_examples")
        if not isinstance(examples, list) or not examples:
            return None

        label_scores: dict[tuple[str, str], int] = defaultdict(int)
        label_examples: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for example in examples:
            if not isinstance(example, dict):
                continue
            intent = str(example.get("intent") or "").strip().lower()
            action = str(example.get("action") or "").strip().lower()
            if not intent or not action:
                continue
            label = (intent, action)
            label_scores[label] += int(example.get("score") or 0)
            label_examples[label].append(example)

        if not label_scores:
            return None

        best_label, best_score = max(
            label_scores.items(),
            key=lambda item: (item[1], len(label_examples[item[0]])),
        )
        best_examples = label_examples[best_label]
        distinct_keywords = {
            keyword
            for example in best_examples
            for keyword in example.get("shared_keywords") or []
        }
        if best_score < 2 or len(distinct_keywords) < 2:
            return None

        user_request = str(state.get("user_request", "")).strip()
        classification = self._build_classification_from_label(
            user_request=user_request,
            intent=best_label[0],
            action=best_label[1],
        )
        if classification is None:
            return None
        classification["classification_examples"] = [
            {
                "user_text": example.get("user_text"),
                "intent": example.get("intent"),
                "action": example.get("action"),
                "shared_keywords": example.get("shared_keywords"),
                "score": example.get("score"),
            }
            for example in best_examples[:3]
        ]
        return classification

    def _build_classification_from_label(
        self,
        *,
        user_request: str,
        intent: str,
        action: str,
    ) -> dict[str, Any] | None:
        normalized = self.legacy_service._normalize_text(user_request)
        response_language = self.legacy_service._detect_response_language(user_request)

        if intent == "rapport" and action == "delete_report":
            return {
                "intent": "rapport",
                "action": "delete_report",
                "response_language": response_language,
                "report_id": self.legacy_service._extract_report_identifier(user_request),
            }

        if intent == "rapport" and action == "structure_report":
            return {
                "intent": "rapport",
                "action": "structure_report",
                "response_language": response_language,
                "rapport": self.legacy_service._extract_inline_report_text(user_request),
            }

        if intent == "rapport" and action == "query_database":
            return {
                "intent": "rapport",
                "action": "query_database",
                "response_language": response_language,
                "db_scope": {"tables": ["structured_reports"]},
                "user_question": user_request,
                "query_kind": self.legacy_service._infer_query_kind(normalized),
            }

        if intent == "publication" and action == "generate_publication":
            media_type = "non_precise"
            if any(keyword in normalized for keyword in ("image", "photo", "visuel", "affiche")):
                media_type = "image"
            elif any(keyword in normalized for keyword in ("video", "vdo", "reel")):
                media_type = "video"

            generation_mode = "missing"
            if self.legacy_service._looks_like_next_occasion_request(normalized):
                generation_mode = "next_occasion"
            elif any(
                keyword in normalized
                for keyword in ("examen", "examens", "exam", "bac", "revision")
            ):
                generation_mode = "exam_period"
            else:
                occasion = self.legacy_service._extract_occasion_fragment(user_request)
                if occasion:
                    generation_mode = "given_occasion"
                else:
                    occasion = None

            return {
                "intent": "publication",
                "action": "generate_publication",
                "response_language": response_language,
                "media_type": media_type,
                "generation_mode": generation_mode,
                "occasion": occasion if generation_mode == "given_occasion" else None,
                "date": None,
            }

        if intent == "publication" and action == "recommend_music":
            generation_mode = "missing"
            if self.legacy_service._looks_like_next_occasion_request(normalized):
                generation_mode = "next_occasion"
            elif any(
                keyword in normalized
                for keyword in ("examen", "examens", "exam", "bac", "revision")
            ):
                generation_mode = "exam_period"
            else:
                occasion = self.legacy_service._extract_occasion_fragment(user_request)
                if occasion:
                    generation_mode = "given_occasion"
                else:
                    occasion = None

            return {
                "intent": "publication",
                "action": "recommend_music",
                "response_language": response_language,
                "media_type": "audio",
                "generation_mode": generation_mode,
                "occasion": occasion if generation_mode == "given_occasion" else None,
                "date": None,
                "top_k": 5,
            }

        if intent == "publication" and action == "query_database":
            media_scope = self.legacy_service._resolve_publication_media_scope(normalized)
            if media_scope == "missing" and any(
                keyword in normalized
                for keyword in ("publication", "publications", "post", "posts", "media", "medias")
            ):
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
                "response_language": response_language,
                "media_scope": media_scope,
                "db_scope": {"tables": tables},
                "user_question": user_request,
                "query_kind": self.legacy_service._infer_query_kind(normalized),
            }

        return None

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
            "image",
            "images",
            "photo",
            "photos",
            "video",
            "videos",
            "vdo",
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
