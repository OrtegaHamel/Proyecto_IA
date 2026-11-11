# Límites de la métrica de evaluación

## Qué mide

La métrica compara las palabras de una respuesta con una referencia, contando repeticiones después de limpiar y tokenizar ambos textos. Reporta precisión, cobertura y F1.

## Modos de falla conocidos

- Caso: ID 9, consulta: "¿Qué es la tasa de rebote o abandono temprano?".
  Referencia: "El abandono temprano ocurre cuando los espectadores cierran el vídeo en los primeros segundos."
  Respuesta: "Porcentaje de visitantes que abandonan un sitio web sin interactuar con otra página."
  F1: 0.000
  Hallazgo: Confusión de dominio. El modelo confunde el concepto específico de YouTube (abandono temprano de vídeo) con la métrica web general de "tasa de rebote", mostrando una imprecisión factual parcial que la métrica captura correctamente asignando un F1 de 0.0 por la nula coincidencia de tokens clave.

- Caso: ID 12, consulta: "¿Qué es una pantalla final en YouTube?".
  Referencia: "La pantalla final promociona otros vídeos o canales durante los últimos segundos de reproducción."
  Respuesta: "Es un elemento interactivo que promociona contenido al"
  F1: 0.091
  Hallazgo: Respuesta truncada de forma incompleta debido a un corte abrupto en la generación. Aunque el inicio es coherente, la falta absoluta de completitud se refleja adecuadamente en un puntaje F1 extremadamente bajo por la escasez de tokens coincidentes.

- Caso: ID 4, consulta: "¿Qué función cumplen las etiquetas o tags en YouTube?".
  Referencia: "Las etiquetas ayudan al algoritmo a entender el contexto y la temática del vídeo."
  Respuesta: "Permiten categorizar y optimizar los videos para mejorar su visibilidad en las búsquedas."
  F1: 0.148
  Hallazgo: Penalización por sinonimia y reformulación léxica. La respuesta es correcta y útil, pero utiliza un vocabulario completamente distinto al de la referencia ("categorizar y optimizar" frente a "ayudan al algoritmo a entender"), lo que demuestra que la métrica basada en tokens castiga las explicaciones válidas que varían en redacción.

- Caso: ID 16, consulta: "¿Por qué importa la descripción del vídeo para el SEO?".
  Referencia: "La descripción aporta contexto textual relevante para los motores de búsqueda de la plataforma."
  Respuesta: "La descripción optimizada ayuda a los buscadores a comprender e indexar mejor el contenido."
  F1: 0.214
  Hallazgo: Falsa alarma por variación léxica en respuestas completas. A pesar de estar evaluada positivamente en corrección factual y completitud ("sí" en ambas), obtiene un F1 bajo porque el modelo sustituye términos clave ("motores de búsqueda" por "buscadores", "contexto textual" por "comprender e indexar"), evidenciando que la métrica ignora por completo la equivalencia semántica.

- Caso: ID 5, consulta: "¿Qué es una miniatura de alto impacto?".
  Referencia: "Una miniatura de alto impacto utiliza colores contrastantes y elementos visuales claros para destacar."
  Respuesta: "Una imagen visualmente atractiva diseñada para captar la atención instantánea y generar clics."
  F1: 0.222
  Hallazgo: Cobertura parcial enfocada en propósitos generales. La respuesta es acertada pero se centra en el objetivo comercial (generar clics) omitiendo los detalles técnicos específicos que exigía la referencia (colores contrastantes y elementos visuales claros), lo cual justifica una penalización moderada por falta de exhaustividad.

## Muestra revisada

Se revisaron 10 casos de un conjunto de 20 respuestas generadas con consultar_modelo.

La muestra combina los cinco F1 más bajos y los cinco más altos.

Casos revisados: [9, 12, 4, 16, 5, 13, 14, 7, 3, 1].
Fecha de revisión: Noviembre 2026.

Se aplicó la rúbrica de corrección factual, completitud y contradicción, con una justificación por caso.

## Recomendación de uso

Esta métrica de coincidencia de tokens resulta útil en el pipeline como un filtro automatizado rápido para descartar respuestas vacías, desviadas o con errores graves de dominio (como respuestas totalmente desalineadas).

Sin embargo, dado que penaliza fuertemente el uso de sinónimos y variaciones léxicas válidas, las respuestas con puntajes F1 bajos o intermedios necesitan revisión humana obligatoria antes de ser integradas en producción, garantizando así que no se desechen respuestas semánticamente correctas que simplemente utilizaron un vocabulario alternativo.