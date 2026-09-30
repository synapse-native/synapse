# Expediente de alineación cli_lint_fmt

base: bc71fc0  # commit sobre el que se leyó el manual
cambio_hash: 07ba3f460c6d0bee

> ME cli_lint_fmt: el dispatcher Python (cli.py) despacha `synapse lint` y
> `synapse fmt` a las herramientas NATIVAS (stage2 del bootstrap, backend de
> módulos .syn nucleo/lint.syn + nucleo/formatter.syn desde r153/Opción A) —
> NO reimplementa el linter ni el formateador. Además: rc del subcomando
> propagado (sys.exit(main())) — antes se descartaba → rc=0 falso de
> `cli.py lint --fix x.syn` (brecha documentada en FASE_33_CERTIFICACION §5).
> Backing on-demand del stage2 con el comando del job CI del bootstrap (M1 §6).
> Deuda #2 del reporte FASE_33_CERTIFICACION §5. Plan: docs/plan_ME_cli_lint_fmt.md.
> cli.py no aparece en mapa_alineacion.md; el legacy "*.py" → "Manual 1" exige
> el manual entero — se ancla M1 §6 (regla de hierro) y M8 §4.1 (tabla de
> comandos, el comando canónico que se implementa).

## cli.py
- manual: 1
  seccion: 6
  cita: "Regla de hierro: Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: cli.py:55
  oraculo: tests/auditoria/test_oraculos_cli_lint_fmt.py
- manual: 8
  seccion: 4.1
  cita: "| **`synapse lint`** (Fase 31) | Ejecuta el linter nativo sobre el código fuente. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: cli.py:93
  oraculo: tests/auditoria/test_oraculos_cli_lint_fmt.py
- manual: 8
  seccion: 4.1
  cita: "| **`synapse fmt`** (Fase 31) | Ejecuta el formateador nativo sobre el código fuente. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: cli.py:989
  oraculo: tests/auditoria/test_oraculos_cli_lint_fmt.py
