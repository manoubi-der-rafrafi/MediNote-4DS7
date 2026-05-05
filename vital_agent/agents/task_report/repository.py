import json
from typing import Any, Dict, List, Optional
import mysql.connector
from mysql.connector import Error
import os


class TaskReportRepository:
    def __init__(self):
        self._connection = None

    def _get_connection(self):
        """Get database connection directly."""
        if self._connection is None or not self._connection.is_connected():
            try:
                self._connection = mysql.connector.connect(
                    host=os.getenv('DB_HOST', '127.0.0.1'),
                    port=int(os.getenv('DB_PORT', 3306)),
                    user=os.getenv('DB_USER', 'root'),
                    password=os.getenv('DB_PASSWORD', ''),
                    database=os.getenv('DB_NAME', 'vital')
                )
                print("Database connected successfully")
            except Error as e:
                print(f"Database connection error: {e}")
                return None
        return self._connection

    def fetch_tasks(self, user_id: Optional[int] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch tasks from database - tasks table has conversation_id, not user_id."""
        try:
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT id, conversation_id, intent, action, status, 
                       infos_json, missing_fields_json, created_at, updated_at
                FROM tasks
                ORDER BY created_at DESC
                LIMIT %s
            """
            cursor.execute(query, (limit,))
            
            results = cursor.fetchall()
            cursor.close()
            print(f"Fetched {len(results)} tasks")
            return results
        except Error as e:
            print(f"Error fetching tasks: {e}")
            return []

    def fetch_conversations(self, user_id: Optional[int] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch conversations from database."""
        try:
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            if user_id:
                query = """
                    SELECT id, user_id, title, created_at, updated_at
                    FROM conversations
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """
                cursor.execute(query, (user_id, limit))
            else:
                query = """
                    SELECT id, user_id, title, created_at, updated_at
                    FROM conversations
                    ORDER BY created_at DESC
                    LIMIT %s
                """
                cursor.execute(query, (limit,))
            
            results = cursor.fetchall()
            cursor.close()
            print(f"Fetched {len(results)} conversations")
            return results
        except Error as e:
            print(f"Error fetching conversations: {e}")
            return []

    def fetch_messages(self, conversation_id: Optional[int] = None, limit: int = 200) -> List[Dict[str, Any]]:
        """Fetch messages from database."""
        if not conversation_id:
            return []
        
        try:
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT id, conversation_id, role, text, asset_url, asset_kind, 
                       display_json, created_at
                FROM messages
                WHERE conversation_id = %s
                ORDER BY created_at ASC
                LIMIT %s
            """
            cursor.execute(query, (conversation_id, limit))
            
            results = cursor.fetchall()
            cursor.close()
            print(f"Fetched {len(results)} messages for conversation {conversation_id}")
            return results
        except Error as e:
            print(f"Error fetching messages: {e}")
            return []

    def fetch_publications(self, media_type: str = "both", limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch publications from database."""
        publications = []
        
        try:
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            if media_type in ("image", "both"):
                try:
                    cursor.execute("""
                        SELECT id, produit, occasion, generation_mode, date_publication, created_at
                        FROM generated_images
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, (limit,))
                    images = cursor.fetchall()
                    for img in images:
                        img["type"] = "image"
                    publications.extend(images)
                    print(f"Fetched {len(images)} images")
                except Error as e:
                    print(f"Error fetching images: {e}")
            
            if media_type in ("video", "both"):
                try:
                    cursor.execute("""
                        SELECT id, produit, occasion, generation_mode, date_publication, created_at
                        FROM generated_videos
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, (limit,))
                    videos = cursor.fetchall()
                    for vid in videos:
                        vid["type"] = "video"
                    publications.extend(videos)
                    print(f"Fetched {len(videos)} videos")
                except Error as e:
                    print(f"Error fetching videos: {e}")
            
            cursor.close()
            publications.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return publications[:limit]
        except Error as e:
            print(f"Error fetching publications: {e}")
            return []

    def fetch_structured_reports(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch structured reports from database."""
        try:
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT id, raw_text, text_corrige, mouvement, potentiel, conseil, 
                       emplacement_proximite, emplacement_qualite, personnel_attitude,
                       mise_en_place, invitations, stock_disponibilite, type_pharmacie,
                       eligibilite_animation, aucun_point_fort, created_at
                FROM structured_reports
                ORDER BY created_at DESC
                LIMIT %s
            """
            cursor.execute(query, (limit,))
            
            results = cursor.fetchall()
            cursor.close()
            print(f"Fetched {len(results)} structured reports")
            return results
        except Error as e:
            print(f"Error fetching structured reports: {e}")
            return []