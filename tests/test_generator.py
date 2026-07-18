import pytest
from compilador.lexer import Lexer
from compilador.parser import Parser
from compilador.analizador_semantico import AnalizadorSemantico
from compilador.generator import GeneradorC
from compilador.diagnostics import DiagnosticManager
from compilador.ast_nodes import Programa


class TestGeneradorCFunciones:
    """Tests de generación de código para funciones"""
    
    def test_funcion_simple(self):
        """Test generación de función simple"""
        fuente = "#lang: es\nfuncion f() -> int:\n    retornar 42"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "int f(void)" in codigo
        assert "= 42" in codigo
        assert "return " in codigo
    
    def test_funcion_con_parametros(self):
        """Test generación de función con parámetros"""
        fuente = "#lang: es\nfuncion sumar(a: int, b: int) -> int:\n    retornar a + b"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "int sumar(int a, int b)" in codigo
    
    def test_funcion_con_principal(self):
        """Test generación de función principal"""
        fuente = "#lang: es\nfuncion principal() -> int:\n    retornar 0"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "int main(int argc, char** argv)" in codigo
        assert "principal();" in codigo
    
    def test_funcion_sin_retorno(self):
        """Test generación de función void"""
        fuente = "#lang: es\nfuncion f() -> nulo:\n    x = 1"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "void f(void)" in codigo


class TestGeneradorCExpresiones:
    """Tests de generación de código para expresiones"""
    
    def test_literal_entero(self):
        """Test generación de literal entero"""
        fuente = "#lang: es\nfuncion f() -> int:\n    x = 42\n    retornar x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "42" in codigo
    
    def test_literal_decimal(self):
        """Test generación de literal decimal"""
        fuente = "#lang: es\nfuncion f() -> float:\n    x = 3.14\n    retornar x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "3.14" in codigo
    
    def test_literal_cadena(self):
        """Test generación de literal cadena"""
        fuente = '#lang: es\nfuncion f() -> text:\n    x = "hola"\n    retornar x'
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert '"hola"' in codigo
    
    def test_operador_suma(self):
        """Test generación de operador suma"""
        fuente = "#lang: es\nfuncion f() -> int:\n    x = 1 + 2\n    retornar x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "+" in codigo
    
    def test_operador_resta(self):
        """Test generación de operador resta"""
        fuente = "#lang: es\nfuncion f() -> int:\n    x = 5 - 3\n    retornar x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "-" in codigo
    
    def test_operador_multiplicacion(self):
        """Test generación de operador multiplicación"""
        fuente = "#lang: es\nfuncion f() -> int:\n    x = 2 * 3\n    retornar x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "*" in codigo
    
    def test_operador_division(self):
        """Test generación de operador división"""
        fuente = "#lang: es\nfuncion f() -> int:\n    x = 6 / 2\n    retornar x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "/" in codigo
    
    def test_operador_modulo(self):
        """Test generación de operador módulo"""
        fuente = "#lang: es\nfuncion f() -> int:\n    x = 7 % 3\n    retornar x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "%" in codigo
    
    def test_operador_comparacion_mayor(self):
        """Test generación de operador mayor que"""
        fuente = "#lang: es\nfuncion f() -> int:\n    x = 1 > 2\n    retornar x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert ">" in codigo
    
    def test_operador_comparacion_menor(self):
        """Test generación de operador menor que"""
        fuente = "#lang: es\nfuncion f() -> int:\n    x = 1 < 2\n    retornar x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "<" in codigo
    
    def test_operador_igual(self):
        """Test generación de operador igual"""
        fuente = "#lang: es\nfuncion f() -> int:\n    x = 1 == 2\n    retornar x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "==" in codigo
    
    def test_operador_diferente(self):
        """Test generación de operador diferente"""
        fuente = "#lang: es\nfuncion f() -> int:\n    x = 1 != 2\n    retornar x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "!=" in codigo
    
    def test_operador_mayor_igual(self):
        """Test generación de operador mayor o igual"""
        fuente = "#lang: es\nfuncion f() -> int:\n    x = 1 >= 2\n    retornar x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert ">=" in codigo
    
    def test_operador_menor_igual(self):
        """Test generación de operador menor o igual"""
        fuente = "#lang: es\nfuncion f() -> int:\n    x = 1 <= 2\n    retornar x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "<=" in codigo


