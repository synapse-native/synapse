"""
tests/integration/test_verificacion_aot_e2e.py - E2E de Fase 32.5.

cumple Manual 7 §4.2: valida el código generado con el compilador real antes
de ejecutar los casos límite.
cumple Manual 7 §6.3: bucle de validación/corrección con auto-refutación.

El módulo opensyn/verificacion_aot.syn invoca el comando `synapse` mediante
_syn_capturar_comando_timeout. Para el oráculo se compila un wrapper mínimo
`synapse.exe` que traduce:
  synapse check --no-emit <archivo>  -> main.py <archivo> --check --no-emit
  synapse <archivo> -o <exe>         -> main.py <archivo> -o <exe>
"""
import os
import subprocess

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PYTHON = os.path.join(RAIZ, ".venv", "Scripts", "python.exe")
MAIN = os.path.join(RAIZ, "main.py")
GCC = os.path.join(RAIZ, "toolchain_gcc12", "mingw64", "bin", "gcc.exe")

WRAPPER_C = r"""
#include <windows.h>
#include <stdio.h>
#include <string.h>

int main(int argc, char** argv) {
    char cmd[8192];
    int n;
    int es_check = (argc > 1 && strcmp(argv[1], "check") == 0);
    if (es_check) {
        n = snprintf(cmd, sizeof(cmd), "\"%s\" \"%s\" \"%s\" --check --no-emit",
                     PYTHON_PATH, MAIN_PATH, argv[argc - 1]);
    } else {
        n = snprintf(cmd, sizeof(cmd), "\"%s\" \"%s\"", PYTHON_PATH, MAIN_PATH);
        for (int i = 1; i < argc && n > 0 && n < (int)sizeof(cmd); i++) {
            n += snprintf(cmd + n, sizeof(cmd) - (size_t)n, " \"%s\"", argv[i]);
        }
    }
    if (n <= 0 || n >= (int)sizeof(cmd)) return 127;

    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    memset(&si, 0, sizeof(si));
    memset(&pi, 0, sizeof(pi));
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESTDHANDLES;
    si.hStdOutput = GetStdHandle(STD_OUTPUT_HANDLE);
    si.hStdError = GetStdHandle(STD_ERROR_HANDLE);
    si.hStdInput = GetStdHandle(STD_INPUT_HANDLE);
    if (!CreateProcessA(NULL, cmd, NULL, NULL, TRUE, CREATE_NO_WINDOW,
                        NULL, NULL, &si, &pi)) {
        return 127;
    }
    WaitForSingleObject(pi.hProcess, INFINITE);
    DWORD rc = 127;
    GetExitCodeProcess(pi.hProcess, &rc);
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    return (int)rc;
}
"""


def _c_path(ruta):
    return ruta.replace("\\", "/")


def _preparar_wrapper(tmp_path):
    if not os.path.isfile(GCC):
        pytest.skip("toolchain gcc no disponible para el wrapper synapse")
    fuente = tmp_path / "synapse_wrapper.c"
    codigo = WRAPPER_C.replace("PYTHON_PATH", '"' + _c_path(PYTHON) + '"').replace(
        "MAIN_PATH", '"' + _c_path(MAIN) + '"'
    )
    fuente.write_text(codigo, encoding="utf-8")
    subprocess.run(
        [GCC, "-O2", str(fuente), "-o", str(tmp_path / "synapse.exe")],
        check=True,
        capture_output=True,
        timeout=120,
    )


def _compilar_y_ejecutar(tmp_path, nombre, fuente):
    archivo = tmp_path / f"{nombre}.syn"
    archivo.write_text(fuente, encoding="utf-8")
    exe = tmp_path / f"{nombre}.exe"
    compilacion = subprocess.run(
        [PYTHON, MAIN, str(archivo), "-o", str(exe)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert compilacion.returncode == 0, compilacion.stdout + compilacion.stderr
    entorno = os.environ.copy()
    entorno["PATH"] = str(tmp_path) + os.pathsep + entorno.get("PATH", "")
    ejecucion = subprocess.run(
        [str(exe)],
        cwd=str(tmp_path),
        env=entorno,
        capture_output=True,
        text=True,
        timeout=300,
    )
    return ejecucion


CODIGO_VALIDO = (
    "#lang: es\\n"
    "funcion suma(a: entero, b: entero) -> entero:\\n"
    "    requiere:\\n"
    "        a >= 0\\n"
    "    garantiza:\\n"
    "        _resultado_ >= 0\\n"
    "    retornar a + b\\n"
)

PROBE_VALIDO = """#lang: es
importar std.io
importar opensyn.verificacion_aot
funcion principal() -> entero:
    let codigo = "%s"
    let casos = generar_casos_limite(codigo)
    let fallos = 0
    let total = 0
    para caso en casos:
        let resultado = verificar_caso_limite(codigo, caso)
        total = total + 1
        si no aot_resultado_valido(resultado, caso.valor_esperado):
            fallos = fallos + 1
    escribir_linea("casos=" + entero_a_texto(total) + " fallos=" + entero_a_texto(fallos))
    let r = verificar_codigo_generado(codigo, "memoria.syn")
    coincidir r:
        ok(_) => escribir_linea("VERIF=ok")
        err(_) => escribir_linea("VERIF=err")
    retornar 0
""" % CODIGO_VALIDO

PROBE_INVALIDO = """#lang: es
importar std.io
importar opensyn.verificacion_aot
funcion principal() -> entero:
    let codigo = "#lang: es\\nfuncion rota( -> entero:\\n    retornar 0\\n"
    si validar_con_compilador(codigo):
        escribir_linea("CHECK=ok")
    sino:
        escribir_linea("CHECK=error")
    let r = verificar_codigo_generado(codigo, "roto.syn")
    coincidir r:
        ok(_) => escribir_linea("VERIF=ok")
        err(_) => escribir_linea("VERIF=err")
    retornar 0
"""


def test_aot_codigo_valido_compila_y_ejecuta_casos(tmp_path):
    _preparar_wrapper(tmp_path)
    ejecucion = _compilar_y_ejecutar(tmp_path, "probe_valido", PROBE_VALIDO)
    assert ejecucion.returncode == 0, ejecucion.stdout + ejecucion.stderr
    assert "casos=5 fallos=0" in ejecucion.stdout
    assert "VERIF=ok" in ejecucion.stdout
    assert not list(tmp_path.glob("opensyn_aot_*.syn"))
    assert not list(tmp_path.glob("opensyn_aot_*.exe"))
    assert not list(tmp_path.glob("opensyn_aot_check_*.syn"))


def test_aot_codigo_invalido_no_ejecuta_casos(tmp_path):
    _preparar_wrapper(tmp_path)
    ejecucion = _compilar_y_ejecutar(tmp_path, "probe_invalido", PROBE_INVALIDO)
    assert ejecucion.returncode == 0, ejecucion.stdout + ejecucion.stderr
    assert "CHECK=error" in ejecucion.stdout
    assert "VERIF=err" in ejecucion.stdout
    assert not list(tmp_path.glob("opensyn_aot_*.syn"))
    assert not list(tmp_path.glob("opensyn_aot_check_*.syn"))
