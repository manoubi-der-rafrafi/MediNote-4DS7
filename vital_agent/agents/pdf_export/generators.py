import io
from datetime import datetime
from typing import List, Dict, Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Image as RLImage
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from .schemas import PdfGenerationResult


class PdfGenerator:
    """PDF generation service using reportlab."""

    def __init__(self):
        self._register_fonts()

    def _register_fonts(self):
        """Register fonts for Unicode support."""
        try:
            # Try to register DejaVu fonts for better Unicode support
            import os
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
            ]
            for path in font_paths:
                if os.path.exists(path):
                    pdfmetrics.registerFont(TTFont('CustomFont', path))
                    pdfmetrics.registerFont(TTFont('CustomFontBold', path))
                    return
        except Exception:
            pass
        # Fallback to default fonts (may not support all Unicode)
        pdfmetrics.registerFont(TTFont('Helvetica', 'Helvetica'))

    def generate_report(
        self,
        title: str,
        content: str,
        format: str = "A4",
        include_toc: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PdfGenerationResult:
        """Generate a PDF report from markdown content."""
        try:
            pagesize = A4 if format.upper() == "A4" else letter
            buffer = io.BytesIO()

            doc = SimpleDocTemplate(
                buffer,
                pagesize=pagesize,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72,
            )

            styles = self._get_styles()
            story = []

            # Add title
            title_style = styles['Title']
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 0.25 * inch))

            # Add metadata / header
            if metadata:
                meta_style = ParagraphStyle(
                    'Metadata',
                    parent=styles['Normal'],
                    fontSize=9,
                    textColor=colors.grey,
                )
                for key, value in metadata.items():
                    if value:
                        story.append(Paragraph(f"<b>{key}:</b> {value}", meta_style))
                story.append(Spacer(1, 0.2 * inch))

            # Add date
            date_style = ParagraphStyle(
                'Date',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.grey,
                alignment=TA_RIGHT,
            )
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", date_style))
            story.append(Spacer(1, 0.3 * inch))

            # Parse and add content
            self._add_markdown_content(story, content, styles)

            # Build PDF
            doc.build(story)

            pdf_bytes = buffer.getvalue()
            buffer.close()

            return PdfGenerationResult(success=True, pdf_bytes=pdf_bytes)

        except Exception as e:
            return PdfGenerationResult(success=False, error=str(e))

    def _get_styles(self):
        """Get paragraph styles."""
        styles = getSampleStyleSheet()

        # Custom styles
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            alignment=TA_CENTER,
            spaceAfter=30,
        ))

        styles.add(ParagraphStyle(
            name='Heading1',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=12,
            spaceBefore=18,
        ))

        styles.add(ParagraphStyle(
            name='Heading2',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=10,
            spaceBefore=12,
        ))

        styles.add(ParagraphStyle(
            name='Code',
            parent=styles['Code'],
            fontSize=9,
            backColor=colors.HexColor('#F8F9FA'),
            textColor=colors.HexColor('#E74C3C'),
        ))

        return styles

    def _add_markdown_content(self, story: List, content: str, styles):
        """Parse simple markdown and add to story."""
        lines = content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Headers
            if line.startswith('# '):
                story.append(Paragraph(line[2:], styles['CustomTitle']))
                story.append(Spacer(1, 0.1 * inch))
            elif line.startswith('## '):
                story.append(Paragraph(line[3:], styles['Heading1']))
                story.append(Spacer(1, 0.05 * inch))
            elif line.startswith('### '):
                story.append(Paragraph(line[4:], styles['Heading2']))
                story.append(Spacer(1, 0.05 * inch))
            # List items (unordered)
            elif line.startswith('- ') or line.startswith('* '):
                bullet_text = line[2:]
                story.append(Paragraph(f"• {bullet_text}", styles['Normal']))
            # Numbered lists
            elif line and line[0].isdigit() and '. ' in line[:4]:
                story.append(Paragraph(line, styles['Normal']))
            # Empty line
            elif not line:
                story.append(Spacer(1, 0.05 * inch))
            # Regular paragraph
            else:
                # Check for table (simplified)
                if line.startswith('|') and '|' in line[1:]:
                    story.extend(self._parse_table(lines, i, styles))
                    # Skip table lines
                    while i < len(lines) and (lines[i].strip().startswith('|') or '---' in lines[i]):
                        i += 1
                    continue
                else:
                    story.append(Paragraph(line, styles['Normal']))
            
            i += 1

    def _parse_table(self, lines: List[str], start_idx: int, styles) -> List:
        """Parse a simple markdown table."""
        from reportlab.platypus import Table, TableStyle
        
        table_data = []
        i = start_idx
        
        while i < len(lines) and lines[i].strip().startswith('|'):
            row = [cell.strip() for cell in lines[i].strip().split('|')[1:-1]]
            if not table_data and all('---' in cell for cell in row):
                # This is a separator row, skip it
                i += 1
                continue
            table_data.append(row)
            i += 1
        
        if not table_data:
            return []
        
        # Create table
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        return [Spacer(1, 0.1 * inch), table, Spacer(1, 0.1 * inch)]


# Create singleton instance
pdf_generator = PdfGenerator()