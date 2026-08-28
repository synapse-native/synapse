# plan_ME_S2 — Conversión sniff→oráculo: tests/opensyn/ restantes

MTS (docs/METODO_TRABAJO.md). Oráculo ejecutable; el código lleva cita grep-chequeable.

## Requisito
requisito: Manual 7 §2.3 / Manual 7 §7 / Regla Transversal plan_AUDITORIA_TESTS.md
texto: "Oráculos reales sobre la API ya implementada, no content-sniff. Calidad total: especificación COMPLETA del comportamiento."
implementacion: Convertir test_inference.py, test_download.py, test_detect_hardware.py, test_bindings.py: reemplazar skips/interinas y substring por asserts de contrato contra la API real. Las features aún no implementadas (llama_client.h/.c, orchestrator.h, installer.syn, modelos.toml, std/os.syn, bindings TS) FALLAN en ROJO TDD (pytest.fail) apuntando a su ME de feature (ME_29_T1/T2/T3) — NUNCA pytest.skip. Marca @pytest.mark.tdd.
oraculo: tests/opensyn/test_inference.py

## Alcance (sin desviación)
Convierte ÚNICAMENTE los archivos del lote indicado; no toca otros directorios.

## Criterio de aceptación
- Sin assert substring sin compilar/ejecutar.
- Cero pytest.skip ocultando deuda: toda feature faltante es ROJO TDD con ME de feature.
- Tests completos (oráculos de contrato) listos para pasar en VERDE al implementar la feature.
