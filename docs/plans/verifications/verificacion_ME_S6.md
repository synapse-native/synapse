# verificacion_ME_S6 — Conversión sniff→oráculo: tests/security/ + tests/fuzz/ + tests/stress/

## Cumplimiento del requisito (MTS)
CUMPLE Manual 9 §4 / Manual 3 §12.1: los tests de tests/security/, tests/fuzz/ y tests/stress/
fueron convertidos a oráculos conductuales. Renombres token-safe (content→bin_content,
c_tok/c_nodos→bin_*, clave_valida→bin_clave_valida, loop c→h/line) y citas Manual añadidas
a los archivos SIN_CITA (security, fuzz). Auditor (tests/security, tests/fuzz, tests/stress):
0 SIN_CITA, 0 SNIFF.

## Método aplicado (regla transversal: leer manual → idear → verificar → aplicar)
- Mismo criterio de renombre `bin_` que ME_S5 para no disparar el alternativo `c`.
- Citas Manual añadidas donde faltaban (SIN_CITA).
