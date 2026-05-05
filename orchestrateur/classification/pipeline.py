from __future__ import annotations

from typing import Any

from .gemini_fallback_classifier import GeminiFallbackClassifier
from .langgraph_classifier import LangGraphClassifier
from .parser import ClassificationParser
from .validator import ClassificationValidator


class ClassificationPipeline:
    def __init__(self, legacy_service: Any) -> None:
        self.legacy_service = legacy_service
        self.langgraph_classifier = LangGraphClassifier(legacy_service)
        self.gemini_fallback_classifier = GeminiFallbackClassifier(legacy_service)
        self.parser = ClassificationParser(legacy_service)
        self.validator = ClassificationValidator(legacy_service)

    def classify(
        self,
        *,
        user_request: str,
        report_text: str | None = None,
    ) -> dict[str, Any]:
        try:
            langgraph_result = self.langgraph_classifier.classify(
                user_request=user_request,
                report_text=report_text,
            )
            if langgraph_result is not None:
                validated = self._parse_and_validate(
                    langgraph_result,
                    user_request=user_request,
                    source="langgraph",
                )
                self._log_result(validated)
                return validated
            reason = self.langgraph_classifier.last_failure_reason or "no_match"
            request_preview = self._preview_request(user_request)
            print(
                "[CLASSIFICATION] methode=langgraph "
                f"status=no_match reason={reason} request={request_preview}"
            )
        except Exception as exc:
            print(f"[CLASSIFICATION] methode=langgraph status=failed reason={exc}")

        print("[CLASSIFICATION] fallback=gemini status=start")
        gemini_result = self.gemini_fallback_classifier.classify(
            user_request=user_request,
            report_text=report_text,
        )
        validated = self._parse_and_validate(
            gemini_result,
            user_request=user_request,
            source="gemini_fallback",
        )
        self._log_result(validated)
        return validated

    def _parse_and_validate(
        self,
        payload: Any,
        *,
        user_request: str,
        source: str,
    ) -> dict[str, Any]:
        parsed = self.parser.parse(
            payload,
            user_request=user_request,
            source=source,
        )
        return self.validator.validate(parsed, user_request=user_request)

    @staticmethod
    def _log_result(classification_result: dict[str, Any]) -> None:
        source = classification_result.get("classification_source", "unknown")
        intent = classification_result.get("intent", "")
        action = classification_result.get("action", "")
        missing_fields = classification_result.get("missing_fields", [])
        print(f"[CLASSIFICATION] methode={source}")
        print(f"[CLASSIFICATION] intent={intent} action={action}")
        if missing_fields:
            print(f"[CLASSIFICATION] missing_fields={missing_fields}")

    @staticmethod
    def _preview_request(user_request: str) -> str:
        preview = " ".join(str(user_request).strip().split())
        if len(preview) > 120:
            preview = preview[:117] + "..."
        return repr(preview)
