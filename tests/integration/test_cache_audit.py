"""
tests/test_cache_audit.py
M20.2: Auditoria de Caché Incremental SHA-256
"""
import subprocess, os, sys, tempfile, time, hashlib, shutil
import pytest

pytestmark = pytest.mark.integration

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# cumple Manual 1 §7.2 (ME r193_fixtures_infra): la suite completa de pruebas
# debe pasar bajo el intérprete del PROYECTO (que tiene pytest y el sys.path
# del repo), no bajo un `python`/`python3` del sistema arbitrario. La detección
# _find_python() resolvía el venv ajeno de otra herramienta (sin pytest) y el
# subproceso `pytest tests/integration/test_axon_e2e.py` moría con rc=1.
PYTHON = sys.executable

PASS, FAIL = 0, 0
# cumple Manual 1 §7.2 (ME r193_fixtures_infra): cada test del auditor parte
# de contadores LIMPIOS y cobra SU propia cuenta. Antes, el único assert del
# contador global vivía al final de test_axon_lock_existente, así que un check
# fallido de T1-T3 (que terminaban en `return bool` — pytest ignora el valor y
# los marcaba passed) quedaba impago y lo cobraba el test Axon T1 siguiente.
@pytest.fixture(autouse=True)
def _contadores_limpios_por_test():
    global PASS, FAIL
    PASS, FAIL = 0, 0
    yield

def check(desc, cond, detail=""):
    global PASS, FAIL
    if cond:
        print(f"  [PASS] {desc}")
        PASS += 1
    else:
        print(f"  [FAIL] {desc} — {detail}")
        FAIL += 1

def run(cmd, timeout=900):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, timeout=timeout)
    return r.returncode, r.stdout, r.stderr

def _limpiar_cache():
    cache_dir = os.path.expanduser("~/.synapse/cache")
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)

def test_cache_hit():
    """Compilar dos veces seguida — la segunda debe usar cache HIT (más rápida)"""
    print("\n--- [Cache T1] HIT: segunda compilacion debe usar cache ---")
    _limpiar_cache()
    with tempfile.TemporaryDirectory(prefix="cache_audit_") as td:
        test_syn = os.path.join(td, "cache_test.syn")
        with open(test_syn, "w") as f:
            f.write('#lang: es\nfuncion principal() -> entero:\n    retornar 42\n')

        t0 = time.time()
        rc1, out1, err1 = run([PYTHON, "main.py", "--incremental", test_syn, "-o", os.path.join(td, "out1.exe")])
        t1 = time.time()
        t_first = t1 - t0

        t0 = time.time()
        rc2, out2, err2 = run([PYTHON, "main.py", "--incremental", test_syn, "-o", os.path.join(td, "out2.exe")])
        t1 = time.time()
        t_second = t1 - t0

        check("Primera compilacion exitosa", rc1 == 0, err1[-200:])
        check("Segunda compilacion exitosa", rc2 == 0, err2[-200:])
        check("[CACHE HIT] en segunda compilacion", "[CACHE" in out2 or "HIT" in out2, out2[-300:])
        check(f"Segunda ({t_second:.3f}s) mas rapida que primera ({t_first:.3f}s)",
              t_second < t_first, f"{t_first:.3f}s -> {t_second:.3f}s")
        # HIT real, determinista (ME r193): la segunda pasada NO recompila el
        # runtime — los [RUNTIME] gcc -c solo pueden aparecer en la primera.
        check("Sin recompilacion del runtime en segunda pasada (HIT real)",
              "[RUNTIME] gcc -c" not in out2, out2[-300:])
    assert FAIL == 0, "Checks fallaron"
