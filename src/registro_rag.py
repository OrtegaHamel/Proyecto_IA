import argparse
import json
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from rag_indexer import cargar_vectorstore, formatear_contexto


ROOT = Path(__file__).resolve().parents[1]
VECTORSTORE_DEFAULT = ROOT / "data" / "vectorstore_youtube"
REGISTRO_DEFAULT = ROOT / "registros_latencia_costo.jsonl"

load_dotenv(ROOT / ".env")

PROMPT_TEMPLATE = """Responde la pregunta usando SOLO el contexto de abajo. Cita la \
fuente de cada afirmacion con su numero entre corchetes, como [1]. Si el contexto no \
alcanza para responder, dilo explicitamente en vez de inventar.

Contexto:
{contexto}

Pregunta: {pregunta}

Respuesta:"""


@contextmanager
def medir(tiempos: dict[str, float], etapa: str):
    inicio = time.perf_counter()
    yield
    tiempos[etapa] = time.perf_counter() - inicio


def _leer_tarifas() -> tuple[float | None, float | None]:
    entrada = os.getenv("GEMINI_INPUT_USD_PER_1M", "").strip()
    salida = os.getenv("GEMINI_OUTPUT_USD_PER_1M", "").strip()

    if bool(entrada) != bool(salida):
        raise ValueError(
            "Configura juntas GEMINI_INPUT_USD_PER_1M y "
            "GEMINI_OUTPUT_USD_PER_1M usando las tarifas actuales del modelo."
        )
    if not entrada:
        return None, None

    tarifa_entrada = float(entrada)
    tarifa_salida = float(salida)
    if tarifa_entrada < 0 or tarifa_salida < 0:
        raise ValueError("Las tarifas de Gemini no pueden ser negativas.")
    return tarifa_entrada, tarifa_salida


def calcular_costo(
    tokens_entrada: int,
    tokens_salida: int,
    tarifa_entrada_x1M: float | None,
    tarifa_salida_x1M: float | None,
) -> float | None:
    if tarifa_entrada_x1M is None or tarifa_salida_x1M is None:
        return None

    costo_entrada = tokens_entrada / 1_000_000 * tarifa_entrada_x1M
    costo_salida = tokens_salida / 1_000_000 * tarifa_salida_x1M
    return round(costo_entrada + costo_salida, 8)


def registrar_consulta(
    vectorstore,
    pregunta: str,
    k: int = 3,
    chat_model=None,
    tarifa_entrada_x1M: float | None = None,
    tarifa_salida_x1M: float | None = None,
) -> dict:
    if not pregunta.strip():
        raise ValueError("La pregunta no puede estar vacia.")
    if k < 1:
        raise ValueError("k debe ser un entero mayor que cero.")

    tiempos: dict[str, float] = {}
    embeddings = vectorstore.embeddings
    if embeddings is None:
        raise ValueError("El vector store no tiene una funcion de embeddings.")

    with medir(tiempos, "embed"):
        embedding_pregunta = embeddings.embed_query(pregunta)

    with medir(tiempos, "busqueda"):
        chunks = vectorstore.similarity_search_by_vector(embedding_pregunta, k=k)

    with medir(tiempos, "armado_prompt"):
        contexto, citas = formatear_contexto(chunks)
        prompt = PROMPT_TEMPLATE.format(contexto=contexto, pregunta=pregunta)

    modelo = chat_model or ChatGoogleGenerativeAI(
        model=os.getenv("RAG_CHAT_MODEL", "gemini-3.5-flash-lite")
    )
    with medir(tiempos, "generacion"):
        respuesta = modelo.invoke(prompt)

    uso = respuesta.usage_metadata
    tokens = dict(uso) if uso else None
    if tarifa_entrada_x1M is None and tarifa_salida_x1M is None:
        tarifa_entrada, tarifa_salida = _leer_tarifas()
    elif tarifa_entrada_x1M is None or tarifa_salida_x1M is None:
        raise ValueError("Configura ambas tarifas o deja ambas sin configurar.")
    else:
        tarifa_entrada, tarifa_salida = tarifa_entrada_x1M, tarifa_salida_x1M
    costo_generacion = None
    if tokens is not None:
        costo_generacion = calcular_costo(
            tokens_entrada=tokens.get("input_tokens", 0),
            tokens_salida=tokens.get("output_tokens", 0),
            tarifa_entrada_x1M=tarifa_entrada,
            tarifa_salida_x1M=tarifa_salida,
        )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pregunta": pregunta,
        "k": k,
        "modelo": getattr(modelo, "model", os.getenv("RAG_CHAT_MODEL", "gemini-3.5-flash-lite")),
        "respuesta_generada": respuesta.content,
        "citas_disponibles": citas,
        "tiempos_ms": {
            etapa: round(segundos * 1000, 2)
            for etapa, segundos in tiempos.items()
        },
        "tiempo_total_ms": round(sum(tiempos.values()) * 1000, 2),
        "tokens": tokens,
        "costo_generacion_estimado_usd": costo_generacion,
        "tarifas_usd_por_1m_tokens": {
            "entrada": tarifa_entrada,
            "salida": tarifa_salida,
        },
    }


def guardar_registro_jsonl(
    registro: dict,
    ruta_archivo: str | Path = REGISTRO_DEFAULT,
) -> Path:
    ruta = Path(ruta_archivo)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return ruta


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mide latencia y tokens de una consulta RAG del copiloto."
    )
    parser.add_argument("pregunta", help="Pregunta que se enviara al flujo RAG.")
    parser.add_argument("--k", type=int, default=3, help="Chunks que se recuperaran.")
    parser.add_argument(
        "--vectorstore",
        type=Path,
        default=VECTORSTORE_DEFAULT,
        help="Directorio del indice Chroma.",
    )
    parser.add_argument(
        "--salida",
        type=Path,
        default=REGISTRO_DEFAULT,
        help="Archivo JSONL al que se agrega el registro.",
    )
    args = parser.parse_args()

    if not args.vectorstore.is_dir():
        raise FileNotFoundError(
            f"No existe el indice RAG en {args.vectorstore}. "
            "Ejecuta primero src\\preparar_rag_youtube.py."
        )

    vectorstore = cargar_vectorstore(str(args.vectorstore))
    registro = registrar_consulta(vectorstore, args.pregunta, args.k)
    ruta = guardar_registro_jsonl(registro, args.salida)
    print(json.dumps(registro, indent=2, ensure_ascii=False))
    print(f"\nRegistro agregado a: {ruta}")


if __name__ == "__main__":
    main()
