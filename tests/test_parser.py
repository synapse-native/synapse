import os, json, glob
import pytest

from conftest import DIR_VALID, compilar_texto, ast_a_canonico_test
from compilador.lexer import Lexer
from compilador.parser import Parser
from compilador.diagnostics import DiagnosticManager
from compilador.ast_nodes import (
    Programa, DefinicionFuncion, DefinicionEstructura,
    SentenciaSi, SentenciaMientras, SentenciaLanzar, SentenciaRetornar,
    AsignacionVariable, OpBinaria, LiteralNumero,
    LlamadaFuncion, LiteralCadena, LiteralDecimal, SentenciaRomper,
    SentenciaSiguiente, SentenciaImportar, AsignacionCampo, ExprAccesoCampo,
    SentenciaEscuchar, SentenciaRecuperar, OpUnaria, ExprTensor, ArgumentoTransferido
)


def _listar_fixtures_validas():
    return sorted(glob.glob(os.path.join(DIR_VALID, '*.syn')))


@pytest.mark.parametrize('ruta_syn', _listar_fixtures_validas())
def test_ast_coincide_con_expectativa(ruta_syn):
    with open(ruta_syn, 'r', encoding='utf-8') as f:
        fuente = f.read()

    ast, diag = compilar_texto(fuente)

    assert not diag.hay_errores(), (
        f"Se esperaba 0 errores en {os.path.basename(ruta_syn)}, "
        f"se obtuvieron {diag.contar()}"
    )

    ruta_json = ruta_syn.rsplit('.', 1)[0] + '.expected.json'
    if not os.path.exists(ruta_json):
        pytest.fail(f"Archivo de expectativa faltante: {ruta_json}")

    with open(ruta_json, 'r', encoding='utf-8') as f:
        esperado = json.load(f)

    obtenido = json.loads(ast_a_canonico_test(ast))
    assert obtenido == esperado, (
        f"AST no coincide con expectativa en {os.path.basename(ruta_syn)}\n"
        f"Esperado:\n{json.dumps(esperado, indent=2, ensure_ascii=False)}\n"
        f"Obtenido:\n{json.dumps(obtenido, indent=2, ensure_ascii=False)}"
    )


class TestParserFunciones:
    """Tests de parsing de funciones"""
    
    def test_funcion_simple(self):
        """Test parsing de función simple"""
        fuente = "#lang: es\nfuncion f() -> int:\n    retornar 1"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        assert isinstance(prog, Programa)
        assert len(prog.sentencias) == 1
        assert isinstance(prog.sentencias[0], DefinicionFuncion)
        assert prog.sentencias[0].nombre == "f"
        assert prog.sentencias[0].tipo_retorno == "int"
    
    def test_funcion_con_parametros(self):
        """Test parsing de función con parámetros"""
        fuente = "#lang: es\nfuncion sumar(a: int, b: int) -> int:\n    retornar a + b"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        func = prog.sentencias[0]
        assert len(func.parametros) == 2
        assert func.parametros[0].nombre == "a"
        assert func.parametros[0].tipo == "int"
        assert func.parametros[1].nombre == "b"
        assert func.parametros[1].tipo == "int"
    
    def test_funcion_con_parametro_transferencia(self):
        """Test parsing de función con parámetro de transferencia"""
        fuente = "#lang: es\nfuncion procesar(-> x: int) -> int:\n    retornar x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        func = prog.sentencias[0]
        assert len(func.parametros) == 1
        assert func.parametros[0].es_transferencia == True


class TestParserEstructuras:
    """Tests de parsing de estructuras"""
    
    def test_estructura_simple(self):
        """Test parsing de estructura simple"""
        fuente = "#lang: es\nestructura Punto:\n    a: int\n    b: int"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        assert isinstance(prog.sentencias[0], DefinicionEstructura)
        struct = prog.sentencias[0]
        assert struct.nombre == "Punto"
        assert len(struct.campos) == 2
        assert struct.campos[0].nombre == "a"
        assert struct.campos[1].nombre == "b"


class TestParserSi:
    """Tests de parsing de sentencias si"""
    
    def test_si_simple(self):
        """Test parsing de si simple"""
        fuente = "#lang: es\nsi True:\n    x = 1"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        assert isinstance(prog.sentencias[0], SentenciaSi)
        assert len(prog.sentencias[0].cuerpo) == 1
    
    def test_si_con_sino(self):
        """Test parsing de si con sino"""
        fuente = "#lang: es\nsi True:\n    x = 1\nsino:\n    y = 2"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        stmt = prog.sentencias[0]
        assert isinstance(stmt, SentenciaSi)
        assert stmt.cuerpo_sino is not None
        assert len(stmt.cuerpo_sino) == 1


