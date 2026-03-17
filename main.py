"""
Chamber - Maximiza tus tokens gratuitos de LLM
Punto de entrada principal.
"""

import sys
import os

# Asegurar que el directorio del script esté en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui import ChamberApp


def main():
    app = ChamberApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
