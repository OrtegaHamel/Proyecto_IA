import os
import requests
from dotenv import load_dotenv

import time

import json
import re

load_dotenv()

#Constantes
#MODELO = "gemini-3.5-flash-lite"
URL_BASE = "https://generativelanguage.googleapis.com/v1beta/models/"
API_KEY = os.getenv("GEMINI_API_KEY")

#función para crear la solicitud
def armar_peticion(modelo, pregunta, system_instruction, response_schema=None): #pregunta = "Confirma la conexion"
    if not pregunta:
        raise ValueError("La pregunta no puede estar vacía")
    url = f"{URL_BASE}{modelo}:generateContent?key={API_KEY}" #url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key=MI API KEY"
    body = {
            "systemInstruction": {
                "parts": [ {"text": system_instruction} ]
            },
            "contents":
                [{"parts": [{"text": pregunta}]}]
        }

    if response_schema is not None:
        body["generationConfig"] = {
            "responseMimeType": "application/json",
            "responseSchema": response_schema
        }


    return url, body


#función envía la petición
def enviar_peticion(url, body, response_schema=None):
    try:
        respuesta = requests.post(url, json=body, timeout=30)
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Error de conexión. Verifica tu conexión a internet.")
    except requests.exceptions.Timeout:
        raise RuntimeError("El tiempo de espera se agotó. Intenta de nuevo.")

    if respuesta.status_code != 200:
        detalle = respuesta.text.strip()
        mensaje = f"Error en la petición ({respuesta.status_code})"
        if detalle:
            mensaje = f"{mensaje}: {detalle}"
        raise RuntimeError(mensaje)

    try:
        return respuesta.json()
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError("La respuesta del servicio no llegó en el formato esperado.")

#funcion procesa y extrae dato
def extraer_texto(datos): #Gemini
    try:
        return datos["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError("No se encontró el texto esperado en la respuesta.")

def obtener_dato_de_prueba(pregunta): #pregunta = "Confirma la conexion"

    response_schema = {
        "type": "OBJECT",
        "properties": {
            "categoria": {"type": "STRING"},
            "nivel": {"type": "NUMBER"}
        },
        "required": ["categoria", "nivel"]
    }

    system_instruction = "Eres un asistente amigable y respondes en máximo 2 palabras."
    url, body = armar_peticion("gemini-3.5-flash-lite", pregunta, system_instruction, response_schema) #obtiene url y body

    inicio = time.perf_counter() #Empezar el contador

    #url = resultado de armar_peticion
    #body = resultado de armar_peticion
    datos = enviar_peticion(url, body)

    fin = time.perf_counter() #Termina el contador
    latencia = fin - inicio
    print(f"Latencia: {latencia:.2f} segundos")

    costo = calcular_costo(datos, 0.00000030, 0.00000250)
    print(f"Costo de la petición: ${costo:.6f} USD")
    texto = extraer_texto(datos)
    datos_formateados = parsear_respuesta_json(texto, ["categoria", "nivel"])
    return datos_formateados

def calcular_costo(datos, precio_entrada, precio_salida):
    uso = datos["usageMetadata"]
    tokens_entrada = uso["promptTokenCount"]
    tokens_salida = uso["candidatesTokenCount"]
    tokens_razonamiento = uso.get("thoughtsTokenCount", 0)
    costo = (tokens_entrada * precio_entrada) + ((tokens_salida + tokens_razonamiento) * precio_salida)
    return costo

def parsear_respuesta_json(texto, claves_requeridas=None):
    """
    claves_requeridas = ["categoria", "nivel"]
    """
    texto_limpio = texto.strip()
    texto_limpio = re.sub(r"^```(?:json)?\s*", "", texto_limpio)
    texto_limpio = re.sub(r"\s*```$", "", texto_limpio)
    try:
        datos = json.loads(texto_limpio)
    except json.JSONDecodeError:
        raise ValueError("La respuesta del modelo no es JSON válido")

    if claves_requeridas:
        faltantes = [clave for clave in claves_requeridas if clave not in datos]
        if faltantes:
            raise ValueError("La respuesta no tiene la estructura esperada.")
    return datos

if __name__ == "__main__": #No lo ejecuta en IMPORT
    try:
        print(obtener_dato_de_prueba("Confirma si mi conexión está funcionando."))
    except (ValueError, RuntimeError) as error:
        print(f"Error: {error}")