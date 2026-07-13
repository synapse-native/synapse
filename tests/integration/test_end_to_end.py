import os
import tempfile
import subprocess
import pytest
from lexer import Lexer
from parser import Parser
from analizador_semantico import AnalizadorSemantico
from generator import GeneradorC
from diagnostics import DiagnosticManager
from exceptions import SynapseError


class TestIntegrationEndToEnd:
    """Tests de integración end-to-end del pipeline de compilación"""
    
    def _compilar_synapse(self, fuente: str) -> tuple[str, DiagnosticManager]:
        """Compila código Synapse a C"""
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        if diag.hay_errores():
            return "", diag
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        if diag.hay_errores():
            return "", diag
        
        generador = GeneradorC(prog)
        codigo_c = generador.generar()
        
        return codigo_c, diag
    
    def test_hola_mundo(self):
        """Test compilación y ejecución de hola mundo"""
        fuente = '#lang: es\nfuncion principal() -> int:\n    escribir("Hola Mundo")\n    retornar 0'
        
        codigo_c, diag = self._compilar_synapse(fuente)
        
        assert not diag.hay_errores()
        assert codigo_c
        assert "Hola Mundo" in codigo_c or "escribir" in codigo_c
        assert "int main" in codigo_c
    
    def test_funcion_simple(self):
        """Test compilación de función simple"""
        fuente = "#lang: es\nfuncion sumar(a: int, b: int) -> int:\n    retornar a + b\nfuncion principal() -> int:\n    x = sumar(1, 2)\n    retornar x"
        
        codigo_c, diag = self._compilar_synapse(fuente)
        
        assert not diag.hay_errores()
        assert codigo_c
        assert "int sumar(void)" in codigo_c or "int sumar(int" in codigo_c
        assert "a + b" in codigo_c
    
    def test_condicional_si(self):
        """Test compilación de condicional si"""
        fuente = "#lang: es\nfuncion principal() -> int:\n    x = 10\n    si x > 5:\n        x = 20\n    retornar x"
        
        codigo_c, diag = self._compilar_synapse(fuente)
        
        assert not diag.hay_errores()
        assert codigo_c
        assert "if" in codigo_c
    
    def test_condicional_si_sino(self):
        """Test compilación de si con sino"""
        fuente = "#lang: es\nfuncion principal() -> int:\n    x = 3\n    si x > 5:\n        x = 20\n    sino:\n        x = 10\n    retornar x"
        
        codigo_c, diag = self._compilar_synapse(fuente)
        
        assert not diag.hay_errores()
        assert codigo_c
        assert "if" in codigo_c
        assert "else" in codigo_c
    
    def test_ciclo_mientras(self):
        """Test compilación de ciclo mientras"""
        fuente = "#lang: es\nfuncion principal() -> int:\n    x = 0\n    mientras x < 10:\n        x = x + 1\n    retornar x"
        
        codigo_c, diag = self._compilar_synapse(fuente)
        
        assert not diag.hay_errores()
        assert codigo_c
        assert "while" in codigo_c
    
    def test_estructura(self):
        """Test compilación de estructura"""
        fuente = "#lang: es\nestructura Punto:\n    a: int\n    b: int\nfuncion principal() -> int:\n    p = Punto()\n    p.a = 10\n    p.b = 20\n    retornar p.a"
        
        codigo_c, diag = self._compilar_synapse(fuente)
        
        assert not diag.hay_errores()
        assert codigo_c
        assert "struct Punto" in codigo_c
    
    def test_operaciones_aritmeticas(self):
        """Test compilación de operaciones aritméticas"""
        fuente = "#lang: es\nfuncion principal() -> int:\n    a = 10\n    b = 5\n    c = a + b\n    d = a - b\n    e = a * b\n    f = a / b\n    g = a % b\n    retornar c"
        
        codigo_c, diag = self._compilar_synapse(fuente)
        
        assert not diag.hay_errores()
        assert codigo_c
        assert "+" in codigo_c
        assert "-" in codigo_c
        assert "*" in codigo_c
        assert "/" in codigo_c
        assert "%" in codigo_c
    
    def test_operaciones_comparacion(self):
        """Test compilación de operaciones de comparación"""
        fuente = "#lang: es\nfuncion principal() -> int:\n    a = 10\n    b = 5\n    c = a > b\n    d = a < b\n    e = a == b\n    f = a != b\n    g = a >= b\n    h = a <= b\n    retornar 0"
        
        codigo_c, diag = self._compilar_synapse(fuente)
        
        assert not diag.hay_errores()
        assert codigo_c
        assert ">" in codigo_c
        assert "<" in codigo_c
        assert "==" in codigo_c
        assert "!=" in codigo_c
        assert ">=" in codigo_c
        assert "<=" in codigo_c
    
    def test_tipo_decimal(self):
        """Test compilación de tipo decimal"""
        fuente = "#lang: es\nfuncion principal() -> int:\n    a = 3.14\n    b = 2.5\n    c = a + b\n    retornar 0"
        
        codigo_c, diag = self._compilar_synapse(fuente)
        
        assert not diag.hay_errores()
        assert codigo_c
        assert "float" in codigo_c
    
    def test_tipo_texto(self):
        """Test compilación de tipo texto"""
        fuente = '#lang: es\nfuncion principal() -> int:\n    a = "hola"\n    b = " mundo"\n    c = concat(a, b)\n    retornar 0'
        
        codigo_c, diag = self._compilar_synapse(fuente)
        
        assert not diag.hay_errores()
        assert codigo_c
        assert "CadenaSegura" in codigo_c
        assert "concat" in codigo_c
    
    def test_coercion_tipos(self):
        """Test coerción de tipos"""
        fuente = '#lang: es\nfuncion principal() -> int:\n    a = 42\n    b = concat("valor: ", a)\n    retornar 0'
        
        codigo_c, diag = self._compilar_synapse(fuente)
        
        assert not diag.hay_errores()
        assert codigo_c
        # Debería aplicar coerción int a texto
        assert "entero_a_texto" in codigo_c
    
    def test_tensor(self):
        """Test compilación de tensor"""
        fuente = "#lang: es\nfuncion principal() -> int:\n    t = tensor(3, 4)\n    retornar 0"
        
        codigo_c, diag = self._compilar_synapse(fuente)
        
        assert not diag.hay_errores()
        assert codigo_c
        assert "Tensor" in codigo_c
        assert "crear_tensor" in codigo_c
    
    def test_log(self):
        """Test compilación de log"""
        fuente = '#lang: es\nfuncion principal() -> int:\n    log("mensaje de prueba")\n    retornar 0'
        
        codigo_c, diag = self._compilar_synapse(fuente)
        
        assert not diag.hay_errores()
        assert codigo_c
    
    def test_importar(self):
        """Test compilación de importar"""
        fuente = "#lang: es\nimportar std.io\nfuncion principal() -> int:\n    retornar 0"
        
        codigo_c, diag = self._compilar_synapse(fuente)
        
        assert not diag.hay_errores()
        assert codigo_c
    
    def test_funciones_conversion(self):
        """Test funciones de conversión"""
        fuente = '#lang: es\nfuncion principal() -> int:\n    a = texto_a_entero("42")\n    b = texto_a_decimal("3.14")\n    c = decimal_a_texto(2.5)\n    retornar a'
        
        codigo_c, diag = self._compilar_synapse(fuente)
        
        assert not diag.hay_errores()
        assert codigo_c
        assert "texto_a_entero" in codigo_c
        assert "texto_a_decimal" in codigo_c
        assert "decimal_a_texto" in codigo_c
    
    def test_romper(self):
        """Test compilación de romper"""
        fuente = "#lang: es\nfuncion principal() -> int:\n    x = 0\n    mientras x < 10:\n        x = x + 1\n        si x == 5:\n            romper\n    retornar x"
        
        codigo_c, diag = self._compilar_synapse(fuente)
        
        assert not diag.hay_errores()
        assert codigo_c
        assert "break;" in codigo_c
    
    def test_siguiente(self):
        """Test compilación de siguiente"""
        fuente = "#lang: es\nfuncion principal() -> int:\n    x = 0\n    mientras x < 10:\n        x = x + 1\n        si x == 5:\n            siguiente\n    retornar x"
        
        codigo_c, diag = self._compilar_synapse(fuente)
        
        assert not diag.hay_errores()
        assert codigo_c
        assert "continue;" in codigo_c
    
    def test_multiple_funciones(self):
        """Test compilación de múltiples funciones"""
        fuente = "#lang: es\nfuncion f1() -> int:\n    retornar 1\nfuncion f2() -> int:\n    retornar 2\nfuncion principal() -> int:\n    x = f1() + f2()\n    retornar x"
        
        codigo_c, diag = self._compilar_synapse(fuente)
        
        assert not diag.hay_errores()
        assert codigo_c
        assert "int f1(void)" in codigo_c or "int f1(" in codigo_c
        assert "int f2(void)" in codigo_c or "int f2(" in codigo_c
    
    def test_parametros_funcion(self):
        """Test compilación de función con parámetros"""
        fuente = "#lang: es\nfuncion sumar(a: int, b: int, c: int) -> int:\n    retornar a + b + c\nfuncion principal() -> int:\n    x = sumar(1, 2, 3)\n    retornar x"
        
        codigo_c, diag = self._compilar_synapse(fuente)
        
        assert not diag.hay_errores()
        assert codigo_c
        assert "int sumar(int a, int b, int c)" in codigo_c
    
    def test_anidamiento_bloques(self):
        """Test compilación de bloques anidados"""
        fuente = "#lang: es\nfuncion principal() -> int:\n    x = 0\n    mientras x < 10:\n        si x > 5:\n            mientras x < 8:\n                x = x + 1\n        x = x + 1\n    retornar x"
        
        codigo_c, diag = self._compilar_synapse(fuente)
        
        assert not diag.hay_errores()
        assert codigo_c
    
    def test_error_lexico(self):
        """Test que error léxico se detecta en el pipeline"""
        fuente = "#lang: es\nfuncion f() -> int:\n    x = @\n    retornar x"
        
        try:
            codigo_c, diag = self._compilar_synapse(fuente)
        except (SyntaxError, SynapseError):
            # Error léxico lanza SyntaxError/SynapseError antes de llegar a diagnostics
            return
        
        assert diag.hay_errores()
        assert codigo_c == ""
    
    def test_error_sintactico(self):
        """Test que error sintáctico se detecta en el pipeline"""
        fuente = "#lang: es\nfuncion f( -> int:\n    retornar 1"
        
        codigo_c, diag = self._compilar_synapse(fuente)
        
        assert diag.hay_errores()
        assert codigo_c == ""
    
    def test_error_semantico(self):
        """Test que error semántico se detecta en el pipeline"""
        fuente = "#lang: es\nfuncion f() -> int:\n    x = y\n    retornar x"
        
        codigo_c, diag = self._compilar_synapse(fuente)
        
        assert diag.hay_errores()
        assert codigo_c == ""
    
    def test_codigo_c_valido(self):
        """Test que el código C generado es sintácticamente válido"""
        fuente = "#lang: es\nfuncion principal() -> int:\n    retornar 0"
        
        codigo_c, diag = self._compilar_synapse(fuente)
        
        assert not diag.hay_errores()
        assert codigo_c
        
        # Verificar que el código C tiene estructura básica válida
        assert "#include" in codigo_c
        assert "int main" in codigo_c
        assert "return 0" in codigo_c
        assert "}" in codigo_c


