# Verificación ME r222b_wrappers_regression

**Base:** 10ccda8 (R220/R222/R223). **Método:** MTS + gate de compilación.
**Tests existentes:** no modificados. **Alcance:** `opensyn/router.syn`,
`nucleo/lsp_v3.syn` y baseline de Fase 32.

## Marcas por requisito

- Manual 7 §2.4 R1 el router compila y enruta usando `std.texto`: CUMPLE.
  `opensyn/router.syn` ya no redeclara `cmp_texto`, `strstr_f` ni `atoi_f`
  (evidencia `opensyn/router.syn:26`; oráculo
  `tests/auditoria/test_oraculos_r222b_wrappers.py`).

- Manual 7 §4.2 R2 el router procesa la respuesta para extraer código: CUMPLE.
  conserva sus llamadas de comparación/búsqueda resueltas por `std.texto`
  (evidencia `opensyn/router.syn:854`; oráculo
  `tests/auditoria/test_oraculos_r222b_wrappers.py`).

- Manual 8 §1 R3 el LSP nativo compila sin dependencias duplicadas: CUMPLE.
  `nucleo/lsp_v3.syn` usa la única definición pública `cmp_texto` de
  `std.texto` (evidencia `nucleo/lsp_v3.syn:1106`; oráculo
  `tests/auditoria/test_oraculos_r222b_wrappers.py`).

- Manual 1 §6 R4 el compilador no oculta deuda de producción: CUMPLE.
  `tests/fixtures/compilacion_baseline.txt` queda vacío y el gate de Fase 32
  compila todos los módulos (evidencia
  `tests/fixtures/compilacion_baseline.txt:9`; oráculo
  `tests/auditoria/test_oraculos_r222b_wrappers.py`).

## Validación ejecutada

- Oráculo propio: `tests/auditoria/test_oraculos_r222b_wrappers.py` 3/3 GREEN
  (router compila, LSP compila y baseline vacío).
- Gate Fase 32: `tests/integration/test_compilacion_fase32.py` 2/2 GREEN
  (antes 1 failed/1 passed).
- Regresión dirigida: 57/57 GREEN en router, LSP (unit/integration) y
  `test_std_contracts.py`.
- Gates:
  - `python auditoria/contrastar.py --plan docs/plan_ME_r222b_wrappers_regression.md`.
  - `python auditoria/alineacion.py --verificar --me r222b_wrappers_regression`.
  - `python auditoria/verificar_alineacion.py`.

## Hallazgos

- H-R222b-1 (resuelto): R222 restauró los wrappers en `std/texto.syn` sin
  retirar los duplicados locales de `opensyn/router.syn` y
  `nucleo/lsp_v3.syn`; el gate de Fase 32 quedó rojo y `lsp_v3` dejó de
  compilar. La corrección elimina la duplicación, no el gate.
- H-R222b-2 (resuelto): R219 dejó `opensyn/verificacion_aot.syn` compilando
  pero aún en el baseline; el gate lo reportaba como TRIQUETE. El baseline
  queda vacío.
