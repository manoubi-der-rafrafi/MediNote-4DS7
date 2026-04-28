from __future__ import annotations

import re


class DatabaseQueryValidationError(RuntimeError):
    pass


FORBIDDEN_KEYWORDS = (
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "truncate",
    "create",
    "replace",
    "grant",
    "revoke",
)


def validate_read_only_sql(
    sql: str,
    allowed_tables: set[str],
) -> tuple[str, list[str]]:
    normalized_sql = str(sql).strip()
    if not normalized_sql:
        raise DatabaseQueryValidationError("La requete SQL est vide.")

    if ";" in normalized_sql.rstrip(";"):
        raise DatabaseQueryValidationError(
            "Une seule requete SQL est autorisee par demande."
        )

    normalized_sql = normalized_sql.rstrip(";").strip()
    lowered = normalized_sql.lower()

    if not lowered.startswith("select "):
        raise DatabaseQueryValidationError(
            "Seules les requetes SELECT sont autorisees."
        )

    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", lowered):
            raise DatabaseQueryValidationError(
                f"Le mot-cle SQL '{keyword}' est interdit."
            )

    used_tables = _extract_table_names(lowered)
    if not used_tables:
        raise DatabaseQueryValidationError(
            "Impossible d'identifier les tables utilisees dans la requete."
        )

    disallowed_tables = sorted(table_name for table_name in used_tables if table_name not in allowed_tables)
    if disallowed_tables:
        raise DatabaseQueryValidationError(
            "La requete utilise des tables non autorisees: "
            + ", ".join(disallowed_tables)
            + "."
        )

    if not _is_aggregate_query(lowered) and " limit " not in f" {lowered} ":
        raise DatabaseQueryValidationError(
            "Les requetes de listing doivent contenir un LIMIT explicite."
        )

    return normalized_sql, sorted(used_tables)


def ensure_user_scope_for_conversation_tables(
    sql: str,
    used_tables: list[str],
    user_id: int | None,
) -> str:
    conversation_tables = {"conversations", "messages", "tasks"}
    if not conversation_tables.intersection({table.lower() for table in used_tables}):
        return sql

    if user_id is None:
        raise DatabaseQueryValidationError(
            "Les requetes sur conversations, messages ou tasks exigent un id_user."
        )

    lowered = sql.lower()
    if "conversations" not in {table.lower() for table in used_tables}:
        raise DatabaseQueryValidationError(
            "Les requetes sur messages ou tasks doivent joindre la table conversations."
        )

    conversation_ref = _resolve_conversations_reference(sql)
    user_filter_pattern = rf"\b{re.escape(conversation_ref)}\s*\.\s*user_id\s*=\s*{int(user_id)}\b"
    if re.search(user_filter_pattern, lowered):
        return sql

    return _inject_user_filter(sql, int(user_id), conversation_ref)


def _extract_table_names(lowered_sql: str) -> set[str]:
    matches = re.findall(
        r"\b(?:from|join)\s+`?([a-zA-Z_][a-zA-Z0-9_]*)`?",
        lowered_sql,
        flags=re.IGNORECASE,
    )
    return {match.lower() for match in matches}


def _inject_user_filter(sql: str, user_id: int, conversation_ref: str) -> str:
    order_limit_pattern = re.compile(
        r"\s+(order\s+by|group\s+by|limit)\b",
        flags=re.IGNORECASE,
    )
    match = order_limit_pattern.search(sql)
    if match:
        head = sql[: match.start()].rstrip()
        tail = sql[match.start():]
    else:
        head = sql.rstrip()
        tail = ""

    if re.search(r"\bwhere\b", head, flags=re.IGNORECASE):
        return f"{head} AND {conversation_ref}.user_id = {user_id}{tail}"
    return f"{head} WHERE {conversation_ref}.user_id = {user_id}{tail}"


def _resolve_conversations_reference(sql: str) -> str:
    alias_pattern = re.compile(
        r"\b(?:from|join)\s+`?conversations`?(?:\s+as)?\s+`?([a-zA-Z_][a-zA-Z0-9_]*)`?",
        flags=re.IGNORECASE,
    )
    for match in alias_pattern.finditer(sql):
        alias = str(match.group(1)).strip("`")
        if alias.lower() != "conversations":
            return alias
    return "conversations"


def _is_aggregate_query(lowered_sql: str) -> bool:
    aggregate_patterns = (
        r"\bcount\s*\(",
        r"\bsum\s*\(",
        r"\bavg\s*\(",
        r"\bmin\s*\(",
        r"\bmax\s*\(",
        r"\bgroup\s+by\b",
    )
    return any(re.search(pattern, lowered_sql) for pattern in aggregate_patterns)
