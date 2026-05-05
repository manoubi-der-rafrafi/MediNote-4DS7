from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from enum import Enum


class ReportType(str, Enum):
    TASKS = "tasks"
    CONVERSATIONS = "conversations"
    PUBLICATIONS = "publications"
    MESSAGES = "messages"
    FULL = "full"
    RAPPORTS = "rapports"


class TaskReportRequest(BaseModel):
    """Request model for task report generation."""
    report_type: ReportType
    user_id: Optional[int] = None
    conversation_id: Optional[int] = None
    limit: int = 100
    format: str = "markdown"  # markdown, json


class TaskReportResponse(BaseModel):
    """Response model for task report."""
    status: str  # success, error, needs_choice, missing_information
    report_type: str
    content: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    message: str = ""
    missing_fields: List[str] = []
    choices: List[str] = []