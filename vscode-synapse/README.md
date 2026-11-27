# Synapse Language — VS Code Extension

**Synapse** es un lenguaje de sistemas soberano con compilación nativa a C, concurrencia con fibras y canales, y asistente IA local 100% privado (CERO telemetría).

## Features

- **Syntax Highlighting** para `.syn` y `.syq` (TextMate)
- **Snippets** para funciones, estructuras, contratos `requiere`/`garantiza`
- **LSP Nativo** (`synapse_lsp.exe` / `synapse.exe --lsp`) — diagnósticos en tiempo real, hover, completion, go-to-definition, validación con `--check`
- **Run & Debug** — compila `main.syn` → `programa.c` → `programa.exe` vía `gcc`
- **IA Local (Opt-in)** — `synapse.aiStatus`, `aiExplain`, `aiComplete`, `aiTranspile`, `aiBindings` — requiere `modelo_synapse.gguf` y ≥8GB RAM (hardware-gated)
- **Zero Telemetry** — todo local, sin datos a servidores externos

## Requirements

- **Synapse Ecosystem** instalado via `Synapse-8.1.0-industrial-Windows-x64.exe` (Inno Setup) en `C:\Program Files\Synapse` o `C:\Synapse`
- `synapse.exe` y `synapse_lsp.exe` en `PATH` (`{app}\bin`)
- Opcional: VS Code ≥1.60

## Extension Settings

- `synapse.lsp.nativeBinary`: ruta manual a `synapse_lsp.exe`
- `synapse.lsp.enabled`: habilita/deshabilita LSP
- `synapse.ai.enabled`: habilita IA local (auto-deshabilitada si <8GB RAM)
- `synapse.trace.server`: traza JSON-RPC (`off`/`messages`/`verbose`)

## Known Issues

- Runtimes se activan al abrir un archivo `.syn` (`onLanguage:synapse`)
- Tras instalar Synapse, reinicia la terminal para actualizar `PATH` (`refreshenv` o reinicio VS Code)

## Release Notes

### 8.1.0
- LSP con hardware-gating, IA local, instalación multi-ruta (Program Files / C:\Synapse / PATH)
- Soporte bilingüe (ES/EN), firma Ed25519, SBOM SPDX
