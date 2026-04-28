from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class SQLQueryPlan(BaseModel):
    mode: Literal["sql_query"]
    tables: list[str] = Field(min_length=1)
    sql: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    confidence: float | None = None

    @field_validator("tables")
    @classmethod
    def validate_tables(cls, value: list[str]) -> list[str]:
        cleaned = [str(table_name).strip() for table_name in value if str(table_name).strip()]
        if not cleaned:
            raise ValueError("La liste des tables ne peut pas etre vide.")
        return cleaned


class SQLQueryRejection(BaseModel):
    mode: Literal["rejected"]
    reason: str = Field(min_length=1)
