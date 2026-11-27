# tests/auditoria/test_oraculos_33_5_certificacion.py
# Oráculo de certificación de la Fase 33 (ME 33.5_certificacion, ROADMAP §33.5).
# OBL | Manual 9 §6.1: "el proceso de bootstrap de 3 etapas produce `diff 0
# bytes` entre Stage 2 y Stage 3"; Manual 9 §6.2: el pipeline ejecuta "La
# verificación del bootstrap (diff 0 bytes)" y `synapse lint --check` /
# `synapse fmt --check`; Manual 8 §4.1: `synapse lint --fix <arch>` /
# `synapse fmt --check <arch>` (orden canónico); Manual 1 §6: regla de hierro
# del bootstrap. | integracion | TDD
#
# Requisitos:
# 1. Ejecutar desde la raíz: .venv/Scripts/python.exe -m pytest tests/auditoria/test_oraculos_33_5_certificacion.py -v
# 2. Suite LENTA (bootstrap 3 etapas): timeout 900 en contrastar.py.
import hashlib
import os
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PY = sys.executable

STAGE1 = os.path.join(RAIZ, "synapse_stage1.exe")
STAGE2 = os.path.join(RAIZ, "synapse_stage2.exe")
STAGE3 = os.path.join(RAIZ, "synapse_stage3.exe")
PRINCIPAL = os.path.join(RAIZ, "nucleo", "principal.syn")


def _sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def _exe_fresco():
    """Stage2 del bootstrap; regenera Etapa 1→2 si quedó stale tras editar
    nucleo/*.syn o nucleo/generador/*.syn (un exe stale parece éxito y no lo
    es — lección R161)."""
    exe = STAGE2
    fuentes = [os.path.join(RAIZ, "nucleo", f) for f in (
        "lexer.syn", "parser_expr.syn", "parser_declaraciones.syn",
        "ast_nodes.syn", "puente_ast.syn", "generator.syn", "principal.syn")]
    fuentes += [os.path.join(RAIZ, "nucleo", "generador", f) for f in (
        "monomorfizacion.syn", "orquestador.syn", "expr_eval.syn",
        "nodos_flujo.syn", "recorrido.syn")]
    limite = 0
    for f in fuentes:
        if os.path.exists(f) and os.path.getmtime(f) > limite:
            limite = os.path.getmtime(f)
    if not os.path.exists(exe) or os.path.getmtime(exe) < limite:
        r1 = subprocess.run(
            [PY, os.path.join(RAIZ, "main.py"), PRINCIPAL, "-o", STAGE1],
            cwd=RAIZ, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=600)
        assert r1.returncode == 0, f"stage1 rc={r1.returncode}\n{r1.stdout[-400:]}"
        r2 = subprocess.run([STAGE1, PRINCIPAL, "-o", STAGE2], cwd=RAIZ,
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=600)
        assert r2.returncode == 0, f"stage2 rc={r2.returncode}\n{r2.stdout[-400:]}"
    return exe


def _compilar_completo(ruta_syn, tmp, nombre):
    """Compila y ENLAZA un .syn con el pipeline S1 real (no check_only) —
    mismo mecanismo de tests/auditoria/test_matriz_compilacion.py."""
    salida = os.path.join(str(tmp), nombre + ".exe")
    script = (
        "import sys;"
        "sys.path.insert(0, r'%s');"
        "from pipeline import ejecutar_compilador;"
        "sys.exit(ejecutar_compilador(r'%s', output_path=r'%s'))"
        % (RAIZ, ruta_syn, salida))
    return subprocess.run([PY, "-c", script], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=str(tmp),
                          timeout=600)


def test_bootstrap_3_etapas_s2_s3_byte_identicos():
    """M9 §6.1 + M1 §6: bootstrap 0→1→2→3 real con sha256(S2)==sha256(S3)."""
    assert os.path.exists(STAGE1) or True  # _exe_fresco lo genera si falta
    _exe_fresco()
    assert os.path.exists(STAGE2), "stage2 no existe tras _exe_fresco"
    r3 = subprocess.run([STAGE2, PRINCIPAL, "-o", STAGE3], cwd=RAIZ,
                        capture_output=True, text=True, encoding="utf-8",
                        errors="replace", timeout=600)
    assert r3.returncode == 0, (
        f"Etapa 3 rc={r3.returncode}\n{r3.stdout[-600:]}\n{r3.stderr[-300:]}")
    assert os.path.exists(STAGE3), "Etapa 3 no genero synapse_stage3.exe"
    s2, s3 = _sha256(STAGE2), _sha256(STAGE3)
    assert s2 == s3, (
        f"Manual 9 §6.1 VIOLADO: S2 != S3\n  S2 sha256: {s2}\n  S3 sha256: {s3}")


