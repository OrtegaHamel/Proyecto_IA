"""Aprobacion humana del prompt antes de activarlo en el Copiloto de YouTube."""
import argparse
from pathlib import Path
from typing import TypedDict
from uuid import uuid4

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

if __package__:
    from .configuracion import DOCS, guardar_json
    from .registro_prompts import (
        ARCHIVO_ACTIVO,
        NOMBRE_PROMPT,
        cargar_registro,
        diff_prompts,
        obtener_activa,
    )
else:
    from configuracion import DOCS, guardar_json
    from registro_prompts import (
        ARCHIVO_ACTIVO,
        NOMBRE_PROMPT,
        cargar_registro,
        diff_prompts,
        obtener_activa,
    )


class EstadoDespliegue(TypedDict):
    huella_nueva: str
    huella_activa: str
    aprobado: bool


def proponer(estado: EstadoDespliegue) -> dict:
    if not estado["huella_nueva"] or estado["huella_nueva"] == estado["huella_activa"]:
        raise ValueError("La propuesta debe tener una huella distinta de la version activa.")
    if not any(
        version["nombre"] == NOMBRE_PROMPT
        and version["huella"] == estado["huella_nueva"]
        for version in cargar_registro().versiones
    ):
        raise ValueError("La version propuesta no esta registrada.")
    return {}


def supervisar(estado: EstadoDespliegue) -> dict:
    decision = interrupt(
        {
            "motivo": "Revisar el diff y aprobar la activacion local del prompt de YouTube",
            "huella_propuesta": estado["huella_nueva"],
            "huella_activa": estado["huella_activa"],
        }
    )
    if type(decision) is not bool:
        raise ValueError("La decision debe ser un booleano, nunca un texto como 'no'.")
    return {"aprobado": decision}


def aplicar(estado: EstadoDespliegue) -> dict:
    return {"huella_activa": estado["huella_nueva"]} if estado["aprobado"] else {}


def crear_app():
    grafo = StateGraph(EstadoDespliegue)
    grafo.add_node("proponer", proponer)
    grafo.add_node("supervisar", supervisar)
    grafo.add_node("aplicar", aplicar)
    grafo.add_edge(START, "proponer")
    grafo.add_edge("proponer", "supervisar")
    grafo.add_edge("supervisar", "aplicar")
    grafo.add_edge("aplicar", END)
    return grafo.compile(checkpointer=InMemorySaver())


def iniciar(app, anterior: str, nueva: str) -> tuple[dict, dict]:
    config = {"configurable": {"thread_id": "prompt-" + uuid4().hex}}
    resultado = app.invoke(
        {
            "huella_nueva": nueva,
            "huella_activa": anterior,
            "aprobado": False,
        },
        config=config,
    )
    if "__interrupt__" not in resultado or resultado["huella_activa"] != anterior:
        raise RuntimeError("No se verifico la pausa anterior a la activacion.")
    return config, resultado


def resolver(app, config: dict, aprobar: bool, huella_revisada: str) -> dict:
    if type(aprobar) is not bool:
        raise ValueError("La decision debe ser True o False.")
    snapshot = app.get_state(config)
    if not snapshot.next or not snapshot.interrupts:
        raise ValueError("No existe una aprobacion pendiente en este hilo.")
    if snapshot.values["huella_nueva"] != huella_revisada:
        raise ValueError("La huella pendiente no coincide con la revisada.")
    return app.invoke(Command(resume=aprobar), config=config)


def persistir_activacion(final: dict, anterior: str, ruta=None) -> None:
    archivo = Path(ruta) if ruta is not None else ARCHIVO_ACTIVO
    if not final["aprobado"]:
        return
    if obtener_activa(ruta=archivo)["huella"] != anterior:
        raise ValueError("La version activa cambio durante la revision. Inicia otra solicitud.")
    if not any(
        version["nombre"] == NOMBRE_PROMPT
        and version["huella"] == final["huella_activa"]
        for version in cargar_registro().versiones
    ):
        raise ValueError("La version propuesta no esta registrada.")
    temporal = archivo.with_name(archivo.name + "." + uuid4().hex + ".tmp")
    guardar_json(temporal, {"huella": final["huella_activa"]})
    temporal.replace(archivo)


def verificar() -> list[dict]:
    registro = cargar_registro()
    versiones = [v for v in registro.versiones if v["nombre"] == NOMBRE_PROMPT]
    anterior, nueva = versiones[-2]["huella"], versiones[-1]["huella"]
    app = crear_app()
    evidencias = []
    for decision in (True, False):
        config, _ = iniciar(app, anterior, nueva)
        final = resolver(app, config, decision, nueva)
        assert final["huella_activa"] == (nueva if decision else anterior)
        evidencias.append(
            {
                "thread_id": config["configurable"]["thread_id"],
                "pausa_verificada": True,
                "decision": decision,
                "estado_final": final,
            }
        )
    guardar_json(DOCS / "evidencias_simuladas" / "supervision.json", evidencias)
    print("OK: pausa, aprobacion y rechazo. La prueba no cambia la version activa.")
    return evidencias


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Solicita aprobacion antes de activar la ultima version del prompt."
    )
    parser.add_argument("--verificar", action="store_true")
    args = parser.parse_args()
    if args.verificar:
        verificar()
        return

    anterior = obtener_activa()
    versiones = [
        version
        for version in cargar_registro().versiones
        if version["nombre"] == NOMBRE_PROMPT
    ]
    nueva = versiones[-1]
    if anterior["huella"] == nueva["huella"]:
        print("La ultima version ya esta activa. No hay cambio que aprobar.")
        return

    print(diff_prompts(anterior["texto"], nueva["texto"]))
    app = crear_app()
    config, _ = iniciar(app, anterior["huella"], nueva["huella"])
    print("PAUSADO:", app.get_state(config).interrupts[0].value)
    respuesta = input("Escribe aprobar o rechazar: ").strip().lower()
    while respuesta not in {"aprobar", "rechazar"}:
        respuesta = input("Escribe aprobar o rechazar: ").strip().lower()
    final = resolver(app, config, respuesta == "aprobar", nueva["huella"])
    persistir_activacion(final, anterior["huella"])
    guardar_json(
        ARCHIVO_ACTIVO.parent / "ultima_revision_prompt.json",
        {
            "thread_id": config["configurable"]["thread_id"],
            "decision": respuesta,
            "huella_revisada": nueva["huella"],
            "estado_final": final,
        },
    )
    print("Huella activa:", obtener_activa()["huella"])
    print("El cambio es local. El checkpointer de esta practica vive en memoria.")


if __name__ == "__main__":
    main()
