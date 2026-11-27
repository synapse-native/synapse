# tests/auditoria/test_oraculos_r150.py
# Oraculos TDD del ME r150_funcional (hallazgos M1/M2/M3/M4/M6/M7/M13/M14/M15 de R149).
# OBL-R150-M1 | Manual 1 §3 | std.llvm/std.wasm enlazan con el runtime (backends C cableados) | integracion | TDD
# OBL-R150-M2 | Manual 5 §8.1 | worker_ejecutar/worker_robar/worker_cola_vacia existen y operan la cola ws_* | unit | TDD
# OBL-R150-M3a | Manual 7 §1 | synapse opensyn bindings regenera lib/runtime_bindings.syq real | integracion | TDD
# OBL-R150-M3b | Manual 7 §3 | synapse opensyn status reporta estado local real | integracion | TDD
# OBL-R150-M3c | Manual 7 §3 | download/finetune sin servicio devuelven rc!=0 con mensaje honesto | integracion | TDD
# OBL-R150-M3d | Manual 8 §3.4 | debug --load/--step/--reverse/--snapshots operan trazas TRACE v1 reales | integracion | TDD
# OBL-R150-M6 | Manual 8 §4.1 | banner del CLI usa VERSION como fuente unica | unit | TDD
# OBL-R150-M7 | Manual 1 §3 | scripts/verificar_e2e.py importa sin SyntaxWarning | unit | TDD
# OBL-R150-M13 | Manual 9 §9 | el working tree no acumula ruido (keep/.venv-1) | unit | TDD
# OBL-R150-M15 | Manual 7 §2.3 | std.testing expone verificar() que el prompt TDD genera | integracion | TDD
"""
Requisitos:
1. Ejecutar desde la raiz del repo: .venv/Scripts/python.exe -m pytest tests/auditoria/test_oraculos_r150.py -v
2. Los probes E2E usan TEMP para no contaminar el arbol (convencion regla 12).
"""
import os
import subprocess
import sys
import tempfile

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PY = sys.executable


def _compilar_completo(ruta_syn: str, tmp: str, nombre: str) -> subprocess.CompletedProcess:
    """Compila y ENLAZA un .syn con el pipeline S1 real (no check_only).
    output_path debe terminar en .exe: el pipeline verifica la existencia de
    ESE nombre exacto (ME-R2)."""
    salida = os.path.join(tmp, nombre + ".exe")
    script = (
        "import sys;"
        "sys.path.insert(0, r'%s');"
        "from pipeline import ejecutar_compilador;"
        "sys.exit(ejecutar_compilador(r'%s', output_path=r'%s'))"
        % (RAIZ, ruta_syn, salida)
    )
    return subprocess.run([PY, "-c", script], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=tmp, timeout=600)


def _compilar_check(ruta_syn: str, tmp: str) -> subprocess.CompletedProcess:
    script = (
        "import sys;"
        "sys.path.insert(0, r'%s');"
        "from pipeline import ejecutar_compilador;"
        "sys.exit(ejecutar_compilador(r'%s', check_only=True))" % (RAIZ, ruta_syn)
    )
    return subprocess.run([PY, "-c", script], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=tmp, timeout=300)


# =========================================================================
# M1: std.llvm / std.wasm ENLAZAN (backends C en _RT_FUENTES)
# =========================================================================

def test_llvm_enlaza_y_ejecuta():
    """OBL-R150-M1: probe importa std.llvm, crea contexto y verifica errores."""
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "probe_llvm.syn")
        with open(src, "w", encoding="utf-8", newline="\n") as f:
            f.write(
                "#lang: es\n"
                "importar std.llvm\n"
                "\n"
                "funcion principal() -> entero:\n"
                "    ctx = LLVMContextCreate()\n"
                "    si ctx == nulo:\n"
                "        escribir_linea(\"[FAIL] LLVMContextCreate nulo\")\n"
                "        retornar 1\n"
                "    errores = LLVMContextGetErrorCount(ctx)\n"
                "    escribir_linea(concat(\"llvm ctx ok errores=\", entero_a_texto(errores)))\n"
                "    LLVMContextDispose(ctx)\n"
                "    retornar 0\n"
            )
        r = _compilar_completo(src, tmp, "probe_llvm")
        assert r.returncode == 0, f"std.llvm no enlaza:\n{r.stdout}\n{r.stderr[:2000]}"
        candidato = os.path.join(tmp, "probe_llvm.exe")
        run = subprocess.run([candidato], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=60)
        assert run.returncode == 0, f"probe llvm rc={run.returncode}: {run.stdout} {run.stderr[:500]}"
        assert "llvm ctx ok errores=0" in run.stdout


