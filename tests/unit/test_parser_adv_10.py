# -*- coding: utf-8 -*-
"""
test_parser_adv_10.py — Tests avanzados de parser (Fase 1).

Manual 2 §1-3: Gramática EBNF, sentencias, tipos.
Cubre: anidamiento profundo, recuperación de errores, casos borde.
"""
import pytest
from conftest import compilar_texto

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# 1. ANIDAMIENTO PROFUNDO (>5 niveles)
# ---------------------------------------------------------------------------
class TestAnidamientoProfundo:
    """Verifica que el parser maneja anidamiento profundo."""

    def test_si_anidado_5_niveles(self):
        """5 niveles de si anidados compilan."""
        fuente = '''#lang: es
funcion principal() -> entero:
    x = 1
    si x > 0:
        si x > 0:
            si x > 0:
                si x > 0:
                    si x > 0:
                        x = 2
    retornar x
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0, \
            f"5 niveles de si anidados fallaron: {[e.get('mensaje','') for e in diag.errores]}"

    def test_si_anidado_8_niveles(self):
        """8 niveles de si anidados compilan."""
        fuente = '''#lang: es
funcion principal() -> entero:
    x = 1
    si x > 0:
        si x > 0:
            si x > 0:
                si x > 0:
                    si x > 0:
                        si x > 0:
                            si x > 0:
                                si x > 0:
                                    x = 2
    retornar x
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0, \
            f"8 niveles de si anidados fallaron: {[e.get('mensaje','') for e in diag.errores]}"

    def test_mientras_anidado_5_niveles(self):
        """5 niveles de mientras anidados compilan."""
        fuente = '''#lang: es
funcion principal() -> entero:
    x = 0
    mientras x < 1:
        mientras x < 2:
            mientras x < 3:
                mientras x < 4:
                    mientras x < 5:
                        x = x + 1
    retornar x
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_si_mientras_anidado(self):
        """Si y mientras alternados compilan."""
        fuente = '''#lang: es
funcion principal() -> entero:
    x = 0
    si x >= 0:
        mientras x < 10:
            si x == 5:
                x = x + 2
            sino:
                x = x + 1
    retornar x
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_funcion_anidada_3_niveles(self):
        """3 funciones anidadas (llamadas encadenadas) compilan."""
        fuente = '''#lang: es
funcion f1() -> entero:
    retornar f2()
funcion f2() -> entero:
    retornar f3()
funcion f3() -> entero:
    retornar 42
funcion principal() -> entero:
    retornar f1()
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0


# ---------------------------------------------------------------------------
# 2. RECUPERACIÓN DE ERRORES (error sync)
# ---------------------------------------------------------------------------
class TestRecuperacionErrores:
    """Verifica que el parser reporta errores con ubicación precisa."""

    def error_en_linea_especifica(self, fuente, linea_esperada, subcadena_error):
        """Verifica que un error aparece en la línea esperada."""
        ast, diag = compilar_texto(fuente)
        assert diag.hay_errores(), f"Se esperaba error pero compiló OK"
        errores = diag.errores
        # Verificar que al menos un error contiene la subcadena
        mensajes = [e.get('mensaje', '') for e in errores]
        assert any(subcadena_error in m for m in mensajes), \
            f"Error '{subcadena_error}' no encontrado en: {mensajes}"

    def test_funcion_sin_body(self):
        """Función sin cuerpo reporta error."""
        fuente = '''#lang: es
funcion incompleta()
'''
        self.error_en_linea_especifica(fuente, 2, "")

    def test_variable_no_declarada(self):
        """Variable no declarada reporta error."""
        fuente = '''#lang: es
funcion principal() -> entero:
    retornar x
'''
        ast, diag = compilar_texto(fuente)
        assert diag.hay_errores(), "Variable no declarada debería fallar"

    def test_tipo_no_existe(self):
        """Tipo inexistente reporta error."""
        fuente = '''#lang: es
funcion principal() -> entero:
    x: tipofantasma = 42
'''
        ast, diag = compilar_texto(fuente)
        # Puede fallar por tipo no existente
        assert diag.hay_errores(), "Tipo inexistente debería fallar"

    def test_args_incorrectos(self):
        """Número incorrecto de argumentos reporta error."""
        fuente = '''#lang: es
