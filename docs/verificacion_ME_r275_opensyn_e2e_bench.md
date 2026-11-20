# Verificación ME r275 — E2E real y benchmark local de OpenSyn

**Fecha:** 2026-11-20
**Plan:** `docs/plan_ME_r275_opensyn_e2e_bench.md`
**Cita textual (Manual 7 §7.3):** “Cero telemetría: Verificado con monitoreo de
red (sin conexiones salientes).”
**Cita textual (Manual 9 §5.5):** “El instalador ejecuta una consulta simple al
modelo para verificar que todo funciona.”

## 1. Manual 7 §7.2 CUMPLE (con límite declarado) — benchmark medido

- `tests/integration/test_opensyn_e2e_local.py::test_chat_real_y_metricas`
  levanta `llama-server` real y mide latencia, tokens/s y VRAM.
- Medición 2026-11-20: latencia **4.029 s**, 32 tokens, **12.13 tokens/s**,
  modelo `deepseek-coder-1.3b-Q4_K_M.gguf`, CPU (VRAM N/A).
- El umbral `< 1 s` de Manual 7 §7.2 es para 7B en GPU; no se aplica a esta
  máquina CPU/1.3B. Se mide y reporta sin falsificar el resultado.

## 2. Manual 7 §7.3 CUMPLE — privacidad, sandbox y red

- `tests/integration/test_opensyn_sin_red.py` (2/2 PASS): todo endpoint HTTP
  literal de `opensyn/` es loopback o descarga documentada del instalador;
  cero telemetría/analytics sin descargo.
- `test_tool_con_aprobacion_y_sandbox`: sonda compilada y ejecutada contra
  `opensyn/permisos.syn` → editar dentro = ASK(1), editar fuera = DENY(2),
  leer dentro = ALLOW(0).
- `test_doctor_sin_conexiones_salientes`: monitorea `netstat` del PID de
  `opensyn.exe doctor` y exige sólo loopback.
- Límite declarado: la sonda se compila con S1 porque S2 no emite
  `permisos.syn` (hallazgo H-R275-1, ver R275).

## 3. Manual 7 §8 CUMPLE — validación con `synapse check --no-emit`

- `test_validacion_check_no_emit` ejecuta el binario nativo real:
  código válido rc=0; código inválido rc≠0.
- El E2E del agente usa la misma validación que el flujo del manual antes de
  mostrar código generado.

## 4. Manual 9 §5.5 CUMPLE — prueba de humo

- La consulta simple “Di 'Hola' en español.” se ejecuta contra el
  `llama-server` real y se exige respuesta no vacía
  (`test_chat_real_y_metricas`).
- La misma prueba produce la latencia registrada en el reporte R275.

## Evidencia

- `auditoria/oraculos/oraculo_r275_opensyn_e2e_bench.py` → rc=0 con `[OK]`
  (estático siempre + E2E real cuando detecta `llama-server` y GGUF; rc=1 con
  causa si no los hay, sin verde falso).
- `contrastar --plan docs/plan_ME_r275_opensyn_e2e_bench.md` → PASS.
- `verificar_alineacion.py` → 0 brechas.