class TestParserMientras:
    """Tests de parsing de sentencias mientras"""
    
    def test_mientras_simple(self):
        """Test parsing de mientras simple"""
        fuente = "#lang: es\nmientras True:\n    x = x + 1"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        assert isinstance(prog.sentencias[0], SentenciaMientras)
        assert len(prog.sentencias[0].cuerpo) == 1


class TestParserRomperSiguiente:
    """Tests de parsing de romper y siguiente"""
    
    def test_romper(self):
        """Test parsing de romper"""
        fuente = "#lang: es\nmientras True:\n    romper"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        while_stmt = prog.sentencias[0]
        assert isinstance(while_stmt, SentenciaMientras)
        assert isinstance(while_stmt.cuerpo[0], SentenciaRomper)
    
    def test_siguiente(self):
        """Test parsing de siguiente"""
        fuente = "#lang: es\nmientras True:\n    siguiente"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        while_stmt = prog.sentencias[0]
        assert isinstance(while_stmt, SentenciaMientras)
        assert isinstance(while_stmt.cuerpo[0], SentenciaSiguiente)


class TestParserLanzar:
    """Tests de parsing de lanzar"""
    
    def test_lanzar_simple(self):
        """Test parsing de lanzar simple"""
        fuente = "#lang: es\nlanzar f()"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        assert isinstance(prog.sentencias[0], SentenciaLanzar)
        assert isinstance(prog.sentencias[0].llamada, LlamadaFuncion)


class TestParserRetornar:
    """Tests de parsing de retornar"""
    
    def test_retornar_con_valor(self):
        """Test parsing de retornar con valor"""
        fuente = "#lang: es\nfuncion f() -> int:\n    retornar 42"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        func = prog.sentencias[0]
        assert isinstance(func.cuerpo[0], SentenciaRetornar)
        assert isinstance(func.cuerpo[0].expr, LiteralNumero)
    
    def test_retornar_con_transferencia(self):
        """Test parsing de retornar con transferencia"""
        fuente = "#lang: es\nfuncion f() -> int:\n    retornar -> x"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        func = prog.sentencias[0]
        assert isinstance(func.cuerpo[0], SentenciaRetornar)
        assert func.cuerpo[0].es_transferencia == True


class TestParserEscuchar:
    """Tests de parsing de escuchar"""
    
    def test_escuchar_simple(self):
        """Test parsing de escuchar simple"""
        fuente = "#lang: es\nescuchar canal -> respuesta()"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        assert isinstance(prog.sentencias[0], SentenciaEscuchar)
        assert isinstance(prog.sentencias[0].respuesta, LlamadaFuncion)


class TestParserRecuperar:
    """Tests de parsing de recuperar"""
    
    def test_recuperar_simple(self):
        """Test parsing de recuperar simple"""
        fuente = "#lang: es\naccion_critica() recuperar: plan_b()"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        assert isinstance(prog.sentencias[0], SentenciaRecuperar)


class TestParserImportar:
    """Tests de parsing de importar"""
    
    def test_importar_simple(self):
        """Test parsing de importar simple"""
        fuente = "#lang: es\nimportar std.io"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        assert isinstance(prog.sentencias[0], SentenciaImportar)
        assert prog.sentencias[0].ruta == "std.io"
    
    def test_importar_anidado(self):
        """Test parsing de importar con ruta anidada"""
        fuente = "#lang: es\nimportar std.math.funciones"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        assert prog.sentencias[0].ruta == "std.math.funciones"


class TestParserAsignacion:
    """Tests de parsing de asignación"""
    
    def test_asignacion_simple(self):
        """Test parsing de asignación simple"""
        fuente = "#lang: es\nx = 42"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        assert isinstance(prog.sentencias[0], AsignacionVariable)
        assert prog.sentencias[0].nombre == "x"
    
    def test_asignacion_campo(self):
        """Test parsing de asignación de campo"""
        fuente = "#lang: es\npunto.x = 10"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        assert isinstance(prog.sentencias[0], AsignacionCampo)
        assert prog.sentencias[0].nombre_campo == "x"


