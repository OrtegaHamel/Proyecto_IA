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
.\.venv\Scripts\python.exe src\mi_agente.py
.\.venv\Scripts\python.exe -m src.registro_prompts
.\.venv\Scripts\python.exe -m src.matriz_riesgos
.\.venv\Scripts\python.exe -m src.grafo_supervision --verificar
```

En macOS o Linux, activa `.venv` como se indica arriba y ejecuta:

```bash
python src/consumir_gemini.py
python src/evaluacion_modelos.py
python src/consistencia.py
python src/mi_agente.py
python -m src.registro_prompts
python -m src.matriz_riesgos
python -m src.grafo_supervision --verificar
```

Los programas son:

- `consumir_gemini.py`: envía una petición de prueba a Gemini y muestra la respuesta, la latencia y el costo estimado.
- `evaluacion_modelos.py`: consulta tres modelos cuatro veces cada uno y resume latencia y costo.
- `consistencia.py`: ejecuta los tres prompts del banco hasta tres veces cada uno y guarda el resumen en `src/prompts/registro_resultados.json`.
- `mi_agente.py`: inicia un copiloto interactivo con memoria de conversación para apoyar en guiones, SEO y planificación de retención. Guarda las trazas localmente en `trazas_agente.jsonl`, incluyendo la huella del prompt utilizado.
- `registro_prompts.py`: conserva dos versiones del prompt del copiloto, sus huellas y el diff en `docs/`. Al cambiar `PROMPT_V2` y ejecutar el modulo, registra el cambio sin sobrescribir el historial.
- `grafo_supervision.py`: pausa la activacion de una version nueva hasta que una persona revise el diff y apruebe o rechace su huella. `--verificar` prueba ambos caminos sin llamar a Gemini ni cambiar la version activa. El prompt aprobado se carga al iniciar `mi_agente.py`; reinicia el proceso para aplicar un cambio.
- `matriz_riesgos.py`: genera la matriz del copiloto en `docs/matriz_riesgos.md` y `docs/matriz_riesgos.json`, con responsables y controles pendientes diferenciados.

Para solicitar una aprobacion real, primero ejecuta `registro_prompts.py` despues de editar `PROMPT_V2` y luego ejecuta `python -m src.grafo_supervision` (en Windows, `.\.venv\Scripts\python.exe -m src.grafo_supervision`). El grafo muestra el diff, se pausa y solo actualiza `.local/prompt_activo.json` si apruebas la huella propuesta. `--verificar` solo prueba los caminos y no modifica la version activa.

Las ejecuciones consumen solicitudes de tu cuenta de Gemini y pueden generar costos. Para comprobar la configuración con una sola petición, empieza por `consumir_gemini.py`.

La version activa y la ultima decision de supervision se guardan en `.local/`, que no se sube a Git. Las trazas del agente y del medidor RAG contienen entradas y respuestas; mantenlas locales y no las compartas con datos reales sin revisarlas.

## Flujo RAG: preparación y medición

El flujo de prueba del Copiloto de YouTube usa `data/conocimiento_youtube.md` como corpus y almacena el índice Chroma local en `data/vectorstore_youtube/` (no se sube a Git). Configura `.env` con tu llave antes de indexar:

```powershell
.\.venv\Scripts\python.exe src\preparar_rag_youtube.py
```

Mide consultas reales de una en una. Cada ejecución agrega una línea JSONL a `registros_latencia_costo.jsonl`:

```powershell
.\.venv\Scripts\python.exe src\registro_rag.py "¿Qué es la retención de audiencia?" --k 3
.\.venv\Scripts\python.exe src\registro_rag.py "¿Qué caracteriza a un buen título para YouTube?" --k 3
.\.venv\Scripts\python.exe src\registro_rag.py "¿Cómo ayuda la preproducción en un canal de YouTube?" --k 3
.\.venv\Scripts\python.exe src\registro_rag.py "¿Qué caracteriza a un buen título para YouTube?" --k 6
```

Estas consultas cubren tres preguntas del conjunto de evaluación de `src/precision.py` y repiten la del título con `k=6` para compararla con `k=3`. El registro desglosa `embed`, `busqueda`, `armado_prompt` y `generacion`, junto con la latencia total, las citas y los tokens que devuelve Gemini. Para estimar el costo de generación, completa `GEMINI_INPUT_USD_PER_1M` y `GEMINI_OUTPUT_USD_PER_1M` en `.env` con las tarifas vigentes para el modelo indicado en `RAG_CHAT_MODEL`; si no se configuran, el costo queda como `null`. El adaptador de embeddings no expone aquí el uso de tokens de la consulta, por lo que este costo no incluye el embedding.

La primera vez crea el índice con llamadas reales al servicio de embeddings. El script evita agregar chunks de nuevo si ya hay un índice en la ruta elegida. Las consultas de medición también llaman a Gemini y no se ejecutan automáticamente durante las pruebas unitarias.

## Dataset de ejemplos de personalización

`data/ejemplos_personalizacion.jsonl` contiene 200 pares sintéticos de entrada y salida, distribuidos en cuatro tareas: SEO, estructura de guion, análisis de propuesta de valor y planificación de retención (50 ejemplos por tarea). Cada línea incluye `id`, `categoria`, `entrada`, `salida` y `sintetico`.

Los registros se prepararon localmente, sin llamadas a la API ni tuning. Después se hizo una llamada de inferencia a Gemini para revisar el documento y una muestra estratificada de 20 ejemplos: el proveedor reportó 5.867 tokens de entrada y 80 de salida. Con tarifas de $0,30/$2,50 por millón de tokens de entrada/salida, su costo estimado es $0,0019601 USD (asumiendo precios por millón). La revisión no encontró contradicciones, pero los ejemplos siguen siendo borradores sintéticos: revisa su exactitud y apruébalos antes de usarlos para entrenar. Se mantienen separados de `resultados_metricas.json`, que contiene resultados de evaluación.

## Estructura del proyecto

```text
.
├── data/                 # Corpus RAG y ejemplos sintéticos de personalización
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
