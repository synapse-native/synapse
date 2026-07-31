MANUAL 7: HERRAMIENTAS DE DESARROLLO (LSP Y VS CODE)

Archivo: 07\_LSP\_Y\_HERRAMIENTAS.md

Versión: 5.1.1-industrial

Propósito: Especificar el servidor LSP nativo, la extensión VS Code, la integración con IA local (llama.cpp) y el pipeline RAG.



7.1 Arquitectura del Servidor LSP Nativo

El LSP es un binario hermano (synapse\_lsp.exe) que se comunica vía stdin/stdout usando JSON-RPC 2.0 con cabeceras Content-Length.



text

Editor (VS Code)  →  STDIN  →  synapse\_lsp.exe  →  STDOUT  →  Editor

Regla de oro: El LSP nunca llama a exit() en caso de error de sintaxis. Captura, formatea y envía diagnostics.



7.2 Protocolo de Cabecera (Lectura estricta)

c

int leer\_cabecera() {

&#x20;   char buffer\[4096];

&#x20;   int content\_length = -1;

&#x20;   while (fgets(buffer, sizeof(buffer), stdin)) {

&#x20;       if (strncmp(buffer, "Content-Length:", 15) == 0)

&#x20;           content\_length = atoi(buffer + 15);

&#x20;       if (strcmp(buffer, "\\r\\n") == 0 || strcmp(buffer, "\\n") == 0) break;

&#x20;   }

&#x20;   return content\_length;

}

7.3 Métodos LSP Soportados

Método	ID	Descripción

initialize	✅	Negocia capacidades.

initialized	✅	Confirmación.

textDocument/didOpen	✅	Envía diagnostics al abrir.

textDocument/didChange	✅	Re-analiza en cada cambio (full).

textDocument/didClose	✅	Limpia diagnostics.

synapse/aiStatus	✅	Extensión: estado de IA local.

synapse/aiExplain	✅	Extensión: explicación con RAG.

synapse/aiComplete	✅	Extensión: generación de código.

7.4 Mapeo de Coordenadas y Diagnostics

Synapse (interno): Líneas 1-based, columnas 0-based.



LSP (protocolo): Líneas 0-based, columnas 0-based.



text

lsp\_line = synapse\_line - 1

lsp\_character = synapse\_columna

Formato del Diagnostic:



json

{

&#x20; "range": { "start": { "line": 4, "character": 10 }, "end": { "line": 4, "character": 11 } },

&#x20; "severity": 1,

&#x20; "code": "ERR\_SEM\_VAR\_NO\_DECLARADA",

&#x20; "source": "synapse",

&#x20; "message": "Variable 'x' no declarada en este ámbito."

}

7.5 Extensión VS Code (Cliente)

Auto-detección del binario: ./test\_lsp\_bin.exe → ./nucleo/lsp\_test.exe → ./build/bin/synapse\_lsp.exe.

Comandos en la paleta:



Synapse: Verificar estado de IA local → synapse/aiStatus



Synapse: Explicar código con IA local → synapse/aiExplain



Synapse: Generar código con IA local → synapse/aiComplete



7.6 IA Local Nativa (llama.cpp) — Pipeline RAG

Arquitectura desacoplada:



text

VS Code → LSP (synapse\_lsp) → llama-server.exe (localhost:8088)

&#x20;                                  ├── /props

&#x20;                                  ├── /completion

&#x20;                                  ├── /slot\_save

&#x20;                                  └── /slot\_restore

Pipeline RAG quirúrgico:



Extracción: 5 líneas antes y 5 después del cursor (total 11 líneas).



Contexto: AST del nodo actual, diagnósticos activos.



Presupuesto: Leer n\_ctx. Calcular max\_tokens = clamp(n\_ctx \* 0.3, 64, 2048).



Prompt: Contexto + instrucción.



Inferencia: POST /completion con temperature=0.7.

Shutdown Hooks: SetConsoleCtrlHandler (Windows) / signal(SIGINT/SIGTERM) (POSIX) + SIGKILL + waitpid.



7.7 Tests Obligatorios para esta Etapa

Test	Comando	Criterio

LSP inicialización	pytest tests/integration/test\_lsp\_native.py -v	5/5 PASS

Diagnostics en didOpen	pytest tests/integration/test\_lsp\_diagnostics.py -v	Errores mapeados correctamente

RAG / IA local	pytest tests/integration/test\_rag\_pipeline.py -v	Contexto extraído correctamente

Shutdown hooks	gcc -o test\_shutdown opensyn/orchestrator.c \&\& ./test\_shutdown	0 procesos huérfanos

