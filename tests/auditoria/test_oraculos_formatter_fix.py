# tests/auditoria/test_oraculos_formatter_fix.py
# Oráculo del ME formatter_fix (cierre de H-33.5-3).
# OBL | Manual 8 §4.1: "| **`synapse fmt`** (Fase 31) | Ejecuta el formateador
# nativo sobre el código fuente. |" con ejemplo canónico "synapse fmt --check
# src/"; Manual 1 §6: "Regla de hierro: Ninguna característica nueva puede
# romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0). El determinismo
# se verifica obligatoriamente en la CI mediante la comparación de los hashes
# SHA-256 de las etapas 2 y 3."; Manual 2 §2: cadena_literal
# ::= '"' { caracter_escapado | cualquier_caracter } '"' | integracion | TDD
#
# Requisitos:
# 1. Ejecutar desde la raíz: .venv/Scripts/python.exe -m pytest tests/auditoria/test_oraculos_formatter_fix.py -v
# 2. Suite LENTA (bootstrap 2 etapas): timeout >= 900 en contrastar.py.
import os
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PY = sys.executable

STAGE1 = os.path.join(RAIZ, "synapse_stage1.exe")
STAGE2 = os.path.join(RAIZ, "synapse_stage2.exe")
PRINCIPAL = os.path.join(RAIZ, "nucleo", "principal.syn")

LINT_SYN = os.path.join(RAIZ, "nucleo", "lint.syn")
FORMATTER_SYN = os.path.join(RAIZ, "nucleo", "formatter.syn")


def _exe_fresco():
    """Stage2 del bootstrap; regenera Etapa 1→2 si quedó stale tras editar
    nucleo/*.syn o nucleo/generador/*.syn (un exe stale parece éxito y no lo
    es — lección R161)."""
    exe = STAGE2
    fuentes = [os.path.join(RAIZ, "nucleo", f) for f in (
        "lexer.syn", "parser_expr.syn", "parser_declaraciones.syn",
        "ast_nodes.syn", "puente_ast.syn", "generator.syn", "principal.syn",
        "lint.syn", "formatter.syn")]
    fuentes += [os.path.join(RAIZ, "nucleo", "generador", f) for f in (
        "monomorfizacion.syn", "orquestador.syn", "expr_eval.syn",
        "nodos_flujo.syn", "recorrido.syn")]
    limite = 0
    for f in fuentes:
        if os.path.exists(f) and os.path.getmtime(f) > limite:
            limite = os.path.getmtime(f)
    # stage1 AUSENTE también dispara regeneración: el pre-commit limpia
    # synapse_stage1.exe (artefacto no rastreado) PERO conserva stage2 —
    # sin este guard, stage2 fresco + stage1 borrado daba falso negativo.
    if (not os.path.exists(exe) or not os.path.exists(STAGE1)
            or os.path.getmtime(exe) < limite):
        r1 = subprocess.run(
            [PY, os.path.join(RAIZ, "main.py"), PRINCIPAL, "-o", STAGE1],
            cwd=RAIZ, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=900)
        assert r1.returncode == 0, f"stage1 rc={r1.returncode}\n{r1.stdout[-400:]}"
        r2 = subprocess.run([STAGE1, PRINCIPAL, "-o", STAGE2], cwd=RAIZ,
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=900)
        assert r2.returncode == 0, f"stage2 rc={r2.returncode}\n{r2.stdout[-400:]}"
    return exe


def _escribir(ruta, contenido):
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(contenido)


MALO = (
    "#lang: es\n"
    "// cumple Manual 1 §7.1: probe del formatter\n"
    "funcion  prueba( ) -> entero:\n"
    "    let x=1,  y = 2\n"
    "\tlet s = \"hola  mundo  \"\n"
    "    retornar x + y\n"
)


def test_dedupe_backend_sin_simbolos_duplicados():
    """Manual 3 §12 (12.2): lint.syn se compone con formatter.syn vía import;
    anti-regresión del first-wins que causó H-33.5-3 (un duplicado de
    normalizar_espacios en lint.syn ensombrece al del formatter)."""
    fuente = open(LINT_SYN, encoding="utf-8").read()
    assert "importar formatter" in fuente, "lint.syn debe importar formatter"
    assert "funcion normalizar_espacios" not in fuente, \
        "lint.syn NO debe definir normalizar_espacios (duplicado first-wins)"
    assert "funcion recortar" not in fuente, \
        "lint.syn NO debe definir recortar (duplicado)"
    assert "funcion fix_linea" in fuente, "fix_linea() debe seguir existiendo"
    fmt = open(FORMATTER_SYN, encoding="utf-8").read()
    assert "funcion normalizar_espacios" in fmt
    assert "en_literal" in fmt, "protección de literales ausente"


