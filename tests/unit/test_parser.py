# -*- coding: utf-8 -*-
"""Tests unitarios del parser S1 (checklist FASE 1, 1.5/1.6).

Manual 2 §12 — Parser EBNF: `pytest tests/unit/test_parser.py -v`
con 100% pass y >95% cobertura de compilador/parser.py.
Criterio 1.6: los errores de sintaxis reportan ubicación precisa
(línea y columna) a través de DiagnosticManager.
"""
from compilador.lexer import Lexer
from compilador.parser import Parser
import pytest

pytestmark = pytest.mark.unit
from compilador.ast_nodes import (
    TokenID, Nodo, SentenciaSi, AsignacionVariable,
    OpBinaria, OpUnaria, DeclaracionVariable, DefinicionFuncion,
    DefinicionEstructura, DeclaracionTipo, DeclaracionExport,
    SentenciaRecuperar, SentenciaLanzar, SentenciaDelegar,
    SentenciaEnviarCanal, ExprRecibirCanal, SentenciaEscuchar,
    SentenciaMientras, SentenciaPara, SentenciaRomper, SentenciaSiguiente,
    SentenciaExpr, BloqueInseguro, NodoCoincidir,
    ExprCrearCanal, ExprTensor, ExprIndice, ExprAsm,
    LogLlamada, AsignacionCampo, StmtConstante, ImportarC,
    SentenciaImportar, DeclaracionExterna,
)
from compilador.diagnostics import DiagnosticManager, ErrorCodes


def _parsear(fuente: str):
    lexer = Lexer(fuente)
    tokens = lexer.tokenizar()
    diag = DiagnosticManager()
    parser = Parser(tokens, diag)
    prog = parser.parsear()
    return prog, diag


def _funcion(prog, nombre: str) -> DefinicionFuncion:
    for s in prog.sentencias:
        if isinstance(s, DefinicionFuncion) and s.nombre == nombre:
            return s
    raise AssertionError("funcion '%s' no encontrada en el programa" % nombre)


class TestParserOperadoresFase0:
    def test_comparacion_menor_igual(self):
        prog, diag = _parsear("#lang: es\nx = 1 <= 2")
        assert not diag.hay_errores()
        assign = prog.sentencias[0]
        assert isinstance(assign, AsignacionVariable)
        assert isinstance(assign.expresion, OpBinaria)
        assert assign.expresion.operador == "<="

    def test_comparacion_mayor_igual(self):
        prog, diag = _parsear("#lang: es\nx = 1 >= 2")
        assert not diag.hay_errores()
        assign = prog.sentencias[0]
        assert isinstance(assign.expresion, OpBinaria)
        assert assign.expresion.operador == ">="

    def test_comparacion_distinto(self):
        prog, diag = _parsear("#lang: es\nx = 1 != 2")
        assert not diag.hay_errores()
        assign = prog.sentencias[0]
        assert isinstance(assign.expresion, OpBinaria)
        assert assign.expresion.operador == "!="

    def test_igualdad_vs_asignacion(self):
        prog_asign, _ = _parsear("#lang: es\nx = 10")
        assign = prog_asign.sentencias[0]
        assert isinstance(assign, AsignacionVariable)

        prog_igual, _ = _parsear("#lang: es\nx = 10 == 10")
        assign2 = prog_igual.sentencias[0]
        assert isinstance(assign2, AsignacionVariable)
        assert isinstance(assign2.expresion, OpBinaria)
        assert assign2.expresion.operador == "=="

    def test_unario_menos(self):
        prog, diag = _parsear("#lang: es\nx = -a")
        assert not diag.hay_errores()
        assign = prog.sentencias[0]
        assert isinstance(assign, AsignacionVariable)
        assert isinstance(assign.expresion, OpUnaria)
        assert assign.expresion.operador == "-"

    def test_punto_y_coma_separador(self):
        prog, diag = _parsear("#lang: es\nfuncion f() -> nulo:\n    a=10; b=20")
        assert not diag.hay_errores()

    def test_si_inline_operadores(self):
        prog, diag = _parsear("#lang: es\nsi a<=b: escribir_linea(\"OK\")")
        assert not diag.hay_errores()
        assert isinstance(prog.sentencias[0], SentenciaSi)

    def test_cadena_comparacion(self):
        prog, diag = _parsear('#lang: es\nx = "hola" == "hola"')
        assert not diag.hay_errores()
        assign = prog.sentencias[0]
        assert isinstance(assign, AsignacionVariable)


# ------------------------------------------------------ 1.5: programa extenso


