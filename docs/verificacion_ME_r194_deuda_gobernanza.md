# Verificación ME — r194_deuda_gobernanza (cierre MTS gate, auditoria/contrastar.py paso 4)
# Expediente: docs/alineacion/r194_deuda_gobernanza.md (0 brechas, sello 060024ceeb5779fb)
# Gates ejecutados 2026-10-22: contrastar rc=0 · verificar_alineacion 0 brechas · lectura previa 7/7 cubiertas

Manual 7 §7.3 — R1 CUMPLE (oráculo tests/auditoria/test_oraculos_r194_sandbox.py pytest release PASS: kiosko de permisos mínimo del servidor de inferencia OpenSyn, probes .syn validados contra el runtime sandbox M7 §2.3)

Manual 9 §5.3 — R2 CUMPLE (H-R144-3 RESUELTA/VERIFICADA (verificación de descarga y SHA-256 de modelos §5.6): opensyn/modelos.toml con 5 SHA256 reales == X-Linked-ETag LFS de HuggingFace capturado 5/5 por HTTP HEAD el 2026-10-22; transcript comiteado auditoria/evidencia/r194_catalogo_etag.txt; oráculo auditoria/evidencia/r194_catalogo_verificar.py rc=0 — catálogo real, sin placeholder)

Manual 32 §3 §5 §6 — R3 CUMPLE (0 SIN_CITA: los 3 heads OBL-M32-04..06 en tests/opensyn/test_memoria_cifrada.py, test_pipeline_multiagente.py y test_verificacion_aot.py citan secciones reales del Manual 32; oráculo auditoria/evidencia/r194_gates.py rc=0)

Manual 6 §1 — R4 CUMPLE (H-CONTROL-3 saneado: check_mto con 0 AVISO de citas fantasma y 0 GREEN sin test; oráculo --solo-mto rc=0 "52 entradas OBL validadas")

Manual 3 §3 — R4 CUMPLE (H-CONTROL-3 saneado alineado a Manual 3 §3: check_mto con 0 AVISO
 de citas fantasma y 0 GREEN sin test; oráculo --solo-mto rc=0 "52 entradas OBL validadas")

Manual 30 — R5 CUMPLE (cierre documental "CERRADO (R183e)" presente en el docstring de tests/integration/test_ai_explain.py; concordancia del ROADMAP/memoria verificada en la misma ME)

Manual 1 §2 — R6 CUMPLE (D-R194-1 ratificada por el Arquitecto: suites-guarda estructurales en lista blanca cerrada FAMILIA_ESTRUCTURAL_RATIFICADA; puerta --estricto-sniff activa rc=0 y el RESUMEN reporta el conteo de exentos de forma explícita — sin ocultar deudas)
