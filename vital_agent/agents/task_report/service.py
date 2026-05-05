from typing import Any, Dict, Optional

from .repository import TaskReportRepository
from .formatters import markdown_formatter


class TaskReportService:
    def __init__(self, repository: Optional[TaskReportRepository] = None):
        self.repository = repository or TaskReportRepository()

    def handle(
        self,
        classification_result: Dict[str, Any],
        user_id: Optional[int] = None,
        conversation_id: Optional[int] = None
    ) -> Dict[str, Any]:
        try:
            report_type = classification_result.get("report_type", "rapports")
            
            # Normalize report type
            if report_type in ("task", "tasks"):
                report_type = "tasks"
            elif report_type in ("conversation", "conversations"):
                report_type = "conversations"
            elif report_type in ("publication", "publications", "post", "posts"):
                report_type = "publications"
            elif report_type in ("message", "messages"):
                report_type = "messages"
            elif report_type in ("rapport", "rapports", "report", "reports"):
                report_type = "rapports"
            elif report_type in ("full", "dashboard", "complete", "complet"):
                report_type = "full"

            # Check for missing information
            missing_fields = []
            if report_type == "messages" and not conversation_id:
                missing_fields.append("conversation_id")
            if report_type in ("tasks", "conversations", "full") and not user_id:
                missing_fields.append("user_id")

            if missing_fields:
                return {
                    "status": "missing_information",
                    "report_type": report_type,
                    "message": f"Missing required fields: {', '.join(missing_fields)}",
                    "missing_fields": missing_fields,
                    "choices": [],
                    "content": None,
                    "data": None,
                }

            # Fetch data based on report type
            if report_type == "tasks":
                tasks = self.repository.fetch_tasks(user_id=user_id)
                if not tasks:
                    return {
                        "status": "success",
                        "report_type": report_type,
                        "content": "No tasks found in the database.",
                        "data": [],
                        "message": "No tasks found",
                        "missing_fields": [],
                        "choices": [],
                    }
                content = markdown_formatter.format_tasks(tasks)
                return {
                    "status": "success",
                    "report_type": report_type,
                    "content": content,
                    "data": tasks,
                    "message": f"Found {len(tasks)} tasks",
                    "missing_fields": [],
                    "choices": [],
                }

            elif report_type == "conversations":
                conversations = self.repository.fetch_conversations(user_id=user_id)
                if not conversations:
                    return {
                        "status": "success",
                        "report_type": report_type,
                        "content": "No conversations found in the database.",
                        "data": [],
                        "message": "No conversations found",
                        "missing_fields": [],
                        "choices": [],
                    }
                content = markdown_formatter.format_conversations(conversations)
                return {
                    "status": "success",
                    "report_type": report_type,
                    "content": content,
                    "data": conversations,
                    "message": f"Found {len(conversations)} conversations",
                    "missing_fields": [],
                    "choices": [],
                }

            elif report_type == "messages":
                if not conversation_id:
                    return {
                        "status": "missing_information",
                        "report_type": report_type,
                        "message": "conversation_id is required for messages report",
                        "missing_fields": ["conversation_id"],
                        "choices": [],
                        "content": None,
                        "data": None,
                    }
                messages = self.repository.fetch_messages(conversation_id=conversation_id)
                if not messages:
                    return {
                        "status": "success",
                        "report_type": report_type,
                        "content": f"No messages found in conversation {conversation_id}.",
                        "data": [],
                        "message": "No messages found",
                        "missing_fields": [],
                        "choices": [],
                    }
                content = markdown_formatter.format_messages(messages)
                return {
                    "status": "success",
                    "report_type": report_type,
                    "content": content,
                    "data": messages,
                    "message": f"Found {len(messages)} messages",
                    "missing_fields": [],
                    "choices": [],
                }

            elif report_type == "publications":
                publications = self.repository.fetch_publications()
                if not publications:
                    return {
                        "status": "success",
                        "report_type": report_type,
                        "content": "No publications found in the database.",
                        "data": [],
                        "message": "No publications found",
                        "missing_fields": [],
                        "choices": [],
                    }
                content = markdown_formatter.format_publications(publications)
                return {
                    "status": "success",
                    "report_type": report_type,
                    "content": content,
                    "data": publications,
                    "message": f"Found {len(publications)} publications",
                    "missing_fields": [],
                    "choices": [],
                }

            elif report_type == "rapports":
                reports = self.repository.fetch_structured_reports()
                if not reports:
                    return {
                        "status": "success",
                        "report_type": report_type,
                        "content": "No structured reports found in the database.",
                        "data": [],
                        "message": "No structured reports found",
                        "missing_fields": [],
                        "choices": [],
                    }
                content = markdown_formatter.format_reports(reports)
                return {
                    "status": "success",
                    "report_type": report_type,
                    "content": content,
                    "data": reports,
                    "message": f"Found {len(reports)} structured reports",
                    "missing_fields": [],
                    "choices": [],
                }

            elif report_type == "full":
                tasks = self.repository.fetch_tasks(user_id=user_id)
                conversations = self.repository.fetch_conversations(user_id=user_id)
                reports = self.repository.fetch_structured_reports()
                publications = self.repository.fetch_publications()

                content = markdown_formatter.format_full_report(
                    tasks=tasks,
                    conversations=conversations,
                    reports=reports,
                    publications=publications,
                    user_id=user_id,
                )
                
                return {
                    "status": "success",
                    "report_type": report_type,
                    "content": content,
                    "data": {
                        "tasks": tasks,
                        "conversations": conversations,
                        "reports": reports,
                        "publications": publications,
                    },
                    "message": f"Generated full report: {len(tasks)} tasks, {len(conversations)} conversations, {len(reports)} reports, {len(publications)} publications",
                    "missing_fields": [],
                    "choices": [],
                }

            else:
                return {
                    "status": "needs_choice",
                    "report_type": report_type,
                    "message": "Please specify what type of report you want: tasks, conversations, messages, publications, rapports, or full",
                    "missing_fields": ["report_type"],
                    "choices": ["tasks", "conversations", "messages", "publications", "rapports", "full"],
                    "content": None,
                    "data": None,
                }

        except Exception as e:
            return {
                "status": "error",
                "report_type": classification_result.get("report_type", "unknown"),
                "message": f"Failed to generate report: {str(e)}",
                "missing_fields": [],
                "choices": [],
                "content": None,
                "data": None,
                "error": str(e),
            }