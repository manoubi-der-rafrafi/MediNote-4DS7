import os

import requests
from google import genai


class GroqLLMError(RuntimeError):
    pass


class GeminiLLMError(RuntimeError):
    pass


MODEL_ID        = "llama-3.3-70b-versatile"
GEMINI_MODEL_ID = "gemini-2.5-flash"
TEMPERATURE     = 0.1
TOP_P           = 0.85
MAX_TOKENS      = 600


def _load_groq_keys() -> list[str]:
    keys = []
    k = os.getenv("GROQ_API_KEY", "").strip()
    if k:
        keys.append(k)
    for i in range(2, 10):
        k = os.getenv(f"GROQ_API_KEY_{i}", "").strip()
        if k:
            keys.append(k)
    return keys


def _load_gemini_keys() -> list[str]:
    keys = []
    k = os.getenv("GEMINI_API_KEY", "").strip()
    if k:
        keys.append(k)
    for i in range(1, 9):
        k = os.getenv(f"GEMINI_API_KEY_{i}", "").strip()
        if k:
            keys.append(k)
    return keys


def load_llm():
    groq_keys      = _load_groq_keys()
    gemini_keys    = _load_gemini_keys()
    groq_idx       = [0]
    gemini_key_idx = [0]

    def call_gemini(prompt: str) -> str:
        if not gemini_keys:
            raise GeminiLLMError("Aucune GEMINI_API_KEY trouvée.")
        for attempt in range(len(gemini_keys)):
            client = genai.Client(api_key=gemini_keys[gemini_key_idx[0]])
            try:
                response = client.models.generate_content(
                    model=GEMINI_MODEL_ID,
                    contents=prompt,
                    config={"temperature": TEMPERATURE, "top_p": TOP_P, "max_output_tokens": MAX_TOKENS},
                )
                text = getattr(response, "text", "") or ""
                if text.strip():
                    return text.strip()
            except Exception as exc:
                if any(c in str(exc) for c in ["429", "RESOURCE_EXHAUSTED", "API_KEY_INVALID", "400"]):
                    gemini_key_idx[0] = (gemini_key_idx[0] + 1) % len(gemini_keys)
                    print(f"Gemini rotation → clé {gemini_key_idx[0]}")
                    continue
                raise GeminiLLMError(f"Gemini failed: {exc}") from exc
        raise GeminiLLMError("Toutes les clés Gemini sont épuisées.")

    def call_with_gemini_fallback(prompt: str, groq_error: Exception) -> str:
        if not gemini_keys:
            raise GroqLLMError(str(groq_error)) from groq_error
        print(f"Groq indisponible, bascule Gemini: {groq_error}")
        return call_gemini(prompt)

    def call_api(prompt: str) -> str:
        if not groq_keys:
            return call_with_gemini_fallback(prompt, GroqLLMError("Aucune GROQ_API_KEY."))

        for attempt in range(len(groq_keys)):
            api_key = groq_keys[groq_idx[0]]
            payload = {
                "model": MODEL_ID,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": MAX_TOKENS,
                "temperature": TEMPERATURE,
                "top_p": TOP_P,
            }
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            try:
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers, json=payload, timeout=30,
                )
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"].strip()
            except requests.HTTPError as exc:
                status = getattr(exc.response, "status_code", 0)
                if status == 429:
                    groq_idx[0] = (groq_idx[0] + 1) % len(groq_keys)
                    print(f"Groq 429, rotation → clé {groq_idx[0]}")
                    continue
                return call_with_gemini_fallback(prompt, GroqLLMError(f"Groq HTTP {status}"))
            except requests.Timeout:
                return call_with_gemini_fallback(prompt, GroqLLMError("Groq timeout."))
            except Exception as exc:
                return call_with_gemini_fallback(prompt, GroqLLMError(str(exc)))

        return call_with_gemini_fallback(prompt, GroqLLMError("Toutes les clés Groq épuisées."))

    print(f"LLM ready - Groq: {len(groq_keys)} clé(s) | {MODEL_ID} | temp={TEMPERATURE} top_p={TOP_P} max_tokens={MAX_TOKENS}")
    print(f"Gemini fallback: {len(gemini_keys)} clé(s) | {GEMINI_MODEL_ID}")
    return call_api