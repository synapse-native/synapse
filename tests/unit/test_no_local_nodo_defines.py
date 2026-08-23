"""
test_no_local_nodo_defines.py — D-9(e): test de regresión

Verifica que NINGÚN archivo .c/.h del proyecto (git-tracked y generados
no-track _synapse_shared.h) contenga bloques #ifndef duplicados para
NODO_* o T_*. Esa tabla canónica vive únicamente en
runtime/core/ast_nodos.h (fuente: nucleo/parser_constantes.syn).

Si este test falla:
  1. El generador Python (generator.py) fue modificado para emitir inline defines
     de nuevo → corregir el generador.
  2. Un archivo C fue editado manualmente añadiendo definiciones locales
     → reemplazar con #include "runtime/core/ast_nodos.h".
  3. Un nuevo archivo .c/.h fue agregado con defines duplicados
     → migrarlo también.
  4. Un _synapse_shared.h generado está desactualizado (aún no regenerado
     con la versión corregida de generator.py) → borrarlo o migrarlo.
"""
import os
import re
import subprocess

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RE_NODO_DEFINE = re.compile(r"^\s*#ifndef\s+NODO_")
RE_T_DEFINE = re.compile(
    r"^\s*#ifndef\s+T_(SI|SINO|FUNCION|RETORNAR|LANZAR|RECUPERAR|ESCUCHAR|MIENTRAS|"
    r"IMPORTAR|ESTRUCTURA|ROMPER|SIGUIENTE|PUNTO|Y|O|NO|VERDADERO|FALSO|"
    r"IDENTIFICADOR|NUMERO|FLOTANTE|CADENA|MAYOR|MENOR|IGUAL|DISTINTO|"
    r"MENOR_IGUAL|MAYOR_IGUAL|ASIGNAR|MAS|MENOS|POR|DIV|MOD|FLECHA|COINCIDIR|"
    r"FLECHA_DER|PAREN_IZQ|PAREN_DER|DOSPUNTOS|COMA|NUEVALINEA|INDENTAR|"
    r"DESINDENTAR|AMPERSAND|INSEGURO|IMPORTAR_C|EXTERNO|FLECHA_IZQ|"
    r"REQUIERE|GARANTIZA|CANAL|ASM|CONSTANTE|PUNTOCOMA|PARA|FIN|LET|"
    r"TIPO|TENSOR|NULO|OK|ERR|ALGUN|NINGUNO|MODULO|DELEGAR|EXPORT|"
    r"RC|ARC|DEBIL|PIPE|INTERROGACION)\s*$"
)


def _get_tracked_c_h_files():
    """Lista archivos .c/.h git-tracked desde el repo root."""
    result = subprocess.run(
        ["git", "ls-files", "--", "*.c", "*.h"],
        capture_output=True, text=True, cwd=RAIZ
    )
    for fpath in result.stdout.strip().split("\n"):
        if fpath and os.path.isfile(os.path.join(RAIZ, fpath)):
            yield os.path.join(RAIZ, fpath)


def _get_untracked_synapse_shared():
    """Lista archivos _synapse_shared.h NO trackados (generados).

    Estos headers se generan con pipeline.py -> GeneradorC.generar(modo='header').
    Si quedan en disco con #ifndef inline, indican que fueron generados antes de
    la migración D-9(e) y no se regeneraron.
    """
    for dirpath, dirnames, filenames in os.walk(RAIZ):
        dirnames[:] = [
            d for d in dirnames
            if d not in ('.git', '__pycache__', '.venv', 'venv',
                         'node_modules', '.pytest_cache')
        ]
        for fname in filenames:
            if fname == '_synapse_shared.h':
                fpath = os.path.join(dirpath, fname)
                # Solo archivos no trackados por git
                check = subprocess.run(
                    ["git", "ls-files", "--error-unmatch",
                     os.path.relpath(fpath, RAIZ)],
                    capture_output=True, text=True, cwd=RAIZ
                )
                if check.returncode != 0:
                    yield fpath


def _get_all_scanned_files():
    """Combina tracked .c/.h + untracked _synapse_shared.h."""
    for f in _get_tracked_c_h_files():
        yield f
    for f in _get_untracked_synapse_shared():
        yield f


def test_no_local_nodo_defines():
    violations = []
    for fpath in _get_all_scanned_files():
        with open(fpath, encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f, 1):
                if RE_NODO_DEFINE.match(line):
                    violations.append((fpath, i, line.strip()))
    assert not violations, (
        f"Archivos con #ifndef NODO_* locales encontrados (deben incluir "
        f"runtime/core/ast_nodos.h en su lugar):\n"
        + "\n".join(
            f"  {os.path.relpath(fp, RAIZ)}:{i}: {text}" for fp, i, text in violations
        )
    )


def test_no_local_tokenid_defines():
    violations = []
    for fpath in _get_all_scanned_files():
        with open(fpath, encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f, 1):
                if RE_T_DEFINE.match(line):
                    violations.append((fpath, i, line.strip()))
    assert not violations, (
        f"Archivos con #ifndef T_* locales encontrados (deben incluir "
        f"runtime/core/ast_nodos.h en su lugar):\n"
        + "\n".join(
            f"  {os.path.relpath(fp, RAIZ)}:{i}: {text}" for fp, i, text in violations
        )
    )
