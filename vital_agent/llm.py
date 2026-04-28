import os

import requests
from google import genai


class GroqLLMError(RuntimeError):
    pass


class GeminiLLMError(RuntimeError):
    pass


GROQ_API_KEY = "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"
MODEL_ID = "llama-3.3-70b-versatile"
GEMINI_MODEL_ID = "gemini-2.5-flash-lite"


def load_llm():
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    gemini_client = None
    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if gemini_api_key:
        gemini_client = genai.Client(api_key=gemini_api_key)

    def call_gemini(prompt: str) -> str:
        if gemini_client is None:
            raise GeminiLLMError("GEMINI_API_KEY is missing.")

        try:
            response = gemini_client.models.generate_content(
                model=GEMINI_MODEL_ID,
                contents=prompt,
                config={"temperature": 0.3},
            )
        except Exception as exc:
            raise GeminiLLMError(
                f"Gemini request failed (model={GEMINI_MODEL_ID}): {exc}"
            ) from exc

        text = getattr(response, "text", "") or ""
        if text.strip():
            return text.strip()

        raise GeminiLLMError(
            f"Gemini returned an empty response (model={GEMINI_MODEL_ID})."
        )

    def call_api(prompt: str) -> str:
        payload = {
            "model": MODEL_ID,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000,
            "temperature": 0.3,
        }

        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
        except requests.Timeout as exc:
            raise GroqLLMError(
                f"Groq API timeout after 30s (model={MODEL_ID})."
            ) from exc
        except requests.HTTPError as exc:
            status_code = getattr(exc.response, "status_code", "unknown")
            details = ""
            try:
                body = exc.response.text.strip()
                if body:
                    details = f" Details: {body[:500]}"
            except Exception:
                pass
            raise GroqLLMError(
                f"Groq API HTTP {status_code} (model={MODEL_ID}).{details}"
            ) from exc
        except requests.RequestException as exc:
            if gemini_client is not None:
                print(
                    f"Groq unavailable, falling back to Gemini: {exc}"
                )
                return call_gemini(prompt)
            raise GroqLLMError(
                f"Groq API request failed (model={MODEL_ID}): {exc}"
            ) from exc

        try:
            return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            raise GroqLLMError(
                f"Groq API returned an invalid response (model={MODEL_ID})."
            ) from exc

    print(f"LLM ready - Groq API: {MODEL_ID}")
    if gemini_client is not None:
        print(f"LLM fallback ready - Gemini API: {GEMINI_MODEL_ID}")
    return call_api
