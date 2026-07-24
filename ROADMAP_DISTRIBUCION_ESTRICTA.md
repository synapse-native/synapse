# ROADMAP DE DISTRIBUCIÓN Y DESPLIEGUE COGNITIVO (v2.0)
**Estado Actual:** Fases 1 y 2 completadas y validadas en entorno estéril (E2E). Ejecutando Fase 3 (Subprocesos en C — integración nativa llama.cpp) y rediseñando Fase 4 (Inno Setup Modular).

---

## FASE 1: AISLAMIENTO DEL COMPILADOR Y REPARACIÓN DEL CLI (COMPLETADA)
**Objetivo:** Garantizar que `synapse.exe` no dependa del entorno del usuario ni filtre comandos al backend.
*   ✅ **1.1 Refactorización de `cli.py`:** Parser estricto con `argparse`, intercepción de `--help`, `--version` y comandos del sistema antes de invocar el linker.
*   ✅ **1.2 Aprovisionamiento de Toolchain C:** `install.ps1` descarga e instala MinGW-w64 portable (WinLibs) en `C:\Synapse\toolchain\bin\gcc.exe` sin intervención del usuario.
*   ✅ **1.3 Rutas Internas:** Motor de compilación enrutado de forma relativa (`[RAIZ_SYNAPSE]/toolchain/bin/gcc.exe`) y aislado del PATH global de Windows. `cli.py` y `install.ps1` validan existencia del toolchain antes de compilar.

---

## FASE 2: DESPLIEGUE DEL ENTORNO DE DESARROLLO (VS CODE VSIX) (COMPLETADA)
**Objetivo:** Instalación "Plug & Play" sin intervención humana en terminales.
*   ✅ **2.1 Lógica de Auto-Instalación en `extension.js`:** `_asegurar_binario_lsp()` y `_instalar_synapse_automatico()` auditan si `synapse.exe` está presente; si no, descargan instalador desde GitHub Releases, extraen en `C:\Synapse` y ejecutan post-instalación (MinGW) vía PowerShell embebido.
*   ✅ **2.2 Empaquetado VSIX:** Proyecto `vscode-synapse/` configurado con `package.json` completo (v2.2.2, soporte estricto `.syn`, bypass Workspace Trust). Listo para `vsce package` → `synapse-vscode-v2.2.2.vsix`.
*   ✅ **2.3 Integración de Comandos LSP:** Endpoints `synapse/aiExplain`, `synapse/aiComplete`, `synapse/aiStatus` cableados en `extension.js` → `synapse_lsp/server.py` → binario nativo `synapse.exe --lsp`. Parche de nomenclatura (`synapse.exe`) y ejecución del post-instalador de MinGW. Cero dependencia de Python en runtime del usuario.

---

## FASE 3: CAPA COGNITIVA AUTÓNOMA (EN PROGRESO)
**Objetivo:** Implementar inteligencia artificial local y privada orquestada nativamente por el compilador, **eliminando dependencias de terceros (como Ollama)** — integración directa con `llama.cpp`/`llama-server.exe`.
*   🔄 **3.1 Orquestador de Subprocesos LSP (C):** Implementar ciclo de vida en `nucleo/ai_orchestrator.c` para encender/apagar `llama-server.exe` dinámicamente, controlando puertos y **liberación de memoria al cerrar el editor**.
*   🔄 **3.2 Integración Cliente HTTP Nativo:** Adaptar el LSP para emitir peticiones en **formato nativo de llama.cpp** (`n_predict`, `prompt`, parámetros de sampling) — sin capa intermedia Ollama.
*   🔄 **3.3 Pipeline RAG Quirúrgico y Adaptativo:**
    *   **Inyección de contexto en micro-dosis (RAG Liviano):** Nodo AST, línea actual y diagnósticos del compilador.
    *   **Negociación dinámica:** Basada en la ventana de contexto del modelo cargado (`n_ctx`) para evitar desbordamientos, compatible desde modelos 1.2B hasta 8B.
*   ✅ **3.4 Base de código existente:** `nucleo/ai_orchestrator.c/h` + `nucleo/ollama_client.c/h` implementan `_syn_modelo_cargar`, `_syn_modelo_inferir`, gestión de hilos y memoria. **Pendiente:** migrar de API Ollama a API nativa llama.cpp.

---

