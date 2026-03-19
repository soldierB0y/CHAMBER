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


@app.route("/v1", methods=["GET"])
@app.route("/v1/", methods=["GET"])
def welcome():
    active = _roulette.get_active_count() if _roulette else 0
    current_id = _roulette.get_current_provider_id() if _roulette else ""
    status_color = "#22c55e" if _roulette else "#ef4444"
    status_text = "Online" if _roulette else "Offline"
    provider_html = ""
    if _roulette and current_id:
        from providers import PROVIDERS
        name = PROVIDERS.get(current_id, {}).get("name", current_id)
        provider_html = f'<div class="pill">Proveedor activo: <strong>{name}</strong></div>'

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Chamber API</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:#0a0a0f;color:#e2e8f0;font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:2rem}}
  .card{{background:#13131a;border:1px solid #1e1e2e;border-radius:16px;padding:3rem 2.5rem;max-width:600px;width:100%;box-shadow:0 25px 60px rgba(0,0,0,.5)}}
  .logo{{font-size:2.8rem;font-weight:800;letter-spacing:.08em;background:linear-gradient(135deg,#a78bfa,#60a5fa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:.25rem}}
  .tagline{{color:#6b7280;font-size:.95rem;margin-bottom:2rem}}
  .status-row{{display:flex;align-items:center;gap:.6rem;margin-bottom:2rem}}
  .dot{{width:10px;height:10px;border-radius:50%;background:{status_color};box-shadow:0 0 8px {status_color}}}
  .status-text{{font-size:.9rem;color:#9ca3af}}
  .providers-count{{margin-left:auto;font-size:.85rem;color:#6b7280}}{'' if not provider_html else ''}
  .pill{{display:inline-block;background:#1e1e2e;border:1px solid #2d2d44;border-radius:999px;padding:.35rem 1rem;font-size:.85rem;color:#a78bfa;margin-bottom:2rem}}
  .section-title{{font-size:.75rem;text-transform:uppercase;letter-spacing:.1em;color:#4b5563;margin-bottom:1rem}}
  .endpoint-list{{display:flex;flex-direction:column;gap:.6rem;margin-bottom:2rem}}
  .endpoint{{background:#0a0a0f;border:1px solid #1e1e2e;border-radius:8px;padding:.7rem 1rem;display:flex;align-items:center;gap:.75rem;font-family:'Courier New',monospace;font-size:.85rem}}
  .method{{font-size:.7rem;font-weight:700;padding:.2rem .5rem;border-radius:4px;min-width:42px;text-align:center}}
  .get{{background:#064e3b;color:#6ee7b7}}.post{{background:#1e3a5f;color:#93c5fd}}
  .ep-path{{color:#e2e8f0}}.ep-desc{{margin-left:auto;color:#6b7280;font-size:.78rem;font-family:'Segoe UI',sans-serif}}
  .code-block{{background:#0a0a0f;border:1px solid #1e1e2e;border-radius:8px;padding:1rem 1.2rem;font-family:'Courier New',monospace;font-size:.8rem;color:#86efac;line-height:1.7;margin-bottom:.5rem;overflow-x:auto;white-space:pre}}
  .footer{{text-align:center;color:#374151;font-size:.78rem;margin-top:2rem;padding-top:1.5rem;border-top:1px solid #1e1e2e}}
</style>
</head>
<body>
<div class="card">
  <div class="logo">CHAMBER</div>
  <div class="tagline">Free LLM Proxy &mdash; Compatible con OpenAI API</div>
  <div class="status-row">
    <span class="dot"></span>
    <span class="status-text">{status_text}</span>
    <span class="providers-count">{active} proveedor{"es" if active != 1 else ""} activo{"s" if active != 1 else ""}</span>
  </div>
  {provider_html}
  <div class="section-title">Endpoints disponibles</div>
  <div class="endpoint-list">
    <div class="endpoint"><span class="method get">GET</span><span class="ep-path">/v1/models</span><span class="ep-desc">Lista de modelos</span></div>
    <div class="endpoint"><span class="method post">POST</span><span class="ep-path">/v1/chat/completions</span><span class="ep-desc">Chat</span></div>
    <div class="endpoint"><span class="method get">GET</span><span class="ep-path">/health</span><span class="ep-desc">Estado del servidor</span></div>
  </div>
  <div class="section-title">Ejemplo rápido</div>
  <div class="code-block">from openai import OpenAI
client = OpenAI(
    base_url="http://{request.host}/v1",
    api_key="x"
)
r = client.chat.completions.create(
    model="auto",
    messages=[{{"role":"user","content":"Hola!"}}]
)
print(r.choices[0].message.content)</div>
  <div class="footer">Chamber &mdash; github.com/soldierB0y/CHAMBER</div>
</div>
</body>
</html>"""
    return Response(html, mimetype="text/html")


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
    # Respetar stream del cliente; si no lo manda, usar config toggle
    if "stream" in data:
        stream_enabled = bool(data["stream"])
    else:
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

    if "choices" not in result or not result.get("choices"):
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


def _get_lan_ip():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "0.0.0.0"


class APIServer:
    def __init__(self, roulette, port=11411, host="0.0.0.0", on_log=None):
        self.port = port
        self.host = host
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
        from werkzeug.serving import make_server
        self._server = make_server(self.host, self.port, app)
        lan_ip = _get_lan_ip()
        _log(f"🚀 Servidor API iniciado — http://localhost:{self.port}/v1")
        _log(f"🌐 Red local — http://{lan_ip}:{self.port}/v1")
        self._server.serve_forever()

    def stop(self):
        self.running = False
        if hasattr(self, "_server") and self._server:
            self._server.shutdown()
        set_roulette(None)