class TestGeneradorCSentenciasControl:
    """Tests de generación de sentencias de control"""
    
    def test_si_simple(self):
        """Test generación de si simple"""
        fuente = "#lang: es\nfuncion f() -> int:\n    si 1 > 0:\n        retornar 1\n    retornar 0"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "if" in codigo
        assert "= 1" in codigo
        assert "return " in codigo
    
    def test_si_con_sino(self):
        """Test generación de si con sino"""
        fuente = "#lang: es\nfuncion f() -> int:\n    si 1 > 0:\n        retornar 1\n    sino:\n        retornar 0"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "if" in codigo
        assert "else" in codigo
    
    def test_mientras(self):
        """Test generación de mientras"""
        fuente = "#lang: es\nfuncion f() -> int:\n    x = 0\n    mientras x < 10:\n        x = x + 1\n    retornar x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "while" in codigo
    
    def test_romper(self):
        """Test generación de romper"""
        fuente = "#lang: es\nfuncion f() -> int:\n    mientras True:\n        romper\n    retornar 0"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "break;" in codigo
    
    def test_siguiente(self):
        """Test generación de siguiente"""
        fuente = "#lang: es\nfuncion f() -> int:\n    mientras True:\n        siguiente\n    retornar 0"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "continue;" in codigo


class TestGeneradorCEstructuras:
    """Tests de generación de código para estructuras"""
    
    def test_estructura_simple(self):
        """Test generación de estructura simple"""
        fuente = "#lang: es\nestructura Punto:\n    a: int\n    b: int"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "struct Punto" in codigo
        assert "int a" in codigo
        assert "int b" in codigo
    
    def test_acceso_campo(self):
        """Test generación de acceso a campo"""
        fuente = "#lang: es\nestructura Punto:\n    a: int\nfuncion f() -> int:\n    p = Punto()\n    retornar p.a"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert ".a" in codigo
    
    def test_asignacion_campo(self):
        """Test generación de asignación a campo"""
        fuente = "#lang: es\nestructura Punto:\n    a: int\nfuncion f() -> int:\n    p = Punto()\n    p.a = 10\n    retornar p.a"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert ".a =" in codigo
    
    def test_acceso_campo_pointer_con_flecha(self):
        """Test que acceso a campo via puntero emite ->"""
        fuente = "#lang: es\nestructura Punto:\n    a: int\n    b: int\nfuncion f() -> int:\n    inseguro:\n        p = Punto()\n        ptr = &p\n        ptr.a = 10\n        retornar ptr.a"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "->a = 10" in codigo
        assert "ptr->a" in codigo
        assert "return " in codigo


class TestGeneradorCTipos:
    """Tests de mapeo de tipos"""
    
    def test_tipo_int(self):
        """Test mapeo de tipo int"""
        fuente = "#lang: es\nfuncion f() -> int:\n    x: int = 1\n    retornar x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "int" in codigo
    
    def test_tipo_float(self):
        """Test mapeo de tipo float"""
        fuente = "#lang: es\nfuncion f() -> decimal:\n    x: decimal = 1.5\n    retornar x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "float" in codigo
    
    def test_tipo_texto(self):
        """Test mapeo de tipo texto"""
        fuente = '#lang: es\nfuncion f() -> texto:\n    x: texto = "hola"\n    retornar x'
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "CadenaSegura" in codigo
    
    def test_tipo_void(self):
        """Test mapeo de tipo void"""
        fuente = "#lang: es\nfuncion f() -> nulo:\n    x = 1"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "void" in codigo


class TestGeneradorCBuiltins:
    """Tests de generación de funciones builtin"""
    
    def test_concat(self):
        """Test generación de concat"""
        fuente = '#lang: es\nfuncion f() -> texto:\n    x = concat("hola", " mundo")\n    retornar x'
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "CadenaSegura concat" in codigo
    
    def test_texto_a_entero(self):
        """Test generación de texto_a_entero"""
        fuente = '#lang: es\nfuncion f() -> int:\n    x = texto_a_entero("42")\n    retornar x'
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "texto_a_entero" in codigo
    
    def test_texto_a_decimal(self):
        """Test generación de texto_a_decimal"""
        fuente = '#lang: es\nfuncion f() -> decimal:\n    x = texto_a_decimal("3.14")\n    retornar x'
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "texto_a_decimal" in codigo
    
    def test_decimal_a_texto(self):
        """Test generación de decimal_a_texto"""
        fuente = "#lang: es\nfuncion f() -> texto:\n    x = decimal_a_texto(3.14)\n    retornar x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "decimal_a_texto" in codigo


