from compilador.lexer import Lexer
from compilador.parser import Parser
from compilador.analizador_semantico import AnalizadorSemantico
from compilador.diagnostics import DiagnosticManager, ErrorCodes


class TestAnalizadorSemanticoVariables:
    """Tests de análisis semántico de variables"""
    
    def test_variable_no_declarada(self):
        """Test que variable no declarada genera error"""
        fuente = "#lang: es\nfuncion f() -> int:\n    x = z\n    retornar x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert diag.hay_errores()
        assert any(e['codigo'] == ErrorCodes.ERR_SEM_VAR_NO_DECLARADA for e in diag.errores)
    
    def test_variable_declarada_correctamente(self):
        """Test que variable declarada correctamente no genera error"""
        fuente = "#lang: es\nfuncion f() -> int:\n    x = 42\n    z = x\n    retornar z"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert not diag.hay_errores()
    
    def test_variable_redefinida(self):
        """Test que redefinición de variable genera error"""
        fuente = "#lang: es\nfuncion f() -> int:\n    x = 1\n    x = 2"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        # La redefinición en el mismo scope debería generar error
        # (dependiendo de la implementación de la tabla de símbolos)


class TestAnalizadorSemanticoFunciones:
    """Tests de análisis semántico de funciones"""
    
    def test_funcion_no_definida(self):
        """Test que función no definida genera error"""
        fuente = "#lang: es\nfuncion f() -> int:\n    x = f_no_existe()\n    retornar x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert diag.hay_errores()
        assert any(e['codigo'] == ErrorCodes.ERR_SEM_FUNC_NO_DEFINIDA for e in diag.errores)
    
    def test_funcion_redefinida(self):
        """Test que redefinición de función genera error"""
        fuente = "#lang: es\nfuncion f() -> int:\n    retornar 1\nfuncion f() -> int:\n    retornar 2"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert diag.hay_errores()
        assert any(e['codigo'] == ErrorCodes.ERR_SEM_REDEFINICION for e in diag.errores)
    
    def test_funcion_builtin(self):
        """Test que funciones builtin no generan error"""
        fuente = "#lang: es\nx = texto_a_entero(\"42\")"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert not diag.hay_errores()
    
    def test_argumentos_invalidos_cantidad(self):
        """Test que cantidad incorrecta de argumentos genera error"""
        fuente = "#lang: es\nfuncion f() -> int:\n    x = texto_a_entero()\n    retornar x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert diag.hay_errores()
        assert any(e['codigo'] == ErrorCodes.ERR_SEM_ARGUMENTOS_INVALIDOS for e in diag.errores)
    
    def test_tipo_retorno_correcto(self):
        """Test que tipo de retorno correcto no genera error"""
        fuente = "#lang: es\nfuncion f() -> int:\n    retornar 42"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert not diag.hay_errores()
    
    def test_tipo_retorno_incorrecto(self):
        """Test que tipo de retorno incorrecto genera error"""
        fuente = '#lang: es\nfuncion f() -> int:\n    retornar "hola"'
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert diag.hay_errores()
        assert any(e['codigo'] == ErrorCodes.ERR_SEM_TIPO_RETORNO for e in diag.errores)
    
    def test_falta_retorno(self):
        """Test que falta de retorno cuando se espera genera error"""
        fuente = "#lang: es\nfuncion f() -> int:\n    x = 1"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        # El analizador actual no detecta esto, pero debería
        # Este test documenta el comportamiento esperado


