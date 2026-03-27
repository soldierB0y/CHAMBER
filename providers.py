"""
Definiciones de proveedores de LLM gratuitos.
Cada proveedor tiene: nombre, base_url, modelos recomendados,
formato de headers, y límites conocidos.
"""

import requests as http_requests

PROVIDERS = {
    "openrouter": {
        "name": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_header": "Authorization",
        "api_key_prefix": "Bearer ",
        "default_model": "meta-llama/llama-3.3-70b-instruct:free",
        "models": [
            "meta-llama/llama-3.3-70b-instruct:free",
            "google/gemma-3-27b-it:free",
            "google/gemma-3-12b-it:free",
            "mistralai/mistral-small-3.1-24b-instruct:free",
            "qwen/qwen3-4b:free",
            "qwen/qwen3-coder:free",
            "nousresearch/hermes-3-llama-3.1-405b:free",
        ],
        "extra_headers": {
            "HTTP-Referer": "https://github.com/Chamber",
            "X-Title": "Chamber",
        },
        "limits": "20 req/min, 50 req/day (200 con topup)",
        "signup_url": "https://openrouter.ai/",
        "notes": "Modelos con sufijo :free son gratuitos",
        "context_window": 128000,
        "speed_tier": "medium",
    },
    "groq": {
        "name": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_header": "Authorization",
        "api_key_prefix": "Bearer ",
        "default_model": "llama-3.3-70b-versatile",
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "llama-4-scout-17b-16e-instruct",
            "llama-4-maverick-17b-128e-instruct",
            "qwen-qwq-32b",
            "gemma2-9b-it",
        ],
        "extra_headers": {},
        "limits": "1,000-14,400 req/day según modelo",
        "signup_url": "https://console.groq.com/",
        "notes": "Muy rápido (hardware Groq LPU)",
        "context_window": 32768,
        "speed_tier": "high",
    },
    "cerebras": {
        "name": "Cerebras",
        "base_url": "https://api.cerebras.ai/v1",
        "api_key_header": "Authorization",
        "api_key_prefix": "Bearer ",
        "default_model": "llama-3.3-70b",
        "models": [
            "llama-3.3-70b",
            "llama3.1-8b",
        ],
        "extra_headers": {},
        "limits": "30 req/min, 14,400 req/day",
        "signup_url": "https://cloud.cerebras.ai/",
        "notes": "Inferencia ultra rápida",
        "context_window": 8192,
        "speed_tier": "high",
    },
    "cohere": {
        "name": "Cohere",
        "base_url": "https://api.cohere.com/v2",
        "api_key_header": "Authorization",
        "api_key_prefix": "Bearer ",
        "default_model": "command-r-plus-08-2024",
        "models": [
            "command-r-plus-08-2024",
            "command-r-08-2024",
            "command-r7b-12-2024",
            "command-a-03-2025",
            "c4ai-aya-expanse-32b",
        ],
        "extra_headers": {},
        "limits": "20 req/min, 1,000 req/mes",
        "signup_url": "https://cohere.com/",
        "notes": "API compatible con OpenAI en v2",
        "chat_endpoint": "/chat",
        "custom_format": "cohere",
        "context_window": 128000,
        "speed_tier": "medium",
    },
    "github_models": {
        "name": "GitHub Models",
        "base_url": "https://models.inference.ai.azure.com",
        "api_key_header": "Authorization",
        "api_key_prefix": "Bearer ",
        "default_model": "gpt-4o-mini",
        "models": [
            "gpt-4o-mini",
            "gpt-4o",
            "Meta-Llama-3.1-405B-Instruct",
            "Meta-Llama-3.1-8B-Instruct",
            "Mistral-small",
            "Phi-4",
        ],
        "extra_headers": {},
        "limits": "Depende del tier de GitHub Copilot",
        "signup_url": "https://github.com/marketplace/models",
        "notes": "Usar GitHub PAT como API key",
        "context_window": 128000,
        "speed_tier": "medium",
    },
    "mistral": {
        "name": "Mistral AI",
        "base_url": "https://api.mistral.ai/v1",
        "api_key_header": "Authorization",
        "api_key_prefix": "Bearer ",
        "default_model": "mistral-small-latest",
        "models": [
            "mistral-small-latest",
            "mistral-medium-latest",
            "open-mistral-nemo",
            "codestral-latest",
        ],
        "extra_headers": {},
        "limits": "1 req/s, 500K tokens/min",
        "signup_url": "https://console.mistral.ai/",
        "notes": "Plan Experiment gratis (requiere verificación tel.)",
        "context_window": 128000,
        "speed_tier": "medium",
    },
    "google_ai": {
        "name": "Google AI Studio",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "api_key_header": "Authorization",
        "api_key_prefix": "Bearer ",
        "default_model": "gemini-2.5-flash",
        "models": [
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemma-3-27b-it",
            "gemma-3-12b-it",
        ],
        "extra_headers": {},
        "limits": "Varía por modelo, 15-500 req/day",
        "signup_url": "https://aistudio.google.com/",
        "notes": "Compatible OpenAI vía endpoint /v1beta/openai",
        "context_window": 128000,
        "speed_tier": "medium",
    },
    "nvidia_nim": {
        "name": "NVIDIA NIM",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "api_key_header": "Authorization",
        "api_key_prefix": "Bearer ",
        "default_model": "meta/llama-3.1-8b-instruct",
        "models": [
            "meta/llama-3.1-8b-instruct",
            "meta/llama-3.1-70b-instruct",
            "mistralai/mistral-7b-instruct-v0.3",
            "google/gemma-2-9b-it",
        ],
        "extra_headers": {},
        "limits": "40 req/min",
        "signup_url": "https://build.nvidia.com/explore/discover",
        "notes": "Requiere verificación telefónica",
        "context_window": 32768,
        "speed_tier": "medium",
    },
    "sambanova": {
        "name": "SambaNova",
        "base_url": "https://api.sambanova.ai/v1",
        "api_key_header": "Authorization",
        "api_key_prefix": "Bearer ",
        "default_model": "Meta-Llama-3.3-70B-Instruct",
        "models": [
            "Meta-Llama-3.3-70B-Instruct",
            "Meta-Llama-3.1-8B-Instruct",
            "deepseek-ai/DeepSeek-V3-0324",
            "Qwen/Qwen3-32B",
        ],
        "extra_headers": {},
        "limits": "$5 créditos por 3 meses",
        "signup_url": "https://cloud.sambanova.ai/",
        "notes": "Créditos de prueba $5",
        "context_window": 32768,
        "speed_tier": "high",
    },
    "hyperbolic": {
        "name": "Hyperbolic",
        "base_url": "https://api.hyperbolic.xyz/v1",
        "api_key_header": "Authorization",
        "api_key_prefix": "Bearer ",
        "default_model": "meta-llama/Llama-3.3-70B-Instruct",
        "models": [
            "meta-llama/Llama-3.3-70B-Instruct",
            "meta-llama/Llama-3.1-8B-Instruct",
            "Qwen/Qwen2.5-72B-Instruct",
            "deepseek-ai/DeepSeek-V3-0324",
        ],
        "extra_headers": {},
        "limits": "$1 créditos de prueba",
        "signup_url": "https://app.hyperbolic.ai/",
        "notes": "Créditos de prueba $1",
        "context_window": 32768,
        "speed_tier": "high",
    },
    "fireworks": {
        "name": "Fireworks AI",
        "base_url": "https://api.fireworks.ai/inference/v1",
        "api_key_header": "Authorization",
        "api_key_prefix": "Bearer ",
        "default_model": "accounts/fireworks/models/llama-v3p1-8b-instruct",
        "models": [
            "accounts/fireworks/models/llama-v3p1-8b-instruct",
            "accounts/fireworks/models/llama-v3p3-70b-instruct",
            "accounts/fireworks/models/qwen2p5-72b-instruct",
        ],
        "extra_headers": {},
        "limits": "$1 créditos de prueba",
        "signup_url": "https://fireworks.ai/",
        "notes": "Créditos de prueba $1",
        "context_window": 32768,
        "speed_tier": "medium",
    },
    "nebius": {
        "name": "Nebius",
        "base_url": "https://api.studio.nebius.ai/v1",
        "api_key_header": "Authorization",
        "api_key_prefix": "Bearer ",
        "default_model": "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "models": [
            "meta-llama/Meta-Llama-3.1-8B-Instruct",
            "meta-llama/Meta-Llama-3.1-70B-Instruct",
            "Qwen/Qwen2.5-72B-Instruct",
        ],
        "extra_headers": {},
        "limits": "$1 créditos de prueba",
        "signup_url": "https://tokenfactory.nebius.com/",
        "notes": "Créditos de prueba $1",
        "context_window": 32768,
        "speed_tier": "medium",
    },
}

