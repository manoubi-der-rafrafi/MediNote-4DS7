from collections.abc import Iterator
from typing import Any

from google import genai

from gemini_keyring import (
    GeminiKeyConfigError,
    build_client as build_shared_client,
    generate_content_with_key_rotation as generate_shared_content_with_key_rotation,
    get_api_key as get_shared_api_key,
    get_api_keys as get_shared_api_keys,
    iter_clients as iter_shared_clients,
)


DEFAULT_MODEL_NAME = "gemini-2.5-flash-lite"


class GeminiClientConfigError(RuntimeError):
    pass


def get_api_keys() -> list[str]:
    try:
        return get_shared_api_keys()
    except GeminiKeyConfigError as exc:
        raise GeminiClientConfigError(str(exc)) from exc


def get_api_key() -> str:
    return get_api_keys()[0]


def iter_clients() -> Iterator[genai.Client]:
    try:
        yield from iter_shared_clients()
    except GeminiKeyConfigError as exc:
        raise GeminiClientConfigError(str(exc)) from exc


def build_client(api_key: str | None = None) -> genai.Client:
    try:
        return build_shared_client(api_key=api_key)
    except GeminiKeyConfigError as exc:
        raise GeminiClientConfigError(str(exc)) from exc


def generate_content_with_key_rotation(**kwargs: Any) -> Any:
    try:
        return generate_shared_content_with_key_rotation(**kwargs)
    except GeminiKeyConfigError as exc:
        raise GeminiClientConfigError(str(exc)) from exc
