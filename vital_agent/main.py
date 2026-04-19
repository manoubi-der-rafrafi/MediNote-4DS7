from flask import Flask, jsonify, request
from agent import VitalAgent

app = Flask(__name__)
agent = VitalAgent()


@app.route("/ask", methods=["POST"])
def ask():
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify({"error": "Body JSON invalide."}), 400

    demande = payload.get("demande") or payload.get("text", "")

    if not isinstance(demande, str) or not demande.strip():
        return jsonify({"error": "Le champ 'demande' est obligatoire."}), 400

    try:
        response = agent.ask(demande.strip())
    except Exception as exc:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Erreur agent.", "details": str(exc)}), 500

    return jsonify({"response": response}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "vital-agent"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
