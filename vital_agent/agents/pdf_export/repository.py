import json
from typing import Any, Dict, List, Optional

from gestionBDD import DatabaseQueryService


class PdfExportRepository:
    """Repository for fetching data from database for PDF export."""

    def __init__(self, db_service: Optional[DatabaseQueryService] = None):
        self.db_service = db_service or DatabaseQueryService()

    def fetch_tasks(self, user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch user tasks from database."""
        query = """
            SELECT id, intent, action, status, created_at, updated_at
            FROM tasks
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """
        result = self.db_service.execute_raw_query(query, [user_id, limit])
        return result.get("rows", []) if isinstance(result, dict) else []

    def fetch_conversations(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch user conversations."""
        query = """
            SELECT id, title, created_at, updated_at
            FROM conversations
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """
        result = self.db_service.execute_raw_query(query, [user_id, limit])
        return result.get("rows", []) if isinstance(result, dict) else []

    def fetch_messages(self, conversation_id: int, limit: int = 200) -> List[Dict[str, Any]]:
        """Fetch messages from a conversation."""
        query = """
            SELECT id, role, text, created_at
            FROM messages
            WHERE conversation_id = %s
            ORDER BY created_at ASC
            LIMIT %s
        """
        result = self.db_service.execute_raw_query(query, [conversation_id, limit])
        return result.get("rows", []) if isinstance(result, dict) else []

    def fetch_structured_reports(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch structured reports."""
        query = """
            SELECT id, raw_text, text_corrige, mouvement, potentiel, conseil, 
                   emplacement_proximite, emplacement_qualite, personnel_attitude,
                   mise_en_place, invitations, stock_disponibilite, type_pharmacie,
                   eligibilite_animation, created_at
            FROM structured_reports
            ORDER BY created_at DESC
            LIMIT %s
        """
        result = self.db_service.execute_raw_query(query, [limit])
        return result.get("rows", []) if isinstance(result, dict) else []

    def fetch_publications(self, media_type: str = "both", limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch generated publications."""
        images = []
        videos = []
        
        if media_type in ("image", "both"):
            img_query = """
                SELECT id, produit, occasion, generation_mode, date_publication, created_at
                FROM generated_images
                ORDER BY created_at DESC
                LIMIT %s
            """
            img_result = self.db_service.execute_raw_query(img_query, [limit])
            images = img_result.get("rows", []) if isinstance(img_result, dict) else []
            for img in images:
                img["type"] = "image"
        
        if media_type in ("video", "both"):
            vid_query = """
                SELECT id, produit, occasion, generation_mode, date_publication, created_at
                FROM generated_videos
                ORDER BY created_at DESC
                LIMIT %s
            """
            vid_result = self.db_service.execute_raw_query(vid_query, [limit])
            videos = vid_result.get("rows", []) if isinstance(vid_result, dict) else []
            for vid in videos:
                vid["type"] = "video"
        
        combined = images + videos
        combined.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return combined[:limit]