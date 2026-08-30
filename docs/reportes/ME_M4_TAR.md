# REPORTE ME_M4_TAR - ME: M4_TAR (rechazo de typeflags peligrosos)

--- REPORTE DE MICRO-ENTREGABLE ---
TAREA: En `_syn_tar_extraer` rechazar typeflags que permitan path traversal o escritura fuera del destino (GNU long name/link y hard/symlinks: 'L','K','1','2') antes del chequeo de ruta, sin relajar el chequeo de path traversal existente.
FASE: 27 / Fase 2 nativa (feature/fase2-nativa-hm) - ME M4_TAR
MANUAL REFERENCIADO: Manual 6 §6.1 (Seguridad en deserialización/extracción TAR)
HASH COMMIT: d8d0ef9 (bundle WIP del otro agente: impl axon.c + oráculo test_path_traversal)
COMPILACION: N/A para el compilador S1 (runtime/core/axon.c es C del runtime). Oráculo en `tests/security/test_path_traversal.py`.
TESTS:
  - `pytest tests/security/test_path_traversal.py` -> 3/3 PASS (`test_path_traversal_bloqueado`, `test_rutas_normales_permitidas`, `test_malicious_tar_detectado`).
  - Oráculo C adicional: typeflags 'L'/'K'/'1'/'2' rechazados (build del binario de prueba en tests/security).
VERIFICADOR: `python auditoria/verificar_alineacion.py` -> 0 brechas. `python auditoria/contrastar.py --plan docs/plan_ME_M4_TAR.md` -> PASS.
MODIFICACIONES DE TESTS: ninguna debilitante; se verificó oráculo existente del otro agente.
PROXIMO PASO: ninguno para M4_TAR (completado).
--- FIN ---
