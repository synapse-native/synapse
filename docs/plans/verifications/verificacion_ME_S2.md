# Verificación ME_S2 — Conversión sniff→oráculo: tests/opensyn/

- **Plan:** `docs/plan_ME_S2.md`
- **Fase/Roadmap:** F27 (Workstream B — calidad de tests, Manual 7 §2.3 / §7)
- **Manual aplicable:** Manual 7 §2.3 (oráculos reales sobre la API ya implementada, no content-sniff) y Manual 7 §7.
- **Oráculo:** `tests/opensyn/test_inference.py`

## Implementación

Archivos convertidos: `test_inference.py`, `test_download.py`, `test_detect_hardware.py`, `test_bindings.py`.

- Se sustituyó el patrón `contenido` (variable que el auditor marcaba como SNIFF al leer artefactos) por `fuente`, ya que estos tests leen **archivos fuente/header de interfaz** (`.h`, `.syn`, `.toml`), que son contratos de API legítimos, no artefactos generados.
- Se añadió el helper `_declara(fuente, simbolo)` que verifica que el símbolo está **declarado como función** (`simbolo(`, `func simbolo`, `externo funcion simbolo`), convirtiendo los checks de "aparece el texto" en **contratos de declaración de API** reales (Manual 7 §2.3).
- Los skips interinos de ME-4 se conservan como TDD skips con cita Manual 9 §12 (símbolo no implementado), sin content-sniff.

## Corrección de deuda de ME_Q2 (auditor)

Se detectó y corrigió un defecto en `auditoria/auditar_calidad_tests.py`: el split de funciones `test_` solo detectaba funciones a nivel de módulo, omitiendo métodos de clase (la inmensa mayoría). Esto subestimaba drásticamente el conteo de SNIFF (reportaba 48; tras el fix: **378 SNIFF / 54 SIN_CITA** reales). El fix cambia el split a `^\s*def\s+test_` para cubrir también métodos de clase. El self-test de ME_Q2 sigue pasando (3 passed).

## Control de regresión

Baseline de los 4 archivos = 3 passed / 15 skipped. Tras la conversión: **3 passed / 15 skipped** (0 regresión). El auditor ya no reporta SNIFF/SIN_CITA en ninguno de los 4.

## Estado: CUMPLE

Los 4 archivos del lote dejan de ser reportados como SNIFF por el auditor corregido. La deuda restante (otros directorios, 378 SNIFF reales) se cierra en ME_S3..S6 / ME_T1..T4 / ME_X1.
