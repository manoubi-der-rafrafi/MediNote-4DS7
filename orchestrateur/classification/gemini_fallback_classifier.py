from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from ..errors import (
    OrchestratorConfigError,
    OrchestratorRequestError,
    OrchestratorResponseError,
)
from ..gemini_client import (
    GeminiClientConfigError,
    generate_content_with_key_rotation,
)
from .prompts import ORCHESTRATOR_SYSTEM_PROMPT, build_orchestrator_user_prompt


class GeminiFallbackClassifier:
    def __init__(self, legacy_service: Any) -> None:
        self.legacy_service = legacy_service

    def classify(
        self,
        *,
        user_request: str,
        report_text: str | None = None,
    ) -> dict[str, Any] | list[Any]:
        del report_text

        try:
            response = generate_content_with_key_rotation(
                model=self.legacy_service.model_name,
                contents=[
                    {"role": "user", "parts": [{"text": ORCHESTRATOR_SYSTEM_PROMPT}]},
                    {
                        "role": "user",
                        "parts": [{"text": build_orchestrator_user_prompt(user_request)}],
                    },
                ],
                config={
                    "response_mime_type": "application/json",
                    "temperature": 0,
                },
            )
        except GeminiClientConfigError as exc:
            raise OrchestratorConfigError(str(exc)) from exc
        except Exception as exc:
            raise OrchestratorRequestError(str(exc)) from exc

        try:
            parsed = getattr(response, "parsed", None)
            if parsed is not None:
                if isinstance(parsed, (dict, list)):
                    return parsed
                if isinstance(parsed, str):
                    return self.legacy_service._parse_json(parsed)
                return self.legacy_service._parse_json(json.dumps(parsed))

            response_text = getattr(response, "text", "")
            return self.legacy_service._parse_json(response_text)
        except (json.JSONDecodeError, TypeError, ValidationError) as exc:
            raise OrchestratorResponseError(
                "La reponse Gemini de classification n'est pas un JSON valide."
            ) from exc
        except Exception as exc:
            raise OrchestratorResponseError(str(exc)) from exc