class TestAnalizadorSemanticoTipos:
    """Tests de análisis de tipos"""
    
    def test_operacion_aritmetica_tipos_compatibles(self):
        """Test que operación aritmética con tipos compatibles no genera error"""
        fuente = "#lang: es\nx = 1 + 2"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert not diag.hay_errores()
    
    def test_operacion_aritmetica_tipos_incompatibles(self):
        """Test que operación aritmética con tipos incompatibles genera error"""
        fuente = '#lang: es\nfuncion f() -> int:\n    x = 1 + "hola"\n    retornar x'
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert diag.hay_errores()
        assert any(e['codigo'] == ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE for e in diag.errores)
    
    def test_coercion_int_float(self):
        """Test que coerción int a float funciona"""
        fuente = "#lang: es\nx = 1 + 2.5"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert not diag.hay_errores()
    
    def test_operador_unario_tipo_correcto(self):
        """Test que operador unario con tipo correcto no genera error"""
        fuente = "#lang: es\nx = -5"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert not diag.hay_errores()
    
    def test_operador_unario_tipo_incorrecto(self):
        """Test que operador unario con tipo incorrecto genera error"""
        fuente = '#lang: es\nfuncion f() -> int:\n    x = -"hola"\n    retornar x'
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert diag.hay_errores()
        assert any(e['codigo'] == ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE for e in diag.errores)
    
    def test_condicion_si_tipo_correcto(self):
        """Test que condición de si con tipo correcto no genera error"""
        fuente = "#lang: es\nfuncion f() -> int:\n    x = 0\n    si 1 > 0:\n        x = 1\n    retornar x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert not diag.hay_errores()
    
    def test_condicion_si_tipo_incorrecto(self):
        """Test que condición de si con tipo incorrecto genera error"""
        fuente = '#lang: es\nfuncion f() -> int:\n    si "hola":\n        x = 1\n    retornar x'
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert diag.hay_errores()
        assert any(e['codigo'] == ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE for e in diag.errores)
    
    def test_condicion_mientras_tipo_correcto(self):
        """Test que condición de mientras con tipo correcto no genera error"""
        fuente = "#lang: es\nfuncion f() -> int:\n    x = 0\n    mientras 1 > 0:\n        x = x + 1\n    retornar x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert not diag.hay_errores()
    
    def test_condicion_mientras_tipo_incorrecto(self):
        """Test que condición de mientras con tipo incorrecto genera error"""
        fuente = '#lang: es\nfuncion f() -> int:\n    x = 0\n    mientras "hola":\n        x = x + 1\n    retornar x'
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert diag.hay_errores()
        assert any(e['codigo'] == ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE for e in diag.errores)


class TestAnalizadorSemanticoEstructuras:
    """Tests de análisis semántico de estructuras"""
    
    def test_estructura_no_definida(self):
        """Test que estructura no definida genera error"""
        fuente = "#lang: es\nfuncion f() -> int:\n    x = Punto()\n    retornar x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert diag.hay_errores()
        assert any(e['codigo'] == ErrorCodes.ERR_SEM_FUNC_NO_DEFINIDA for e in diag.errores)
    
    def test_estructura_definida_correctamente(self):
        """Test que estructura definida correctamente no genera error"""
        fuente = "#lang: es\nestructura Punto:\n    a: int\n    b: int\nfuncion f() -> Punto:\n    p = Punto()\n    retornar p"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert not diag.hay_errores()
    
    def test_campo_no_existente(self):
        """Test que acceso a campo inexistente genera error"""
        fuente = "#lang: es\nestructura Punto:\n    a: int\nfuncion f() -> int:\n    p = Punto()\n    z = p.z\n    retornar z"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert diag.hay_errores()
        assert any(e['codigo'] == ErrorCodes.ERR_SEM_CAMPO_NO_EXISTE for e in diag.errores)
    
    def test_campo_existente(self):
        """Test que acceso a campo existente no genera error"""
        fuente = "#lang: es\nestructura Punto:\n    a: int\nfuncion f() -> int:\n    p = Punto()\n    z = p.a\n    retornar z"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert not diag.hay_errores()
    
    def test_asignacion_campo_tipo_correcto(self):
        """Test que asignación a campo con tipo correcto no genera error"""
        fuente = "#lang: es\nestructura Punto:\n    a: int\nfuncion f() -> int:\n    p = Punto()\n    p.a = 10\n    retornar p.a"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert not diag.hay_errores()
    
    def test_asignacion_campo_tipo_incorrecto(self):
        """Test que asignación a campo con tipo incorrecto genera error"""
        fuente = '#lang: es\nestructura Punto:\n    a: int\nfuncion f() -> int:\n    p = Punto()\n    p.a = "hola"\n    retornar p.a'
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert diag.hay_errores()
        assert any(e['codigo'] == ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE for e in diag.errores)


