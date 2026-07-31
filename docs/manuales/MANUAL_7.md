MANUAL 7: HERRAMIENTAS DE DESARROLLO (LSP Y VS CODE)
Archivo: 07_LSP_Y_HERRAMIENTAS.md
Versión: 5.1.1-industrial
Propósito: Especificar el servidor LSP nativo, la extensión VS Code, la integración con IA local (llama.cpp) y el pipeline RAG.

7.1 Arquitectura del Servidor LSP Nativo
El LSP es un binario hermano (synapse_lsp.exe o test_lsp_bin.exe) que se comunica vía stdin/stdout usando JSON-RPC 2.0 con cabeceras Content-Length.

text
Editor (VS Code)
  │  STDIN: Content-Length: 57\r\n\r\n{"jsonrpc":"2.0","method":"initialize",...}
  ▼
synapse_lsp.exe
  ├── Bucle principal (lector de cabeceras + cuerpos)
  ├── Enrutador de métodos (initialize, didOpen, didChange, ...)
  ├── Compilador en memoria (Lexer → Parser → Semántico)
  ├── Mapeador de errores → Diagnostics LSP
  └── STDOUT: Content-Length: ...\r\n\r\n{"jsonrpc":"2.0","result":...}
Regla de oro: El LSP nunca llama a exit() en caso de error de sintaxis. Captura, formatea y envía diagnostics.

7.2 Protocolo de Cabecera (Lectura estricta)
c
// Pseudocódigo C
int leer_cabecera() {
    char buffer[4096];
    int content_length = -1;
    while (1) {
        char* line = fgets(buffer, sizeof(buffer), stdin);
        if (strncmp(line, "Content-Length:", 15) == 0) {
            content_length = atoi(line + 15);
        }
        if (strcmp(line, "\r\n") == 0) break; // Fin de cabeceras
    }
    return content_length;
}
// Luego leer exactamente content_length bytes del body.
7.3 Métodos LSP Soportados (Capacidades)
Método	ID	Descripción
initialize	✅	Negocia capacidades (textDocumentSync = 1, full).
initialized	✅	Confirmación.
textDocument/didOpen	✅	Envía diagnostics al abrir.
textDocument/didChange	✅	Re-analiza y envía diagnostics en cada cambio (full text).
textDocument/didSave	✅	Re-analiza al guardar (opcional).
textDocument/didClose	✅	Limpia diagnostics del documento.
shutdown	✅	Apagado ordenado.
exit	✅	Termina proceso.
synapse/aiStatus	✅	Extensión: estado de IA local.
synapse/aiExplain	✅	Extensión: explicación con RAG.
synapse/aiComplete	✅	Extensión: generación de código.
7.4 Mapeo de Coordenadas y Diagnostics
Conversión (Synapse → LSP):

Sistema	Líneas	Columnas
Synapse (interno)	1-based	0-based
LSP (protocolo)	0-based	0-based
text
lsp_line = synapse_line - 1
lsp_character = synapse_columna   // sin cambio
Formato del Diagnostic:

json
{
  "range": {
    "start": { "line": 4, "character": 10 },
    "end": { "line": 4, "character": 11 }
  },
  "severity": 1,
  "code": "ERR_SEM_VAR_NO_DECLARADA",
  "source": "synapse",
  "message": "Variable 'x' no declarada en este ámbito."
}
Mapeo de severidad: Todos los errores de compilación son severity: 1 (Error). Los warnings no se emiten aún (futuro).

7.5 Extensión VS Code (Cliente)
Auto-detección del binario (orden):

./test_lsp_bin.exe (raíz del proyecto)

./nucleo/lsp_test.exe

./build/bin/synapse_lsp.exe

Configuración del usuario: "synapse.lsp.nativeBinary": "ruta"

Activación: Se activa al abrir archivos con extensión .syn.

Comandos registrados en la paleta:

Synapse: Verificar estado de IA local → llama a synapse/aiStatus

Synapse: Explicar código con IA local → llama a synapse/aiExplain

Synapse: Generar código con IA local → llama a synapse/aiComplete

7.6 IA Local Nativa (llama.cpp) — Pipeline RAG
Arquitectura desacoplada:

text
VS Code → LSP (synapse_lsp) → llama-server.exe (localhost:8088)
                                    ├── /props (n_ctx, model_name)
                                    ├── /completion (generación)
                                    ├── /slot_save (guardar contexto)
                                    └── /slot_restore (cargar contexto)
Pipeline RAG quirúrgico:

Extracción: Tomar 5 líneas antes y 5 después del cursor (total 11 líneas).

Contexto: AST del nodo actual, diagnósticos activos.

Presupuesto: Leer n_ctx del modelo. Calcular max_tokens = clamp(n_ctx * 0.3, 64, 2048).

Prompt: Construir con contexto + instrucción.

Inferencia: POST /completion con temperature=0.7, stop=["\n\n\n", "```"].

Shutdown Hooks (garantizados):

Plataforma	Mecanismo
Windows	SetConsoleCtrlHandler + TerminateProcess + EmptyWorkingSet.
POSIX	signal(SIGINT/SIGTERM) + SIGKILL + waitpid + malloc_trim(0).
Resultado validado: 7/7 tests nativos (sin leaks, sin procesos huérfanos).