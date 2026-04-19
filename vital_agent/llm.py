import requests

GROQ_API_KEY = "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"  # ← gratuit sur console.groq.com
MODEL_ID     = "llama-3.3-70b-versatile"

def load_llm():
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    def call_api(prompt: str) -> str:
        payload = {
            "model": MODEL_ID,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000,
            "temperature": 0.3,
        }
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()

    print(f"✅ LLM prêt — Groq API : {MODEL_ID}")
    return call_api
