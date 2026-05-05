import json
import traceback
from pathlib import Path

from flask import Blueprint, abort, jsonify, request, send_file
from conversation import ConversationAccessError
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
from gestionPublication.generationImage.config import OUTPUT_DIR
from gestionRapport.structuration import (
    StructurationConfigError,
    StructurationPersistenceError,
    StructurationRapportService,
    StructurationRequestError,
    StructurationResponseError,
)
from orchestrateur import (
    OrchestratorConfigError,
    OrchestratorMissingDataError,
    OrchestratorProcessingError,
    OrchestratorRequestError,
    OrchestratorResponseError,
    OrchestratorService,
)
from voice import (
    VoiceSynthesisError,
    VoiceSynthesisService,
    VoiceTranscriptionConfigError,
    VoiceTranscriptionRequestError,
    VoiceTranscriptionService,
    VoiceValidationError,
)

main = Blueprint("main", __name__)


def build_orchestrator_missing_report_response(details: str) -> tuple:
    return (
        jsonify(
            {
                "status": "missing_information",
                "intent": "rapport",
                "message": (
                    "Votre demande concerne un rapport, mais le texte du rapport n'a pas ete fourni. "
                    "Ajoutez le contenu du rapport dans le champ 'rapport'."
                ),
                "data": None,
                "choices": [],
                "missing_fields": ["rapport"],
                "error": "Des donnees sont manquantes.",
                "source": "request",
                "details": details,
            }
        ),
        200,
    )


def build_orchestrator_quota_response(details: str) -> tuple:
    normalized = details.lower()
    retry_message = ""
    retry_match = None
    try:
        import re

        retry_match = re.search(r"retry in\s+([0-9]+(?:\.[0-9]+)?)s", normalized)
    except Exception:
        retry_match = None

    if retry_match:
        retry_seconds = retry_match.group(1)
        retry_message = f" Reessayez dans environ {retry_seconds} secondes."

    return (
        jsonify(
            {
                "error": "Le quota Gemini est depasse pour l'orchestrateur.",
                "source": "gemini_quota",
                "message": (
                    "Le service Gemini a refuse la requete parce que le quota disponible est epuise."
                    + retry_message
                ),
                "details": details,
            }
        ),
        429,
    )


def build_orchestrator_auth_response(details: str) -> tuple:
    return (
        jsonify(
            {
                "error": "La cle Gemini utilisee par l'orchestrateur est invalide ou bloquee.",
                "source": "gemini_auth",
                "message": (
                    "Le service Gemini a refuse la requete car la cle API est invalide, bloquee, "
                    "ou signalee comme exposee. Remplacez GEMINI_API_KEY par une nouvelle cle valide "
                    "puis redemarrez le serveur."
                ),
                "details": details,
            }
        ),
        403,
    )


def build_voice_transcription_quota_response(details: str) -> tuple:
    normalized = details.lower()
    retry_message = ""
    retry_match = None
    try:
        import re

        retry_match = re.search(r"retry in\s+([0-9]+(?:\.[0-9]+)?)s", normalized)
    except Exception:
        retry_match = None

    if retry_match:
        retry_seconds = retry_match.group(1)
        retry_message = f" Reessayez dans environ {retry_seconds} secondes."

    return (
        jsonify(
            {
                "error": "Le quota Gemini est depasse pour la transcription vocale.",
                "source": "gemini_quota",
                "message": (
                    "Le service Gemini a refuse la transcription vocale parce que le quota "
                    "disponible est epuise."
                    + retry_message
                ),
                "details": details,
            }
        ),
        429,
    )


def build_voice_transcription_auth_response(details: str) -> tuple:
    return (
        jsonify(
            {
                "error": "La cle Gemini utilisee pour la transcription vocale est invalide ou bloquee.",
                "source": "gemini_auth",
                "message": (
                    "Le service Gemini a refuse la transcription vocale car la cle API est invalide, "
                    "bloquee, ou signalee comme exposee. Remplacez GEMINI_API_KEY par une nouvelle "
                    "cle valide puis redemarrez le serveur."
                ),
                "details": details,
            }
        ),
        403,
    )