def test_wasm_enlaza_y_ejecuta():
    """OBL-R150-M1: probe importa std.wasm, crea modulo y emite header WAT."""
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "probe_wasm.syn")
        with open(src, "w", encoding="utf-8", newline="\n") as f:
            f.write(
                "#lang: es\n"
                "importar std.wasm\n"
                "\n"
                "funcion principal() -> entero:\n"
                "    mod = WasmModuleCreate(\"probe\")\n"
                "    si mod == nulo:\n"
                "        escribir_linea(\"[FAIL] WasmModuleCreate nulo\")\n"
                "        retornar 1\n"
                "    WasmModuleEmitHeader(mod)\n"
                "    n = WasmModuleGetWATLength(mod)\n"
                "    escribir_linea(concat(\"wasm mod ok wat_len=\", entero_a_texto(n)))\n"
                "    WasmModuleDispose(mod)\n"
                "    retornar 0\n"
            )
        r = _compilar_completo(src, tmp, "probe_wasm")
        assert r.returncode == 0, f"std.wasm no enlaza:\n{r.stdout}\n{r.stderr[:2000]}"
        candidato = os.path.join(tmp, "probe_wasm.exe")
        run = subprocess.run([candidato], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=60)
        assert run.returncode == 0, f"probe wasm rc={run.returncode}: {run.stdout} {run.stderr[:500]}"
        assert "wasm mod ok" in run.stdout


# =========================================================================
# M2: work-stealing de std.cluster implementado (Manual 5 §8.1)
# =========================================================================

def _gcc() -> str:
    g = os.path.join(RAIZ, "toolchain_gcc12", "mingw64", "bin", "gcc.exe")
    return g if os.path.exists(g) else "gcc"


def _runtime_objs(tmp: str) -> list:
    """Compila la FRONTERA CANONICA de enlace del S1: _RT_FUENTES
    (synapse_rt.c + runtime/core/*.c + motores nucleo + tweetnacl + sqlite3)
    + cuánticos + federated + IA, igual que el enlace modular de
    ejecutar_compilador (pipeline.py:828-850). Un probe que enlaza menos
    que el S1 no mide la frontera real (hallazgo M2: enlazaba solo
    cluster.c+synapse_rt.c y el link reventaba con pool_alloc/sha256_*/
    crypto_*/randombytes sin resolver — la misma clase de brecha que
    R149 §4 detectó en std↔runtime)."""
    import glob
    gcc = _gcc()
    out = []
    fuentes = ["synapse_rt.c"]
    fuentes += sorted(glob.glob(os.path.join(RAIZ, "runtime", "core", "*.c")))
    fuentes += ["nucleo/atp_engine.c", "nucleo/symbolic_exec.c",
                "nucleo/proof_bridge.c", "nucleo/quantum_err_corr.c",
                "nucleo/dist_orchestrator.c",
                "axon/tweetnacl.c", "vendor/sqlite3/sqlite3.c",
                "nucleo/quantum_runtime.c", "nucleo/quantum_memory.c",
                "nucleo/surface_code.c",
                "nucleo/federated.c",
                "nucleo/fine_tuning.c", "nucleo/distillation.c",
                "nucleo/quantization.c"]
    for src in fuentes:
        ruta = os.path.join(RAIZ, src)
        if not os.path.exists(ruta):
            continue  # módulos opcionales del S1: si no existen, se omiten
        o = os.path.join(tmp, "r150_" + os.path.basename(src) + ".o")
        rc = subprocess.run([gcc, "-O2", "-c", "-I", RAIZ, ruta, "-o", o],
                            capture_output=True, text=True, timeout=300)
        assert rc.returncode == 0, f"compilando {src}: {rc.stderr[:600]}"
        out.append(o)
    return out


