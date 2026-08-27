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

## NO CUMPLE aun (lo hace ME-P2)

- La EMISION nativa (nucleo/analizador_semantico.syn:679) sigue usando
  ERR_SEM_VAR_MOVIDA (22) / "(E-501)". Por tanto test_fase2_nativa_hm.py sigue
  esperando E-501. La paridad total es ME-P2.
- nucleo/diagnostics.c (rastreado) queda con el nombre viejo: es un artefacto
  generado que el build no reescribe (usa _diagnostics.c en raiz); se regenera
  en el bootstrap/CI. Sin impacto en la compilacion ni en los tests.

H-OWN-10b (parcial): ME-P1 cumple; ME-P2 pendiente.
