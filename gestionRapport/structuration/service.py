from pydantic import ValidationError

from .gemini_client import (
    DEFAULT_MODEL_NAME,
    StructurationGeminiConfigError,
    build_client,
)
from .heuristics import classify_point_fort_locally
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .repository import delete_structured_report, save_structured_report
from .schemas import PointFortStructured


class StructurationConfigError(RuntimeError):
    pass


class StructurationRequestError(RuntimeError):
    pass


class StructurationResponseError(RuntimeError):
    pass


class StructurationPersistenceError(RuntimeError):
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
                    structured_report = response.parsed
                else:
                    structured_report = PointFortStructured.model_validate(response.parsed)
            else:
                structured_report = PointFortStructured.model_validate_json(response.text)
        except ValidationError as exc:
            raise StructurationResponseError(
                "La reponse Gemini ne respecte pas le schema attendu."
            ) from exc
        except Exception as exc:
            raise StructurationResponseError(str(exc)) from exc

        try:
            save_structured_report(text_brut, structured_report)
        except Exception as exc:
            raise StructurationPersistenceError(
                f"Echec de la sauvegarde du rapport structure en BDD: {exc}"
            ) from exc

        return structured_report

    def handle_locally(self, text_brut: str) -> PointFortStructured:
        return classify_point_fort_locally(text_brut)

    def delete_report(self, report_id: int) -> dict:
        try:
            deleted_row = delete_structured_report(int(report_id))
        except Exception as exc:
            raise StructurationPersistenceError(
                f"Echec de la suppression du rapport structure en BDD: {exc}"
            ) from exc

        if deleted_row is None:
            return {
                "status": "not_found",
                "report_id": int(report_id),
                "deleted": False,
            }

        return {
            "status": "success",
            "report_id": int(deleted_row.id),
            "deleted": True,
        }
