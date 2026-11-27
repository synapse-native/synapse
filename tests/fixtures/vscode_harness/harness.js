// tests/fixtures/vscode_harness/harness.js
// Harness que simula la extensión VS Code para probar el registro de comandos.
// 15 comandos: aiLint, aiFmt, aiTest, format, docs, debugStepForward/Backward,
// Snapshots, Restart, plus debug palette commands.

const vscode = require('vscode');

// Mapa de comandos registrados por la extensión r278
const comandosRegistrados = [
    // Comandos de depuración debugger (Manual 8 §3.5)
    "synapse.debugStepForward",
    "synapse.debugStepBackward",
    "synapse.debugContinue",
    "synapse.debugRestart",
    "synapse.debugSnapshots",
    "synapse.debugPalette",

    // Comandos de IA (Manual 8 §2.3)
    "aiFmt",
    "aiLint",
    "aiTest",
    "aiComplete",
    "aiExplain",

    // Comandos de formato y docs
    "format",
    "docs",

    // Comando de debug adicional
    "synapse.debug"
];

function activar(contexto) {
    // Registrar todos los comandos
    contexto.subscriptions.push(
        vscode.commands.registerCommand('synapse.debugStepForward', () => {
            // Implementación real delegada al CLI
        })
    );
    contexto.subscriptions.push(
        vscode.commands.registerCommand('synapse.debugStepBackward', () => {
            // Implementación real delegada al CLI
        })
    );
    contexto.subscriptions.push(
        vscode.commands.registerCommand('synapse.debugContinue', () => {
            // Implementación real delegada al CLI
        })
    );
    contexto.subscriptions.push(
        vscode.commands.registerCommand('synapse.debugRestart', () => {
            // Implementación real delegada al CLI
        })
    );
    contexto.subscriptions.push(
        vscode.commands.registerCommand('synapse.debugSnapshots', () => {
            // Implementación real delegada al CLI
        })
    );
    contexto.subscriptions.push(
        vscode.commands.registerCommand('synapse.debugPalette', () => {
            // Implementación real delegada al CLI
        })
    );

    // Comandos de IA
    contexto.subscriptions.push(
        vscode.commands.registerCommand('aiFmt', () => {})
    );
    contexto.subscriptions.push(
        vscode.commands.registerCommand('aiLint', () => {})
    );
    contexto.subscriptions.push(
        vscode.commands.registerCommand('aiTest', () => {})
    );
    contexto.subscriptions.push(
        vscode.commands.registerCommand('aiComplete', () => {})
    );
    contexto.subscriptions.push(
        vscode.commands.registerCommand('aiExplain', () => {})
    );

    // Comandos de soporte
    contexto.subscriptions.push(
        vscode.commands.registerCommand('format', () => {})
    );
    contexto.subscriptions.push(
        vscode.commands.registerCommand('docs', () => {})
    );

    // Comando debug principal
    contexto.subscriptions.push(
        vscode.commands.registerCommand('synapse.debug', () => {})
    );
}

module.exports = { activar, comandosRegistrados };

// Harness para testing
function verificar_comandos(cantidad_esperada) {
    const registrados = comandosRegistrados.length;
    const validos = comandosRegistrados.filter(c => c && c.length > 0).length;

    return {
        ok: registrados >= cantidad_esperada,
        comandos_registrados: registrados,
        comandos_validos: validos,
        lista_comandos: comandosRegistrados
    };
}