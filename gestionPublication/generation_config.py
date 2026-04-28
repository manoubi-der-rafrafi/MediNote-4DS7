import os
from pathlib import Path
from typing import Any

from google import genai


DEFAULT_MODEL_NAME = "gemini-2.5-flash-lite"
VIDEO_MODEL_NAME = "sora-2"
VIDEO_OUTPUT_FILENAME = "generated_video.mp4"
VIDEO_SECONDS = "8"
VIDEO_SIZE = "720x1280"
VIDEO_STATUS_POLL_SECONDS = 15
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OPENAI_VIDEOS_URL = "https://api.openai.com/v1/videos"


class PublicationGeminiConfigError(RuntimeError):
    pass


class PublicationOpenAIConfigError(RuntimeError):
    pass


def get_gemini_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not api_key.strip():
        raise PublicationGeminiConfigError(
            "La variable d'environnement GEMINI_API_KEY est absente ou vide."
        )
    return api_key.strip()


def build_gemini_client() -> genai.Client:
    return genai.Client(api_key=get_gemini_api_key())


def get_openai_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or not api_key.strip():
        raise PublicationOpenAIConfigError(
            "La variable d'environnement OPENAI_API_KEY est absente ou vide."
        )
    return api_key.strip()


def build_video_prompt(context: dict[str, Any]) -> str:
    return f"""
Tu es un assistant marketing social media et video ads.

Ta tache:
- generer une description de post Facebook ou Instagram en francais naturel
- generer un prompt_VDO detaille pour une video publicitaire verticale courte
- choisir une date_publication comprise obligatoirement dans l'intervalle [date_actuelle, date_occasion]

Informations produit:
- marque: Vital
- contexte: il s'agit d'une publication marketing video pour un produit de la gamme Vital
- produit: {context["produit"]}
- produit_source_csv: {context["produit_source"]}
- occasion: {context["occasion"]}
- saison: {context["saison"]}
- date_actuelle: {context["date_actuelle"]}
- date_occasion: {context["date_occasion"]}
- product_url: {context["product_url"]}
- image_url_officielle: {context["image_url"]}

Contraintes:
- Retourne uniquement un JSON valide.
- La date_publication doit etre une date ISO au format YYYY-MM-DD.
- La date_publication doit etre entre date_actuelle et date_occasion incluses.
- La description_post doit faire comprendre naturellement qu'il s'agit d'une publication pour la marque Vital.
- Le ton doit etre elegant, chaleureux et adapte a l'occasion.
- N'invente pas de promesses medicales.
- Le prompt_VDO doit decrire une video publicitaire verticale 9:16, premium, realiste et courte, adaptee aux reseaux sociaux.
- Le prompt_VDO doit utiliser exactement le produit Vital correspondant.
- Le prompt_VDO doit decrire clairement: scene, cadrage, ambiance, mouvements de camera, lumiere, texte bref a l'ecran si utile, et fin propre pour publication sociale.
- Si image_url_officielle est renseignee, le prompt_VDO doit demander explicitement de l'utiliser comme reference principale du produit et comme base visuelle du premier plan.
- Le packaging, la forme, les couleurs, le logo et le nom du produit doivent rester identiques au visuel officiel Vital.
- Il ne faut pas inventer un autre flacon, une autre boite, une autre etiquette ou un autre produit.
- Le produit doit rester l'element central de la video.
- Evite les scenes avec personnes reelles reconnaissables.

Format attendu:
{{
  "description_post": "...",
  "prompt_VDO": "...",
  "date_publication": "YYYY-MM-DD"
}}
""".strip()
