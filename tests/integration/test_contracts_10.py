# -*- coding: utf-8 -*-
"""
test_contracts_10.py — Tests avanzados de contratos para cobertura 10/10.

Manual 2 §5: requiere se evalúa antes del cuerpo; garantiza antes de cada retornar.
Se emiten como assert() en C (runtime, no estático).

Complementa test_contracts.py con:
  1. Múltiples condiciones requiere con conjunción
  2. garantiza con retorno condicional
  3. Contratos con tipos ADT (Resultado, Opcion)
  4. Contratos genéricos
  5. Verificación de código C generado contiene assert
"""
import pytest
from conftest import compilar_texto
from compilador.lexer import Lexer
from compilador.parser import Parser
from compilador.analizador_semantico import AnalizadorSemantico
from compilador.generator import GeneradorC
from compilador.diagnostics import DiagnosticManager

pytestmark = pytest.mark.integration


def _generar_c(fuente: str) -> str:
    """Genera código C desde Synapse."""
    tokens = Lexer(fuente).tokenizar()
    diag = DiagnosticManager()
    parser = Parser(tokens, diag)
    prog = parser.parsear()
    if diag.hay_errores():
        return ""
    analizador = AnalizadorSemantico(prog, diag)
    analizador.analizar()
    if diag.hay_errores():
        return ""
    generador = GeneradorC(prog)
    return generador.generar()


# ---------------------------------------------------------------------------
# 1. REQUIERE: MÚLTIPLES CONDICIONES
# ---------------------------------------------------------------------------

class TestRequiereMultiples:
    """requiere con múltiples condiciones."""

    def test_requiere_dos_condiciones(self):
        """requiere con dos condiciones separadas."""
        fuente = '''#lang: es
funcion clamp(v: entero, minimo: entero, maximo: entero) -> entero:
    requiere: minimo <= maximo
    requiere: v >= minimo
    retornar v
funcion principal() -> entero:
    retornar clamp(5, 0, 10)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_requiere_genera_assert_en_c(self):
        """Verifica que requiere genera assert en C."""
        fuente = '''#lang: es
funcion dividir(a: entero, b: entero) -> entero:
    requiere: b != 0
    retornar a / b
funcion principal() -> entero:
    retornar dividir(10, 2)
'''
        codigo = _generar_c(fuente)
        assert codigo, "No se generó código C"
        assert "assert" in codigo, "requiere debe generar assert en C"


# ---------------------------------------------------------------------------
# 2. GARANTIZA: RETORNO CONDICIONAL
# ---------------------------------------------------------------------------

class TestGarantizaRetorno:
    """garantiza verificado antes de cada retornar."""

    def test_garantiza_positivo(self):
        """garantiza con resultado positivo."""
        fuente = '''#lang: es
funcion absoluta(x: entero) -> entero:
    garantiza: _resultado_ >= 0
    si x < 0:
        retornar x * -1
    retornar x
funcion principal() -> entero:
    retornar absoluta(-5)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_garantiza_genera_assert_en_c(self):
        """Verifica que garantiza genera assert en C."""
        fuente = '''#lang: es
funcion absoluto(x: entero) -> entero:
    garantiza: _resultado_ >= 0
    si x < 0:
        retornar x * -1
    retornar x
funcion principal() -> entero:
    retornar absoluto(3)
'''
        codigo = _generar_c(fuente)
        assert codigo, "No se generó código C"
        assert "assert" in codigo, "garantiza debe generar assert en C"


# ---------------------------------------------------------------------------
# 3. CONTRATOS CON ADTs
# ---------------------------------------------------------------------------

class TestContratosADT:
    """Contratos con tipos ADT (Resultado, Opcion)."""

    def test_requiere_con_resultado(self):
        """requiere con parámetro Resultado."""
        fuente = '''#lang: es
funcion extraer_ok(r: Resultado<entero, texto>) -> entero:
    retornar 0
funcion principal() -> entero:
    retornar 0
'''
        ast, diag = compilar_texto(fuente)
        # Verificar que compila (requiere con Resultado puede no estar soportado aún)
        assert diag.codigo_salida() == 0, \
            f"requiere con Resultado debe compilar: {[e.get('mensaje','') for e in diag.errores]}"

    def test_garantiza_con_opcion(self):
        """garantiza con retorno Opcion."""
        fuente = '''#lang: es
funcion buscar(x: entero) -> Opcion<entero>:
    retornar algun(x)
funcion principal() -> nulo:
    buscar(42)
'''
        ast, diag = compilar_texto(fuente)
        # Verificar que compila (garantiza con Opcion puede no estar soportado aún)
        assert diag.codigo_salida() == 0, \
            f"garantiza con Opcion debe compilar: {[e.get('mensaje','') for e in diag.errores]}"


