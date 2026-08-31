# Verificación ME_29_T5 — opensyn/installer.syn

## Requisitos
- **CUMPLE** Manual 7 §2.3 — Pipeline RAG (`synapse_rag.c`) y arquitectura OpenSyn
- **CUMPLE** Manual 9 §5.2-§5.4 — Selección de modelo según VRAM

## Cambios
1. `opensyn/installer.syn` — Instalador OpenSyn (estructuras `HardwareInfo`/`ModeloInfo`, detección vía `externo _syn_*`, selección por VRAM, selección de hilos/capas GPU).
2. `tests/opensyn/test_installer.py` — Corregido helper `_compilar_syq` (ruta de salida para `.syn` en subdirectorios).
3. `compilador/generator/emit_expressions.py:84-93` — Fix bug H-F29-T5a: `tipo_de_expr` en `ExprAccesoCampo` aceptaba sólo `"struct X"`, fallando a `"int"` para tipos Synapse puros. Acepta `"X"` y `"struct X"` (Manual 2 §3).
4. `docs/plan_ME_29_T5.md` — Plan MTS con bloque `requisito:/texto:/implementacion:/oraculo:` + nota de hallazgos.

## Validación
- Compila `opensyn/installer.syn` → `tests/fixtures/installer.exe` rc=0.
- Ejecución rc=0; salida contiene `Hardware:` `Modelo:` `Hilos:` `Capas GPU:`.
- `tests/opensyn/test_installer.py::test_installer_opensyn` GREEN.
- Gate MTS (`auditoria/contrastar.py --plan`): PASS.
- `auditoria/verificar_alineacion.py`: 0 brechas.
- Tests opensyn restantes: 9 RED TDD (ME_29_T1/T2/T3, fuera de alcance).

## Hallazgos
- **H-F29-T5a (CORREGIDO)**: `tipo_de_expr` colapsaba `ExprAccesoCampo` a `int` cuando el tipo Synapse no tenía prefijo `struct `. Fix mínimo en `emit_expressions.py`.
- **H-F29-T5b (REGISTRADO, no resuelto)**: bug RAII preexistente en `runtime/core/sistema.c:24 concat()` con CadenaSegura retornada por FFI → "malloc fallo en concat()" cuando se concatena múltiples veces el mismo campo texto. Workaround en installer: prefijos como literales separados, valores en líneas siguientes. Deuda D-F29-T5b propuesta para ME aparte.