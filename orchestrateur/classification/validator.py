from __future__ import annotations

from typing import Any

from ..errors import OrchestratorResponseError
from ..schemas import ClassificationResult


class ClassificationValidator:
    def __init__(self, legacy_service: Any) -> None:
        self.legacy_service = legacy_service

    def validate(self, payload: dict[str, Any], *, user_request: str) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise OrchestratorResponseError(
                "La classification doit etre un objet JSON."
            )

        normalized = dict(payload)
        intent = str(normalized.get("intent", "")).strip()
        if not intent:
            raise OrchestratorResponseError(
                "La classification ne contient pas d'intent."
            )

        normalized["action"] = self.legacy_service._infer_action(normalized)
        normalized["response_language"] = (
            self.legacy_service._normalize_response_language(
                normalized.get("response_language")
            )
            or self.legacy_service._detect_response_language(user_request)
        )
        normalized["missing_fields"] = list(normalized.get("missing_fields", []))

        validated = ClassificationResult.model_validate(normalized)
        return validated.model_dump()
