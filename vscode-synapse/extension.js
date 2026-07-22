/**
 * Synapse Language Support for VS Code
 *
 * Extension principal que conecta VS Code con el servidor LSP nativo de Synapse
 * (test_lsp_bin.exe / synapse_lsp.exe) a través del protocolo estándar JSON-RPC.
 *
 * Arquitectura:
 * - Activa cuando se abre un archivo .syn
 * - Lanza `synapse_lsp.exe` como proceso hijo (sin dependencia Python)
 * - Conecta VS Code LanguageClient al proceso
 * - Expone comandos para IA local (Ollama, integrado via LSP)
 *
 * Requisitos:
 * - Synapse compiler en la raíz del proyecto
 * - Binario LSP nativo compilado: synapse_lsp.exe o test_lsp_bin.exe
 * - Opcional: Ollama para características IA (phi3:mini, llama3.2)
 */

const path = require('path');
const fs = require('fs');
const vscode = require('vscode');

// ---------------------------------------------------------------------------
// Lazy-load vscode-languageclient solo cuando se activa la extensión
// (evita errores MODULE_NOT_FOUND si no está instalado como dependencia)
// ---------------------------------------------------------------------------

let LanguageClient = null;

function _cargar_languageclient() {
    if (!LanguageClient) {
        const lc = require('vscode-languageclient/node');
        LanguageClient = lc.LanguageClient;
    }
}

// ---------------------------------------------------------------------------
// Detección de la raíz del proyecto Synapse
// Busca el binario LSP nativo o main.py en la jerarquía
// ---------------------------------------------------------------------------

function _encontrar_raiz_synapse(uriDocumento) {
    const carpetaWorkspace = vscode.workspace.workspaceFolders?.[0]?.uri?.fsPath;
    if (carpetaWorkspace) {
        // Check for test_lsp_bin.exe (LSP nativo) or main.py (build root)
        if (fs.existsSync(path.join(carpetaWorkspace, 'test_lsp_bin.exe')) ||
            fs.existsSync(path.join(carpetaWorkspace, 'main.py'))) {
            return carpetaWorkspace;
        }
    }

    if (uriDocumento) {
        let dir = path.dirname(uriDocumento.fsPath);
        while (dir !== path.parse(dir).root) {
            if (fs.existsSync(path.join(dir, 'test_lsp_bin.exe')) ||
                fs.existsSync(path.join(dir, 'main.py'))) {
                return dir;
            }
            dir = path.dirname(dir);
        }
    }

    return carpetaWorkspace || process.cwd();
}

// ---------------------------------------------------------------------------
// Construcción de opciones para el LanguageClient (usa binario LSP nativo)
// ---------------------------------------------------------------------------

function _crear_opciones_servidor(raizSynapse) {
    const cfg = vscode.workspace.getConfiguration('synapse');

    // Buscar binario LSP nativo: test_lsp_bin.exe > nucleo/lsp_test.exe > config
    let lspBinary = cfg.get('lsp.nativeBinary', '');
    if (!lspBinary) {
        const candidates = [
            path.join(raizSynapse, 'test_lsp_bin.exe'),
            path.join(raizSynapse, 'nucleo', 'lsp_test.exe'),
            path.join(raizSynapse, 'build', 'bin', 'synapse_lsp.exe'),
        ];
        for (const c of candidates) {
            if (fs.existsSync(c)) {
                lspBinary = c;
                break;
            }
        }
        if (!lspBinary) {
            lspBinary = path.join(raizSynapse, 'test_lsp_bin.exe');
        }
    }

    return {
        command: lspBinary,
        args: [],
        options: {
            cwd: raizSynapse,
            env: { ...process.env },
            stdio: 'pipe',
        },
        transport: 0,
    };
}

// ---------------------------------------------------------------------------
// Comandos registrados por la extensión
// ---------------------------------------------------------------------------

let _clienteLsp = null;

/**
 * Registra los comandos de IA local disponibles en la paleta de VS Code.
 */
