# 🔫 CHAMBER

**Chamber** es una potente aplicación de escritorio diseñada para maximizar el uso de tokens gratuitos de múltiples proveedores de LLM, funcionando como un **Proxy Inteligente** que rota y procesa tus peticiones automáticamente.

## ✨ Características Principales

- **🔄 Rotación Automática (Revolver Mode)**: Cambia de proveedor instantáneamente si uno agota su cuota o falla.
- **🚀 Enrutamiento Dinámico**: Chamber analiza tu mensaje y elige el mejor proveedor:
    - **Contexto Grande**: Prioriza proveedores de **128k tokens** (Gemini, Mistral, Cohere) para archivos grandes.
    - **Alta Velocidad**: Prioriza proveedores ultra-rápidos (Groq, Cerebras) para consultas breves.
- **✂ Smart Crop (Manejo de Contexto)**: Si envías demasiado código, Chamber trunca inteligentemente la parte central para no romper los límites de las APIs gratuitas, manteniendo lo más crítico (cabecera y final).
- **🛸 Modo Gadget**: Una ventana flotante minimalista con Chat y **Monitor de Logs en tiempo real**.
- **📊 Estadísticas Detalladas**: Gráficos de consumo de tokens (Prompt/Completion) y conteo de errores por proveedor.
- **🔗 Compatibilidad Total**: Expone un endpoint local (`http://localhost:11411/v1`) compatible con la API de OpenAI.

---

## 🛠 Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/soldierB0y/CHAMBER.git
cd CHAMBER

# 2. Crear entorno virtual
python -m venv venv
venv\Scripts\activate     # Windows
source venv/bin/activate  # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Iniciar aplicación
python main.py
```

---

## 🔑 Proveedores Soportados

Chamber centraliza las mejores APIs gratuitas del mercado:

| Proveedor | Ventana Contexto | Velocidad | Nota |
|-----------|------------------|-----------|------|
| **Google AI Studio** | 128K+ | Media | Ideal para archivos grandes (Gemini) |
| **Groq** | 32K | **Ultra** | Inferencia instantánea LPU |
| **Mistral AI** | 128K | Alta | Plan Experiment gratuito |
| **Cerebras** | 8K | **Ultra** | Especializada en velocidad |
| **OpenRouter** | Varía | Alta | Acceso a modelos *:free* |
| **Cohere** | 128K | Media | Excelente para RAG y lógica |
| **GitHub Models** | 8-128K | Alta | Requiere GitHub PAT |
| **SambaNova** | 32K | **Ultra** | Velocidad de hardware dedicado |

---

## 🚀 Cómo Usar

### 1. Configuración
- Ve a la pestaña **Proveedores**.
- Haz clic en los enlaces para registrarte y obtener tus API Keys.
- Pega las keys, activa los proveedores y presiona **▶ Iniciar Servidor**.

### 2. Integración con Herramientas
Configura tu cliente favorito (VS Code, Cursor, Continue) con estos datos:
- **Base URL**: `http://localhost:11411/v1`
- **API Key**: `cualquier_valor` (no se valida localmente)
- **Modelo**: `auto` (Chamber decidirá el mejor) o `proveedor/modelo` (ej: `groq/llama-3.3-70b`).

### 3. Modo Gadget
Activa el **Modo Gadget** en Configuración para tener una pequeña ventana flotante sobre tus herramientas de desarrollo. Incluye una pestaña de **Logs** para ver qué está pasando "bajo el capó" (rotaciones, cuotas agotadas, etc.).

---

## 📂 Estructura del Proyecto

- `main.py`: Punto de entrada del programa.
- `gui.py`: Interfaz gráfica moderna (CustomTkinter) y Modo Gadget.
- `server.py`: Servidor Flask que emula la API de OpenAI y realiza el Smart Crop.
- `roulette.py`: Motor de rotación y lógica de enrutamiento dinámico.
- `providers.py`: Definiciones, límites y metadatos de los proveedores.
- `config.py`: Persistencia de configuraciones en JSON.

---

## 📦 Exportar a Ejecutable

Si deseas generar un `.exe` para Windows:
```bash
pip install pyinstaller
python build.py
```
El ejecutable aparecerá en la carpeta `dist/`.

---

**Chamber** — *Tu munición infinita de LLM gratuitos.* 🔫
