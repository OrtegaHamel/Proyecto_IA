"""Versionado del prompt de sistema del Copiloto de YouTube."""
import difflib
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__:
    from .configuracion import DOCS, LOCAL, NOMBRE_PROYECTO, guardar_json
else:
    from configuracion import DOCS, LOCAL, NOMBRE_PROYECTO, guardar_json


PROMPT_V1 = """Eres un copiloto en espanol para creadores de YouTube.
Ayudas a proponer titulos, ideas de guion y recomendaciones de SEO.
Adapta tus sugerencias al tema y al publico que indique el creador."""

PROMPT_V2 = """Eres un copiloto en español para creadores y equipos de YouTube. Ayudas con preproducción, guiones, SEO y planificación de retención. 
Puedes proponer títulos, descripciones y etiquetas; diseñar un gancho para los primeros segundos, bloques de guion y una llamada a la acción; 
y definir audiencia, propuesta de valor y ángulo diferenciador. Usa las herramientas cuando aporten cálculos o revisiones concretas. 
Usa el historial para respetar el nicho, la audiencia y el tono del creador sin volver a preguntar lo ya indicado. 
Distingue las recomendaciones de las métricas reales: no inventes datos, tendencias ni resultados de rendimiento, 
y aclara que la retención solo puede medirse con analíticas del video publicado. 
No afirmes que el creador ofrece archivos descargables, productos o episodios futuros salvo que lo haya indicado; 
redacta llamadas a la acción sin prometer recursos no confirmados. Adapta el nivel de detalle a la solicitud y entrega respuestas claras y accionables."""

ARCHIVO_REGISTRO = DOCS / "registro_prompts.json"
ARCHIVO_ACTIVO = LOCAL / "prompt_activo.json"
NOMBRE_PROMPT = NOMBRE_PROYECTO
MODELO = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")


def huella_prompt(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:12]


class RegistroDePrompts:
    def __init__(self) -> None:
        self.versiones: list[dict[str, Any]] = []

    def registrar(
        self,
        nombre: str,
        texto: str,
        autor: str,
        nota: str,
        modelo: str = MODELO,
    ) -> dict[str, Any]:
        if not nombre.strip() or not texto.strip():
            raise ValueError("El nombre y el texto del prompt no pueden estar vacios.")
        version = {
            "nombre": nombre,
            "huella": huella_prompt(texto),
            "texto": texto,
            "autor": autor,
            "fecha": datetime.now(timezone.utc).isoformat(),
            "nota": nota,
            "modelo": modelo,
            "parametros": {"temperature": "valor por defecto del proveedor"},
        }
        self.versiones.append(version)
        return version

    def ultima(self, nombre: str) -> dict[str, Any] | None:
        return next(
            (version for version in reversed(self.versiones) if version["nombre"] == nombre),
            None,
        )


def crear_registro() -> RegistroDePrompts:
    registro = RegistroDePrompts()
    registro.registrar(
        NOMBRE_PROMPT,
        PROMPT_V1,
        "ProyectoIA",
        "Linea base de referencia reconstruida; el repositorio no conserva una version anterior.",
    )
    actual = registro.registrar(
        NOMBRE_PROMPT,
        PROMPT_V2,
        "ProyectoIA",
        "Prompt actual de mi_agente.py; explicita limites sobre metricas y llamadas a la accion.",
    )
    actual["activa_por_defecto"] = True
    return registro


def cargar_registro(ruta: str | Path | None = None) -> RegistroDePrompts:
    archivo = Path(ruta) if ruta is not None else ARCHIVO_REGISTRO
    registro = RegistroDePrompts()
    if not archivo.exists():
        return crear_registro()

    versiones = json.loads(archivo.read_text(encoding="utf-8"))
    if not isinstance(versiones, list) or not versiones:
        raise ValueError("El registro de prompts debe contener una lista no vacia.")
    for version in versiones:
        if not isinstance(version, dict) or not isinstance(version.get("texto"), str):
            raise ValueError("El registro contiene una version con formato invalido.")
        if version.get("huella") != huella_prompt(version["texto"]):
            raise ValueError("El registro de prompts no coincide con sus huellas")
    registro.versiones = versiones
    return registro


def obtener_activa(
    ruta: str | Path | None = None,
    nombre: str = NOMBRE_PROMPT,
) -> dict[str, Any]:
    registro = cargar_registro()
    archivo = Path(ruta) if ruta is not None else ARCHIVO_ACTIVO
    if archivo.exists():
        datos = json.loads(archivo.read_text(encoding="utf-8"))
        huella = datos.get("huella")
    else:
        versiones = [
            version for version in registro.versiones if version["nombre"] == nombre
        ]
        predeterminada = next(
            (version for version in reversed(versiones) if version.get("activa_por_defecto")),
            None,
        )
        activa = predeterminada or (versiones[-1] if versiones else None)
        if activa is None:
            raise ValueError(f"No hay versiones registradas para {nombre}.")
        huella = activa["huella"]

    version = next(
        (
            candidata
            for candidata in registro.versiones
            if candidata["nombre"] == nombre and candidata["huella"] == huella
        ),
        None,
    )
    if version is None:
        raise ValueError("La version activa no existe en el registro")
    return version


def diff_prompts(anterior: str, nueva: str) -> str:
    return "\n".join(
        difflib.unified_diff(
            anterior.splitlines(),
            nueva.splitlines(),
            fromfile="prompt_anterior",
            tofile="prompt_nuevo",
            lineterm="",
        )
    )


def main() -> None:
    registro = cargar_registro()
    versiones_prompt = [
        version for version in registro.versiones if version["nombre"] == NOMBRE_PROMPT
    ]
    ultima = registro.ultima(NOMBRE_PROMPT)
    if ultima is None:
        raise ValueError(f"No hay versiones registradas para {NOMBRE_PROMPT}.")

    if not ARCHIVO_ACTIVO.exists():
        guardar_json(ARCHIVO_ACTIVO, {"huella": obtener_activa()["huella"]})

    if ultima["texto"] != PROMPT_V2:
        registro.registrar(
            NOMBRE_PROMPT,
            PROMPT_V2,
            NOMBRE_PROYECTO,
            "Nueva version del prompt de sistema de mi_agente.py.",
        )
        versiones_prompt.append(registro.versiones[-1])

    if len(versiones_prompt) < 2:
        raise ValueError("Registra al menos dos versiones para generar el diff.")
    guardar_json(ARCHIVO_REGISTRO, registro.versiones)
    anterior, nueva = versiones_prompt[-2:]
    (DOCS / "diff_prompts.txt").write_text(
        diff_prompts(anterior["texto"], nueva["texto"]),
        encoding="utf-8",
    )
    print("Versiones registradas:")
    for version in versiones_prompt:
        print(version["huella"], "-", version["nota"])
    print("Ultima registrada:", registro.ultima(NOMBRE_PROMPT)["huella"])
    print("Activa:", obtener_activa()["huella"])


if __name__ == "__main__":
    main()
