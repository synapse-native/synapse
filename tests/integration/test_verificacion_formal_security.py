"""
tests/integration/test_verificacion_formal.py — Pruebas de Verificación Formal (M10.1)

Suite de pruebas que intenta compilar código con violaciones de pureza,
recursión sin convergencia y mutaciones prohibidas bajo --safe, exigiendo
que el compilador rechace el código con los códigos de error exactos (ERR_VER_*).

Estructura:
  - test_safe_bucle_mientras_inacotado:    E-700
  - test_safe_mutacion_global:              E-701
  - test_safe_recursion_sin_convergencia:   E-702
  - test_safe_contrato_invalido:            E-703
  - test_safe_codigo_valido:                No debe emitir errores
  - test_safe_contrato_resultado_en_void:   E-703 (variante)
  - test_safe_funcion_pura_con_efectos:     E-701 (variante)
  - test_fuzzing_contratos:                 Fuzzing de contratos
"""

import os
import sys
import pytest

pytestmark = pytest.mark.integration

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from compilador.diagnostics import DiagnosticManager, ErrorCodes
from compilador.verificador_formal import VerificadorFormal
from conftest import compilar_texto


# ================================================================
# Fixtures: código fuente para pruebas
# NOTA: Usar 'funcion' (keyword español) porque los tests usan #lang: es
# ================================================================

# E-700: Bucle 'mientras' sin cota estática
CODIGO_WHILE_INACOTADO = """#lang: es

funcion bucle_infinito() -> nulo:
    mientras verdadero:
        escribir_linea("hola")
"""

# E-701: Asignación a nivel global (fuera de función)
CODIGO_MUTACION_GLOBAL = """#lang: es

x = 42
"""

# E-702: Recursión sin convergencia estructural
CODIGO_RECURSION_SIN_CONVERGENCIA = """#lang: es

funcion factorial_sin_base(n: entero) -> entero:
    retornar factorial_sin_base(n)
"""

# E-703: Contrato inválido (operación aritmética en requiere)
CODIGO_CONTRATO_INVALIDO = """#lang: es

funcion dividir(a: entero, b: entero) -> entero:
    requiere:
        a + b
    retornar a / b
"""

# Código válido en modo --safe (debe pasar sin errores)
# ME-R2: se agrego 'principal' para que el fragmento sea un programa completo
# compilable y enlazable. Sin entrada el pipeline no puede generar el exe y la
# propagacion de errores (antes tragada) devuelve RC=1, destapando el fallo
# preexistente de los tests de integracion con --safe.
CODIGO_VALIDO_SAFE = """#lang: es

funcion factorial(n: entero) -> entero:
    si n <= 1:
        retornar 1
    sino:
        retornar n * factorial(n - 1)

funcion principal() -> nulo:
    retornar
"""

# E-703: Contrato garantiza menciona _resultado_ en función void
CODIGO_CONTRATO_RESULTADO_EN_VOID = """#lang: es

funcion procesar(n: entero) -> nulo:
    garantiza:
        _resultado_ == nulo
    escribir_linea("procesando")
"""

# E-701: Función pura con bloque inseguro
CODIGO_PURA_CON_EFECTOS = """#lang: es

funcion pura_calculo(n: entero) -> entero:
    inseguro:
        asm("nop")
    retornar n
"""

# Código con contrato válido en modo --safe
CODIGO_CONTRATO_VALIDO = """#lang: es

funcion dividir_seguro(a: entero, b: entero) -> entero:
    requiere:
        b != 0
    garantiza:
        _resultado_ * b == a
    retornar a / b
"""

# Código con while acotado (válido en --safe)
CODIGO_WHILE_ACOTADO = """#lang: es

funcion procesar_hasta(n: entero) -> nulo:
    MAX = 100
    mientras n < MAX:
        escribir_linea("iterando")
        n = n + 1
"""


# ================================================================
# Helpers
# ================================================================

def _verificar_safe(fuente: str) -> DiagnosticManager:
    """Compila código en modo --safe y retorna el DiagnosticManager."""
    ast, diag = compilar_texto(fuente)
    if not diag.hay_errores():
        verificador = VerificadorFormal(ast, diag)
        verificador.verificar()
    return diag


def _tiene_error(diag: DiagnosticManager, codigo: ErrorCodes) -> bool:
    """Verifica si hay al menos un error con el código especificado."""
    return any(e['codigo'] == codigo for e in diag.errores)