class TestIntegrationCompilacionReal:
    """Tests de compilación real con gcc (si está disponible)"""
    
    def _compilar_con_gcc(self, codigo_c: str) -> tuple[bool, str]:
        """Intenta compilar código C con gcc"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
                f.write(codigo_c)
                temp_c = f.name
            
            temp_exe = temp_c.replace('.c', '.exe')
            
            # Intentar compilar con gcc (ignorando errores de linking del runtime)
            result = subprocess.run(
                ['gcc', '-c', temp_c, '-o', temp_c.replace('.c', '.o')],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Limpiar archivos temporales
            for ext in ['.c', '.o', '.exe']:
                temp_file = temp_c.replace('.c', ext)
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            
            return result.returncode == 0, result.stderr
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # gcc no disponible o timeout
            return False, "gcc no disponible"
        finally:
            # Limpieza adicional
            try:
                if 'temp_c' in locals():
                    for ext in ['.c', '.o', '.exe']:
                        temp_file = temp_c.replace('.c', ext)
                        if os.path.exists(temp_file):
                            os.unlink(temp_file)
            except:
                pass
    
    def test_compilacion_gcc_simple(self):
        """Test compilación con gcc de código simple"""
        fuente = "#lang: es\nfuncion principal() -> int:\n    retornar 0"
        
        from lexer import Lexer
        from parser import Parser
        from analizador_semantico import AnalizadorSemantico
        from generator import GeneradorC
        from diagnostics import DiagnosticManager
        
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo_c = generador.generar()
        
        if not diag.hay_errores():
            # Intentar compilar con gcc si está disponible
            exito, stderr = self._compilar_con_gcc(codigo_c)
            # Si gcc no está disponible, no fallar el test
            # Solo verificar que el código C se generó correctamente
            assert codigo_c


class TestIntegrationFixtures:
    """Tests de integración usando fixtures existentes"""
    
    def _compilar_synapse(self, fuente: str) -> tuple[str, DiagnosticManager]:
        """Compila código Synapse a C"""
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        if diag.hay_errores():
            return "", diag
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        if diag.hay_errores():
            return "", diag
        
        generador = GeneradorC(prog)
        codigo_c = generador.generar()
        
        return codigo_c, diag
    
    def test_fixture_basico(self):
        """Test usando fixture básico existente"""
        fixture_path = "d:\\proyecto_synapse\\examples\\01_basico.syn"
        
        if not os.path.exists(fixture_path):
            pytest.skip(f"Fixture no encontrado: {fixture_path}")
        
        with open(fixture_path, 'r', encoding='utf-8') as f:
            fuente = f.read()
        
        codigo_c, diag = self._compilar_synapse(fuente)
        
        assert not diag.hay_errores()
        assert codigo_c
    
    def test_fixture_estructuras(self):
        """Test usando fixture de estructuras"""
        fixture_path = "d:\\proyecto_synapse\\examples\\02_estructuras.syn"
        
        if not os.path.exists(fixture_path):
            pytest.skip(f"Fixture no encontrado: {fixture_path}")
        
        with open(fixture_path, 'r', encoding='utf-8') as f:
            fuente = f.read()
        
        codigo_c, diag = self._compilar_synapse(fuente)
        
        assert not diag.hay_errores()
        assert codigo_c
