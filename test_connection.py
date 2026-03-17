"""
Script de prueba para verificar que el servidor Chamber funciona.
Primero asegúrate de que el servidor esté corriendo (python main.py o python headless.py).
"""

import requests
import json
import sys

BASE = "http://localhost:11411"


def test_health():
    print("─── Health Check ───")
    try:
        r = requests.get(f"{BASE}/health", timeout=5)
        data = r.json()
        print(f"  Status:     {data['status']}")
        print(f"  Activos:    {data['active_providers']}")
        print(f"  Actual:     {data['current_provider']}")
        return data["status"] == "ok"
    except requests.ConnectionError:
        print("  ✗ No se pudo conectar. ¿Está el servidor corriendo?")
        return False


def test_models():
    print("\n─── Modelos Disponibles ───")
    r = requests.get(f"{BASE}/v1/models", timeout=5)
    data = r.json()
    models = data.get("data", [])
    print(f"  {len(models)} modelos disponibles")
    for m in models[:5]:
        print(f"    • {m['id']} ({m['owned_by']})")
    if len(models) > 5:
        print(f"    ... y {len(models) - 5} más")


def test_chat():
    print("\n─── Chat Completion ───")
    payload = {
        "model": "auto",
        "messages": [
            {"role": "user", "content": "Dime hola en una línea corta."}
        ],
        "max_tokens": 50,
    }
    r = requests.post(
        f"{BASE}/v1/chat/completions",
        json=payload,
        timeout=120
    )

    if r.status_code == 200:
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        model = data.get("model", "?")
        print(f"  Modelo:     {model}")
        print(f"  Respuesta:  {content[:200]}")
        print("  ✓ Funcionando correctamente")
    elif r.status_code == 502:
        data = r.json()
        err = data.get("error", {}).get("message", "Error desconocido")
        print(f"  ✗ Error del proveedor: {err}")
    else:
        print(f"  ✗ HTTP {r.status_code}: {r.text[:200]}")


if __name__ == "__main__":
    print("╔═══════════════════════════════════════╗")
    print("║       Chamber — Test de conexión       ║")
    print("╚═══════════════════════════════════════╝\n")

    if not test_health():
        print("\nInicia el servidor primero:")
        print("  python main.py      (con GUI)")
        print("  python headless.py  (sin GUI)")
        sys.exit(1)

    test_models()
    test_chat()
    print()