# ── Tiers de modelos: agrupa modelos equivalentes entre proveedores ──
MODEL_TIERS = {
    "large": {
        "openrouter": "meta-llama/llama-3.3-70b-instruct:free",
        "groq": "llama-3.3-70b-versatile",
        "cerebras": "llama-3.3-70b",
        "cohere": "command-r-plus-08-2024",
        "github_models": "gpt-4o",
        "mistral": "mistral-medium-latest",
        "google_ai": "gemini-2.5-flash",
        "nvidia_nim": "meta/llama-3.1-70b-instruct",
        "sambanova": "Meta-Llama-3.3-70B-Instruct",
        "hyperbolic": "meta-llama/Llama-3.3-70B-Instruct",
        "fireworks": "accounts/fireworks/models/llama-v3p3-70b-instruct",
        "nebius": "meta-llama/Meta-Llama-3.1-70B-Instruct",
    },
    "medium": {
        "openrouter": "google/gemma-3-27b-it:free",
        "groq": "qwen-qwq-32b",
        "cohere": "c4ai-aya-expanse-32b",
        "github_models": "Mistral-small",
        "mistral": "mistral-small-latest",
        "google_ai": "gemma-3-27b-it",
        "sambanova": "Qwen/Qwen3-32B",
        "hyperbolic": "Qwen/Qwen2.5-72B-Instruct",
        "fireworks": "accounts/fireworks/models/qwen2p5-72b-instruct",
        "nebius": "Qwen/Qwen2.5-72B-Instruct",
    },
    "small": {
        "openrouter": "google/gemma-3-12b-it:free",
        "groq": "llama-3.1-8b-instant",
        "cerebras": "llama3.1-8b",
        "cohere": "command-r7b-12-2024",
        "github_models": "gpt-4o-mini",
        "mistral": "open-mistral-nemo",
        "google_ai": "gemma-3-12b-it",
        "nvidia_nim": "meta/llama-3.1-8b-instruct",
        "sambanova": "Meta-Llama-3.1-8B-Instruct",
        "hyperbolic": "meta-llama/Llama-3.1-8B-Instruct",
        "fireworks": "accounts/fireworks/models/llama-v3p1-8b-instruct",
        "nebius": "meta-llama/Meta-Llama-3.1-8B-Instruct",
    },
}


