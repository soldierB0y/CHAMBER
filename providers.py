"""
Definiciones de proveedores de LLM gratuitos.
Cada proveedor tiene: nombre, base_url, modelos recomendados,
formato de headers, y límites conocidos.
"""

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
    """Retorna el modelo equivalente en el proveedor destino para el tier dado."""
    model = MODEL_TIERS.get(tier, {}).get(target_provider)
    if model:
        return model
    # Fallback: buscar en tiers adyacentes
    fallback = {"large": ["medium", "small"], "medium": ["large", "small"], "small": ["medium", "large"]}
    for fb_tier in fallback.get(tier, []):
        model = MODEL_TIERS.get(fb_tier, {}).get(target_provider)
        if model:
            return model
    # Último recurso: modelo default del proveedor
    return PROVIDERS[target_provider]["default_model"]


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
]

# HTTP status codes que indican agotamiento
EXHAUSTION_STATUS_CODES = [429, 402, 403, 503]