def test_fmt_detecta_y_colapsa_espacios():
    """Manual 8 §4.1 + Manual 1 §7.1: fmt --check rc=1 en mal formateado
    (ANTES del fix daba rc=0 falso: reproducción de H-33.5-3), fmt reescribe
    colapsando espacios dobles FUERA de literales y queda idempotente."""
    exe = _exe_fresco()
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "probe.syn")
        _escribir(p, MALO)
        r = subprocess.run([exe, "fmt", "--check", p], cwd=RAIZ,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=120)
        assert r.returncode == 1, (
            f"fmt --check debe rc=1 en mal formateado (H-33.5-3); rc={r.returncode}")
        r = subprocess.run([exe, "fmt", p], cwd=RAIZ,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=120)
        assert r.returncode == 0, f"fmt (write) rc={r.returncode}"
        reformateado = open(p, encoding="utf-8").read()
        assert "let x=1, y = 2" in reformateado, reformateado
        r = subprocess.run([exe, "fmt", "--check", p], cwd=RAIZ,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=120)
        assert r.returncode == 0, "fmt --check debe rc=0 tras reformato (idempotencia)"


def test_fmt_no_corrompe_literales():
    """Manual 2 §2 cadena_literal: el contenido del literal (con escapes) es
    significativo — el colapso de espacios NO debe tocar dentro de "..."."""
    exe = _exe_fresco()
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "literal.syn")
        _escribir(p, MALO)
        subprocess.run([exe, "fmt", p], cwd=RAIZ, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=120)
        reformateado = open(p, encoding="utf-8").read()
        assert '"hola  mundo  "' in reformateado, \
            "el literal debe sobrevivir byte a byte:\n" + reformateado


def test_lint_fix_paridad_fmt():
    """Manual 1 §7.1: lint --fix y fmt aplican la MISMA regla de estilo —
    paridad fix_linea -> formatear_linea (R1)."""
    exe = _exe_fresco()
    with tempfile.TemporaryDirectory() as tmp:
        p1 = os.path.join(tmp, "a.syn")
        p2 = os.path.join(tmp, "b.syn")
        _escribir(p1, MALO)
        _escribir(p2, MALO)
        r1 = subprocess.run([exe, "lint", "--fix", p1], cwd=RAIZ,
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=120)
        assert r1.returncode in (0, 1), f"lint --fix rc={r1.returncode}"
        r2 = subprocess.run([exe, "fmt", p2], cwd=RAIZ,
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=120)
        assert r2.returncode == 0, f"fmt rc={r2.returncode}"
        a = open(p1, encoding="utf-8").read()
        b = open(p2, encoding="utf-8").read()
        assert a == b, f"lint --fix y fmt divergen:\n--- lint --fix ---\n{a}\n--- fmt ---\n{b}"


def test_bootstrap_s1_s2_verde():
    """Manual 1 §6 (regla de hierro): el bootstrap sigue enlazando con el
    backend deduplicado; humo fmt --check rc=0 sobre un probe formateado."""
    exe = _exe_fresco()
    assert os.path.exists(STAGE1), "stage1 no existe"
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "ok.syn")
        _escribir(p, "#lang: es\nfuncion principal() -> entero:\n    retornar 0\n")
        subprocess.run([exe, "fmt", p], cwd=RAIZ, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=120)
        r = subprocess.run([exe, "fmt", "--check", p], cwd=RAIZ,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=120)
        assert r.returncode == 0, f"stage2 (nativo) fmt --check rc={r.returncode}"


def test_nucleo_formateado():
    """Manual 1 §7.1 (R4): TODO el nucleo reformateado pasa fmt --check
    (idempotencia real del estado final, no maquillada)."""
    exe = _exe_fresco()
    import glob
    malos = []
    for f in sorted(glob.glob(os.path.join(RAIZ, "nucleo", "*.syn"))) + \
            sorted(glob.glob(os.path.join(RAIZ, "nucleo", "generador", "*.syn"))):
        if os.path.basename(f).startswith("_tmp_"):
            continue  # artefactos efímeros gitignored
        r = subprocess.run([exe, "fmt", "--check", f], cwd=RAIZ,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=120)
        if r.returncode != 0:
            malos.append(os.path.relpath(f, RAIZ))
    assert not malos, f"archivos del nucleo mal formateados: {malos}"
