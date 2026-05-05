import json
import re
from typing import Any

from hashem_integration import HashemChatService, HashemIntegrationError
from pydantic import ValidationError

from conversation import ConversationAccessError, ConversationTaskService
from gestionBDD import (
    DatabaseQueryConfigError,
    DatabaseQueryExecutionError,
    DatabaseQueryRequestError,
    DatabaseQueryResponseError,
    DatabaseQueryService,
)
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
from gestionProduit import ProductService, ProductServiceError
from gestionRapport.structuration import StructurationRapportService
from .gemini_client import (
    DEFAULT_MODEL_NAME,
    GeminiClientConfigError,
    generate_content_with_key_rotation,
)
from .hashem_router import HashemRouter, should_try_hashem_fallback
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


class OrchestratorMissingDataError(RuntimeError):
    pass


class OrchestratorProcessingError(RuntimeError):
    pass


class OrchestratorService:
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        hashem_router: HashemRouter | None = None,
        hashem_chat_service: HashemChatService | None = None,
    ) -> None:
        self.model_name = model_name
        self.report_service = StructurationRapportService()
        self.publication_service = PublicationService()
        self.image_generation_service = ImageGenerationService()
        self.database_query_service = DatabaseQueryService(model_name=model_name)
        self.product_service = ProductService()
        self.conversation_task_service = ConversationTaskService()
        self.hashem_router = hashem_router or HashemRouter()
        self.hashem_chat_service = hashem_chat_service or HashemChatService()

    def handle(
        self,
        user_request: str,
        report_text: str | None = None,
        user_id: int | None = None,
        conversation_id: int | None = None,
    ) -> dict[str, Any] | list[Any]:
        local_report_deletion = self._try_local_report_deletion_classification(user_request)
        if local_report_deletion is not None:
            local_report_deletion = self._with_response_language(
                local_report_deletion,
                user_request,
            )
            return self._finalize_response(
                client=None,
                user_request=user_request,
                classification_result=local_report_deletion,
                report_text=report_text,
                user_id=user_id,
                conversation_id=conversation_id,
            )

        local_report_classification = self._try_local_report_classification(user_request)
        if local_report_classification is not None:
            local_report_classification = self._with_response_language(
                local_report_classification,
                user_request,
            )
            return self._finalize_response(
                client=None,
                user_request=user_request,
                classification_result=local_report_classification,
                report_text=report_text,
                user_id=user_id,
                conversation_id=conversation_id,
            )

        if self._looks_like_product_management_request(user_request):
            classification_result = {
                "intent": "produit",
                "action": "product_management",
                "response_language": self._detect_response_language(user_request),
            }
            dispatched_result = self.product_service.handle(
                user_request,
                classification_result,
            )
            response_payload = self._build_response_payload(
                user_request=user_request,
                classification_result=classification_result,
                dispatched_result=dispatched_result,
            )
            response_payload["message"] = str(
                dispatched_result.get("response", "")
            ).strip()
            return response_payload

        try:
            response = generate_content_with_key_rotation(
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
        except GeminiClientConfigError as exc:
            raise OrchestratorConfigError(str(exc)) from exc
        except Exception as exc:
            raise OrchestratorRequestError(str(exc)) from exc

        try:
            parsed = getattr(response, "parsed", None)
            if parsed is not None:
                if isinstance(parsed, (dict, list)):
                    parsed = self._with_response_language(parsed, user_request)
                    parsed = self._normalize_classification_result(parsed, user_request)
                    delegated_response = self._try_hashem_fallback(
                        user_request=user_request,
                        classification_result=parsed,
                        user_id=user_id,
                        conversation_id=conversation_id,
                    )
                    if delegated_response is not None:
                        return delegated_response
                    return self._finalize_response(
                        None,
                        user_request,
                        parsed,
                        report_text=report_text,
                        user_id=user_id,
                        conversation_id=conversation_id,
                    )
                if isinstance(parsed, str):
                    parsed_json = self._normalize_classification_result(
                        self._with_response_language(
                            self._parse_json(parsed),
                            user_request,
                        ),
                        user_request,
                    )
                    delegated_response = self._try_hashem_fallback(
                        user_request=user_request,
                        classification_result=parsed_json,
                        user_id=user_id,
                        conversation_id=conversation_id,
                    )
                    if delegated_response is not None:
                        return delegated_response
                    return self._finalize_response(
                        None,
                        user_request,
                        parsed_json,
                        report_text=report_text,
                        user_id=user_id,
                        conversation_id=conversation_id,
                    )
                parsed_json = self._normalize_classification_result(
                    self._with_response_language(
                        self._parse_json(json.dumps(parsed)),
                        user_request,
                    ),
                    user_request,
                )
                delegated_response = self._try_hashem_fallback(
                    user_request=user_request,
                    classification_result=parsed_json,
                    user_id=user_id,
                    conversation_id=conversation_id,
                )
                if delegated_response is not None:
                    return delegated_response
                return self._finalize_response(
                    None,
                    user_request,
                    parsed_json,
                    report_text=report_text,
                    user_id=user_id,
                    conversation_id=conversation_id,
                )

            response_text = getattr(response, "text", "")
            parsed_response = self._normalize_classification_result(
                self._with_response_language(
                    self._parse_json(response_text),
                    user_request,
                ),
                user_request,
            )
            delegated_response = self._try_hashem_fallback(
                user_request=user_request,
                classification_result=parsed_response,
                user_id=user_id,
                conversation_id=conversation_id,
            )
            if delegated_response is not None:
                return delegated_response
            return self._finalize_response(
                None,
                user_request,
                parsed_response,
                report_text=report_text,
                user_id=user_id,
                conversation_id=conversation_id,
            )
        except (json.JSONDecodeError, TypeError, ValidationError) as exc:
            raise OrchestratorResponseError(
                "La reponse Gemini de l'orchestrateur n'est pas un JSON valide."
            ) from exc
        except (
            ConversationAccessError,
            DatabaseQueryConfigError,
            DatabaseQueryExecutionError,
            DatabaseQueryRequestError,
            DatabaseQueryResponseError,
            ImageGenerationConfigError,
            ImageGenerationContextError,
            ImageGenerationPersistenceError,
            ImageGenerationRequestError,
            ImageGenerationRequestValidationError,
            PublicationConfigError,
            PublicationPersistenceError,
            PublicationRequestError,
            PublicationResponseError,
            ProductServiceError,
            HashemIntegrationError,
        ) as exc:
            if isinstance(exc, ConversationAccessError):
                raise OrchestratorProcessingError(str(exc)) from exc
            if isinstance(exc, DatabaseQueryConfigError):
                raise OrchestratorConfigError(str(exc)) from exc
            if isinstance(exc, DatabaseQueryRequestError):
                raise OrchestratorRequestError(str(exc)) from exc
            if isinstance(exc, DatabaseQueryResponseError):
                raise OrchestratorResponseError(str(exc)) from exc
            if isinstance(exc, HashemIntegrationError):
                raise OrchestratorProcessingError(str(exc)) from exc
            raise OrchestratorProcessingError(str(exc)) from exc
        except OrchestratorMissingDataError:
            raise
        except Exception as exc:
            raise OrchestratorResponseError(str(exc)) from exc

    def _try_hashem_fallback(
        self,
        user_request: str,
        classification_result: dict[str, Any] | list[Any],
        user_id: int | None = None,
        conversation_id: int | None = None,
    ) -> dict[str, Any] | None:
        if not should_try_hashem_fallback(classification_result):
            return None

        decision = self.hashem_router.detect(user_request)
        if not decision.should_route:
            return None

        response_language = (
            self._normalize_response_language(classification_result.get("response_language"))
            if isinstance(classification_result, dict)
            else None
        ) or self._detect_response_language(user_request)

        return self.hashem_chat_service.handle(
            user_request=user_request,
            response_language=response_language,
            user_id=user_id,
            conversation_id=conversation_id,
        )

    def _finalize_response(
        self,
        client: Any | None,
        user_request: str,
        classification_result: dict[str, Any] | list[Any],
        report_text: str | None = None,
        user_id: int | None = None,
        conversation_id: int | None = None,
    ) -> dict[str, Any]:
        if (
            user_id is not None
            and conversation_id is not None
            and isinstance(classification_result, dict)
            and self.conversation_task_service.is_managed(classification_result)
        ):
            return self._finalize_conversation_task_response(
                client=None,
                user_request=user_request,
                classification_result=classification_result,
                report_text=report_text,
                user_id=user_id,
                conversation_id=conversation_id,
            )

        dispatched_result = self._dispatch(
            classification_result,
            user_request=user_request,
            explicit_report_text=report_text,
            user_id=user_id,
            conversation_id=conversation_id,
        )
        response_payload = self._build_response_payload(
            user_request=user_request,
            classification_result=classification_result,
            dispatched_result=dispatched_result,
        )
        response_payload["_user_request"] = user_request
        response_payload["message"] = self._generate_explanatory_message(
            client=None,
            user_request=user_request,
            response_payload=response_payload,
        )
        response_payload["message"] = self._post_process_explanatory_message(
            user_request=user_request,
            response_payload=response_payload,
        )
        response_payload.pop("_user_request", None)
        return response_payload

    def _finalize_conversation_task_response(
        self,
        client: Any | None,
        user_request: str,
        classification_result: dict[str, Any],
        report_text: str | None,
        user_id: int,
        conversation_id: int,
    ) -> dict[str, Any]:
        if (
            classification_result.get("intent") == "rapport"
            and self._infer_action(classification_result) == "structure_report"
            and report_text
        ):
            classification_result = dict(classification_result)
            classification_result["rapport"] = report_text

        merge_result = self.conversation_task_service.merge_task(
            user_id=user_id,
            conversation_id=conversation_id,
            classification=classification_result,
        )

        if not merge_result.is_complete:
            response_payload = {
                "status": self._status_for_incomplete_task(merge_result.classification),
                "intent": merge_result.classification.get("intent"),
                "action": self._infer_action(merge_result.classification),
                "response_language": self._normalize_response_language(
                    merge_result.classification.get("response_language")
                ) or self._detect_response_language(user_request),
                "message": "",
                "data": None,
                "choices": merge_result.choices,
                "missing_fields": merge_result.missing_fields,
                "task": merge_result.task,
            }
            response_payload["message"] = self._generate_explanatory_message(
                client=None,
                user_request=user_request,
                response_payload=response_payload,
            )
            return response_payload

        try:
            dispatched_result = self._dispatch(
                merge_result.classification,
                user_request=user_request,
                explicit_report_text=report_text,
                user_id=user_id,
                conversation_id=conversation_id,
            )
        except Exception:
            self.conversation_task_service.mark_failed(int(merge_result.task["id"]))
            raise

        completed_task = self.conversation_task_service.mark_completed(
            int(merge_result.task["id"])
        )
        response_payload = self._build_response_payload(
            user_request=user_request,
            classification_result=merge_result.classification,
            dispatched_result=dispatched_result,
        )
        response_payload["task"] = completed_task
        response_payload["_user_request"] = user_request
        response_payload["message"] = self._generate_explanatory_message(
            client=None,
            user_request=user_request,
            response_payload=response_payload,
        )
        response_payload["message"] = self._post_process_explanatory_message(
            user_request=user_request,
            response_payload=response_payload,
        )
        response_payload.pop("_user_request", None)
        return response_payload

    def _dispatch(
        self,
        parsed_response: dict[str, Any] | list[Any],
        user_request: str,
        explicit_report_text: str | None = None,
        user_id: int | None = None,
        conversation_id: int | None = None,
    ) -> dict[str, Any] | list[Any]:
        if not isinstance(parsed_response, dict):
            return parsed_response

        intent = parsed_response.get("intent")
        action = self._infer_action(parsed_response)
        if action == "query_database":
            return self.database_query_service.handle(
                user_request,
                parsed_response,
                user_id=user_id,
                conversation_id=conversation_id,
            )

        if intent == "produit":
            return self.product_service.handle(user_request, parsed_response)

        if intent == "rapport":
            if action == "delete_report":
                report_id = parsed_response.get("report_id")
                if report_id is None:
                    return {
                        "status": "missing_information",
                        "missing_fields": ["report_id"],
                        "choices": [],
                        "reason": "L'id du rapport a supprimer est requis.",
                    }
                return self.report_service.delete_report(int(report_id))

            resolved_report_text = self._resolve_report_text(
                user_request=user_request,
                parsed_response=parsed_response,
                explicit_report_text=explicit_report_text,
            )
            return self.report_service.handle(resolved_report_text).model_dump()

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
        response_language = (
            self._normalize_response_language(classification_result.get("response_language"))
            if isinstance(classification_result, dict)
            else self._detect_response_language(user_request)
        )
        if not response_language:
            response_language = self._detect_response_language(user_request)
        action = (
            self._infer_action(classification_result)
            if isinstance(classification_result, dict)
            else ""
        )

        status = "classified_only"
        choices: list[str] = []
        missing_fields: list[str] = []
        data = dispatched_result

        if action == "query_database" and isinstance(dispatched_result, dict):
            status = str(dispatched_result.get("status", "classified_only")).strip() or "classified_only"
            choices = list(dispatched_result.get("choices", []))
            missing_fields = list(dispatched_result.get("missing_fields", []))
            data = {
                key: value
                for key, value in dispatched_result.items()
                if key not in {"status", "choices", "missing_fields"}
            }
        elif action == "delete_report" and isinstance(dispatched_result, dict):
            status = str(dispatched_result.get("status", "classified_only")).strip() or "classified_only"
            choices = list(dispatched_result.get("choices", []))
            missing_fields = list(dispatched_result.get("missing_fields", []))
            data = {
                key: value
                for key, value in dispatched_result.items()
                if key not in {"status", "choices", "missing_fields"}
            }
        elif intent == "rapport":
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
        elif intent == "produit" and isinstance(dispatched_result, dict):
            status = str(dispatched_result.get("status", "success")).strip() or "success"
            data = dispatched_result
        elif intent == "conversation" and action == "query_database" and isinstance(dispatched_result, dict):
            status = str(dispatched_result.get("status", "classified_only")).strip() or "classified_only"
            choices = list(dispatched_result.get("choices", []))
            missing_fields = list(dispatched_result.get("missing_fields", []))
            data = {
                key: value
                for key, value in dispatched_result.items()
                if key not in {"status", "choices", "missing_fields"}
            }
        elif intent == "inconnue":
            status = "unsupported_request"

        return {
            "status": status,
            "intent": intent,
            "action": action,
            "response_language": response_language,
            "message": "",
            "data": data,
            "display": self._build_display_payload(
                user_request=user_request,
                intent=intent,
                action=action,
                data=data,
            ),
            "choices": choices,
            "missing_fields": missing_fields,
        }

    @staticmethod
    def _status_for_incomplete_task(classification_result: dict[str, Any]) -> str:
        intent = str(classification_result.get("intent", "")).strip().lower()
        action = OrchestratorService._infer_action(classification_result)
        if intent == "publication" and action in {"generate_publication", "query_database"}:
            return "needs_choice"
        return "missing_information"

    def _generate_explanatory_message(
        self,
        client: Any | None,
        user_request: str,
        response_payload: dict[str, Any],
    ) -> str:
        if response_payload.get("intent") == "produit":
            data = response_payload.get("data")
            if isinstance(data, dict):
                response_text = data.get("response")
                if isinstance(response_text, str) and response_text.strip():
                    return response_text.strip()

        try:
            if client is not None:
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
                                        response_language=self._resolve_response_language(
                                            user_request,
                                            response_payload,
                                        ),
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
            else:
                response = generate_content_with_key_rotation(
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
                                        response_language=self._resolve_response_language(
                                            user_request,
                                            response_payload,
                                        ),
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

        return self._build_fallback_message(
            response_payload,
            language=self._resolve_response_language(user_request, response_payload),
        )

    @staticmethod
    def _build_fallback_message(
        response_payload: dict[str, Any],
        language: str | None = None,
    ) -> str:
        status = response_payload.get("status")
        intent = response_payload.get("intent")
        action = response_payload.get("action")
        data = response_payload.get("data")
        is_english = language == "English"
        is_arabic = language == "Arabic"

        if status == "success" and action == "query_database":
            return OrchestratorService._build_query_database_fallback_message(
                data,
                display=response_payload.get("display"),
                language=language,
                user_request=str(response_payload.get("_user_request", "")),
            )
        if status == "success" and action == "delete_report" and isinstance(data, dict):
            report_id = data.get("report_id")
            if is_arabic:
                return f"تم حذف التقرير رقم {report_id} بنجاح."
            if is_english:
                return f"The report with id {report_id} was deleted successfully."
            return f"Le rapport avec l'id {report_id} a ete supprime avec succes."
        if status == "success" and intent == "rapport":
            if is_arabic:
                return "تمت هيكلة التقرير بنجاح."
            if is_english:
                return "The report was structured successfully."
            return "Le rapport a ete structure avec succes."
        if status == "not_found" and action == "delete_report" and isinstance(data, dict):
            report_id = data.get("report_id")
            if is_arabic:
                return f"لم يتم العثور على تقرير بالمعرف {report_id}."
            if is_english:
                return f"No report was found with id {report_id}."
            return f"Aucun rapport n'a ete trouve avec l'id {report_id}."
        if status == "success" and intent == "publication" and isinstance(data, dict):
            publication_type = data.get("type_publication", "publication")
            occasion = data.get("occasion")
            if is_arabic:
                if occasion:
                    return f"تم إنشاء منشور {publication_type} بنجاح للمناسبة {occasion}."
                return f"تم إنشاء منشور {publication_type} بنجاح."
            if is_english:
                if occasion:
                    return (
                        f"The {publication_type} publication was generated successfully "
                        f"for {occasion}."
                    )
                return f"The {publication_type} publication was generated successfully."
            if occasion:
                return (
                    f"La publication {publication_type} a ete generee avec succes "
                    f"pour l'occasion {occasion}."
                )
            return f"La publication {publication_type} a ete generee avec succes."
        if status == "success" and intent == "produit" and isinstance(data, dict):
            response_text = data.get("response")
            if isinstance(response_text, str) and response_text.strip():
                return response_text.strip()
            if is_arabic:
                return "تم إنجاز تحليل المنتجات بنجاح."
            if is_english:
                return "The product analysis was completed successfully."
            return "L'analyse produit a ete realisee avec succes."
        if status == "needs_choice":
            if action == "query_database" and intent == "publication":
                if is_arabic:
                    return (
                        "طلبك يتعلق بقاعدة بيانات المنشورات. "
                        "حدد هل تريد الاستعلام عن الصور أم الفيديوهات أم الاثنين معا."
                    )
                return (
                    "Votre demande concerne la base des publications. "
                    "Precisez si vous voulez interroger les images, les videos, ou les deux."
                )
            if is_arabic:
                return (
                    "طلبك يتعلق بمنشور، لكن السياق غير مكتمل. "
                    "حدد هل تريد المناسبة القادمة، أو فترة الامتحانات، أو مناسبة معينة."
                )
            return (
                "Votre demande concerne une publication, mais il manque le contexte. "
                "Precisez s'il faut viser la prochaine occasion, la periode d'examens, ou une occasion donnee."
            )
        if status == "query_rejected" and isinstance(data, dict):
            reason = str(data.get("reason", "")).strip()
            if reason:
                if is_arabic:
                    return f"تم رفض استعلام قاعدة البيانات: {reason}"
                if is_english:
                    return f"The database query was rejected: {reason}"
                return f"La requete BDD a ete refusee: {reason}"
            if is_arabic:
                return "تعذر تنفيذ استعلام قاعدة البيانات بشكل آمن."
            if is_english:
                return "The database query could not be executed safely."
            return "La requete BDD n'a pas pu etre executee de maniere sure."
        if status == "database_unavailable":
            reason = ""
            details = ""
            if isinstance(data, dict):
                reason = str(data.get("reason", "")).strip()
                details = str(data.get("details", "")).strip()
            if reason:
                return reason
            if details:
                if is_arabic:
                    return f"فشل تنفيذ SQL: {details}"
                if is_english:
                    return f"SQL execution failed: {details}"
                return f"Echec d'execution SQL: {details}"
            if is_arabic:
                return (
                    "قاعدة البيانات غير متاحة. تحقق من أن خادم قاعدة البيانات يعمل "
                    "ومن صحة إعدادات الاتصال."
                )
            if is_english:
                return (
                    "The database is not accessible. Check that the database server "
                    "is running and that the connection configuration is correct."
                )
            return (
                "La base de donnees n'est pas accessible. Verifiez que le serveur "
                "BDD est demarre et que la configuration de connexion est correcte."
            )
        if status == "missing_information":
            if action == "delete_report":
                if is_arabic:
                    return "معرف التقرير المراد حذفه مطلوب."
                if is_english:
                    return "The report id to delete is required."
                return "L'id du rapport a supprimer est requis."
            if is_arabic:
                return "تم فهم الطلب، لكن هناك معلومات ناقصة قبل المتابعة."
            if is_english:
                return (
                    "The request was understood, but more information is needed before continuing."
                )
            return (
                "Votre demande a ete comprise, mais il manque des informations avant de continuer."
            )
        if status == "classified_only" and intent == "publication":
            if isinstance(data, dict):
                media_type = str(data.get("media_type", "")).strip().lower()
                generation_mode = str(data.get("generation_mode", "")).strip().lower()
                if media_type == "video" and generation_mode in {"exam_period", "given_occasion"}:
                    if is_arabic:
                        return "إنشاء الفيديو مدعوم حاليا للمناسبة القادمة فقط."
                    return (
                        "La generation video n'est supportee pour le moment que pour la prochaine occasion."
                    )
            if is_arabic:
                return (
                    "تم فهم الطلب كمنشور، لكن لم يتم تشغيل معالجة كاملة لهذه الحالة."
                )
            return (
                "La demande a ete comprise comme une publication, mais aucun traitement complet "
                "n'a ete lance pour ce cas."
            )
        if status == "unsupported_request":
            if is_arabic:
                return (
                    "لم أتمكن من تحديد ما إذا كان طلبك يتعلق بهيكلة تقرير "
                    "أو بإنشاء منشور."
                )
            if is_english:
                return (
                    "I could not determine whether your request is about report structuring "
                    "or publication generation."
                )
            return (
                "Je n'ai pas pu determiner si votre demande concerne une structuration de rapport "
                "ou une publication."
            )
        if is_arabic:
            return "تمت معالجة الطلب."
        if is_english:
            return "The processing was completed."
        return "Le traitement a ete realise."

    @staticmethod
    def _build_query_database_fallback_message(
        data: Any,
        display: Any = None,
        language: str | None = None,
        user_request: str = "",
    ) -> str:
        is_english = language == "English"
        is_arabic = language == "Arabic"
        if not isinstance(data, dict):
            if is_arabic:
                return "تم تنفيذ استعلام قاعدة البيانات بنجاح."
            if is_english:
                return "The database query was executed successfully."
            return "La requete sur la base de donnees a ete executee avec succes."

        row_count = data.get("row_count")
        if row_count == 0:
            if is_arabic:
                return "## نتائج قاعدة البيانات\n\nلم يتم العثور على أي نتيجة في قاعدة البيانات."
            if is_english:
                return "## Database Results\n\nNo result was found in the database."
            return "## Resultats BDD\n\nAucun resultat n'a ete trouve dans la base de donnees."

        rows = data.get("rows")
        if not isinstance(row_count, int):
            if is_arabic:
                return "تم تنفيذ استعلام قاعدة البيانات بنجاح."
            if is_english:
                return "The database query was executed successfully."
            return "La requete sur la base de donnees a ete executee avec succes."

        if isinstance(display, dict) and display.get("type") == "table":
            title = str(display.get("title", "")).strip()
            if is_arabic:
                heading = title or "نتائج قاعدة البيانات"
                suffix = (
                    "\n\nيتم عرض جزء فقط من النتائج في الجدول."
                    if bool(data.get("truncated", False))
                    else ""
                )
                return f"## {heading}\n\nوجدت {row_count} نتيجة في قاعدة البيانات.{suffix}"
            if is_english:
                heading = title or "Database Results"
                suffix = (
                    "\n\nOnly part of the results is shown in the table."
                    if bool(data.get("truncated", False))
                    else ""
                )
                return f"## {heading}\n\nI found {row_count} result(s) in the database.{suffix}"

            heading = title or "Resultats BDD"
            suffix = (
                "\n\nSeule une partie des resultats est affichee dans le tableau."
                if bool(data.get("truncated", False))
                else ""
            )
            return f"## {heading}\n\nJ'ai trouve {row_count} resultat(s) dans la base de donnees.{suffix}"

        if not isinstance(rows, list) or not rows:
            if is_arabic:
                return f"وجدت {row_count} نتيجة في قاعدة البيانات."
            if is_english:
                return f"I found {row_count} result(s) in the database."
            return f"J'ai trouve {row_count} resultat(s) dans la base de donnees."

        displayed_rows = rows[:5]
        rendered_rows = [
            OrchestratorService._render_row_for_message(row, user_request=user_request)
            for row in displayed_rows
            if isinstance(row, dict)
        ]
        rendered_rows = [row for row in rendered_rows if row]
        if not rendered_rows:
            if is_arabic:
                return f"وجدت {row_count} نتيجة في قاعدة البيانات."
            if is_english:
                return f"I found {row_count} result(s) in the database."
            return f"J'ai trouve {row_count} resultat(s) dans la base de donnees."

        intro = (
            f"وجدت {row_count} نتيجة في قاعدة البيانات:"
            if is_arabic
            else (
                f"I found {row_count} result(s) in the database:"
                if is_english
                else f"J'ai trouve {row_count} resultat(s) dans la base de donnees :"
            )
        )
        body = "\n".join(f"- {row}" for row in rendered_rows)
        if bool(data.get("truncated", False)) or row_count > len(displayed_rows):
            if is_arabic:
                return f"{intro}\n{body}\n- ... نتائج أخرى غير معروضة"
            if is_english:
                return f"{intro}\n{body}\n- ... other results not displayed"
            return f"{intro}\n{body}\n- ... autres resultats non affiches"
        return f"{intro}\n{body}"

    @staticmethod
    def _render_row_for_message(row: dict[str, Any], user_request: str = "") -> str:
        if (
            not OrchestratorService._is_explicit_structured_report_request(user_request)
            and any(key in row for key in ("raw_text", "text_corrige"))
        ):
            raw_text = str(row.get("raw_text", "")).strip()
            if raw_text:
                return raw_text
            corrected_text = str(row.get("text_corrige", "")).strip()
            if corrected_text:
                return corrected_text

        preferred_keys = (
            "id",
            "text_corrige",
            "mouvement",
            "potentiel",
            "conseil",
            "occasion",
            "generation_mode",
            "produit",
            "description_post",
            "date_publication",
            "created_at",
        )

        parts: list[str] = []
        used_keys: set[str] = set()
        for key in preferred_keys:
            value = row.get(key)
            if value in (None, "", [], {}):
                continue
            rendered_value = str(value).strip()
            if not rendered_value:
                continue
            parts.append(f"{key}={rendered_value}")
            used_keys.add(key)
            if len(parts) >= 4:
                break

        if not parts:
            for key, value in row.items():
                if key in used_keys or value in (None, "", [], {}):
                    continue
                rendered_value = str(value).strip()
                if not rendered_value:
                    continue
                parts.append(f"{key}={rendered_value}")
                if len(parts) >= 4:
                    break

        return ", ".join(parts)

    @classmethod
    def _build_display_payload(
        cls,
        user_request: str,
        intent: Any,
        action: Any,
        data: Any,
    ) -> dict[str, Any] | None:
        if str(action).strip().lower() != "query_database":
            return None
        if not isinstance(data, dict):
            return None

        rows = data.get("rows")
        if not isinstance(rows, list) or not rows:
            return None

        row_dicts = [row for row in rows if isinstance(row, dict)]
        if not row_dicts:
            return None

        tables_used = data.get("tables_used")
        table_name = (
            str(tables_used[0]).strip().lower()
            if isinstance(tables_used, list) and tables_used
            else str(intent).strip().lower()
        )
        if (
            table_name == "structured_reports"
            and not cls._is_explicit_structured_report_request(user_request)
        ):
            return None

        column_keys = cls._select_display_columns(
            user_request=user_request,
            table_name=table_name,
            data_columns=data.get("columns"),
            rows=row_dicts,
        )
        if not column_keys:
            return None
        if cls._should_prefer_text_list(user_request=user_request, column_keys=column_keys):
            return None

        return {
            "type": "table",
            "title": cls._build_display_title(user_request, table_name),
            "columns": [
                {"key": key, "label": cls._display_label_for_column(key)}
                for key in column_keys
            ],
            "rows": [
                {key: cls._serialize_display_value(row.get(key)) for key in column_keys}
                for row in row_dicts
            ],
            "truncated": bool(data.get("truncated", False)),
            "row_count": int(data.get("row_count", len(row_dicts))),
        }

    @classmethod
    def _select_display_columns(
        cls,
        user_request: str,
        table_name: str,
        data_columns: Any,
        rows: list[dict[str, Any]],
    ) -> list[str]:
        available_columns: list[str] = []
        if isinstance(data_columns, list):
            available_columns = [
                str(column).strip()
                for column in data_columns
                if isinstance(column, str) and str(column).strip()
            ]
        if not available_columns and rows:
            available_columns = [str(key) for key in rows[0].keys()]

        preferred_by_table: dict[str, tuple[str, ...]] = {
            "tasks": ("id", "intent", "action", "status", "created_at", "updated_at"),
            "messages": ("id", "role", "text", "created_at"),
            "conversations": ("id", "title", "created_at", "updated_at"),
            "structured_reports": (
                "id",
                "raw_text",
                "text_corrige",
                "mouvement",
                "potentiel",
                "conseil",
                "emplacement_proximite",
                "emplacement_qualite",
                "personnel_attitude",
                "mise_en_place",
                "invitations",
                "stock_disponibilite",
                "type_pharmacie",
                "eligibilite_animation",
                "aucun_point_fort",
                "created_at",
            ),
            "generated_images": ("id", "produit", "occasion", "generation_mode", "date_publication", "created_at"),
            "generated_videos": ("id", "produit", "occasion", "generation_mode", "date_publication", "created_at"),
            "conversation": ("id", "intent", "action", "status", "created_at"),
        }
        preferred_columns = preferred_by_table.get(table_name, ())

        selected = [column for column in preferred_columns if column in available_columns]
        if not selected:
            selected = [
                column
                for column in available_columns
                if column not in {"sql", "infos_json", "missing_fields_json"}
            ]
        if (
            table_name == "structured_reports"
            and cls._is_explicit_structured_report_request(user_request)
        ):
            return selected
        return selected[:6]

    @classmethod
    def _should_prefer_text_list(
        cls,
        user_request: str,
        column_keys: list[str],
    ) -> bool:
        if not column_keys:
            return False

        normalized_request = cls._normalize_text(user_request)
        wants_textual_content = any(
            keyword in normalized_request
            for keyword in (
                "texte",
                "textes",
                "raw text",
                "contenu",
                "contenus",
                "phrase",
                "phrases",
                "rapport contenant",
                "rapports contenant",
            )
        )
        if not wants_textual_content:
            return False

        normalized_columns = [cls._normalize_text(column) for column in column_keys]
        text_like_columns = {
            "raw_text",
            "raw text",
            "text",
            "texte",
            "message",
            "content",
            "contenu",
            "description",
            "description_post",
            "text_corrige",
            "rapport",
            "report_text",
        }
        non_text_columns = [
            column for column in normalized_columns if column not in text_like_columns
        ]

        return len(non_text_columns) == 0

    @classmethod
    def _is_explicit_structured_report_request(cls, user_request: str) -> bool:
        normalized_request = cls._normalize_text(user_request)
        return any(
            keyword in normalized_request
            for keyword in (
                "structuration",
                "structure du rapport",
                "structure des rapports",
                "rapport structure",
                "rapports structures",
                "details du rapport",
                "details des rapports",
                "champs du rapport",
                "champs des rapports",
                "afficher la structure",
                "affiche la structure",
            )
        )

    @classmethod
    def _post_process_explanatory_message(
        cls,
        user_request: str,
        response_payload: dict[str, Any],
    ) -> str:
        message = str(response_payload.get("message", "")).strip()
        if not message:
            return message

        response_payload["_user_request"] = user_request
        display = response_payload.get("display")
        if isinstance(display, dict) and display.get("type") == "table":
            message = cls._strip_markdown_tables(message)
        return message.strip()

    @staticmethod
    def _strip_markdown_tables(message: str) -> str:
        lines = message.splitlines()
        cleaned_lines: list[str] = []
        in_table = False

        for line in lines:
            stripped = line.strip()
            is_table_line = "|" in stripped
            is_separator_line = bool(re.fullmatch(r"\|?[\s:-]+\|[\s|:-]*", stripped))

            if is_table_line or is_separator_line:
                in_table = True
                continue

            if in_table and not stripped:
                continue

            in_table = False
            cleaned_lines.append(line)

        cleaned_message = "\n".join(cleaned_lines)
        cleaned_message = re.sub(r"\n{3,}", "\n\n", cleaned_message)
        return cleaned_message.strip()

    @staticmethod
    def _display_label_for_column(column: str) -> str:
        # Display labels are mostly used by explicit tables; free-text answers are
        # handled by the explanatory message/fallback language logic.
        labels = {
            "id": "Tache",
            "intent": "Type",
            "action": "Action",
            "status": "Statut",
            "created_at": "Date",
            "updated_at": "Mise a jour",
            "role": "Role",
            "text": "Message",
            "title": "Titre",
            "produit": "Produit",
            "occasion": "Occasion",
            "generation_mode": "Mode",
            "date_publication": "Date publication",
            "mouvement": "Mouvement",
            "potentiel": "Potentiel",
            "conseil": "Conseil",
        }
        return labels.get(column, column.replace("_", " ").capitalize())

    @staticmethod
    def _build_display_title(user_request: str, table_name: str) -> str:
        normalized = OrchestratorService._normalize_text(user_request)
        language = OrchestratorService._detect_response_language(user_request)
        if language == "Arabic":
            titles = {
                "tasks": "قائمة مهامك",
                "messages": "سجل الرسائل",
                "conversations": "قائمة المحادثات",
                "structured_reports": "التقارير الموجودة",
                "generated_images": "الصور الموجودة",
                "generated_videos": "الفيديوهات الموجودة",
                "conversation": "النتائج",
            }
            return titles.get(table_name, "النتائج")
        if language == "English":
            titles = {
                "tasks": "Your tasks",
                "messages": "Message history",
                "conversations": "Your conversations",
                "structured_reports": "Reports found",
                "generated_images": "Images found",
                "generated_videos": "Videos found",
                "conversation": "Results",
            }
            return titles.get(table_name, "Results")

        if "tableau" in normalized or "table" in normalized:
            if table_name == "tasks":
                return "Liste de vos taches"
            if table_name == "messages":
                return "Liste de vos messages"

        titles = {
            "tasks": "Liste de vos taches",
            "messages": "Historique des messages",
            "conversations": "Liste de vos discussions",
            "structured_reports": "Rapports trouves",
            "generated_images": "Images trouvees",
            "generated_videos": "Videos trouvees",
            "conversation": "Resultats",
        }
        return titles.get(table_name, "Resultats")

    @staticmethod
    def _serialize_display_value(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, (dict, list)):
            try:
                return json.dumps(value, ensure_ascii=False)
            except TypeError:
                return str(value)
        return str(value)

    @classmethod
    def _resolve_report_text(
        cls,
        user_request: str,
        parsed_response: dict[str, Any],
        explicit_report_text: str | None = None,
    ) -> str:
        if isinstance(explicit_report_text, str) and explicit_report_text.strip():
            return explicit_report_text.strip()

        inline_report_text = cls._extract_inline_report_text(user_request)
        if inline_report_text:
            return inline_report_text

        report_text = parsed_response.get("rapport")
        if isinstance(report_text, str) and report_text.strip():
            cleaned_report_text = report_text.strip()
            if not cls._looks_like_report_request_without_content(
                user_request=user_request,
                report_text=cleaned_report_text,
            ):
                return cleaned_report_text

        raise OrchestratorMissingDataError(
            "Des donnees sont manquantes: le texte du rapport n'a pas ete fourni."
        )

    @classmethod
    def _extract_inline_report_text(cls, user_request: str) -> str | None:
        request_text = str(user_request).strip()
        if not request_text:
            return None

        normalized_request = cls._normalize_text(request_text)
        if "rapport" not in normalized_request:
            return None

        for separator in ("\n\n", "\r\n\r\n", "\n", "\r\n", ":"):
            if separator not in request_text:
                continue
            suffix = request_text.split(separator, 1)[1].strip()
            if cls._is_report_content_candidate(suffix):
                return suffix

        trailing_fragment_match = re.search(
            r"\brapport\b[\s:,-]*(.+)$",
            request_text,
            flags=re.IGNORECASE,
        )
        if trailing_fragment_match:
            suffix = trailing_fragment_match.group(1).strip()
            if cls._is_report_content_candidate(suffix):
                return suffix

        return None

    @classmethod
    def _looks_like_report_request_without_content(
        cls,
        user_request: str,
        report_text: str,
    ) -> bool:
        normalized_request = cls._normalize_text(user_request)
        normalized_report = cls._normalize_text(report_text)

        if normalized_report != normalized_request:
            return False

        has_action = re.search(
            r"\b(structurer|structure|analyser|analyse|corriger|corrige|traiter|traite|resumer|resume)\b",
            normalized_request,
        )
        has_report_reference = re.search(
            r"\b(ce|mon|le|du)\s+rapport\b|\brapport\b",
            normalized_request,
        )
        return bool(has_action and has_report_reference)

    @classmethod
    def _is_report_content_candidate(cls, value: str) -> bool:
        candidate = str(value).strip()
        if len(candidate) < 8:
            return False

        normalized_candidate = cls._normalize_text(candidate)
        request_patterns = (
            r"^\b(peux[- ]?tu|pouvez[- ]?vous|merci de|stp|svp)\b",
            r"\b(structurer|structure|analyser|analyse|corriger|corrige|traiter|traite|resumer|resume)\b",
        )
        if any(re.search(pattern, normalized_candidate) for pattern in request_patterns):
            return False

        report_field_keywords = (
            "mouvement",
            "potentiel",
            "potential",
            "conseil",
            "advice",
            "emplacement",
            "location",
            "proximite",
            "proximity",
            "personnel",
            "staff",
            "attitude",
            "stock",
            "invitation",
            "mise en place",
            "mise_en_place",
            "animation",
            "pharmacie",
            "pharmacy",
            "point fort",
            "strength",
            "welcome",
            "reception",
        )
        if any(keyword in normalized_candidate for keyword in report_field_keywords):
            return True

        return bool(
            re.search(
                r"\b(est|sont|is|are|very|tres|fort|forte|strong|weak|faible|moyen|moyenne|medium|low|high)\b",
                normalized_candidate,
            )
        )

    @staticmethod
    def _parse_json(payload: str) -> dict[str, Any] | list[Any]:
        parsed = json.loads(payload)
        if not isinstance(parsed, (dict, list)):
            raise TypeError("La reponse n'est ni un objet JSON ni une liste JSON.")
        return parsed

    @staticmethod
    def _try_local_product_classification(user_request: str) -> dict[str, Any] | None:
        normalized = OrchestratorService._normalize_text(user_request)
        if not normalized:
            return None

        if any(keyword in normalized for keyword in ("rapport", "report", "publication", "post", "image", "video")):
            return None

        action_keywords: tuple[tuple[str, tuple[str, ...]], ...] = (
            (
                "stock",
                (
                    "rupture",
                    "stock",
                    "disponib",
                    "indisponible",
                    "approvisionnement",
                    "manque",
                    "out of stock",
                    "reapprovisionnement",
                ),
            ),
            (
                "clinical",
                (
                    "indication",
                    "composition",
                    "ingredient",
                    "actif",
                    "forme",
                    "comprime",
                    "gelule",
                    "therapeutique",
                    "posologie",
                    "contre-indication",
                ),
            ),
            (
                "commercial",
                (
                    "prix",
                    "promo",
                    "remise",
                    "tarif",
                    "cout",
                    "budget",
                    "discount",
                    "promotion",
                    "competitif",
                    "positionnement prix",
                    "marge",
                ),
            ),
            (
                "product_profile",
                (
                    "profil",
                    "fiche",
                    "analyse",
                    "detail",
                    "ce produit",
                    "parle-moi de",
                    "dis-moi",
                    "approfondis",
                    "zoom sur",
                    "focus sur",
                ),
            ),
            (
                "gamme",
                (
                    "gamme",
                    "ligne",
                    "famille",
                    "portfolio",
                    "collection",
                    "range",
                ),
            ),
            (
                "risk",
                (
                    "risque",
                    "danger",
                    "alerte",
                    "menace",
                    "surveiller",
                    "declin",
                    "decline",
                    "probleme",
                    "faiblesse",
                    "vulnerable",
                    "critique",
                    "substitution",
                    "concurrent fort",
                    "perte",
                ),
            ),
            (
                "opportunity",
                (
                    "opportunite",
                    "opportunites",
                    "opportuniter",
                    "meilleur",
                    "meilleure",
                    "potentiel",
                    "top",
                    "performer",
                    "a investir",
                    "developper",
                    "locomotive",
                    "fort momentum",
                    "investissement",
                    "prioriser",
                    "priorite",
                    "croissance forte",
                    "dynamique forte",
                    "best",
                    "opportunity",
                    "opportunities",
                    "potential",
                    "top performer",
                ),
            ),
            (
                "momentum",
                (
                    "momentum",
                    "velocite",
                    "acceleration",
                    "moteur",
                    "locomotive",
                    "vitesse",
                ),
            ),
            (
                "trend",
                (
                    "tendance",
                    "trend",
                    "croissance",
                    "marche",
                    "dynamique",
                    "evolution",
                    "secteur",
                    "categorie",
                    "emergent",
                ),
            ),
            (
                "comparison",
                (
                    "compare",
                    "comparaison",
                    "versus",
                    " vs ",
                    "difference entre",
                    "lequel est",
                    "meilleur entre",
                ),
            ),
        )

        for action, keywords in action_keywords:
            if any(keyword in normalized for keyword in keywords):
                return {
                    "intent": "produit",
                    "action": action,
                    "user_question": user_request.strip(),
                }

        product_markers = ("produit", "produits", "product", "products", "catalogue", "portefeuille")
        if any(keyword in normalized for keyword in product_markers):
            return {
                "intent": "produit",
                "action": "strategic",
                "user_question": user_request.strip(),
            }

        return None

    @staticmethod
    def _try_local_conversation_database_classification(user_request: str) -> dict[str, Any] | None:
        normalized = OrchestratorService._normalize_text(user_request)
        conversation_keywords = (
            "discussion",
            "discussions",
            "conversation",
            "conversations",
            "message",
            "messages",
            "tache",
            "taches",
            "task",
            "tasks",
        )
        query_keywords = (
            "combien",
            "liste",
            "lister",
            "quels",
            "quelles",
            "montre",
            "affiche",
            "donne",
            "historique",
            "dernier",
            "derniere",
            "mes",
            "my",
            "show",
            "list",
            "count",
            "how many",
        )
        if not any(keyword in normalized for keyword in conversation_keywords):
            return None
        if not any(keyword in normalized for keyword in query_keywords):
            return None

        has_messages = "message" in normalized or "messages" in normalized
        has_tasks = any(keyword in normalized for keyword in ("tache", "taches", "task", "tasks"))
        has_conversations = any(keyword in normalized for keyword in ("discussion", "discussions", "conversation", "conversations"))

        if has_messages and has_tasks:
            scope = "all"
        elif has_messages:
            scope = "messages"
        elif has_tasks:
            scope = "tasks"
        else:
            scope = "conversations"

        return {
            "intent": "conversation",
            "action": "query_database",
            "conversation_scope": scope,
            "user_question": user_request.strip(),
            "query_kind": OrchestratorService._infer_query_kind(normalized),
        }

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

        if OrchestratorService._looks_like_publication_database_query(normalized):
            media_scope = OrchestratorService._resolve_publication_media_scope(normalized)
            db_scope_tables: list[str] = []
            if media_scope == "image":
                db_scope_tables = ["generated_images"]
            elif media_scope == "video":
                db_scope_tables = ["generated_videos"]
            elif media_scope == "both":
                db_scope_tables = ["generated_images", "generated_videos"]

            return {
                "intent": "publication",
                "action": "query_database",
                "response_language": OrchestratorService._detect_response_language(user_request),
                "media_scope": media_scope,
                "db_scope": {"tables": db_scope_tables},
                "user_question": user_request.strip(),
                "query_kind": OrchestratorService._infer_query_kind(normalized),
            }

        media_type = "non_precise"
        if any(keyword in normalized for keyword in ("image", "photo", "visuel", "affiche")):
            media_type = "image"
        elif any(keyword in normalized for keyword in ("video", "vdo", "reel", "réel")):
            media_type = "video"

        generation_mode = "missing"
        if OrchestratorService._looks_like_next_occasion_request(normalized):
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
            "action": "generate_publication",
            "response_language": OrchestratorService._detect_response_language(user_request),
            "media_type": media_type,
            "generation_mode": generation_mode,
            "occasion": occasion if generation_mode == "given_occasion" else None,
            "date": None,
        }

    @staticmethod
    def _try_local_report_classification(user_request: str) -> dict[str, Any] | None:
        normalized = OrchestratorService._normalize_text(user_request)
        has_report_reference = (
            "rapport" in normalized
            or "report" in normalized
            or any(keyword in normalized for keyword in ("تقرير", "تقارير", "التقرير", "التقارير"))
        )
        if not has_report_reference:
            return None

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
            "rÃ©el",
        )
        if any(keyword in normalized for keyword in publication_keywords):
            return None

        if OrchestratorService._looks_like_report_creation_request(normalized):
            return {
                "intent": "rapport",
                "action": "structure_report",
                "response_language": OrchestratorService._detect_response_language(user_request),
                "rapport": OrchestratorService._extract_inline_report_text(user_request),
            }

        if OrchestratorService._looks_like_report_database_query(normalized):
            return {
                "intent": "rapport",
                "action": "query_database",
                "response_language": OrchestratorService._detect_response_language(user_request),
                "db_scope": {"tables": ["structured_reports"]},
                "user_question": user_request.strip(),
                "query_kind": OrchestratorService._infer_query_kind(normalized),
            }

        has_report_action = re.search(
            r"\b(structurer|structure|analyser|analyse|corriger|corrige|traiter|traite|resumer|resume)\b",
            normalized,
        )
        if not has_report_action:
            return None

        return {
            "intent": "rapport",
            "action": "structure_report",
            "response_language": OrchestratorService._detect_response_language(user_request),
            "rapport": None,
        }

    @staticmethod
    def _try_local_report_deletion_classification(user_request: str) -> dict[str, Any] | None:
        normalized = OrchestratorService._normalize_text(user_request)
        if "rapport" not in normalized and "report" not in normalized:
            return None

        has_delete_action = bool(
            re.search(
                r"\b(delete|remove|supprimer|supprime|supprimez|effacer|efface|effacez)\b",
                normalized,
            )
        )
        if not has_delete_action:
            return None

        report_id = OrchestratorService._extract_report_identifier(user_request)
        return {
            "intent": "rapport",
            "action": "delete_report",
            "response_language": OrchestratorService._detect_response_language(user_request),
            "report_id": report_id,
        }

    @staticmethod
    def _extract_report_identifier(user_request: str) -> int | None:
        request_text = str(user_request).strip()
        if not request_text:
            return None

        patterns = (
            r"\b(?:id|identifiant)\s*(?:=|:)?\s*(\d+)\b",
            r"\brapport\s+(?:numero|n°|num(?:ero)?|#)?\s*(\d+)\b",
            r"\breport\s+(?:number|#)?\s*(\d+)\b",
        )
        for pattern in patterns:
            match = re.search(pattern, request_text, flags=re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except (TypeError, ValueError):
                    return None

        return None

    @staticmethod
    def _looks_like_report_creation_request(normalized: str) -> bool:
        has_report = "rapport" in normalized or "report" in normalized
        has_write_action = bool(
            re.search(
                r"\b(add|save|insert|create|store|record|ajoute|ajouter|enregistre|enregistrer|sauvegarde|sauvegarder)\b",
                normalized,
            )
        )
        has_structuring_action = bool(
            re.search(
                r"\b(structurer|structure|analyser|analyse|corriger|corrige|traiter|traite|resumer|resume)\b",
                normalized,
            )
        )
        if not has_report or (not has_write_action and not has_structuring_action):
            return False

        return ":" in normalized or bool(
            re.search(
                r"\b(is|are|est|sont|weak|strong|medium|low|high|faible|fort|forte|moyen|moyenne|potentiel|personnel|emplacement|stock|conseil)\b",
                normalized,
            )
        )

    @staticmethod
    def _infer_action(classification_result: dict[str, Any]) -> str:
        action = str(classification_result.get("action", "")).strip().lower()
        if action:
            return action

        if classification_result.get("db_scope"):
            return "query_database"
        if "media_scope" in classification_result and "generation_mode" not in classification_result:
            return "query_database"

        intent = str(classification_result.get("intent", "")).strip().lower()
        if intent == "rapport":
            return "structure_report"
        if intent == "publication":
            return "generate_publication"
        if intent == "produit":
            return "product_query"
        return ""

    @staticmethod
    def _looks_like_product_management_request(user_request: str) -> bool:
        normalized = user_request.strip().lower()
        patterns = (
            "product manager",
            "product management",
            "gestion de produit",
            "gestion produit",
            "roadmap",
            "mvp",
            "backlog",
            "user stories",
            "user story",
        )
        return any(pattern in normalized for pattern in patterns)

    @staticmethod
    def _looks_like_report_database_query(normalized: str) -> bool:
        if re.search(
            r"\b(structurer|structure|analyser|analyse|corriger|corrige|traiter|traite|resumer|resume)\b",
            normalized,
        ):
            return False

        explicit_db_keywords = (
            "bdd",
            "base de donnees",
            "base de donnee",
            "database",
            "sql",
            "table structured_reports",
        )
        if any(keyword in normalized for keyword in explicit_db_keywords):
            return True

        if any(keyword in normalized for keyword in ("كل التقارير", "جميع التقارير", "اعطني التقارير", "اعطني كل التقارير", "قائمة التقارير")):
            return True

        if re.search(
            r"\b(give|list|show|get|display|fetch)\b.*\b(all|existing|exist|reports?|rapports?)\b",
            normalized,
        ):
            return True

        if re.search(
            r"\b(all|existing|exist)\b.*\b(reports?|rapports?)\b",
            normalized,
        ):
            return True

        if re.search(
            r"\b(i\s+want|want|give|show|list|je\s+veux|veux|donne|montre|affiche)\b.*\b(reports?|rapports?)\b",
            normalized,
        ):
            return True

        return bool(
            re.search(
                r"\b(combien|liste|lister|quels|quelles|montre|affiche|donne)\b.*\brapports?\b",
                normalized,
            )
        )

    @staticmethod
    def _looks_like_publication_database_query(normalized: str) -> bool:
        explicit_db_keywords = (
            "bdd",
            "base de donnees",
            "base de donnee",
            "database",
            "sql",
            "table generated_images",
            "table generated_videos",
        )
        if any(keyword in normalized for keyword in explicit_db_keywords):
            return True

        return bool(
            re.search(
                r"\b(combien|liste|lister|quels|quelles|montre|affiche|donne)\b.*\b(images?|videos?|vdo|publications?)\b",
                normalized,
            )
        )

    @staticmethod
    def _resolve_publication_media_scope(normalized: str) -> str:
        has_image = any(keyword in normalized for keyword in ("image", "images", "photo", "photos", "visuel", "visuels"))
        has_video = any(keyword in normalized for keyword in ("video", "videos", "vdo", "reel"))
        if has_image and has_video:
            return "both"
        if has_image:
            return "image"
        if has_video:
            return "video"
        return "missing"

    @staticmethod
    def _infer_query_kind(normalized: str) -> str:
        analytics_keywords = (
            "combien",
            "total",
            "nombre",
            "statistique",
            "statistiques",
            "repartition",
            "repartition",
            "groupe",
            "groupes",
            "moyenne",
            "pourcentage",
            "compare",
            "comparaison",
            "how many",
            "count",
            "number",
            "statistics",
            "stats",
            "average",
            "percentage",
            "comparison",
        )
        if any(keyword in normalized for keyword in analytics_keywords):
            return "analytics"
        return "listing"

    @staticmethod
    def _with_response_language(
        classification_result: dict[str, Any] | list[Any],
        user_request: str,
    ) -> dict[str, Any] | list[Any]:
        if not isinstance(classification_result, dict):
            return classification_result

        normalized_language = OrchestratorService._normalize_response_language(
            classification_result.get("response_language")
        )
        if not normalized_language:
            normalized_language = OrchestratorService._detect_response_language(user_request)

        enriched = dict(classification_result)
        enriched["response_language"] = normalized_language
        return enriched

    @staticmethod
    def _resolve_response_language(
        user_request: str,
        payload: dict[str, Any] | None = None,
    ) -> str:
        if isinstance(payload, dict):
            normalized_language = OrchestratorService._normalize_response_language(
                payload.get("response_language")
            )
            if normalized_language:
                return normalized_language
        return OrchestratorService._detect_response_language(user_request)

    @staticmethod
    def _normalize_response_language(value: Any) -> str | None:
        normalized = str(value or "").strip().lower()
        if not normalized:
            return None
        if normalized in {"arabic", "arabe", "العربية", "عربي"}:
            return "Arabic"
        if normalized in {"french", "francais", "français", "fr"}:
            return "French"
        if normalized in {"english", "anglais", "en"}:
            return "English"
        return None

    @staticmethod
    def _detect_response_language(user_request: str) -> str:
        normalized = OrchestratorService._normalize_text(user_request)
        if re.search(r"\b(in english|answer in english|respond in english)\b", normalized):
            return "English"
        if re.search(r"\b(en francais|en français|reponds en francais|repond en francais|réponds en français)\b", normalized):
            return "French"
        if any(keyword in normalized for keyword in ("بالعربي", "بالعربية", "باللغة العربية", "عربي", "العربية")):
            return "Arabic"
        if re.search(r"[\u0600-\u06FF]", str(user_request)):
            return "Arabic"

        english_markers = (
            "give",
            "me",
            "the",
            "i",
            "want",
            "show",
            "list",
            "add",
            "save",
            "insert",
            "store",
            "all",
            "existing",
            "exist",
            "this",
            "report",
            "reports",
            "product",
            "products",
            "image",
            "video",
            "generate",
            "create",
            "what",
            "which",
            "how",
            "many",
            "with",
            "database",
            "potential",
            "weak",
            "strong",
            "medium",
            "low",
            "high",
        )
        french_markers = (
            "donne",
            "liste",
            "lister",
            "montre",
            "affiche",
            "tous",
            "existant",
            "existants",
            "rapport",
            "rapports",
            "produit",
            "produits",
            "image",
            "video",
            "genere",
            "creer",
            "quel",
            "quelle",
            "combien",
            "avec",
        )

        tokens = re.findall(r"[a-zA-Z]+", normalized)
        english_score = sum(1 for token in tokens if token in english_markers)
        french_score = sum(1 for token in tokens if token in french_markers)
        if english_score > french_score:
            return "English"
        if french_score > english_score:
            return "French"
        return "the dominant language of the user request"

    @staticmethod
    def _build_response_language_instruction() -> str:
        return (
            "the exact same language as the user request. "
            "If the request mixes languages, use the dominant language. "
            "Do not default to French unless French is the dominant language."
        )

    @staticmethod
    def _extract_occasion_fragment(user_request: str) -> str | None:
        lowered = user_request.strip()
        if not lowered:
            return None

        normalized = OrchestratorService._normalize_text(lowered)
        if OrchestratorService._looks_like_next_occasion_request(normalized):
            return None
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
    def _normalize_classification_result(
        classification_result: dict[str, Any] | list[Any],
        user_request: str,
    ) -> dict[str, Any] | list[Any]:
        if not isinstance(classification_result, dict):
            return classification_result

        intent = str(classification_result.get("intent", "")).strip().lower()
        if intent != "publication":
            return classification_result

        normalized_request = OrchestratorService._normalize_text(user_request)
        normalized_result = dict(classification_result)
        generation_mode = str(normalized_result.get("generation_mode", "")).strip().lower()
        occasion = str(normalized_result.get("occasion", "")).strip()

        if (
            generation_mode == "given_occasion"
            and OrchestratorService._looks_like_generic_next_event(occasion)
        ) or (
            generation_mode in {"", "missing"}
            and OrchestratorService._looks_like_next_occasion_request(normalized_request)
        ):
            normalized_result["generation_mode"] = "next_occasion"
            normalized_result["occasion"] = None

        return normalized_result

    @staticmethod
    def _looks_like_next_occasion_request(normalized: str) -> bool:
        next_occasion_markers = (
            "prochaine occasion",
            "occasion la plus proche",
            "prochaine fete",
            "fete la plus proche",
            "prochain evenement",
            "evenement a venir",
            "next occasion",
            "nearest occasion",
            "next event",
            "upcoming event",
            "upcoming occasion",
            "coming event",
            "uncoming event",
        )
        return any(marker in normalized for marker in next_occasion_markers)

    @staticmethod
    def _looks_like_generic_next_event(value: str) -> bool:
        normalized = OrchestratorService._normalize_text(value)
        if not normalized:
            return False

        generic_event_markers = (
            "next event",
            "upcoming event",
            "upcoming occasion",
            "coming event",
            "uncoming event",
            "prochain evenement",
            "evenement a venir",
            "prochaine occasion",
        )
        return any(marker == normalized for marker in generic_event_markers)

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
