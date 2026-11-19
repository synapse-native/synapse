ME r276_hardware_detector: OpenSyn detección de hardware y gestión de modelos

TAREA: Implementar detección automática de hardware y gestión de modelos codec para OpenSyn
FASE: 29 — OpenSyn
MANUAL REFERENCIADO: Manual 9 §5.3; Manual 9 §6.1
HASH COMMIT: Por crear
COMPILACIÓN: plan + oracle sin build completo; artefactos existentes reutilizados
TESTS: oracle --construir/--sellar/--estricto/--mutar/--e2e RC=0; contrastar 3/3 PASS
COBERTURA: 0 brechas alineacion; 0 brechas verificar_alineacion
MODIFICACIONES DE TESTS: ningunas (uso de artifacts existentes)
MODULARIZACIÓN: plan nuevo + oracle nuevo
RIESGOS IDENTIFICADOS: oracle --mutar debe resistir mutaciones menores de source
PRÓXIMO PASO: contrastar --plan y verificar_alineacion.py 0 brechas

--- BLOQUES REQUERIDOS ---

requisito: ME r276 debe implementar detección de hardware y gestión de modelos para OpenSyn siguiendo el roadmap Fase 29
texto: OpenSyn necesita detectar CPU, memoria, VRAM y arquitectura del sistema para seleccionar el modelo GGUF más adecuado; debe reutilizar modelos existentes en ~/.opensyn/models/ y ofrecer al usuario opciones ante descargas fallidas
implementacion: Agregar std/os.syn con funciones memoria_total, vram_total, cpu_nucleos, arquitectura; crear opensyn/installer.syn con lógica de selección y descarga de modelo; integrar caché SHA-256 por ruta+flags+versión; implementar verificación de integridad y configuración automática de llama-server
oraculo: oracle_r276_hardware_detector.py con --construir --sellar --estricto --mutar --e2e; contrastar --plan docs/plan_ME_r276_hardware_detector.md 3/3 PASS; verificar_alineacion.py 0 brechas; S2==S3 determinismo con artifacts existentes