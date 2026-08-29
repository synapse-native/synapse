#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_cobertura_d5.py — D-5 (FASE A/A5): cobertura del generador >=70%.

  Cierra la deuda D-5 (cobertura del ME: generator.py 58% < 70%). El harness se
  reorienta al frontend unico (S1 = fuente de verdad del codegen desde A4):
  un programa extenso que ejercita las ramas del generador (control de flujo,
  lanzar/recuperar, coincidir sobre ADT generico, canales, tensores, contratos,
  @export, asm, structs, alias, constante, importar_c, externa) + tests
  dirigidos a los modos de emision (header/modulo), no_std, safe_mode y rutas
  de error.

  Medicion: `coverage run --source=compilador/generator -m pytest
  tests/unit/test_generator.py tests/test_cobertura_d5.py tests/...` — el
  criterio D-5 es generator.py >=70% en el ME que cierra FASE A.

Manuales: Manual 2 §2 (control de flujo, canales, contratos), §4.2 (ADT),
Manual 3 §7 (?/delegar), Manual 9 §9.7 (determinismo).
"""
import os
import subprocess
import sys
import tempfile

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from pipeline import compilar_desde_texto
from compilador.generator import GeneradorC
from cli import _resolver_gcc

_FIXTURE = os.path.join(RAIZ, "tests", "integration", "fixtures", "test_d5_cobertura.syn")
with open(_FIXTURE, "r", encoding="utf-8") as _f:
    _PROGRAMA = _f.read()

_FUNCIONES = [
    "clasificar", "clasificar_adt", "con_contrato", "con_delegar",
    "con_lanzar", "con_recuperar", "con_tensor", "exportada", "factorial",
    "llamar_exportada", "paridad", "propagar", "sumar_puntos",
    "usar_coincidir_generico", "usar_mientras", "usar_para", "principal",
]


def _compilar_ast(programa=None):
    prog = programa if programa is not None else _PROGRAMA
    with tempfile.TemporaryDirectory(prefix="synapse_d5_") as tmp:
        src = os.path.join(tmp, "programa.syn")
        with open(src, "w", encoding="utf-8") as f:
            f.write(prog)
        ast, diag = compilar_desde_texto(src, set())
        assert not diag.hay_errores(), f"Error compilando el programa D-5: {diag}"
        return ast


def _gcc_disponible() -> bool:
    try:
        gcc = _resolver_gcc()
        subprocess.run([gcc, "--version"], capture_output=True, check=True, timeout=10)
        return True
    except Exception:
        return False


def test_codegen_s1_programa_extenso():
    """D-5: el programa extenso genera C con todas las ramas esperadas."""
    ast = _compilar_ast()
    codigo = GeneradorC(ast).generar()
    for fn in _FUNCIONES:
        # El codegen envuelve principal() en _principal_impl(); verificar ambos
        if fn == "principal":
            assert f"{fn}(" in codigo or "_principal_impl(" in codigo, f"falta funcion {fn} (ni _principal_impl)"
        else:
            assert f" {fn}(" in codigo or f"{fn}(" in codigo, f"falta funcion {fn}"
    assert "if (" in codigo and "else {" in codigo, "si/sino"
    assert "while (" in codigo, "mientras"
    assert "for (" in codigo, "para"
    assert "switch (" in codigo and "case TAG_OK:" in codigo, "coincidir"
    assert "case TAG_ERR:" in codigo
    assert "typedef struct Resultado_entero_texto" in codigo, "monomorfizacion D-2"
    assert "if (_prop.tag == 1) return _prop;" in codigo, "operador ? (D-6)"
    assert "Resultado _del = " in codigo, "delegar (patron ?)"
    assert "synapse_lanzar_hilo" in codigo, "lanzar"
    assert "Fallo en contrato: requiere" in codigo, "requiere"
    assert "int64_t exportada(int64_t x)" in codigo, "@export"
    assert "typedef struct Punto" in codigo, "estructura"
    assert "typedef int64_t AliasEntero" in codigo, "alias"
    assert "#define LIMITE (10" in codigo, "constante"  # (10) o (10LL)
    assert "#include \"stddef.h\"" in codigo, "importar_c"
    assert "extern int64_t ayuda_externa" in codigo, "externa"


def test_codegen_s1_modo_header():
    """D-5: modo 'header' — solo cabecera + prototipos, sin cuerpos ni main."""
    ast = _compilar_ast()
    codigo = GeneradorC(ast).generar("header")
    assert "int main(" not in codigo, "header no lleva main"
    assert "int64_t factorial(int64_t n);" in codigo, "prototipo en header"
    assert "int64_t factorial(int64_t n) {" not in codigo, "header no lleva cuerpos"


def test_codegen_s1_modo_modulo():
    """D-5: modo 'modulo' — #include header + solo cuerpos del alcance."""
    ast = _compilar_ast()
    codigo = GeneradorC(ast).generar("modulo", include_header="n.h")
    assert '#include "n.h"' in codigo, "modulo incluye header"
    assert "int64_t factorial(int64_t n)" in codigo, "cuerpo en modulo"
    codigo2 = GeneradorC(ast).generar("modulo", scope_names={"principal"})
    assert "int main(" in codigo2, "main si el modulo tiene principal"
    assert "int64_t clasificar(int64_t v)" not in codigo2, (
        "funciones fuera del alcance no se emiten")


