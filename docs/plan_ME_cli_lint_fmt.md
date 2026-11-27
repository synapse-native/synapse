# Plan MTS — ME cli_lint_fmt

> Deuda #2 de `docs/reportes/FASE_33_CERTIFICACION.md` §5 (prioridad tras formatter_fix):
> "cli.py sin lint/fmt Python — el dispatcher Python no despacha lint/fmt". Hoy
> `python cli.py lint --fix x.syn` trata "lint" como ARCHIVO a compilar
> ("Archivo no encontrado: lint") y retorna rc=0 (sonda 2026-09-29).

requisito: Manual 8 §4.1 (tabla de comandos principales)
texto: "| **`synapse lint`** (Fase 31) | Ejecuta el linter nativo sobre el código fuente. |"
implementacion: cli.py `main()`: despachar `synapse lint <archivo>` al backend nativo
  (stage2 del bootstrap, backend de módulos .syn desde r153/Opción A) — flags --fix,
  salida del linter propagada tal cual, rc propagado (0 limpio, 1 con advertencias);
  archivo inexistente → rc=1 (hoy rc=0 falso). Comentario `# cumple Manual 8 §4.1`.
oraculo: tests/auditoria/test_oraculos_cli_lint_fmt.py

requisito: Manual 8 §4.1 (tabla de comandos principales)
texto: "| **`synapse fmt`** (Fase 31) | Ejecuta el formateador nativo sobre el código fuente. |"
implementacion: cli.py `main()`: despachar `synapse fmt <archivo>` al mismo backend —
  `--check` rc=0 formateado / rc=1 no formateado (sin reescritura), fmt in-place
  reescribe; orden canónico flags-ANTES-de-archivo (H-33.5-2) y el antiguo
  (archivo-antes-de-flags) ambos aceptados, paridad con el dispatcher nativo.
  Comentario `# cumple Manual 8 §4.1`.
oraculo: tests/auditoria/test_oraculos_cli_lint_fmt.py

requisito: Manual 1 §6 (regla de hierro del bootstrap)
texto: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0). El determinismo se verifica obligatoriamente en la CI mediante la comparación de los hashes SHA‑256 de las etapas 2 y 3."
implementacion: cli.py `_bootstrap_stage2_fresco()`: backing on-demand del stage2 con
  el comando EXACTO del job bootstrap del CI (convención tests/unit/test_r3_param_adt.py
  y tests/nucleo/test_modulos_compilan.py) — reconstruye S1 (python main.py
  nucleo/principal.syn -o synapse_stage1.exe) y S2 (stage1 principal -o stage2) SOLO si
  faltan o quedaron stale (mtime de nucleo/*.syn + nucleo/generador/*.syn > exe);
  si están frescos NO recompila. Comentario `# cumple Manual 1 §6`.
oraculo: tests/auditoria/test_oraculos_cli_lint_fmt.py (escenario del hook: stage1
  ausente + stage2 fresco → rebuild on-demand y despacho operativo)

requisito: Manual 8 §4.1 (comandos sobre el fuente, evidencia E2E)
texto: "| `synapse build <archivo>` | Compila el archivo (`.syn` o `.syq`) a binario. |"
implementacion: oráculo NUEVO tests/auditoria/test_oraculos_cli_lint_fmt.py — E2E real
  invocando `python cli.py lint/fmt` sobre probes: lint limpio rc=0, lint con
  indentación mala rc=1 + WARN_LINT_*, fmt --check rc 0/1 en ambos órdenes, fmt
  in-place byte a byte e idempotente, lint --fix == fmt (paridad), archivo
  inexistente rc=1, `lint` sin archivo rc=1 (NO "archivo no encontrado: lint"),
  anti-fabricación: la salida lleva la marca nativa ([Lint]/[Fmt]) y el escenario
  on-demand reconstruye con el comando del CI.
oraculo: tests/auditoria/test_oraculos_cli_lint_fmt.py

## Notas de alcance
- NO se tocan los tests inmutables; el oráculo es NUEVO.
- El backend del trabajo es el nativo (nucleo/lint.syn + nucleo/formatter.syn, ya
  verificados en 58ff1d1): el dispatcher Python NO reimplementa lint/fmt (no se
  inventa código a medias — lección de FASE_33_CERTIFICACION §5).
- cli.py es producción de mapa puntual: NO aparece en mapa_alineacion.md ni en el
  legacy → requisitos_vacio() del gate de alineación (contrastar exige la cita
  `// cumple Manual 8 §4.1` / `# cumple Manual 1 §6` colectable; el expediente del ME
  declarará 0 requisitos exigidos, con las anclas igualmente registradas).
