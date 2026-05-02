import os
import re
from collections.abc import Iterator
from typing import Any

from google import genai


DEFAULT_MODEL_NAME = "gemini-2.5-flash-lite"


class GeminiKeyConfigError(RuntimeError):
    pass


def get_api_keys() -> list[str]:
    candidates: list[str] = []

    for name in ("GEMINI_API_KEY", "GEMINI_API_KEYS"):
        value = os.getenv(name)
        if value:
            candidates.extend(
                item.strip()
                for item in re.split(r"[,;\s]+", value)
                if item.strip()
            )

    for index in range(1, 9):
        value = os.getenv(f"GEMINI_API_KEY_{index}")
        if value and value.strip():
            candidates.append(value.strip())

    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate not in seen:
            deduped.append(candidate)
            seen.add(candidate)

    if not deduped:
        raise GeminiKeyConfigError(
            "Aucune cle Gemini trouvee. Configurez GEMINI_API_KEY, GEMINI_API_KEYS, "
            "ou GEMINI_API_KEY_1 jusqu'a GEMINI_API_KEY_8."
        )

    return deduped


def get_api_key() -> str:
    return get_api_keys()[0]


def iter_clients() -> Iterator[genai.Client]:
    for api_key in get_api_keys():
        yield genai.Client(api_key=api_key)


def build_client(api_key: str | None = None) -> genai.Client:
    return genai.Client(api_key=(api_key or get_api_key()))


def is_key_retryable_error(error: Exception) -> bool:
    normalized = str(error).lower()
    retry_markers = (
        "resource_exhausted",
        "quota exceeded",
        "429",
        "permission_denied",
        "api key not valid",
        "api_key_invalid",
        "api key was reported as leaked",
        "403",
        "401",
    )
    return any(marker in normalized for marker in retry_markers)


def generate_content_with_key_rotation(**kwargs: Any) -> Any:
    last_error: Exception | None = None

    try:
        clients = list(iter_clients())
    except GeminiKeyConfigError:
        raise

    for client in clients:
        try:
            return client.models.generate_content(**kwargs)
        except Exception as exc:
            last_error = exc
            if not is_key_retryable_error(exc):
                raise

    if last_error is not None:
        raise RuntimeError(
            f"Toutes les cles Gemini configurees ont echoue. Derniere erreur: {last_error}"
        ) from last_error

    raise GeminiKeyConfigError("Aucune cle Gemini disponible pour effectuer la requete.")
