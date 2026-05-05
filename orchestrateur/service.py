from __future__ import annotations

from typing import Any

from .classification import ClassificationPipeline
from .dispatch import OrchestratorDispatcher
from .orchestrator_service import (
    OrchestratorConfigError,
    OrchestratorMissingDataError,
    OrchestratorProcessingError,
    OrchestratorRequestError,
    OrchestratorResponseError,
    OrchestratorService as LegacyOrchestratorService,
)
from .response import ResponseMessageBuilder, ResponsePayloadBuilder


class OrchestratorService:
    def __init__(
        self,
        model_name: str = "gemini-2.5-flash-lite",
        hashem_router: Any | None = None,
        hashem_chat_service: Any | None = None,
    ) -> None:
        self.legacy_service = LegacyOrchestratorService(
            model_name=model_name,
            hashem_router=hashem_router,
            hashem_chat_service=hashem_chat_service,
        )
        self.classification_pipeline = ClassificationPipeline(self.legacy_service)
        self.dispatcher = OrchestratorDispatcher(self.legacy_service)
        self.payload_builder = ResponsePayloadBuilder(self.legacy_service)
        self.message_builder = ResponseMessageBuilder(self.legacy_service)

    def handle(
        self,
        user_request: str,
        report_text: str | None = None,
        user_id: int | None = None,
        conversation_id: int | None = None,
    ) -> dict[str, Any]:
        try:
            classification_result = self.classification_pipeline.classify(
                user_request=user_request,
                report_text=report_text,
            )
            delegated_response = self.legacy_service._try_hashem_fallback(
                user_request=user_request,
                classification_result=classification_result,
                user_id=user_id,
                conversation_id=conversation_id,
            )
            if delegated_response is not None:
                return delegated_response

            if (
                user_id is not None
                and conversation_id is not None
                and self.legacy_service.conversation_task_service.is_managed(
                    classification_result
                )
            ):
                return self.legacy_service._finalize_conversation_task_response(
                    client=None,
                    user_request=user_request,
                    classification_result=classification_result,
                    report_text=report_text,
                    user_id=user_id,
                    conversation_id=conversation_id,
                )

            dispatch_result = self.dispatcher.dispatch(
                classification_result=classification_result,
                user_request=user_request,
                report_text=report_text,
                user_id=user_id,
                conversation_id=conversation_id,
            )
            response_payload = self.payload_builder.build(
                user_request=user_request,
                classification_result=classification_result,
                dispatch_result=dispatch_result,
            ).model_dump()
            response_payload["message"] = self.message_builder.build(
                user_request=user_request,
                response_payload=response_payload,
            )
            return response_payload
        except (
            OrchestratorConfigError,
            OrchestratorMissingDataError,
            OrchestratorProcessingError,
            OrchestratorRequestError,
            OrchestratorResponseError,
        ):
            raise
