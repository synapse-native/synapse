# Verificación ME-control_solido — endurecimiento del sistema de control

Fecha: 2026-09-14 · Verificador: `auditoria/contrastar.py` (gate MTS fase 4b)
Oráculo: `tests/auditoria/test_gate_mts_oraculos.py` — **GREEN (15 passed)**

## Manual 7 §2.3 — CUMPLE
Los oráculos del plan se EJECUTAN, no se declaran:
- `auditoria/contrastar.py::ejecutar_oraculo` — pytest en modo release; SKIP /
  "no tests ran" / rc!=0 => FAIL; scripts con contrato de marca de verificación
  (OK/PASS/SIN BRECHAS).
- CI: `alineacion.py --verificar` SIN `--sin-oraculos`; pre-commit corre
  oráculos por defecto (opt-out explícito `ALINEACION_ORACULOS=0`).
- Oráculo: `tests/auditoria/test_gate_mts_oraculos.py` (oráculo vacío, skip y
  fallido => rechazados; verde => aceptado).
- Evidencia: `auditoria/contrastar.py:ejecutar_oraculo`; 4 ejecuciones GREEN en
  el gate (salida "✅ Oráculo ejecutado (release)").

## Manual 2 §12 — CUMPLE
Trazabilidad anti-fabricación y cobertura total:
- `verificar_alineacion.py`: `.syq` en PROD_EXTS; `nonnull_base` (base CI vacía
  degrada a HEAD~1); bitácora con fecha completa (regex AAAA-MM-DD, sin
  hardcode 2026); D-9 ampliado (opensyn/, syquex/, runtime/core/*.c; MODULOS_D9
  acepta .c y registra los 11 módulos >1200 líneas reales).
- `contrastar.py`: vínculo ESTRICTO archivo↔plan (multi-plan con --plan
  repetible; el hook y el CI pasan TODOS los planes staged juntos); producción
  staged filtrada por `_es_produccion`.
- Oráculo: `test_nonnull_base_en_ambos_gates`, `test_d9_acepta_runtime_c`,
  `test_cubre_req_exige_manual_coincidente`, `test_parsear_plan_mantiene_oraculos_por_bloque`.
- Evidencia: `auditoria/verificar_alineacion.py` — SIN BRECHAS con la rama staged completa.

## Manual 8 §1.2 (convención de gates con oráculo) — CUMPLE
MTO autenticado y registrado:
- Nueva entrada OBL-MCTRL-01..04 en `docs/manuales/MANUAL_TESTS_OBLIGATORIOS.md`
  (aditiva, según su regla de mantenimiento).
- `auditar_calidad_tests.py --solo-mto` como paso BLOQUEANTE del pre-commit y del CI.
- SIN_OBL fatal en modo incremental (todo test nuevo/modificado cita su OBL).
- Oráculo: `test_mto_valido_pasaria_solo_mto`, `test_sin_obl_detectado_en_modo_incremental`,
  `test_con_obl_no_reporta_sin_obl`.
- Evidencia: `auditoria/auditar_calidad_tests.py --solo-mto` — 45 entradas OBL validadas.

## Manual 6 §5 (evidencia atada al contenido) — CUMPLE
- `alineacion.py`: mismatch de cambio_hash BLOQUEA (era aviso); sello de lectura
  previa con frescura (expira al día siguiente, fecha futura rechazada, sello
  posterior al código detectado); `evidencia_ci_ok` exige evidencia COMITEADA
  en CI con el mismo cambio_hash y sin oráculos fallidos; `--exigir-sello` en
  el pre-commit.
- Oráculo: `test_sello_expirado_rechazado`, `test_sello_corrupto_rechazado`,
  `test_evidencia_ci_ausente_bloquea`.

## CI corregido
- Job `auditoria`: paso `id: base` PROPIO añadido (antes usaba steps.base sin
  definirlo => gate muerto con 0 brechas falsas) + fallo por exit code (pipefail).
- Job `alineacion`: `--sin-oraculos` ELIMINADO; oráculos ejecutan en CI.
- Job `mts-contraste`: `.syq` en producción; TODOS los planes staged contrastados juntos.
- Job `trazabilidad-codigo`: `.syq` incluido.
- Branch protection documentado: `docs/GOBERNANZA_BRANCH_PROTECTION.md`.

## Deuda visible (requiere ratificación del Arquitecto; NO corregida aquí)
1. MTO cita 10 secciones renumeradas inexistentes (Manual 7 §6.3/§7, Manual 8
   §6.3, Manual 9 §9) — AVISO visible en --solo-mto; corregir exige regla 5.
2. 30 entradas GREEN del MTO sin test citador (deuda heredada) — AVISO visible.
3. 15 SNIFF_AMP en tests heredados (asserts de literal sin ejecutar) —
   `--estricto-sniff` los hace fatales al ratificarse.
4. `tests/test_auditoria_alineacion.py::test_seccion_es_de_manual` falla por
   construcción del propio test (busca "§" en cadena sin §) — INMUTABLE sin
   aprobación (regla 5). Preexistente a esta sesión, verificado en HEAD.
