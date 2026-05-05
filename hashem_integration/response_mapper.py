from __future__ import annotations

from typing import Any


def build_hashem_display_payload(raw_response: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "hashem_analysis",
        "task_id": raw_response.get("task_id"),
        "mode": raw_response.get("mode"),
        "top_results": raw_response.get("top_results", []),
        "confidence_note": raw_response.get("confidence_note"),
    }


def map_hashem_response(
    raw_response: dict[str, Any],
    response_language: str,
    role: str,
) -> dict[str, Any]:
    message = str(
        raw_response.get("explanation")
        or raw_response.get("message")
        or "Le traitement Hashem a ete execute."
    ).strip()

    status = str(raw_response.get("status", "")).strip().lower()
    normalized_status = "success" if status == "success" else "unsupported_request"

    return {
        "status": normalized_status,
        "intent": "hashem_chat",
        "action": "delegate_to_hashem",
        "response_language": response_language,
        "message": message,
        "data": {
            "role": role,
            "source": "hashem_orchestrator",
            "hashem_response": raw_response,
        },
        "display": build_hashem_display_payload(raw_response),
        "choices": [],
        "missing_fields": [],
        "source": "hashem_orchestrator",
    }
