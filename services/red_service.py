"""Red zone sandbox (adversarial prompts / attack tooling live here).

Runs on red_net ONLY. /probe lets the gateway ask this container to try to reach things it
must not reach (Blue, the LLM container directly) plus a control it must reach (the gateway).
Targets are fixed in code: this endpoint cannot be used to scan arbitrary hosts.
"""
import os
import socket

from flask import Flask, jsonify

app = Flask(__name__)

TARGETS = (
    {"target": "blue-service:8102", "role": "must_be_blocked"},
    {"target": "llm-service:8103", "role": "must_be_blocked"},
    {"target": "gateway:8000", "role": "control"},
)


def tcp_probe(host, port, timeout=2.0):
    out = {"resolved": None, "connected": False, "error": None}
    try:
        out["resolved"] = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)[0][4][0]
    except OSError as exc:
        out["error"] = "dns:" + type(exc).__name__
        return out
    try:
        with socket.create_connection((host, port), timeout=timeout):
            out["connected"] = True
    except OSError as exc:
        out["error"] = "tcp:" + type(exc).__name__
    return out


@app.get("/health")
def health():
    return {"service": "red", "status": "ok"}


@app.get("/probe")
def probe():
    results = []
    for t in TARGETS:
        host, port = t["target"].split(":")
        results.append({**t, **tcp_probe(host, int(port))})
    return jsonify({"zone": "red", "results": results})


if __name__ == "__main__":
    app.run(host=os.getenv("BIND_HOST", "127.0.0.1"), port=int(os.getenv("BIND_PORT", "8101")), threaded=True)
