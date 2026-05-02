from google import genai

from gemini_keyring import (
    DEFAULT_MODEL_NAME as SHARED_DEFAULT_MODEL_NAME,
    GeminiKeyConfigError,
    build_client as build_shared_client,
    generate_content_with_key_rotation as generate_shared_content_with_key_rotation,
    get_api_key as get_shared_api_key,
)
from typing import Any

DEFAULT_MODEL_NAME = SHARED_DEFAULT_MODEL_NAME


class StructurationGeminiConfigError(RuntimeError):
    pass


def get_api_key() -> str:
    try:
        return get_shared_api_key()
    except GeminiKeyConfigError as exc:
        raise StructurationGeminiConfigError(
            str(exc)
        ) from exc


def build_client() -> genai.Client:
    try:
        return build_shared_client()
    except GeminiKeyConfigError as exc:
        raise StructurationGeminiConfigError(str(exc)) from exc


def generate_content_with_key_rotation(**kwargs: Any) -> Any:
    try:
        return generate_shared_content_with_key_rotation(**kwargs)
    except GeminiKeyConfigError as exc:
        raise StructurationGeminiConfigError(str(exc)) from exc
