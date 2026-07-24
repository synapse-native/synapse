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
const child_process = require('child_process');

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
// Constantes de rutas de instalación
// ---------------------------------------------------------------------------

const SYNAPSE_INSTALL_DIR = 'C:\\Synapse';
const SYNAPSE_LSP_PATH = path.join(SYNAPSE_INSTALL_DIR, 'bin', 'synapse.exe');
const SYNAPSE_INSTALLER_URL = 'https://github.com/gedeon1972-svg/synapse-lang/releases/download/v1.5.0/synapse-v1.5.0-windows-x64.zip';

// ---------------------------------------------------------------------------
// Auto-descubrimiento e instalación automática del binario LSP
// ---------------------------------------------------------------------------

async function _asegurar_binario_lsp(salida) {
    // 1. Buscar en la ruta de instalación estándar (configurada por install.ps1)
    if (fs.existsSync(SYNAPSE_LSP_PATH)) {
        salida.appendLine(`[Synapse] Binario LSP encontrado en instalación: ${SYNAPSE_LSP_PATH}`);
        return SYNAPSE_LSP_PATH;
    }

    // 2. Buscar en PATH del sistema
    const pathEntries = process.env.PATH?.split(';') || [];
    for (const entry of pathEntries) {
        const candidate = path.join(entry, 'synapse_lsp.exe');
        if (fs.existsSync(candidate)) {
            salida.appendLine(`[Synapse] Binario LSP encontrado en PATH: ${candidate}`);
            return candidate;
        }
    }

    // 3. Buscar en el workspace actual (desarrollo local)
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri?.fsPath;
    if (workspaceRoot) {
        const candidates = [
            path.join(workspaceRoot, 'test_lsp_bin.exe'),
            path.join(workspaceRoot, 'nucleo', 'lsp_test.exe'),
            path.join(workspaceRoot, 'build', 'bin', 'synapse_lsp.exe'),
        ];
        for (const c of candidates) {
            if (fs.existsSync(c)) {
                salida.appendLine(`[Synapse] Binario LSP encontrado en workspace: ${c}`);
                return c;
            }
        }
    }

    // 4. No encontrado - ofrecer instalación automática
    salida.appendLine('[Synapse] ⚠️  Binario LSP no encontrado. Ofreciendo instalación automática...');
    
    const accion = await vscode.window.showInformationMessage(
        'Synapse: Servidor LSP no encontrado. ¿Desea descargar e instalar Synapse automáticamente?',
        { modal: true },
        'Instalar Synapse',
        'Configurar ruta manualmente',
        'Cancelar'
    );

    if (accion === 'Instalar Synapse') {
        return await _instalar_synapse_automatico(salida);
    } else if (accion === 'Configurar ruta manualmente') {
        const ruta = await vscode.window.showInputBox({
            prompt: 'Introduzca la ruta completa a synapse_lsp.exe',
            placeHolder: 'C:\\ruta\\a\\synapse_lsp.exe',
            ignoreFocusOut: true,
        });
        if (ruta && fs.existsSync(ruta)) {
            salida.appendLine(`[Synapse] Usando ruta manual: ${ruta}`);
            return ruta;
        }
    }

    throw new Error('Synapse LSP no disponible. Instale Synapse o configure la ruta manualmente.');
}

async function _instalar_synapse_automatico(salida) {
    salida.appendLine('[Synapse] Iniciando descarga automática del instalador...');
    
    const tempDir = process.env.TEMP || process.env.TMP || 'C:\\Windows\\Temp';
    const zipPath = path.join(tempDir, 'synapse-install.zip');
    
    // Descargar usando PowerShell (más fiable en Windows)
    return new Promise((resolve, reject) => {
        const psScript = `
            $ProgressPreference = 'silentlyContinue'
            try {
                Write-Host "Descargando Synapse..."
                Invoke-WebRequest -Uri "${SYNAPSE_INSTALLER_URL}" -OutFile "${zipPath}" -UseBasicParsing -ErrorAction Stop
                Write-Host "DESCARGA_OK"
                
                Write-Host "Extrayendo..."
                [System.IO.Compression.ZipFile]::ExtractToDirectory("${zipPath}", "${SYNAPSE_INSTALL_DIR}")
                Write-Host "EXTRACTION_OK"
                
                # Ejecutar post-instalación (MinGW toolchain)
                $PostInstall = Join-Path "${SYNAPSE_INSTALL_DIR}" "install.ps1"
                if (Test-Path $PostInstall) {
                    Write-Host "Ejecutando post-instalacion (MinGW)..."
                    & powershell.exe -ExecutionPolicy Bypass -NoProfile -File $PostInstall
                    Write-Host "POST_INSTALL_OK"
                } else {
                    Write-Host "ADVERTENCIA: install.ps1 no encontrado, saltando post-instalacion"
                }
                
                # Verificar que el binario existe (synapse.exe, no synapse_lsp.exe)
                $LspPath = Join-Path "${SYNAPSE_INSTALL_DIR}" "bin\\synapse.exe"
                if (Test-Path $LspPath) {
                    Write-Host "INSTALL_OK"
                    exit 0
                } else {
                    Write-Host "ERROR: synapse.exe no encontrado tras extraccion"
                    exit 1
                }
            } catch {
                Write-Host "ERROR: $($_.Exception.Message)"
                exit 1
            }
        `;
        
        const psProcess = child_process.spawn('powershell', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', psScript], {
            stdio: ['pipe', 'pipe', 'pipe']
        });

        let stdout = '';
        let stderr = '';

        psProcess.stdout.on('data', (data) => {
            const text = data.toString();
            stdout += text;
            salida.appendLine(`[Install] ${text.trim()}`);
        });

        psProcess.stderr.on('data', (data) => {
            stderr += data.toString();
            salida.appendLine(`[Install ERROR] ${data.toString().trim()}`);
        });

        psProcess.on('close', (code) => {
            if (code === 0 && stdout.includes('INSTALL_OK')) {
                salida.appendLine('[Synapse] ✅ Instalación automática completada');
                resolve(SYNAPSE_LSP_PATH);
            } else {
                const errorMsg = stderr || stdout || `Proceso terminó con código ${code}`;
                salida.appendLine(`[Synapse] ❌ Falló la instalación automática: ${errorMsg}`);
                reject(new Error(`Instalación fallida: ${errorMsg}`));
            }
        });

        psProcess.on('error', (err) => {
            salida.appendLine(`[Synapse] ❌ Error lanzando PowerShell: ${err.message}`);
            reject(err);
        });
    });
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

function _crear_opciones_servidor(raizSynapse, lspBinaryPath) {
    const cfg = vscode.workspace.getConfiguration('synapse');

    // Si el usuario configuró una ruta manual, usarla
    const manualBinary = cfg.get('lsp.nativeBinary', '');
    if (manualBinary && fs.existsSync(manualBinary)) {
        return {
            command: manualBinary,
            args: [],
            options: {
                cwd: raizSynapse,
                env: { ...process.env },
                stdio: 'pipe',
            },
            transport: 0,
        };
    }

    // Usar la ruta validada (instalación o auto-descubierta)
    return {
        command: lspBinaryPath,
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

    // Auto-descubrimiento / instalación del binario LSP
    let lspBinaryPath;
    try {
        lspBinaryPath = await _asegurar_binario_lsp(salida);
    } catch (err) {
        salida.appendLine(`[Synapse] ❌ Error crítico: ${err.message}`);
        vscode.window.showErrorMessage(`Synapse LSP no disponible: ${err.message}`);
        return;
    }

    const opcionesServidor = _crear_opciones_servidor(raizSynapse, lspBinaryPath);
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
