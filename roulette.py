"""
Motor de rotación tipo revólver (Chamber).
Gestiona el ciclo entre proveedores y el reenvío de peticiones.
"""

import json
import time
import threading
import requests as http_requests
from providers import (
    PROVIDERS, EXHAUSTION_ERRORS, EXHAUSTION_STATUS_CODES,
    get_model_tier, get_equivalent_model,
)
from config import (
    get_api_key, is_enabled, get_selected_model,
    increment_stat, save_config
)


class Roulette:
    def __init__(self, config: dict, on_switch=None, on_log=None):
        self.config = config
        self.lock = threading.Lock()
        self.current_index = 0
        self.on_switch = on_switch  # callback(provider_id, reason)
        self.on_log = on_log        # callback(message)
        self._exhausted = set()     # proveedores agotados en esta sesión
        self._current_tier = ""      # tier activo durante rotación
        self._build_active_list()

    def _build_active_list(self):
        """Construye la lista de proveedores activos (con key + habilitados)."""
        order = self.config.get("providers_order", list(PROVIDERS.keys()))
        self.active_providers = [
            pid for pid in order
            if pid in PROVIDERS
            and is_enabled(self.config, pid)
            and get_api_key(self.config, pid).strip()
        ]
        if self.current_index >= len(self.active_providers):
            self.current_index = 0

    def refresh(self):
        with self.lock:
            self._build_active_list()
            self._exhausted.clear()

    def get_current_provider_id(self) -> str:
        with self.lock:
            if not self.active_providers:
                return ""
            return self.active_providers[self.current_index % len(self.active_providers)]

    def get_active_count(self) -> int:
        return len(self.active_providers)

    def _log(self, msg: str):
        if self.on_log:
            self.on_log(msg)

    def _is_exhaustion_error(self, status_code: int, body: str) -> bool:
        if status_code in EXHAUSTION_STATUS_CODES:
            return True
        body_lower = body.lower()
        return any(err in body_lower for err in EXHAUSTION_ERRORS)

    def _rotate(self, reason: str):
        """Rota al siguiente proveedor disponible, manteniendo el nivel del modelo."""
        old_id = self.active_providers[self.current_index % len(self.active_providers)]
        self._exhausted.add(old_id)
        self._log(f"⚠ {PROVIDERS[old_id]['name']}: {reason}")

        # Detectar tier del modelo actual si aún no hay uno fijado
        if not self._current_tier:
            current_model = get_selected_model(self.config, old_id)
            tier = get_model_tier(old_id, current_model)
            if tier:
                self._current_tier = tier

        # Buscar siguiente no agotado
        for _ in range(len(self.active_providers)):
            self.current_index = (self.current_index + 1) % len(self.active_providers)
            next_id = self.active_providers[self.current_index]
            if next_id not in self._exhausted:
                if self._current_tier:
                    eq = get_equivalent_model(next_id, self._current_tier)
                    self._log(f"🔄 Rotando a: {PROVIDERS[next_id]['name']} [{eq}] (tier: {self._current_tier})")
                else:
                    self._log(f"🔄 Rotando a: {PROVIDERS[next_id]['name']}")
                if self.on_switch:
                    self.on_switch(next_id, reason)
                return True

        self._log("❌ Todos los proveedores agotados")
        return False

    def reset_exhausted(self):
        with self.lock:
            self._exhausted.clear()

    def chat_completion(self, messages: list, **kwargs) -> dict:
        """
        Envía una petición de chat completion rotando proveedores si falla.
        Retorna la respuesta del proveedor o un error si todos están agotados.
        Si stream=True en kwargs, retorna dict con '_stream' key conteniendo el generador SSE.
        """
        is_stream = kwargs.get("stream", False)

        with self.lock:
            self._build_active_list()

        if not self.active_providers:
            return {
                "error": {
                    "message": "No hay proveedores configurados y habilitados",
                    "type": "no_providers",
                }
            }

        # Reset tier al inicio de cada petición nueva
        self._current_tier = ""

        max_attempts = len(self.active_providers)
        for attempt in range(max_attempts):
            provider_id = self.get_current_provider_id()
            if not provider_id:
                break

            prov = PROVIDERS[provider_id]

            if is_stream:
                result = self._call_provider_stream(provider_id, prov, messages, **kwargs)
                if result.get("_success"):
                    increment_stat(self.config, provider_id, "requests")
                    save_config(self.config)
                    return result
                # Stream failed, try rotation
                status_code = result.get("_status_code", 0)
                body = json.dumps(result)
                if self._is_exhaustion_error(status_code, body):
                    increment_stat(self.config, provider_id, "errors")
                    error_msg = result.get("error", {}).get("message", "Cuota agotada")
                    increment_stat(self.config, provider_id, "last_error", error_msg)
                    save_config(self.config)
                    with self.lock:
                        if not self._rotate(f"Cuota/Rate limit (HTTP {status_code})"):
                            break
                else:
                    increment_stat(self.config, provider_id, "errors")
                    save_config(self.config)
                    return result
                continue

            result = self._call_provider(provider_id, prov, messages, **kwargs)

            if result.get("_success"):
                # Validate response has expected structure
                if "choices" not in result or not result.get("choices"):
                    self._log(f"⚠ {prov['name']}: respuesta sin 'choices', rotando")
                    increment_stat(self.config, provider_id, "errors")
                    error_msg = result.get("error", {}).get("message", "Respuesta inválida")
                    increment_stat(self.config, provider_id, "last_error", error_msg)
                    save_config(self.config)
                    with self.lock:
                        if not self._rotate(f"Respuesta inválida de {prov['name']}"):
                            break
                    continue

                result.pop("_success", None)
                result.pop("_status_code", None)
                increment_stat(self.config, provider_id, "requests")
                # Track token usage
                usage = result.get("usage", {})
                if usage:
                    pt = usage.get("prompt_tokens", 0)
                    ct = usage.get("completion_tokens", 0)
                    tt = usage.get("total_tokens", pt + ct)
                    if pt:
                        increment_stat(self.config, provider_id, "prompt_tokens", pt)
                    if ct:
                        increment_stat(self.config, provider_id, "completion_tokens", ct)
                    if tt:
                        increment_stat(self.config, provider_id, "total_tokens", tt)
                save_config(self.config)
                return result

            status_code = result.get("_status_code", 0)
            body = json.dumps(result)

            if self._is_exhaustion_error(status_code, body):
                increment_stat(self.config, provider_id, "errors")
                error_msg = result.get("error", {}).get("message", "Cuota agotada")
                increment_stat(self.config, provider_id, "last_error", error_msg)
                save_config(self.config)

                with self.lock:
                    if not self._rotate(f"Cuota/Rate limit (HTTP {status_code})"):
                        break
            else:
                # Error no relacionado con cuota, no rotar
                result.pop("_success", None)
                result.pop("_status_code", None)
                increment_stat(self.config, provider_id, "errors")
                save_config(self.config)
                return result

        return {
            "error": {
                "message": "Todos los proveedores están agotados. Intenta más tarde o agrega más proveedores.",
                "type": "all_exhausted",
            }
        }

    def _resolve_model(self, provider_id: str, **kwargs) -> str:
        """Resuelve qué modelo usar: explícito > tier de rotación > seleccionado."""
        if kwargs.get("model"):
            return kwargs["model"]
        if self._current_tier:
            return get_equivalent_model(provider_id, self._current_tier)
        return get_selected_model(self.config, provider_id)

    def _call_provider(self, provider_id: str, prov: dict, messages: list, **kwargs) -> dict:
        """Hace la llamada HTTP al proveedor."""
        api_key = get_api_key(self.config, provider_id)
        model = self._resolve_model(provider_id, **kwargs)

        # Cohere usa formato diferente
        if prov.get("custom_format") == "cohere":
            return self._call_cohere(provider_id, prov, api_key, model, messages, **kwargs)

        url = f"{prov['base_url']}/chat/completions"
        headers = {
            prov["api_key_header"]: f"{prov['api_key_prefix']}{api_key}",
            "Content-Type": "application/json",
        }
        headers.update(prov.get("extra_headers", {}))

        payload = {
            "model": model,
            "messages": messages,
        }
        # Pasar parámetros opcionales
        for key in ("temperature", "max_tokens", "top_p"):
            if key in kwargs and kwargs[key] is not None:
                payload[key] = kwargs[key]
        # Never pass stream=True to non-stream call
        payload["stream"] = False

        self._log(f"→ {prov['name']} [{model}]")

        try:
            resp = http_requests.post(url, json=payload, headers=headers, timeout=120)
            try:
                data = resp.json()
            except ValueError:
                data = {"error": {"message": resp.text}}
            data["_status_code"] = resp.status_code
            data["_success"] = 200 <= resp.status_code < 300
            if data["_success"] and "choices" not in data:
                self._log(f"⚠ {prov['name']}: respuesta sin 'choices': {str(data)[:200]}")
            return data
        except http_requests.exceptions.Timeout:
            return {"_success": False, "_status_code": 408,
                    "error": {"message": "Timeout de conexión"}}
        except http_requests.exceptions.ConnectionError:
            return {"_success": False, "_status_code": 0,
                    "error": {"message": "Error de conexión"}}
        except Exception as e:
            return {"_success": False, "_status_code": 0,
                    "error": {"message": str(e)}}

    def _call_provider_stream(self, provider_id: str, prov: dict, messages: list, **kwargs) -> dict:
        """Hace la llamada HTTP con stream=True y retorna el response raw."""
        api_key = get_api_key(self.config, provider_id)
        model = self._resolve_model(provider_id, **kwargs)

        if prov.get("custom_format") == "cohere":
            return {"_success": False, "_status_code": 0,
                    "error": {"message": "Cohere no soporta streaming en Chamber"}}

        url = f"{prov['base_url']}/chat/completions"
        headers = {
            prov["api_key_header"]: f"{prov['api_key_prefix']}{api_key}",
            "Content-Type": "application/json",
        }
        headers.update(prov.get("extra_headers", {}))

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        for key in ("temperature", "max_tokens", "top_p"):
            if key in kwargs and kwargs[key] is not None:
                payload[key] = kwargs[key]

        self._log(f"→ {prov['name']} [{model}] (stream)")

        try:
            resp = http_requests.post(url, json=payload, headers=headers, timeout=120, stream=True)
            if 200 <= resp.status_code < 300:
                return {"_success": True, "_stream": resp.iter_lines(), "_raw_resp": resp}
            # Error — read body for error detection
            try:
                data = resp.json()
            except ValueError:
                data = {"error": {"message": resp.text}}
            data["_status_code"] = resp.status_code
            data["_success"] = False
            return data
        except http_requests.exceptions.Timeout:
            return {"_success": False, "_status_code": 408,
                    "error": {"message": "Timeout de conexión"}}
        except http_requests.exceptions.ConnectionError:
            return {"_success": False, "_status_code": 0,
                    "error": {"message": "Error de conexión"}}
        except Exception as e:
            return {"_success": False, "_status_code": 0,
                    "error": {"message": str(e)}}

    def _call_cohere(self, provider_id: str, prov: dict, api_key: str,
                     model: str, messages: list, **kwargs) -> dict:
        """Llama a Cohere usando su formato de chat compatible con OpenAI."""
        url = f"{prov['base_url']}/chat"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": messages,
        }
        for key in ("temperature", "max_tokens", "top_p"):
            if key in kwargs and kwargs[key] is not None:
                payload[key] = kwargs[key]

        self._log(f"→ {prov['name']} [{model}]")

        try:
            resp = http_requests.post(url, json=payload, headers=headers, timeout=120)
            try:
                data = resp.json()
            except ValueError:
                data = {"error": {"message": resp.text}}

            # Convertir respuesta Cohere v2 a formato OpenAI
            if 200 <= resp.status_code < 300 and "message" in data:
                content = ""
                msg = data.get("message", {})
                if "content" in msg and isinstance(msg["content"], list):
                    content = "".join(
                        c.get("text", "") for c in msg["content"]
                        if c.get("type") == "text"
                    )
                return {
                    "_success": True,
                    "_status_code": resp.status_code,
                    "id": data.get("id", ""),
                    "object": "chat.completion",
                    "model": model,
                    "choices": [{
                        "index": 0,
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": data.get("finish_reason", "stop"),
                    }],
                    "usage": data.get("usage", {}),
                }

            data["_status_code"] = resp.status_code
            data["_success"] = False
            return data
        except Exception as e:
            return {"_success": False, "_status_code": 0,
                    "error": {"message": str(e)}}

    def list_models(self) -> list:
        """Retorna todos los modelos disponibles de los proveedores activos."""
        models = []
        for pid in self.active_providers:
            prov = PROVIDERS[pid]
            for m in prov["models"]:
                models.append({
                    "id": f"{pid}/{m}",
                    "object": "model",
                    "owned_by": prov["name"],
                    "provider": pid,
                    "model": m,
                })
        return models
