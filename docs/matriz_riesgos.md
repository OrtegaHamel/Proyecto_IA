# Matriz de riesgos del Copiloto de YouTube

Estimaciones cualitativas iniciales, no probabilidades medidas. BAJO 1-3; MEDIO 4-8; ALTO 9-14; CRITICO 15-25.

AL LIMITE indica que variar un punto en P o I cambia la categoria. Los controles pendientes se identifican como tales.

| ID | Riesgo | P | I | Puntaje | Categoria | AL LIMITE |
|---|---|---:|---:|---:|---|---|
| R1 | Un cambio del prompt debilita los limites y provoca recomendaciones no confiables. | 3 | 4 | 12 | ALTO | Si |
| R2 | Las trazas guardan en texto claro ideas ineditas, consultas y respuestas del creador. | 3 | 4 | 12 | ALTO | Si |
| R4 | Un guion o titulo sugiere afirmaciones o resultados que el creador no puede respaldar. | 3 | 3 | 9 | ALTO | Si |
| R3 | Texto malicioso incorporado al contexto RAG intenta alterar la respuesta del copiloto. | 2 | 4 | 8 | MEDIO | Si |
| R5 | Una sugerencia de estructura o duracion se interpreta como una prediccion de retencion real. | 3 | 2 | 6 | MEDIO | Si |

## R1 Un cambio del prompt debilita los limites y provoca recomendaciones no confiables.

**Justificacion**: Un cambio de instrucciones puede quitar las restricciones sobre metricas o promesas al creador.

**Mitigacion**: Registrar huellas y diff; activar solo la huella exacta aprobada en src/registro_prompts.py y src/grafo_supervision.py (Bloque 32).

**Supervision**: El responsable funcional revisa el diff y las pruebas; debe aprobar la huella exacta antes de activar la version.

**Responsable**: Responsable funcional del copiloto

**Evidencia**: Pruebas de pausa, aprobacion, rechazo y huella revisada en tests/test_bloque32.py.

**Estado**: Control local implementado; almacenamiento del checkpoint en memoria y activacion en un solo equipo.


## R2 Las trazas guardan en texto claro ideas ineditas, consultas y respuestas del creador.

**Justificacion**: mi_agente.py registra entrada, argumentos de herramientas y respuesta; registro_rag.py guarda pregunta y respuesta.

**Mitigacion**: No compartir trazas con datos reales; logs_rag.py ya registra huellas y longitudes, pero no esta conectado a los otros dos registros. Minimizar y limitar acceso sigue pendiente.

**Supervision**: El custodio de datos revisa y redacta las trazas antes de exportarlas o compartirlas; hasta entonces se mantienen locales.

**Responsable**: Custodio de datos del proyecto

**Evidencia**: Inspeccion de registrar_traza en src/mi_agente.py y de registrar_consulta en src/registro_rag.py.

**Estado**: Riesgo vigente: los registros del agente y del medidor RAG conservan contenido sin redactar.


## R4 Un guion o titulo sugiere afirmaciones o resultados que el creador no puede respaldar.

**Justificacion**: Una recomendacion generada puede sonar convincente aunque no coincida con el contenido real del video.

**Mitigacion**: El prompt versionado prohíbe inventar metricas y promesas; revisar cada afirmacion contra fuentes antes de publicar (Bloque 32).

**Supervision**: El creador verifica guion, titulo y descripcion frente a fuentes confiables y al contenido final antes de subir el video.

**Responsable**: Creador o editor del canal

**Evidencia**: Restricciones de exactitud en el prompt actual de src/registro_prompts.py y en src/mi_agente.py.

**Estado**: El prompt reduce el riesgo, pero no verifica los hechos de cada guion.


## R3 Texto malicioso incorporado al contexto RAG intenta alterar la respuesta del copiloto.

**Justificacion**: El contexto recuperado se concatena con la consulta y se envia al modelo; el corpus actual es local, pero una fuente futura puede incluir instrucciones hostiles.

**Mitigacion**: Revisar manualmente las fuentes antes de indexarlas con src/preparar_rag_youtube.py. El prompt de src/registro_rag.py limita la respuesta al contexto y pide abstenerse, pero aun no hay un filtro anti-inyeccion.

**Supervision**: El responsable del corpus revisa origen y contenido antes de cada indexacion o actualizacion.

**Responsable**: Responsable del corpus

**Evidencia**: Inspeccion del prompt RAG y del corpus local data/conocimiento_youtube.md.

**Estado**: Revision de fuentes manual; delimitacion y deteccion automatica de inyecciones pendientes.


## R5 Una sugerencia de estructura o duracion se interpreta como una prediccion de retencion real.

**Justificacion**: El copiloto puede planificar ritmo y duracion, pero la retencion solo se mide con analiticas de un video publicado.

**Mitigacion**: La herramienta crear_estructura_video y data/conocimiento_youtube.md indican que la estructura es orientativa y no predice retencion.

**Supervision**: Comparar las recomendaciones con analiticas reales despues de publicar; no tomar decisiones de rendimiento basandose solo en la estimacion.

**Responsable**: Creador o analista del canal

**Evidencia**: Advertencias incluidas en crear_estructura_video de src/mi_agente.py y data/conocimiento_youtube.md.

**Estado**: Advertencia implementada; no existe conexion automatica a analiticas de YouTube.

