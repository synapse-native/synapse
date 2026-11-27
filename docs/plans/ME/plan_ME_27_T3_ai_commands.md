# ME_27_T3 — LSP AI Command Dispatch (Manual 8 §2.3)

## Meta
Implementar dispatch en el LSP para comandos IA: synapse/aiStatus, synapse/aiTranspile, synapse/aiBindings.

## Requisitos

### R1: synapse/aiStatus
requisito: Manual 8 §2.3
texto: "Synapse: Verificar estado de IA local → synapse/aiStatus"
implementacion: Handler que retorna JSON con modelo cargado (null si no hay), memoria, estado.
oraculo: tests/integration/test_lsp_ai_dispatch.py

### R2: synapse/aiTranspile
requisito: Manual 8 §2.3
texto: "Synapse: Transpilar Python a Syquex → synapse/aiTranspile"
implementacion: Handler que llama a opensyn/transpiler.py y retorna el código Syquex generado.
oraculo: tests/integration/test_lsp_ai_dispatch.py

### R3: synapse/aiBindings
requisito: Manual 8 §2.3
texto: "Synapse: Generar bindings C → Syquex → synapse/aiBindings"
implementacion: Handler que llama a opensyn/bindings_generator.py y retorna los bindings.
oraculo: tests/integration/test_lsp_ai_dispatch.py

## Archivos a modificar
- `nucleo/lsp_v3.syn` (agregar handlers + dispatch)

## Estado: PENDIENTE
