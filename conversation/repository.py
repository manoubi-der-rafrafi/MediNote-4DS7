from __future__ import annotations

from typing import Any

from sqlalchemy import desc

from db.models import Conversation, ConversationTask
from db.session import session_scope


OPEN_TASK_STATUSES = ("draft", "waiting_user_input", "in_progress", "failed")


def conversation_belongs_to_user(
    user_id: int,
    conversation_id: int,
) -> bool:
    with session_scope() as session:
        row = (
            session.query(Conversation.id)
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
            .first()
        )
        return row is not None


def find_latest_compatible_task(
    conversation_id: int,
    intent: str,
    action: str,
) -> dict[str, Any] | None:
    with session_scope() as session:
        task = (
            session.query(ConversationTask)
            .filter(
                ConversationTask.conversation_id == conversation_id,
                ConversationTask.intent == intent,
                ConversationTask.action == action,
                ConversationTask.status.in_(OPEN_TASK_STATUSES),
            )
            .order_by(desc(ConversationTask.updated_at), desc(ConversationTask.id))
            .first()
        )
        if task is None:
            return None
        return _task_to_dict(task)


def list_open_tasks(conversation_id: int) -> list[dict[str, Any]]:
    with session_scope() as session:
        tasks = (
            session.query(ConversationTask)
            .filter(
                ConversationTask.conversation_id == conversation_id,
                ConversationTask.status.in_(OPEN_TASK_STATUSES),
            )
            .order_by(desc(ConversationTask.updated_at), desc(ConversationTask.id))
            .all()
        )
        return [_task_to_dict(task) for task in tasks]


def create_task(
    conversation_id: int,
    intent: str,
    action: str,
    status: str,
    infos: dict[str, Any],
    missing_fields: list[str],
) -> dict[str, Any]:
    with session_scope() as session:
        task = ConversationTask(
            conversation_id=conversation_id,
            intent=intent,
            action=action,
            status=status,
            infos_json=infos,
            missing_fields_json=missing_fields,
        )
        session.add(task)
        session.flush()
        session.refresh(task)
        return _task_to_dict(task)


def update_task(
    task_id: int,
    status: str,
    infos: dict[str, Any],
    missing_fields: list[str],
) -> dict[str, Any]:
    with session_scope() as session:
        task = session.get(ConversationTask, task_id)
        if task is None:
            raise ValueError(f"Tache introuvable: {task_id}")

        task.status = status
        task.infos_json = infos
        task.missing_fields_json = missing_fields
        session.flush()
        session.refresh(task)
        return _task_to_dict(task)


def set_task_status(task_id: int, status: str) -> dict[str, Any]:
    with session_scope() as session:
        task = session.get(ConversationTask, task_id)
        if task is None:
            raise ValueError(f"Tache introuvable: {task_id}")

        task.status = status
        session.flush()
        session.refresh(task)
        return _task_to_dict(task)


def _task_to_dict(task: ConversationTask) -> dict[str, Any]:
    return {
        "id": task.id,
        "conversation_id": task.conversation_id,
        "intent": task.intent,
        "action": task.action,
        "status": task.status,
        "infos": dict(task.infos_json or {}),
        "missing_fields": list(task.missing_fields_json or []),
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }
