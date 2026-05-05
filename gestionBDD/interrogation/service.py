from __future__ import annotations

import json
import re
from typing import Any

from pydantic import ValidationError
from sqlalchemy.exc import OperationalError

from db.config import DatabaseConfigError
from gemini_keyring import (
    GeminiKeyConfigError,
    generate_content_with_key_rotation,
)
from .catalog import build_catalog_prompt_fragment, resolve_tables_for_query
from .executor import execute_read_only_query
from .formatter import format_query_result
from .prompts import SQL_AGENT_SYSTEM_PROMPT, build_sql_agent_user_prompt
from .schemas import SQLQueryPlan, SQLQueryRejection
from .validator import (
    DatabaseQueryValidationError,
    ensure_user_scope_for_conversation_tables,
    validate_read_only_sql,
)

DEFAULT_MODEL_NAME = "gemini-2.5-flash-lite"


class DatabaseQueryConfigError(RuntimeError):
    pass


class DatabaseQueryRequestError(RuntimeError):
    pass


class DatabaseQueryResponseError(RuntimeError):
    pass


class DatabaseQueryExecutionError(RuntimeError):
    pass


class DatabaseQueryService:
    def __init__(self, model_name: str = DEFAULT_MODEL_NAME) -> None:
        self.model_name = model_name

    def handle(
        self,
        user_request: str,
        classification_result: dict[str, Any],
        user_id: int | None = None,
        conversation_id: int | None = None,
    ) -> dict[str, Any]:
        tables = resolve_tables_for_query(classification_result)
        if not tables:
            return self._build_missing_scope_response(classification_result)

        catalog_fragment = build_catalog_prompt_fragment(tables)
        if not catalog_fragment:
            raise DatabaseQueryConfigError(
                "Aucun schema de table n'a ete trouve pour la demande."
            )

        try:
            response = generate_content_with_key_rotation(
                model=self.model_name,
                contents=[
                    {"role": "user", "parts": [{"text": SQL_AGENT_SYSTEM_PROMPT}]},
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": build_sql_agent_user_prompt(
                                    user_request,
                                    classification_result,
                                    catalog_fragment,
                                    user_id=user_id,
                                )
                            }
                        ],
                    },
                ],
                config={
                    "response_mime_type": "application/json",
                    "temperature": 0,
                },
            )
        except GeminiKeyConfigError as exc:
            raise DatabaseQueryConfigError(str(exc)) from exc
        except Exception as exc:
            raise DatabaseQueryRequestError(str(exc)) from exc

        payload = self._parse_llm_payload(response)
        if payload.get("mode") == "rejected":
            rejected = SQLQueryRejection.model_validate(payload)
            return {
                "status": "query_rejected",
                "reason": rejected.reason,
                "choices": [],
                "missing_fields": [],
            }

        try:
            query_plan = SQLQueryPlan.model_validate(payload)
        except ValidationError as exc:
            raise DatabaseQueryResponseError(
                "La reponse de l'agent SQL ne respecte pas le schema attendu."
            ) from exc

        try:
            validated_sql, used_tables = validate_read_only_sql(
                query_plan.sql,
                allowed_tables={table_name.lower() for table_name in tables},
            )
            validated_sql = ensure_user_scope_for_conversation_tables(
                validated_sql,
                used_tables=used_tables,
                user_id=user_id,
            )
            validated_sql = _normalize_sql_filter_values(validated_sql)
            validated_sql, used_tables = validate_read_only_sql(
                validated_sql,
                allowed_tables={table_name.lower() for table_name in tables},
            )
            validated_sql = ensure_user_scope_for_conversation_tables(
                validated_sql,
                used_tables=used_tables,
                user_id=user_id,
            )
        except DatabaseQueryValidationError as exc:
            return {
                "status": "query_rejected",
                "reason": str(exc),
                "choices": [],
                "missing_fields": [],
            }

        try:
            execution_result = execute_read_only_query(validated_sql)
        except DatabaseConfigError as exc:
            raise DatabaseQueryConfigError(str(exc)) from exc
        except OperationalError as exc:
            return self._build_database_unavailable_response(exc)
        except Exception as exc:
            raise DatabaseQueryExecutionError(
                f"Echec d'execution de la requete SQL: {exc}"
            ) from exc

        formatted_result = format_query_result(
            {
                "tables": used_tables,
                "summary": query_plan.summary,
                "sql": validated_sql,
            },
            execution_result,
        )
        return {
            "status": "success",
            "choices": [],
            "missing_fields": [],
            **formatted_result,
        }

    @staticmethod
    def _build_database_unavailable_response(exc: OperationalError) -> dict[str, Any]:
        details = str(exc.orig) if getattr(exc, "orig", None) else str(exc)
        return {
            "status": "database_unavailable",
            "choices": [],
            "missing_fields": [],
            "reason": f"Echec d'execution SQL: {details}",
            "details": details,
        }

    @staticmethod
    def _build_missing_scope_response(classification_result: dict[str, Any]) -> dict[str, Any]:
        intent = str(classification_result.get("intent", "")).strip().lower()
        if intent == "publication":
            return {
                "status": "needs_choice",
                "choices": ["image", "video", "both"],
                "missing_fields": ["media_scope"],
                "reason": "",
            }

        return {
            "status": "query_rejected",
            "choices": [],
            "missing_fields": [],
            "reason": "Le scope de la requete BDD n'est pas exploitable.",
        }

    @staticmethod
    def _parse_llm_payload(response: Any) -> dict[str, Any]:
        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, dict):
            return parsed
        if isinstance(parsed, str):
            return json.loads(parsed)

        response_text = getattr(response, "text", "")
        if not isinstance(response_text, str) or not response_text.strip():
            raise DatabaseQueryResponseError(
                "La reponse de l'agent SQL est vide."
            )

        try:
            payload = json.loads(response_text)
        except json.JSONDecodeError as exc:
            raise DatabaseQueryResponseError(
                "La reponse de l'agent SQL n'est pas un JSON valide."
            ) from exc

        if not isinstance(payload, dict):
            raise DatabaseQueryResponseError(
                "La reponse de l'agent SQL doit etre un objet JSON."
            )
        return payload


def _normalize_sql_filter_values(sql: str) -> str:
    normalizations = (
        ("potentiel", "fort", ("forte", "fort")),
        ("mouvement", "fort", ("forte", "fort")),
        ("conseil", "fort", ("forte", "fort")),
        ("mise_en_place", "moyen", ("moyenne", "moyen")),
    )

    normalized_sql = sql
    for column_name, generated_value, accepted_values in normalizations:
        normalized_sql = _replace_equality_filter_with_in_clause(
            normalized_sql,
            column_name=column_name,
            generated_value=generated_value,
            accepted_values=accepted_values,
        )
    return normalized_sql


def _replace_equality_filter_with_in_clause(
    sql: str,
    column_name: str,
    generated_value: str,
    accepted_values: tuple[str, ...],
) -> str:
    pattern = re.compile(
        rf"(?P<column>(?:`?structured_reports`?\.)?`?{re.escape(column_name)}`?)"
        rf"\s*=\s*(?P<quote>['\"]){re.escape(generated_value)}(?P=quote)",
        flags=re.IGNORECASE,
    )

    def replacement(match: re.Match[str]) -> str:
        values = ", ".join(f"'{value}'" for value in accepted_values)
        return f"{match.group('column')} IN ({values})"

    return pattern.sub(replacement, sql)
