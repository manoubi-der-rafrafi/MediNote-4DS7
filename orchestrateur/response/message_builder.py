from __future__ import annotations

from typing import Any


class ResponseMessageBuilder:
    def __init__(self, legacy_service: Any) -> None:
        self.legacy_service = legacy_service

    def build(
        self,
        *,
        user_request: str,
        response_payload: dict[str, Any],
    ) -> str:
        payload = dict(response_payload)
        payload["_user_request"] = user_request
        payload["message"] = self.legacy_service._generate_explanatory_message(
            client=None,
            user_request=user_request,
            response_payload=payload,
        )
        return self.legacy_service._post_process_explanatory_message(
            user_request=user_request,
            response_payload=payload,
        )