def get_model_tier(provider_id: str, model_name: str) -> str:
    """Dado un proveedor y modelo, retorna su tier ('large', 'medium', 'small')."""
    for tier, mapping in MODEL_TIERS.items():
        if mapping.get(provider_id) == model_name:
            return tier
    return ""  # no tiene tier mapeado


def get_equivalent_model(target_provider: str, tier: str) -> str:
    """Retorna el modelo equivalente exacto para el tier dado, o cadena vacía."""
    return MODEL_TIERS.get(tier, {}).get(target_provider, "")


# Errores que indican que se agotaron los tokens/cuota
EXHAUSTION_ERRORS = [
    "rate_limit",
    "rate limit",
    "quota",
    "exceeded",
    "limit reached",
    "too many requests",
    "429",
    "insufficient_quota",
    "billing",
    "credits",
    "exhausted",
    "capacity",
    "context_length_exceeded",
    "context_window",
    "too long",
]

# HTTP status codes que indican agotamiento o rechazo por tamaño
EXHAUSTION_STATUS_CODES = [429, 413, 402, 403, 503]


def _parse_rate_headers(headers: dict) -> list:
    """Extrae info de rate-limit de headers HTTP estándar."""
    info = []
    mappings = {
        "x-ratelimit-limit-requests": "Límite req",
        "x-ratelimit-remaining-requests": "Req restantes",
        "x-ratelimit-limit-tokens": "Límite tokens",
        "x-ratelimit-remaining-tokens": "Tokens restantes",
        "x-ratelimit-reset-requests": "Reset req",
        "x-ratelimit-reset-tokens": "Reset tokens",
        "x-ratelimit-limit": "Límite",
        "x-ratelimit-remaining": "Restantes",
        "x-ratelimit-reset": "Reset",
        "retry-after": "Reintentar en",
        "x-credits-remaining": "Créditos restantes",
        "x-quota-remaining": "Cuota restante",
    }
    h_lower = {k.lower(): v for k, v in headers.items()}
    for key, label in mappings.items():
        val = h_lower.get(key)
        if val is not None:
            info.append(f"{label}: {val}")
    return info