## FASE 4: INSTALADOR MAESTRO Y SELECTOR MODULAR (DISEÑO APROBADO)
**Objetivo:** Un único ejecutable (`setup.exe` vía Inno Setup) que controle la experiencia de instalación sin requerir descargas de fondo en VS Code.
*   🔄 **4.1 Script Bootstrap Inno Setup:** `instalador_synapse.iss` — Construir instalador con interfaz gráfica profesional y lógica Pascal embebida (páginas personalizadas, descarga con progreso, validación VRAM).
*   🔄 **4.2 Embudos de Decisión del Usuario:**
    *   **Opción A (Synapse Core):** Instala solo compilador, MinGW y VSIX (~50 MB).
    *   **Opción B (OpenSyn Completo):** Activa el entorno de IA local autónoma.
*   🔄 **4.3 Gestión Inteligente de Modelos (Si elige OpenSyn):**
    *   **Rama 1:** Auditoría de hardware (API de Windows para RAM/VRAM via WMI `Win32_VideoController`) y descarga automática del binario `llama-server.exe` + `.gguf` recomendado (1.5B si VRAM < 4GB, 8B si ≥ 8GB).
    *   **Rama 2:** **Selector de ruta local** para vincular un modelo `.gguf` preexistente en el disco del usuario (Fricción cero).
    *   **Integridad:** `axon.lock` (SHA-256) + firma Ed25519 obligatoria (TweetNaCl) en `axon fetch` antes de extraer TAR.

---

## ✅ VALIDACIÓN E2E CONFIRMADA — Fases 1 y 2 (Jul 2026)

| Componente | Estado | Evidencia |
|------------|--------|-----------|
| `cli.py` argparse estricto | ✅ | `cli.py:11-124` |
| MinGW-w64 portable en `C:\Synapse\toolchain` | ✅ | `install.ps1:48-85` |
| GCC invocado por ruta interna | ✅ | `main.py:605,607` (`-Wl,--stack,8388608` + path toolchain) |
| VS Code auto-instala Synapse | ✅ | `extension.js:50-189` (`_asegurar_binario_lsp`, `_instalar_synapse_automatico`) |
| VSIX empaquetable v2.2.2 (`vsce package`) | ✅ | `vscode-synapse/package.json` completo |
| Comandos IA LSP (`aiStatus`, `aiExplain`, `aiComplete`) | ✅ | `extension.js:264-382` + `synapse_lsp/server.py` |
| `install.ps1` silencioso + PATH usuario | ✅ | `install.ps1:19-103` |
| `instalador_synapse.iss` Inno Setup GUI (diseño) | ✅ | `instalador_synapse.iss:1-327` (componentes, VRAM, WMI, SHA-256, Ed25519) |
| Selector Core vs OpenSyn (diseño) | ✅ | `instalador_synapse.iss:[Components]` + `core_only_desc`, `opensyn_full_desc` |

---

## 📦 ARTEFACTOS DE DISTRIBUCIÓN — Estado Actual

| Artefacto | Ubicación | Estado |
|-----------|-----------|--------|
| `synapse-v2.2.0-windows-x64.zip` | Raíz / Releases | ✅ Binarios core generados |
| `synapse-vscode-v2.2.2.vsix` | `vscode-synapse/` | ✅ Listo para empaquetar |
| `Synapse-2.2.2-Setup.exe` | `dist/` (output Inno) | 🔄 Pendiente compilación `iscc` |
| `install.ps1` | Raíz | ✅ Funcional |

---

## 🎯 PRÓXIMOS PASOS INMEDIATOS
1. **Fase 3.1–3.3:** Migrar `ai_orchestrator.c` + `ollama_client.c` a API nativa `llama.cpp` (eliminar dependencia Ollama).
2. **Fase 3.3:** Implementar RAG liviano con negociación dinámica `n_ctx` en `synapse_lsp/server.py`.
3. **Fase 4.1:** Compilar `iscc instalador_synapse.iss` → `Synapse-2.2.2-Setup.exe` en `dist/`.
4. **Fase 4.3:** Implementar Rama 2 (selector ruta local `.gguf`) en Pascal script del `.iss`.

---

*Roadmap vivo — actualizado tras auditoría cruzada con roadmap v2.0. Fases 1–2: **COMPLETADAS Y VALIDADAS**. Fases 3–4: **EN EJECUCIÓN / DISEÑO APROBADO**.*