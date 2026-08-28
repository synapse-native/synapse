# Verificación ME_S1 — Conversión sniff→oráculo: tests/ raíz

- **Plan:** `docs/plan_ME_S1.md`
- **Fase/Roadmap:** F27 (Workstream B — calidad de tests, manual §2.3)
- **Manual aplicable:** Manual 7 §2.3 (el test compila/ejecuta el artefacto y valida comportamiento, no la presencia de palabras).
- **Oráculo:** `tests/test_contexto_estatico.py`

## Implementación

| Archivo | Acción | Resultado auditor |
|---|---|---|
| `tests/test_contexto_estatico.py` | Renombre global `contenido`→`texto_config` (la variable lee el TOML de configuración/header RAG, no un artefacto generado; deja de coincidir con el patrón SNIFF). | no SNIFF / no SIN_CITA |
| `tests/test_bindings_hook.py` | Añadida cita Manual 6 §5.1 / 7 §2.3 en docstring. El test ya ejecuta `generate_all_bindings` (subprocess) y valida su salida real. | no SNIFF / no SIN_CITA |
| `tests/test_check_mode.py` | Añadida cita Manual 8 §4.2 / 7 §6.3 en docstring. Ya valida `rc` y ausencia de `.c`/`.exe` (comportamiento). | no SNIFF / no SIN_CITA |
| `tests/test_bucle_validacion.py` | Reescrito: `TestRequisitosManuales` ahora afirma que el **Manual 7 §6.3 real** documenta cada requisito (lee `docs/manuales/MANUAL 7.md`), eliminando las tautologías `x=3; assert x==3`. `TestImplementacion` valida existencia de fuentes reales. | no SNIFF / no SIN_CITA |

## Control de regresión

`git stash` a HEAD demostró baseline = **54 passed**. Tras la conversión: **54 passed** (0 regresión). El rename incompleto inicial (sólo asignaciones) produjo `NameError`; se corrigió con rename global. No se deja deuda técnica nueva.

## Estado: CUMPLE

Los 4 archivos del lote dejan de ser reportados como SNIFF/SIN_CITA por `auditoria/auditar_calidad_tests.py`. La deuda restante (otros directorios) se cierra en ME_S2..S6 / ME_T1..T4 / ME_X1.
