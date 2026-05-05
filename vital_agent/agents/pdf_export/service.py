import base64
import os
from datetime import datetime
from typing import Optional
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO

from .schemas import PdfExportRequest, PdfExportResponse


class PdfExportService:
    """PDF export service using reportlab."""

    def export_report(
        self,
        request: PdfExportRequest,
        save_to_disk: bool = False,
        base_url: Optional[str] = None
    ) -> PdfExportResponse:
        """Export content as PDF."""
        try:
            # Create PDF in memory
            buffer = BytesIO()
            pagesize = A4 if request.format.upper() == "A4" else letter
            
            doc = SimpleDocTemplate(
                buffer,
                pagesize=pagesize,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72,
            )
            
            styles = getSampleStyleSheet()
            
            # Add custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=20,
                alignment=TA_CENTER,
                spaceAfter=30,
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading1'],
                fontSize=14,
                spaceAfter=12,
                spaceBefore=18,
            )
            
            # Date style with TA_RIGHT properly imported
            date_style = ParagraphStyle(
                'Date',
                parent=styles['Normal'],
                fontSize=9,
                alignment=TA_RIGHT,
            )
            
            story = []
            
            # Add title
            story.append(Paragraph(request.title.replace('_', ' ').title(), title_style))
            story.append(Spacer(1, 0.2 * inch))
            
            # Add date
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", date_style))
            story.append(Spacer(1, 0.3 * inch))
            
            # Add content (simple markdown to PDF conversion)
            lines = request.content.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    story.append(Spacer(1, 0.1 * inch))
                elif line.startswith('# '):
                    story.append(Paragraph(line[2:], title_style))
                elif line.startswith('## '):
                    story.append(Paragraph(line[3:], heading_style))
                elif line.startswith('### '):
                    story.append(Paragraph(line[4:], styles['Heading2']))
                elif line.startswith('- ') or line.startswith('* '):
                    story.append(Paragraph(f"• {line[2:]}", styles['Normal']))
                elif line.startswith('|') and '|' in line:
                    # Skip tables for now (complex)
                    continue
                else:
                    # Clean up markdown bold/italic
                    cleaned = line.replace('**', '').replace('*', '')
                    story.append(Paragraph(cleaned, styles['Normal']))
            
            # Build PDF
            doc.build(story)
            
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            # Convert to base64
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            
            # Save to disk if requested
            pdf_url = None
            if save_to_disk:
                export_dir = os.path.join(os.getcwd(), "exports", "pdf")
                os.makedirs(export_dir, exist_ok=True)
                
                safe_title = "".join(c for c in request.title if c.isalnum() or c in " _-")[:50]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{safe_title}_{timestamp}.pdf"
                filepath = os.path.join(export_dir, filename)
                
                with open(filepath, "wb") as f:
                    f.write(pdf_bytes)
                
                pdf_url = f"/exports/pdf/{filename}"
            
            return PdfExportResponse(
                status="success",
                message="PDF generated successfully",
                pdf_base64=pdf_base64,
                pdf_url=pdf_url,
            )
            
        except Exception as e:
            return PdfExportResponse(
                status="error",
                message="PDF generation failed",
                error=str(e),
            )