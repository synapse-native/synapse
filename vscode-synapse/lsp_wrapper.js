/**
 * lsp_wrapper.js — Transparent logging wrapper for synapse_lsp.exe
 * 
 * Launches synapse_lsp.exe and pipes all communication through,
 * while logging every byte sent/received to a log file.
 * 
 * Usage: node lsp_wrapper.js [args...]
 * Logs to: %TEMP%/synapse_lsp_proxy.log
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const LOG_PATH = path.join(process.env.TEMP || process.env.TMP || 'C:\\Windows\\Temp', 'synapse_lsp_proxy.log');
const SYNAPSE_LSP = path.join('C:\\Program Files\\Synapse\\bin', 'synapse_lsp.exe');

// Clear log
fs.writeFileSync(LOG_PATH, `=== Synapse LSP Proxy started at ${new Date().toISOString()} ===\nPID: ${process.pid}\n`);
fs.appendFileSync(LOG_PATH, `ARGV: ${JSON.stringify(process.argv)}\n`);
fs.appendFileSync(LOG_PATH, `CWD: ${process.cwd()}\n`);
fs.appendFileSync(LOG_PATH, `SYNAPSE_LSP: ${SYNAPSE_LSP}\n`);
fs.appendFileSync(LOG_PATH, `EXISTS: ${fs.existsSync(SYNAPSE_LSP)}\n`);
fs.appendFileSync(LOG_PATH, `ENV PATH: ${process.env.PATH}\n`);
fs.appendFileSync(LOG_PATH, '---\n');

function log(tag, data) {
    const ts = new Date().toISOString();
    const text = typeof data === 'string' ? data : data.toString('utf8');
    const hex = typeof data === 'string' ? Buffer.from(data, 'utf8').toString('hex') : data.toString('hex');
    fs.appendFileSync(LOG_PATH, `[${ts}] ${tag} [${data.length || 0} bytes]\n  HEX: ${hex.substring(0, 200)}${hex.length > 200 ? '...' : ''}\n  TEXT: ${JSON.stringify(text.substring(0, 300))}${text.length > 300 ? '...' : ''}\n`);
}

// Spawn the real binary
const realArgs = process.argv.slice(2);
log('SPAWN', `Spawning: ${SYNAPSE_LSP} args=${JSON.stringify(realArgs)}`);

const child = spawn(SYNAPSE_LSP, realArgs, {
    stdio: ['pipe', 'pipe', 'pipe'],
    env: { ...process.env },
});

log('SPAWNED', `Child PID: ${child.pid}`);

// Pipe stdin → child stdin (with logging)
process.stdin.on('data', (data) => {
    log('CLIENT→SERVER', data);
    child.stdin.write(data);
});
process.stdin.on('end', () => {
    log('STDIN_EOF', 'stdin closed');
    child.stdin.end();
});

// Pipe child stdout → stdout (with logging)
child.stdout.on('data', (data) => {
    log('SERVER→CLIENT', data);
    process.stdout.write(data);
});

// Pipe child stderr → stderr (with logging)
child.stderr.on('data', (data) => {
    log('STDERR', data);
    process.stderr.write(data);
});

child.on('error', (err) => {
    log('ERROR', `Child error: ${err.message}`);
    process.exit(1);
});

child.on('close', (code) => {
    log('CLOSE', `Child exited with code ${code}`);
    process.exit(code || 0);
});

process.on('SIGTERM', () => {
    log('SIGTERM', 'Received SIGTERM');
    child.kill();
});

process.on('SIGINT', () => {
    log('SIGINT', 'Received SIGINT');
    child.kill();
});

log('READY', 'Proxy ready, waiting for data...');