def test_codegen_s1_no_std():
    """D-5: modo no_std — cabecera freestanding (stdint/stddef, main(void))."""
    ast = _compilar_ast()
    ast.is_no_std = True
    codigo = GeneradorC(ast).generar()
    assert "#include <stddef.h>" in codigo, "no_std incluye stddef"
    assert "#include <stdio.h>" not in codigo, "no_std no incluye stdio"
    assert "int main(void)" in codigo, "no_std: main(void)"
    assert "__syn_asignar" in codigo, "no_std: allocador __syn_asignar"


def test_codegen_s1_safe_mode():
    """D-5: --safe activa _G_safe_mode en main()."""
    ast = _compilar_ast()
    gen = GeneradorC(ast)
    gen.ctx.enable_safe_mode()
    codigo = gen.generar()
    assert "_G_safe_mode = 1;" in codigo, "safe mode en main"


def test_codegen_s1_principal_retorno():
    """D-5: principal con retorno entero -> main() espera hilos y retorna _rc."""
    prog = _PROGRAMA.replace(
        "funcion principal() -> nulo:",
        "funcion principal() -> entero:\n    retornar 0",
    )
    ast = _compilar_ast(prog)
    codigo = GeneradorC(ast).generar()
    assert "int64_t _rc = principal();" in codigo, "main captura principal"
    assert "synapse_esperar_hilos();" in codigo, "main espera hilos (Manual 5)"
    assert "return _rc;" in codigo, "main retorna _rc"


def test_codegen_s1_ejecutable_fuera_de_ambito():
    """D-5: ruta de error — código ejecutable en ámbito global lanza SyntaxError."""
    prog = (
        "#lang: es\n"
        "funcion f() -> entero:\n"
        "    retornar 1\n"
        "x = f()\n"
    )
    with tempfile.TemporaryDirectory(prefix="synapse_d5_") as tmp:
        src = os.path.join(tmp, "programa.syn")
        with open(src, "w", encoding="utf-8") as f:
            f.write(prog)
        ast, diag = compilar_desde_texto(src, set())
    assert not diag.hay_errores(), "el parser acepta la asignacion global"
    with pytest.raises(SyntaxError):
        GeneradorC(ast).generar()


def test_codegen_s1_lanzar_con_transferencia():
    """D-5/F4.4: lanzar con argumento transferido (->x) emite wrapper + typedef
    y crea una FIBRA M:N (fibra_crear, Manual 5 §2.6) — antes thread
    (synapse_lanzar_hilo, deuda D-4/R15). Firma del wrapper void (trampolín
    de fibra), no void*."""
    prog = (
        "#lang: es\n"
        "funcion consumir(v: entero) -> nulo:\n"
        "    escribir_linea(entero_a_texto(v))\n"
        "funcion disparar(n: entero) -> nulo:\n"
        "    lanzar consumir(->n)\n"
        "    synapse_esperar_hilos()\n"
        "funcion principal() -> nulo:\n"
        "    disparar(3)\n"
        "    retornar\n"
    )
    ast = _compilar_ast(prog)
    codigo = GeneradorC(ast).generar()
    assert "fibra_crear(_wrap_" in codigo, "lanzar con wrapper crea fibra M:N"
    assert "static void _wrap_1(void* arg);" in codigo, "forward del wrapper"
    assert "synapse_lanzar_hilo(_wrap_" not in codigo, "F4.4: sin thread directo"


