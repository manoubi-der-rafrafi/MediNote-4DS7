from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import text

from db.session import session_scope


_EXCLUDED_EXAMPLE_DATE = date(2026, 5, 5)


@dataclass(frozen=True)
class HistoricalClassificationExample:
    user_text: str
    intent: str
    action: str
    created_at: str | None


def load_recent_examples(limit: int = 250) -> list[HistoricalClassificationExample]:
    sql = text(
        """
        SELECT
            message_text.user_text AS user_text,
            tasks.intent AS intent,
            tasks.action AS action,
            DATE_FORMAT(tasks.created_at, '%Y-%m-%dT%H:%i:%s') AS created_at
        FROM tasks
        JOIN (
            SELECT
                t.id AS task_id,
                (
                    SELECT m.text
                    FROM messages AS m
                    WHERE m.conversation_id = t.conversation_id
                      AND m.role = 'user'
                      AND m.created_at <= t.created_at
                    ORDER BY m.created_at DESC, m.id DESC
                    LIMIT 1
                ) AS user_text
            FROM tasks AS t
        ) AS message_text ON message_text.task_id = tasks.id
        WHERE message_text.user_text IS NOT NULL
          AND DATE(tasks.created_at) <> :excluded_date
        ORDER BY tasks.created_at DESC, tasks.id DESC
        LIMIT :limit_value
        """
    )

    with session_scope() as session:
        rows = session.execute(
            sql,
            {
                "excluded_date": _EXCLUDED_EXAMPLE_DATE.isoformat(),
                "limit_value": int(limit),
            },
        ).mappings()
        return [
            HistoricalClassificationExample(
                user_text=str(row.get("user_text") or "").strip(),
                intent=str(row.get("intent") or "").strip().lower(),
                action=str(row.get("action") or "").strip().lower(),
                created_at=str(row.get("created_at") or "").strip() or None,
            )
            for row in rows
            if str(row.get("user_text") or "").strip()
            and str(row.get("intent") or "").strip()
            and str(row.get("action") or "").strip()
        ]
