from __future__ import annotations

from typing import Any, TypedDict


class ClassificationState(TypedDict, total=False):
    user_request: str
    report_text: str | None
    classification: dict[str, Any] | None
    failed: bool
    failure_reason: str | None
