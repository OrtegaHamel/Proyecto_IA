from pathlib import Path

from dotenv import load_dotenv
from langchain_core.documents import Document

from rag_indexer import indexar_corpus


ROOT = Path(__file__).resolve().parents[1]
RUTA_CORPUS = ROOT / "data" / "conocimiento_youtube.md"
RUTA_VECTORSTORE = ROOT / "data" / "vectorstore_youtube"

load_dotenv(ROOT / ".env")


def preparar_indice(
    ruta_corpus: Path = RUTA_CORPUS,
    ruta_vectorstore: Path = RUTA_VECTORSTORE,
):
    if not ruta_corpus.is_file():
        raise FileNotFoundError(f"No se encontro el corpus: {ruta_corpus}")
    if ruta_vectorstore.exists() and any(ruta_vectorstore.iterdir()):
        raise FileExistsError(
            f"El indice ya contiene datos: {ruta_vectorstore}. "
            "Para evitar duplicar chunks, elige otro directorio o limpia "
            "manualmente el indice existente antes de reconstruirlo."
        )

    documento = Document(
        page_content=ruta_corpus.read_text(encoding="utf-8"),
        metadata={"fuente": ruta_corpus.name},
    )
    vectorstore = indexar_corpus(
        corpus=[documento],
        persist_directory=str(ruta_vectorstore),
        es_documento=True,
    )
    total_chunks = len(vectorstore.get()["ids"])
    if total_chunks == 0:
        raise RuntimeError("La indexacion termino, pero no se guardaron chunks.")
    return total_chunks


if __name__ == "__main__":
    cantidad = preparar_indice()
    print(f"Indice RAG preparado: {cantidad} chunks en {RUTA_VECTORSTORE}")