PROGRAMA_EXTENSO = """#lang: es
importar std.io
importar_c "stdint.h"
externo funcion ayuda_externa(x: entero) -> entero

constante LIMITE = 10
constante LIMITE2: entero = 20

estructura Punto:
    x: entero
    z: entero

tipo Resultado<T, E> = ok(T) | err(E)
tipo Paridad = par(entero, texto) | impar(entero)
tipo AliasEntero = entero

@export ( c ) funcion exportada(x: entero) -> entero:
    retornar x * 2

funcion con_contrato(x: entero) -> entero:
    requiere:
        x > 0
    garantiza:
        _resultado_ >= 0
    retornar x + 1

funcion clasificar(v: entero) -> texto:
    coincidir paridad(v):
        par(x) => retornar "par"
        impar(x) => retornar "impar"

funcion usar_control(n: entero) -> entero:
    si n > 0:
        x = n
    sino:
        x = 0
    mientras x < 10:
        x = x + 1
        si x == 5:
            siguiente
        si x == 8:
            romper
    para i = 0 mientras i < n:
        x = x + i
        i = i + 1
    retornar x

funcion usar_canales() -> nulo:
    ch = canal(entero, 4)
    ch <- x
    val = ch ->
    let z: entero = ch ->
    escuchar ch:
        procesar(x)
    retornar

funcion usar_recuperar(v: texto) -> entero:
    texto_a_entero(v) recuperar: -1
    retornar -1

funcion usar_lanzar(n: entero) -> nulo:
    lanzar trabajar(n)
    retornar

funcion usar_let() -> nulo:
    let a = 1
    let b: entero = 2
    let c: entero
    retornar

funcion transferir(-> x: entero) -> entero:
    retornar -> x

funcion usar_asm() -> nulo:
    inseguro:
        asm("x = 1;")
    retornar

funcion usar_delegar(a: entero, b: entero) -> Resultado<entero,texto>:
    delegar dividir(a, b)
    retornar ok(0)

funcion usar_misc(v: entero) -> entero:
    log("evento", v)
    p = Punto()
    p.x = 9
    let q: entero = 7
    let ptr: entero* = nulo
    t = tensor(2, 3)
    r = t[0]
    retornar v

funcion principal() -> nulo:
    retornar
"""


