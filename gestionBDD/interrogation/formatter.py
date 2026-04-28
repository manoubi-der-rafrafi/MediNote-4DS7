from __future__ import annotations

from typing import Any


def format_query_result(
    query_plan: dict[str, Any],
    execution_result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "tables_used": query_plan.get("tables", []),
        "query_summary": query_plan.get("summary", ""),
        "sql": query_plan.get("sql", ""),
        "columns": execution_result.get("columns", []),
        "rows": execution_result.get("rows", []),
        "row_count": execution_result.get("row_count", 0),
        "truncated": bool(execution_result.get("truncated", False)),
    }
