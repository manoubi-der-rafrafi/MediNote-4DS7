import os
from google import genai

DEFAULT_MODEL_NAME = "gemini-2.5-flash-lite"
DEFAULT_API_KEY = "AIzaSyAzxg0dbL-3qAas1QqH0paX3YHd9MX-Q4o"

class GeminiClientConfigError(RuntimeError):
    pass

def get_api_key() -> str:
    return DEFAULT_API_KEY  # ← ligne modifiée

def build_client() -> genai.Client:
    return genai.Client(api_key=get_api_key())