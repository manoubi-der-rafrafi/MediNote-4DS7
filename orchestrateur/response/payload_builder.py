from __future__ import annotations

from typing import Any

from ..schemas import DispatchResult, FinalResponse


class ResponsePayloadBuilder:
    def __init__(self, legacy_service: Any) -> None:
        self.legacy_service = legacy_service

    def build(
        self,
        *,
        user_request: str,
        classification_result: dict[str, Any],
        dispatch_result: DispatchResult,
    ) -> FinalResponse:
        payload = self.legacy_service._build_response_payload(
            user_request=user_request,
            classification_result=classification_result,
            dispatched_result=dispatch_result.raw_result,
        )
        payload["classification_source"] = classification_result.get(
            "classification_source"
        )
        return FinalResponse.model_validate(payload)
