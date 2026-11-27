# plan_ME_S1 — Conversión sniff→oráculo: tests/ raíz

MTS (docs/METODO_TRABAJO.md). Oráculo ejecutable; el código lleva cita grep-chequeable.

## Requisito
requisito: Manual 7 §2.3
texto: "El test compila/ejecuta el artefacto generado y valida comportamiento, no la presencia de palabras clave."
implementacion: Convertir test_contexto_estatico.py, test_bindings_hook.py, test_check_mode.py, test_bucle_validacion.py: reemplazar assert "X" in c/syq por compilación/ejecución real del artefacto y assert de comportamiento del manual.
oraculo: tests/test_contexto_estatico.py

## Alcance (sin desviación)
Convierte ÚNICAMENTE los archivos del lote indicado; no toca otros directorios.

## Criterio de aceptación
- Sin assert substring sin compilar/ejecutar.
- El archivo oraculo pasa sin skip de deuda ME-4.
