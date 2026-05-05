from __future__ import annotations

import json
from typing import Any

from ..errors import OrchestratorResponseError


class ClassificationParser:
    def __init__(self, legacy_service: Any) -> None:
        self.legacy_service = legacy_service

    def parse(
        self,
        payload: Any,
        *,
        user_request: str,
        source: str,
    ) -> dict[str, Any]:
        parsed = payload
        if isinstance(parsed, str):
            parsed = self.legacy_service._parse_json(parsed)
        elif not isinstance(parsed, dict):
            parsed = self.legacy_service._parse_json(json.dumps(parsed))

        if not isinstance(parsed, dict):
            raise OrchestratorResponseError(
                "La classification retournee n'est pas un objet JSON exploitable."
            )

        normalized = self.legacy_service._with_response_language(parsed, user_request)
        normalized = self.legacy_service._normalize_classification_result(
            normalized,
            user_request,
        )
        normalized["classification_source"] = source
        return normalized
