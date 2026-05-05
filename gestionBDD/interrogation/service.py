from __future__ import annotations

import json
import re
import traceback
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
        self._debug(
            "start",
            {
                "user_request": user_request,
                "classification": classification_result,
                "resolved_tables": tables,
            },
        )
        if not tables:
            return self._build_missing_scope_response(classification_result)

        catalog_fragment = build_catalog_prompt_fragment(tables)
        if not catalog_fragment:
            raise DatabaseQueryConfigError(
                "Aucun schema de table n'a ete trouve pour la demande."
            )
        self._debug(
            "catalog_ready",
            {
                "tables": tables,
                "catalog_length": len(catalog_fragment),
            },
        )

        try:
            prompt = build_sql_agent_user_prompt(
                user_request,
                classification_result,
                catalog_fragment,
                user_id=user_id,
            )
            self._debug(
                "llm_request",
                {
                    "model": self.model_name,
                    "prompt_length": len(prompt),
                },
            )
            response = generate_content_with_key_rotation(
                model=self.model_name,
                contents=[
                    {"role": "user", "parts": [{"text": SQL_AGENT_SYSTEM_PROMPT}]},
                    {
                        "role": "user",
                        "parts": [{"text": prompt}],
                    },
                ],
                config={
                    "response_mime_type": "application/json",
                    "temperature": 0,
                },
            )
            self._debug("llm_response_received", {"response_type": type(response).__name__})
        except GeminiKeyConfigError as exc:
            self._debug(
                "llm_config_error",
                {
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                },
            )
            raise DatabaseQueryConfigError(str(exc)) from exc
        except Exception as exc:
            self._debug(
                "llm_request_error",
                {
                    "error": f"{exc.__class__.__name__}: {exc}",
                    "traceback": traceback.format_exc(),
                },
            )
            raise DatabaseQueryRequestError(str(exc)) from exc

        try:
            payload = self._parse_llm_payload(response)
        except Exception as exc:
            self._debug(
                "llm_parse_error",
                {
                    "error": f"{exc.__class__.__name__}: {exc}",
                    "response_type": type(response).__name__,
                    "response_text": str(getattr(response, "text", ""))[:2000],
                    "parsed": str(getattr(response, "parsed", ""))[:2000],
                    "traceback": traceback.format_exc(),
                },
            )
            raise
        self._debug("llm_payload", payload)
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
            self._debug(
                "schema_error",
                {
                    "error": str(exc),
                    "payload": payload,
                    "traceback": traceback.format_exc(),
                },
            )
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
            self._debug(
                "validated_sql",
                {
                    "sql": validated_sql,
                    "used_tables": used_tables,
                },
            )
        except DatabaseQueryValidationError as exc:
            self._debug(
                "validation_error",
                {
                    "error": str(exc),
                    "payload": payload,
                },
            )
            return {
                "status": "query_rejected",
                "reason": str(exc),
                "choices": [],
                "missing_fields": [],
            }

        try:
            execution_result = execute_read_only_query(validated_sql)
        except DatabaseConfigError as exc:
            self._debug("config_error", {"error": str(exc), "sql": validated_sql})
            raise DatabaseQueryConfigError(str(exc)) from exc
        except OperationalError as exc:
            self._debug(
                "operational_error",
                {
                    "error": str(exc),
                    "orig": str(exc.orig) if getattr(exc, "orig", None) else "",
                    "sql": validated_sql,
                },
            )
            return self._build_database_unavailable_response(exc)
        except Exception as exc:
            self._debug(
                "execution_error",
                {
                    "error": str(exc),
                    "sql": validated_sql,
                    "traceback": traceback.format_exc(),
                },
            )
            raise DatabaseQueryExecutionError(
                f"Echec d'execution de la requete SQL: {exc}"
            ) from exc

        try:
            self._debug(
                "execution_success",
                {
                    "columns": execution_result.get("columns"),
                    "row_count": execution_result.get("row_count"),
                    "truncated": execution_result.get("truncated"),
                },
            )
            formatted_result = format_query_result(
                {
                    "tables": used_tables,
                    "summary": query_plan.summary,
                    "sql": validated_sql,
                },
                execution_result,
            )
            self._debug(
                "format_success",
                {
                    "keys": sorted(formatted_result.keys()),
                    "row_count": formatted_result.get("row_count"),
                },
            )
        except Exception as exc:
            self._debug(
                "format_error",
                {
                    "error": f"{exc.__class__.__name__}: {exc}",
                    "execution_result": execution_result,
                    "traceback": traceback.format_exc(),
                },
            )
            raise DatabaseQueryExecutionError(
                f"Echec de formatage du resultat SQL: {exc}"
            ) from exc
        return {
            "status": "success",
            "choices": [],
            "missing_fields": [],
            **formatted_result,
        }

    @staticmethod
    def _debug(event: str, payload: dict[str, Any]) -> None:
        try:
            rendered = json.dumps(payload, ensure_ascii=False, default=str)
        except Exception:
            rendered = str(payload)
        print(f"[DB_QUERY] {event}: {rendered}", flush=True)

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
    normalized_sql = _wrap_union_selects_with_limit(normalized_sql)
    return normalized_sql


def _wrap_union_selects_with_limit(sql: str) -> str:
    if not re.search(r"\bunion\s+all\b", sql, flags=re.IGNORECASE):
        return sql

    parts = re.split(r"(\bUNION\s+ALL\b)", sql, flags=re.IGNORECASE)
    if len(parts) < 3:
        return sql

    normalized_parts: list[str] = []
    for index, part in enumerate(parts):
        if index % 2 == 1:
            normalized_parts.append(part)
            continue

        candidate = part.strip()
        if not candidate:
            normalized_parts.append(part)
            continue
        if not re.match(r"^select\b", candidate, flags=re.IGNORECASE):
            normalized_parts.append(part)
            continue
        if not re.search(r"\blimit\s+\d+\b", candidate, flags=re.IGNORECASE):
            normalized_parts.append(part)
            continue
        if candidate.startswith("(") and candidate.endswith(")"):
            normalized_parts.append(candidate)
            continue
        normalized_parts.append(f"({candidate})")

    return " ".join(segment.strip() for segment in normalized_parts if segment.strip())


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
