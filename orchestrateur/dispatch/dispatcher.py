from __future__ import annotations

from typing import Any

from ..schemas import DispatchResult


class OrchestratorDispatcher:
    def __init__(self, legacy_service: Any) -> None:
        self.legacy_service = legacy_service

    def dispatch(
        self,
        *,
        classification_result: dict[str, Any],
        user_request: str,
        report_text: str | None = None,
        user_id: int | None = None,
        conversation_id: int | None = None,
    ) -> DispatchResult:
        raw_result = self.legacy_service._dispatch(
            classification_result,
            user_request=user_request,
            explicit_report_text=report_text,
            user_id=user_id,
            conversation_id=conversation_id,
        )
        service = self._resolve_service_name(classification_result)
        status = self._resolve_status(classification_result, raw_result)
        choices = list(raw_result.get("choices", [])) if isinstance(raw_result, dict) else []
        missing_fields = (
            list(raw_result.get("missing_fields", []))
            if isinstance(raw_result, dict)
            else []
        )
        error = str(raw_result.get("reason", "")).strip() if isinstance(raw_result, dict) else None
        if not error:
            error = None

        return DispatchResult(
            status=status,
            service=service,
            raw_result=raw_result,
            normalized_data=raw_result,
            choices=choices,
            missing_fields=missing_fields,
            error=error,
        )

    def _resolve_service_name(self, classification_result: dict[str, Any]) -> str:
        intent = str(classification_result.get("intent", "")).strip().lower()
        action = self.legacy_service._infer_action(classification_result)
        if intent == "rapport":
            return "report_structuring" if action != "delete_report" else "report_delete"
        if intent == "publication":
            media_type = str(classification_result.get("media_type", "")).strip().lower()
            if action == "query_database":
                return "database_query"
            if media_type == "video":
                return "publication_video"
            return "publication_image"
        if intent == "produit":
            return "product"
        if action == "query_database":
            return "database_query"
        return "classification_only"

    @staticmethod
    def _resolve_status(
        classification_result: dict[str, Any],
        raw_result: dict[str, Any] | list[Any],
    ) -> str:
        if isinstance(raw_result, dict):
            status = str(raw_result.get("status", "")).strip()
            if status:
                return status

        intent = str(classification_result.get("intent", "")).strip().lower()
        if intent in {"rapport", "publication", "produit"}:
            return "success"
        return "classified_only"
