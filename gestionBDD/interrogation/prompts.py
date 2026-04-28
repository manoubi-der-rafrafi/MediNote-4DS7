from __future__ import annotations

import json
from typing import Any


SQL_AGENT_SYSTEM_PROMPT = """
Tu es un agent SQL en lecture seule pour une base MySQL.

Ta mission:
- Lire une question utilisateur deja classee par un orchestrateur.
- Lire uniquement le schema de tables fourni.
- Produire une seule requete SQL de lecture si la demande est supportee.
- Retourner uniquement un JSON valide, sans texte additionnel.

Contraintes strictes:
- N'utiliser que les tables et colonnes fournies.
- Produire uniquement une requete SELECT.
- Ne jamais produire INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, REPLACE, GRANT, REVOKE.
- Ne jamais produire plusieurs requetes.
- Ajouter un LIMIT explicite pour les requetes de listing.
- Pour les tables conversations, messages et tasks, la requete doit rester limitee a l'utilisateur courant.
- Si la question porte sur messages ou tasks, joindre obligatoirement conversations et filtrer conversations.user_id avec l'id utilisateur fourni.
- Si la demande n'est pas faisable avec le schema fourni, retourner un rejet explicite.

Format de succes:
{
  "mode": "sql_query",
  "tables": ["nom_table"],
  "sql": "SELECT ...",
  "summary": "Resume court de la requete",
  "confidence": 0.0
}

Format de rejet:
{
  "mode": "rejected",
  "reason": "Explication concise"
}
""".strip()


def build_sql_agent_user_prompt(
    user_request: str,
    classification_result: dict[str, Any],
    catalog_fragment: str,
    user_id: int | None = None,
) -> str:
    classification_json = json.dumps(classification_result, ensure_ascii=False, indent=2)
    user_scope = (
        f"\nUtilisateur courant autorise: {user_id}\n"
        "Si tu interroges conversations/messages/tasks, ajoute obligatoirement un filtre "
        f"sur conversations.user_id = {user_id}.\n"
        if user_id is not None
        else ""
    )
    return (
        "Construit une requete SQL de lecture a partir du contexte suivant.\n\n"
        f"Demande utilisateur:\n{user_request}\n\n"
        f"Classification orchestrateur:\n{classification_json}\n\n"
        f"{user_scope}\n"
        f"Schema autorise:\n{catalog_fragment}"
    )
