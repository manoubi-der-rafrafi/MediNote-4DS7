from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from hashem_integration.config import is_hashem_chat_enabled
from hashem_integration.loader import HashemModuleLoadError, load_hashem_orchestrator_module


@dataclass(frozen=True)
class HashemRouteDecision:
    should_route: bool
    confidence: float = 0.0
    reason: str = ""
    task_id: str | None = None


class HashemRouter:
    _ENTITY_KEYWORDS = (
        "pharmacie",
        "pharmacy",
        "delegue",
        "délégué",
        "delegate",
        "commercial",
        "superviseur",
        "doctor",
        "medecin",
        "médecin",
        "campaign",
        "campagne",
        "marketing",
        "visite",
        "visit",
        "zone",
        "region",
        "région",
        "roi",
        "churn",
    )
    _ANALYTICS_KEYWORDS = (
        "risque",
        "risk",
        "prediction",
        "predict",
        "prevision",
        "prévision",
        "forecast",
        "performance",
        "score",
        "ranking",
        "priorite",
        "priorité",
        "sentiment",
        "segment",
        "trend",
        "tendance",
        "annulation",
        "paiement",
    )

    def detect(self, user_request: str) -> HashemRouteDecision:
        if not is_hashem_chat_enabled():
            return HashemRouteDecision(False, reason="hashem_disabled")

        module_decision = self._detect_with_hashem_rules(user_request)
        if module_decision.should_route:
            return module_decision

        return self._detect_with_local_keywords(user_request)

    def _detect_with_hashem_rules(self, user_request: str) -> HashemRouteDecision:
        try:
            orchestrator_module = load_hashem_orchestrator_module()
        except HashemModuleLoadError:
            return HashemRouteDecision(False, reason="hashem_module_unavailable")

        try:
            intent_agent = orchestrator_module.IntentAgent(api_key="")
            intent = intent_agent._rule_extract(user_request)
        except Exception:
            return HashemRouteDecision(False, reason="hashem_rule_detection_failed")

        task_id = str(intent.get("task_id", "")).strip()
        confidence = float(intent.get("confidence", 0) or 0)
        if task_id and task_id != "unknown" and confidence >= 0.5:
            return HashemRouteDecision(
                True,
                confidence=confidence,
                reason="hashem_rule_match",
                task_id=task_id,
            )

        return HashemRouteDecision(False, confidence=confidence, task_id=task_id or None)

    def _detect_with_local_keywords(self, user_request: str) -> HashemRouteDecision:
        normalized = user_request.strip().lower()
        entity_hits = sum(
            1 for keyword in self._ENTITY_KEYWORDS if keyword in normalized
        )
        analytics_hits = sum(
            1 for keyword in self._ANALYTICS_KEYWORDS if keyword in normalized
        )
        if entity_hits == 0 or analytics_hits == 0:
            return HashemRouteDecision(False, reason="keyword_threshold_not_met")

        confidence = min(0.95, 0.35 + entity_hits * 0.15 + analytics_hits * 0.12)
        return HashemRouteDecision(
            True,
            confidence=round(confidence, 2),
            reason="local_keyword_match",
        )


def should_try_hashem_fallback(classification_result: dict[str, Any] | list[Any]) -> bool:
    if not isinstance(classification_result, dict):
        return False

    intent = str(classification_result.get("intent", "")).strip().lower()
    if intent in {"", "inconnue", "unknown"}:
        return True

    action = str(classification_result.get("action", "")).strip().lower()
    return not action and intent not in {"rapport", "publication", "produit", "conversation"}
