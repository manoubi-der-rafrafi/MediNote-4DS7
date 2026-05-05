from pydantic import BaseModel
from typing import Optional


class PdfExportRequest(BaseModel):
    """Request model for PDF export."""
    content: str
    title: str = "report"
    author: str = "Vital Agent"
    format: str = "A4"


class PdfExportResponse(BaseModel):
    """Response model for PDF export."""
    status: str
    message: str
    pdf_base64: Optional[str] = None
    pdf_url: Optional[str] = None
    error: Optional[str] = None