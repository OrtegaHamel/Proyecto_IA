from collections import Counter
from pipeline_limpieza import procesar_texto
from cliente import consultar_modelo
import json
from pathlib import Path


def contar_coincidencias(
    tokens_referencia: list[str],
    tokens_respuesta: list[str],
) -> int:
    """Cuenta las coincidencias entre referencia y respuesta."""
    conteo_referencia = Counter(tokens_referencia)
    conteo_respuesta = Counter(tokens_respuesta)
    interseccion = conteo_referencia & conteo_respuesta
    return sum(interseccion.values())

def calcular_precision_cobertura_f1(
    tokens_referencia: list[str],
    tokens_respuesta: list[str],
) -> dict[str, float]:
    """Calcula precisión, cobertura y F1 de dos listas de tokens."""
    coincidencias = contar_coincidencias(
        tokens_referencia, tokens_respuesta
    )

    if not tokens_respuesta or not tokens_referencia:
        return {"precision": 0.0, "cobertura": 0.0, "f1": 0.0}

    precision = coincidencias / len(tokens_respuesta)
    cobertura = coincidencias / len(tokens_referencia)

    if precision + cobertura == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * cobertura / (precision + cobertura)

    resultado = {
        "precision": precision,
        "cobertura": cobertura,
        "f1": f1,
    }

    return resultado

def calcular_metricas(texto_referencia, texto_respuesta):
    tokens_referencia = procesar_texto(texto_referencia)
    tokens_respuesta = procesar_texto(texto_respuesta)
    
    return calcular_precision_cobertura_f1(
        tokens_referencia, tokens_respuesta
    )

def cargar_resultados(ruta):
    if not ruta.exists():
        return []

    contenido = ruta.read_text(encoding="utf-8").strip()
    if not contenido:
        return []

    return json.loads(contenido)


# Casos de prueba adaptados al Copiloto de Preproducción y SEO para YouTube
casos = [
    (
        "¿Qué es el CTR en YouTube?",
        "El CTR mide el porcentaje de usuarios que hacen clic en tu miniatura.",
    ),
    (
        "¿Qué es la retención de audiencia?",
        "La retención de audiencia indica el porcentaje de vídeo que los usuarios ven.",
    ),
    (
        "¿Para qué sirve el gancho o hook al inicio de un vídeo?",
        "El gancho sirve para capturar la atención en los primeros segundos y evitar que abandonen.",
    ),
    (
        "¿Qué función cumplen las etiquetas o tags en YouTube?",
        "Las etiquetas ayudan al algoritmo a entender el contexto y la temática del vídeo.",
    ),
    (
        "¿Qué es una miniatura de alto impacto?",
        "Una miniatura de alto impacto utiliza colores contrastantes y elementos visuales claros para destacar.",
    ),
    (
        "¿Por qué es importante el SEO en YouTube?",
        "El SEO optimiza tu contenido para aparecer en los resultados de búsqueda y sugeridos.",
    ),
    (
        "¿Qué mide el tiempo de visualización o watch time?",
        "El tiempo de visualización mide el total de horas que los espectadores pasan viendo tus vídeos.",
    ),
    (
        "¿Para qué sirve un llamado a la acción o CTA?",
        "Un llamado a la acción guía al espectador para que se suscriba, comente o vea otro vídeo.",
    ),
    (
        "¿Qué es la tasa de rebote o abandono temprano?",
        "El abandono temprano ocurre cuando los espectadores cierran el vídeo en los primeros segundos.",
    ),
    (
        "¿Qué son los capítulos de vídeo en YouTube?",
        "Los capítulos dividen el vídeo en secciones con marcas de tiempo para facilitar la navegación.",
    ),
    (
        "¿Cómo influye la miniatura en las impresiones?",
        "Una buena miniatura impulsa las impresiones al generar mayor interés visual en el feed.",
    ),
    (
        "¿Qué es una pantalla final en YouTube?",
        "La pantalla final promociona otros vídeos o canales durante los últimos segundos de reproducción.",
    ),
    (
        "¿Para qué sirve analizar las analíticas de YouTube Studio?",
        "Permite identificar qué contenido retiene mejor a la audiencia para replicar el éxito.",
    ),
    (
        "¿Qué caracteriza a un buen título para YouTube?",
        "Un buen título genera curiosidad, incluye palabras clave y es directo al punto.",
    ),
    (
        "¿Qué es el algoritmo de recomendación de YouTube?",
        "El algoritmo recomienda vídeos basándose en el historial y comportamiento previo del usuario.",
    ),
    (
        "¿Por qué importa la descripción del vídeo para el SEO?",
        "La descripción aporta contexto textual relevante para los motores de búsqueda de la plataforma.",
    ),
    (
        "¿Qué es el formato Shorts en YouTube?",
        "Shorts es un formato de vídeo vertical de corta duración enfocado en consumo rápido.",
    ),
    (
        "¿Cómo ayuda la preproducción en un canal de YouTube?",
        "La preproducción organiza la estructura, el guion y los recursos antes de grabar para ahorrar tiempo.",
    ),
    (
        "¿Qué es el engagement en una comunidad de YouTube?",
        "El engagement refleja la interacción activa de los usuarios mediante likes, comentarios y compartidos.",
    ),
    (
        "¿Qué ventaja aporta un guion estructurado por bloques?",
        "Un guion estructurado evita baches de contenido y mantiene un ritmo dinámico en la narración.",
    ),
]


def resumir_metricas(resultados):
    if not resultados:
        return {
            "precision_promedio": 0,
            "cobertura_promedio": 0,
            "f1_promedio": 0,
        }
    n = len(resultados)
    return {
        "precision_promedio": sum(
            r["precision"] for r in resultados
        ) / n,
        "cobertura_promedio": sum(
            r["cobertura"] for r in resultados
        ) / n,
        "f1_promedio": sum(r["f1"] for r in resultados) / n,
    }


def main():
    raiz = Path(__file__).resolve().parents[1]
    ruta_resultados = raiz / "resultados_metricas.json"
    resultados = cargar_resultados(ruta_resultados)

    completados = {
        (caso["consulta"], caso["referencia"])
        for caso in resultados
    }

    for numero, (consulta, referencia) in enumerate(casos, start=1):
        if (consulta, referencia) in completados:
            print("Ya guardada:", consulta)
            continue

        try:
            respuesta = consultar_modelo(
                consulta,
                system_instruction=(
                    "Responde en español con una definición breve, "
                    "en una sola oración de máximo 15 palabras. "
                    "Sin listas, ejemplos ni introducciones."
                )
            )
        except RuntimeError as error:
            print("\nSe detuvo la generación:", error)
            print(f"Respuestas guardadas: {len(resultados)}")
            break

        metricas = calcular_metricas(referencia, respuesta)
        resultados.append({
            "id": numero,
            "consulta": consulta,
            "referencia": referencia,
            "respuesta": respuesta,
            **metricas,
        })

        with ruta_resultados.open("w", encoding="utf-8") as archivo:
            json.dump(
                resultados,
                archivo,
                indent=2,
                ensure_ascii=False
            )

        completados.add((consulta, referencia))
        print("\nConsulta:", consulta)
        print("Respuesta:", respuesta)
        print("Métricas:", metricas)
        print(f"Guardadas: {len(resultados)}/{len(casos)}")
    
    print("Promedios")
    print(resumir_metricas(resultados))
    
    peores_casos = sorted(resultados, key=lambda r: r["f1"])

    for caso in peores_casos[:3]:
        print(caso["consulta"], caso["f1"])


if __name__ == "__main__":
    main()