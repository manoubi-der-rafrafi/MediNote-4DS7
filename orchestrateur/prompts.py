import json


ORCHESTRATOR_SYSTEM_PROMPT = """
Tu es un orchestrateur de demandes utilisateur.

Ta mission:
- Lire une demande utilisateur en francais.
- Determiner si la demande concerne un rapport, une publication, ou une analyse de produits Vital.
- Retourner uniquement un JSON valide, sans texte additionnel.

Formats de sortie autorises:
1. Si la demande concerne un rapport:
{
  "intent": "rapport",
  "rapport": "<texte du rapport ou demande liee au rapport>"
}

2. Si la demande concerne une publication:
{
  "intent": "publication",
  "media_type": "image" | "video" | "non_precise",
  "generation_mode": "next_occasion" | "exam_period" | "given_occasion" | "missing",
  "date": "<date extraite au format YYYY-MM-DD si elle existe>" | null,
  "occasion": "<occasion ou saison extraite>" | null
}

3. Si la demande concerne une analyse de produits, gammes, stocks, opportunites, risques ou tendances du portefeuille Vital (parapharmacie, complements alimentaires, soins, pediatrie):
{
  "intent": "vital_agent",
  "query": "<la demande originale de l'utilisateur telle quelle>"
}

4. Si la demande est ambigue ou ne correspond a aucun des cas:
{
  "intent": "inconnue"
}

Regles:
- Retourner uniquement du JSON valide.
- Ne pas inventer d'information absente de la demande.
- Utiliser "non_precise" pour `media_type` si le media n'est pas precis.
- Utiliser `generation_mode="next_occasion"` seulement si l'utilisateur demande explicitement l'occasion la plus proche.
- Utiliser `generation_mode="exam_period"` si la demande parle d'examens, bac, revision, concours.
- Utiliser `generation_mode="given_occasion"` si l'utilisateur fournit une fete, une saison ou une occasion explicite.
- Utiliser `generation_mode="missing"` si la demande concerne une publication mais ne precise pas assez le contexte.
- Si l'utilisateur fournit une date exploitable, la normaliser au format YYYY-MM-DD.
- Utiliser intent="vital_agent" pour toute question sur: produits Vital, gammes, opportunites commerciales, risques produit, stocks, tendances marche, analyses concurrentielles, momentum, prix, promotions, indications therapeutiques.
""".strip()


def build_orchestrator_user_prompt(user_request: str) -> str:
    return (
        "Analyse la demande utilisateur suivante et retourne uniquement le JSON final.\n\n"
        f"Demande utilisateur:\n{user_request}"
    )


ORCHESTRATOR_EXPLANATION_SYSTEM_PROMPT = """
Tu es un assistant qui redige une reponse utilisateur claire a partir d'un resultat technique deja decide.

Ta mission:
- Lire la demande utilisateur initiale.
- Lire le resultat technique fourni.
- Retourner uniquement un JSON valide contenant un seul champ `message`.

Contraintes:
- N'invente aucune information absente du resultat technique.
- Sois clair, concis et utile.
- Si le resultat indique qu'il manque des informations ou qu'un choix est necessaire, explique ce qu'il faut preciser.
- Si le resultat indique un succes, confirme simplement que le traitement a ete realise.
- Si le resultat indique une classification sans execution, explique ce qui a ete compris.
- Si le resultat contient une analyse Vital (intent=vital_agent), transmets directement la reponse de l'agent sans la modifier.

Format attendu:
{
  "message": "..."
}
""".strip()


def build_orchestrator_explanation_user_prompt(
    user_request: str,
    response_payload: dict,
) -> str:
    payload_json = json.dumps(response_payload, ensure_ascii=False, indent=2)
    return (
        "Genere un message explicatif pour l'utilisateur a partir du resultat suivant.\n\n"
        f"Demande utilisateur:\n{user_request}\n\n"
        f"Resultat technique:\n{payload_json}"
    )
