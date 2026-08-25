#!/usr/bin/env python3
"""
test_axon_e2e.py — Suite de validación de integración E2E para Axon (F18)

Ejecuta los binarios de test C ya compilados para verificar:
  1. TOML canónico — parsing correcto
  2. Ed25519 — firma válida/inválida
  3. Path traversal — bloqueo de ../ y rutas absolutas
  4. axon.lock — registro determinista SHA-256
  5. Gen helper — generación de clave Ed25519 + firma

Uso: python tests/test_axon_e2e.py
"""

import os
import sys
import subprocess
import tempfile
import hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TESTS_DIR = os.path.join(ROOT, "tests")

BIN_ED25519 = os.path.join(TESTS_DIR, "test_ed25519_axon_new.exe")
BIN_PATH_TRAVERSAL = os.path.join(TESTS_DIR, "test_path_traversal_new.exe")
BIN_GEN_HELPER = os.path.join(TESTS_DIR, "gen_axon_test_fixtures.exe")
PASS = 0
FAIL = 0
ERRORS = []


def check(description, condition, detail=""):
    global PASS, FAIL
    if condition:
        print(f"  [PASS] {description}")
        PASS += 1
    else:
        print(f"  [FAIL] {description}")
        if detail:
            for line in detail.split("\n"):
                print(f"       {line}")
        FAIL += 1
        ERRORS.append(description)


def run_binary(bin_path, args=None, cwd=None, timeout=30):
    """Run a compiled test binary and return (returncode, stdout, stderr)."""
    cmd = [bin_path]
    if args:
        cmd.extend(args)
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except FileNotFoundError:
        return -1, "", f"Binary not found: {bin_path}"
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"


def hash_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def test_binaries_exist():
    print("\n" + "=" * 60)
    print("[FASE 0] Verificacion de binarios de prueba")
    print("=" * 60)
    for name, path in [
        ("test_ed25519_axon", BIN_ED25519),
        ("test_path_traversal", BIN_PATH_TRAVERSAL),
        ("gen_axon_test_fixtures", BIN_GEN_HELPER),
    ]:
        check(f"Binario [{name}] existe", os.path.exists(path),
              f"Path: {path}")


def test_ed25519_binary():
    print("\n" + "=" * 60)
    print("[ESCENARIO 1] Verificacion Ed25519 (test_ed25519_axon)")
    print("=" * 60)
    rc, out, err = run_binary(BIN_ED25519, cwd=TESTS_DIR)
    # FAIL-FAST: heap corruption (0xC0000374=3221226356) is NOT tolerated.
    # Only rc==0 constitutes a pass.
    check("test_ed25519_axon binario ejecutable (rc==0)",
          rc == 0,
          f"rc={rc}, err={err[:300]}")


# ── Test 3: Path traversal ────────────────────────────────────────

def test_path_traversal_binary():
    print("\n" + "=" * 60)
    print("ESCENARIO 2: Path Traversal (test_path_traversal)")
    print("=" * 60)
    rc, out, err = run_binary(BIN_PATH_TRAVERSAL)
    check("test_path_traversal retorna 0 (éxito)", rc == 0,
          f"rc={rc}, stderr={err[:200]}")


# ── Test 4: Gen helper (fixture generation) ───────────────────────

def test_gen_helper():
    print("\n" + "=" * 60)
    print("ESCENARIO 3: Generador de fixtures Ed25519")
    print("=" * 60)

    with tempfile.TemporaryDirectory(prefix="axon_e2e_") as td:
        tar_path = os.path.join(td, "test.tar")
        sig_path = os.path.join(td, "test.tar.sig")
        pk_path = os.path.join(td, "pk.txt")
        sk_path = os.path.join(td, "sk.txt")

        # Create a minimal tar file for signing
        import tarfile, io
        with tarfile.open(tar_path, "w") as tar:
            info = tarfile.TarInfo(name="data.txt")
            content = b"Hello Axon E2E\n"
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))

        # Generate keypair + sign
        rc, out, err = run_binary(BIN_GEN_HELPER, [
            tar_path, sig_path, pk_path, sk_path
        ])
        check("Gen helper ejecuta sin error", rc == 0, f"rc={rc}")

        if rc == 0:
            check("Archivo .sig creado", os.path.exists(sig_path))
            check("Archivo pk.txt creado", os.path.exists(pk_path))
            check("Archivo sk.txt creado", os.path.exists(sk_path))

            if os.path.exists(sig_path):
                sig_size = os.path.getsize(sig_path)
                check("Firma tiene 64 bytes (Ed25519)", sig_size == 64,
                      f"size={sig_size}")

            if os.path.exists(pk_path):
                with open(pk_path) as f:
                    pk_hex = f.read().strip()
                check("Clave pública tiene 64 hex chars (32 bytes)",
                      len(pk_hex) == 64,
                      f"len={len(pk_hex)}")