def _contar_errores(diag: DiagnosticManager, codigo: ErrorCodes) -> int:
    """Cuenta cuántos errores con el código especificado hay."""
    return sum(1 for e in diag.errores if e['codigo'] == codigo)


# ================================================================
# Pruebas
# ================================================================

class TestVerificacionFormal:

    def test_safe_bucle_mientras_inacotado(self):
        """E-700: Bucle 'mientras' sin cota estática comprobable debe fallar."""
        diag = _verificar_safe(CODIGO_WHILE_INACOTADO)
        assert _tiene_error(diag, ErrorCodes.ERR_VER_WHILE_INACOTADO), \
            "Debe reportar ERR_VER_WHILE_INACOTADO (E-700) para bucle 'mientras' sin cota"

    def test_safe_mutacion_global(self):
        """E-701: Asignación a variable global (fuera de función) prohibida en modo --safe."""
        diag = _verificar_safe(CODIGO_MUTACION_GLOBAL)
        assert _tiene_error(diag, ErrorCodes.ERR_VER_MUTACION_GLOBAL), \
            "Debe reportar ERR_VER_MUTACION_GLOBAL (E-701) para asignación global"

    def test_safe_recursion_sin_convergencia(self):
        """E-702: Recursión sin convergencia estructural debe fallar."""
        diag = _verificar_safe(CODIGO_RECURSION_SIN_CONVERGENCIA)
        assert _tiene_error(diag, ErrorCodes.ERR_VER_RECURSION_NO_TERMINAL), \
            "Debe reportar ERR_VER_RECURSION_NO_TERMINAL (E-702) para recursión sin caso base"

    def test_safe_contrato_invalido(self):
        """E-703: Contrato con expresión aritmética inválida debe fallar."""
        diag = _verificar_safe(CODIGO_CONTRATO_INVALIDO)
        assert _tiene_error(diag, ErrorCodes.ERR_VER_CONTRATO_INVALIDO), \
            "Debe reportar ERR_VER_CONTRATO_INVALIDO (E-703) para contrato con operación aritmética"

    def test_safe_contrato_resultado_en_void(self):
        """E-703: Contrato garantiza mencionando _resultado_ en función void debe fallar."""
        diag = _verificar_safe(CODIGO_CONTRATO_RESULTADO_EN_VOID)
        assert _tiene_error(diag, ErrorCodes.ERR_VER_CONTRATO_INVALIDO), \
            "Debe reportar ERR_VER_CONTRATO_INVALIDO (E-703) cuando garantiza usa _resultado_ en función void"

    def test_safe_funcion_pura_con_efectos(self):
        """E-701: Función pura con bloque inseguro debe fallar."""
        diag = _verificar_safe(CODIGO_PURA_CON_EFECTOS)
        assert _tiene_error(diag, ErrorCodes.ERR_VER_MUTACION_GLOBAL), \
            "Debe reportar ERR_VER_MUTACION_GLOBAL (E-701) para función pura con bloque inseguro"

    def test_safe_codigo_valido(self):
        """Código válido con recursión estructural debe pasar sin errores."""
        diag = _verificar_safe(CODIGO_VALIDO_SAFE)
        assert not diag.hay_errores(), \
            f"Código válido no debe reportar errores, pero reportó: {diag.resumen()}"

    def test_safe_contrato_valido(self):
        """Código con contratos válidos debe pasar sin errores."""
        diag = _verificar_safe(CODIGO_CONTRATO_VALIDO)
        # Puede haber errores semánticos (tipos) porque _resultado_*b==a no es válido en Synapse,
        # pero NO debe haber ERR_VER_CONTRATO_INVALIDO
        assert not _tiene_error(diag, ErrorCodes.ERR_VER_CONTRATO_INVALIDO), \
            "Contratos válidos no deben reportar ERR_VER_CONTRATO_INVALIDO"

    def test_safe_while_acotado(self):
        """Bucle 'mientras' con cota estática debe ser aceptado."""
        diag = _verificar_safe(CODIGO_WHILE_ACOTADO)
        assert not _tiene_error(diag, ErrorCodes.ERR_VER_WHILE_INACOTADO), \
            "Bucle 'mientras' con cota estática (n < MAX) no debe reportar E-700"

    def test_safe_sin_errores_falsos_positivos(self):
        """Código sin violaciones no debe generar errores de verificación."""
        codigo = """#lang: es

funcion suma(a: entero, b: entero) -> entero:
    retornar a + b

funcion principal() -> nulo:
    escribir_linea("Hola desde modo --safe")
"""
        diag = _verificar_safe(codigo)
        ver_errors = [
            ErrorCodes.ERR_VER_WHILE_INACOTADO,
            ErrorCodes.ERR_VER_MUTACION_GLOBAL,
            ErrorCodes.ERR_VER_RECURSION_NO_TERMINAL,
            ErrorCodes.ERR_VER_CONTRATO_INVALIDO,
        ]
        for ver_err in ver_errors:
            assert not _tiene_error(diag, ver_err), \
                f"No debe reportar {ver_err.name} para código sin violaciones"


