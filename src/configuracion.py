"""Configuracion compartida del Copiloto de YouTube."""
import json
import os
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "data"
LOCAL = RAIZ / ".local"
DOCS = RAIZ / "docs"
NOMBRE_PROYECTO = "copiloto_youtube"


def guardar_json(ruta: str | Path, datos: Any) -> None:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


def cargar_configuracion_real(requiere_embedding: bool = True) -> dict[str, str | None]:
    from dotenv import load_dotenv

    load_dotenv(RAIZ / ".env", override=False)
    clave = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    modelo = os.getenv("GEMINI_MODEL")
    embedding = os.getenv("GEMINI_EMBEDDING_MODEL")
    if not clave or not modelo or (requiere_embedding and not embedding):
        raise ValueError("Configura clave y modelo en .env; el RAG requiere tambien GEMINI_EMBEDDING_MODEL")
    return {"api_key": clave, "modelo": modelo, "embedding": embedding}


def crear_modelo():
    from langchain_google_genai import ChatGoogleGenerativeAI
    cfg = cargar_configuracion_real(requiere_embedding=False)
    return ChatGoogleGenerativeAI(model=cfg["modelo"], api_key=cfg["api_key"],
                                 temperature=0, timeout=30, max_retries=0)


def ruta_indice(real: bool = False) -> Path:
    if real:
        valor = Path(os.getenv("RAG_INDEX_DIR", str(DATOS / "vectorstore_youtube")))
        return valor if valor.is_absolute() else RAIZ / valor
    return DATOS / "vectorstore_youtube"