class TestGeneradorCConcurrencia:
    """Tests de generación de código de concurrencia"""
    
    def test_lanzar(self):
        """Test generación de lanzar"""
        fuente = "#lang: es\nfuncion f() -> int:\n    retornar 1\nfuncion principal() -> int:\n    lanzar f()"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "pthread_create" in codigo or "thread" in codigo.lower()
    
    def test_escuchar(self):
        """Test generación de escuchar"""
        fuente = "#lang: es\nfuncion respuesta() -> int:\n    retornar 1\nfuncion principal() -> int:\n    escuchar canal -> respuesta()"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        # Debería generar una función listener
        assert "listener" in codigo.lower() or "callback" in codigo.lower()


class TestGeneradorCHeaders:
    """Tests de generación de headers"""
    
    def test_headers_estandar(self):
        """Test que se incluyen headers estándar"""
        fuente = "#lang: es\nfuncion f() -> int:\n    retornar 0"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "#include <stdio.h>" in codigo
        assert "#include <stdlib.h>" in codigo
        assert "#include <stdint.h>" in codigo
        assert "#include <pthread.h>" in codigo
        assert "#include <string.h>" in codigo
    
    def test_typedef_cadena_segura(self):
        """Test que se define CadenaSegura"""
        fuente = "#lang: es\nfuncion f() -> int:\n    retornar 0"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "typedef struct { int longitud; const char* datos; } CadenaSegura;" in codigo
    
    def test_typedef_tensor(self):
        """Test que se define Tensor"""
        fuente = "#lang: es\nfuncion f() -> int:\n    retornar 0"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "typedef struct { uint32_t filas; uint32_t columnas; float* datos; int es_mapeado; } Tensor;" in codigo
    
    def test_typedef_canal(self):
        """Test que se define Canal"""
        fuente = "#lang: es\nfuncion f() -> int:\n    retornar 0"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "typedef struct { FILE* stream; int es_valido; int es_virtual; const char* virtual_data; int virtual_len; } Canal;" in codigo


class TestGeneradorCMain:
    """Tests de generación de función main"""
    
    def test_main_con_pool_init(self):
        """Test que main inicializa pool de memoria"""
        fuente = "#lang: es\nfuncion principal() -> int:\n    retornar 0"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "pool_init(POOL_BLOQUES, TAMANO_BLOQUE);" in codigo
    
    def test_main_sin_principal(self):
        """Test que main sin función principal no la llama"""
        fuente = "#lang: es\nfuncion f() -> int:\n    retornar 0"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "f();" not in codigo


class TestGeneradorCCoercion:
    """Tests de coerción de tipos en generación"""
    
    def test_coercion_int_a_texto(self):
        """Test coerción int a texto"""
        fuente = '#lang: es\nfuncion f() -> texto:\n    x = concat("valor: ", 42)\n    retornar x'
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        # Debería aplicar coerción
        assert "entero_a_texto" in codigo
    
    def test_coercion_float_a_texto(self):
        """Test coerción float a texto"""
        fuente = '#lang: es\nfuncion f() -> texto:\n    x = concat("valor: ", 3.14)\n    retornar x'
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        # Debería aplicar coerción
        assert "decimal_a_texto" in codigo


class TestGeneradorCTensores:
    """Tests de generación de código para tensores"""
    
    def test_tensor_creation(self):
        """Test generación de creación de tensor"""
        fuente = "#lang: es\nfuncion f() -> tensor:\n    x = tensor(3, 4)\n    retornar x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "crear_tensor" in codigo
    
    def test_tensor_operations(self):
        """Test generación de operaciones de tensor"""
        fuente = "#lang: es\nfuncion f() -> tensor:\n    a = tensor(2, 2)\n    b = tensor(2, 2)\n    c = suma(a, b)\n    retornar c"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "suma" in codigo


class TestGeneradorCIo:
    """Tests de generación de código I/O"""
    
    def test_log(self):
        """Test generación de log"""
        fuente = '#lang: es\nfuncion f() -> int:\n    log("hola mundo")\n    retornar 0'
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        # log debería generar printf o similar
        assert "printf" in codigo or "escribir" in codigo
    
    def test_escribir(self):
        """Test generación de escribir"""
        fuente = '#lang: es\nfuncion f() -> int:\n    escribir("hola")\n    retornar 0'
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        generador = GeneradorC(prog)
        codigo = generador.generar()
        
        assert "escribir" in codigo