# ================================================================
# Fuzzing de contratos
# ================================================================

class TestFuzzingContratos:

    @pytest.mark.parametrize("codigo,debe_fallar", [
        # Contratos inválidos (operación aritmética en requiere)
        ('#lang: es\nfuncion test_arit(a: entero, b: entero) -> entero:\n    requiere:\n        a + b\n    retornar a\n', True),
        ('#lang: es\nfuncion test_mult(a: entero, b: entero) -> entero:\n    requiere:\n        a * b\n    retornar a\n', True),
        ('#lang: es\nfuncion test_io_en_contrato() -> nulo:\n    requiere:\n        leer_linea()\n    escribir_linea("ok")\n', True),
        # Contratos válidos
        ('#lang: es\nfuncion test_cmp(a: entero, b: entero) -> entero:\n    requiere:\n        a > 0\n    retornar a + b\n', False),
        ('#lang: es\nfuncion test_eq(a: entero, b: entero) -> entero:\n    requiere:\n        a == b\n    retornar a\n', False),
        ('#lang: es\nfuncion test_and(a: entero, b: entero) -> entero:\n    requiere:\n        a > 0 y b > 0\n    retornar a + b\n', False),
    ])
    def test_fuzzing_contratos(self, codigo, debe_fallar):
        """Prueba parametrizada de fuzzing de contratos."""
        diag = _verificar_safe(codigo)
        tiene_error_contrato = _tiene_error(diag, ErrorCodes.ERR_VER_CONTRATO_INVALIDO)
        if debe_fallar:
            assert tiene_error_contrato, \
                f"El código debería fallar con ERR_VER_CONTRATO_INVALIDO:\n{codigo}\nErrores: {diag.errores}"
        else:
            assert not tiene_error_contrato, \
                f"El código no debería fallar:\n{codigo}\nErrores: {diag.errores}"


# ================================================================
# Pruebas de integración con el pipeline completo
# ================================================================

class TestIntegracionSafe:

    def test_pipeline_safe_flag(self):
        """Verifica que el pipeline acepte y procese el flag --safe."""
        from pipeline import ejecutar_compilador
        import tempfile

        with tempfile.NamedTemporaryFile(mode='w', suffix='.syn', delete=False, encoding='utf-8') as f:
            f.write(CODIGO_VALIDO_SAFE)
            temp_path = f.name

        try:
            # Con --safe debe pasar (el código es válido)
            codigo = ejecutar_compilador(temp_path, modo_safe=True)
            assert codigo == 0, f"Pipeline con --safe debe retornar 0, pero retornó {codigo}"
        finally:
            os.unlink(temp_path)

    def test_pipeline_safe_flag_rechaza(self):
        """Verifica que el pipeline rechace código inválido con --safe."""
        from pipeline import ejecutar_compilador
        import tempfile

        with tempfile.NamedTemporaryFile(mode='w', suffix='.syn', delete=False, encoding='utf-8') as f:
            f.write(CODIGO_WHILE_INACOTADO)
            temp_path = f.name

        try:
            # Con --safe debe fallar
            codigo = ejecutar_compilador(temp_path, modo_safe=True)
            assert codigo != 0, "Pipeline con --safe debe rechazar código con bucle inacotado"
        finally:
            os.unlink(temp_path)

    def test_pipeline_safe_combinado_incremental(self):
        """Verifica que --safe funcione combinado con --incremental."""
        from pipeline import ejecutar_compilador
        import tempfile

        with tempfile.NamedTemporaryFile(mode='w', suffix='.syn', delete=False, encoding='utf-8') as f:
            f.write(CODIGO_VALIDO_SAFE)
            temp_path = f.name

        try:
            codigo = ejecutar_compilador(temp_path, modo_safe=True, incremental=True)
            assert codigo == 0, f"--safe + --incremental debe retornar 0, pero retornó {codigo}"
        finally:
            os.unlink(temp_path)
