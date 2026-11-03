import json

import pytest

from precision import cargar_resultados


def test_cargar_resultados_archivo_inexistente_devuelve_lista_vacia(tmp_path):
    assert cargar_resultados(tmp_path / "resultados.json") == []


def test_cargar_resultados_archivo_vacio_devuelve_lista_vacia(tmp_path):
    ruta = tmp_path / "resultados.json"
    ruta.write_text("", encoding="utf-8")

    assert cargar_resultados(ruta) == []


def test_cargar_resultados_lee_json_valido(tmp_path):
    ruta = tmp_path / "resultados.json"
    ruta.write_text(json.dumps([{"id": 1}]), encoding="utf-8")

    assert cargar_resultados(ruta) == [{"id": 1}]


def test_cargar_resultados_informa_json_malformado(tmp_path):
    ruta = tmp_path / "resultados.json"
    ruta.write_text("{", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        cargar_resultados(ruta)