class TestParserProgramaExtenso:
    def test_programa_extenso_sin_errores(self):
        prog, diag = _parsear(PROGRAMA_EXTENSO)
        assert not diag.hay_errores(), diag.errores
        assert len(prog.sentencias) >= 18

    def test_nodos_top_level(self):
        prog, _ = _parsear(PROGRAMA_EXTENSO)
        tipos = {type(s).__name__ for s in prog.sentencias}
        assert 'SentenciaImportar' in tipos
        assert 'ImportarC' in tipos
        assert 'DeclaracionExterna' in tipos
        assert 'StmtConstante' in tipos
        assert 'DefinicionEstructura' in tipos
        assert 'DeclaracionTipo' in tipos
        assert 'DeclaracionExport' in tipos
        assert 'DefinicionFuncion' in tipos

    def test_declaracion_tipo_generico(self):
        prog, _ = _parsear(PROGRAMA_EXTENSO)
        dt = next(s for s in prog.sentencias if isinstance(s, DeclaracionTipo))
        assert dt.nombre == 'Resultado'
        assert dt.parametros_tipo == ['T', 'E']
        assert [c.nombre for c in dt.constructores] == ['ok', 'err']
        assert [c.tipos for c in dt.constructores] == [['T'], ['E']]

    def test_declaracion_tipo_adt_y_alias(self):
        prog, _ = _parsear(PROGRAMA_EXTENSO)
        tipos = [s for s in prog.sentencias if isinstance(s, DeclaracionTipo)]
        paridad = next(t for t in tipos if t.nombre == 'Paridad')
        assert [c.nombre for c in paridad.constructores] == ['par', 'impar']
        alias = next(t for t in tipos if t.nombre == 'AliasEntero')
        assert alias.tipo_base == 'entero'

    def test_control_flujo(self):
        f = _funcion(_parsear(PROGRAMA_EXTENSO)[0], 'usar_control')
        tipos = {type(n).__name__ for n in f.cuerpo}
        assert 'SentenciaSi' in tipos
        assert 'SentenciaMientras' in tipos
        assert 'SentenciaPara' in tipos
        si = next(n for n in f.cuerpo if isinstance(n, SentenciaSi))
        assert si.cuerpo_sino is not None
        mientras = next(n for n in f.cuerpo if isinstance(n, SentenciaMientras))
        anidados = [n for n in mientras.cuerpo if isinstance(n, SentenciaSi)]
        # 'siguiente'/'romper' viven dentro de los 'si' anidados del cuerpo
        assert any(any(isinstance(x, SentenciaRomper)
                       or isinstance(x, SentenciaSiguiente)
                       for x in (si.cuerpo or [])) for si in anidados)

    def test_canales(self):
        f = _funcion(_parsear(PROGRAMA_EXTENSO)[0], 'usar_canales')
        # ch = canal(entero, 4) -> AsignacionVariable con ExprCrearCanal
        asign = next(n for n in f.cuerpo if isinstance(n, AsignacionVariable))
        assert isinstance(asign.expresion, ExprCrearCanal)
        assert asign.expresion.tipo_contenido == 'entero'
        assert any(isinstance(n, SentenciaEnviarCanal) for n in f.cuerpo)
        recib = next(n for n in f.cuerpo
                     if isinstance(n, AsignacionVariable)
                     and isinstance(n.expresion, ExprRecibirCanal))
        assert recib.nombre == 'val'
        assert any(isinstance(n, SentenciaEscuchar) for n in f.cuerpo)

    def test_recuperar(self):
        f = _funcion(_parsear(PROGRAMA_EXTENSO)[0], 'usar_recuperar')
        assert any(isinstance(n, SentenciaRecuperar) for n in f.cuerpo)

    def test_lanzar(self):
        f = _funcion(_parsear(PROGRAMA_EXTENSO)[0], 'usar_lanzar')
        assert any(isinstance(n, SentenciaLanzar) for n in f.cuerpo)

    def test_let(self):
        f = _funcion(_parsear(PROGRAMA_EXTENSO)[0], 'usar_let')
        lets = [n for n in f.cuerpo if isinstance(n, DeclaracionVariable)]
        assert len(lets) == 3
        assert lets[0].tipo == '' and lets[0].expresion is not None
        assert lets[1].tipo == 'entero' and lets[1].expresion is not None
        assert lets[2].tipo == 'entero' and lets[2].expresion is None

    def test_transferencia(self):
        f = _funcion(_parsear(PROGRAMA_EXTENSO)[0], 'transferir')
        assert f.parametros and f.parametros[0].es_transferencia is True
        ret = f.cuerpo[0]
        assert ret.es_transferencia is True

    def test_inseguro_asm(self):
        f = _funcion(_parsear(PROGRAMA_EXTENSO)[0], 'usar_asm')
        bloque = next(n for n in f.cuerpo if isinstance(n, BloqueInseguro))
        assert any(isinstance(n, SentenciaExpr) and isinstance(n.expr, ExprAsm)
                   and n.expr.instruccion == 'x = 1;' for n in bloque.cuerpo)

    def test_delegar(self):
        f = _funcion(_parsear(PROGRAMA_EXTENSO)[0], 'usar_delegar')
        assert any(isinstance(n, SentenciaDelegar) for n in f.cuerpo)
        assert f.tipo_retorno == 'Resultado<entero,texto>'

    def test_coincidir(self):
        f = _funcion(_parsear(PROGRAMA_EXTENSO)[0], 'clasificar')
        nodo = next(n for n in f.cuerpo if isinstance(n, NodoCoincidir))
        assert [c.patron for c in nodo.casos] == ['par(x)', 'impar(x)']

    def test_contratos(self):
        f = _funcion(_parsear(PROGRAMA_EXTENSO)[0], 'con_contrato')
        assert len(f.requiere) >= 1
        assert len(f.garantiza) >= 1

    def test_export(self):
        prog, _ = _parsear(PROGRAMA_EXTENSO)
        exp = next(s for s in prog.sentencias if isinstance(s, DeclaracionExport))
        assert exp.destino == 'c'
        assert exp.funcion is not None and exp.funcion.nombre == 'exportada'

    def test_misc(self):
        f = _funcion(_parsear(PROGRAMA_EXTENSO)[0], 'usar_misc')
        assert any(isinstance(n, LogLlamada) for n in f.cuerpo)
        assert any(isinstance(n, AsignacionCampo) for n in f.cuerpo)
        declaraciones = [n for n in f.cuerpo if isinstance(n, DeclaracionVariable)]
        assert declaraciones and declaraciones[0].tipo == 'entero'
        asig_tensor = next(n for n in f.cuerpo
                           if isinstance(n, AsignacionVariable)
                           and isinstance(n.expresion, ExprTensor))
        assert asig_tensor.nombre == 't'
        asig_indice = next(n for n in f.cuerpo
                           if isinstance(n, AsignacionVariable)
                           and isinstance(n.expresion, ExprIndice))
        assert asig_indice.nombre == 'r'


