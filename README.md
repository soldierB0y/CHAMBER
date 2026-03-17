# 🔫 Chamber

Aplicación de escritorio que maximiza el uso de tokens gratuitos de múltiples plataformas de LLM, rotando automáticamente entre ellas como las cámaras de un revólver.

## Concepto

Te registras una vez en todas las plataformas que ofrecen APIs gratuitas, pegas tus API keys en Chamber, y la aplicación expone **un único endpoint local compatible con OpenAI** (`http://localhost:11411/v1`). Cuando un proveedor se agota, rota automáticamente al siguiente.

## Proveedores soportados

### Gratuitos permanentes
| Proveedor | Límites | Registro |
|-----------|---------|----------|
| **OpenRouter** | 50 req/día (modelos :free) | https://openrouter.ai/ |
| **Groq** | 1,000-14,400 req/día | https://console.groq.com/ |
| **Cerebras** | 14,400 req/día | https://cloud.cerebras.ai/ |
| **Cohere** | 1,000 req/mes | https://cohere.com/ |
| **GitHub Models** | Según tier Copilot | https://github.com/marketplace/models |
| **Mistral AI** | 500K tokens/min | https://console.mistral.ai/ |
| **Google AI Studio** | 15-500 req/día | https://aistudio.google.com/ |
| **NVIDIA NIM** | 40 req/min | https://build.nvidia.com/ |

### Con créditos de prueba
| Proveedor | Créditos | Registro |
|-----------|----------|----------|
| **SambaNova** | $5 (3 meses) | https://cloud.sambanova.ai/ |
| **Hyperbolic** | $1 | https://app.hyperbolic.ai/ |
| **Fireworks** | $1 | https://fireworks.ai/ |
| **Nebius** | $1 | https://tokenfactory.nebius.com/ |

## Instalación

```bash
# 1. Clonar o descargar el proyecto
cd AIRoulette

# 2. Crear entorno virtual (recomendado)
python -m venv venv
venv\Scripts\activate     # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar
python main.py
```

## Uso

### Paso 1: Configurar proveedores
1. Abre la app → pestaña **🔑 Proveedores**
2. Haz clic en el nombre de cada proveedor para ir a su página de registro
3. Obtén tu API Key y pégala en el campo correspondiente
4. Activa la casilla ✓ de cada proveedor que quieras usar
5. Haz clic en **💾 Guardar Config**

### Paso 2: Iniciar servidor
1. Haz clic en **▶ Iniciar Servidor**
2. El servidor se inicia en `http://localhost:11411/v1`

### Paso 3: Usar la API

#### Con Python (librería openai)
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11411/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="auto",
    messages=[{"role": "user", "content": "¡Hola! ¿Cómo estás?"}]
)

print(response.choices[0].message.content)
```

#### Con curl
```bash
curl http://localhost:11411/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"auto","messages":[{"role":"user","content":"Hola!"}]}'
```

#### Listar modelos disponibles
```bash
curl http://localhost:11411/v1/models
```

#### Health check
```bash
curl http://localhost:11411/health
```

### Configuración en herramientas

Puedes usar Chamber como backend en cualquier herramienta compatible con OpenAI:

- **Continue (VS Code)**: Base URL = `http://localhost:11411/v1`
- **Open WebUI**: Conexión OpenAI con URL `http://localhost:11411/v1`
- **LangChain**: `ChatOpenAI(base_url="http://localhost:11411/v1", api_key="x")`
- **Cualquier app OpenAI-compatible**: misma configuración

## Cómo funciona la rotación

```
Petición → [Proveedor 1] → ✓ Respuesta
                           ✗ Error 429/cuota
           [Proveedor 2] → ✓ Respuesta
                           ✗ Error 429/cuota
           [Proveedor 3] → ✓ Respuesta
           ...
           [Último]       → ✗ "Todos agotados"
```

- Detecta automáticamente errores HTTP 429, 402, 403, 503
- Detecta mensajes de error con palabras clave: "rate limit", "quota", "exceeded", etc.
- Al agotar un proveedor, lo marca y pasa al siguiente
- Botón **🔄 Reset Agotados** para reiniciar el ciclo

## Archivos

```
Chamber/
├── main.py          # Punto de entrada
├── gui.py           # Interfaz gráfica (customtkinter)
├── server.py        # Servidor API local (Flask)
├── roulette.py      # Motor de rotación
├── providers.py     # Definiciones de proveedores
├── config.py        # Gestión de configuración
├── logo.png         # Logo de la aplicación
├── requirements.txt # Dependencias
└── README.md        # Este archivo
```

La configuración se guarda en `~/.chamber/config.json`.
