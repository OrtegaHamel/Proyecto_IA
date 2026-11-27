import json

import pytest

from src import configuracion, grafo_supervision, matriz_riesgos, registro_prompts


def test_registro_incluye_dos_prompts_reales_y_detecta_cambios(tmp_path, monkeypatch):
    registro = registro_prompts.crear_registro()
    versiones = [
        version
        for version in registro.versiones
        if version["nombre"] == registro_prompts.NOMBRE_PROMPT
    ]

    assert len(versiones) >= 2
    assert versiones[0]["huella"] != versiones[1]["huella"]
    assert registro.ultima(registro_prompts.NOMBRE_PROMPT) == versiones[-1]
    assert registro_prompts.PROMPT_V2 in versiones[-1]["texto"]
    assert registro_prompts.diff_prompts(versiones[0]["texto"], versiones[-1]["texto"])

    ruta = tmp_path / "registro.json"
    configuracion.guardar_json(ruta, versiones)
    monkeypatch.setattr(registro_prompts, "ARCHIVO_REGISTRO", ruta)
    assert registro_prompts.obtener_activa()["huella"] == versiones[-1]["huella"]

    versiones[-1]["texto"] += " cambio no registrado"
    ruta.write_text(json.dumps(versiones), encoding="utf-8")
    with pytest.raises(ValueError, match="huellas"):
        registro_prompts.cargar_registro()


def test_grafo_pausa_aprueba_o_rechaza_y_persiste_solo_aprobacion(
    tmp_path, monkeypatch
):
    registro = registro_prompts.crear_registro()
    versiones = [
        version
        for version in registro.versiones
        if version["nombre"] == registro_prompts.NOMBRE_PROMPT
    ]
    anterior, nueva = versiones[0]["huella"], versiones[-1]["huella"]
    ruta_registro = tmp_path / "registro.json"
    configuracion.guardar_json(ruta_registro, versiones)
    monkeypatch.setattr(registro_prompts, "ARCHIVO_REGISTRO", ruta_registro)

    app = grafo_supervision.crear_app()
    ruta_activa = tmp_path / "activa.json"
    configuracion.guardar_json(ruta_activa, {"huella": anterior})

    config, interrumpido = grafo_supervision.iniciar(app, anterior, nueva)
    assert "__interrupt__" in interrumpido
    assert interrumpido["huella_activa"] == anterior
    final = grafo_supervision.resolver(app, config, True, nueva)
    assert final["huella_activa"] == nueva
    grafo_supervision.persistir_activacion(final, anterior, ruta_activa)
    assert json.loads(ruta_activa.read_text(encoding="utf-8"))["huella"] == nueva

    configuracion.guardar_json(ruta_activa, {"huella": anterior})
    config_rechazo, _ = grafo_supervision.iniciar(app, anterior, nueva)
    rechazado = grafo_supervision.resolver(app, config_rechazo, False, nueva)
    assert rechazado["huella_activa"] == anterior
    grafo_supervision.persistir_activacion(rechazado, anterior, ruta_activa)
    assert json.loads(ruta_activa.read_text(encoding="utf-8"))["huella"] == anterior

    config_error, _ = grafo_supervision.iniciar(app, anterior, nueva)
    with pytest.raises(ValueError, match="no coincide"):
        grafo_supervision.resolver(app, config_error, True, "huella-incorrecta")


def test_matriz_tiene_riesgos_concretos_y_supervision_para_niveles_altos():
    filas = matriz_riesgos.completar_matriz()
    assert len(filas) >= 5
    assert all(fila["riesgo"] and fila["mitigacion"] for fila in filas)
    assert any(fila["categoria"] in {"ALTO", "CRITICO"} for fila in filas)
    assert all(
        fila["supervision"]
        for fila in filas
        if fila["categoria"] in {"ALTO", "CRITICO"}
    )
    assert sum("Bloque 32" in fila["mitigacion"] for fila in filas) >= 2
    assert matriz_riesgos.puntaje_riesgo(3, 4) == 12
    assert matriz_riesgos.categoria_riesgo(12) == "ALTO"
    with pytest.raises(ValueError):
        matriz_riesgos.puntaje_riesgo(True, 4)
