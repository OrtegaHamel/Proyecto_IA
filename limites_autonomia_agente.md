# Límites de autonomía: Copiloto para creadores de YouTube

**Revisión:** Noviembre de 2026  
**Código revisado:** `src/mi_agente.py`

## Alcance actual

El agente usa Gemini para proponer guiones, títulos, descripciones y estrategias de
preproducción. No se conecta a YouTube Studio, no publica ni edita videos y no
realiza compras, pagos u otras acciones externas mediante herramientas.

Las tres herramientas disponibles solo calculan o revisan información local.
Por eso, en la implementación actual no hay herramientas de escritura reversible
ni de escritura irreversible con impacto económico.

## Herramientas y nivel de riesgo

- `calcular_duracion_guion`: **solo lectura (riesgo bajo)**. Calcula un rango
  estimado a partir del número de palabras; no modifica ni guarda el guion.
- `crear_estructura_video`: **solo lectura (riesgo bajo)**. Calcula bloques
  temporales orientativos; no modifica ni publica el video.
- `revisar_titulo`: **solo lectura (riesgo bajo)**. Comprueba longitud y presencia
  de una palabra clave; no cambia ni publica el título.

## Herramientas que requieren aprobación humana

Ninguna de las herramientas actuales requiere aprobación antes de ejecutarse:
solo producen cálculos o recomendaciones y no generan cambios externos.

La revisión editorial humana sí debe ocurrir antes de publicar cualquier contenido
generado, para comprobar exactitud, tono, derechos y que las promesas del guion
correspondan a recursos o compromisos reales del canal. Esto es una revisión del
contenido, no una aprobación de una acción ejecutada por una herramienta.

`mi_agente.py` no implementa `esperar_aprobacion`; no se necesita para las
herramientas actuales. Si se agrega una herramienta que publique, modifique datos
del canal o genere un gasto, se debe reclasificar el riesgo e implementar una
confirmación humana antes de ejecutarla. Ante timeout o rechazo, la acción debe
cancelarse.

## Revisión de trazas

- **Frecuencia:** revisar las trazas cada 10 interacciones o al menos una vez por
  semana; revisar de inmediato después de una respuesta o llamada inesperada.
- **Qué revisar:** que la herramienta elegida corresponda a la consulta; que sus
  argumentos estén dentro de los límites esperados; que la observación respalde
  la respuesta final; y que no haya llamadas repetidas, argumentos extraños ni
  promesas de recursos no confirmados.
- **Datos y almacenamiento:** `trazas_agente.jsonl` guarda fecha, sesión, entrada
  del usuario, argumentos y observaciones de las herramientas y respuesta final.
  No introducir claves, tokens ni otra información sensible en las consultas,
  que también se envían a Gemini. Aunque `.gitignore` contiene una regla para
  este archivo, `trazas_agente.jsonl` ya está bajo seguimiento de Git en este
  repositorio; la regla no impide que sus cambios se incluyan en un commit.
  No añadir ni confirmar el archivo de trazas sin revisar su contenido.

### Evidencia disponible

Al revisar `trazas_agente.jsonl` el 25 de noviembre de 2026, encontré tres líneas
JSON válidas y una llamada a cada herramienta:

- `crear_estructura_video`, con `duracion_minutos: 8`.
- `calcular_duracion_guion`, con `palabras: 900`.
- `revisar_titulo`, con el título `Aprende Python desde cero` y la palabra clave
  `Python`.

Esto confirma que se ejecutaron y registraron todas las herramientas disponibles.
No hay herramientas de escritura reversible ni de impacto económico que probar.

En Windows PowerShell, se pueden comprobar las líneas y llamadas así:

```powershell
(Get-Content .\trazas_agente.jsonl | Measure-Object -Line).Lines
(Select-String -Path .\trazas_agente.jsonl -Pattern '"herramienta": "crear_estructura_video"').Count # 1
(Select-String -Path .\trazas_agente.jsonl -Pattern '"herramienta": "calcular_duracion_guion"').Count # 1
(Select-String -Path .\trazas_agente.jsonl -Pattern '"herramienta": "revisar_titulo"').Count # 1
```

## Qué hacer ante un comportamiento inesperado

1. Detener la ejecución escribiendo `salir` o con `Ctrl+C`.
2. Conservar y revisar la traza correspondiente: comparar la entrada, herramienta,
   argumentos, observación y respuesta final.
3. Si la llamada fue improcedente, retirar temporalmente esa herramienta de
   `herramientas` en `src/mi_agente.py` y reiniciar el proceso.
4. Corregir la descripción o el esquema de argumentos de la herramienta y, si el
   problema fue de contenido, ajustar las instrucciones del sistema para limitar
   esa respuesta.
5. Probar de nuevo con entradas válidas y casos límite; volver a habilitar la
   herramienta solo después de comprobar el resultado.
6. Si una futura herramienta puede escribir, publicar o gastar dinero, mantenerla
   deshabilitada hasta implementar y probar una aprobación humana previa.