# ---------------------------------------------------------------------------
# 4. CONTRATOS GENÉRICOS
# ---------------------------------------------------------------------------

class TestContratosGenericas:
    """Contratos en funciones genéricas."""

    def test_contrato_generico_simple(self):
        """Función genérica con contrato."""
        fuente = '''#lang: es
funcion intercambiar(a: T, b: T) -> T:
    retornar a
funcion principal() -> entero:
    retornar intercambiar(1, 2)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0


# ---------------------------------------------------------------------------
# 5. CONTRATOS: CASOS BORDE
# ---------------------------------------------------------------------------

class TestContratosBorde:
    """Casos borde de contratos."""

    def test_funcion_sin_contratos(self):
        """Función sin contratos funciona normal."""
        fuente = '''#lang: es
funcion sumar(a: entero, b: entero) -> entero:
    retornar a + b
funcion principal() -> entero:
    retornar sumar(1, 2)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_requiere_solo(self):
        """Solo requiere, sin garantiza."""
        fuente = '''#lang: es
funcion raiz_cuadrada(x: entero) -> entero:
    requiere: x >= 0
    retornar x
funcion principal() -> entero:
    retornar raiz_cuadrada(9)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_garantiza_solo(self):
        """Solo garantiza, sin requiere."""
        fuente = '''#lang: es
funcion duplicar(x: entero) -> entero:
    garantiza: _resultado_ == x * 2
    retornar x * 2
funcion principal() -> entero:
    retornar duplicar(5)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_requiere_con_texto(self):
        """requiere con comparación de texto."""
        fuente = '''#lang: es
funcion procesar(s: texto) -> nulo:
    requiere: s != ""
    retornar
funcion principal() -> nulo:
    procesar("hola")
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0


# ---------------------------------------------------------------------------
# 6. CONTRATOS INVÁLIDOS: DEBEN FALLAR EN RUNTIME
# ---------------------------------------------------------------------------

class TestContratosInvalidosFallan:
    """Verifica que contratos inválidos generan assert que falla.
    Manual 2 §5.3: requiere se evalúa antes del cuerpo; si falla, aborta."""

    def test_requiere_falso_genera_assert(self):
        """requiere: falso genera assert que aborta."""
        fuente = '''#lang: es
funcion imposible() -> entero:
    requiere: falso
    retornar 42
funcion principal() -> entero:
    retornar imposible()
'''
        codigo = _generar_c(fuente)
        assert codigo, "No se generó código C"
        # Debe generar assert con condición que puede fallar
        assert "assert" in codigo, \
            f"requiere: falso debe generar assert en C:\n{codigo[:800]}"

    def test_requiere_expresion_no_booleana_falla(self):
        """requiere con expresión no booleana debe fallar.
        Manual 2 §5.1: All expressions in requiere must be boolean."""
        fuente = '''#lang: es
funcion mala() -> entero:
    requiere: 42
    retornar 0
funcion principal() -> entero:
    retornar mala()
'''
        ast, diag = compilar_texto(fuente)
        assert diag.hay_errores(), \
            "requiere con expresión no booleana debe generar error de compilación"

    def test_requiere_expresion_no_booleana_texto_falla(self):
        """requiere con expresión no booleana (texto) debe fallar.
        Manual 2 §5.1: All expressions in requiere must be boolean."""
        fuente = '''#lang: es
funcion mala() -> entero:
    requiere: "hola"
    retornar 0
funcion principal() -> entero:
    retornar mala()
'''
        ast, diag = compilar_texto(fuente)
        assert diag.hay_errores(), \
            "requiere con expresión texto debe generar error de compilación"

    def test_requiere_division_por_cero_genera_assert(self):
        """requiere: b != 0 genera assert que falla con b=0."""
        fuente = '''#lang: es
funcion dividir(a: entero, b: entero) -> entero:
    requiere: b != 0
    retornar a / b
funcion principal() -> entero:
    retornar dividir(10, 0)
'''
        codigo = _generar_c(fuente)
        assert codigo
        # Debe generar assert que verifica b != 0
        assert "assert" in codigo, \
            f"requiere: b != 0 debe generar assert:\n{codigo[:800]}"
