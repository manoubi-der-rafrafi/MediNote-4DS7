import json
import re
from typing import Any

from pydantic import ValidationError

from gestionPublication import (
    ImageGenerationConfigError,
    ImageGenerationContextError,
    ImageGenerationPersistenceError,
    ImageGenerationRequestError,
    ImageGenerationRequestValidationError,
    ImageGenerationService,
    PublicationConfigError,
    PublicationPersistenceError,
    PublicationRequestError,
    PublicationResponseError,
    PublicationService,
)
from gestionRapport.structuration import StructurationRapportService
from .gemini_client import DEFAULT_MODEL_NAME, GeminiClientConfigError, build_client
from .prompts import (
    ORCHESTRATOR_EXPLANATION_SYSTEM_PROMPT,
    ORCHESTRATOR_SYSTEM_PROMPT,
    build_orchestrator_explanation_user_prompt,
    build_orchestrator_user_prompt,
)


class OrchestratorConfigError(RuntimeError):
    pass


class OrchestratorRequestError(RuntimeError):
    pass


class OrchestratorResponseError(RuntimeError):
    pass


class OrchestratorProcessingError(RuntimeError):
    pass


class OrchestratorService:
    def __init__(self, model_name: str = DEFAULT_MODEL_NAME) -> None:
        self.model_name = model_name
        self.report_service = StructurationRapportService()
        self.publication_service = PublicationService()
        self.image_generation_service = ImageGenerationService()

    def handle(self, user_request: str) -> dict[str, Any] | list[Any]:
        local_classification = self._try_local_publication_classification(user_request)
        if local_classification is not None:
            try:
                return self._finalize_response(None, user_request, local_classification)
            except (
                ImageGenerationConfigError,
                ImageGenerationContextError,
                ImageGenerationPersistenceError,
                ImageGenerationRequestError,
                ImageGenerationRequestValidationError,
                PublicationConfigError,
                PublicationPersistenceError,
                PublicationRequestError,
                PublicationResponseError,
            ) as exc:
                raise OrchestratorProcessingError(str(exc)) from exc
            except Exception as exc:
                raise OrchestratorResponseError(str(exc)) from exc

        try:
            client = build_client()
        except GeminiClientConfigError as exc:
            raise OrchestratorConfigError(str(exc)) from exc

        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents=[
                    {"role": "user", "parts": [{"text": ORCHESTRATOR_SYSTEM_PROMPT}]},
                    {
                        "role": "user",
                        "parts": [{"text": build_orchestrator_user_prompt(user_request)}],
                    },
                ],
                config={
                    "response_mime_type": "application/json",
                    "temperature": 0,
                },
            )
        except Exception as exc:
            raise OrchestratorRequestError(str(exc)) from exc

        try:
            parsed = getattr(response, "parsed", None)
            if parsed is not None:
                if isinstance(parsed, (dict, list)):
                    return self._finalize_response(client, user_request, parsed)
                if isinstance(parsed, str):
                    return self._finalize_response(
                        client, user_request, self._parse_json(parsed)
                    )
                return self._finalize_response(
                    client, user_request, self._parse_json(json.dumps(parsed))
                )

            response_text = getattr(response, "text", "")
            parsed_response = self._parse_json(response_text)
            return self._finalize_response(client, user_request, parsed_response)
        except (json.JSONDecodeError, TypeError, ValidationError) as exc:
            raise OrchestratorResponseError(
                "La reponse Gemini de l'orchestrateur n'est pas un JSON valide."
            ) from exc
        except (
            ImageGenerationConfigError,
            ImageGenerationContextError,
            ImageGenerationPersistenceError,
            ImageGenerationRequestError,
            ImageGenerationRequestValidationError,
            PublicationConfigError,
            PublicationPersistenceError,
            PublicationRequestError,
            PublicationResponseError,
        ) as exc:
            raise OrchestratorProcessingError(str(exc)) from exc
        except Exception as exc:
            raise OrchestratorResponseError(str(exc)) from exc

    def _finalize_response(
        self,
        client: Any | None,
        user_request: str,
        classification_result: dict[str, Any] | list[Any],
    ) -> dict[str, Any]:
        dispatched_result = self._dispatch(classification_result)
        response_payload = self._build_response_payload(
            user_request=user_request,
            classification_result=classification_result,
            dispatched_result=dispatched_result,
        )
        response_payload["message"] = self._generate_explanatory_message(
            client=client,
            user_request=user_request,
            response_payload=response_payload,
        )
        return response_payload

    def _dispatch(self, parsed_response: dict[str, Any] | list[Any]) -> dict[str, Any] | list[Any]:
        if not isinstance(parsed_response, dict):
            return parsed_response

        intent = parsed_response.get("intent")
        if intent == "rapport":
            report_text = parsed_response.get("rapport")
            if not isinstance(report_text, str) or not report_text.strip():
                raise OrchestratorResponseError(
                    "La reponse de l'orchestrateur contient intent=rapport sans champ 'rapport' valide."
                )
            return self.report_service.handle(report_text).model_dump()

        if intent == "publication":
            media_type = str(parsed_response.get("media_type", "")).strip().lower()
            generation_mode = str(parsed_response.get("generation_mode", "")).strip().lower()

            if media_type == "image" and generation_mode in {
                "next_occasion",
                "exam_period",
                "given_occasion",
            }:
                return self.image_generation_service.handle(parsed_response)

            if media_type == "video" and generation_mode == "next_occasion":
                return self.publication_service.handle(parsed_response)

        return parsed_response

    def _build_response_payload(
        self,
        user_request: str,
        classification_result: dict[str, Any] | list[Any],
        dispatched_result: dict[str, Any] | list[Any],
    ) -> dict[str, Any]:
        intent = (
            classification_result.get("intent")
            if isinstance(classification_result, dict)
            else "inconnue"
        )

        status = "classified_only"
        choices: list[str] = []
        missing_fields: list[str] = []

        if intent == "rapport":
            status = "success"
        elif intent == "publication" and isinstance(dispatched_result, dict):
            if dispatched_result.get("status") == "success":
                status = "success"
            else:
                media_type = str(dispatched_result.get("media_type", "")).strip().lower()
                generation_mode = str(dispatched_result.get("generation_mode", "")).strip().lower()

                if media_type not in {"image", "video"} and generation_mode not in {"", "missing"}:
                    status = "missing_information"
                    choices = ["image", "video"]
                    missing_fields = ["media_type"]
                elif media_type not in {"image", "video"} and generation_mode in {"", "missing"}:
                    status = "missing_information"
                    choices = ["image", "video"]
                    missing_fields = ["media_type", "generation_mode"]
                elif media_type in {"image", "video"} and generation_mode in {"", "missing"}:
                    status = "needs_choice"
                    choices = ["next_occasion", "exam_period", "given_occasion"]
                    missing_fields = ["generation_mode"]
                elif media_type == "video" and generation_mode in {"exam_period", "given_occasion"}:
                    status = "classified_only"
                else:
                    status = "classified_only"
        elif intent == "inconnue":
            status = "unsupported_request"

        return {
            "status": status,
            "intent": intent,
            "message": "",
            "data": dispatched_result,
            "choices": choices,
            "missing_fields": missing_fields,
        }

    def _generate_explanatory_message(
        self,
        client: Any | None,
        user_request: str,
        response_payload: dict[str, Any],
    ) -> str:
        if client is None:
            return self._build_fallback_message(response_payload)

        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents=[
                    {
                        "role": "user",
                        "parts": [{"text": ORCHESTRATOR_EXPLANATION_SYSTEM_PROMPT}],
                    },
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": build_orchestrator_explanation_user_prompt(
                                    user_request,
                                    response_payload,
                                )
                            }
                        ],
                    },
                ],
                config={
                    "response_mime_type": "application/json",
                    "temperature": 0,
                },
            )

            parsed = getattr(response, "parsed", None)
            if isinstance(parsed, dict) and isinstance(parsed.get("message"), str):
                return parsed["message"].strip()
            if isinstance(parsed, str):
                payload = self._parse_json(parsed)
                if isinstance(payload, dict) and isinstance(payload.get("message"), str):
                    return payload["message"].strip()

            response_text = getattr(response, "text", "")
            payload = self._parse_json(response_text)
            if isinstance(payload, dict) and isinstance(payload.get("message"), str):
                return payload["message"].strip()
        except Exception:
            pass

        return self._build_fallback_message(response_payload)

    @staticmethod
    def _build_fallback_message(response_payload: dict[str, Any]) -> str:
        status = response_payload.get("status")
        intent = response_payload.get("intent")
        data = response_payload.get("data")

        if status == "success" and intent == "rapport":
            return "Le rapport a ete structure avec succes."
        if status == "success" and intent == "publication" and isinstance(data, dict):
            publication_type = data.get("type_publication", "publication")
            occasion = data.get("occasion")
            if occasion:
                return (
                    f"La publication {publication_type} a ete generee avec succes "
                    f"pour l'occasion {occasion}."
                )
            return f"La publication {publication_type} a ete generee avec succes."
        if status == "needs_choice":
            return (
                "Votre demande concerne une publication, mais il manque le contexte. "
                "Precisez s'il faut viser la prochaine occasion, la periode d'examens, ou une occasion donnee."
            )
        if status == "missing_information":
            return (
                "Votre demande a ete comprise, mais il manque des informations avant de continuer."
            )
        if status == "classified_only" and intent == "publication":
            if isinstance(data, dict):
                media_type = str(data.get("media_type", "")).strip().lower()
                generation_mode = str(data.get("generation_mode", "")).strip().lower()
                if media_type == "video" and generation_mode in {"exam_period", "given_occasion"}:
                    return (
                        "La generation video n'est supportee pour le moment que pour la prochaine occasion."
                    )
            return (
                "La demande a ete comprise comme une publication, mais aucun traitement complet "
                "n'a ete lance pour ce cas."
            )
        if status == "unsupported_request":
            return (
                "Je n'ai pas pu determiner si votre demande concerne une structuration de rapport "
                "ou une publication."
            )
        return "Le traitement a ete realise."

    @staticmethod
    def _parse_json(payload: str) -> dict[str, Any] | list[Any]:
        parsed = json.loads(payload)
        if not isinstance(parsed, (dict, list)):
            raise TypeError("La reponse n'est ni un objet JSON ni une liste JSON.")
        return parsed

    @staticmethod
    def _try_local_publication_classification(user_request: str) -> dict[str, Any] | None:
        normalized = OrchestratorService._normalize_text(user_request)

        publication_keywords = (
            "image",
            "photo",
            "visuel",
            "publication",
            "post",
            "affiche",
            "video",
            "vdo",
            "reel",
            "réel",
        )
        if not any(keyword in normalized for keyword in publication_keywords):
            return None

        media_type = "non_precise"
        if any(keyword in normalized for keyword in ("image", "photo", "visuel", "affiche")):
            media_type = "image"
        elif any(keyword in normalized for keyword in ("video", "vdo", "reel", "réel")):
            media_type = "video"

        generation_mode = "missing"
        if any(
            keyword in normalized
            for keyword in (
                "prochaine occasion",
                "occasion la plus proche",
                "prochaine fete",
                "fete la plus proche",
                "prochain evenement",
            )
        ):
            generation_mode = "next_occasion"
        elif any(keyword in normalized for keyword in ("examen", "examens", "exam", "bac", "revision", "révision")):
            generation_mode = "exam_period"
        else:
            occasion = OrchestratorService._extract_occasion_fragment(user_request)
            if occasion:
                generation_mode = "given_occasion"
            else:
                occasion = None

        return {
            "intent": "publication",
            "media_type": media_type,
            "generation_mode": generation_mode,
            "occasion": occasion if generation_mode == "given_occasion" else None,
            "date": None,
        }

    @staticmethod
    def _extract_occasion_fragment(user_request: str) -> str | None:
        lowered = user_request.strip()
        if not lowered:
            return None

        normalized = OrchestratorService._normalize_text(lowered)
        if "saison en cours" in normalized:
            return "saison en cours"

        for season in ("hiver", "printemps", "ete", "été", "automne"):
            if season in lowered.lower() or season in normalized:
                return season

        patterns = [
            r"\bpour\s+(.+)$",
            r"\boccasion\s+(.+)$",
        ]
        fragment = None
        for pattern in patterns:
            match = re.search(pattern, lowered, flags=re.IGNORECASE)
            if match:
                fragment = match.group(1).strip()
                break

        if fragment is None:
            return None

        fragment = re.sub(r"^[\s:,-]+", "", fragment).strip()
        fragment = re.sub(
            r"^(la|le|les|l'|un|une|du|de la|de l'|des)\s+",
            "",
            fragment,
            flags=re.IGNORECASE,
        ).strip()
        fragment = re.sub(r"[?.!,;:]+$", "", fragment).strip()
        return fragment or None

    @staticmethod
    def _normalize_text(value: str) -> str:
        return (
            str(value)
            .strip()
            .lower()
            .replace("é", "e")
            .replace("è", "e")
            .replace("ê", "e")
            .replace("à", "a")
            .replace("ù", "u")
            .replace("û", "u")
            .replace("î", "i")
            .replace("ï", "i")
            .replace("ô", "o")
        )
