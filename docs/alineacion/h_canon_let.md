# Expediente de alineación h_canon_let

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: ad34c2eb084787cf

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## compilador/canonical.py
- manual: 2
  seccion: 13
  cita: "Código fuente (`programa.syn`):"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/canonical.py:201
  oraculo: tests/integration/test_codegen_embebido_d_f1c.py
  nota: decisión ratificada en bitácora (175d268, precedente test_codegen_embebido_d_f1c: "M2 §13 (175d268): el formato canonico es plano, sin wrapper {synapse,ast}"); el índice de M2 §13 no indexa los bloques JSON del ejemplo (solo prosa), por lo que la oración de código fuente es la única citable del §13; mapa de alineación actualizado (compilador/canonical.py -> Manual 2 §13) porque el mapa anterior (compilador/* -> Manual 1 entero) carecía de sección puntual
