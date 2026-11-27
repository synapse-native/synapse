# Verificación ME:control_alineacion

Protocolo MTS: cada requisito del plan, marcado CUMPLE / NO CUMPLE con
`archivo:linea` y el comando que lo prueba.

| Requisito | Estado | Evidencia | Prueba |
|---|---|---|---|
| Manual 2 §12 — oráculos ejecutados (100% pass, sin SKIP) | CUMPLE | `auditoria/alineacion.py:326` (`ejecutar_oraculo`), `:355-357` (rechaza no-tests/SKIP) | `pytest tests/test_alineacion_control.py -k oraculo` |
| Manual 8 §1.2 — fail-loud, sin degradación silenciosa | CUMPLE | `auditoria/alineacion.py:406` (sin expediente = brecha), `auditoria/indice_manual.py:234` (cita no literal = brecha) | `pytest tests/test_alineacion_control.py -k bloquea` |
| Manual 7 §4.2 — comparación contra el manual vigente | CUMPLE | `auditoria/alineacion.py:373` (`verificar`), `docs/manuales/.indice.json` (sha256 por manual) | `pytest tests/test_alineacion_control.py -k cita` |

## Comandos ejecutados

```
.venv\Scripts\python.exe -m pytest tests/test_alineacion_control.py tests/test_auditoria_lectura.py tests/test_auditoria_contrastar.py tests/test_citas_formato.py tests/test_obt_citas_manuales.py -q
    → 40 passed (24 nuevos; los gates previos sin regresión)

.venv\Scripts\python.exe auditoria/indice_manual.py --generar
    → 9 manuales, 296 secciones, 2452 oraciones citables

.venv\Scripts\python.exe auditoria/alineacion.py --baseline
    → citas muertas=71, archivos sin mapa=0

.venv\Scripts\python.exe auditoria/alineacion.py --verificar --desde cdc1a58 --ci --sin-oraculos --modo warn
    → brecha: falta el expediente/evidencia del commit ME-7 2f62084 (cambio_hash=1a4b130148cb7d5e)

.venv\Scripts\python.exe auditoria/alineacion.py --verificar --me ME-7 --archivos <7 opensyn/*.syn> --sin-oraculos
    → 53 citas `cumple Manual` a secciones que ya no existen, en 6 archivos

.venv\Scripts\python.exe auditoria/contrastar.py --plan docs/plan_ME_control_alineacion.md
    → 3 requisitos con oráculo válido, 0 brechas, verificación CUMPLE OK

bash -n scripts/githooks/pre-commit   → sintaxis OK
```

## Pendiente (no de este ME)

- Completar `docs/alineacion/ME-7.md` y resolver la desincronización
  `MANUAL 7.md` ↔ citas del código (§5–§9 desaparecidas): 53 citas en los
  archivos del ME-7 (9 `permisos.syn`, 8 `planificador.syn`, 12 `principal.syn`,
  6 `router.syn`, 11 `run_manager.syn`, 7 `validation_loop.syn`).
- Commitear `docs/manuales/.indice.json` (el CI valida las citas contra él) y
  regenerarlo con `--indice` cada vez que un manual cambie.
- Activar `ALINEACION_MODO=block` cuando el árbol quede en 0 brechas.
- Fila en `docs/AUDITORIA_ALINEACION_MANUALES.md` + reporte `docs/reportes/R*.md`
  DESPUÉS del commit, con el hash real.