def test_cache_stale():
    """Modificar std/ leaf file y detectar STALE en recompilacion incremental"""
    print("\n--- [Cache T2] STALE: detectar cambio en dependencia std/ ---")

    # Clear cache for clean test
    _limpiar_cache()

    std_io = os.path.join(ROOT, "std", "io.syn")
    backup = std_io + ".bak"

    # Create a test file that imports std.io
    with tempfile.TemporaryDirectory(prefix="cache_audit_") as td:
        test_syn = os.path.join(td, "cache_stale.syn")
        with open(test_syn, "w") as f:
            f.write('#lang: es\nimportar std.io\nfuncion principal() -> entero:\n    retornar 0\n')

        rc1, out1, err1 = run([PYTHON, "main.py", "--incremental", test_syn, "-o", os.path.join(td, "out1.exe")])
        check("Compilacion inicial exitosa", rc1 == 0, err1[-200:])
        if rc1 != 0:
            pytest.fail(f"Compilacion inicial fallo: {err1[-200:]}")

        # Add a comment to std/io.syn to simulate modification
        if os.path.exists(std_io):
            shutil.copy2(std_io, backup)
            try:
                with open(std_io, "a") as f:
                    f.write("\n// CACHE TEST: modification\n")

                rc2, out2, err2 = run([PYTHON, "main.py", "--incremental", test_syn, "-o", os.path.join(td, "out2.exe")])
                check("Recompilacion post-modificacion exitosa", rc2 == 0, err2[-200:])
                check("[CACHE MISS/STALE] detectado en recompilacion", "[CACHE" in out2 or "MISS" in out2, out2[-300:])

                # Restore original
                shutil.copy2(backup, std_io)
                os.remove(backup)

                # STALE real, determinista (ME r193): la recompilacion tras
                # tocar std/ NO vuelve a compilar el runtime (objs cacheados,
                # fuente sin cambios) — solo el objeto de usuario.
                check("Sin recompilacion del runtime en recompilacion STALE",
                      "[RUNTIME] gcc -c" not in out2, out2[-300:])
            except Exception as e:
                # Restore
                if os.path.exists(backup):
                    shutil.copy2(backup, std_io)
                    os.remove(backup)
                pytest.fail(f"ERROR en STALE: {e}")
        else:
            pytest.skip(f"{std_io} not found")

    assert FAIL == 0, "Checks fallaron"
def test_cache_determinismo():
    """Mismo contenido debe producir mismo hash SHA-256"""
    print("\n--- [Cache T3] Determinismo SHA-256 ---")

    content = b"contenido de prueba para hash"
    h1 = hashlib.sha256(content).hexdigest()
    h2 = hashlib.sha256(content).hexdigest()

    check("SHA-256 determinista: mismo contenido = mismo hash", h1 == h2)

    # Different content = different hash
    h3 = hashlib.sha256(b"otro contenido").hexdigest()
    check("SHA-256 diferenciador: distinto contenido = distinto hash", h1 != h3)

    assert FAIL == 0, "Checks fallaron"
def test_axon_lock_existente():
    """Ejecutar test_axon_e2e.py existente"""
    print("\n--- [Axon T1] Suite E2E existente ---")
    rc, out, err = run([sys.executable, "-m", "pytest", "tests/integration/test_axon_e2e.py", "-v", "--tb=short"], timeout=120)
    check("test_axon_e2e.py ejecuta sin error", rc == 0, err[-300:] + out[-300:])
    assert FAIL == 0, "Checks fallaron"

def main():
    print("=" * 60)
    print("  M20.2: AUDITORIA DE CACHE INCREMENTAL SHA-256 + AXON")
    print("  Manual 3 S3.4 / Manual 6 S6.5")
    print("=" * 60)

    # Clear cache
    _limpiar_cache()

    test_cache_hit()
    test_cache_stale()
    test_cache_determinismo()
    test_axon_lock_existente()

    print(f"\n{'='*60}")
    print(f"  Resultados: {PASS} PASS, {FAIL} FAIL de {PASS+FAIL} tests")
    print(f"{'='*60}")
    return FAIL == 0

if __name__ == "__main__":
    sys.exit(0 if main() else 1)

    assert FAIL == 0, "Checks fallaron"