function _registrar_comandos_ia(contexto, cliente) {
    // synapse.aiStatus — Verificar disponibilidad de IA local
    const comandoStatus = vscode.commands.registerCommand(
        'synapse.aiStatus',
        async () => {
            try {
                const resultado = await cliente.sendRequest('synapse/aiStatus', {});
                if (resultado?.ai_available) {
                    vscode.window.showInformationMessage(
                        `Synapse IA: ${resultado.provider} activo. Modelos: ${resultado.modelos.join(', ') || 'ninguno'}`
                    );
                } else {
                    const accion = await vscode.window.showWarningMessage(
                        'Synapse IA: Ollama no detectado. ¿Instalar Ollama?',
                        'Ir a ollama.ai',
                        'Cerrar'
                    );
                    if (accion === 'Ir a ollama.ai') {
                        vscode.env.openExternal(vscode.Uri.parse('https://ollama.ai'));
                    }
                }
            } catch (err) {
                vscode.window.showErrorMessage(`Synapse IA: Error de conexión — ${err.message}`);
            }
        }
    );

    // synapse.aiExplain — Explicar código seleccionado con IA local
    const comandoExplain = vscode.commands.registerCommand(
        'synapse.aiExplain',
        async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showWarningMessage('No hay editor activo');
                return;
            }

            const seleccion = editor.selection;
            let codigo = editor.document.getText(seleccion);
            if (!codigo) {
                const linea = editor.document.lineAt(seleccion.active.line);
                codigo = linea.text;
            }

            if (!codigo.trim()) {
                vscode.window.showWarningMessage('No hay código para explicar');
                return;
            }

            try {
                const resultado = await cliente.sendRequest('synapse/aiExplain', {
                    textDocument: { uri: editor.document.uri.toString() },
                    code: codigo,
                });

                if (resultado?.ai_available && resultado?.explanation) {
                    const panel = vscode.window.createOutputChannel('Synapse IA');
                    panel.clear();
                    panel.appendLine('=== Explicación IA ===');
                    panel.appendLine('');
                    panel.appendLine(resultado.explanation);
                    panel.show();
                } else {
                    vscode.window.showWarningMessage(
                        resultado?.message || 'IA local no disponible'
                    );
                }
            } catch (err) {
                vscode.window.showErrorMessage(`Error IA: ${err.message}`);
            }
        }
    );

    // synapse.aiComplete — Generar código con IA desde selección
    const comandoComplete = vscode.commands.registerCommand(
        'synapse.aiComplete',
        async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showWarningMessage('No hay editor activo');
                return;
            }

            const prompt = await vscode.window.showInputBox({
                prompt: 'Describe el código Synapse a generar',
                placeHolder: 'Ej: funcion que suma dos numeros enteros',
                ignoreFocusOut: true,
            });

            if (!prompt) return;

            const documento = editor.document;
            const textoActual = documento.getText();

            try {
                const resultado = await cliente.sendRequest('synapse/aiComplete', {
                    textDocument: { uri: documento.uri.toString() },
                    context: textoActual,
                    prompt: prompt,
                });

                if (resultado?.ai_available && resultado?.code) {
                    editor.edit((editBuilder) => {
                        const posicion = editor.selection.active;
                        editBuilder.insert(posicion, resultado.code + '\n');
                    });
                } else {
                    vscode.window.showWarningMessage(
                        resultado?.message || 'IA local no disponible'
                    );
                }
            } catch (err) {
                vscode.window.showErrorMessage(`Error IA: ${err.message}`);
            }
        }
    );

    contexto.subscriptions.push(comandoStatus, comandoExplain, comandoComplete);
}

// ---------------------------------------------------------------------------
// activate — llamada por VS Code al activar la extensión
// ---------------------------------------------------------------------------

/**
 * @param {vscode.ExtensionContext} contexto
 */
async function activate(contexto) {
    _cargar_languageclient();

    const salida = vscode.window.createOutputChannel('Synapse LSP');
    salida.appendLine('[Synapse] Activando extensión de lenguaje Synapse...');

    // Detectar la raíz del proyecto
    const documentoActual = vscode.window.activeTextEditor?.document;
    const raizSynapse = _encontrar_raiz_synapse(documentoActual?.uri);

    if (!raizSynapse) {
        salida.appendLine('[Synapse] ⚠️  Raiz del proyecto no detectada.');
        vscode.window.showWarningMessage(
            'Synapse: No se pudo detectar la raíz del proyecto. Abre una carpeta del proyecto Synapse.'
        );
        return;
    }

    salida.appendLine(`[Synapse] Raíz del proyecto: ${raizSynapse}`);
    const opcionesServidor = _crear_opciones_servidor(raizSynapse);
    salida.appendLine(`[Synapse] Iniciando servidor LSP nativo: ${opcionesServidor.command}`);

    const cliente = new LanguageClient(
        'synapseLsp',
        'Synapse Language Server',
        opcionesServidor,
        {
            documentSelector: [
                { scheme: 'file', language: 'synapse' },
                { scheme: 'file', pattern: '**/*.syn' },
            ],
            synchronize: {
                fileEvents: vscode.workspace.createFileSystemWatcher('**/*.syn'),
            },
            outputChannel: salida,
            traceOutputChannel: salida,
        }
    );

    // Registrar comandos de IA antes de iniciar el cliente
    _registrar_comandos_ia(contexto, cliente);

    // Iniciar el cliente LSP
    _clienteLsp = cliente;
    contexto.subscriptions.push(cliente.start());

    salida.appendLine('[Synapse] ✅ Servidor LSP iniciado correctamente');
    salida.appendLine('[Synapse]   - Diagnósticos en tiempo real');
    salida.appendLine('[Synapse]   - Comandos IA: synapse.aiStatus, synapse.aiExplain, synapse.aiComplete');
    salida.appendLine('[Synapse]   - IA local: Ollama en localhost:11434 (opcional)');
}

// ---------------------------------------------------------------------------
// deactivate — llamada por VS Code al desactivar la extensión
// ---------------------------------------------------------------------------

async function deactivate() {
    if (_clienteLsp) {
        await _clienteLsp.stop();
        _clienteLsp = null;
    }
}

module.exports = { activate, deactivate };
