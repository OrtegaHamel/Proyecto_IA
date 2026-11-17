import logging

from dotenv import load_dotenv
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableBranch, RunnableLambda, RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="error.log",
    filemode="a",
    encoding="utf-8",
    force=True,
)
logger = logging.getLogger(__name__)

load_dotenv()

modelo = ChatGoogleGenerativeAI(model="gemini-3.6-flash")

plantilla_clasificacion = PromptTemplate.from_template(
    "Clasifica la siguiente referencia como 'datos' si incluye estadísticas o "
    "cifras concretas; de lo contrario, clasifícala como 'general'. Responde "
    "solo con una de esas dos palabras. \n\n{texto}"
)

paso_clasificacion = (
    plantilla_clasificacion
    | modelo
    | StrOutputParser()
    | (lambda tipo: tipo.strip().lower())
)

plantilla_extraccion = PromptTemplate.from_template(
    "Lee la siguiente referencia y devuelve solo sus 3 puntos clave principales, "
    "uno por línea, sin desarrollarlos: \n\n{texto}"
)

paso_extraccion = (
    plantilla_extraccion
    | modelo
    | StrOutputParser()
    | (lambda puntos: {"puntos": puntos})
)

plantilla_gancho_datos = PromptTemplate.from_template(
    "Con base en estos puntos clave, escribe un gancho de apertura para YouTube "
    "que destaque la cifra o estadística más sorprendente y capte la atención en "
    "los primeros 5 segundos: \n\n{puntos}"
)

plantilla_gancho_general = PromptTemplate.from_template(
    "Con base en estos puntos clave, escribe un gancho de apertura para YouTube "
    "que despierte curiosidad y capte la atención en los primeros 5 segundos: "
    "\n\n{puntos}"
)

plantilla_formato = PromptTemplate.from_template(
    "Convierte este resultado en una estructura limpia de preproducción para "
    "YouTube en viñetas markdown de máximo 3 líneas, sin introducción: "
    "\n\n{texto_simple}"
)


def crear_cadena_gancho(plantilla_gancho):
    return (
        plantilla_gancho
        | modelo
        | StrOutputParser()
        | (lambda gancho: {"texto_simple": gancho})
        | plantilla_formato
        | modelo
        | StrOutputParser()
    )


cadena_gancho_datos = crear_cadena_gancho(plantilla_gancho_datos)
cadena_gancho_general = crear_cadena_gancho(plantilla_gancho_general)

bifurcacion = RunnableBranch(
    (lambda entrada: entrada["clasificacion"] == "datos", cadena_gancho_datos),
    cadena_gancho_general,
)

cadena_con_enrutamiento = (
    RunnablePassthrough.assign(
        clasificacion=paso_clasificacion,
        puntos=paso_extraccion,
    )
    | bifurcacion
)


def fallback_con_log(_entrada):
    logger.warning("Cadena principal falló. Activando respuesta genérica")
    return (
        "No fue posible generar la estructura de preproducción para YouTube "
        "en este momento. Intenta de nuevo más tarde."
    )


respuesta_generica = RunnableLambda(fallback_con_log)
cadena_robusta = cadena_con_enrutamiento.with_fallbacks([respuesta_generica])


class CapturadorError(BaseCallbackHandler):
    def on_chain_error(self, error: BaseException, **kwargs):
        logger.warning(
            "Error capturado antes del fallback: [%s] -> %s",
            type(error).__name__,
            error,
        )


manejador_error = CapturadorError()


def procesar_referencia_segura(cadena, texto):
    try:
        return cadena.invoke({"texto": texto}, config={"callbacks": [manejador_error]})
    except Exception as error:
        logger.error("Error procesando la referencia: %s", error)
        return (
            "No pudimos procesar tu referencia en este momento. "
            "Intenta de nuevo más tarde."
        )


texto_prueba = (
    "El uso de herramientas de inteligencia artificial en la creación de contenido "
    "ha reducido el tiempo de investigación hasta en un 60%. Sin embargo, los "
    "algoritmos de YouTube priorizan la autenticidad y la retención, por lo que "
    "los creadores que usan IA solo para estructurar ideas y guiones —manteniendo "
    "su voz original y su estilo visual— obtienen un 40% más de interacción que "
    "quienes automatizan el contenido al 100%."
)

if __name__ == "__main__":
    print(procesar_referencia_segura(cadena_robusta, texto_prueba))
