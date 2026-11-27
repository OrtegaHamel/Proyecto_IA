"""Matriz de riesgos del Copiloto de YouTube."""
if __package__:
    from .configuracion import DOCS, guardar_json
else:
    from configuracion import DOCS, guardar_json


RIESGOS = [
    {
        "id": "R1",
        "riesgo": "Un cambio del prompt debilita los limites y provoca recomendaciones no confiables.",
        "probabilidad": 3,
        "impacto": 4,
        "justificacion": "Un cambio de instrucciones puede quitar las restricciones sobre metricas o promesas al creador.",
        "mitigacion": "Registrar huellas y diff; activar solo la huella exacta aprobada en src/registro_prompts.py y src/grafo_supervision.py (Bloque 32).",
        "supervision": "El responsable funcional revisa el diff y las pruebas; debe aprobar la huella exacta antes de activar la version.",
        "responsable": "Responsable funcional del copiloto",
        "evidencia": "Pruebas de pausa, aprobacion, rechazo y huella revisada en tests/test_bloque32.py.",
        "estado": "Control local implementado; almacenamiento del checkpoint en memoria y activacion en un solo equipo.",
    },
    {
        "id": "R2",
        "riesgo": "Las trazas guardan en texto claro ideas ineditas, consultas y respuestas del creador.",
        "probabilidad": 3,
        "impacto": 4,
        "justificacion": "mi_agente.py registra entrada, argumentos de herramientas y respuesta; registro_rag.py guarda pregunta y respuesta.",
        "mitigacion": "No compartir trazas con datos reales; logs_rag.py ya registra huellas y longitudes, pero no esta conectado a los otros dos registros. Minimizar y limitar acceso sigue pendiente.",
        "supervision": "El custodio de datos revisa y redacta las trazas antes de exportarlas o compartirlas; hasta entonces se mantienen locales.",
        "responsable": "Custodio de datos del proyecto",
        "evidencia": "Inspeccion de registrar_traza en src/mi_agente.py y de registrar_consulta en src/registro_rag.py.",
        "estado": "Riesgo vigente: los registros del agente y del medidor RAG conservan contenido sin redactar.",
    },
    {
        "id": "R3",
        "riesgo": "Texto malicioso incorporado al contexto RAG intenta alterar la respuesta del copiloto.",
        "probabilidad": 2,
        "impacto": 4,
        "justificacion": "El contexto recuperado se concatena con la consulta y se envia al modelo; el corpus actual es local, pero una fuente futura puede incluir instrucciones hostiles.",
        "mitigacion": "Revisar manualmente las fuentes antes de indexarlas con src/preparar_rag_youtube.py. El prompt de src/registro_rag.py limita la respuesta al contexto y pide abstenerse, pero aun no hay un filtro anti-inyeccion.",
        "supervision": "El responsable del corpus revisa origen y contenido antes de cada indexacion o actualizacion.",
        "responsable": "Responsable del corpus",
        "evidencia": "Inspeccion del prompt RAG y del corpus local data/conocimiento_youtube.md.",
        "estado": "Revision de fuentes manual; delimitacion y deteccion automatica de inyecciones pendientes.",
    },
    {
        "id": "R4",
        "riesgo": "Un guion o titulo sugiere afirmaciones o resultados que el creador no puede respaldar.",
        "probabilidad": 3,
        "impacto": 3,
        "justificacion": "Una recomendacion generada puede sonar convincente aunque no coincida con el contenido real del video.",
        "mitigacion": "El prompt versionado prohíbe inventar metricas y promesas; revisar cada afirmacion contra fuentes antes de publicar (Bloque 32).",
        "supervision": "El creador verifica guion, titulo y descripcion frente a fuentes confiables y al contenido final antes de subir el video.",
        "responsable": "Creador o editor del canal",
        "evidencia": "Restricciones de exactitud en el prompt actual de src/registro_prompts.py y en src/mi_agente.py.",
        "estado": "El prompt reduce el riesgo, pero no verifica los hechos de cada guion.",
    },
    {
        "id": "R5",
        "riesgo": "Una sugerencia de estructura o duracion se interpreta como una prediccion de retencion real.",
        "probabilidad": 3,
        "impacto": 2,
        "justificacion": "El copiloto puede planificar ritmo y duracion, pero la retencion solo se mide con analiticas de un video publicado.",
        "mitigacion": "La herramienta crear_estructura_video y data/conocimiento_youtube.md indican que la estructura es orientativa y no predice retencion.",
        "supervision": "Comparar las recomendaciones con analiticas reales despues de publicar; no tomar decisiones de rendimiento basandose solo en la estimacion.",
        "responsable": "Creador o analista del canal",
        "evidencia": "Advertencias incluidas en crear_estructura_video de src/mi_agente.py y data/conocimiento_youtube.md.",
        "estado": "Advertencia implementada; no existe conexion automatica a analiticas de YouTube.",
    },
]


