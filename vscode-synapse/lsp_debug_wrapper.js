/**
 * lsp_debug_wrapper.js — Transparent proxy that logs all raw bytes
 * between VS Code LanguageClient and synapse_lsp.exe.
 * 
 * Logs to %TEMP%/synapse_lsp_debug.log
 * The extension sets SYNAPSE_LSP_REAL env var to the real binary path.
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const LOG_PATH = path.join(process.env.TEMP || process.env.TMP || 'C:\\Windows\\Temp', 'synapse_lsp_debug.log');
const REAL_BINARY = process.env.SYNAPSE_LSP_REAL || 'C:\\Program Files\\Synapse\\bin\\synapse_lsp.exe';

function log(tag, data) {
    const ts = new Date().toISOString();
    const buf = Buffer.isBuffer(data) ? data : Buffer.from(data, 'utf8');
    const hex = buf.toString('hex');
    const text = buf.toString('utf8');
    fs.appendFileSync(LOG_PATH, `[${ts}] ${tag} [${buf.length} bytes]\n`);
    fs.appendFileSync(LOG_PATH, `  HEX: ${hex.substring(0, 400)}${hex.length > 400 ? '...' : ''}\n`);
    fs.appendFileSync(LOG_PATH, `  TEXT: ${JSON.stringify(text.substring(0, 500))}${text.length > 500 ? '...' : ''}\n\n`);
}

// Clear and start log
fs.writeFileSync(LOG_PATH, `=== Synapse LSP Debug Wrapper ===\nStarted: ${new Date().toISOString()}\nPID: ${process.pid}\nReal binary: ${REAL_BINARY}\nExists: ${fs.existsSync(REAL_BINARY)}\nCWD: ${process.cwd()}\nARGV: ${JSON.stringify(process.argv.slice(2))}\n\n`);

const child = spawn(REAL_BINARY, process.argv.slice(2), {
    stdio: ['pipe', 'pipe', 'pipe'],
    env: { ...process.env },
});

log('SPAWN', `Child PID: ${child.pid}`);

// Capture ALL stdin (from VS Code to server)
process.stdin.on('data', (data) => {
    log('STDIN (client->server)', data);
    child.stdin.write(data);
});
process.stdin.on('end', () => {
    log('STDIN_EOF', 'Client closed stdin');
    child.stdin.end();
});

// Capture ALL stdout (from server to VS Code)
child.stdout.on('data', (data) => {
    log('STDOUT (server->client)', data);
    process.stdout.write(data);
});

// Capture ALL stderr
child.stderr.on('data', (data) => {
    log('STDERR', data);
    process.stderr.write(data);
});

child.on('error', (err) => {
    log('ERROR', `Child error: ${err.message}`);
    process.exit(1);
});

child.on('close', (code, signal) => {
    log('CLOSE', `Child exited code=${code} signal=${signal}`);
    process.exit(code || 0);
});

process.on('disconnect', () => {
    log('DISCONNECT', 'Parent disconnected');
    child.kill();
});

log('READY', 'Waiting for data...');
