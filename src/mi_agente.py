import json
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda, RunnableWithMessageHistory
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field


load_dotenv()

modelo = ChatGoogleGenerativeAI(model="gemini-3.6-flash")
RUTA_TRAZAS = Path(__file__).resolve().parent.parent / "trazas_agente.jsonl"


class ArgumentosDuracionGuion(BaseModel):
    palabras: int = Field(ge=1, description="Cantidad de palabras del guion.")


class ArgumentosEstructuraVideo(BaseModel):
    duracion_minutos: int = Field(
        ge=1,
        le=180,
        description="Duración objetivo del video, en minutos.",
    )


class ArgumentosRevisionTitulo(BaseModel):
    titulo: str = Field(min_length=1, description="Título propuesto para el video.")
    palabra_clave: str = Field(
        default="",
        description="Palabra clave principal que se quiere posicionar.",
    )


@tool(args_schema=ArgumentosDuracionGuion)
def calcular_duracion_guion(palabras: int) -> str:
    """Estima cuánto durará la narración según la cantidad de palabras."""
    minutos_minimos = palabras / 160
    minutos_maximos = palabras / 130
    return (
        f"Para {palabras} palabras, la narración duraría aproximadamente "
        f"entre {minutos_minimos:.1f} y {minutos_maximos:.1f} minutos "
        "(a un ritmo orientativo de 130-160 palabras por minuto)."
    )


def _formatear_tiempo(segundos: int) -> str:
    minutos, segundos_restantes = divmod(segundos, 60)
    return f"{minutos:02d}:{segundos_restantes:02d}"


@tool(args_schema=ArgumentosEstructuraVideo)
def crear_estructura_video(duracion_minutos: int) -> str:
    """Propone bloques temporales para planificar un video y cuidar el ritmo."""
    duracion_segundos = duracion_minutos * 60
    segundos_gancho = min(5, duracion_segundos)
    segundos_restantes = duracion_segundos - segundos_gancho
    bloques = [
        ("Gancho inicial (primeros 5 segundos)", segundos_gancho),
        ("Contexto y promesa", round(segundos_restantes * 0.12)),
        ("Desarrollo principal", round(segundos_restantes * 0.68)),
        ("Resumen o conclusión", round(segundos_restantes * 0.12)),
    ]

    resultado = ["Estructura orientativa (ajustar al tema y al estilo del canal):"]
    inicio = 0
    for nombre, duracion_bloque in bloques:
        fin = inicio + duracion_bloque
        resultado.append(
            f"- {_formatear_tiempo(inicio)}-{_formatear_tiempo(fin)}: {nombre}"
        )
        inicio = fin

    resultado.append(
        f"- {_formatear_tiempo(inicio)}-{_formatear_tiempo(duracion_segundos)}: "
        "Llamada a la acción"
    )
    resultado.append(
        "Considera introducir cambios de ritmo, ejemplos o preguntas cada "
        "30-60 segundos. Esta es una guía de edición, no una predicción de "
        "retención real."
    )
    return "\n".join(resultado)


@tool(args_schema=ArgumentosRevisionTitulo)
def revisar_titulo(titulo: str, palabra_clave: str = "") -> str:
    """Revisa longitud y presencia natural de la palabra clave en un título."""
    longitud = len(titulo.strip())
    observaciones = [f"El título tiene {longitud} caracteres."]

    if longitud > 70:
        observaciones.append(
            "Considera acortarlo para que la idea principal sea más fácil de leer."
        )
    elif longitud < 25:
        observaciones.append(
            "Es breve; comprueba que comunique con claridad el tema y el beneficio."
        )
    else:
        observaciones.append(
            "La longitud es razonable; prioriza claridad y una promesa fiel al video."
        )

    if palabra_clave.strip():
        if palabra_clave.casefold() in titulo.casefold():
            observaciones.append("Incluye la palabra clave indicada.")
        else:
            observaciones.append(
                "No incluye la palabra clave indicada; intégrala solo si suena natural."
            )

    observaciones.append("La revisión no garantiza un CTR ni una posición en búsquedas.")
    return " ".join(observaciones)