class TestParserExpresiones:
    """Tests de parsing de expresiones"""
    
    def test_operadores_aritmeticos(self):
        """Test precedence de operadores aritméticos"""
        fuente = "#lang: es\nx = 1 + 2 * 3"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        assign = prog.sentencias[0]
        expr = assign.expresion
        assert isinstance(expr, OpBinaria)
        assert expr.operador == "+"
        assert isinstance(expr.derecho, OpBinaria)
        assert expr.derecho.operador == "*"
    
    def test_operadores_comparacion(self):
        """Test parsing de operadores de comparación"""
        fuente = "#lang: es\nx = 1 > 2"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        assign = prog.sentencias[0]
        assert isinstance(assign.expresion, OpBinaria)
        assert assign.expresion.operador == ">"
    
    def test_operador_unario(self):
        """Test parsing de operador unario"""
        fuente = "#lang: es\nx = -5"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        assign = prog.sentencias[0]
        assert isinstance(assign.expresion, OpUnaria)
        assert assign.expresion.operador == "-"
    
    def test_parentesis(self):
        """Test parsing de paréntesis"""
        fuente = "#lang: es\nx = (1 + 2) * 3"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        assign = prog.sentencias[0]
        expr = assign.expresion
        assert isinstance(expr, OpBinaria)
        assert expr.operador == "*"
        assert isinstance(expr.izquierdo, OpBinaria)
        assert expr.izquierdo.operador == "+"


class TestParserLlamadaFuncion:
    """Tests de parsing de llamadas a función"""
    
    def test_llamada_sin_argumentos(self):
        """Test parsing de llamada sin argumentos"""
        fuente = "#lang: es\nx = f()"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        assign = prog.sentencias[0]
        assert isinstance(assign.expresion, LlamadaFuncion)
        assert assign.expresion.nombre == "f"
        assert len(assign.expresion.argumentos) == 0
    
    def test_llamada_con_argumentos(self):
        """Test parsing de llamada con argumentos"""
        fuente = "#lang: es\nx = f(1, 2, 3)"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        assign = prog.sentencias[0]
        assert isinstance(assign.expresion, LlamadaFuncion)
        assert len(assign.expresion.argumentos) == 3
    
    def test_llamada_con_transferencia(self):
        """Test parsing de llamada con argumento transferido"""
        fuente = "#lang: es\nx = f(-> var)"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        assign = prog.sentencias[0]
        assert isinstance(assign.expresion, LlamadaFuncion)
        assert len(assign.expresion.argumentos) == 1
        assert isinstance(assign.expresion.argumentos[0], ArgumentoTransferido)


class TestParserAccesoCampo:
    """Tests de parsing de acceso a campo"""
    
    def test_acceso_campo_simple(self):
        """Test parsing de acceso a campo simple"""
        fuente = "#lang: es\nx = obj.campo"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        assign = prog.sentencias[0]
        assert isinstance(assign.expresion, ExprAccesoCampo)
        assert assign.expresion.nombre_campo == "campo"


class TestParserTensor:
    """Tests de parsing de tensores"""
    
    def test_tensor_simple(self):
        """Test parsing de tensor simple"""
        fuente = "#lang: es\nx = tensor(3, 4)"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        assign = prog.sentencias[0]
        assert isinstance(assign.expresion, ExprTensor)


class TestParserLiterales:
    """Tests de parsing de literales"""
    
    def test_literal_entero(self):
        """Test parsing de literal entero"""
        fuente = "#lang: es\nx = 42"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        assign = prog.sentencias[0]
        assert isinstance(assign.expresion, LiteralNumero)
        assert assign.expresion.valor == 42
    
    def test_literal_decimal(self):
        """Test parsing de literal decimal"""
        fuente = "#lang: es\nx = 3.14"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        assign = prog.sentencias[0]
        assert isinstance(assign.expresion, LiteralDecimal)
        assert assign.expresion.valor == 3.14
    
    def test_literal_cadena(self):
        """Test parsing de literal cadena"""
        fuente = '#lang: es\nx = "hola"'
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        assign = prog.sentencias[0]
        assert isinstance(assign.expresion, LiteralCadena)
        assert assign.expresion.valor == "hola"


class TestParserRecuperacionErrores:
    """Tests de recuperación de errores en parsing"""
    
    def test_error_sincronizacion(self):
        """Test que el parser se sincroniza después de error"""
        fuente = "#lang: es\nfuncion f( -> int:\nfuncion g() -> int:\n    retornar 1"
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        
        # Debería haber errores pero continuar parsing
        assert diag.hay_errores()
        # La segunda función debería parsearse correctamente
        assert len(prog.sentencias) >= 1