# ------------------------------------------------------ 1.6: errores con ubicación


class TestParserCasosLimite:
    def test_tipo_pipe_inicial(self):
        # RHS que comienza con '|': el parser entra en la rama defensiva pero
        # exige un identificador como primer constructor -> error controlado
        prog, diag = _parsear("#lang: es\ntipo Raro = | a | b")
        assert diag.hay_errores()

    def test_tipo_rhs_parentizado(self):
        prog, diag = _parsear("#lang: es\ntipo Agrupado = (a(entero) | b(texto))")
        assert not diag.hay_errores()
        dt = prog.sentencias[0]
        assert [c.nombre for c in dt.constructores] == ['a', 'b']
        assert [c.tipos for c in dt.constructores] == [['entero'], ['texto']]

    def test_tipo_genericos_incompletos(self):
        # '<T' sin cierre -> se esperaba GREATER (error de sintaxis, no crash)
        prog, diag = _parsear("#lang: es\ntipo Incompleto <T")
        assert diag.hay_errores()

    def test_tipo_sin_rhs(self):
        # 'tipo X |' -> se esperaba ASSIGN
        prog, diag = _parsear("#lang: es\ntipo X |")
        assert diag.hay_errores()

    def test_tipo_constructor_trailing_pipe(self):
        # 'ok(entero) |' -> tras el pipe falta el constructor (error, no crash)
        prog, diag = _parsear("#lang: es\ntipo X = ok(entero) |")
        assert diag.hay_errores()

    def test_recuperar_sin_dos_puntos(self):
        # 'expr recuperar' sin ':' -> error de sintaxis, no crash
        prog, diag = _parsear("#lang: es\nf() recuperar")
        assert diag.hay_errores()

    def test_declaracion_sin_let_rechazada(self):
        """F3-8 (Manual 2 L134): `ptr: entero* = nulo` SIN `let` se rechaza."""
        prog, diag = _parsear("#lang: es\nptr: entero* = nulo")
        assert diag.hay_errores()
        assert any(e['codigo'] == ErrorCodes.ERR_SYNTAX_EXPECTED_TOKEN
                   for e in diag.errores)

    def test_declaracion_con_let_puntero(self):
        """La forma VALIDA (Manual 2 L134): `let ptr: entero* = nulo`."""
        prog, diag = _parsear("#lang: es\nlet ptr: entero* = nulo")
        assert not diag.hay_errores()
        decl = prog.sentencias[0]
        assert isinstance(decl, DeclaracionVariable)
        assert decl.tipo == 'entero*'


class TestParserErroresUbicacion:
    def test_token_inesperado_tras_expresion(self):
        # ')' queda tras la llamada 'f()' -> ERR_SYNTAX_UNEXPECTED_TOKEN en (2, 5)
        prog, diag = _parsear("#lang: es\nf() )")
        assert diag.hay_errores()
        e = diag.errores[0]
        assert e['codigo'] == ErrorCodes.ERR_SYNTAX_UNEXPECTED_TOKEN
        assert e['linea'] == 2
        assert e['columna'] == 4

    def test_expresion_incompleta(self):
        # '1 +' sin operando -> ERR_SYNTAX_UNEXPECTED_EXPR en (2, 0) (NEWLINE)
        prog, diag = _parsear("#lang: es\nx = 1 +")
        assert diag.hay_errores()
        e = diag.errores[0]
        assert e['codigo'] == ErrorCodes.ERR_SYNTAX_UNEXPECTED_EXPR
        assert e['linea'] == 2

    def test_esperado_identificador(self):
        # 'funcion f( -> nulo:' -> se esperaba IDENTIFICADOR (el '->') en línea 2
        prog, diag = _parsear("#lang: es\nfuncion f( -> nulo:")
        assert diag.hay_errores()
        e = diag.errores[0]
        assert e['codigo'] == ErrorCodes.ERR_SYNTAX_EXPECTED_TOKEN
        assert e['linea'] == 2

    def test_let_sin_identificador(self):
        # 'let 3' -> se esperaba IDENTIFICADOR
        prog, diag = _parsear("#lang: es\nlet 3")
        assert diag.hay_errores()
        assert diag.errores[0]['codigo'] == ErrorCodes.ERR_SYNTAX_EXPECTED_TOKEN
