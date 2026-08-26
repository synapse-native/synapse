// examples/syquex/counter/test_e2e.js
// FASE 25 — E2E Test: Counter App WASM en navegador headless (Playwright)
//
// Requisitos: npm install playwright, npx playwright install chromium
// Ejecutar: node test_e2e.js

const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 8081;
const DIR = __dirname;

// ============================================================
// Mini HTTP server para servir los archivos estáticos
// ============================================================
function createServer() {
    return new Promise((resolve) => {
        const server = http.createServer((req, res) => {
            let filePath = path.join(DIR, req.url === '/' ? 'index.html' : req.url);
            const ext = path.extname(filePath);
            const mimeTypes = {
                '.html': 'text/html',
                '.js': 'application/javascript',
                '.wasm': 'application/wasm',
                '.css': 'text/css',
            };
            const contentType = mimeTypes[ext] || 'application/octet-stream';

            fs.readFile(filePath, (err, data) => {
                if (err) {
                    res.writeHead(404);
                    res.end('Not found');
                    return;
                }
                res.writeHead(200, { 'Content-Type': contentType });
                res.end(data);
            });
        });
        server.listen(PORT, () => resolve(server));
    });
}

// ============================================================
// Tests
// ============================================================
async function runTests() {
    let server;
    let browser;
    let passed = 0;
    let failed = 0;

    function check(condition, name) {
        if (condition) {
            console.log(`  [PASS] ${name}`);
            passed++;
        } else {
            console.log(`  [FAIL] ${name}`);
            failed++;
        }
    }

    try {
        // Start server
        console.log('=== FASE 25 — E2E Test: Counter App WASM ===\n');
        server = await createServer();
        console.log(`Server running on http://localhost:${PORT}\n`);

        // Launch browser
        browser = await chromium.launch({ headless: true });
        const page = await browser.newPage();

        // Navigate to the app
        await page.goto(`http://localhost:${PORT}`, { waitUntil: 'networkidle' });

        // --- Test 1: Page loads ---
        console.log('--- 1. Page Load ---');
        const title = await page.title();
        check(title.includes('Syquex'), `Title contains "Syquex": "${title}"`);

        // --- Test 2: WASM loads ---
        console.log('\n--- 2. WASM Load ---');
        const status = await page.textContent('#status');
        check(status.includes('WASM loaded'), `Status shows WASM loaded: "${status}"`);

        // --- Test 3: Initial counter value ---
        console.log('\n--- 3. Initial State ---');
        const initialValue = await page.textContent('#counter-value');
        check(initialValue.trim() === '0', `Initial counter is 0: "${initialValue.trim()}"`);

        // --- Test 4: Increment ---
        console.log('\n--- 4. Increment ---');
        await page.click('#btn-inc');
        await page.waitForTimeout(100);
        let value = await page.textContent('#counter-value');
        check(value.trim() === '1', `After +1: counter is 1: "${value.trim()}"`);

        await page.click('#btn-inc');
        await page.waitForTimeout(100);
        value = await page.textContent('#counter-value');
        check(value.trim() === '2', `After +1 again: counter is 2: "${value.trim()}"`);

        // --- Test 5: Decrement ---
        console.log('\n--- 5. Decrement ---');
        await page.click('#btn-dec');
        await page.waitForTimeout(100);
        value = await page.textContent('#counter-value');
        check(value.trim() === '1', `After -1: counter is 1: "${value.trim()}"`);

        // --- Test 6: Reset ---
        console.log('\n--- 6. Reset ---');
        await page.click('#btn-reset');
        await page.waitForTimeout(100);
        value = await page.textContent('#counter-value');
        check(value.trim() === '0', `After reset: counter is 0: "${value.trim()}"`);

        // --- Test 7: Multiple operations ---
        console.log('\n--- 7. Multiple Operations ---');
        await page.click('#btn-inc');
        await page.click('#btn-inc');
        await page.click('#btn-inc');
        await page.click('#btn-dec');
        await page.waitForTimeout(100);
        value = await page.textContent('#counter-value');
        check(value.trim() === '2', `After +1+1+1-1: counter is 2: "${value.trim()}"`);

        // --- Test 8: Negative values ---
        console.log('\n--- 8. Negative Values ---');
        await page.click('#btn-reset');
        await page.click('#btn-dec');
        await page.waitForTimeout(100);
        value = await page.textContent('#counter-value');
        check(value.trim() === '-1', `After reset then -1: counter is -1: "${value.trim()}"`);

        // --- Test 9: DOM elements exist ---
        console.log('\n--- 9. DOM Structure ---');
        check(await page.isVisible('#counter-value'), 'Counter display visible');
        check(await page.isVisible('#btn-inc'), 'Increment button visible');
        check(await page.isVisible('#btn-dec'), 'Decrement button visible');
        check(await page.isVisible('#btn-reset'), 'Reset button visible');

        // --- Test 10: No JS errors ---
        console.log('\n--- 10. No JS Errors ---');
        let jsErrors = [];
        page.on('pageerror', (err) => jsErrors.push(err.message));
        await page.reload({ waitUntil: 'networkidle' });
        await page.waitForTimeout(500);
        check(jsErrors.length === 0, `No JS errors (got ${jsErrors.length})`);

    } catch (err) {
        console.error('Test error:', err.message);
        failed++;
    } finally {
        if (browser) await browser.close();
        if (server) server.close();
    }

    // Summary
    console.log('\n========================================');
    console.log(`E2E Counter App: ${passed} passed, ${failed} failed`);
    console.log('========================================');

    process.exit(failed > 0 ? 1 : 0);
}

runTests();
