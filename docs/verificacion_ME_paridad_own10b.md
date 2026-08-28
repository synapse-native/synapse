# verificacion_ME_paridad_own10b — ME-P1 (unificar codigo canonico, aditivo)

CUMPLE Manual 2 §9 — codigo canonico de uso tras move unificado en la taxonomia.

| Requisito (ME-P1) | Archivo | Estado |
|-------------------|---------|--------|
| Renombrar ex-ACCESO_MEMORIA_MOVIDA(23) -> ERR_MEM_USE_AFTER_MOVE | nucleo/errores.syn, nucleo/diagnostics.syn | CUMPLE |
| Mapeo S1<->nativo en generator.py | compilador/generator/generator.py | CUMPLE |
| Marcador LSP [ERR_LIFETIME] | synapse_lsp/features/diagnostics.py | CUMPLE |

## Validacion

- Lado S1/LSP: `py_compile` OK; tests/unit/test_lsp_f12.py -> 19 passed (el
  codigo ERR_SEM_VAR_MOVIDA sigue presente y el nuevo ERR_MEM_USE_AFTER_MOVE
  entra al set de ownership).
- Gate MTS (auditoria/contrastar.py --plan docs/plan_ME_paridad_own10b.md): rc=0
  (oraculo existe, citas de cumplimiento presentes, verificar_alineacion 0 brechas).
- Build nativo: `python main.py nucleo/principal.syn -o synapse_stage1.exe`
  genero el ejecutable modular (`[OK] Ejecutable modular generado:
  synapse_stage1.exe`); el modulo C regenerado `_diagnostics.c` contiene
  `#define ERR_MEM_USE_AFTER_MOVE (23LL)`. El compilador nativo COMPILA con el
  codigo renombrado. (El estado "failed" del proceso en background fue un
  artefacto de PowerShell: un warning de gcc en stderr convertido en error de
  pipeline; el enlazado fue exitoso.)

## ME-P2 (CUMPLE 2026-08-27, tests inmutables aprobados por Arquitecto)

- Emision nativa cambiada en nucleo/analizador_semantico.syn:679 ->
  ERR_MEM_USE_AFTER_MOVE (E-504); mensaje "(E-504)" en vez de "(E-501)".
- tests/integration/test_fase2_nativa_hm.py: references E-501/ERR_SEM_VAR_MOVIDA
  actualizadas a E-504/ERR_MEM_USE_AFTER_MOVE (0 restantes).
- Validacion: rebuild nativo (`python main.py nucleo/principal.syn -o
  synapse_stage1.exe`, ejecutable regenerado 19:13:30); pytest
  tests/integration/test_fase2_nativa_hm.py -k "r14 or r15" -> 10 passed.
  Paridad S1<->nativo en use-after-move CONSEGUIDA (ambos ERR_MEM_USE_AFTER_MOVE).

## ME-P3 (pendiente)

- Decidir destino de ERR_SEM_VAR_MOVIDA (22): tras ME-P2 ya no se emite para
  use-after-move; eliminar o alias (regla codigo muerto) actualizando
  nucleo/diagnostics.syn. Alinear mensaje S1 ERR_MEM_USE_AFTER_MOVE para
  quitar "por lanzar/concurrencia". Oráculos: suite HM nativa + ownership S1
  21/21 + test_spawn + test_concurrency_10.

H-OWN-10b (parcial): ME-P1 CUMPLE, ME-P2 CUMPLE (paridad alcanzada), ME-P3 abierto.
