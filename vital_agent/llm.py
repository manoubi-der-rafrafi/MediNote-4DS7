import os

import requests
from google import genai


class GroqLLMError(RuntimeError):
    pass


class GeminiLLMError(RuntimeError):
    pass


MODEL_ID = "llama-3.3-70b-versatile"
GEMINI_MODEL_ID = "gemini-2.5-flash-lite"


def load_llm():
    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
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

    def call_with_gemini_fallback(prompt: str, groq_error: Exception) -> str:
        if gemini_client is None:
            raise GroqLLMError(str(groq_error)) from groq_error

        print(f"Groq unavailable, falling back to Gemini: {groq_error}")
        return call_gemini(prompt)

    def call_api(prompt: str) -> str:
        if not groq_api_key:
            return call_with_gemini_fallback(
                prompt,
                GroqLLMError("GROQ_API_KEY is missing."),
            )

        payload = {
            "model": MODEL_ID,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000,
            "temperature": 0.3,
        }
        headers = {
            "Authorization": f"Bearer {groq_api_key}",
            "Content-Type": "application/json",
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
            return call_with_gemini_fallback(
                prompt,
                GroqLLMError(f"Groq API timeout after 30s (model={MODEL_ID})."),
            )
        except requests.HTTPError as exc:
            status_code = getattr(exc.response, "status_code", "unknown")
            details = ""
            try:
                body = exc.response.text.strip()
                if body:
                    details = f" Details: {body[:500]}"
            except Exception:
                pass
            return call_with_gemini_fallback(
                prompt,
                GroqLLMError(
                    f"Groq API HTTP {status_code} (model={MODEL_ID}).{details}"
                ),
            )
        except requests.RequestException as exc:
            return call_with_gemini_fallback(
                prompt,
                GroqLLMError(
                    f"Groq API request failed (model={MODEL_ID}): {exc}"
                ),
            )

        try:
            return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            return call_with_gemini_fallback(
                prompt,
                GroqLLMError(
                    f"Groq API returned an invalid response (model={MODEL_ID})."
                ),
            )

    if groq_api_key:
        print(f"LLM ready - Groq API: {MODEL_ID}")
    else:
        print("LLM ready - Groq disabled (missing GROQ_API_KEY)")
    if gemini_client is not None:
        print(f"LLM fallback ready - Gemini API: {GEMINI_MODEL_ID}")
    return call_api
