"""
Modo headless (sin GUI) para Chamber.
Inicia el servidor API directamente desde la línea de comandos.

Uso:
    python headless.py                  # puerto por defecto 11411
    python headless.py --port 8080      # puerto personalizado
"""

import sys
import os
import signal
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from providers import PROVIDERS
from config import load_config, is_enabled, get_api_key
from roulette import Roulette
from server import APIServer


def main():
    parser = argparse.ArgumentParser(description="Chamber - Servidor headless")
    parser.add_argument("--port", type=int, default=None, help="Puerto del servidor")
    args = parser.parse_args()

    config = load_config()
    port = args.port or config.get("server_port", 11411)

    def log(msg):
        print(f"  {msg}")

    # Check active providers
    active = [
        pid for pid in PROVIDERS
        if is_enabled(config, pid) and get_api_key(config, pid).strip()
    ]

    if not active:
        print("\n  ╔══════════════════════════════════════════════════╗")
        print("  ║  No hay proveedores configurados y habilitados  ║")
        print("  ║  Ejecuta 'python main.py' para configurar       ║")
        print("  ╚══════════════════════════════════════════════════╝\n")
        sys.exit(1)

    print(f"\n  ┌─────────────────────────────────────────────┐")
    print(f"  │           Chamber — Modo Headless             │")
    print(f"  └─────────────────────────────────────────────┘")
    print(f"  Proveedores activos: {len(active)}")
    for pid in active:
        print(f"    • {PROVIDERS[pid]['name']}")
    print()

    roulette = Roulette(config, on_log=log)
    server = APIServer(roulette, port=port, on_log=log)
    server.start()

    print(f"  Servidor: http://localhost:{port}/v1")
    print(f"  Health:   http://localhost:{port}/health")
    print(f"  Ctrl+C para detener\n")

    try:
        signal.pause()
    except AttributeError:
        # Windows no tiene signal.pause(), usar input
        try:
            input("  Presiona Enter para detener...\n")
        except KeyboardInterrupt:
            pass

    server.stop()
    print("\n  Servidor detenido.")


if __name__ == "__main__":
    main()
