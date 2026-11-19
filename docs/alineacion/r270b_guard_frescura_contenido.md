# Expediente de alineación r270b_guard_frescura_contenido

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash:

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## build.py
- manual: 9
  seccion: 6.2
  cita: "La verificación del bootstrap (diff 0 bytes)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: build.py:75
  oraculo: tests/auditoria/test_r270b_frescura_contenido.py

- manual: 9
  seccion: 2.3
  cita: "Verificar el bootstrap (diff 0 bytes entre Stage 2 y Stage 3)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: build.py:70
  oraculo: tests/auditoria/test_r270b_frescura_contenido.py

- manual: 1
  seccion: 6
  cita: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0). El determinismo se verifica obligatoriamente en la CI mediante la comparación de los hashes SHA‑256 de las etapas 2 y 3."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: build.py:72
  oraculo: tests/auditoria/test_r270b_frescura_contenido.py
