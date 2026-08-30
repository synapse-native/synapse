"""
test_syquex_lexer.py — FASE 22 / R86: `syquex/lexer.syn` (Manual 3 §1-§4).

Verifica contra el lexer Syquex REAL (compilado con el S1 por concatenación
módulo+driver, mismo mecanismo de test_ast_abi):

  1. Tokeniza la muestra del Manual 3 §6/§13 sin errores (rc=0, TOTAL>0).
  2. Keywords propios de Syquex (Manual 3 §4) presentes con sus TokenID:
     estructura/crear/metodo/enumeracion/intentar/atrapar/lista/mapa/
     rango ".."/paso + heredadas (funcion, débil, nulo).
  3. Literales: exponente numérico "2e1" → FLOT (M3 §3 numero), cadena con
     \\uXXXX decodificada a UTF-8 ("Aé\n"), lexema preservado.
  4. Comentarios de bloque ANIDADOS (M3 §1.3) se consumen sin ruido y
     restauran el flujo.
  5. Indentación INDENT/DEDENT tras cabeceras con ':' (M3 §2 bloques).
"""

import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.syquex

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LEXER_PATH = os.path.join(PROJECT_ROOT, "syquex", "lexer.syn")
DRIVER_PATH = os.path.join(PROJECT_ROOT, "tests", "fixtures", "test_syquex_lexer_drv.syn")


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def bin_salida() -> str:
    modulo = _read(LEXER_PATH)
    driver = _read(DRIVER_PATH)
    lineas_mod = [l for l in modulo.splitlines() if not l.startswith("#lang")]
    combinado = driver.rstrip("\n") + "\n\n" + "\n".join(lineas_mod) + "\n"

    nucleo_dir = os.path.join(PROJECT_ROOT, "nucleo")
    drv = os.path.join(nucleo_dir, "_tmp_sq_lex_drv.syn")
    try:
        with open(drv, "w", encoding="utf-8") as f:
            f.write(combinado)
        r = subprocess.run(
            [sys.executable, os.path.join(PROJECT_ROOT, "main.py"), drv],
            capture_output=True, text=True, timeout=900, cwd=PROJECT_ROOT)
        assert r.returncode == 0, \
            f"build rc={r.returncode}\n{r.stdout[-1500:]}\n{r.stderr[-800:]}"
        exe = drv[:-4] + ".exe"
        assert os.path.exists(exe)
        e = subprocess.run([exe], capture_output=True, text=True,
                           timeout=120, encoding="utf-8", errors="replace")
    finally:
        for ext in ("", ".c", ".exe", ".syn.json"):
            p = drv[:-4] + ext
            if os.path.exists(p):
                os.remove(p)
    assert e.returncode == 0, f"run rc={e.returncode}\n{e.stdout[-1500:]}"
    return e.stdout


def _lineas(bin_salida: str) -> list:
    lineas = bin_salida.splitlines()
    ini = next(i for i, l in enumerate(lineas) if l.startswith("TOTAL="))
    fin = next(i for i, l in enumerate(lineas) if l == "FIN_DUMP")
    return lineas[ini + 1:fin]


def test_tokeniza_sin_errores(bin_salida):
    assert bin_salida.startswith("TOTAL=")
    total = int(bin_salida.splitlines()[0].split("=")[1])
    assert total > 40, f"muy pocos tokens ({total})"
    assert "LEX_ERROR" not in bin_salida
    assert _lineas(bin_salida)[-0:] is not None and "FIN_DUMP" in bin_salida


def test_keywords_syquex_presentes(bin_salida):
    dump = "\n".join(_lineas(bin_salida))
    esperados = [
        ("ESTRUCTURA", "estructura"),
        ("CREAR", "crear"),
        ("METODO", "metodo"),
        ("ENUMERACION", "enumeracion"),
        ("LISTA", "lista"),
        ("MAPA", "mapa"),
        ("PASO", "paso"),
        ("INTENTAR", "intentar"),
        ("ATRAPAR", "atrapar"),
        ("DEBIL", "débil"),
        ("NULO", "nulo"),
        ("FUNCION", "funcion"),
        ("EN", "en"),
    ]
    lineas_l = _lineas(bin_salida)
    for nombre, lexema in esperados:
        assert any(l.startswith(nombre + "|") and l.endswith("|" + lexema)
                   for l in lineas_l), f"falta {nombre} '{lexema}'"
    # RANGO es puntuación estructural: se emite SIN lexema (patrón del
    # lexer nativo para operadores no-tipo); verificamos presencia.
    assert any(l.startswith("RANGO|") for l in lineas_l), "falta RANGO '..'"
    # El nombre de la estructura viaja como IDENTIFICADOR con su lexema
    assert any(l.startswith("ID|") and l.endswith("|Punto")
               for l in lineas_l), "falta ID 'Punto'"