def extract_text_from_request() -> str | None:
    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        text = payload.get("text")
        if isinstance(text, str) and text.strip():
            return text.strip()

    form_text = request.form.get("text")
    if isinstance(form_text, str) and form_text.strip():
        return form_text.strip()

    raw_body = request.get_data(cache=True)
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

    raw_body = request.get_data(cache=True)
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


def extract_report_from_request() -> str | None:
    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        for field_name in ("rapport", "report_text"):
            field_value = payload.get(field_name)
            if isinstance(field_value, str) and field_value.strip():
                return field_value.strip()

    for field_name in ("rapport", "report_text"):
        form_value = request.form.get(field_name)
        if isinstance(form_value, str) and form_value.strip():
            return form_value.strip()

    raw_body = request.get_data(cache=True)
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
            for field_name in ("rapport", "report_text"):
                field_value = parsed.get(field_name)
                if isinstance(field_value, str) and field_value.strip():
                    return field_value.strip()

    return None


def extract_int_from_request(*field_names: str) -> int | None:
    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        for field_name in field_names:
            field_value = payload.get(field_name)
            if field_value is None:
                continue
            try:
                return int(field_value)
            except (TypeError, ValueError):
                return None

    for field_name in field_names:
        form_value = request.form.get(field_name)
        if form_value is None:
            continue
        try:
            return int(form_value)
        except (TypeError, ValueError):
            return None

    return None


def extract_speakable_text(payload: object) -> str | None:
    if isinstance(payload, str) and payload.strip():
        return payload.strip()

    if isinstance(payload, dict):
        for field_name in ("response", "message", "text", "error", "details"):
            field_value = payload.get(field_name)
            if isinstance(field_value, str) and field_value.strip():
                return field_value.strip()

        for field_value in payload.values():
            nested_text = extract_speakable_text(field_value)
            if nested_text:
                return nested_text

    if isinstance(payload, list):
        for item in payload:
            nested_text = extract_speakable_text(item)
            if nested_text:
                return nested_text

    return None


def build_voice_response_payload(payload: object) -> dict:
    response_text = extract_speakable_text(payload)
    if not response_text:
        return {
            "available": False,
            "error": "Aucun texte vocalisable trouve dans la reponse orchestrateur.",
        }

    try:
        return VoiceSynthesisService().synthesize_base64(response_text)
    except VoiceSynthesisError as exc:
        return {
            "available": False,
            "error": "La generation vocale a echoue.",
            "details": str(exc),
        }


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


