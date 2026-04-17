from pydantic import ValidationError

from .gemini_client import (
    DEFAULT_MODEL_NAME,
    StructurationGeminiConfigError,
    build_client,
)
from .heuristics import classify_point_fort_locally
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .schemas import PointFortStructured


class StructurationConfigError(RuntimeError):
    pass


class StructurationRequestError(RuntimeError):
    pass


class StructurationResponseError(RuntimeError):
    pass


class StructurationRapportService:
    def __init__(self, model_name: str = DEFAULT_MODEL_NAME) -> None:
        self.model_name = model_name

    def handle(self, text_brut: str) -> PointFortStructured:
        try:
            client = build_client()
        except StructurationGeminiConfigError as exc:
            raise StructurationConfigError(str(exc)) from exc

        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents=[
                    {"role": "user", "parts": [{"text": SYSTEM_PROMPT}]},
                    {"role": "user", "parts": [{"text": build_user_prompt(text_brut)}]},
                ],
                config={
                    "response_mime_type": "application/json",
                    "response_schema": PointFortStructured,
                    "temperature": 0,
                },
            )
        except Exception as exc:
            raise StructurationRequestError(str(exc)) from exc

        try:
            if getattr(response, "parsed", None) is not None:
                if isinstance(response.parsed, PointFortStructured):
                    return response.parsed
                return PointFortStructured.model_validate(response.parsed)

            return PointFortStructured.model_validate_json(response.text)
        except ValidationError as exc:
            raise StructurationResponseError(
                "La reponse Gemini ne respecte pas le schema attendu."
            ) from exc
        except Exception as exc:
            raise StructurationResponseError(str(exc)) from exc

    def handle_locally(self, text_brut: str) -> PointFortStructured:
        return classify_point_fort_locally(text_brut)
