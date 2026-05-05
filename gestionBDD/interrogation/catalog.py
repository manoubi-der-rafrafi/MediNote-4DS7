from __future__ import annotations

from typing import Any


TABLE_CATALOG: dict[str, dict[str, Any]] = {
    "structured_reports": {
        "description": "Rapports structures et sauves en base.",
        "columns": [
            "id",
            "raw_text",
            "text_corrige",
            "mouvement",
            "potentiel",
            "conseil",
            "emplacement_proximite",
            "emplacement_qualite",
            "personnel_attitude",
            "mise_en_place",
            "invitations",
            "stock_disponibilite",
            "type_pharmacie",
            "eligibilite_animation",
            "aucun_point_fort",
            "created_at",
        ],
        "allowed_values": {
            "mouvement": ["aucun", "tres_faible", "faible", "moyen", "forte", "tres_forte", "non_precise"],
            "potentiel": ["aucun", "faible", "moyen", "forte", "non_precise"],
            "conseil": ["aucun", "faible", "moyen", "forte", "non_precise"],
            "emplacement_qualite": ["adequat", "inadequat", "non_precise"],
            "personnel_attitude": ["positive", "negative", "positive_et_negative", "non_precise"],
            "mise_en_place": ["absente", "faible", "moyenne", "forte", "non_precise"],
            "aucun_point_fort": ["oui", "non"],
        },
    },
    "generated_images": {
        "description": "Images marketing generees et sauvees en base.",
        "columns": [
            "id",
            "image_path",
            "prompt_image",
            "description_post",
            "accepted",
            "occasion",
            "occasion_type",
            "generation_mode",
            "produit",
            "product_url",
            "image_url",
            "date_occasion",
            "date_publication",
            "created_at",
        ],
    },
    "generated_videos": {
        "description": "Videos marketing generees et sauvees en base.",
        "columns": [
            "id",
            "video_path",
            "prompt_vdo",
            "description_post",
            "accepted",
            "occasion",
            "generation_mode",
            "produit",
            "produit_source",
            "code_article",
            "product_url",
            "image_url",
            "date_occasion",
            "date_publication",
            "created_at",
        ],
    },
    "conversations": {
        "description": (
            "Discussions de l'utilisateur courant. Toujours filtrer avec conversations.user_id."
        ),
        "columns": [
            "id",
            "user_id",
            "title",
            "created_at",
            "updated_at",
        ],
    },
    "messages": {
        "description": (
            "Messages des discussions. Pour limiter a l'utilisateur courant, joindre conversations "
            "sur messages.conversation_id = conversations.id et filtrer conversations.user_id."
        ),
        "columns": [
            "id",
            "conversation_id",
            "role",
            "text",
            "created_at",
        ],
        "allowed_values": {
            "role": ["user", "assistant", "system"],
        },
    },
    "tasks": {
        "description": (
            "Taches metier des discussions. Pour limiter a l'utilisateur courant, joindre conversations "
            "sur tasks.conversation_id = conversations.id et filtrer conversations.user_id."
        ),
        "columns": [
            "id",
            "conversation_id",
            "intent",
            "action",
            "status",
            "infos_json",
            "missing_fields_json",
            "last_message_id",
            "created_at",
            "updated_at",
        ],
        "allowed_values": {
            "intent": ["rapport", "publication"],
            "action": ["structure_report", "generate_publication", "query_database"],
            "status": ["draft", "waiting_user_input", "in_progress", "completed", "cancelled", "failed"],
        },
    },
}


def resolve_tables_for_query(classification_result: dict[str, Any]) -> list[str]:
    intent = str(classification_result.get("intent", "")).strip().lower()
    action = str(classification_result.get("action", "")).strip().lower()
    if action != "query_database":
        return []

    if intent == "rapport":
        return ["structured_reports"]

    if intent in {"conversation", "discussion"}:
        scope = str(classification_result.get("conversation_scope", "")).strip().lower()
        if scope == "conversations":
            return ["conversations"]
        if scope == "messages":
            return ["messages", "conversations"]
        if scope == "tasks":
            return ["tasks", "conversations"]
        if scope == "all":
            return ["conversations", "messages", "tasks"]
        return []

    if intent != "publication":
        return []

    media_scope = str(classification_result.get("media_scope", "")).strip().lower()
    if media_scope == "image":
        return ["generated_images"]
    if media_scope == "video":
        return ["generated_videos"]
    if media_scope == "both":
        return ["generated_images", "generated_videos"]
    return []


def build_catalog_prompt_fragment(tables: list[str]) -> str:
    sections: list[str] = []
    for table_name in tables:
        table_definition = TABLE_CATALOG.get(table_name)
        if not table_definition:
            continue

        columns = "\n".join(f"- {column}" for column in table_definition["columns"])
        sections.append(
            "\n".join(
                [
                    f"Table: {table_name}",
                    f"Description: {table_definition['description']}",
                    "Colonnes autorisees:",
                    columns,
                    _build_allowed_values_fragment(table_definition),
                ]
            )
        )

    return "\n\n".join(sections)


def _build_allowed_values_fragment(table_definition: dict[str, Any]) -> str:
    allowed_values = table_definition.get("allowed_values")
    if not isinstance(allowed_values, dict) or not allowed_values:
        return "Valeurs standardisees: non specifiees"

    lines = ["Valeurs standardisees a utiliser exactement dans les filtres:"]
    for column_name, values in allowed_values.items():
        rendered_values = ", ".join(str(value) for value in values)
        lines.append(f"- {column_name}: {rendered_values}")
    return "\n".join(lines)
