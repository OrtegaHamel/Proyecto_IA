import json
from types import SimpleNamespace

import pytest

from registro_rag import guardar_registro_jsonl, registrar_consulta


class EmbeddingsFalsos:
    def __init__(self):
        self.preguntas = []

    def embed_query(self, pregunta):
        self.preguntas.append(pregunta)
        return [0.1, 0.2]


class VectorStoreFalso:
    def __init__(self):
        self.embeddings = EmbeddingsFalsos()
        self.busquedas = []
        self.chunk = SimpleNamespace(
            page_content="La estructura del video incluye un gancho inicial.",
            metadata={"fuente": "conocimiento_youtube.md"},
        )

    def similarity_search_by_vector(self, embedding, k):
        self.busquedas.append((embedding, k))
        return [self.chunk]


class ModeloFalso:
    model = "modelo-de-prueba"

    def __init__(self):
        self.prompts = []
        self.contenido = "Empieza con un gancho [1]."

    def invoke(self, prompt):
        self.prompts.append(prompt)
        return SimpleNamespace(
            content=self.contenido,
            usage_metadata={
                "input_tokens": 100,
                "output_tokens": 20,
                "total_tokens": 120,
            },
        )


def test_registrar_consulta_mide_etapas_y_calcula_costo_de_generacion():
    vectorstore = VectorStoreFalso()
    modelo = ModeloFalso()

    registro = registrar_consulta(
        vectorstore,
        "Como estructuro un video?",
        k=4,
        chat_model=modelo,
        tarifa_entrada_x1M=0.3,
        tarifa_salida_x1M=2.5,
    )

    assert vectorstore.embeddings.preguntas == ["Como estructuro un video?"]
    assert vectorstore.busquedas == [([0.1, 0.2], 4)]
    assert "[1] La estructura del video" in modelo.prompts[0]
    assert set(registro["tiempos_ms"]) == {
        "embed",
        "busqueda",
        "armado_prompt",
        "generacion",
    }
    assert registro["tokens"]["total_tokens"] == 120
    assert registro["costo_generacion_estimado_usd"] == 0.00008
    assert registro["citas_disponibles"] == {1: "conocimiento_youtube.md"}


def test_registrar_consulta_conserva_bloques_y_metadatos_del_modelo():
    modelo = ModeloFalso()
    contenido = [
        {
            "type": "text",
            "text": "Gancho inicial [1].",
            "extras": {"signature": "metadato-no-visible"},
        }
    ]
    modelo.contenido = contenido

    registro = registrar_consulta(
        VectorStoreFalso(),
        "Como estructuro un video?",
        chat_model=modelo,
        tarifa_entrada_x1M=0.3,
        tarifa_salida_x1M=2.5,
    )

    assert registro["respuesta_generada"] == contenido


def test_costo_queda_sin_calcular_si_no_hay_tarifas_configuradas(monkeypatch):
    monkeypatch.delenv("GEMINI_INPUT_USD_PER_1M", raising=False)
    monkeypatch.delenv("GEMINI_OUTPUT_USD_PER_1M", raising=False)

    registro = registrar_consulta(
        VectorStoreFalso(),
        "Como estructuro un video?",
        chat_model=ModeloFalso(),
    )

    assert registro["tokens"]["total_tokens"] == 120
    assert registro["costo_generacion_estimado_usd"] is None


def test_registrar_consulta_rechaza_pregunta_vacia():
    with pytest.raises(ValueError, match="pregunta"):
        registrar_consulta(VectorStoreFalso(), "   ", chat_model=ModeloFalso())


def test_guardar_registro_jsonl_agrega_un_objeto_por_linea(tmp_path):
    ruta = tmp_path / "subcarpeta" / "registros.jsonl"
    primero = {"pregunta": "pregunta uno"}
    segundo = {"pregunta": "pregunta dos"}

    guardar_registro_jsonl(primero, ruta)
    guardar_registro_jsonl(segundo, ruta)

    lineas = ruta.read_text(encoding="utf-8").splitlines()
    assert [json.loads(linea) for linea in lineas] == [primero, segundo]
