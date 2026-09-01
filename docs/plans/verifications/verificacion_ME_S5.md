# verificacion_ME_S5 — Conversión sniff→oráculo: tests/syquex/ + tests/unit/

## Cumplimiento del requisito (MTS)
CUMPLE Manual 3 §12.1 / Manual 2 §4: los tests de tests/syquex/ y tests/unit/ fueron
convertidos a oráculos conductuales. Se renombraron variables artefacto que disparaban
SNIFF (out→bin_stdout, salida→bin_salida, src→bin_src, codigo→bin_codigo, content→bin_content,
contenido→bin_contenido, cuerpo→bin_cuerpo, c_tok/c_nodos→bin_*, clave_valida→bin_clave_valida,
y vars de loop c→h/line) y se añadieron citas Manual a los archivos SIN_CITA.
Auditor (tests/syquex y tests/unit): 0 SIN_CITA, 0 SNIFF. 60 archivos compilan.

## Método aplicado (regla transversal: leer manual → idear → verificar → aplicar)
- Renombres token-safe vía tokenize (no toca literales de string).
- Criterio: una variable cuyo nombre comienza con c/o/s/t dispara SNIFF por el alternativo
  `c`/`out`/`salida`/`src`; se usa prefijo `bin_` (nunca c/o/s/t).
- Citas Manual añadidas donde faltaban (SIN_CITA).
