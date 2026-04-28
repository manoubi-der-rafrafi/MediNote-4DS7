from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from . import repository


class ConversationAccessError(RuntimeError):
    pass


@dataclass
class TaskMergeResult:
    task: dict[str, Any]
    classification: dict[str, Any]
    is_complete: bool
    choices: list[str]
    missing_fields: list[str]


class ConversationTaskService:
    MANAGED_ACTIONS = {
        ("rapport", "structure_report"),
        ("rapport", "query_database"),
        ("publication", "generate_publication"),
        ("publication", "query_database"),
    }

    TERMINAL_STATUSES = {"completed", "cancelled"}

    def is_managed(self, classification: dict[str, Any]) -> bool:
        intent = str(classification.get("intent", "")).strip().lower()
        action = self.infer_action(classification)
        return (intent, action) in self.MANAGED_ACTIONS

    def infer_continuation(
        self,
        user_request: str,
        user_id: int,
        conversation_id: int,
    ) -> dict[str, Any] | None:
        self._validate_access(user_id, conversation_id)
        for task in repository.list_open_tasks(conversation_id):
            extracted = self._extract_infos_for_task(user_request, task)
            if not extracted:
                continue

            classification = {
                "intent": task["intent"],
                "action": task["action"],
                **extracted,
            }
            if task["action"] == "query_database":
                classification["user_question"] = user_request.strip()
            return classification

        return None

    def merge_task(
        self,
        user_id: int,
        conversation_id: int,
        classification: dict[str, Any],
    ) -> TaskMergeResult:
        self._validate_access(user_id, conversation_id)

        intent = str(classification.get("intent", "")).strip().lower()
        action = self.infer_action(classification)
        if (intent, action) not in self.MANAGED_ACTIONS:
            raise ValueError("La classification ne correspond pas a une tache geree.")

        new_infos = self.extract_infos(classification)
        existing_task = repository.find_latest_compatible_task(
            conversation_id=conversation_id,
            intent=intent,
            action=action,
        )

        if existing_task is None:
            merged_infos = new_infos
            missing_fields = self.compute_missing_fields(intent, action, merged_infos)
            status = self._status_for_missing_fields(missing_fields)
            task = repository.create_task(
                conversation_id=conversation_id,
                intent=intent,
                action=action,
                status=status,
                infos=merged_infos,
                missing_fields=missing_fields,
            )
        else:
            merged_infos = self._merge_infos(existing_task.get("infos", {}), new_infos)
            missing_fields = self.compute_missing_fields(intent, action, merged_infos)
            status = self._status_for_missing_fields(missing_fields)
            task = repository.update_task(
                task_id=int(existing_task["id"]),
                status=status,
                infos=merged_infos,
                missing_fields=missing_fields,
            )

        merged_classification = self.build_classification_from_task(task)
        choices = self.choices_for_missing_fields(intent, action, missing_fields)
        return TaskMergeResult(
            task=task,
            classification=merged_classification,
            is_complete=not missing_fields,
            choices=choices,
            missing_fields=missing_fields,
        )

    def mark_completed(self, task_id: int) -> dict[str, Any]:
        return repository.set_task_status(task_id, "completed")

    def mark_failed(self, task_id: int) -> dict[str, Any]:
        return repository.set_task_status(task_id, "failed")

    @classmethod
    def infer_action(cls, classification: dict[str, Any]) -> str:
        action = str(classification.get("action", "")).strip().lower()
        if action:
            return action
        if classification.get("db_scope"):
            return "query_database"
        if "media_scope" in classification and "generation_mode" not in classification:
            return "query_database"
        intent = str(classification.get("intent", "")).strip().lower()
        if intent == "rapport":
            return "structure_report"
        if intent == "publication":
            return "generate_publication"
        return ""

    @classmethod
    def extract_infos(cls, classification: dict[str, Any]) -> dict[str, Any]:
        intent = str(classification.get("intent", "")).strip().lower()
        action = cls.infer_action(classification)

        if intent == "rapport" and action == "structure_report":
            return cls._clean_infos({"rapport": classification.get("rapport")})

        if intent == "publication" and action == "generate_publication":
            return cls._clean_infos(
                {
                    "media_type": classification.get("media_type"),
                    "generation_mode": classification.get("generation_mode"),
                    "occasion": classification.get("occasion"),
                    "date": classification.get("date"),
                }
            )

        if action == "query_database":
            db_scope = classification.get("db_scope")
            return cls._clean_infos(
                {
                    "media_scope": classification.get("media_scope"),
                    "db_scope": db_scope if isinstance(db_scope, dict) else None,
                    "user_question": classification.get("user_question"),
                    "query_kind": classification.get("query_kind"),
                }
            )

        return {}

    @classmethod
    def compute_missing_fields(
        cls,
        intent: str,
        action: str,
        infos: dict[str, Any],
    ) -> list[str]:
        missing: list[str] = []

        if intent == "rapport" and action == "structure_report":
            if not cls._has_value(infos.get("rapport")):
                missing.append("rapport")
            return missing

        if intent == "publication" and action == "generate_publication":
            if not cls._has_value(infos.get("media_type")):
                missing.append("media_type")
            if not cls._has_value(infos.get("generation_mode")):
                missing.append("generation_mode")
            if infos.get("generation_mode") == "given_occasion" and not cls._has_value(infos.get("occasion")):
                missing.append("occasion")
            return missing

        if intent == "publication" and action == "query_database":
            if not cls._has_value(infos.get("media_scope")):
                missing.append("media_scope")
            return missing

        return missing

    @classmethod
    def build_classification_from_task(cls, task: dict[str, Any]) -> dict[str, Any]:
        intent = str(task.get("intent", "")).strip().lower()
        action = str(task.get("action", "")).strip().lower()
        infos = dict(task.get("infos") or {})
        classification: dict[str, Any] = {
            "intent": intent,
            "action": action,
        }

        if intent == "rapport" and action == "structure_report":
            classification["rapport"] = infos.get("rapport")
        elif intent == "publication" and action == "generate_publication":
            classification.update(
                {
                    "media_type": infos.get("media_type") or "non_precise",
                    "generation_mode": infos.get("generation_mode") or "missing",
                    "occasion": infos.get("occasion"),
                    "date": infos.get("date"),
                }
            )
        elif action == "query_database":
            classification.update(
                {
                    "media_scope": infos.get("media_scope") or "missing",
                    "db_scope": cls._resolve_db_scope(intent, infos),
                    "user_question": infos.get("user_question"),
                    "query_kind": infos.get("query_kind") or "listing",
                }
            )

        return classification

    @classmethod
    def choices_for_missing_fields(
        cls,
        intent: str,
        action: str,
        missing_fields: list[str],
    ) -> list[str]:
        if intent == "publication" and action == "generate_publication":
            if "media_type" in missing_fields:
                return ["image", "video"]
            if "generation_mode" in missing_fields:
                return ["next_occasion", "exam_period", "given_occasion"]
        if intent == "publication" and action == "query_database" and "media_scope" in missing_fields:
            return ["image", "video", "both"]
        return []

    @classmethod
    def _extract_infos_for_task(
        cls,
        user_request: str,
        task: dict[str, Any],
    ) -> dict[str, Any]:
        intent = str(task.get("intent", "")).strip().lower()
        action = str(task.get("action", "")).strip().lower()
        normalized = cls._normalize_text(user_request)

        if intent == "publication" and action == "generate_publication":
            infos: dict[str, Any] = {}
            media_type = cls._extract_media_type(normalized)
            generation_mode = cls._extract_generation_mode(normalized)
            occasion = cls._extract_occasion(user_request, normalized)
            if media_type:
                infos["media_type"] = media_type
            if generation_mode:
                infos["generation_mode"] = generation_mode
            if occasion:
                infos["occasion"] = occasion
                infos.setdefault("generation_mode", "given_occasion")
            return infos

        if intent == "publication" and action == "query_database":
            media_scope = cls._extract_media_scope(normalized)
            return {"media_scope": media_scope, "user_question": user_request.strip()} if media_scope else {}

        if intent == "rapport" and action == "structure_report":
            candidate = user_request.strip()
            if len(candidate) >= 8 and not cls._looks_like_smalltalk(normalized):
                return {"rapport": candidate}

        return {}

    @classmethod
    def _merge_infos(
        cls,
        existing_infos: dict[str, Any],
        new_infos: dict[str, Any],
    ) -> dict[str, Any]:
        merged = dict(existing_infos or {})
        for key, value in new_infos.items():
            if cls._has_value(value):
                merged[key] = value
        return cls._clean_infos(merged)

    @classmethod
    def _clean_infos(cls, infos: dict[str, Any]) -> dict[str, Any]:
        cleaned: dict[str, Any] = {}
        for key, value in infos.items():
            if isinstance(value, str):
                value = value.strip()
                if value.lower() in {"", "missing", "non_precise", "none", "null"}:
                    value = None
            if key == "media_type" and value == "vdo":
                value = "video"
            if key == "media_scope" and value == "both":
                value = "both"
            cleaned[key] = value
        return cleaned

    @staticmethod
    def _status_for_missing_fields(missing_fields: list[str]) -> str:
        return "waiting_user_input" if missing_fields else "in_progress"

    @classmethod
    def _resolve_db_scope(cls, intent: str, infos: dict[str, Any]) -> dict[str, list[str]]:
        if intent == "rapport":
            return {"tables": ["structured_reports"]}

        media_scope = infos.get("media_scope")
        if media_scope == "image":
            return {"tables": ["generated_images"]}
        if media_scope == "video":
            return {"tables": ["generated_videos"]}
        if media_scope == "both":
            return {"tables": ["generated_images", "generated_videos"]}
        return {"tables": []}

    @classmethod
    def _has_value(cls, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip()) and value.strip().lower() not in {"missing", "non_precise", "none", "null"}
        if isinstance(value, (list, dict)):
            return bool(value)
        return True

    @staticmethod
    def _extract_media_type(normalized: str) -> str | None:
        if any(keyword in normalized for keyword in ("video", "videos", "vdo", "reel")):
            return "video"
        if any(keyword in normalized for keyword in ("image", "images", "photo", "photos", "visuel", "affiche")):
            return "image"
        return None

    @classmethod
    def _extract_media_scope(cls, normalized: str) -> str | None:
        has_image = any(keyword in normalized for keyword in ("image", "images", "photo", "photos", "visuel", "affiche"))
        has_video = any(keyword in normalized for keyword in ("video", "videos", "vdo", "reel"))
        if has_image and has_video:
            return "both"
        if has_image:
            return "image"
        if has_video:
            return "video"
        if "deux" in normalized or "both" in normalized or "tous" in normalized:
            return "both"
        return None

    @staticmethod
    def _extract_generation_mode(normalized: str) -> str | None:
        if any(
            keyword in normalized
            for keyword in (
                "prochaine occasion",
                "occasion la plus proche",
                "prochaine fete",
                "fete la plus proche",
                "prochain evenement",
                "next occasion",
                "next event",
            )
        ):
            return "next_occasion"
        if any(keyword in normalized for keyword in ("examen", "examens", "exam", "bac", "revision", "revision")):
            return "exam_period"
        return None

    @staticmethod
    def _extract_occasion(user_request: str, normalized: str) -> str | None:
        if any(keyword in normalized for keyword in ("prochaine occasion", "next occasion", "examen", "examens", "exam")):
            return None

        match = re.search(r"\bpour\s+(.+)$", user_request.strip(), flags=re.IGNORECASE)
        if not match:
            match = re.search(r"\boccasion\s+(.+)$", user_request.strip(), flags=re.IGNORECASE)
        if not match:
            return None

        fragment = match.group(1).strip()
        fragment = re.sub(r"[?.!,;:]+$", "", fragment).strip()
        return fragment or None

    @staticmethod
    def _looks_like_smalltalk(normalized: str) -> bool:
        return normalized in {"bonjour", "salut", "merci", "ok", "d'accord", "hello", "hi", "thanks"}

    @staticmethod
    def _normalize_text(value: str) -> str:
        return (
            str(value)
            .strip()
            .lower()
            .replace("Ã©", "e")
            .replace("é", "e")
            .replace("è", "e")
            .replace("ê", "e")
            .replace("à", "a")
            .replace("ù", "u")
            .replace("û", "u")
            .replace("î", "i")
            .replace("ï", "i")
            .replace("ô", "o")
        )

    @staticmethod
    def _validate_access(user_id: int, conversation_id: int) -> None:
        if not repository.conversation_belongs_to_user(user_id, conversation_id):
            raise ConversationAccessError(
                "Conversation introuvable ou non autorisee pour cet utilisateur."
            )
