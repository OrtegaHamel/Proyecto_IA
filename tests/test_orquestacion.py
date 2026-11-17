import logging
from unittest.mock import MagicMock

from src import enrutamiento as cadena


def test_procesar_referencia_segura_envia_el_texto_a_la_cadena():
    texto = "Referencia para un video"
    cadena_falsa = MagicMock()
    cadena_falsa.invoke.return_value = "Procesado: Referencia para un video"

    resultado = cadena.procesar_referencia_segura(cadena_falsa, texto)

    assert resultado == "Procesado: Referencia para un video"
    cadena_falsa.invoke.assert_called_once()
    entrada, = cadena_falsa.invoke.call_args.args
    opciones = cadena_falsa.invoke.call_args.kwargs
    assert entrada == {"texto": texto}
    assert opciones["config"]["callbacks"] == [cadena.manejador_error]


def test_procesar_referencia_segura_no_propaga_excepciones(caplog):
    cadena_falsa = MagicMock()
    cadena_falsa.invoke.side_effect = ConnectionError("fallo simulado")

    with caplog.at_level(logging.ERROR, logger=cadena.__name__):
        resultado = cadena.procesar_referencia_segura(
            cadena_falsa, "Referencia para un video"
        )

    assert resultado == (
        "No pudimos procesar tu referencia en este momento. "
        "Intenta de nuevo más tarde."
    )
    assert "fallo simulado" in caplog.text
    cadena_falsa.invoke.assert_called_once()