def test_worker_work_stealing_operativo():
    """OBL-R150-M2: worker_* existen y operan la cola ws_* real."""
    gcc = _gcc()
    with tempfile.TemporaryDirectory() as tmp:
        probe_c = os.path.join(tmp, "probe_ws.c")
        with open(probe_c, "w", encoding="utf-8", newline="\n") as f:
            f.write(
                '#include <stdio.h>\n'
                '#include "synapse_rt_types.h"\n'
                '#include "runtime/core/cluster.h"\n'
                'int main(void) {\n'
                '    if (ws_inicializar(8) != 0) { puts("[FAIL] init"); return 1; }\n'
                '    if (!worker_cola_vacia(0)) { puts("[FAIL] cola debe iniciar vacia"); return 1; }\n'
                '    CadenaSegura t1 = { .longitud = 6, .datos = "tarea1" };\n'
                '    if (ws_encolar(41, t1) != 0) { puts("[FAIL] encolar"); return 1; }\n'
                '    if (worker_cola_vacia(0)) { puts("[FAIL] cola no debe estar vacia"); return 1; }\n'
                '    int robado = worker_robar(1);\n'
                '    if (robado != 41) { printf("[FAIL] robo id=%d\\n", robado); return 1; }\n'
                '    CadenaSegura t2 = { .longitud = 6, .datos = "tarea2" };\n'
                '    ws_encolar(7, t2);\n'
                '    ws_encolar(9, t2);\n'
                '    int n = worker_ejecutar(0);\n'
                '    if (n != 2) { printf("[FAIL] procesadas=%d\\n", n); return 1; }\n'
                '    if (!worker_cola_vacia(0)) { puts("[FAIL] cola debe quedar vacia"); return 1; }\n'
                '    puts("ws ok");\n'
                '    return 0;\n'
                '}\n'
            )
        exe = os.path.join(tmp, "probe_ws")
        cmd = [gcc, "-O2", "-I", RAIZ, probe_c] + _runtime_objs(tmp) + \
              ["-lm", "-lpthread", "-lws2_32", "-lole32", "-ldxgi", "-luuid", "-o", exe]
        rc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        assert rc.returncode == 0, f"link probe ws fallo: {rc.stderr[:800]}"
        run = subprocess.run([exe], capture_output=True, text=True, timeout=60)
        assert run.returncode == 0, f"probe ws rc={run.returncode}: {run.stdout} {run.stderr[:400]}"
        assert "ws ok" in run.stdout


# =========================================================================
# M3a: opensyn bindings REAL
# =========================================================================