def puntaje_riesgo(probabilidad: int, impacto: int) -> int:
    if any(type(numero) is not int or not 1 <= numero <= 5 for numero in (probabilidad, impacto)):
        raise ValueError("P e I deben ser enteros entre 1 y 5")
    return probabilidad * impacto


def categoria_riesgo(puntaje: int) -> str:
    if puntaje >= 15:
        return "CRITICO"
    if puntaje >= 9:
        return "ALTO"
    if puntaje >= 4:
        return "MEDIO"
    return "BAJO"


def esta_en_el_limite(probabilidad: int, impacto: int) -> bool:
    actual = categoria_riesgo(puntaje_riesgo(probabilidad, impacto))
    vecinos = [
        (probabilidad + 1, impacto),
        (probabilidad - 1, impacto),
        (probabilidad, impacto + 1),
        (probabilidad, impacto - 1),
    ]
    return any(
        categoria_riesgo(p * i) != actual
        for p, i in vecinos
        if 1 <= p <= 5 and 1 <= i <= 5
    )


def completar_matriz() -> list[dict]:
    filas = []
    for riesgo in RIESGOS:
        fila = dict(riesgo)
        fila["puntaje"] = puntaje_riesgo(fila["probabilidad"], fila["impacto"])
        fila["categoria"] = categoria_riesgo(fila["puntaje"])
        fila["al_limite"] = esta_en_el_limite(fila["probabilidad"], fila["impacto"])
        filas.append(fila)
    return sorted(filas, key=lambda riesgo: -riesgo["puntaje"])


def main() -> None:
    filas = completar_matriz()
    guardar_json(DOCS / "matriz_riesgos.json", filas)
    lineas = [
        "# Matriz de riesgos del Copiloto de YouTube",
        "",
        "Estimaciones cualitativas iniciales, no probabilidades medidas. BAJO 1-3; MEDIO 4-8; ALTO 9-14; CRITICO 15-25.",
        "",
        "AL LIMITE indica que variar un punto en P o I cambia la categoria. Los controles pendientes se identifican como tales.",
        "",
        "| ID | Riesgo | P | I | Puntaje | Categoria | AL LIMITE |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for riesgo in filas:
        limite = "Si" if riesgo["al_limite"] else "No"
        lineas.append(
            f"| {riesgo['id']} | {riesgo['riesgo']} | {riesgo['probabilidad']} | "
            f"{riesgo['impacto']} | {riesgo['puntaje']} | {riesgo['categoria']} | {limite} |"
        )
    for riesgo in filas:
        lineas.extend(["", f"## {riesgo['id']} {riesgo['riesgo']}", ""])
        for campo in (
            "justificacion",
            "mitigacion",
            "supervision",
            "responsable",
            "evidencia",
            "estado",
        ):
            lineas.append(f"**{campo.capitalize()}**: {riesgo[campo]}\n")
    (DOCS / "matriz_riesgos.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    for riesgo in filas:
        limite = "AL LIMITE" if riesgo["al_limite"] else ""
        print(riesgo["id"], riesgo["categoria"], riesgo["puntaje"], limite)


if __name__ == "__main__":
    main()
