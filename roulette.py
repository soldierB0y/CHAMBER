"""
Motor de rotación tipo revólver (Chamber).
Gestiona el ciclo entre proveedores y el reenvío de peticiones.
"""
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
    get_global_tier, increment_stat, save_config
)

L10N = {
    "es": {
        "rotating_priority": "🔄 Rotando por prioridad '{p}': {n}",
        "rotating_to": "🔄 Rotando a: {n} [{m}] (tier: {t})",
        "rotating_to_simple": "🔄 Rotando a: {n}",
        "exhausted_tier": "⚠ Todos los proveedores agotados en tier '{t}'",
        "downgrading": "⬇ Bajando a tier '{t}': {n} [{m}]",
        "all_exhausted": "❌ Todos los proveedores agotados",
        "waiting_backoff": "⏳ Esperando {s:.1f}s (Backoff) para liberar cuota...",
        "invalid_resp": "⚠ {n}: respuesta sin 'choices', rotando",
        "no_providers": "No hay proveedores configurados y habilitados",
        "quota_exhausted": "Todos los proveedores están agotados. Intenta más tarde o agrega más proveedores.",
    },
    "en": {
        "rotating_priority": "🔄 Rotating by priority '{p}': {n}",
        "rotating_to": "🔄 Rotating to: {n} [{m}] (tier: {t})",
        "rotating_to_simple": "🔄 Rotating to: {n}",
        "exhausted_tier": "⚠ All providers exhausted in tier '{t}'",
        "downgrading": "⬇ Downgrading to tier '{t}': {n} [{m}]",
        "all_exhausted": "❌ All providers exhausted",
        "waiting_backoff": "⏳ Waiting {s:.1f}s (Backoff) to free quota...",
        "invalid_resp": "⚠ {n}: response without 'choices', rotating",
        "no_providers": "No providers configured and enabled",
        "quota_exhausted": "All providers are exhausted. Try later or add more providers.",
    }
}


