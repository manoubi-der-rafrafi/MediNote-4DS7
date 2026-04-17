import os

from google import genai


DEFAULT_MODEL_NAME = "gemini-2.5-flash-lite"
DEFAULT_API_KEY = "AIzaSyAgikj7qAiLn7vyy74T8eMq19wGiLJR4yA"


class GeminiClientConfigError(RuntimeError):
    pass


def get_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY", DEFAULT_API_KEY)
    if not api_key or not api_key.strip():
        raise GeminiClientConfigError(
            "La variable d'environnement GEMINI_API_KEY est absente ou vide."
        )
    return api_key.strip()


def build_client() -> genai.Client:
    return genai.Client(api_key=get_api_key())
