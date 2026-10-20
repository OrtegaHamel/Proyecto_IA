import os
import requests
from dotenv import load_dotenv

load_dotenv()

#Constantes
MODELO = "gemini-3.6-flash"
URL_BASE = "https://generativelanguage.googleapis.com/v1beta/models/"
API_KEY = os.getenv("GEMINI_API_KEY")

#función para crear la solicitud
def armar_peticion(pregunta): #pregunta = "Confirma la conexion"
    if not pregunta:
        raise ValueError("La pregunta no puede estar vacía.")
    url = f"{URL_BASE}{MODELO}:generateContent?key={API_KEY}" #url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key=MI API KEY"
    body = {
        "contents": 
            [{"parts": [{"text": pregunta}]}]
        }
    return url, body

#función envía la petición
def enviar_peticion(url, body):
    try:
        respuesta = requests.post(url, json=body, timeout=30)
    except requests.exception.ConectionError:
        raise RuntimeError("Error de conexión. Verifica tu conexión a internet.")
    except requests.exception.Timeout:
        raise RuntimeError("El tiempo de espera se agotó. Intenta de nuevo.")

    if respuesta.status_code != 200:
        raise RuntimeError(f"Error en la petición: {respuesta.status_code}")

    try:
        return respuesta.json()
    except requests.exception.JSONDecodeError:
        raise RuntimeError("La respuesta del servicio no llegó en el formato esperado.")

#funcion procesa y extrae dato
def extraer_texto(datos): #Gemini
    try:
        return datos["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError("No se encontró el texto esperado en la respuesta.")

def obtener_dato_de_prueba(pregunta): #pregunta = "Confirma la conexion"
    url, body = armar_peticion(pregunta) #obtiene url y body
    #url = resultado de armar_peticion
    #body = resultado de armar_peticion
    datos = enviar_peticion(url, body)
    costo = calcular_costo(datos, 0.00000075, 0.00000375)
    print(f"Costo estimado: ${costo:.6f} USD")
    return extraer_texto(datos)

def calcular_costo(datos, precio_entrada, precio_salida):
    uso = datos["usageMetadata"]
    tokens_entrada = uso["promptTokenCount"]
    tokens_salida = uso["candidatesTokenCount"]
    tokens_razonamiento = uso["thoughtTokenCount"]
    costo = (tokens_entrada * precio_entrada) + ((tokens_salida + tokens_razonamiento) * precio_salida)
    return costo

try:
    print(obtener_dato_de_prueba("Confirma si mi conexión está funcionando."))
except (ValueError, RuntimeError) as error:
    print(f"Error: {error}")