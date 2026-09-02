# REPORTE ME_detect_hardware - ME: detect_hardware (M4.1 / Manual 9 §5.7)

--- REPORTE DE MICRO-ENTREGABLE ---
TAREA: Detectar RAM, VRAM, CPUs y sugerir config (tier/modelo/ctx/threads/ngl) para OpenSyn. Hallazgo A2: DXGI `DedicatedVideoMemory` es la fuente correcta de VRAM (WinSAT GraphicsScore y `GetDeviceCaps` no reportan VRAM real). El oráculo `tests/test_detect_hardware.c` (43 asserts) estaba HUÉRFANO (solo corría manualmente) -> cablearlo a la suite.
FASE: 27 / Fase 2 nativa (feature/fase2-nativa-hm) - ME detect_hardware (M4.1)
MANUAL REFERENCIADO: Manual 9 §5.7 (detección de hardware/GPU)
HASH COMMIT: d8d0ef9 (impl nucleo/detect_hardware.c + oráculo tests/test_detect_hardware.c) + commit de terminación (este ME: wiring en tests/integration/test_detect_hardware.py)
COMPILACION: build compila tests/test_detect_hardware.c junto con nucleo/detect_hardware.c con enlaces -lgdi32 -ldxgi -lole32 -luuid (rc=0). N/A para compilador S1.
TESTS:
  - `pytest tests/integration/test_detect_hardware.py` -> 1/1 PASS (binario imprime "43 passed" + "TODOS LOS TESTS DE HARDWARE PASARON", rc=0). Diferenciación 8/16/32/64 GB y serialización JSON verificadas.
  - Oráculo C `tests/test_detect_hardware.c`: 43 asserts PASS (corrida manual y vía wrapper).
VERIFICADOR: `python auditoria/verificar_alineacion.py` -> 0 brechas. `python auditoria/contrastar.py --plan docs/plan_ME_detect_hardware.md` -> oráculo válido (tests/test_detect_hardware.c); brechas de protocolo de reporte resueltas con este documento.
MODIFICACIONES DE TESTS: se añadió `tests/integration/test_detect_hardware.py` (wrapper) que NO modifica el oráculo del otro agente; sólo lo cablea a la suite de pytest.
PROXIMO PASO: ninguno para detect_hardware (completado). Falta pendiente del WIP del otro agente: ME test_fixes (0/24 conversiones a TDD RED; ver docs/plan_ME_test_fixes.md).
--- FIN ---