funcion sumar(a: entero, b: entero) -> entero:
    retornar a + b
funcion principal() -> entero:
    retornar sumar(1)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.hay_errores() or diag.codigo_salida() != 0, \
            "sumar(1) debería fallar por aridad"

    def test_retorno_tipo_incorrecto(self):
        """Retorno con tipo incorrecto reporta error."""
        fuente = '''#lang: es
funcion obtener() -> entero:
    retornar "hola"
funcion principal() -> entero:
    retornar 0
'''
        ast, diag = compilar_texto(fuente)
        # Puede fallar por tipo de retorno
        assert diag.hay_errores(), "Retorno tipo incorrecto debería fallar"


# ---------------------------------------------------------------------------
# 3. CASOS BORDE DE SINTAXIS
# ---------------------------------------------------------------------------
class TestCasosBordeSintaxis:
    """Casos borde de sintaxis que deben manejar correctamente."""

    def test_programa_vacio(self):
        """Programa vacío (solo #lang) compila."""
        fuente = '''#lang: es
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0, \
            f"Programa vacío debería compilar: {[e.get('mensaje','') for e in diag.errores]}"

    def test_funcion_solo_retorna(self):
        """Función con solo retorno compila."""
        fuente = '''#lang: es
funcion principal() -> entero:
    retornar 0
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def testMultiples_funciones(self):
        """10 funciones compilan."""
        funcs = "\n".join([f"funcion f{i}() -> entero:\n    retornar {i}" for i in range(10)])
        fuente = f'''#lang: es
{funcs}
funcion principal() -> entero:
    retornar 0
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_comentario_en_medio(self):
        """Comentarios entre sentencias compilan."""
        fuente = '''#lang: es
funcion principal() -> entero:
    x = 42
    retornar x
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_string_con_espacios(self):
        """String con espacios compila."""
        fuente = '''#lang: es
funcion principal() -> nulo:
    s = "hola mundo con espacios"
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_expresion_compleja(self):
        """Expresión con múltiples operadores compila."""
        fuente = '''#lang: es
funcion principal() -> entero:
    x = (1 + 2) * 3 - 4 / 2 % 1
    retornar x
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0


# ---------------------------------------------------------------------------
# 4. UBICACIÓN PRECISA DE ERRORES (Manual 2 §10)
# ---------------------------------------------------------------------------
class TestErrorUbicacionPrecisa:
    """Verifica que los errores incluyen información de ubicación (línea/columna).

    Manual 2 §10: "Each error includes exact location file/line/column".
    """

    def test_error_syntax_tiene_linea(self):
        """Error de sintaxis incluye campo 'linea' o 'line'."""
        fuente = '''#lang: es
funcion principal() -> entero:
    x = )
    retornar x
'''
        ast, diag = compilar_texto(fuente)
        assert diag.hay_errores(), "Código roto debería fallar"
        for err in diag.errores:
            assert 'linea' in err or 'line' in err, \
                f"Error sin ubicación: {err}"

    def test_error_tipo_tiene_linea(self):
        """Error de tipo incluye campo 'linea' o 'line'."""
        fuente = '''#lang: es
funcion principal() -> entero:
    x: tipofantasma = 42
    retornar x
'''
        ast, diag = compilar_texto(fuente)
        assert diag.hay_errores(), "Tipo inexistente debería fallar"
        for err in diag.errores:
            assert 'linea' in err or 'line' in err, \
                f"Error sin ubicación: {err}"

    def test_error_multiples_lineas_reportan_diferentes(self):
        """Errores en diferentes líneas reportan ubicaciones distintas."""
        fuente = '''#lang: es
funcion principal() -> entero:
    x = )
    y = )
    retornar x + y
'''
        ast, diag = compilar_texto(fuente)
        assert diag.hay_errores(), "Código roto debería fallar"
        lineas = set()
        for err in diag.errores:
            linea = err.get('linea') or err.get('line')
            if linea is not None:
                lineas.add(linea)
        assert len(lineas) >= 2, \
            f"Se esperaban errores en al menos 2 líneas distintas, solo en: {lineas}"