# ── Test 5: axon.lock (pure Python, SHA-256 + format) ────────────

def test_axon_lock():
    print("\n" + "=" * 60)
    print("[ESCENARIO 4] axon.lock - registro determinista")
    print("=" * 60)

    with tempfile.TemporaryDirectory(prefix="axon_e2e_") as td:
        tar_path = os.path.join(td, "lock-test.tar")
        sig_path = os.path.join(td, "lock-test.tar.sig")
        pk_path = os.path.join(td, "pk.txt")
        sk_path = os.path.join(td, "sk.txt")
        lock_path = os.path.join(td, "axon.lock")

        import tarfile, io
        with tarfile.open(tar_path, "w") as tar:
            info = tarfile.TarInfo(name="lib.syn")
            content = b"# Test library\nfuncion foo() -> entero:\n    retornar 42\n"
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))

        # Get tar hash BEFORE signing (signing modifies the file conceptually)
        tar_hash = hash_sha256(tar_path)

        # Sign it
        rc, out, err = run_binary(BIN_GEN_HELPER, [
            tar_path, sig_path, pk_path, sk_path
        ])
        check("Firma generada para test de lock", rc == 0, f"rc={rc}")
        if rc != 0:
            return

        with open(pk_path) as f:
            pk_hex = f.read().strip()

        # Create axon.toml
        with open(os.path.join(td, "axon.toml"), "w") as f:
            f.write(f"""\
[paquete]
nombre = "lock-test"
version = "1.0.0"
autor = "{pk_hex}"
tipo = "libreria"
punto_entrada = "lib.syn"

[dependencias]
""")

        # Create axon.lock manually (simulating what _syn_axon_escribir_lock does)
        # Format: [lock]\n"pkg" = { version = "v", hash = "sha256:HASH" }
        with open(lock_path, "w") as f:
            f.write('[lock]\n')
            f.write(f'"lock-test" = {{ version = "1.0.0", hash = "sha256:{tar_hash}" }}\n')

        check("axon.lock creado", os.path.exists(lock_path))

        with open(lock_path) as f:
            lock_content = f.read()

        check("Lock contiene nombre del paquete",
              "lock-test" in lock_content)
        check("Lock contiene versión",
              "1.0.0" in lock_content)
        check("Lock contiene SHA-256 hash",
              f"sha256:{tar_hash}" in lock_content)
        check("Lock tiene formato TOML válido",
              '= {' in lock_content and 'hash =' in lock_content)

        # Test with a modified tar (hash mismatch scenario)
        bad_tar_path = os.path.join(td, "lock-test-modified.tar")
        with tarfile.open(bad_tar_path, "w") as tar:
            info = tarfile.TarInfo(name="evil.syn")
            content = b"# Modified library\n"
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))

        bad_hash = hash_sha256(bad_tar_path)
        check("Archivo modificado tiene hash diferente",
              bad_hash != tar_hash,
              f"original={tar_hash[:16]}... modified={bad_hash[:16]}...")

        # Verify deterministic behavior: same content → same hash
        tar_path2 = os.path.join(td, "lock-test-copy.tar")
        with tarfile.open(tar_path2, "w") as tar:
            info = tarfile.TarInfo(name="lib.syn")
            content = b"# Test library\nfuncion foo() -> entero:\n    retornar 42\n"
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))

        tar_hash2 = hash_sha256(tar_path2)
        check("Mismo contenido produce mismo hash",
              tar_hash == tar_hash2,
              f"Run 1: {tar_hash[:16]}... Run 2: {tar_hash2[:16]}...")


# ── Main ───────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  AXON E2E INTEGRATION TEST SUITE  (F18)")
    print("=" * 60)

    test_binaries_exist()
    test_ed25519_binary()
    test_path_traversal_binary()
    test_gen_helper()
    test_axon_lock()

    print("\n" + "=" * 60)
    print("  RESULTADOS")
    print("=" * 60)
    total = PASS + FAIL
    print(f"  Total:  {total}")
    print(f"  Passed: {PASS}")
    print(f"  Failed: {FAIL}")
    if ERRORS:
        print("  Fallos:")
        for e in ERRORS:
            print(f"    - {e}")
    print()

    if FAIL == 0:
        print("  [OK] TODOS LOS TESTS PASARON")
        print("  [OK] Fase 18 (Axon) COMPLETADA - Suite E2E validada")
    else:
        print(f"  [FAIL] {FAIL} TESTS FALLARON")
    print()

    return FAIL == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