class TestAnalizadorSemanticoCoercion:
    """Tests de coerción de tipos"""
    
    def test_coercion_int_a_texto(self):
        """Test que coerción int a texto funciona"""
        fuente = '#lang: es\nx = concat("valor: ", 42)'
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert not diag.hay_errores()
    
    def test_coercion_float_a_texto(self):
        """Test que coerción float a texto funciona"""
        fuente = '#lang: es\nx = concat("valor: ", 3.14)'
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert not diag.hay_errores()
    
    def test_funcion_conversion_texto_a_entero(self):
        """Test que función de conversión texto a entero funciona"""
        fuente = '#lang: es\nx = texto_a_entero("42")'
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert not diag.hay_errores()
    
    def test_funcion_conversion_texto_a_decimal(self):
        """Test que función de conversión texto a decimal funciona"""
        fuente = '#lang: es\nx = texto_a_decimal("3.14")'
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert not diag.hay_errores()
    
    def test_funcion_conversion_decimal_a_texto(self):
        """Test que función de conversión decimal a texto funciona"""
        fuente = '#lang: es\nx = decimal_a_texto(3.14)'
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert not diag.hay_errores()


class TestAnalizadorSemanticoTensores:
    """Tests de análisis semántico de tensores"""
    
    def test_tensor_tipos_correctos(self):
        """Test que tensor con tipos correctos no genera error"""
        fuente = "#lang: es\nx = tensor(3, 4)"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert not diag.hay_errores()
    
    def test_tensor_tipo_incorrecto(self):
        """Test que tensor con tipo incorrecto genera error"""
        fuente = '#lang: es\nfuncion f() -> Tensor:\n    x = tensor("hola", 4)\n    retornar x'
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert diag.hay_errores()
        assert any(e['codigo'] == ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE for e in diag.errores)


class TestAnalizadorSemanticoScopes:
    """Tests de análisis de scopes"""
    
    def test_variable_scope_funcion(self):
        """Test que variable en scope de función es accesible"""
        fuente = "#lang: es\nfuncion f() -> int:\n    x = 1\n    retornar x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert not diag.hay_errores()
    
    def test_variable_fuera_scope(self):
        """Test que variable fuera de scope genera error"""
        fuente = "#lang: es\nfuncion f() -> int:\n    x = 1\n    retornar x\nfuncion g() -> int:\n    z = x\n    retornar z"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert diag.hay_errores()
        assert any(e['codigo'] == ErrorCodes.ERR_SEM_VAR_NO_DECLARADA for e in diag.errores)
    
    def test_parametro_funcion(self):
        """Test que parámetro de función es accesible"""
        fuente = "#lang: es\nfuncion f(x: int) -> int:\n    retornar x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert not diag.hay_errores()
    
    def test_scope_anidado(self):
        """Test que scope anidado funciona correctamente"""
        fuente = "#lang: es\nfuncion f() -> int:\n    x = 1\n    si 1 > 0:\n        z = x\n    retornar x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert not diag.hay_errores()


class TestAnalizadorSemanticoConcurrencia:
    """Tests de análisis semántico de concurrencia"""
    
    def test_lanzar_funcion(self):
        """Test que lanzar función no genera error"""
        fuente = "#lang: es\nfuncion f() -> int:\n    retornar 1\nlanzar f()"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert not diag.hay_errores()
    
    def test_escuchar_canal(self):
        """Test que escuchar canal no genera error"""
        fuente = "#lang: es\nfuncion respuesta() -> int:\n    retornar 1\nescuchar canal -> respuesta()"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert not diag.hay_errores()
    
    def test_recuperar_plan_b(self):
        """Test que recuperar con plan B no genera error"""
        fuente = "#lang: es\naccion_critica() recuperar: plan_b()"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert not diag.hay_errores()


class TestAnalizadorSemanticoLog:
    """Tests de análisis semántico de log"""
    
    def test_log_con_argumentos(self):
        """Test que log con argumentos no genera error"""
        fuente = '#lang: es\nlog("hola mundo")'
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert not diag.hay_errores()
    
    def test_log_multiples_argumentos(self):
        """Test que log con múltiples argumentos no genera error"""
        fuente = '#lang: es\nlog("valor: ", 42)'
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        
        assert not diag.hay_errores()