def build_orchestrator_response(
    demande: str,
    report_text: str | None = None,
    user_id: int | None = None,
    conversation_id: int | None = None,
) -> tuple:
    service = OrchestratorService()

    try:
        result = service.handle(
            demande,
            report_text=report_text,
            user_id=user_id,
            conversation_id=conversation_id,
        )
    except OrchestratorMissingDataError as exc:
        return build_orchestrator_missing_report_response(str(exc))
    except ConversationAccessError as exc:
        return (
            jsonify(
                {
                    "error": str(exc),
                    "source": "conversation_access",
                }
            ),
            403,
        )
    except OrchestratorConfigError as exc:
        return (
            jsonify(
                {
                    "error": "Configuration invalide pour l'orchestrateur.",
                    "source": "config",
                    "details": str(exc),
                }
            ),
            500,
        )
    except OrchestratorRequestError as exc:
        details = str(exc)
        normalized = details.lower()
        if "resource_exhausted" in normalized or "quota exceeded" in normalized:
            return build_orchestrator_quota_response(details)
        if "permission_denied" in normalized or "api key was reported as leaked" in normalized:
            return build_orchestrator_auth_response(details)
        return (
            jsonify(
                {
                    "error": "L'appel a un service externe a echoue pour l'orchestrateur.",
                    "source": "external_service",
                    "details": details,
                }
            ),
            502,
        )
    except OrchestratorResponseError as exc:
        return (
            jsonify(
                {
                    "error": "La reponse retournee pour l'orchestrateur est invalide.",
                    "source": "service_response",
                    "details": str(exc),
                }
            ),
            502,
        )
    except OrchestratorProcessingError as exc:
        print("[/orchestrate] Processing error:")
        traceback.print_exc()
        details = str(exc)
        normalized = details.lower()
        if "resource_exhausted" in normalized or "quota exceeded" in normalized:
            return build_orchestrator_quota_response(details)
        if "permission_denied" in normalized or "api key was reported as leaked" in normalized:
            return build_orchestrator_auth_response(details)
        return (
            jsonify(
                {
                    "error": "Le traitement metier de l'orchestrateur a echoue.",
                    "source": "processing",
                    "details": details,
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


@main.post("/orchestrate-voice")
def orchestrate_voice_request():
    audio_file = (
        request.files.get("voice")
        or request.files.get("audio")
        or request.files.get("file")
    )
    report_text = extract_report_from_request()
    user_id = extract_int_from_request("id_user", "user_id")
    conversation_id = extract_int_from_request("id_conversation", "conversation_id")

    if (user_id is None) != (conversation_id is None):
        return (
            jsonify(
                {
                    "error": "Les champs 'id_user' et 'id_conversation' doivent etre fournis ensemble."
                }
            ),
            400,
        )

    transcription_service = VoiceTranscriptionService()

    try:
        demande = transcription_service.transcribe(audio_file)
    except VoiceValidationError as exc:
        return (
            jsonify(
                {
                    "error": str(exc),
                    "source": "voice_request",
                }
            ),
            400,
        )
    except VoiceTranscriptionConfigError as exc:
        return (
            jsonify(
                {
                    "error": "Configuration invalide pour la transcription vocale.",
                    "source": "voice_config",
                    "details": str(exc),
                }
            ),
            500,
        )
    except VoiceTranscriptionRequestError as exc:
        details = str(exc)
        normalized = details.lower()
        if "resource_exhausted" in normalized or "quota exceeded" in normalized:
            return build_voice_transcription_quota_response(details)
        if "permission_denied" in normalized or "api key was reported as leaked" in normalized:
            return build_voice_transcription_auth_response(details)
        return (
            jsonify(
                {
                    "error": "La transcription du fichier vocal a echoue.",
                    "source": "voice_transcription",
                    "details": details,
                }
            ),
            502,
        )

    orchestrator_response, status_code = build_orchestrator_response(
        demande,
        report_text=report_text,
        user_id=user_id,
        conversation_id=conversation_id,
    )
    orchestrator_payload = orchestrator_response.get_json(silent=True)
    if orchestrator_payload is None:
        return orchestrator_response, status_code

    audio_response = build_voice_response_payload(orchestrator_payload)

    return (
        jsonify(
            {
                "transcription": demande,
                "result": orchestrator_payload,
                "audio_response": audio_response,
            }
        ),
        status_code,
    )


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
    except StructurationPersistenceError as exc:
        return (
            jsonify(
                {
                    "error": "La sauvegarde en base du rapport structure a echoue.",
                    "source": "storage",
                    "details": str(exc),
                }
            ),
            500,
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
    report_text = extract_report_from_request()
    user_id = extract_int_from_request("id_user", "user_id")
    conversation_id = extract_int_from_request("id_conversation", "conversation_id")

    if not isinstance(demande, str) or not demande:
        return (
            jsonify(
                {
                    "error": "Le champ 'demande' est obligatoire et doit etre une chaine non vide."
                }
            ),
            400,
        )

    if (user_id is None) != (conversation_id is None):
        return (
            jsonify(
                {
                    "error": "Les champs 'id_user' et 'id_conversation' doivent etre fournis ensemble."
                }
            ),
            400,
        )

    return build_orchestrator_response(
        demande,
        report_text=report_text,
        user_id=user_id,
        conversation_id=conversation_id,
    )


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


@main.get("/media/generated-image")
def serve_generated_image():
    raw_path = request.args.get("path", "").strip()
    if not raw_path:
        abort(400)

    candidate = Path(raw_path).expanduser()
    try:
        resolved = candidate.resolve(strict=True)
        output_root = OUTPUT_DIR.resolve(strict=True)
    except FileNotFoundError:
        abort(404)
    except Exception:
        abort(400)

    try:
        resolved.relative_to(output_root)
    except ValueError:
        abort(403)

    if not resolved.is_file():
        abort(404)

    return send_file(resolved)


# ========== ADDED FOR PDF EXPORT ==========
@main.get("/exports/pdf/<path:filename>")
def serve_exported_pdf(filename):
    """Serve exported PDF files."""
    export_dir = Path("exports/pdf")
    filepath = export_dir / filename
    
    try:
        resolved = filepath.resolve()
        exports_root = export_dir.resolve()
        resolved.relative_to(exports_root)
    except (ValueError, FileNotFoundError):
        abort(403)
    
    if not resolved.is_file():
        abort(404)
    
    return send_file(resolved, mimetype='application/pdf')


@main.get("/test-pdf")
def test_pdf_direct():
    """Test PDF export directly from structured reports."""
    from vital_agent.agents.task_report import TaskReportService
    from vital_agent.agents.pdf_export import PdfExportService, PdfExportRequest
    
    # Get structured reports directly
    task_service = TaskReportService()
    result = task_service.handle({"intent": "task_report", "report_type": "rapports"})
    
    if result.get("status") == "success" and result.get("content"):
        pdf_service = PdfExportService()
        pdf_result = pdf_service.export_report(
            PdfExportRequest(content=result["content"], title="test_report"),
            save_to_disk=True
        )
        return jsonify({
            "success": True,
            "pdf_url": pdf_result.pdf_url,
            "message": pdf_result.message
        })
    else:
        return jsonify({"success": False, "error": result.get("message")}), 500


@main.get("/debug-pdf")
def debug_pdf():
    """Debug PDF export step by step."""
    from vital_agent.agents.task_report import TaskReportService
    from vital_agent.agents.pdf_export import PdfExportService, PdfExportRequest
    from vital_agent.agents.task_report.repository import TaskReportRepository
    
    result = {
        "steps": [],
        "success": False,
        "error": None
    }
    
    # Step 1: Test database connection
    try:
        repo = TaskReportRepository()
        conn = repo._get_connection()
        if conn:
            result["steps"].append({"step": "database_connection", "status": "success"})
        else:
            result["steps"].append({"step": "database_connection", "status": "failed", "error": "Could not connect"})
            return jsonify(result)
    except Exception as e:
        result["steps"].append({"step": "database_connection", "status": "failed", "error": str(e)})
        return jsonify(result)
    
    # Step 2: Fetch structured reports
    try:
        task_service = TaskReportService()
        report_result = task_service.handle({"intent": "task_report", "report_type": "rapports"})
        result["steps"].append({
            "step": "fetch_reports",
            "status": report_result.get("status"),
            "message": report_result.get("message"),
            "content_length": len(report_result.get("content", "")),
            "has_content": bool(report_result.get("content"))
        })
        
        if report_result.get("status") != "success":
            result["error"] = report_result.get("message")
            return jsonify(result)
    except Exception as e:
        import traceback
        result["steps"].append({"step": "fetch_reports", "status": "failed", "error": str(e), "trace": traceback.format_exc()})
        return jsonify(result)
    
    # Step 3: Generate PDF
    try:
        pdf_service = PdfExportService()
        pdf_result = pdf_service.export_report(
            PdfExportRequest(content=report_result["content"], title="test_report"),
            save_to_disk=True
        )
        result["steps"].append({
            "step": "generate_pdf",
            "status": pdf_result.status,
            "message": pdf_result.message,
            "pdf_url": pdf_result.pdf_url,
            "error": pdf_result.error
        })
        
        if pdf_result.status == "success":
            result["success"] = True
            result["pdf_url"] = pdf_result.pdf_url
        else:
            result["error"] = pdf_result.error
    except Exception as e:
        import traceback
        result["steps"].append({"step": "generate_pdf", "status": "failed", "error": str(e), "trace": traceback.format_exc()})
    
    return jsonify(result)
# ==========================================