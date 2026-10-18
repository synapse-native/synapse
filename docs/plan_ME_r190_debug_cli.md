# PLAN ME r190 — debug_cli_sesion (H-R184, 4 RED de test_cli_run_debug)

**Base:** 4662e00 (docs r188b). Mandato de dirección vigente (plan maestro):
los tests SOLO se modifican para ALINEARLOS al manual; deuda de R184 medida
en vivo: `test_cli_run_debug` 4 RED (help/step/reverse/snapshots rc=1 —
feature gap del dispatcher).

## R1 — ayuda del debugger accesible sin sesión

requisito: Manual 8 §3.4 (comandos del debugger: --load/--step/--reverse/
--snapshots) + Manual 8 §4.2 (ayuda del CLI unificado).
texto: "El CLI unificado (`synapse`) incluye comandos para depuración:
`synapse debug --load ejecucion.trace` … `synapse debug --snapshots`"
(M8 §3.4 L370-389).
implementacion: cli.py — el bloque de AYUDA (consulta) se evalúa ANTES del
requisito de traza, cuando no hay subcomando ni flags de navegación
(--load/--step/--reverse/--snapshots); rc=0 con el listado §3.4.
Contrato con el oráculo r150 (inmutable): la navegación sin traza MANTIENE
rc!=0 + "no hay traza cargada" — no teatro (R150 L319-320).
oraculo: tests/auditoria/test_oraculos_r190.py (r1 ayuda rc=0; r2 navegación
sin traza rc!=0; r3 flujo canónico --load → --step "#0 x=42" → --reverse
vuelve a #0 → --snapshots con variable real).

## Checklist de cierre (fase 4b + 5)

- `alineacion.py --leer --me r190` (sello + lectura dirigida)
- lecturas previas del día POR ARCHIVO según mapa (cli.py→M1 §3.1;
  tests→M8 §3.4)
- oráculo r190 3/3 + test_cli_run_debug 16/16 + oráculo r150 14/14 (contrato
  r150 fiel) + check focal (check_cli)
- expediente: NO APLICABLE — verificado con --nuevo: el gate considera
  producción solo nucleo/*.syn (cli.py/tests no entran); gates = contrastar
  + verificar_alineacion + lectura previa cli.py (M1 §3.1, registrado)
- contrastar --plan docs/plan_ME_r190_debug_cli.md RC=0
- verificar_alineacion SIN BRECHAS