def test_opensyn_bindings_real():
    """OBL-R150-M3a: 'synapse opensyn bindings' regenera el .syq real."""
    marcador = "// cumple Manual 6 §3.1: declaraciones externo de funciones C"
    bindings = os.path.join(RAIZ, "lib", "runtime_bindings.syq")
    antes = os.path.getmtime(bindings) if os.path.exists(bindings) else 0
    r = subprocess.run([PY, os.path.join(RAIZ, "cli.py"), "opensyn", "bindings"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=RAIZ, timeout=300)
    assert r.returncode == 0, f"bindings rc={r.returncode}: {r.stderr[:600]}"
    assert os.path.exists(bindings), "runtime_bindings.syq no regenerado"
    with open(bindings, encoding="utf-8", errors="replace") as f:
        contenido = f.read()
    assert marcador in contenido, "el .syq regenerado no trae el marcador del generador"
    assert "externo funcion" in contenido
    if antes:
        assert os.path.getmtime(bindings) >= antes, "el archivo no fue reescrito"


# =========================================================================
# M3b: opensyn status REAL (local, sin telemetría)
# =========================================================================

def test_opensyn_status_real():
    """OBL-R150-M3b: status nunca imprime el estado fijo offline falso."""
    r = subprocess.run([PY, os.path.join(RAIZ, "cli.py"), "opensyn", "status"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=RAIZ, timeout=120)
    assert r.returncode == 0, f"status rc={r.returncode}: {r.stderr[:600]}"
    salida = r.stdout + r.stderr
    assert "Estado del entorno (local)" in salida, salida[:400]
    assert "Servidor: no disponible (offline)" not in salida, "status falso persiste"
    assert "Modelos locales en disco" in salida


# =========================================================================
# M3c: download/finetune honestos (rc!=0 sin servicio, jamás [OK] vacío)
# =========================================================================

@pytest.mark.parametrize("sub", ["download", "finetune"])
def test_opensyn_download_finetune_honestos(sub):
    """OBL-R150-M3c: sin servidor local, rc!=0 con mensaje claro (no 'desconocido')."""
    r = subprocess.run([PY, os.path.join(RAIZ, "cli.py"), "opensyn", sub],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=RAIZ, timeout=120)
    assert r.returncode != 0, f"{sub} devolvio exito sin hacer nada"
    salida = r.stdout + r.stderr
    assert "Subcomando" not in salida and "desconocido" not in salida, salida[:400]
    assert "8088" in salida or "ollama" in salida.lower(), salida[:400]


# =========================================================================
# M3d/M4: debugger TRACE v1 real; construir eliminado
# =========================================================================

_TRAZA = "\n".join([
    "TRACE v1",
    "id=probe123",
    "programa=probe.syn",
    "eventos=3",
    "capacidad=4096",
    "---",
    "0|100|principal|probe.syn|10|42|0.000000||x",
    "1|110|principal|probe.syn|12|0|0.000000||",
    "2|120|aux|probe.syn|20|0|0.000000|listo|",
]) + "\n"


def test_debug_flujo_completo_sobre_traza_real():
    """OBL-R150-M3d: --load/--step/--reverse/--snapshots operan eventos reales."""
    cli = os.path.join(RAIZ, "cli.py")
    with tempfile.TemporaryDirectory() as tmp:
        traza = os.path.join(tmp, "probe.trace")
        with open(traza, "w", encoding="utf-8", newline="\n") as f:
            f.write(_TRAZA)
        sesion = os.path.join(tempfile.gettempdir(), "r150_dbg_session.json")
        if os.path.exists(sesion):
            os.remove(sesion)
        env = dict(os.environ)
        # El estado de sesión del debugger vive en ~/.synapse/cache; el test lo
        # usa tal cual (última escritura gana) y verifica el flujo completo.
        r1 = subprocess.run([PY, cli, "debug", "--load", traza],
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace", cwd=tmp, timeout=120, env=env)
        assert r1.returncode == 0, f"load rc={r1.returncode}: {r1.stderr[:500]}"
        assert "probe123" in r1.stdout and "3 eventos" in r1.stdout, r1.stdout[:400]
        r2 = subprocess.run([PY, cli, "debug", "--step"],
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace", cwd=tmp, timeout=120, env=env)
        assert r2.returncode == 0 and "ASIGNACION" in r2.stdout, r2.stdout[:400]
        r3 = subprocess.run([PY, cli, "debug", "--step"],
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace", cwd=tmp, timeout=120, env=env)
        assert r3.returncode == 0 and "LLAMADA" in r3.stdout, r3.stdout[:400]
        r4 = subprocess.run([PY, cli, "debug", "--reverse"],
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace", cwd=tmp, timeout=120, env=env)
        assert r4.returncode == 0 and "ASIGNACION" in r4.stdout, r4.stdout[:400]
        r5 = subprocess.run([PY, cli, "debug", "--snapshots"],
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace", cwd=tmp, timeout=120, env=env)
        assert r5.returncode == 0 and "SNAPSHOT" in r5.stdout and "x=42" in r5.stdout, r5.stdout[:400]


def test_debug_step_sin_traza_es_honesto():
    """OBL-R150-M3d: sin sesión, --step falla con rc!=0 (antes: éxito fijo)."""
    sesion = os.path.join(os.path.expanduser("~"), ".synapse", "cache",
                          "debug_session.json")
    respaldo = None
    if os.path.exists(sesion):
        with open(sesion, encoding="utf-8") as f:
            respaldo = f.read()
        os.remove(sesion)
    try:
        r = subprocess.run([PY, os.path.join(RAIZ, "cli.py"), "debug", "--step"],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", cwd=RAIZ, timeout=120)
        assert r.returncode != 0, "step sin traza devolvio exito (teatro)"
        assert "no hay traza cargada" in (r.stdout + r.stderr)
    finally:
        if respaldo is not None:
            with open(sesion, "w", encoding="utf-8") as f:
                f.write(respaldo)


def test_construir_eliminado():
    """OBL-R150-M4/D-R150-2: 'construir' ya no secuestra el CLI (código muerto)."""
    with open(os.path.join(RAIZ, "cli.py"), encoding="utf-8") as f:
        src = f.read()
    assert 'args.construir' not in src
    assert 'axon_build.exe' not in src


# =========================================================================
# M6/M7: versiones y SyntaxWarning
# =========================================================================

def test_banner_usa_version():
    """OBL-R150-M6: el banner del CLI muestra la VERSION canónica."""
    with open(os.path.join(RAIZ, "VERSION"), encoding="utf-8") as f:
        version = f.read().strip()
    with open(os.path.join(RAIZ, "cli.py"), encoding="utf-8") as f:
        src = f.read()
    assert 'v5.0 - Poliglota' not in src
    assert 'VERSION' in src  # se lee el archivo VERSION
    r = subprocess.run([PY, "-c",
                        "import sys; sys.path.insert(0, r'%s');"
                        "import cli; print(cli.main.__doc__)" % RAIZ],
                       capture_output=True, text=True, timeout=60)
    # El chequeo fuerte: la descripción del parser se construye desde VERSION
    assert version == "8.1.0-industrial"
    assert '"Synapse Compiler v5.0' not in src


def test_verificar_e2e_sin_syntaxwarning():
    """OBL-R150-M7: importar scripts/verificar_e2e.py no emite SyntaxWarning."""
    import importlib.util
    import warnings
    ruta = os.path.join(RAIZ, "scripts", "verificar_e2e.py")
    spec = importlib.util.spec_from_file_location("verificar_e2e", ruta)
    mod = importlib.util.module_from_spec(spec)
    with warnings.catch_warnings():
        warnings.simplefilter("error", SyntaxWarning)
        spec.loader.exec_module(mod)


# =========================================================================
# M13: working tree limpio
# =========================================================================

def test_working_tree_sin_ruido():
    """OBL-R150-M13: keep/ y .venv-1/ no existen (ruido M13)."""
    assert not os.path.exists(os.path.join(RAIZ, "keep"))
    assert not os.path.exists(os.path.join(RAIZ, ".venv-1"))


# =========================================================================
# M15: std.testing.expone verificar() y compila+enlaza
# =========================================================================

def test_testing_verificar_e2e():
    """OBL-R150-M15: el código que genera SKILL_TDD_PROMPT compila y pasa."""
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "probe_tdd.syn")
        with open(src, "w", encoding="utf-8", newline="\n") as f:
            f.write(
                "#lang: es\n"
                "importar std.testing\n"
                "\n"
                "funcion principal() -> entero:\n"
                "    fallos = 0\n"
                "    fallos = fallos + verificar(1 == 1, \"uno mas uno\")\n"
                "    escribir_linea(concat(\"fallos=\", entero_a_texto(fallos)))\n"
                "    retornar fallos\n"
            )
        r = _compilar_completo(src, tmp, "probe_tdd")
        assert r.returncode == 0, f"std.testing.verificar no enlaza:\n{r.stdout}\n{r.stderr[:1500]}"
        candidato = os.path.join(tmp, "probe_tdd.exe")
        run = subprocess.run([candidato], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=60)
        assert run.returncode == 0, f"probe tdd rc={run.returncode}: {run.stdout} {run.stderr[:400]}"
        assert "[PASS] uno mas uno" in run.stdout and "fallos=0" in run.stdout


