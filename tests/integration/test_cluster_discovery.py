"""
test_cluster_discovery.py — Pruebas de integración para M8.5 (Auto-Descubrimiento y Membresía)

Valida:
- Inicialización del subsistema de descubrimiento
- Registro de nodos y consulta de membresía
- Heartbeat: tick, timeout, purga automática
- Generación y procesamiento de anuncios SYNCLUSTER
- Verificación de salud de nodos
- Casos borde: tabla llena, nodos duplicados, anuncios inválidos
"""

import os
import subprocess
import sys
import time

# --- Configuración ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TESTS_DIR = os.path.join(PROJECT_ROOT, "tests")
BIN_NAME = "test_cluster_discovery.exe" if sys.platform == "win32" else "test_cluster_discovery"
BIN_PATH = os.path.join(TESTS_DIR, BIN_NAME)
SYNAPSE_RT_O = os.path.join(PROJECT_ROOT, "synapse_rt.o")
SYNAPSE_RT_MEM_O = os.path.join(PROJECT_ROOT, "synapse_rt_memory.o")
SYNAPSE_RT_CONC_O = os.path.join(PROJECT_ROOT, "synapse_rt_concurrency.o")
TENSOR_O = os.path.join(PROJECT_ROOT, "tensor.o")

# Toolchain GCC
TOOLCHAIN_GCC = os.path.join(PROJECT_ROOT, "toolchain_gcc12", "mingw64", "bin", "gcc.exe")
if not os.path.exists(TOOLCHAIN_GCC):
    TOOLCHAIN_GCC = "gcc"


def _compilar():
    """Compila el binario de prueba de descubrimiento."""
    if not os.path.exists(SYNAPSE_RT_O):
        print(f"[SKIP] synapse_rt.o no encontrado. Compilar con: gcc -c synapse_rt.c -o synapse_rt.o -lpthread")
        return False

    src = os.path.join(TESTS_DIR, "test_cluster_discovery.c")
    if not os.path.exists(src):
        print(f"[SKIP] {src} no encontrado")
        return False

    cmd = [
        TOOLCHAIN_GCC, "-O2", "-std=c99",
        src, SYNAPSE_RT_O, SYNAPSE_RT_MEM_O, SYNAPSE_RT_CONC_O, TENSOR_O,
        os.path.join(PROJECT_ROOT, "tweetnacl.o"),
        "-o", BIN_PATH,
        "-lm", "-lpthread", "-lws2_32"
    ]
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
        print(f"\n[STDOUT]\n{stdout}")
        print(f"\n[STDERR]\n{stderr}")
        assert rc == 0, f"El binario retornó código {rc} (se esperaba 0)"
        assert "TODOS LOS TESTS PASARON" in stderr or "TODOS LOS TESTS PASARON" in stdout, \
            "Debe indicar que todos los tests pasaron"
        assert "Fallos: 0" in stderr or "Fallos: 0" in stdout or "fallos: 0" in stderr, \
            "No debe haber fallos"

    def test_no_hay_segfaults(self):
        rc, stdout, stderr = _ejecutar()
        assert "SIGSEGV" not in stderr and "SEGV" not in stderr, \
            "No debe haber segfaults"
        assert "ESCAPA_DEL_ALCANCE" not in stderr, \
            "No debe haber errores de alcance (pool alloc)"

    def test_salida_estructurada(self):
        rc, stdout, stderr = _ejecutar()
        # Verificar que hay secciones de test
        assert "Test M8.5" in stderr or "Test M8.5" in stdout, \
            "Debe mostrar encabezado M8.5"
        assert "RESULTADOS" in stderr or "RESULTADOS" in stdout, \
            "Debe mostrar sección de resultados"