class Roulette:
    def __init__(self, config: dict, on_switch=None, on_log=None):
        self.config = config
        self.lang = config.get("language", "es")
        if self.lang not in L10N: self.lang = "es"
        self.lock = threading.Lock()
        self.current_index = 0
        self.on_switch = on_switch  # callback(provider_id, reason)
        self.on_log = on_log        # callback(message)
        self._exhausted = set()     # proveedores agotados en esta sesión
        self._current_tier = ""      # tier activo durante rotación
        self._build_active_list()

    def _t(self, key, **kwargs):
        return L10N.get(self.lang, L10N["es"]).get(key, key).format(**kwargs)

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

    _TIER_DOWNGRADE = {"large": ["medium", "small"], "medium": ["small"], "small": []}

    def _rotate(self, reason: str, priority_type: str = None):
        """Rota al siguiente proveedor disponible, manteniendo el nivel del modelo y respetando prioridades."""
        old_id = self.active_providers[self.current_index % len(self.active_providers)]
        self._exhausted.add(old_id)
        self._log(f"⚠ {PROVIDERS[old_id]['name']}: {reason}")

        # Intentar rotar respetando priority_type si existe
        if priority_type:
            next_id = self._find_next_available(priority_type=priority_type)
            if next_id:
                self._log(self._t("rotating_priority", p=priority_type, n=PROVIDERS[next_id]['name']))
                if self.on_switch:
                    self.on_switch(next_id, reason)
                return True

        if not self._current_tier:
            cfg_tier = get_global_tier(self.config)
            if cfg_tier and cfg_tier != "auto":
                self._current_tier = cfg_tier
            else:
                current_model = get_selected_model(self.config, old_id)
                tier = get_model_tier(old_id, current_model)
                if tier:
                    self._current_tier = tier

        if self._current_tier:
            next_id = self._find_next_at_tier(self._current_tier)
            if next_id:
                eq = get_equivalent_model(next_id, self._current_tier)
                self._log(self._t("rotating_to", n=PROVIDERS[next_id]['name'], m=eq, t=self._current_tier))
                if self.on_switch:
                    self.on_switch(next_id, reason)
                return True

            for lower_tier in self._TIER_DOWNGRADE.get(self._current_tier, []):
                next_id = self._find_next_at_tier(lower_tier)
                if next_id:
                    eq = get_equivalent_model(next_id, lower_tier)
                    self._log(self._t("exhausted_tier", t=self._current_tier))
                    self._log(self._t("downgrading", t=lower_tier, n=PROVIDERS[next_id]['name'], m=eq))
                    self._current_tier = lower_tier
                    if self.on_switch:
                        self.on_switch(next_id, reason)
                    return True
        else:
            next_id = self._find_next_available()
            if next_id:
                self._log(self._t("rotating_to_simple", n=PROVIDERS[next_id]['name']))
                if self.on_switch:
                    self.on_switch(next_id, reason)
                return True

        self._log(self._t("all_exhausted"))
        return False

    def _find_next_at_tier(self, tier: str):
        start = self.current_index
        for i in range(len(self.active_providers)):
            idx = (start + 1 + i) % len(self.active_providers)
            pid = self.active_providers[idx]
            if pid not in self._exhausted and get_equivalent_model(pid, tier):
                self.current_index = idx
                return pid
        return None

    def _find_next_available(self, priority_type: str = None):
        start = self.current_index
        for i in range(len(self.active_providers)):
            idx = (start + i) % len(self.active_providers)
            pid = self.active_providers[idx]
            if pid in self._exhausted:
                continue
                
            if priority_type == "large_context":
                if PROVIDERS[pid].get("context_window", 0) >= 128000:
                    self.current_index = idx
                    return pid
            elif priority_type == "high_speed":
                if PROVIDERS[pid].get("speed_tier") == "high":
                    self.current_index = idx
                    return pid
            elif not priority_type:
                self.current_index = idx
                return pid
        
        # Si no hay ninguno con esa prioridad, devolver el primero disponible sin filtro
        if priority_type:
            return self._find_next_available(priority_type=None)
        return None

    def reset_exhausted(self):
        with self.lock:
            self._exhausted.clear()

    def chat_completion(self, messages: list, **kwargs) -> dict:
        is_stream = kwargs.get("stream", False)
        priority_type = kwargs.get("priority_type")

        with self.lock:
            self._build_active_list()

        if not self.active_providers:
            return {
                "error": {
                    "message": self._t("no_providers"),
                    "type": "no_providers",
                }
            }

        self._current_tier = ""
        max_attempts = len(self.active_providers)
        
        for attempt in range(max_attempts):
            # --- LÓGICA DE BACKOFF EXPONENCIAL ---
            if attempt > 0:
                # Espera progresiva: 1.5s, 3s, 6s... limitado a 10s máximo
                wait_time = min(0.75 * (2 ** attempt), 10.0)
                self._log(self._t("waiting_backoff", s=wait_time))
                time.sleep(wait_time)
            # -------------------------------------

            if attempt == 0 and priority_type:
                provider_id = self._find_next_available(priority_type=priority_type)
            else:
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
                
                status_code = result.get("_status_code", 0)
                body = json.dumps(result)
                if self._is_exhaustion_error(status_code, body):
                    increment_stat(self.config, provider_id, "errors")
                    error_msg = result.get("error", {}).get("message", "Cuota agotada")
                    increment_stat(self.config, provider_id, "last_error", error_msg)
                    save_config(self.config)
                    with self.lock:
                        if not self._rotate(f"Cuota/Context limit (HTTP {status_code})", priority_type=priority_type):
                            break
                else:
                    increment_stat(self.config, provider_id, "errors")
                    save_config(self.config)
                    return result
                continue

            result = self._call_provider(provider_id, prov, messages, **kwargs)

            if result.get("_success"):
                if "choices" not in result or not result.get("choices"):
                    self._log(self._t("invalid_resp", n=prov['name']))
                    increment_stat(self.config, provider_id, "errors")
                    error_msg = result.get("error", {}).get("message", "Respuesta inválida")
                    increment_stat(self.config, provider_id, "last_error", error_msg)
                    save_config(self.config)
                    with self.lock:
                        if not self._rotate(f"Respuesta inválida de {prov['name']}", priority_type=priority_type):
                            break
                    continue

                result.pop("_success", None)
                result.pop("_status_code", None)
                increment_stat(self.config, provider_id, "requests")
                usage = result.get("usage", {})
                if usage:
                    pt = usage.get("prompt_tokens", 0)
                    ct = usage.get("completion_tokens", 0)
                    tt = usage.get("total_tokens", pt + ct)
                    if pt: increment_stat(self.config, provider_id, "prompt_tokens", pt)
                    if ct: increment_stat(self.config, provider_id, "completion_tokens", ct)
                    if tt: increment_stat(self.config, provider_id, "total_tokens", tt)
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
                    if not self._rotate(f"Cuota/Context limit (HTTP {status_code})", priority_type=priority_type):
                        break
            else:
                result.pop("_success", None)
                result.pop("_status_code", None)
                increment_stat(self.config, provider_id, "errors")
                save_config(self.config)
                return result

        return {
            "error": {
                "message": self._t("quota_exhausted"),
                "type": "all_exhausted",
            }
        }

    def _resolve_model(self, provider_id: str, **kwargs) -> str:
        if kwargs.get("model"):
            return kwargs["model"]
        tier = self._current_tier
        if not tier:
            cfg_tier = get_global_tier(self.config)
            if cfg_tier and cfg_tier != "auto":
                tier = cfg_tier
        if tier:
            model = get_equivalent_model(provider_id, tier)
            if model:
                return model
        return get_selected_model(self.config, provider_id)

    def _call_provider(self, provider_id: str, prov: dict, messages: list, **kwargs) -> dict:
        api_key = get_api_key(self.config, provider_id)
        model = self._resolve_model(provider_id, **kwargs)

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
            "stream": False
        }
        for key in ("temperature", "max_tokens", "top_p"):
            if key in kwargs and kwargs[key] is not None:
                payload[key] = kwargs[key]

        self._log(f"→ {prov['name']} [{model}]")

        try:
            resp = http_requests.post(url, json=payload, headers=headers, timeout=120)
            try:
                data = resp.json()
                if isinstance(data, list):
                    data = {"data": data}
            except ValueError:
                data = {"error": {"message": resp.text}}
            data["_status_code"] = resp.status_code
            data["_success"] = 200 <= resp.status_code < 300
            return data
        except Exception as e:
            return {"_success": False, "_status_code": 0, "error": {"message": str(e)}}

    def _call_provider_stream(self, provider_id: str, prov: dict, messages: list, **kwargs) -> dict:
        api_key = get_api_key(self.config, provider_id)
        model = self._resolve_model(provider_id, **kwargs)

        if prov.get("custom_format") == "cohere":
            normal_kwargs = kwargs.copy()
            normal_kwargs["stream"] = False
            return self._call_cohere(provider_id, prov, api_key, model, messages, **normal_kwargs)

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
            try:
                data = resp.json()
                if isinstance(data, list):
                    data = {"data": data}
            except ValueError:
                data = {"error": {"message": resp.text}}
            data["_status_code"] = resp.status_code
            data["_success"] = False
            return data
        except Exception as e:
            return {"_success": False, "_status_code": 0, "error": {"message": str(e)}}

    def _call_cohere(self, provider_id: str, prov: dict, api_key: str,
                     model: str, messages: list, **kwargs) -> dict:
        url = f"{prov['base_url']}/chat"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": model, "messages": messages}
        for key in ("temperature", "max_tokens", "top_p"):
            if key in kwargs and kwargs[key] is not None:
                payload[key] = kwargs[key]

        self._log(f"→ {prov['name']} [{model}]")

        try:
            resp = http_requests.post(url, json=payload, headers=headers, timeout=120)
            try:
                data = resp.json()
                if isinstance(data, list):
                    data = {"data": data}
            except ValueError:
                data = {"error": {"message": resp.text}}

            if 200 <= resp.status_code < 300 and "message" in data:
                content = "".join(c.get("text", "") for c in data["message"].get("content", []) if c.get("type") == "text")
                return {
                    "_success": True,
                    "_status_code": resp.status_code,
                    "id": data.get("id", ""),
                    "object": "chat.completion",
                    "model": model,
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": data.get("finish_reason", "stop")}],
                    "usage": data.get("usage", {}),
                }
            data["_status_code"] = resp.status_code
            data["_success"] = False
            return data
        except Exception as e:
            return {"_success": False, "_status_code": 0, "error": {"message": str(e)}}

    def list_models(self, tier: str = None) -> list:
        models = []
        for pid in self.active_providers:
            prov = PROVIDERS[pid]
            if tier:
                eq = get_equivalent_model(pid, tier)
                if eq:
                    models.append({"id": f"{pid}/{eq}", "object": "model", "owned_by": prov["name"], "provider": pid, "model": eq})
            else:
                for m in prov["models"]:
                    models.append({"id": f"{pid}/{m}", "object": "model", "owned_by": prov["name"], "provider": pid, "model": m})
        return models