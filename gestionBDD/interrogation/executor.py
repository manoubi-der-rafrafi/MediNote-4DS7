from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import text

from db.session import session_scope


def execute_read_only_query(
    sql: str,
    max_rows: int = 200,
) -> dict[str, Any]:
    with session_scope() as session:
        result = session.execute(text(sql))
        columns = list(result.keys())
        fetched_rows = result.mappings().fetchmany(max_rows + 1)

    truncated = len(fetched_rows) > max_rows
    rows = fetched_rows[:max_rows]

    return {
        "columns": columns,
        "rows": [_serialize_row(row) for row in rows],
        "row_count": len(rows),
        "truncated": truncated,
    }


def _serialize_row(row: Any) -> dict[str, Any]:
    return {
        str(key): _serialize_value(value)
        for key, value in dict(row).items()
    }


def _serialize_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value
