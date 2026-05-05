from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


ResponseStatus = Literal[
    "success",
    "needs_choice",
    "missing_information",
    "query_rejected",
    "database_unavailable",
    "classified_only",
    "unsupported_request",
    "not_found",
    "error",
]

ClassificationSource = Literal["langgraph", "gemini_fallback"]


class ClassificationResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    intent: str
    action: str = ""
    response_language: str = "French"
    missing_fields: list[str] = Field(default_factory=list)
    classification_source: ClassificationSource


class DispatchResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: str
    service: str
    raw_result: dict[str, Any] | list[Any] | None = None
    normalized_data: dict[str, Any] | list[Any] | None = None
    choices: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    error: str | None = None


class FinalResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: str
    intent: str
    action: str
    response_language: str | None = None
    classification_source: ClassificationSource | None = None
    message: str = ""
    data: dict[str, Any] | list[Any] | None = None
    display: dict[str, Any] | None = None
    task: dict[str, Any] | None = None
    choices: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    error: str | None = None
