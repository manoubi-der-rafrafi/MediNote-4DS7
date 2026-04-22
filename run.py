import os
import sys
import json

# ── Forcer le répertoire de travail = dossier contenant ce fichier ────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from flask import Flask, request, jsonify

# ── Import VitalAgent (lazy) ──────────────────────────────────────────────────
_vital_agent = None

def get_vital_agent():
    global _vital_agent
    if _vital_agent is None:
        from vital_agent.agent import VitalAgent
        _vital_agent = VitalAgent()
    return _vital_agent

# ── App Flask ─────────────────────────────────────────────────────────────────
app = Flask(__name__)

from orchestrateur import (
    OrchestratorConfigError,
    OrchestratorProcessingError,
    OrchestratorRequestError,
    OrchestratorResponseError,
    OrchestratorService,
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
from gestionRapport.structuration import (
    StructurationConfigError,
    StructurationRapportService,
    StructurationRequestError,
    StructurationResponseError,
)


# ── Helpers extraction payload ────────────────────────────────────────────────

def extract_demande_from_request() -> str | None:
    payload = request.get_json(silent=True)
    print(f"[DEBUG] extract_demande payload: {payload}, type: {type(payload)}")
    if isinstance(payload, dict):
        for field in ("demande", "text"):
            val = payload.get(field)
            if isinstance(val, str) and val.strip():
                return val.strip()

    for field in ("demande", "text"):
        form_val = request.form.get(field)
        if isinstance(form_val, str) and form_val.strip():
            return form_val.strip()

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
            for field in ("demande", "text"):
                val = parsed.get(field)
                if isinstance(val, str) and val.strip():
                    return val.strip()

    return None


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


def extract_generation_payload(default_media_type: str) -> dict:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        payload = {}
    result = dict(payload)
    result["media_type"] = default_media_type
    for field in ("generation_mode", "occasion", "date"):
        if field in result and isinstance(result[field], str):
            result[field] = result[field].strip()
    return result


# ── Routes ────────────────────────────────────────────────────────────────────

@app.post("/orchestrate")
def orchestrate_request():
    demande = extract_demande_from_request()
    if not demande:
        return jsonify({"error": "Le champ 'demande' est obligatoire."}), 400
    service = OrchestratorService()
    try:
        result = service.handle(demande)
    except OrchestratorConfigError as exc:
        return jsonify({"error": "Configuration invalide.", "details": str(exc)}), 500
    except OrchestratorRequestError as exc:
        return jsonify({"error": "Appel Gemini echoue.", "details": str(exc)}), 502
    except OrchestratorResponseError as exc:
        return jsonify({"error": "Reponse Gemini invalide.", "details": str(exc)}), 502
    except OrchestratorProcessingError as exc:
        return jsonify({"error": "Traitement echoue.", "details": str(exc)}), 502
    except Exception as exc:
        return jsonify({"error": "Erreur serveur.", "details": str(exc)}), 500
    return jsonify(result), 200


@app.post("/structure-points-forts")
def structure_points_forts():
    text = extract_text_from_request()
    if not text:
        return jsonify({"error": "Le champ 'text' est obligatoire."}), 400
    service = StructurationRapportService()
    try:
        result = service.handle(text)
    except StructurationConfigError as exc:
        return jsonify({"error": "Configuration invalide.", "details": str(exc)}), 500
    except StructurationRequestError as exc:
        return jsonify({"error": "Appel Gemini echoue.", "details": str(exc)}), 502
    except StructurationResponseError as exc:
        return jsonify({"error": "Reponse invalide.", "details": str(exc)}), 502
    except Exception as exc:
        return jsonify({"error": "Erreur serveur.", "details": str(exc)}), 500
    return jsonify(result.model_dump()), 200


@app.post("/generationImage")
def generate_image():
    payload = extract_generation_payload("image")
    print(f"[DEBUG] generationImage payload: {payload}")
    service = ImageGenerationService()
    try:
        result = service.handle(payload)
    except ImageGenerationRequestValidationError as exc:
        return jsonify({"error": str(exc), "source": "request", "debug_payload": payload}), 400
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


@app.post("/generationVDO")
def generate_video():
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


# ── VitalAgent ────────────────────────────────────────────────────────────────

@app.post("/ask-vital")
def ask_vital():
    demande = extract_demande_from_request()
    if not demande:
        return jsonify({"error": "Le champ 'demande' est obligatoire."}), 400
    try:
        agent = get_vital_agent()
        response = agent.ask(demande)
    except Exception as exc:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Erreur VitalAgent.", "details": str(exc)}), 500
    return jsonify({"response": response}), 200


@app.get("/ask-vital/health")
def ask_vital_health():
    return jsonify({"status": "ok", "service": "vital-agent"}), 200


@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(debug=True)