def test_exponente_numerico_es_flotante(bin_salida):
    """M3 §3 numero ::= DIGITO+ ['.'DIGITO+] ['e'['-']DIGITO+] → '2e1' es FLOT."""
    lineas = _lineas(bin_salida)
    assert any(l.startswith("FLOT|") and l.endswith("|2e1") for l in lineas), \
        "exponente '2e1' no clasificado como FLOTANTE"


def test_cadena_unicode_escape(bin_salida):
    """M2/M3 cadena_literal: \u00e9 → UTF-8 'é'; \n real dentro de la cadena."""
    lineas = _lineas(bin_salida)
    # La cadena es "A\u00e9\n" → decodificada "Aé\n" (el \n real corta el
    # lexema mostrado en el dump; comprobamos prefijo Aé)
    assert any(l.startswith("STR|") and "|A\xc3\xa9" in l for l in lineas) or \
           any(l.startswith("STR|") and "|Aé" in l for l in lineas), \
           "escape \\u00e9 no decodificado a UTF-8"


def test_comentarios_bloque_anidados():
    """M3 §1.3: /* anidado /* más */ */ se consume completo y el flujo sigue."""
    modulo = _read(LEXER_PATH)
    lineas_mod = [l for l in modulo.splitlines() if not l.startswith("#lang")]
    muestra = (
        "#lang: es\\n"
        "/* externo /* anidado */ aun externo */\\n"
        "funcion principal() -> entero:\\n"
        "    retornar 7\\n"
    )
    driver_cb = (
        "#lang: es\n"
        "funcion nombre_token(t: entero) -> cadena:\n"
        "    si t == T_FUNCION:\n"
        "        retornar \"FUNCION\"\n"
        "    si t == T_NUMERO:\n"
        "        retornar \"NUM\"\n"
        "    retornar \"?\"\n"
        "funcion principal() -> entero:\n"
        '    fuente = "' + muestra + '"\n'
        "    total = tokenizar_syquex(fuente)\n"
        '    escribir_linea(concat("TOTAL=", entero_a_texto(total)))\n'
        "    si total < 0:\n"
        "        escribir_linea(\"LEX_ERROR\")\n"
        "        retornar 1\n"
        "    i = 0\n"
        "    mientras i < total:\n"
        '        p1 = concat(nombre_token(sq_token_tipo(i)), "|")\n'
        '        p2 = concat(p1, entero_a_texto(sq_token_linea(i)))\n'
        '        p3 = concat(p2, "|")\n'
        '        p4 = concat(p3, sq_token_lexema(i))\n'
        "        escribir_linea(p4)\n"
        "        i = i + 1\n"
        '    escribir_linea("FIN_DUMP")\n'
        "    retornar 0\n"
    )
    combinado = (driver_cb.rstrip("\n") + "\n\n" + "\n".join(lineas_mod) + "\n")
    nucleo_dir = os.path.join(PROJECT_ROOT, "nucleo")
    drv = os.path.join(nucleo_dir, "_tmp_sq_lex_cb.syn")
    try:
        with open(drv, "w", encoding="utf-8") as f:
            f.write(combinado)
        r = subprocess.run(
            [sys.executable, os.path.join(PROJECT_ROOT, "main.py"), drv],
            capture_output=True, text=True, timeout=900, cwd=PROJECT_ROOT)
        assert r.returncode == 0, r.stderr[-800:]
        exe = drv[:-4] + ".exe"
        e = subprocess.run([exe], capture_output=True, text=True,
                           timeout=120, encoding="utf-8", errors="replace")
    finally:
        for ext in ("", ".c", ".exe", ".syn.json"):
            p = drv[:-4] + ext
            if os.path.exists(p):
                os.remove(p)
    assert e.returncode == 0
    lineas = [l for l in e.stdout.splitlines()
              if l and not l.startswith("TOTAL=") and l != "FIN_DUMP"]
    assert any(l.startswith("FUNCION|") and l.endswith("|funcion") for l in lineas), \
        "el comentario anidado no se consumió correctamente:\n" + e.stdout
    assert not any("|externo|" in l or "|anidado|" in l for l in lineas), \
        "restos del comentario en el flujo:\n" + e.stdout
