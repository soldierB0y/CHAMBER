"""
Servidor local compatible con la API de OpenAI.
Expone endpoints en localhost para que cualquier herramienta
(Continue, Cursor, scripts, etc.) pueda usarlo como si fuera OpenAI.
"""

import json
import threading
import logging
from flask import Flask, request, jsonify, Response

# Suprimir logs de Flask en consola (se muestran en el GUI)
log = logging.getLogger("werkzeug")
log.setLevel(logging.WARNING)

app = Flask(__name__)
_roulette = None
_on_log = None


def set_roulette(roulette_instance):
    global _roulette
    _roulette = roulette_instance


def set_log_callback(callback):
    global _on_log
    _on_log = callback


def _log(msg):
    if _on_log:
        _on_log(msg)


@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    if not _roulette:
        return jsonify({"error": {"message": "Roulette no inicializada"}}), 500

    data = request.get_json(force=True)
    messages = data.get("messages", [])
    if not messages:
        return jsonify({"error": {"message": "Se requiere 'messages'"}}), 400

    # Extraer modelo específico si se pide uno de un proveedor
    model = data.get("model")
    # Usar config de stream del roulette (toggle en Configuración)
    stream_enabled = _roulette.config.get("stream_enabled", False) if _roulette else False
    kwargs = {
        "temperature": data.get("temperature"),
        "max_tokens": data.get("max_tokens"),
        "top_p": data.get("top_p"),
        "stream": stream_enabled,
    }

    # Si el modelo es "provider_id/model_name", seleccionar ese proveedor
    if model and "/" in model:
        parts = model.split("/", 1)
        from providers import PROVIDERS
        if parts[0] in PROVIDERS:
            kwargs["model"] = parts[1]

    result = _roulette.chat_completion(messages, **kwargs)

    # If streaming, proxy the SSE response directly
    if "_stream" in result:
        def generate():
            try:
                for line in result["_stream"]:
                    if isinstance(line, bytes):
                        line = line.decode("utf-8")
                    if line:
                        yield f"{line}\n\n"
                yield "data: [DONE]\n\n"
            finally:
                raw = result.get("_raw_resp")
                if raw:
                    raw.close()
        return Response(
            generate(),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*",
            }
        )

    if "error" in result and "choices" not in result:
        return jsonify(result), 502

    return jsonify(result)


@app.route("/v1/models", methods=["GET"])
def list_models():
    if not _roulette:
        return jsonify({"data": [], "object": "list"}), 200

    models = _roulette.list_models()
    return jsonify({"data": models, "object": "list"})


@app.route("/v1/chat/completions", methods=["OPTIONS"])
@app.route("/v1/models", methods=["OPTIONS"])
def options():
    return "", 204


@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


# Health check
@app.route("/health", methods=["GET"])
def health():
    active = _roulette.get_active_count() if _roulette else 0
    current = _roulette.get_current_provider_id() if _roulette else ""
    return jsonify({
        "status": "ok",
        "active_providers": active,
        "current_provider": current,
    })


class APIServer:
    def __init__(self, roulette, port=11411, on_log=None):
        self.port = port
        self.roulette = roulette
        self.thread = None
        self.running = False
        set_roulette(roulette)
        if on_log:
            set_log_callback(on_log)

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(
            target=self._run, daemon=True, name="api-server"
        )
        self.thread.start()

    def _run(self):
        _log(f"🚀 Servidor API iniciado en http://localhost:{self.port}/v1")
        app.run(host="127.0.0.1", port=self.port, use_reloader=False)

    def stop(self):
        self.running = False
