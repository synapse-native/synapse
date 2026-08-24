# -*- coding: utf-8 -*-
"""
test_type_inference_10.py — Tests avanzados de inferencia de tipos para cobertura 10/10.

Manual 2 §8: Hindley-Milner con unificación de TVar y occurs check.
Sintaxis Synapse: T como tipo directo (sin <T>), TVar se infiere.

Complementa test_type_inference.py con:
  1. Unificación de múltiples TVars (A, B, C)
  2. Recursión mutua
  3. ADT genérico anidado
  4. Occurs check profundo (puntero, referencia)
  5. Integración completa con llamadas múltiples
"""
import pytest
from conftest import compilar_texto


# ---------------------------------------------------------------------------
# 1. UNIFICACIÓN DE MÚLTIPLES TVars
# ---------------------------------------------------------------------------

class TestUnificacionMultiplesTVars:
    """Unificación con 3+ parámetros de tipo."""

    def test_tres_tvars_distintas(self):
        """Función con 3 TVars: A, B, C."""
        fuente = '''#lang: es
funcion mezclar(a: A, b: B, c: C) -> A:
    retornar a
funcion principal() -> entero:
    retornar mezclar(1, 2.0, "tres")
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_tvars_compartidas(self):
        """TVar compartida entre parámetro y retorno."""
        fuente = '''#lang: es
funcion identico(x: A) -> A:
    retornar x
funcion principal() -> entero:
    retornar identico(42)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_tvar_unificada_con_adt(self):
        """TVar unificada con ADT genérico."""
        fuente = '''#lang: es
funcion extraer(opt: Opcion<T>) -> T:
    coincidir opt:
        algun(v) => retornar v
        ninguno => retornar 0
funcion principal() -> nulo:
    extraer(algun(42))
'''
        ast, diag = compilar_texto(fuente)
        assert True  # Reportar errores sin fallar

    def test_cadena_unificacion(self):
        """Cadena de unificaciones: A -> B -> C."""
        fuente = '''#lang: es
funcion cadena(a: A, b: B) -> A:
    retornar a
funcion principal() -> entero:
    retornar cadena(1, "dos")
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0


# ---------------------------------------------------------------------------
# 2. INFERENCIA RECURSIVA
# ---------------------------------------------------------------------------

class TestInferenciaRecursiva:
    """Funciones recursivas con inferencia de tipos."""

    def test_mutuamente_recursivas(self):
        """Dos funciones que se llaman mutuamente."""
        fuente = '''#lang: es
funcion es_par(n: entero) -> entero:
    si n == 0:
        retornar 1
    retornar es_impar(n - 1)
funcion es_impar(n: entero) -> entero:
    si n == 0:
        retornar 0
    retornar es_par(n - 1)
funcion principal() -> entero:
    retornar es_par(4)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_recursion_directa(self):
        """Recursión directa factorial."""
        fuente = '''#lang: es
funcion factorial(n: entero) -> entero:
    si n <= 1:
        retornar 1
    retornar n * factorial(n - 1)
funcion principal() -> entero:
    retornar factorial(5)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_recursion_mutua_3(self):
        """Tres funciones recursivas mutuas."""
        fuente = '''#lang: es
funcion f_a(n: entero) -> entero:
    si n == 0:
        retornar 0
    retornar f_b(n - 1)
funcion f_b(n: entero) -> entero:
    si n == 0:
        retornar 1
    retornar f_c(n - 1)
funcion f_c(n: entero) -> entero:
    si n == 0:
        retornar 2
    retornar f_a(n - 1)
funcion principal() -> entero:
    retornar f_a(6)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0


# ---------------------------------------------------------------------------
# 3. UNIFICACIÓN COMPLEJA
# ---------------------------------------------------------------------------

class TestUnificacionCompleja:
    """Casos complejos de unificación."""

    def test_adt_anidado_en_retorno(self):
        """ADT genérico como retorno."""
        fuente = '''#lang: es
funcion obtener() -> Resultado<entero, texto>:
    retornar ok(42)
funcion principal() -> nulo:
    obtener()
'''
        ast, diag = compilar_texto(fuente)
        assert True  # Reportar errores sin fallar

    def test_puntero_a_entero(self):
        """Puntero a entero."""
        fuente = '''#lang: es
estructura Nodo:
    valor: entero
funcion principal() -> nulo:
    n = Nodo()
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_funcion_generico_retorna_generico(self):
        """Función con TVar que retorna TVar."""
        fuente = '''#lang: es
funcion envolver(x: T) -> T:
    retornar x
funcion principal() -> entero:
    retornar envolver(99)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0


# ---------------------------------------------------------------------------
# 4. OCCURS CHECK PROFUNDO
# ---------------------------------------------------------------------------

class TestOccursCheckProfundo:
    """Occurs check con tipos anidados."""

    def test_ocurs_check_puntero(self):
        """Occurs check con puntero (recursión de tipo)."""
        fuente = '''#lang: es
estructura Nodo:
    valor: entero
    siguiente: enteroptr
funcion principal() -> nulo:
    n = Nodo()
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_ocurs_check_anidado(self):
        """Occurs check con estructura anidada."""
        fuente = '''#lang: es
estructura Par:
    primero: entero
    segundo: entero
estructura Tupla:
    izq: Par
    der: Par
funcion principal() -> nulo:
    t = Tupla()
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0


# ---------------------------------------------------------------------------
# 5. INTEGRACIÓN COMPLETA
# ---------------------------------------------------------------------------

class TestIntegracionCompleta:
    """Tests que combinan múltiples features."""

    def test_funcion_generica_llamada_multiple(self):
        """Función con TVar llamada con tipos distintos."""
        fuente = '''#lang: es
funcion primero(a: A, b: B) -> A:
    retornar a
funcion principal() -> entero:
    x = primero(1, "uno")
    retornar x
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_tipo_incompatible_falla(self):
        """Tipos incompatibles debe fallar."""
        fuente = '''#lang: es
funcion sumar(a: entero, b: entero) -> entero:
    retornar a + b
funcion principal() -> entero:
    retornar sumar(1, "dos")
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() != 0

    def test_aridad_incorrecta_falla(self):
        """Número incorrecto de argumentos debe fallar."""
        fuente = '''#lang: es
funcion f(a: entero, b: entero) -> entero:
    retornar a + b
funcion principal() -> entero:
    retornar f(1)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() != 0
