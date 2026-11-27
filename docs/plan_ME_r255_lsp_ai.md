# Plan ME r255_lsp_ai (reasignado de r219_lsp_ai)

requisito: Manual 8 §2.3
texto: "Synapse: Verificar estado de IA local → synapse/aiStatus"
implementacion: nucleo/lsp_v3.syn handle_ai_status ahora consulta _syn_ollama_modelos("127.0.0.1", 8088) y devuelve loaded/model/status reflejando el servidor real; handle_ai_explain/Complete/Fix/Transpile/Bindings ya existentes; dispatch ya enruta los seis comandos. tests/integration/test_ai_commands_opensyn.py deja de tener los 5 skips TDD (5/5).
oraculo: tests/integration/test_ai_commands_opensyn.py

requisito: Manual 8 §1.1
texto: "El LSP es nativo, sin telemetría y sin dependencias externas."
implementacion: handle_ai_status no agrega telemetria; solo consulta el backend local.
oraculo: tests/integration/test_lsp_ai_dispatch.py
