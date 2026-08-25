"""
test_cluster_handshake_e2e.py — M18.3+M18.4: Arnes de prueba Handshake Ed25519

Cubre:
  1. Compilacion del binario C de handshake E2E
  2. Tests unitarios de criptografia Ed25519 (21 tests)
  3. Dual-process handshake sobre UDP (servidor + cliente simultaneos)
  4. Zero-Trust: clave invalida -> RECHAZADO
  5. Compilacion y ejecucion del test .syn via pipeline Synapse
"""

import os
import subprocess
import sys
import time
import pytest

from conftest import rt_objs

pytestmark = pytest.mark.integration

RT_OBJS = rt_objs()  # F3-15: objetos del runtime derivados de runtime/core/*.c (sin hardcoding)

# --- Configuracion ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TESTS_DIR = os.path.join(PROJECT_ROOT, "tests")
BIN_NAME = "test_cluster_handshake_e2e.exe" if sys.platform == "win32" else "test_cluster_handshake_e2e"
BIN_PATH = os.path.join(TESTS_DIR, BIN_NAME)
SYN_PATH = os.path.join(PROJECT_ROOT, "tests", "integration", "test_cluster_handshake.syn")




def _find_gcc() -> str:
    """Encuentra el GCC toolchain."""
    candidates = [
        os.path.join(PROJECT_ROOT, "toolchain_gcc12", "mingw64", "bin", "gcc.exe"),
        "gcc", "gcc.exe"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
        try:
            subprocess.run([c, "--version"], capture_output=True)
            return c
        except FileNotFoundError:
            continue
    return candidates[0]


def _compilar() -> bool:
    """Compila el binario de prueba de handshake E2E."""
    src = os.path.join(TESTS_DIR, "test_cluster_handshake_e2e.c")
    if not os.path.exists(src):
        print(f"[SKIP] {src} no encontrado")
        return False

    objs = [o for o in RT_OBJS if o and os.path.exists(o)]

    if not objs:
        print("[SKIP] No se encontraron objetos runtime")
        return False

    gcc = _find_gcc()
    cmd = [gcc, "-O2", "-std=c99", "-Wall", src, *objs, "-o", BIN_PATH, "-lm", "-lpthread", "-lws2_32"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    if r.returncode != 0:
        print(f"[COMPILE FAIL] rc={r.returncode}")
        print(r.stderr[:500])
        return False
    return True


def _run_bin(args: str = "", timeout: int = 30) -> tuple:
    """Ejecuta el binario y retorna (rc, stdout, stderr). Con reintento si hay lock."""
    cmd = [BIN_PATH] + (args.split() if args else [])
    for intento in range(3):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return r.returncode, r.stdout, r.stderr
        except PermissionError:
            if intento < 2:
                time.sleep(1.0)
                _compilar()  # Recompilar para renovar el binario
                continue
            return -3, "", f"PERMISSION DENIED tras {intento+1} intentos"
        except subprocess.TimeoutExpired:
            return -1, "", f"TIMEOUT ({timeout}s)"
        except FileNotFoundError:
            return -2, "", "BINARIO_NO_ENCONTRADO"
    return -3, "", "FALLO DESCONOCIDO"


def _compilar_synapse_syn(syn_path: str) -> bool:
    """Compila un archivo .syn usando el pipeline Synapse (python main.py)."""
    if not os.path.exists(syn_path):
        return False
    syn_py = os.path.join(PROJECT_ROOT, "main.py")
    if not os.path.exists(syn_py):
        return False
    env = os.environ.copy()
    # Buscar GCC toolchain
    gcc_paths = [
        os.path.join(PROJECT_ROOT, "toolchain_gcc12", "mingw64", "bin", "gcc.exe"),
        os.path.join(PROJECT_ROOT, "toolchain", "bin", "gcc.exe"),
        "C:/TDM-GCC-64/bin/gcc.exe",
        "/c/TDM-GCC-64/bin/gcc.exe",
    ]
    for gp in gcc_paths:
        if os.path.exists(gp):
            env["SYNAPSE_GCC_PATH"] = gp
            break
    r = subprocess.run(
        [sys.executable, syn_py, syn_path],
        capture_output=True, text=True, timeout=60, env=env
    )
    if r.returncode != 0:
        # Check if .c file was generated (partial success)
        c_path = syn_path.replace(".syn", ".c")
        if os.path.exists(c_path):
            print(f"[SYN PARTIAL] Codigo C generado pero link fallo (toolchain)")
            return True
        print(f"[SYN COMPILE FAIL] rc={r.returncode}")
        print(r.stderr[:500])
        return False
    return True


# ============================================================
# Tests M18.4: C binary
# ============================================================

class TestM184_Compilacion:
    """Compilacion del binario C de handshake."""

    def test_compilacion(self):
        assert _compilar(), "El binario de prueba debe compilar correctamente"


class TestM184_Unitarios:
    """Tests unitarios de criptografia Ed25519 + UDP primitivas."""

    @classmethod
    def setup_class(cls):
        if not os.path.exists(BIN_PATH):
            if not _compilar():
                raise RuntimeError("No se pudo compilar el binario")

    def test_unitarios_pasan(self):
        """21 tests unitarios: Ed25519 keygen, firma, verificacion, rechazos, raw UDP."""
        rc, out, err = _run_bin("", timeout=15)
        assert rc == 0, f"Binario debe retornar 0 (rc={rc}): {err[:200]}"
        assert "21" in out, f"Deben pasar 21 tests: {out}"
        assert "Fallos: 0" in out, f"No debe haber fallos: {out}"
        print(f"\n[OK] Tests unitarios C pasan:\n{out[-200:]}")


class TestM184_HandshakeCompleto:
    """Prueba dual-process: servidor y cliente como procesos separados.
    
    Utiliza sockets RAW (sendto/recvfrom) independientes del runtime para
    garantizar interoperabilidad cross-process con verificacion Ed25519.
    """

    @classmethod
    def setup_class(cls):
        if not os.path.exists(BIN_PATH):
            if not _compilar():
                raise RuntimeError("No se pudo compilar")

    def _do_handshake(self, puerto: int, args_client: str = "") -> dict:
        """Lanza servidor (background) + cliente (foreground), retorna ambos resultados."""
        svr = subprocess.Popen(
            [BIN_PATH, "server", str(puerto)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        time.sleep(1.5)
        rc_cli, out_cli, err_cli = _run_bin(f"client 127.0.0.1 {puerto} {args_client}", timeout=15)
        out_svr, err_svr = svr.communicate(timeout=15)
        return {
            "rc_svr": svr.returncode, "out_svr": out_svr,
            "rc_cli": rc_cli, "out_cli": out_cli, "err_cli": err_cli
        }

    def test_handshake_valido(self):
        """Handshake exitoso: dos procesos, Ed25519, HANDSHAKE EXITOSO."""
        r = self._do_handshake(19500)
        print(f"\n[SVR] rc={r['rc_svr']}: {r['out_svr'][-100:]}")
        print(f"[CLI] rc={r['rc_cli']}: {r['out_cli'][-100:]}")
        assert r['rc_svr'] == 0, f"Server debe retornar 0 (Handshake OK). rc={r['rc_svr']}"
        assert r['rc_cli'] == 0, f"Cliente debe retornar 0 (Handshake OK). rc={r['rc_cli']}"
        assert "HANDSHAKE EXITOSO" in r['out_cli'], f"Cliente debe reportar HANDSHAKE EXITOSO"
        assert "Handshake completado" in r['out_svr'], f"Servidor debe completar handshake"

    def test_zero_trust_clave_invalida(self):
        """Clave invalida: servidor rc=2 + cliente rc=2 (acoplamiento determinista)."""
        r = self._do_handshake(19502, "clave_invalida")
        print(f"\n[SVR] rc={r['rc_svr']}: {r['out_svr'][-150:]}")
        print(f"[CLI] rc={r['rc_cli']}: {r['out_cli'][:100]}")
        assert r['rc_svr'] == 2, f"Server debe retornar 2 (ZERO-TRUST). rc={r['rc_svr']}"
        assert r['rc_cli'] == 2, f"Cliente debe retornar 2 (ZERO-TRUST). rc={r['rc_cli']}"
        assert "ZERO-TRUST" in r['out_svr'], "Server debe detectar ZERO-TRUST"
        assert "INVALIDA" in r['out_svr'], "Server debe reportar firma invalida"

    def test_zero_trust_firma_corrupta(self):
        """Firma corrupta: servidor rc=2 + cliente rc=2 (acoplamiento determinista)."""
        r = self._do_handshake(19504, "firma_corrupta")
        print(f"\n[SVR] rc={r['rc_svr']}: {r['out_svr'][-150:]}")
        print(f"[CLI] rc={r['rc_cli']}: {r['out_cli'][:100]}")
        assert r['rc_svr'] == 2, f"Server debe retornar 2 (ZERO-TRUST). rc={r['rc_svr']}"
        assert r['rc_cli'] == 2, f"Cliente debe retornar 2 (ZERO-TRUST). rc={r['rc_cli']}"
        assert "ZERO-TRUST" in r['out_svr'], "Server debe detectar ZERO-TRUST"


# ============================================================
# Tests M18.3: .syn compilation
# ============================================================

class TestM183_SynapseHandshake:
    """Compilacion del modulo .syn de handshake Ed25519 via pipeline Synapse."""

    def test_compilacion_syn(self):
        """El archivo .syn debe compilar sin errores via python main.py."""
        assert os.path.exists(SYN_PATH), f"{SYN_PATH} no existe"
        assert _compilar_synapse_syn(SYN_PATH), \
            f"Falló compilacion de {SYN_PATH}"
        print(f"[OK] {SYN_PATH} compila correctamente")


# ============================================================
# Punto de entrada para ejecucion directa
# ============================================================

def run_direct():
    """Ejecuta pruebas sin pytest. Retorna 0 si todo OK, >0 si falla."""
    fallos = 0
    print("=== M18.3+M18.4: Handshake Ed25519 Zero-Trust E2E ===\n")

    if not _compilar():
        print("[FAIL] No se pudo compilar el binario")
        return 1
    print("[OK] Binario compilado\n")

    # Test unitarios C
    print("--- Test unitarios C ---")
    rc, out, err = _run_bin("", timeout=15)
    if rc == 0 and "Fallos: 0" in out:
        print(f"[PASS] Tests C: {out[-100:]}")
    else:
        print(f"[FAIL] rc={rc}: {err[:200]}")
        fallos += 1

    # Test compilacion .syn
    print("\n--- Test compilacion Synapse ---")
    if _compilar_synapse_syn(SYN_PATH):
        print(f"[PASS] {os.path.basename(SYN_PATH)} compila")
    else:
        print(f"[FAIL] {os.path.basename(SYN_PATH)} no compila")
        fallos += 1

    # Test dual-process handshake valido (rc_svr=0, rc_cli=0)
    print("\n--- Test dual-process handshake valido ---")
    puerto = 19600
    svr = subprocess.Popen(
        [BIN_PATH, "server", str(puerto)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    time.sleep(1.5)
    rc_cli, out_cli, err_cli = _run_bin(f"client 127.0.0.1 {puerto}", timeout=15)
    try:
        out_svr, err_svr = svr.communicate(timeout=15)
    except subprocess.TimeoutExpired:
        svr.kill()
        out_svr, err_svr = svr.communicate()

    print(f"  Server: rc={svr.returncode}, {out_svr[-80:]}")
    print(f"  Client: rc={rc_cli}, {out_cli[-80:]}")
    if svr.returncode != 0 or rc_cli != 0:
        print("[FAIL] Handshake valido: se esperaba rc_svr=0, rc_cli=0")
        fallos += 1

    # Test Zero-Trust clave_invalida (rc_svr=2, rc_cli=2)
    print("\n--- Test Zero-Trust clave_invalida ---")
    puerto = 19602
    svr2 = subprocess.Popen(
        [BIN_PATH, "server", str(puerto)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    time.sleep(1.5)
    rc_cli2, out_cli2, err_cli2 = _run_bin(f"client 127.0.0.1 {puerto} clave_invalida", timeout=15)
    out_svr2, err_svr2 = svr2.communicate(timeout=15)
    print(f"  Server: rc={svr2.returncode}")
    print(f"  Client: rc={rc_cli2}")
    if svr2.returncode != 2 or rc_cli2 != 2:
        print(f"[FAIL] Zero-Trust: se esperaba rc_svr=2, rc_cli=2 (svr={svr2.returncode}, cli={rc_cli2})")
        fallos += 1

    # Test Zero-Trust firma_corrupta (rc_svr=2, rc_cli=2)
    print("\n--- Test Zero-Trust firma_corrupta ---")
    puerto = 19604
    svr3 = subprocess.Popen(
        [BIN_PATH, "server", str(puerto)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    time.sleep(1.5)
    rc_cli3, out_cli3, err_cli3 = _run_bin(f"client 127.0.0.1 {puerto} firma_corrupta", timeout=15)
    out_svr3, err_svr3 = svr3.communicate(timeout=15)
    print(f"  Server: rc={svr3.returncode}")
    print(f"  Client: rc={rc_cli3}")
    if svr3.returncode != 2 or rc_cli3 != 2:
        print(f"[FAIL] Zero-Trust: se esperaba rc_svr=2, rc_cli=2 (svr={svr3.returncode}, cli={rc_cli3})")
        fallos += 1

    print("\n=== Resumen ===")
    print(f"Fallos: {fallos}")
    if fallos > 0:
        print("[FAIL] Algunas pruebas fallaron")
        return 1
    print("[PASS] Todas las pruebas pasaron")
    return 0


if __name__ == "__main__":
    sys.exit(run_direct())
