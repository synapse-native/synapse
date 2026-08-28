# Verificación ME_S3 — Conversión sniff→oráculo: tests/integration/ lote 1

- **Plan:** `docs/plan_ME_S3.md`
- **Fase/Roadmap:** F27 (Workstream B — calidad de tests, Manual 8 §1.2 / §1.4)
- **Manual aplicable:** Manual 8 §1.2 (initialize/shutdown + capacidades) y Manual 8 §1.4 (Diagnostics / publishDiagnostics); CLI en Manual 8 §4.2.
- **Oráculo:** `tests/integration/test_diagnostics.py`

## Implementación

Archivos: `test_diagnostics.py`, `test_cli.py`, `test_lsp_native.py`.

- El auditor (corregido en ME_S2) NO reportó SNIFF en ninguno de los tres: ya son
  oráculos conductuales reales (compilan fixtures y verifican códigos de error;
  envían JSON-RPC al binario LSP y validan el protocolo; el CLI se ejecuta y se
  comprueba exit-code y ausencia de invocación al linker). No había sniff que convertir.
- Única deficiencia detectada: **SIN_CITA** (sin cita de Manual). Se añadió la
  cita correspondiente en el docstring de cada archivo (Manual 8 §1.4 / §1.2 / §4.2).

## Control de regresión

Baseline de los 3 archivos = 3 failed / 18 passed (fallos previos en
`test_lsp_native.py` por gaps de implementación del LSP, no por este ME). Tras la
conversión: **3 failed / 18 passed** (0 regresión introducida).

## Estado: CUMPLE

Los 3 archivos del lote dejan de ser reportados como SIN_CITA por el auditor. No
había SNIFF que convertir: eran ya tests conductuales. La deuda restante
(otros directorios) se cierra en ME_S4..S6 / ME_T1..T4 / ME_X1.
