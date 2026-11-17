# Plan ME r234 - Certificación E2E y Smoke Test de Usuario Final (Fases 30 y 32.8)

## Contexto

El ecosistema Synapse + Syquex + OpenSyn cuenta con compilador autoalojado, frontend Syquex, herramientas nativas (Fase 31), agente autónomo con grafo AST y memoria cifrada (Fase 32), instalador para Windows (Inno Setup) y extensión para VS Code (`vscode-synapse`).

Para declarar el sistema 100% operativo y listo para usuario final, se requiere un arnés de certificación automatizado post-instalación que verifique en una máquina limpia (sin Python ni GCC preconfigurados en el sistema):
1. La instalación desatendida del paquete unificado.
2. La compilación y ejecución de programas de prueba en Synapse (`.syn`) y Syquex (`.syq`).
3. La carga del `.vsix` en VS Code con respuesta correcta del LSP nativo (`synapse_lsp`).
4. El arranque de OpenSyn en modo TUI / CLI interactivo con el modelo GGUF instruct local validado.

## Requisitos (MTS)

requisito: Manual 9 §7
texto: "| Instalación en Windows (limpiamente) | Ejecutar instalador en máquina virtual Windows limpia | Instalación exitosa, PATH configurado, `synapse --version` funciona. |"
implementacion: script de verificación post-instalación `tests/e2e/test_smoke_usuario_final.py` que ejecuta la suite de humo sobre los binarios generados en `dist/bin` y el paquete de instalación, comprobando que `synapse build`, `synapse run` y `synapse check` operan de forma autónoma sin depender de Python en el PATH.
oraculo: tests/e2e/test_smoke_usuario_final.py

requisito: Manual 7 §7.3
texto: "Cero telemetría: Verificado con monitoreo de red (sin conexiones salientes). / Sandboxing: El servidor de inferencia se ejecuta con permisos mínimos."
implementacion: la prueba de humo ejecuta `synapse opensyn status` y un comando de consulta local contra `llama-server`, verificando que la inferencia ocurre 100% en local sin conexiones externas y reportando el estado final en `docs/reportes/FASE_32_CERTIFICACION.md`.
oraculo: tests/e2e/test_smoke_usuario_final.py

## Archivos

- `tests/e2e/test_smoke_usuario_final.py` - arnés automatizado de prueba de humo post-instalación (Synapse, Syquex, OpenSyn, LSP).
- `instaladores/test_instalador_silencioso.py` - prueba de instalación limpia desatendida.
- `docs/alineacion/r234_certificacion_usuario_final.md` - expediente de trazabilidad MTS.
- `docs/reportes/FASE_32_CERTIFICACION.md` - reporte formal de certificación final del ecosistema.
