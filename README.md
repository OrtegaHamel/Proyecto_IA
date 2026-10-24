# Proyecto Copiloto para creadores de YouTube — Especialización en Desarrollo con IA Generativa (Accenture)

Este proyecto es una herramienta para YouTubers o agencias de medios que toma un tema y genera la estructura del guión, la estrategia de SEO y la estimación de retención. Utiliza la API de Gemini para generar respuestas estructuradas, incluye un ejemplo de petición, una comparación de modelos y una comprobación de consistencia para un banco de prompts.  

Actualmente en desarrollo.

## Requisitos

- Python 3.12 o superior.
- Una clave de API de Gemini.
- Conexión a Internet para instalar dependencias y consultar la API.

## Instalación

Clona el repositorio y entra en su carpeta:

```powershell
git clone https://github.com/OrtegaHamel/Proyecto_IA.git
cd Proyecto_IA
```

Crea un entorno virtual e instala las dependencias. En Windows con PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

En macOS o Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Configuración de Gemini

1. Obtén una clave de API de Gemini desde [Google AI Studio](https://aistudio.google.com/app/apikey).
2. En la raíz del repositorio, crea tu archivo `.env` a partir de la plantilla:

   ```powershell
   Copy-Item .env.example .env
   ```

   En macOS o Linux, usa `cp .env.example .env`.
3. Abre `.env` y reemplaza el valor de ejemplo:

   ```dotenv
   GEMINI_API_KEY=pega_aqui_tu_clave
   ```

No compartas ni subas `.env` al repositorio. Git ya lo excluye; `.env.example` es solo una plantilla y no debe contener claves reales.

## Ejecución

Ejecuta los comandos desde la raíz del repositorio para que Python encuentre `.env` y los módulos del proyecto.

En Windows, usa el Python del entorno virtual:

```powershell
.\.venv\Scripts\python.exe src\consumir_gemini.py
.\.venv\Scripts\python.exe src\evaluacion_modelos.py
.\.venv\Scripts\python.exe src\consistencia.py
```

En macOS o Linux, activa `.venv` como se indica arriba y ejecuta:

```bash
python src/consumir_gemini.py
python src/evaluacion_modelos.py
python src/consistencia.py
```

Los programas son:

- `consumir_gemini.py`: envía una petición de prueba a Gemini y muestra la respuesta, la latencia y el costo estimado.
- `evaluacion_modelos.py`: consulta tres modelos cuatro veces cada uno y resume latencia y costo.
- `consistencia.py`: ejecuta los tres prompts del banco hasta tres veces cada uno y guarda el resumen en `src/prompts/registro_resultados.json`.

Las ejecuciones consumen solicitudes de tu cuenta de Gemini y pueden generar costos. Para comprobar la configuración con una sola petición, empieza por `consumir_gemini.py`.

## Estructura del proyecto

```text
.
├── docs/                 # Documentación y recursos del proyecto
├── src/
│   ├── prompts/           # Banco de prompts y resultados
│   ├── consistencia.py    # Comprobación de respuestas del banco
│   ├── consumir_gemini.py # Cliente y ejemplo de petición a Gemini
│   └── evaluacion_modelos.py
├── tests/                 # Espacio reservado para pruebas
├── .env.example           # Plantilla de configuración
└── requirements.txt       # Dependencias de Python
```

## Reglas que se mantienen durante todo el programa

- Ningún secreto (contraseña, llave de API, token) va escrito directamente en el código ni en ningún archivo que se suba al repositorio.
- Cada proyecto nuevo tiene su propio entorno virtual: no se comparten dependencias entre proyectos distintos.
- Todo el trabajo que se entrega en este programa vive en un repositorio de GitHub, sin excepción.
