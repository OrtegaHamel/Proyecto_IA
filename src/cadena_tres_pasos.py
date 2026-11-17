from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI #Modelo
from langchain_core.prompts import PromptTemplate #Plantilla -> Prompt dinámico
from langchain_core.output_parsers import StrOutputParser #Parsea la respuesta y la transforma en solo textos
from langchain_core.prompts import ChatPromptTemplate #Plantilla que incluye rol del sistema e instrucción

load_dotenv()

modelo = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite") #temperature= 0 - 1

# Paso 1: Extraer los puntos clave del texto de referencia
plantilla_extraccion = PromptTemplate.from_template(
    "Lee la siguiente referencia y devuelve solo sus 3 puntos clave principales, uno por línea, sin desarrollarlos: \n\n {texto}"
)

# Paso 2: Crear un gancho de retención para YouTube basado en la información extraída
plantilla_simplificacion = PromptTemplate.from_template(
    "Con base en estos puntos clave, escribe un gancho (hook) de apertura para YouTube que capte la atención en los primeros 5 segundos: \n\n{puntos}"
)

# Paso 3: Formatear la estructura final de preproducción
plantilla_formato = PromptTemplate.from_template(
    "Convierte este resultado en una estructura limpia de preproducción para YouTube en viñetas markdown de máximo 3 líneas, sin introducción: \n\n{texto_simple}"
)

# Texto de referencia real (información objetiva a procesar)
texto_prueba = (
    "El uso de herramientas de inteligencia artificial en la creación de contenido "
    "ha reducido el tiempo de investigación hasta en un 60%. Sin embargo, los algoritmos "
    "de YouTube priorizan la autenticidad y la retención, por lo que los creadores que "
    "usan IA solo para estructurar ideas y guiones —manteniendo su voz original y su "
    "estilo visual— obtienen un 40% más de interacción que quienes automatizan el contenido al 100%."
)

# Sintaxis lambda -> lambda argumentos: expresion
cadena_tres_pasos = (
    plantilla_extraccion
    | modelo
    | StrOutputParser()
    | (lambda puntos: {"puntos": puntos})
    | plantilla_simplificacion
    | modelo
    | StrOutputParser()
    | (lambda simple: {"texto_simple": simple})
    | plantilla_formato
    | modelo
    | StrOutputParser()
)

respuesta = cadena_tres_pasos.invoke(
    {"texto": texto_prueba} # El diccionario que corresponde al primer paso/acción inicial
) 

print(respuesta)