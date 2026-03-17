"""
Gestión de configuración persistente.
Guarda API keys, proveedores habilitados, modelo preferido por proveedor,
y estadísticas de uso.
"""

import json
import os
from pathlib import Path
from providers import PROVIDERS

CONFIG_DIR = Path.home() / ".chamber"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Migrar config antigua si existe
_OLD_DIR = Path.home() / ".airoulette"
if _OLD_DIR.exists() and not CONFIG_DIR.exists():
    _OLD_DIR.rename(CONFIG_DIR)

DEFAULT_CONFIG = {
    "server_port": 11411,
    "providers_order": list(PROVIDERS.keys()),
    "api_keys": {},           # {provider_id: "sk-..."}
    "enabled": {},            # {provider_id: True/False}
    "selected_models": {},    # {provider_id: "model-name"}
    "stats": {},              # {provider_id: {"requests": N, "errors": N, "last_error": ""}}
}


def load_config() -> dict:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
        # Merge con defaults para campos nuevos
        for key, val in DEFAULT_CONFIG.items():
            if key not in saved:
                saved[key] = val
        return saved
    return json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy


def save_config(config: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_api_key(config: dict, provider_id: str) -> str:
    return config.get("api_keys", {}).get(provider_id, "")


def set_api_key(config: dict, provider_id: str, key: str):
    config.setdefault("api_keys", {})[provider_id] = key


def is_enabled(config: dict, provider_id: str) -> bool:
    return config.get("enabled", {}).get(provider_id, False)


def set_enabled(config: dict, provider_id: str, enabled: bool):
    config.setdefault("enabled", {})[provider_id] = enabled


def get_selected_model(config: dict, provider_id: str) -> str:
    custom = config.get("selected_models", {}).get(provider_id, "")
    if custom:
        return custom
    prov = PROVIDERS.get(provider_id)
    return prov["default_model"] if prov else ""


def set_selected_model(config: dict, provider_id: str, model: str):
    config.setdefault("selected_models", {})[provider_id] = model


STAT_DEFAULTS = {
    "requests": 0, "errors": 0, "last_error": "",
    "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
}


def increment_stat(config: dict, provider_id: str, field: str, value=1):
    stats = config.setdefault("stats", {})
    pstats = stats.setdefault(provider_id, dict(STAT_DEFAULTS))
    if field in ("requests", "errors", "prompt_tokens", "completion_tokens", "total_tokens"):
        pstats[field] = pstats.get(field, 0) + value
    else:
        pstats[field] = value


def get_stats(config: dict, provider_id: str) -> dict:
    defaults = dict(STAT_DEFAULTS)
    saved = config.get("stats", {}).get(provider_id, {})
    defaults.update(saved)
    return defaults


def reset_stats(config: dict, provider_id: str = None):
    if provider_id:
        config.get("stats", {}).pop(provider_id, None)
    else:
        config["stats"] = {}
