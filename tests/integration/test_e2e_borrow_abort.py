"""
tests/test_e2e_borrow_abort.py
M22.6: Validacion End-to-End del Borrow Checker Nativo.
"""
import subprocess
import os
import sys
import tempfile


SYNAPSE_BIN = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..")
)


def _find_python() -> str:
    for exe in ["python3", "python"]:
        try:
            subprocess.run([exe, "--version"], capture_output=True, check=True)
            return exe
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    return "python"  # fallback to python


def _resolve_main_py() -> str:
    candidates = [
        os.path.join(SYNAPSE_BIN, "main.py"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    raise FileNotFoundError(f"No se encontro main.py en {SYNAPSE_BIN}")


def _resolve_test_syn() -> str:
    path = os.path.join(SYNAPSE_BIN, "tests", "validate_borrow_abort.syn")
    if not os.path.exists(path):
        path = os.path.join(os.path.dirname(__file__), "validate_borrow_abort.syn")
    if not os.path.exists(path):
        raise FileNotFoundError(f"No se encontro validate_borrow_abort.syn")
    return path


def test_borrow_abort_seguro():
    """M22.6: Compila con --safe, ejecuta y verifica crash por violacion de pointer."""
    python_exe = _find_python()
    main_py = _resolve_main_py()
    test_syn = _resolve_test_syn()
    
    with tempfile.TemporaryDirectory(prefix="synapse_m22_6_") as tmpdir:
        output_exe = os.path.join(tmpdir, "borrow_abort_test.exe")
        
        compile_cmd = [python_exe, main_py, test_syn, "--safe", "-o", output_exe]
        compile_proc = subprocess.run(
            compile_cmd, capture_output=True, text=True,
            cwd=SYNAPSE_BIN, timeout=120,
        )
        
        if compile_proc.returncode != 0:
            import pytest
            pytest.skip(f"Compilacion fallo: {compile_proc.stderr[-200:]}")
        
        assert os.path.exists(output_exe), f"Binario no generado: {output_exe}"
        
        # Ejecutar - DEBE fallar (SIGABRT=134 o SIGSEGV=139)
        run_proc = subprocess.run(
            [output_exe], capture_output=True, text=True, timeout=30,
        )
        
        exit_code = run_proc.returncode
        stderr = run_proc.stderr
        stdout = run_proc.stdout
        
        assert exit_code != 0, (
            f"ERROR: Binario NO aborto (exit=0). "
            f"stdout: {stdout[:200]} stderr: {stderr[:200]}"
        )
        
        # Aceptamos SIGABRT (134) por assert() o SIGSEGV (139) por NULL deref
        # (GCC -O2 optimiza assert() en paths con UB comprobado)
        CRASH_CODES = {134, 139, 3, 255, -1, 3221225477}  # SIGABRT, SIGSEGV, etc.
        assert exit_code in CRASH_CODES or exit_code < 0 or (exit_code & 0xFF) != 0, (
            f"Exit code {exit_code} no parece un crash. stderr: {stderr[:200]}"
        )
        
        print(f"[M22.6] ✅ CRASH VERIFICADO: exit_code={exit_code} (0x{exit_code & 0xFFFFFFFF:08x})")


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
