from datetime import datetime
from typing import Any, Dict, List, Optional


class MarkdownFormatter:
    @staticmethod
    def format_tasks(tasks: List[Dict[str, Any]]) -> str:
        """Format tasks as markdown table."""
        if not tasks:
            return "No tasks found."

        lines = ["## Tasks\n"]
        lines.append("| ID | Status | Intent | Action | Created |")
        lines.append("|----|--------|--------|--------|---------|")

        for task in tasks:
            task_id = task.get('id', 'N/A')
            status = task.get('status', 'N/A')
            intent = task.get('intent', '')[:20] if task.get('intent') else 'N/A'
            action = task.get('action', '')[:15] if task.get('action') else 'N/A'
            created = str(task.get('created_at', ''))[:16] if task.get('created_at') else 'N/A'

            lines.append(f"| {task_id} | {status} | {intent} | {action} | {created} |")

        return "\n".join(lines)

    @staticmethod
    def format_conversations(conversations: List[Dict[str, Any]]) -> str:
        """Format conversations as markdown table."""
        if not conversations:
            return "No conversations found."

        lines = ["## Conversations\n"]
        lines.append("| ID | Title | Created | Updated |")
        lines.append("|----|-------|---------|---------|")

        for conv in conversations:
            conv_id = conv.get('id', 'N/A')
            title = conv.get('title', 'Untitled')[:30] if conv.get('title') else 'Untitled'
            created = str(conv.get('created_at', ''))[:16] if conv.get('created_at') else 'N/A'
            updated = str(conv.get('updated_at', ''))[:16] if conv.get('updated_at') else 'N/A'

            lines.append(f"| {conv_id} | {title} | {created} | {updated} |")

        return "\n".join(lines)

    @staticmethod
    def format_messages(messages: List[Dict[str, Any]]) -> str:
        """Format messages as markdown with timestamps."""
        if not messages:
            return "No messages found."

        lines = ["## Messages\n"]

        for msg in messages:
            role = msg.get('role', 'unknown').upper()
            text = msg.get('text', '')
            time = str(msg.get('created_at', ''))[:19] if msg.get('created_at') else 'Unknown'

            lines.append(f"### [{time}] {role}")
            lines.append(f"{text}\n")

        return "\n".join(lines)

    @staticmethod
    def format_publications(publications: List[Dict[str, Any]]) -> str:
        """Format publications as markdown table."""
        if not publications:
            return "No publications found."

        lines = ["## Publications\n"]
        lines.append("| ID | Type | Produit | Occasion | Mode | Created |")
        lines.append("|----|------|---------|----------|------|---------|")

        for pub in publications:
            pub_id = pub.get('id', 'N/A')
            pub_type = pub.get('type', 'N/A')
            produit = pub.get('produit', 'N/A')[:20] if pub.get('produit') else 'N/A'
            occasion = pub.get('occasion', 'N/A')[:15] if pub.get('occasion') else 'N/A'
            mode = pub.get('generation_mode', 'N/A')[:10] if pub.get('generation_mode') else 'N/A'
            created = str(pub.get('created_at', ''))[:16] if pub.get('created_at') else 'N/A'

            lines.append(f"| {pub_id} | {pub_type} | {produit} | {occasion} | {mode} | {created} |")

        return "\n".join(lines)

    @staticmethod
    def format_reports(reports: List[Dict[str, Any]]) -> str:
        """Format structured reports as markdown."""
        if not reports:
            return "No structured reports found."

        lines = ["## Structured Reports\n"]

        for i, report in enumerate(reports, 1):
            lines.append(f"### Report #{i} (ID: {report.get('id')})")
            
            # Get the main content
            content = report.get('text_corrige') or report.get('raw_text', '')
            if content and len(content) > 300:
                content = content[:300] + "..."
            lines.append(f"{content}\n")

            # Add structured fields if they exist
            structured_fields = []
            field_mappings = {
                'mouvement': 'Movement',
                'potentiel': 'Potential',
                'conseil': 'Advice',
                'emplacement_proximite': 'Location Proximity',
                'emplacement_qualite': 'Location Quality',
                'personnel_attitude': 'Staff Attitude',
                'mise_en_place': 'Setup',
                'invitations': 'Invitations',
                'stock_disponibilite': 'Stock Availability',
                'type_pharmacie': 'Pharmacy Type',
                'eligibilite_animation': 'Animation Eligibility',
                'aucun_point_fort': 'No Strong Points'
            }
            
            for field, label in field_mappings.items():
                value = report.get(field)
                if value and value not in (None, "", "null", "non", "no"):
                    structured_fields.append(f"- **{label}:** {value}")

            if structured_fields:
                lines.append("\n".join(structured_fields))
                lines.append("")

            lines.append("---\n")

        return "\n".join(lines)

    @staticmethod
    def format_full_report(
        tasks: List[Dict[str, Any]],
        conversations: List[Dict[str, Any]],
        reports: List[Dict[str, Any]],
        publications: List[Dict[str, Any]],
        user_id: Optional[int] = None
    ) -> str:
        """Format complete dashboard report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines = [
            "# Complete Dashboard Report",
            "",
            f"**Generated:** {timestamp}",
            f"**User ID:** {user_id if user_id else 'All users'}",
            "",
            "---",
            ""
        ]

        # Tasks section
        lines.append("## Tasks Summary")
        lines.append(f"**Total Tasks:** {len(tasks)}")
        lines.append("")
        if tasks:
            lines.append(MarkdownFormatter.format_tasks(tasks))
        else:
            lines.append("No tasks found.")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Conversations section
        lines.append("## Conversations Summary")
        lines.append(f"**Total Conversations:** {len(conversations)}")
        lines.append("")
        if conversations:
            lines.append(MarkdownFormatter.format_conversations(conversations))
        else:
            lines.append("No conversations found.")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Publications section
        lines.append("## Publications Summary")
        lines.append(f"**Total Publications:** {len(publications)}")
        lines.append("")
        if publications:
            lines.append(MarkdownFormatter.format_publications(publications))
        else:
            lines.append("No publications found.")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Reports section
        lines.append("## Structured Reports Summary")
        lines.append(f"**Total Reports:** {len(reports)}")
        lines.append("")
        if reports:
            lines.append(MarkdownFormatter.format_reports(reports))
        else:
            lines.append("No structured reports found.")

        return "\n".join(lines)

    @staticmethod
    def format_simple_list(items: List[Dict[str, Any]], title: str = "Results") -> str:
        """Format a simple list of items with their key info."""
        if not items:
            return f"No {title.lower()} found."

        lines = [f"## {title}\n"]
        
        for item in items:
            item_id = item.get('id', 'N/A')
            # Try to get a meaningful description
            description = (
                item.get('text_corrige') or 
                item.get('raw_text') or 
                item.get('title') or 
                item.get('produit') or
                item.get('occasion') or
                f"Item {item_id}"
            )
            if len(description) > 100:
                description = description[:100] + "..."
            lines.append(f"- **ID {item_id}:** {description}")
        
        return "\n".join(lines)


# Create singleton instance
markdown_formatter = MarkdownFormatter()