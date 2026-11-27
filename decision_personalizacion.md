# Decisión de personalización: copiloto para creadores de YouTube

## 1. El problema

El copiloto ayuda a creadores de YouTube con ideas y estructuras de guion, SEO y planificación de retención. Para que sus recomendaciones se apoyen en conocimiento de referencia del proyecto y ese conocimiento pueda mantenerse separado del modelo, hace falta una estrategia que no dependa de entrenar el modelo.

## 2. Resultado del método de decisión

Aplicando los criterios del Bloque 30 de forma conservadora —sin convertir la falta de evidencia en un resultado favorable—:

| Criterio | Respuesta | Evidencia del proyecto |
| --- | --- | --- |
| `informacion_cambia_seguido` | False | El corpus `data/conocimiento_youtube.md` no registra fechas de actualización y el historial consultado no demuestra cambios mensuales durante los últimos tres meses. No marco True solo porque la plataforma pueda cambiar. |
| `problema_de_formato_o_tono` | False | Revisé las 20 respuestas guardadas en `resultados_metricas.json` con la instrucción del proyecto: español, una respuesta de una sola oración de máximo 15 palabras, sin listas, ejemplos ni introducciones. Las respuestas 6 ("El SEO") y 12 (termina en "al") están incompletas: 2/20 (10 %), por debajo del umbral de 3/20. La respuesta 9 no corresponde a la pregunta, pero es un problema de pertinencia del contenido, no de formato o tono. |
| `dataset_grande_y_de_calidad` | True | Se prepararon 200 pares sintéticos de entrada/salida en `data/ejemplos_personalizacion.jsonl` (50 por tarea). En una muestra aleatoria estratificada de 20 (5 por tarea) no encontré contradicciones entre la tarea y su salida etiquetada. Son borradores sintéticos: requieren revisión factual y aprobación del proyecto antes de usarse para entrenar. |
| `presupuesto_limitado_o_iterar_rapido` | True | Para esta decisión se requiere evitar el costo económico de entrenamientos y no ejecutar tuning. |
| `necesita_multiples_variantes` | False | El proyecto describe un copiloto general; no especifica dos o más versiones del modelo por cliente, idioma o línea de producto. |

Con esas respuestas, el puntaje de la función de decisión de la actividad es:

- **RAG: 2 puntos**
- **Fine-tuning completo: 2 puntos**
- **PEFT: 2 puntos**

**Hay empate entre RAG, fine-tuning completo y PEFT.**

## 3. Técnica elegida y por qué

Aunque el método deja un empate, elijo **RAG** porque resuelve la necesidad de aportar contexto al copiloto sin invertir en fine-tuning. La muestra existente presenta dos respuestas incompletas y una que no corresponde a la pregunta; esta última apunta a un problema de pertinencia y fundamentación, no necesariamente de estilo. RAG encaja con la arquitectura que el proyecto ya implementa: embeddings de Gemini, recuperación con Chroma y generación con Gemini. Los 200 pares creados son sintéticos y no eliminan la preparación, revisión ni el costo de entrenamiento que requerirían fine-tuning completo o PEFT.

La restricción económica se refiere al tuning, no al uso de la API: las llamadas a Gemini para embeddings y generación son aceptables para este proyecto, aunque tienen costo. Operar RAG no es gratis; indexar o actualizar el corpus y procesar consultas puede generar cargos de API. Para revisar este documento y una muestra estratificada de 20 ejemplos hice una llamada de inferencia a Gemini 3.5 Flash Lite: 5.867 tokens de entrada y 80 de salida (5.947 en total, según el proveedor). Con las tarifas indicadas de $0,30 por millón de tokens de entrada y $2,50 por millón de salida, el costo estimado es $0,0017601 + $0,0002 = **$0,0019601 USD** (aproximadamente $0,00196). No se hizo tuning.

## 4. Qué necesitaría para ejecutarla

El proyecto ya contiene **1 archivo de corpus** (`data/conocimiento_youtube.md`) y un directorio de índice Chroma local. Para el prototipo actual no falta un corpus base por indexar. Los 200 ejemplos sintéticos (`data/ejemplos_personalizacion.jsonl`) son un recurso separado y no forman parte del corpus RAG. En esta revisión hice una llamada para auditar el documento y una muestra; no ejecuté indexación. Se pueden usar llamadas a la API al operar el flujo, y antes de reindexar conviene comprobar el estado del índice existente para no duplicar datos. Si el copiloto necesita recomendaciones específicas por canal o información vigente de la plataforma, habrá que reunir y revisar fuentes adicionales, fechadas y pertinentes, como guías de estilo aprobadas por cada creador y documentación oficial. Su cantidad queda por definir al delimitar ese alcance, en lugar de inventar un número.