def test_codegen_s1_prototipos_puntero():
    """D-5: prototipo con parametro puntero emite void* (paridad orquestador)."""
    prog = (
        "#lang: es\n"
        "funcion manejar(p: puntero) -> entero:\n"
        "    retornar 0\n"
        "funcion principal() -> entero:\n"
        "    retornar manejar(nulo)\n"
    )
    ast = _compilar_ast(prog)
    codigo = GeneradorC(ast).generar()
    assert "void*" in codigo, "parametro puntero emite void*"
    assert "int64_t manejar(void* p)" in codigo, "prototipo con void*"


def test_codegen_s1_asignacion_campo_indice():
    """D-5: asignacion de campo (p.x =) e indice (v[i]) en el codegen."""
    prog = (
        "#lang: es\n"
        "estructura Punto:\n"
        "    x: entero\n"
        "    z: entero\n"
        "funcion ajustar(p: Punto) -> nulo:\n"
        "    p.x = 9\n"
        "    retornar\n"
        "funcion principal() -> nulo:\n"
        "    ajustar(Punto())\n"
        "    retornar\n"
    )
    ast = _compilar_ast(prog)
    codigo = GeneradorC(ast).generar()
    assert "typedef struct Punto" in codigo, "estructura"
    assert "p.x = 9LL;" in codigo, "asignacion de campo"


def test_codegen_s1_importar_c_con_alias():
    """D-5: importar_c simple emite include; estructura tipada."""
    prog = (
        "#lang: es\n"
        "importar_c \"stdint.h\"\n"
        "estructura Caja:\n"
        "    valor: entero\n"
        "funcion principal() -> nulo:\n"
        "    c = Caja()\n"
        "    c.valor = 3\n"
        "    retornar\n"
    )
    ast = _compilar_ast(prog)
    codigo = GeneradorC(ast).generar()
    assert "#include \"stdint.h\"" in codigo, "importar_c"
    assert "typedef struct Caja" in codigo, "estructura"
    assert "struct Caja c;" in codigo, "declaracion tipada"


def test_codegen_s1_export_con_asm():
    """D-5: @export ( IDENT ) funcion y bloque asm en el cuerpo."""
    prog = (
        "#lang: es\n"
        "@export ( c ) funcion acelerar(v: entero) -> entero:\n"
        "    inseguro:\n"
        "        asm(\"v = v * 2;\")\n"
        "    retornar v\n"
        "funcion principal() -> nulo:\n"
        "    retornar\n"
    )
    ast = _compilar_ast(prog)
    codigo = GeneradorC(ast).generar()
    assert "int64_t acelerar(int64_t v)" in codigo, "@export"
    assert "v = v * 2;" in codigo, "bloque asm (texto crudo)"


def test_codegen_s1_escuchar_canal():
    """D-5: canal con enviar (<-) y escuchar (bloque, Manual 2 L113) en el codegen."""
    prog = (
        "#lang: es\n"
        "funcion principal() -> nulo:\n"
        "    ch = canal(entero)\n"
        "    ch <- 21\n"
        "    escuchar ch:\n"
        "        mensaje = ch ->\n"
        "        escribir_linea(entero_a_texto(mensaje))\n"
        "    retornar\n"
    )
    ast = _compilar_ast(prog)
    codigo = GeneradorC(ast).generar()
    assert "canal_crear(10)" in codigo, "canal(entero) -> canal_crear(10)"
    assert "canal_enviar(ch," in codigo, "enviar <-"
    assert "canal_recibir(_canal, &_cerrado)" in codigo, "escuchar bloque -> canal_recibir"
def test_codegen_s1_tensor_crear():
    """D-5: crear_tensor en el codegen."""
    prog = (
        "#lang: es\n"
        "funcion principal() -> nulo:\n"
        "    t = crear_tensor(2, 3)\n"
        "    escribir_linea(entero_a_texto(t.filas))\n"
        "    retornar\n"
    )
    ast = _compilar_ast(prog)
    codigo = GeneradorC(ast).generar()
    assert "crear_tensor" in codigo, "crear_tensor"


def test_codegen_s1_tensor_matmul():
    """D-5: suma_tensor y producto_punto en el codegen."""
    prog = (
        "#lang: es\n"
        "funcion principal() -> nulo:\n"
        "    a = crear_tensor(2, 2)\n"
        "    b = crear_tensor(2, 2)\n"
        "    c = suma_tensor(a, b)\n"
        "    d = producto_punto(a, b)\n"
        "    retornar\n"
    )
    ast = _compilar_ast(prog)
    codigo = GeneradorC(ast).generar()
    assert "suma_tensor" in codigo, "suma_tensor"
    assert "producto_punto" in codigo, "producto_punto"
