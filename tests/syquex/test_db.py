"""
FASE 24 — Test de DB/SQLite (Manual 3 §12.1).

TDD: este test ES la especificación. Si _syn_db_* no existen,
el test C NO compila — eso es correcto.

Manual 3 §12.1: lib/db.syq — Conexión a SQLite
Comando: pytest tests/syquex/test_db.py -v
Criterio: CRUD completo, transacciones, NULL safety
"""
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.syquex

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

BIN_NAME = "test_db.exe"
BIN_ABS = os.path.join(PROJECT_ROOT, "tests", BIN_NAME)
TEST_SRC = os.path.join(PROJECT_ROOT, "tests", "test_db.c")


def _find_gcc():
    gcc_candidate = os.path.join(PROJECT_ROOT, "toolchain_gcc12", "mingw64", "bin", "gcc.exe")
    if os.path.exists(gcc_candidate):
        return gcc_candidate
    for candidate in ("gcc", "gcc.exe"):
        try:
            subprocess.run([candidate, "--version"], capture_output=True)
            return candidate
        except FileNotFoundError:
            continue
    return gcc_candidate


@pytest.fixture(scope="module")
def exe_path():
    """Compila el test C y retorna la ruta al ejecutable."""
    if os.path.exists(BIN_ABS):
        return BIN_ABS

    gcc = _find_gcc()
    sqlite_o = os.path.join(PROJECT_ROOT, "vendor", "sqlite3", "sqlite3.o")
    r = subprocess.run(
        [gcc, "-O2", "-I", PROJECT_ROOT, "-I.", "-o", BIN_ABS, TEST_SRC,
         sqlite_o,
         "-lpthread", "-lws2_32"],
        capture_output=True, text=True, timeout=120
    )
    if r.returncode != 0:
        pytest.fail(
            f"test_db.c NO COMPILA (TDD: falta implementar §12.1).\n"
            f"Error de gcc:\n{r.stderr[-1000:]}"
        )
    assert os.path.exists(BIN_ABS), f"{BIN_NAME} no se creó"
    return BIN_ABS


def _run(exe_path):
    """Ejecuta el test C y retorna (returncode, stdout, stderr)."""
    r = subprocess.run(
        [exe_path], capture_output=True, cwd=PROJECT_ROOT,
        timeout=30, encoding="utf-8", errors="replace"
    )
    return r.returncode, r.stdout, r.stderr


class TestDbOpenClose:
    """§12.1 — Apertura / Cierre."""

    def test_abrir(self, exe_path):
        rc, out, err = _run(exe_path)
        assert rc == 0, f"test_db falló:\n{out}\n{err}"
        assert "abrir retorna conn >= 0" in out

    def test_cerrar(self, exe_path):
        rc, out, err = _run(exe_path)
        assert "cerrar no crashea" in out


class TestDbCrud:
    """§12.1 — INSERT / SELECT / UPDATE / DELETE."""

    def test_create_table(self, exe_path):
        rc, out, err = _run(exe_path)
        assert rc == 0, f"test_db falló:\n{out}\n{err}"
        assert "CREATE TABLE rc=0" in out

    def test_insert(self, exe_path):
        rc, out, err = _run(exe_path)
        assert "INSERT rc=0" in out
        assert "ultima_id == 1" in out

    def test_select(self, exe_path):
        rc, out, err = _run(exe_path)
        assert "fila 1 nombre == 'Ana'" in out
        assert "fila 2 nombre == 'Bob'" in out
        assert "fin de resultados" in out

    def test_update(self, exe_path):
        rc, out, err = _run(exe_path)
        assert "UPDATE rc=0" in out
        assert "cambios_fila == 1 tras UPDATE" in out

    def test_delete(self, exe_path):
        rc, out, err = _run(exe_path)
        assert "DELETE rc=0" in out


class TestDbNull:
    """§12.1 — NULL handling."""

    def test_null_detectado(self, exe_path):
        rc, out, err = _run(exe_path)
        assert "nombre NULL detectado" in out


class TestDbTransacciones:
    """§12.1 — BEGIN / COMMIT / ROLLBACK."""

    def test_rollback(self, exe_path):
        rc, out, err = _run(exe_path)
        assert "ROLLBACK rc=0" in out
        assert "tras ROLLBACK: 0 filas" in out

    def test_commit(self, exe_path):
        rc, out, err = _run(exe_path)
        assert "COMMIT rc=0" in out
        assert "tras COMMIT: 1 fila" in out


class TestDbError:
    """§12.1 — Errores."""

    def test_sql_invalido(self, exe_path):
        rc, out, err = _run(exe_path)
        assert "SQL inválido rc != 0" in out
        assert "ultimo_error no vacío" in out


class TestDbIntegracion:
    """Tests de integración completos del módulo db."""

    def test_todos_los_tests_c_pasan(self, exe_path):
        rc, out, err = _run(exe_path)
        assert rc == 0, f"test_db falló (rc={rc}):\n{out}\n{err}"
        assert "RESULTADO" in out, f"Sin resultados en stdout:\n{out}"
        assert "[FAIL]" not in out, f"Hay FAILs en output C:\n{out}"
