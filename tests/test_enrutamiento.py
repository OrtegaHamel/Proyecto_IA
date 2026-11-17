import logging

import pytest
from langchain_core.messages import AIMessage

from src import enrutamiento as cadena


@pytest.mark.parametrize(
    "clasificacion,gancho_esperado,gancho_no_esperado",
    [
        (" DATOS \n", "destaque la cifra", "despierte curiosidad"),
        ("GENERAL", "despierte curiosidad", "destaque la cifra"),
        ("categoria_desconocida", "despierte curiosidad", "destaque la cifra"),
    ],
)
def test_enruta_la_referencia_y_formatea_la_respuesta(
    monkeypatch, clasificacion, gancho_esperado, gancho_no_esperado
):
    prompts = []

    def responder_modelo(_modelo, prompt, config=None, **kwargs):
        texto = prompt.to_string()
        prompts.append(texto)

        if "Clasifica la siguiente referencia" in texto:
            return AIMessage(content=clasificacion)
        if "Lee la siguiente referencia" in texto:
            return AIMessage(content="Punto clave uno\nPunto clave dos\nPunto clave tres")
        if gancho_esperado in texto:
            return AIMessage(content="Gancho elegido")
        if gancho_no_esperado in texto:
            pytest.fail("Se ejecutó la rama incorrecta")
        if "Convierte este resultado" in texto:
            assert "Gancho elegido" in texto
            return AIMessage(content="Estructura final")

        pytest.fail(f"Prompt inesperado: {texto}")

    monkeypatch.setattr(type(cadena.modelo), "invoke", responder_modelo)

    entrada = {"texto": "Referencia de prueba"}
    resultado = cadena.cadena_robusta.invoke(entrada)

    assert resultado == "Estructura final"
    assert entrada == {"texto": "Referencia de prueba"}
    assert len(prompts) == 4
    assert any(gancho_esperado in prompt for prompt in prompts)


def test_activa_fallback_si_falla_el_modelo(monkeypatch, caplog):
    def modelo_fallido(_modelo, prompt, config=None, **kwargs):
        raise RuntimeError("error simulado del modelo")

    monkeypatch.setattr(type(cadena.modelo), "invoke", modelo_fallido)

    with caplog.at_level(logging.WARNING, logger=cadena.__name__):
        resultado = cadena.cadena_robusta.invoke({"texto": "Referencia de prueba"})

    assert resultado == (
        "No fue posible generar la estructura de preproducción para YouTube "
        "en este momento. Intenta de nuevo más tarde."
    )
    assert "Activando respuesta genérica" in caplog.text
