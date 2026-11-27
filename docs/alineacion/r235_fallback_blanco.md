# Expediente de alineación r235_fallback_blanco

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 8bffa132a1f1f3df

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## runtime/core/ollama.c
- manual: 7
  seccion: 2.2
  cita: "Extraer el campo `content` o `completion` de la respuesta JSON."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/ollama.c:869
  oraculo: tests/auditoria/test_oraculos_r235_fallback_blanco.py
  ejecucion: pytest

- manual: 7
  seccion: 2.2
  cita: "Retornar la respuesta como string."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/ollama.c:969
  oraculo: tests/auditoria/test_oraculos_r235_fallback_blanco.py
  ejecucion: pytest

## Nota de alineación

El smoke real de R227 mostró que `/v1/chat/completions` puede responder
`content: "\n\n"` o solo `<|im_end|>`; aceptados por `longitud > 0` impedían el
fallback `POST /completion` que el Manual 7 §2.2 exige. Ahora solo un contenido
con texto útil se extrae y se retorna como respuesta; el resto reintenta
`/completion` y, si tampoco hay texto, se devuelve cadena vacía (el llamador
.syn reporta "sin respuesta" en lugar de una burbuja fantasma).
