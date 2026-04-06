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


def calculate_payload_size(messages):
    """Estima el número de tokens (caracteres / 4)."""
    total_chars = 0
    for m in messages:
        content = m.get("content", "")
        if isinstance(content, str):
            total_chars += len(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    total_chars += len(part.get("text", ""))
    return total_chars // 4


def smart_crop_messages(messages, limit=10000):
    """Truncar el centro de bloques de código grandes en mensajes de usuario."""
    current_size = calculate_payload_size(messages)
    if current_size <= limit:
        return messages, False

    new_messages = []
    cropped = False
    
    # Intentar reducir solo mensajes de usuario con mucho contenido
    for m in messages:
        if m.get("role") == "user" and isinstance(m.get("content"), str):
            content = m["content"]
            lines = content.splitlines()
            # Si tiene más de 300 líneas, probablemente es código o un log grande
            if len(lines) > 300:
                head = lines[:100]
                tail = lines[-100:]
                new_content = "\n".join(head) + "\n\n... [CONTENIDO OMITIDO POR TAMAÑO EXCESIVO EN CHAMBER] ...\n\n" + "\n".join(tail)
                new_m = m.copy()
                new_m["content"] = new_content
                new_messages.append(new_m)
                cropped = True
                continue
        new_messages.append(m)
    
    return new_messages, cropped


def set_log_callback(callback):
    global _on_log
    _on_log = callback


def _log(msg):
    if _on_log:
        _on_log(msg)


@app.route("/v1", methods=["GET"])
@app.route("/v1/", methods=["GET"])
@app.route("/v1/<level>", methods=["GET"])
@app.route("/v1/<level>/", methods=["GET"])
def welcome(level=None):
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
  body{{background:#0a0a0f;color:#e2e8f0;font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh;min-height:100dvh;display:flex;align-items:center;justify-content:center;padding:1rem}}
  .card{{background:#13131a;border:1px solid #1e1e2e;border-radius:16px;padding:2rem 1.5rem;max-width:600px;width:100%;box-shadow:0 25px 60px rgba(0,0,0,.5)}}
  .logo{{font-size:clamp(1.8rem,6vw,2.8rem);font-weight:800;letter-spacing:.08em;background:linear-gradient(135deg,#a78bfa,#60a5fa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:.25rem}}
  .tagline{{color:#6b7280;font-size:clamp(.8rem,2.5vw,.95rem);margin-bottom:1.5rem}}
  .status-row{{display:flex;align-items:center;flex-wrap:wrap;gap:.5rem;margin-bottom:1.5rem}}
  .dot{{width:10px;height:10px;border-radius:50%;background:{status_color};box-shadow:0 0 8px {status_color};flex-shrink:0}}
  .status-text{{font-size:.9rem;color:#9ca3af}}
  .providers-count{{margin-left:auto;font-size:.85rem;color:#6b7280}}{'' if not provider_html else ''}
  .pill{{display:inline-block;background:#1e1e2e;border:1px solid #2d2d44;border-radius:999px;padding:.35rem 1rem;font-size:.82rem;color:#a78bfa;margin-bottom:1.5rem;word-break:break-word}}
  .section-title{{font-size:.75rem;text-transform:uppercase;letter-spacing:.1em;color:#4b5563;margin-bottom:.8rem}}
  .endpoint-list{{display:flex;flex-direction:column;gap:.5rem;margin-bottom:1.5rem}}
  .endpoint{{background:#0a0a0f;border:1px solid #1e1e2e;border-radius:8px;padding:.6rem .8rem;display:flex;align-items:center;flex-wrap:wrap;gap:.5rem;font-family:'Courier New',monospace;font-size:clamp(.72rem,2vw,.85rem)}}
  .method{{font-size:.7rem;font-weight:700;padding:.2rem .5rem;border-radius:4px;min-width:42px;text-align:center;flex-shrink:0}}
  .get{{background:#064e3b;color:#6ee7b7}}.post{{background:#1e3a5f;color:#93c5fd}}
  .ep-path{{color:#e2e8f0;word-break:break-all}}
  .ep-desc{{margin-left:auto;color:#6b7280;font-size:clamp(.7rem,1.8vw,.78rem);font-family:'Segoe UI',sans-serif;white-space:nowrap}}
  .code-block{{background:#0a0a0f;border:1px solid #1e1e2e;border-radius:8px;padding:.8rem 1rem;font-family:'Courier New',monospace;font-size:clamp(.68rem,1.8vw,.8rem);color:#86efac;line-height:1.7;margin-bottom:.5rem;overflow-x:auto;white-space:pre;-webkit-overflow-scrolling:touch}}
  .footer{{text-align:center;color:#374151;font-size:.78rem;margin-top:1.5rem;padding-top:1.2rem;border-top:1px solid #1e1e2e}}
  .chatbot-btn{{display:inline-block;background:linear-gradient(135deg,#a78bfa,#60a5fa);color:#0a0a0f;font-weight:700;padding:.65rem 2rem;border-radius:999px;text-decoration:none;font-size:clamp(.85rem,2.5vw,.95rem);letter-spacing:.03em;transition:opacity .2s}}
  .chatbot-btn:hover{{opacity:.85}}
  @media(max-width:480px){{
    body{{padding:.5rem;align-items:flex-start}}
    .card{{border-radius:12px;padding:1.4rem 1rem}}
    .status-row{{flex-direction:column;align-items:flex-start;gap:.4rem}}
    .providers-count{{margin-left:0}}
    .endpoint{{gap:.4rem}}
    .ep-desc{{margin-left:0;width:100%;padding-left:calc(42px + .5rem)}}
  }}
  @media(min-width:481px) and (max-width:768px){{
    body{{padding:1rem}}
    .card{{padding:2rem 1.5rem}}
  }}
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
    <div class="endpoint"><span class="method get">GET</span><span class="ep-path">/chat</span><span class="ep-desc">Chatbot Web</span></div>
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
  <div style="text-align:center;margin:1.5rem 0 .5rem"><a href="/chat" class="chatbot-btn">Abrir Chatbot</a></div>
  <div class="footer">Chamber &mdash; github.com/soldierB0y/CHAMBER</div>
</div>
</body>
</html>"""
    return Response(html, mimetype="text/html")


@app.route("/chat", methods=["GET"])
def chatbot_ui():
    """Chatbot web accesible desde la red local."""
    chat_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>Chamber Chat</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{height:100%;overflow:hidden}}
body{{background:#0a0a0f;color:#e2e8f0;font-family:'Segoe UI',system-ui,sans-serif;display:flex;flex-direction:column;height:100vh;height:100dvh}}
.header{{background:#13131a;border-bottom:1px solid #1e1e2e;padding:.6rem .8rem;display:flex;align-items:center;flex-wrap:wrap;gap:.4rem .8rem;flex-shrink:0}}
.header .logo{{font-size:clamp(1.1rem,3.5vw,1.4rem);font-weight:800;letter-spacing:.06em;background:linear-gradient(135deg,#a78bfa,#60a5fa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}}
.header .subtitle{{color:#6b7280;font-size:.85rem}}
.header-right{{display:flex;align-items:center;gap:.5rem;margin-left:auto}}
.model-label{{font-size:.8rem;color:#6b7280;display:flex;align-items:center;gap:.3rem}}
#model-sel{{background:#1e1e2e;color:#e2e8f0;border:1px solid #2d2d44;border-radius:6px;padding:.35rem .5rem;font-size:.8rem;max-width:180px;-webkit-appearance:none}}
.header .status{{display:flex;align-items:center;gap:.4rem;font-size:.8rem;color:#9ca3af}}
.header .dot{{width:8px;height:8px;border-radius:50%;background:#22c55e;box-shadow:0 0 6px #22c55e;flex-shrink:0}}
.messages{{flex:1;overflow-y:auto;padding:.8rem .8rem 0;display:flex;flex-direction:column;gap:.6rem;-webkit-overflow-scrolling:touch;overscroll-behavior:contain}}
.msg{{max-width:80%;padding:.7rem .9rem;border-radius:12px;line-height:1.55;font-size:clamp(.85rem,2.5vw,.92rem);word-wrap:break-word;overflow-wrap:break-word;white-space:pre-wrap}}
.msg.user{{align-self:flex-end;background:#2d2d6b;border-bottom-right-radius:4px}}
.msg.assistant{{align-self:flex-start;background:#1e2233;border:1px solid #2d3348;border-bottom-left-radius:4px}}
.msg.assistant .thinking{{color:#6b7280;font-style:italic;font-size:.8rem}}
.msg.error{{align-self:center;background:#3b1111;border:1px solid #ef4444;color:#fca5a5;font-size:.85rem;text-align:center;max-width:95%}}
.input-area{{background:#13131a;border-top:1px solid #1e1e2e;padding:.6rem .8rem;display:flex;gap:.5rem;flex-shrink:0;padding-bottom:calc(.6rem + env(safe-area-inset-bottom,0px))}}
#msg-input{{flex:1;background:#1e1e2e;color:#e2e8f0;border:1px solid #2d2d44;border-radius:10px;padding:.65rem .9rem;font-size:16px;font-family:inherit;resize:none;outline:none;min-height:44px;max-height:120px;transition:border-color .2s;-webkit-appearance:none}}
#msg-input:focus{{border-color:#6c63ff}}
#send-btn{{background:linear-gradient(135deg,#a78bfa,#60a5fa);color:#0a0a0f;border:none;border-radius:10px;width:48px;min-width:48px;height:44px;font-size:1.1rem;font-weight:700;cursor:pointer;transition:opacity .2s;flex-shrink:0;display:flex;align-items:center;justify-content:center;-webkit-tap-highlight-color:transparent}}
#send-btn:hover{{opacity:.85}}
#send-btn:disabled{{opacity:.4;cursor:not-allowed}}
.typing-indicator{{align-self:flex-start;padding:.5rem 1rem;color:#6b7280;font-size:.8rem}}
.typing-indicator span{{animation:blink 1.4s infinite both}}
.typing-indicator span:nth-child(2){{animation-delay:.2s}}
.typing-indicator span:nth-child(3){{animation-delay:.4s}}
@keyframes blink{{0%,80%,100%{{opacity:0}}40%{{opacity:1}}}}
@media(max-width:480px){{
  .header{{padding:.5rem .6rem}}
  .header .subtitle{{display:none}}
  .msg{{max-width:92%}}
  #model-sel{{max-width:120px}}
  .messages{{padding:.6rem .5rem 0}}
  .input-area{{padding:.5rem}}
}}
@media(min-width:481px) and (max-width:768px){{
  .msg{{max-width:85%}}
  #model-sel{{max-width:150px}}
}}
</style>
</head>
<body>
<div class="header">
  <span class="logo">CHAMBER</span>
  <span class="subtitle">Chat</span>
  <div class="header-right">
    <label class="model-label">Modelo:
      <select id="model-sel"><option value="auto">auto</option></select>
    </label>
    <div class="status"><span class="dot"></span>Conectado</div>
  </div>
</div>
<div class="messages" id="messages"></div>
<div class="input-area">
  <textarea id="msg-input" rows="1" placeholder="Escribe un mensaje…"></textarea>
  <button id="send-btn">➤</button>
</div>
<script>
const BASE = window.location.origin;
const messagesEl = document.getElementById('messages');
const input = document.getElementById('msg-input');
const sendBtn = document.getElementById('send-btn');
const modelSel = document.getElementById('model-sel');
let conversation = [];
let sending = false;
let typeQueue = "";
let isTyping = false;
let fullText = "";
let assistantDiv = null;

function typeNext() {{
  if (typeQueue.length > 0) {{
    const chunk = typeQueue.substring(0, 2);
    fullText += chunk;
    typeQueue = typeQueue.substring(2);
    if (assistantDiv) assistantDiv.textContent = fullText;
    messagesEl.scrollTop = messagesEl.scrollHeight;
    setTimeout(typeNext, 12); // typist delay
  }} else {{
    isTyping = false;
  }}
}}

// Auto-resize textarea
input.addEventListener('input', () => {{
  input.style.height = 'auto';
  input.style.height = Math.min(input.scrollHeight, 150) + 'px';
}});

// Load models
fetch(BASE + '/v1/models').then(r => r.json()).then(data => {{
  (data.data || []).forEach(m => {{
    const opt = document.createElement('option');
    opt.value = m.id;
    opt.textContent = m.id;
    modelSel.appendChild(opt);
  }});
}}).catch(() => {{}});

function addMsg(role, content) {{
  const div = document.createElement('div');
  div.className = 'msg ' + role;
  div.textContent = content;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return div;
}}

function showTyping() {{
  const div = document.createElement('div');
  div.className = 'typing-indicator';
  div.id = 'typing';
  div.innerHTML = '<span>●</span><span>●</span><span>●</span>';
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}}

function hideTyping() {{
  const el = document.getElementById('typing');
  if (el) el.remove();
}}

async function sendMessage() {{
  const text = input.value.trim();
  if (!text || sending) return;
  sending = true;
  sendBtn.disabled = true;
  input.value = '';
  input.style.height = 'auto';

  addMsg('user', text);
  conversation.push({{role: 'user', content: text}});
  showTyping();

  try {{
    const resp = await fetch(BASE + '/v1/chat/completions', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{
        model: modelSel.value,
        messages: conversation,
        stream: true
      }})
    }});

    hideTyping();

    if (!resp.ok) {{
      const err = await resp.text();
      addMsg('error', 'Error: ' + resp.status + ' — ' + err);
      sending = false;
      sendBtn.disabled = false;
      return;
    }}

    assistantDiv = addMsg('assistant', '');
    fullText = '';
    typeQueue = '';
    isTyping = false;
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {{
      const {{done, value}} = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, {{stream: true}});
      const lines = buffer.split('\\n');
      buffer = lines.pop();
      for (const line of lines) {{
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith('data:')) continue;
        const payload = trimmed.slice(5).trim();
        if (payload === '[DONE]') continue;
        try {{
          const obj = JSON.parse(payload);
          const delta = obj.choices?.[0]?.delta?.content;
          if (delta) {{
            typeQueue += delta;
            if (!isTyping) {{
              isTyping = true;
              typeNext();
            }}
          }}
        }} catch(e) {{}}
      }}
    }}
    const checkTyping = setInterval(() => {{
      if (!isTyping) {{
        clearInterval(checkTyping);
        if (fullText) {{
          conversation.push({{role: 'assistant', content: fullText}});
        }}
      }}
    }}, 100);
  }} catch(e) {{
    hideTyping();
    addMsg('error', 'Error de conexión: ' + e.message);
  }}
  sending = false;
  sendBtn.disabled = false;
  input.focus();
}}

sendBtn.addEventListener('click', sendMessage);
input.addEventListener('keydown', (e) => {{
  if (e.key === 'Enter' && !e.shiftKey) {{
    e.preventDefault();
    sendMessage();
  }}
}});
input.focus();
</script>
</body>
</html>"""
    return Response(chat_html, mimetype="text/html")


@app.route("/v1/chat/completions", methods=["POST"])
@app.route("/v1/<level>/chat/completions", methods=["POST"])
def chat_completions(level=None):
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
    # Lógica de Pre-Procesamiento de Contexto
    token_count = calculate_payload_size(messages)
    priority_type = None

    if token_count > 10000:
        messages, was_cropped = smart_crop_messages(messages, limit=10000)
        if was_cropped:
            lang = _roulette.lang if _roulette else "es"
            msg = "✂ Contexto truncado (Smart Crop)" if lang == "es" else "✂ Context truncated (Smart Crop)"
            _log(msg)
        priority_type = "large_context"
    elif token_count < 2000:
        priority_type = "high_speed"

    kwargs = {
        "temperature": data.get("temperature"),
        "max_tokens": data.get("max_tokens"),
        "top_p": data.get("top_p"),
        "stream": stream_enabled,
        "priority_type": priority_type
    }

    if level:
        kwargs["tier"] = level

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

    # Fake stream (Typist Mode) para proveedores que no soportan streaming pero el cliente lo pidió
    if stream_enabled and "choices" in result and result.get("choices"):
        def generate_fake():
            import time, json, uuid
            content = result["choices"][0].get("message", {}).get("content", "")
            resp_id = result.get("id", f"chatcmpl-{uuid.uuid4().hex}")
            model_id = result.get("model", "chamber-proxy")
            
            chunk_size = 4
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i+chunk_size]
                payload = {
                    "id": resp_id,
                    "object": "chat.completion.chunk",
                    "model": model_id,
                    "choices": [{"delta": {"content": chunk}, "index": 0, "finish_reason": None}]
                }
                yield f"data: {json.dumps(payload)}\n\n"
                time.sleep(0.015)  # typist mode delay
                
            stop_payload = {
                "id": resp_id,
                "object": "chat.completion.chunk",
                "model": model_id,
                "choices": [{"delta": {}, "index": 0, "finish_reason": "stop"}]
            }
            yield f"data: {json.dumps(stop_payload)}\n\n"
            yield "data: [DONE]\n\n"

        return Response(
            generate_fake(),
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
@app.route("/v1/<level>/models", methods=["GET"])
def list_models(level=None):
    if not _roulette:
        return jsonify({"data": [], "object": "list"}), 200

    models = _roulette.list_models(tier=level)
    return jsonify({"data": models, "object": "list"})


@app.route("/v1/chat/completions", methods=["OPTIONS"])
@app.route("/v1/<level>/chat/completions", methods=["OPTIONS"])
@app.route("/v1/models", methods=["OPTIONS"])
@app.route("/v1/<level>/models", methods=["OPTIONS"])
def options(level=None):
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
        lang = self.roulette.lang if self.roulette else "es"
        if lang == "es":
            _log(f"🚀 Servidor API iniciado — http://localhost:{self.port}/v1")
            _log(f"🌐 Red local — http://{lan_ip}:{self.port}/v1")
        else:
            _log(f"🚀 API Server started — http://localhost:{self.port}/v1")
            _log(f"🌐 Local network — http://{lan_ip}:{self.port}/v1")
        self._server.serve_forever()

    def stop(self):
        self.running = False
        if hasattr(self, "_server") and self._server:
            self._server.shutdown()
            self._server.server_close()
        set_roulette(None)
