import json

from flask import Blueprint, jsonify, request
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
from gestionRapport.structuration import (
    StructurationConfigError,
    StructurationRapportService,
    StructurationRequestError,
    StructurationResponseError,
)
from orchestrateur import (
    OrchestratorConfigError,
    OrchestratorProcessingError,
    OrchestratorRequestError,
    OrchestratorResponseError,
    OrchestratorService,
)

main = Blueprint("main", __name__)


def extract_text_from_request() -> str | None:
    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        text = payload.get("text")
        if isinstance(text, str) and text.strip():
            return text.strip()

    form_text = request.form.get("text")
    if isinstance(form_text, str) and form_text.strip():
        return form_text.strip()

    raw_body = request.get_data(cache=False)
    if not raw_body:
        return None

    for encoding in ("utf-8-sig", "utf-8", "utf-16", "utf-16-le", "utf-16-be", "latin-1"):
        try:
            decoded = raw_body.decode(encoding).strip()
        except UnicodeDecodeError:
            continue

        if not decoded:
            continue

        try:
            parsed = json.loads(decoded)
        except json.JSONDecodeError:
            continue

        if isinstance(parsed, dict):
            text = parsed.get("text")
            if isinstance(text, str) and text.strip():
                return text.strip()

    return None


def extract_demande_from_request() -> str | None:
    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        for field_name in ("demande", "text"):
            field_value = payload.get(field_name)
            if isinstance(field_value, str) and field_value.strip():
                return field_value.strip()

    for field_name in ("demande", "text"):
        form_value = request.form.get(field_name)
        if isinstance(form_value, str) and form_value.strip():
            return form_value.strip()

    raw_body = request.get_data(cache=False)
    if not raw_body:
        return None

    for encoding in ("utf-8-sig", "utf-8", "utf-16", "utf-16-le", "utf-16-be", "latin-1"):
        try:
            decoded = raw_body.decode(encoding).strip()
        except UnicodeDecodeError:
            continue

        if not decoded:
            continue

        try:
            parsed = json.loads(decoded)
        except json.JSONDecodeError:
            continue

        if isinstance(parsed, dict):
            for field_name in ("demande", "text"):
                field_value = parsed.get(field_name)
                if isinstance(field_value, str) and field_value.strip():
                    return field_value.strip()

    return None


def extract_generation_payload(default_media_type: str) -> dict:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        payload = {}

    result = dict(payload)
    result["media_type"] = default_media_type

    if "generation_mode" in result and isinstance(result["generation_mode"], str):
        result["generation_mode"] = result["generation_mode"].strip()
    if "occasion" in result and isinstance(result["occasion"], str):
        result["occasion"] = result["occasion"].strip()
    if "date" in result and isinstance(result["date"], str):
        result["date"] = result["date"].strip()

    return result


@main.post("/structure-points-forts")
def structure_points_forts():
    text = extract_text_from_request()

    if not isinstance(text, str) or not text:
        return (
            jsonify(
                {
                    "error": "Le champ 'text' est obligatoire et doit etre une chaine non vide."
                }
            ),
            400,
        )

    service = StructurationRapportService()

    try:
        result = service.handle(text)
    except StructurationConfigError as exc:
        return (
            jsonify(
                {
                    "error": "Configuration Gemini invalide.",
                    "source": "config",
                    "details": str(exc),
                }
            ),
            500,
        )
    except StructurationRequestError as exc:
        return (
            jsonify(
                {
                    "error": "L'appel a Gemini a echoue.",
                    "source": "gemini_api",
                    "details": str(exc),
                }
            ),
            502,
        )
    except StructurationResponseError as exc:
        return (
            jsonify(
                {
                    "error": "La reponse retournee par Gemini est invalide.",
                    "source": "gemini_response",
                    "details": str(exc),
                }
            ),
            502,
        )
    except Exception as exc:
        return (
            jsonify(
                {
                    "error": "La structuration a echoue.",
                    "source": "server",
                    "details": str(exc),
                }
            ),
            500,
        )

    return jsonify(result.model_dump()), 200


@main.post("/orchestrate")
def orchestrate_request():
    demande = extract_demande_from_request()

    if not isinstance(demande, str) or not demande:
        return (
            jsonify(
                {
                    "error": "Le champ 'demande' est obligatoire et doit etre une chaine non vide."
                }
            ),
            400,
        )

    service = OrchestratorService()

    try:
        result = service.handle(demande)
    except OrchestratorConfigError as exc:
        return (
            jsonify(
                {
                    "error": "Configuration Gemini invalide pour l'orchestrateur.",
                    "source": "config",
                    "details": str(exc),
                }
            ),
            500,
        )
    except OrchestratorRequestError as exc:
        return (
            jsonify(
                {
                    "error": "L'appel a Gemini a echoue pour l'orchestrateur.",
                    "source": "gemini_api",
                    "details": str(exc),
                }
            ),
            502,
        )
    except OrchestratorResponseError as exc:
        return (
            jsonify(
                {
                    "error": "La reponse retournee par Gemini pour l'orchestrateur est invalide.",
                    "source": "gemini_response",
                    "details": str(exc),
                }
            ),
            502,
        )
    except OrchestratorProcessingError as exc:
        return (
            jsonify(
                {
                    "error": "Le traitement de publication a echoue.",
                    "source": "publication",
                    "details": str(exc),
                }
            ),
            502,
        )
    except Exception as exc:
        return (
            jsonify(
                {
                    "error": "L'orchestration a echoue.",
                    "source": "server",
                    "details": str(exc),
                }
            ),
            500,
        )

    return jsonify(result), 200


@main.post("/generationImage")
def generate_image_publication():
    payload = extract_generation_payload("image")
    service = ImageGenerationService()

    try:
        result = service.handle(payload)
    except ImageGenerationRequestValidationError as exc:
        return jsonify({"error": str(exc), "source": "request"}), 400
    except ImageGenerationContextError as exc:
        return jsonify({"error": str(exc), "source": "context"}), 400
    except ImageGenerationConfigError as exc:
        return jsonify({"error": str(exc), "source": "config"}), 500
    except ImageGenerationRequestError as exc:
        return jsonify({"error": str(exc), "source": "generation"}), 502
    except ImageGenerationPersistenceError as exc:
        return jsonify({"error": str(exc), "source": "storage"}), 500
    except Exception as exc:
        return jsonify({"error": str(exc), "source": "server"}), 500

    return jsonify(result), 200


@main.post("/generationVDO")
def generate_video_publication():
    payload = extract_generation_payload("video")
    service = PublicationService()

    try:
        result = service.handle(payload)
    except PublicationRequestError as exc:
        return jsonify({"error": str(exc), "source": "request"}), 400
    except PublicationConfigError as exc:
        return jsonify({"error": str(exc), "source": "config"}), 500
    except PublicationResponseError as exc:
        return jsonify({"error": str(exc), "source": "generation"}), 502
    except PublicationPersistenceError as exc:
        return jsonify({"error": str(exc), "source": "storage"}), 500
    except Exception as exc:
        return jsonify({"error": str(exc), "source": "server"}), 500

    return jsonify(result), 200