def _fetch_openrouter(api_key: str) -> list:
    """OpenRouter: GET /api/v1/auth/key para créditos y límites."""
    info = []
    try:
        resp = http_requests.get(
            "https://openrouter.ai/api/v1/auth/key",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            label = data.get("label", "")
            if label:
                info.append(f"Key: {label}")
            limit = data.get("limit")
            if limit is not None:
                info.append(f"Límite de créditos: ${limit}")
            else:
                info.append("Límite de créditos: Ilimitado")
            usage = data.get("usage", 0)
            info.append(f"Créditos usados: ${usage:.4f}")
            if limit:
                remaining = limit - usage
                info.append(f"Créditos restantes: ${remaining:.4f}")
            rate_limit = data.get("rate_limit", {})
            if rate_limit:
                reqs = rate_limit.get("requests", 0)
                interval = rate_limit.get("interval", "")
                info.append(f"Rate limit: {reqs} req/{interval}")
        else:
            info.append(f"Error consultando API: HTTP {resp.status_code}")
    except Exception as e:
        info.append(f"Error de conexión: {e}")
    return info


def _fetch_groq(api_key: str) -> list:
    """Groq: hace GET /models y extrae headers de rate limit."""
    info = []
    try:
        resp = http_requests.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10
        )
        info.extend(_parse_rate_headers(dict(resp.headers)))
        if resp.status_code == 200:
            models = resp.json().get("data", [])
            info.append(f"Modelos disponibles: {len(models)}")
        else:
            info.append(f"HTTP {resp.status_code}: {resp.text[:100]}")
    except Exception as e:
        info.append(f"Error: {e}")
    return info


def _fetch_cohere(api_key: str) -> list:
    """Cohere: GET /v1/check-api-key y headers."""
    info = []
    try:
        resp = http_requests.post(
            "https://api.cohere.com/v1/check-api-key",
            headers={"Authorization": f"Bearer {api_key}",
                     "Content-Type": "application/json"},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            valid = data.get("valid", False)
            info.append(f"Key válida: {'Sí' if valid else 'No'}")
            owner = data.get("owner_id", "")
            if owner:
                info.append(f"Owner: {owner}")
            org = data.get("organization_id", "")
            if org:
                info.append(f"Organización: {org}")
        info.extend(_parse_rate_headers(dict(resp.headers)))
    except Exception as e:
        info.append(f"Error: {e}")
    return info


def _fetch_generic(api_key: str, prov: dict) -> list:
    """Consulta genérica: GET /models y extrae headers de rate limit."""
    info = []
    try:
        url = f"{prov['base_url']}/models"
        headers = {
            prov["api_key_header"]: f"{prov['api_key_prefix']}{api_key}",
            "Content-Type": "application/json",
        }
        headers.update(prov.get("extra_headers", {}))
        resp = http_requests.get(url, headers=headers, timeout=10)
        info.extend(_parse_rate_headers(dict(resp.headers)))
        if resp.status_code == 200:
            data = resp.json()
            models = data.get("data", data.get("models", []))
            if isinstance(models, list):
                info.append(f"Modelos disponibles: {len(models)}")
        elif resp.status_code == 401:
            info.append("API Key inválida o expirada")
        else:
            info.append(f"HTTP {resp.status_code}")
        if not info:
            info.append("Sin información de cuota disponible desde esta API")
    except Exception as e:
        info.append(f"Error: {e}")
    return info


# Mapeo de fetchers especializados
_PROVIDER_FETCHERS = {
    "openrouter": lambda key, prov: _fetch_openrouter(key),
    "groq": lambda key, prov: _fetch_groq(key),
    "cohere": lambda key, prov: _fetch_cohere(key),
}


def fetch_provider_info(provider_id: str, api_key: str) -> list:
    """
    Consulta la API del proveedor y retorna una lista de strings con la información
    disponible: créditos, tokens restantes, rate limits, resets, etc.
    """
    prov = PROVIDERS.get(provider_id)
    if not prov:
        return ["Proveedor no reconocido"]
    if not api_key or not api_key.strip():
        return ["No hay API Key configurada"]

    fetcher = _PROVIDER_FETCHERS.get(provider_id, _fetch_generic)
    info = fetcher(api_key.strip(), prov)

    if not info:
        info.append("No se obtuvo información adicional")
    return info
