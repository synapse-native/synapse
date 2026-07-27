"""
test_cluster_multicast.py — Pruebas de integración para M8.6 (UDP Multicast Real)

Valida:
- Inicialización de socket multicast con IP_ADD_MEMBERSHIP
- Envío y recepción de anuncios SYNCLUSTER por multicast real (loopback)
- Hilo de descubrimiento activo en segundo plano
- Inicialización/detención reentrante
- Casos borde: parámetros inválidos, múltiples inicios
"""

import os
import subprocess
import sys
import time

# --- Configuración ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TESTS_DIR = os.path.join(PROJECT_ROOT, "tests")
BIN_NAME = "test_cluster_multicast.exe" if sys.platform == "win32" else "test_cluster_multicast"
BIN_PATH = os.path.join(TESTS_DIR, BIN_NAME)
SYNAPSE_RT_O = os.path.join(PROJECT_ROOT, "synapse_rt.o")
TWEETNACL_O = os.path.join(PROJECT_ROOT, "tweetnacl.o")

# Toolchain
TOOLCHAIN_GCC = os.path.join(PROJECT_ROOT, "toolchain_gcc12", "mingw64", "bin", "gcc.exe")
if not os.path.exists(TOOLCHAIN_GCC):
    TOOLCHAIN_GCC = "gcc"


def _compilar():
    """Compila el binario de prueba multicast."""
    if not os.path.exists(SYNAPSE_RT_O):
        print(f"[SKIP] synapse_rt.o no encontrado")
        return False
    src = os.path.join(TESTS_DIR, "test_cluster_multicast.c")
    if not os.path.exists(src):
        print(f"[SKIP] {src} no encontrado")
        return False
    cmd = [
        TOOLCHAIN_GCC, "-O2", "-std=c99",
        src, SYNAPSE_RT_O,
        TWEETNACL_O if os.path.exists(TWEETNACL_O) else "",
        "-o", BIN_PATH,
        "-lm", "-lpthread", "-lws2_32"
    ]
    cmd = [c for c in cmd if c]
    print(f"[INFO] Compilando: {' '.join(cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        print(f"[FAIL] Compilación falló:\nSTDERR: {r.stderr}")
        return False
    print(f"[OK] Binario compilado: {BIN_PATH}")
    return True


def _ejecutar():
    """Ejecuta el binario de prueba y retorna (returncode, stdout, stderr)."""
    if not os.path.exists(BIN_PATH):
        return (-1, "", "Binario no encontrado")
    r = subprocess.run([BIN_PATH], capture_output=True, text=True, timeout=30)
    return (r.returncode, r.stdout, r.stderr)


# ============================================================
# Tests
# ============================================================

class TestCompilacion:
    """Prueba que el binario C compile correctamente."""

    def test_compilacion(self):
        assert _compilar(), "El binario de prueba debe compilar"


class TestEjecucionCompleta:
    """Ejecuta el binario y verifica que todos los tests pasen."""

    @classmethod
    def setup_class(cls):
        if not os.path.exists(BIN_PATH):
            if not _compilar():
                raise RuntimeError("No se pudo compilar el binario de prueba")

    def test_todos_los_tests_pasan(self):
        rc, stdout, stderr = _ejecutar()
        print(f"\n[STDERR]\n{stderr[:3000]}")
        assert rc == 0, f"El binario retornó código {rc} (se esperaba 0)"
        assert "TODOS LOS TESTS PASARON" in (stderr + stdout), \
            "Debe indicar que todos los tests pasaron"
        assert "Fallos: 0" in (stderr + stdout), "No debe haber fallos"

    def test_salida_estructurada(self):
        rc, stdout, stderr = _ejecutar()
        assert "Test M8.6" in (stderr + stdout), "Debe mostrar encabezado M8.6"
        assert "RESULTADOS" in (stderr + stdout), "Debe mostrar sección de resultados"


class TestEscenariosEspecificos:
    """Verifica escenarios específicos de multicast."""

    @classmethod
    def setup_class(cls):
        if not os.path.exists(BIN_PATH):
            if not _compilar():
                raise RuntimeError("No se pudo compilar el binario de prueba")
        cls.rc, cls.stdout, cls.stderr = _ejecutar()

    def test_inicializacion_multicast(self):
        assert "Test 1" in self.stderr, "Debe ejecutar test de inicialización multicast"

    def test_envio_recepcion(self):
        assert "Test 2" in self.stderr, "Debe ejecutar test de envío/recepción"

    def test_discovery_completo(self):
        assert "Test 3" in self.stderr, "Debe ejecutar test de discovery completo"

    def test_envio_directo_loopback(self):
        assert "Test 4" in self.stderr, "Debe ejecutar test de loopback directo"

    def test_hilo_descubrimiento(self):
        assert "Test 5" in self.stderr, "Debe ejecutar test de hilo de descubrimiento"
        assert "hilo activo" in self.stderr, "Debe verificar hilo activo"

    def test_reinicio_hilo(self):
        assert "Test 6" in self.stderr, "Debe ejecutar test de reinicio de hilo"
        assert "segundo hilo rechazado" in self.stderr, "Debe verificar rechazo de segundo hilo"

    def test_multicast_reentrante(self):
        assert "Test 7" in self.stderr, "Debe ejecutar test de multicast reentrante"

    def test_cleanup_final(self):
        assert "Test 8" in self.stderr, "Debe ejecutar test de cleanup final"

    def test_todos_los_tests_ejecutados(self):
        for i in range(1, 9):
            assert f"Test {i}" in self.stderr, f"Debe ejecutar Test {i}"


class TestCasosBorde:
    """Prueba casos borde del binario."""

    @classmethod
    def setup_class(cls):
        if not os.path.exists(BIN_PATH):
            if not _compilar():
                raise RuntimeError("No se pudo compilar el binario de prueba")

    def test_binario_no_crasha(self):
        rc, stdout, stderr = _ejecutar()
        assert rc == 0, f"Binario no debe crashar (rc={rc})"
        assert "SIGSEGV" not in stderr, "No debe haber segfaults"


class TestRendimiento:
    """Prueba de rendimiento del componente multicast."""

    @classmethod
    def setup_class(cls):
        if not os.path.exists(BIN_PATH):
            if not _compilar():
                raise RuntimeError("No se pudo compilar el binario de prueba")

    def test_ejecucion_rapida(self):
        inicio = time.time()
        rc, stdout, stderr = _ejecutar()
        duracion = time.time() - inicio
        assert rc == 0, f"Debe pasar (rc={rc})"
        assert duracion < 10.0, f"Debe completar en <10s (tomó {duracion:.2f}s)"
        print(f"[OK] Duración: {duracion:.3f}s")


# ============================================================
# Punto de entrada para ejecución directa
# ============================================================

def run_direct_tests():
    """Ejecuta pruebas directas sin pytest."""
    print("=== Pruebas directas M8.6 ===")
    if not _compilar():
        print("[FAIL] No se pudo compilar")
        return 1
    rc, stdout, stderr = _ejecutar()
    print(f"\n[STDERR]\n{stderr[:3000]}")
    if rc == 0 and "TODOS LOS TESTS PASARON" in (stderr + stdout):
        print("\n[PASS] Todos los tests C pasaron")
        return 0
    else:
        print(f"\n[FAIL] Tests C fallaron (rc={rc})")
        return 1


if __name__ == "__main__":
    sys.exit(run_direct_tests())
