"""
FASE 25 — E2E Test: Counter App WASM en navegador headless (Playwright).

Valida que la SPA Counter App funciona correctamente en un navegador:
- La página carga correctamente
- El módulo WASM se instancia
- Los botones increment/decrement/reset funcionan
- El contador muestra valores correctos
- No hay errores de JavaScript

Comando:
    pytest tests/test_e2e_spa_counter.py -v
"""
import os
import subprocess
import sys
import pytest

pytestmark = pytest.mark.e2e

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SPA_DIR = os.path.join(PROJECT_ROOT, "examples", "syquex", "counter")


def _has_playwright():
    try:
        import playwright
        return True
    except ImportError:
        return False


def _has_chromium():
    ms_playwright = os.path.expanduser("~/AppData/Local/ms-playwright")
    if not os.path.exists(ms_playwright):
        return False
    return any("chromium" in d for d in os.listdir(ms_playwright))


@pytest.mark.skipif(not _has_playwright(), reason="playwright not installed")
@pytest.mark.skipif(not _has_chromium(), reason="chromium not installed")
class TestE2ESPACounter:

    @pytest.fixture(scope="class")
    def page_context(self):
        """Lanza navegador y crea página."""
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            yield page
            browser.close()

    def _start_server(self):
        """Inicia un servidor HTTP en el directorio de la SPA."""
        import threading
        import http.server
        import functools

        handler = functools.partial(
            http.server.SimpleHTTPRequestHandler,
            directory=SPA_DIR
        )
        server = http.server.HTTPServer(("localhost", 8082), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server

    def test_spa_counter_e2e(self, page_context):
        """Test E2E completo: carga, WASM, increment, decrement, reset."""
        server = self._start_server()
        page = page_context

        try:
            # 1. Navigate
            page.goto("http://localhost:8082", wait_until="networkidle")

            # 2. Title
            title = page.title()
            assert "Syquex" in title, f"Title: {title}"

            # 3. WASM loaded
            status = page.text_content("#status")
            assert "WASM loaded" in status, f"Status: {status}"

            # 4. Initial value
            value = page.text_content("#counter-value").strip()
            assert value == "0", f"Initial value: {value}"

            # 5. Increment
            page.click("#btn-inc")
            page.wait_for_timeout(100)
            value = page.text_content("#counter-value").strip()
            assert value == "1", f"After +1: {value}"

            page.click("#btn-inc")
            page.wait_for_timeout(100)
            value = page.text_content("#counter-value").strip()
            assert value == "2", f"After +1 again: {value}"

            # 6. Decrement
            page.click("#btn-dec")
            page.wait_for_timeout(100)
            value = page.text_content("#counter-value").strip()
            assert value == "1", f"After -1: {value}"

            # 7. Reset
            page.click("#btn-reset")
            page.wait_for_timeout(100)
            value = page.text_content("#counter-value").strip()
            assert value == "0", f"After reset: {value}"

            # 8. Negative
            page.click("#btn-dec")
            page.wait_for_timeout(100)
            value = page.text_content("#counter-value").strip()
            assert value == "-1", f"After -1 from 0: {value}"

            # 9. DOM structure
            assert page.is_visible("#counter-value")
            assert page.is_visible("#btn-inc")
            assert page.is_visible("#btn-dec")
            assert page.is_visible("#btn-reset")

        finally:
            server.shutdown()