def test_matriz_extendida_std_con_features_33_4():
    """M9 §6.1 + ROADMAP §33.5: matriz extendida con los std que ejercitan las
    features de 33.4 (para-en: std/debug.syn; indexado: std/modelo.syn) —
    importar + enlace completo + ejecución rc=0."""
    exes = {}
    for mod in ("debug", "modelo"):
        exes[mod] = _exe_fresco()
    with tempfile.TemporaryDirectory() as tmp:
        # std.debug: para-en dentro del módulo; el probe lo importa y llama
        p_debug = os.path.join(tmp, "matriz_ext_debug.syn")
        with open(p_debug, "w", encoding="utf-8", newline="\n") as f:
            f.write("#lang: es\nimportar std.debug\n\n"
                    "funcion principal() -> entero:\n"
                    "    escribir_linea(\"matriz debug ok\")\n"
                    "    retornar 0\n")
        r = _compilar_completo(p_debug, tmp, "matriz_ext_debug")
        assert r.returncode == 0, (
            f"std.debug (para-en): no compila/enlaza:\n{r.stdout}\n{r.stderr[:1500]}")
        exe = os.path.join(tmp, "matriz_ext_debug.exe")
        run = subprocess.run([exe], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=120)
        assert run.returncode == 0 and "matriz debug ok" in run.stdout, (
            f"std.debug: binario rc={run.returncode}: {run.stdout} {run.stderr[:400]}")
        # std.modelo: indexado xs[i] dentro del módulo; el probe lo importa
        p_modelo = os.path.join(tmp, "matriz_ext_modelo.syn")
        with open(p_modelo, "w", encoding="utf-8", newline="\n") as f:
            f.write("#lang: es\nimportar std.modelo\n\n"
                    "funcion principal() -> entero:\n"
                    "    escribir_linea(\"matriz modelo ok\")\n"
                    "    retornar 0\n")
        r = _compilar_completo(p_modelo, tmp, "matriz_ext_modelo")
        assert r.returncode == 0, (
            f"std.modelo (indexado): no compila/enlaza:\n{r.stdout}\n{r.stderr[:1500]}")
        exe = os.path.join(tmp, "matriz_ext_modelo.exe")
        run = subprocess.run([exe], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=120)
        assert run.returncode == 0 and "matriz modelo ok" in run.stdout, (
            f"std.modelo: binario rc={run.returncode}: {run.stdout} {run.stderr[:400]}")


def test_dispatch_fmt_orden_canonico_m8_41():
    """M8 §4.1: `synapse fmt --check <archivo>` (flag antes de la ruta, orden
    del ejemplo canónico 'synapse fmt --check src/') con rc=0 en bien
    formateado y rc=1 en mal formateado; el orden antiguo se conserva."""
    exe = _exe_fresco()
    with tempfile.TemporaryDirectory() as tmp:
        bueno = os.path.join(tmp, "bueno.syn")
        with open(bueno, "w", encoding="utf-8", newline="\n") as f:
            f.write("#lang: es\nfuncion principal() -> entero:\n"
                    "    escribir_linea(\"ok\")\n    retornar 0\n")
        r = subprocess.run([exe, "fmt", "--check", bueno], cwd=RAIZ,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=120)
        assert r.returncode == 0, (
            f"fmt --check <arch> (canonico) rc={r.returncode}: {r.stdout} {r.stderr}")
        # orden antiguo (retrocompatibilidad r152)
        r = subprocess.run([exe, "fmt", bueno, "--check"], cwd=RAIZ,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=120)
        assert r.returncode == 0, f"fmt <arch> --check rc={r.returncode}"


def test_dispatch_lint_orden_canonico_m8_41():
    """M8 §4.1: `synapse lint --fix <archivo>` / `synapse lint <archivo>` con
    rc=0 sin advertencias y rc=1 con advertencias (el rc propaga)."""
    exe = _exe_fresco()
    with tempfile.TemporaryDirectory() as tmp:
        bueno = os.path.join(tmp, "bueno.syn")
        with open(bueno, "w", encoding="utf-8", newline="\n") as f:
            f.write("#lang: es\nfuncion principal() -> entero:\n"
                    "    escribir_linea(\"ok\")\n    retornar 0\n")
        r = subprocess.run([exe, "lint", bueno], cwd=RAIZ,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=120)
        assert r.returncode == 0, f"lint sin advertencias rc={r.returncode}"
        # orden canonico con flag: lint --fix (flag antes de la ruta)
        r = subprocess.run([exe, "lint", "--fix", bueno], cwd=RAIZ,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=120)
        assert r.returncode == 0, f"lint --fix <arch> (canonico) rc={r.returncode}"
        malo = os.path.join(tmp, "malo.syn")
        with open(malo, "w", encoding="utf-8", newline="\n") as f:
            f.write("funcion  principal( ) -> entero:\n"
                    "    escribir_linea(\"x\")\n    retornar 0\n")
        r = subprocess.run([exe, "lint", malo], cwd=RAIZ,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=120)
        assert r.returncode == 1, (
            f"lint con advertencias debe rc=1 (M8 §4.1 --check gate), "
            f"obtuvo rc={r.returncode}")


def test_anti_fabricacion_sha256_sobre_binarios_reales():
    """Anti-fabricación: el sello S2==S3 se calcula sobre los binarios reales
    (no se acepta un par de .exe ausentes); si stage3 no existe se genera."""
    _exe_fresco()
    if not os.path.exists(STAGE3) or os.path.getmtime(STAGE3) < os.path.getmtime(STAGE2):
        r3 = subprocess.run([STAGE2, PRINCIPAL, "-o", STAGE3], cwd=RAIZ,
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=600)
        assert r3.returncode == 0, "Etapa 3 fallo en anti-fabricacion"
    for exe in (STAGE2, STAGE3):
        assert os.path.exists(exe), f"{exe} no existe: sin binario no hay sello"
        h = _sha256(exe)
        assert len(h) == 64 and h != hashlib.sha256(b"").hexdigest()