herramientas = [
    calcular_duracion_guion,
    crear_estructura_video,
    revisar_titulo,
]

historiales: dict[str, InMemoryChatMessageHistory] = {}


def obtener_historial(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in historiales:
        historiales[session_id] = InMemoryChatMessageHistory()
    return historiales[session_id]


prompt_agente = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Eres un copiloto en español para creadores y equipos de YouTube. "
            "Ayudas con preproducción, guiones, SEO y planificación de retención. "
            "Puedes proponer títulos, descripciones y etiquetas; diseñar un gancho "
            "para los primeros segundos, bloques de guion y una llamada a la acción; "
            "y definir audiencia, propuesta de valor y ángulo diferenciador. "
            "Usa las herramientas cuando aporten cálculos o revisiones concretas. "
            "Usa el historial para respetar el nicho, la audiencia y el tono del "
            "creador sin volver a preguntar lo ya indicado. Distingue las "
            "recomendaciones de las métricas reales: no inventes datos, tendencias "
            "ni resultados de rendimiento, y aclara que la retención solo puede "
            "medirse con analíticas del video publicado. No afirmes que el creador "
            "ofrece archivos descargables, productos o episodios futuros salvo que "
            "lo haya indicado; redacta llamadas a la acción sin prometer recursos "
            "no confirmados. Adapta el nivel de detalle a la solicitud y entrega "
            "respuestas claras y accionables.",
        ),
        MessagesPlaceholder("chat_history"),
        ("human", "{entrada}"),
        MessagesPlaceholder("agent_scratchpad"),
    ]
)

agente = create_tool_calling_agent(modelo, herramientas, prompt_agente)
ejecutor_agente = AgentExecutor(
    agent=agente,
    tools=herramientas,
    verbose=True,
    return_intermediate_steps=True,
)

def normalizar_salida(resultado: dict) -> dict:
    salida = resultado.get("output")
    if isinstance(salida, str):
        return resultado

    if isinstance(salida, list):
        textos = [
            parte["text"]
            for parte in salida
            if isinstance(parte, dict) and isinstance(parte.get("text"), str)
        ]
        if textos:
            return {**resultado, "output": "\n".join(textos)}

    raise TypeError("El agente devolvió una salida con un formato no compatible.")



cadena_agente = ejecutor_agente | RunnableLambda(normalizar_salida)

agente_con_memoria = RunnableWithMessageHistory(
    cadena_agente,
    obtener_historial,
    input_messages_key="entrada",
    history_messages_key="chat_history",
    output_messages_key="output",
)


def registrar_traza(session_id: str, entrada: str, resultado: dict) -> None:
    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "entrada": entrada,
        "acciones": [
            {
                "herramienta": accion.tool,
                "argumentos": accion.tool_input,
                "observacion": observacion,
            }
            for accion, observacion in resultado.get("intermediate_steps", [])
        ],
        "respuesta_final": resultado.get("output", ""),
    }

    with RUTA_TRAZAS.open("a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(registro, ensure_ascii=False, default=str) + "\n")


def conversar(session_id: str, entrada: str) -> str:
    resultado = agente_con_memoria.invoke(
        {"entrada": entrada},
        config={"configurable": {"session_id": session_id}},
    )
    registrar_traza(session_id, entrada, resultado)
    return resultado["output"]


if __name__ == "__main__":
    id_sesion = "creador_local"
    print("Copiloto para creadores de YouTube. Escribe 'salir' para terminar.")

    while True:
        entrada_usuario = input("\nTú: ").strip()
        if entrada_usuario.casefold() in {"salir", "exit", "quit"}:
            break
        if not entrada_usuario:
            continue

        print(f"\nCopiloto: {conversar(id_sesion, entrada_usuario)}")