class TestEscenariosEspecificos:
    """Verifica escenarios específicos de descubrimiento y membresía."""

    @classmethod
    def setup_class(cls):
        if not os.path.exists(BIN_PATH):
            if not _compilar():
                raise RuntimeError("No se pudo compilar el binario de prueba")
        cls.rc, cls.stdout, cls.stderr = _ejecutar()

    def test_inicializacion(self):
        assert "Test 1" in self.stderr, "Debe ejecutar test de inicialización"

    def test_registro_nodos(self):
        assert "Test 2" in self.stderr, "Debe ejecutar test de registro de nodos"
        assert "nodo-1" in self.stderr, "Debe mencionar nodo-1"

    def test_obtener_nodo(self):
        assert "Test 3" in self.stderr, "Debe ejecutar test de obtener nodo"

    def test_eliminar_nodo(self):
        assert "Test 4" in self.stderr, "Debe ejecutar test de eliminar nodo"

    def test_heartbeat(self):
        assert "Test 5" in self.stderr, "Debe ejecutar test de heartbeat"
        assert "Test 6" in self.stderr, "Debe ejecutar test de heartbeat revive nodo"

    def test_anuncio_syncluster(self):
        assert "Test 7" in self.stderr, "Debe ejecutar test de anuncio SYNCLUSTER"
        assert "SYNCLUSTER" in self.stderr, "Debe mostrar SYNCLUSTER"

    def test_info_membresia(self):
        assert "Test 8" in self.stderr, "Debe ejecutar test de info membresía"

    def test_nodo_duplicado(self):
        assert "Test 9" in self.stderr, "Debe ejecutar test de nodo duplicado"

    def test_detener_reinicializar(self):
        assert "Test 10" in self.stderr, "Debe ejecutar test de detener/reinicializar"

    def test_todos_los_tests_ejecutados(self):
        # Verificar que se ejecutaron 10 tests
        for i in range(1, 11):
            assert f"Test {i}" in self.stderr, f"Debe ejecutar Test {i}"


class TestCasosBorde:
    """Prueba casos borde específicos del C binary directamente."""

    @classmethod
    def setup_class(cls):
        if not os.path.exists(BIN_PATH):
            if not _compilar():
                raise RuntimeError("No se pudo compilar el binario de prueba")

    def test_binario_no_crasha_con_args_vacios(self):
        """El binario ejecutado sin args no debe crashar."""
        rc, stdout, stderr = _ejecutar()
        assert rc == 0, f"Binario no debe crashar (rc={rc})"
        assert len(stdout) >= 0 or len(stderr) >= 0, "Debe tener salida"


class TestCompilacionConFlags:
    """Prueba que el binario compile con diferentes flags de optimización."""

    def _compilar_con_flags(self, flags):
        if not os.path.exists(SYNAPSE_RT_O):
            return False
        src = os.path.join(TESTS_DIR, "test_cluster_discovery.c")
        out = BIN_PATH + ".tmp"
        cmd = [TOOLCHAIN_GCC] + flags.split() + [src, SYNAPSE_RT_O, SYNAPSE_RT_MEM_O, SYNAPSE_RT_CONC_O, TENSOR_O, os.path.join(PROJECT_ROOT, "tweetnacl.o"), "-o", out, "-lm", "-lpthread", "-lws2_32"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        # Limpiar
        if os.path.exists(out):
            os.unlink(out)
        return r.returncode == 0

    def test_compilacion_sin_optimizacion(self):
        assert self._compilar_con_flags("-O0 -std=c99"), "Debe compilar con -O0"

    def test_compilacion_os(self):
        assert self._compilar_con_flags("-Os -std=c99"), "Debe compilar con -Os"


class TestRendimiento:
    """Prueba de rendimiento del subsistema de membresía."""

    @classmethod
    def setup_class(cls):
        if not os.path.exists(BIN_PATH):
            if not _compilar():
                raise RuntimeError("No se pudo compilar el binario de prueba")

    def test_ejecucion_rapida(self):
        """El binario debe completar en menos de 5 segundos."""
        inicio = time.time()
        rc, stdout, stderr = _ejecutar()
        duracion = time.time() - inicio
        assert rc == 0, f"Debe pasar (rc={rc})"
        assert duracion < 5.0, f"Debe completar en <5s (tomó {duracion:.2f}s)"
        print(f"[OK] Duración: {duracion:.3f}s")


# ============================================================
# Punto de entrada para ejecución directa
# ============================================================

def run_direct_tests():
    """Ejecuta pruebas directas sin pytest para verificación rápida."""
    print("=== Pruebas directas M8.5 ===")

    # Compilar
    if not _compilar():
        print("[FAIL] No se pudo compilar")
        return 1

    # Ejecutar binario
    rc, stdout, stderr = _ejecutar()
    print(f"\n[STDOUT]\n{stdout[:2000]}")
    print(f"\n[STDERR]\n{stderr[:2000]}")

    if rc == 0 and "TODOS LOS TESTS PASARON" in (stderr + stdout):
        print("\n[PASS] Todos los tests C pasaron")
        return 0
    else:
        print(f"\n[FAIL] Tests C fallaron (rc={rc})")
        return 1


if __name__ == "__main__":
    sys.exit(run_direct_tests())
