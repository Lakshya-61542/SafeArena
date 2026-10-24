"""Client LLM service (the model under evaluation). Runs on llm_net ONLY and has no internet egress.

Mock-only by design: the optional Gemini provider is called from the gateway, because the gateway
is the only container allowed to reach the internet.
"""
import os

from flask import Flask, jsonify, request

from common import mock_llm

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024


@app.get("/health")
def health():
    return {"service": "llm", "status": "ok"}


@app.post("/infer")
def infer():
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not isinstance(body.get("prompt"), str):
        return jsonify({"error": "JSON body with a string 'prompt' is required"}), 400
    actor = body.get("actor") if isinstance(body.get("actor"), str) else "unknown"
    return jsonify(mock_llm.infer(body["prompt"][:4000], actor[:32]))


if __name__ == "__main__":
    app.run(host=os.getenv("BIND_HOST", "127.0.0.1"), port=int(os.getenv("BIND_PORT", "8103")), threaded=True)
