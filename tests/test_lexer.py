import pytest
from lexer import Lexer, DICCIONARIOS, TOKEN_UNICARACTER, TOKEN_BICARACTER
from ast_nodes import TokenID, Token
from exceptions import SynapseError


class TestLexerBasico:
    """Tests básicos de tokenización"""
    
    def test_tokenizar_vacio(self):
        """Test que archivo vacío lanza error"""
        with pytest.raises(SynapseError, match="Falta declaración de idioma"):
            lexer = Lexer("")
            lexer.tokenizar()
    
    def test_falta_lang(self):
        """Test que falta #lang lanza error"""
        with pytest.raises(SynapseError, match="Falta declaración de idioma"):
            lexer = Lexer("x = 1")
            lexer.tokenizar()
    
    def test_lang_vacio(self):
        """Test que #lang vacío lanza error"""
        with pytest.raises(SynapseError, match="Código de idioma vacío"):
            lexer = Lexer("#lang:")
            lexer.tokenizar()
    
    def test_lang_no_soportado(self):
        """Test que idioma no soportado lanza error"""
        with pytest.raises(SynapseError, match="Idioma 'xx' no soportado"):
            lexer = Lexer("#lang: xx")
            lexer.tokenizar()


class TestLexerNumeros:
    """Tests de tokenización de números"""
    
    def test_entero_simple(self):
        """Test tokenización de entero simple"""
        lexer = Lexer("#lang: es\nx = 42")
        tokens = lexer.tokenizar()
        assert TokenID.NUMBER in [t.tipo for t in tokens]
        assert any(t.valor == 42 for t in tokens)
    
    def test_decimal_simple(self):
        """Test tokenización de decimal simple"""
        lexer = Lexer("#lang: es\nx = 3.14")
        tokens = lexer.tokenizar()
        assert TokenID.FLOAT in [t.tipo for t in tokens]
        assert any(t.valor == 3.14 for t in tokens)
    
    def test_entero_cero(self):
        """Test tokenización de cero"""
        lexer = Lexer("#lang: es\nx = 0")
        tokens = lexer.tokenizar()
        assert any(t.tipo == TokenID.NUMBER and t.valor == 0 for t in tokens)
    
    def test_decimal_cero(self):
        """Test tokenización de 0.0"""
        lexer = Lexer("#lang: es\nx = 0.0")
        tokens = lexer.tokenizar()
        assert any(t.tipo == TokenID.FLOAT and t.valor == 0.0 for t in tokens)


class TestLexerCadenas:
    """Tests de tokenización de cadenas"""
    
    def test_cadena_comillas_dobles(self):
        """Test cadena con comillas dobles"""
        lexer = Lexer('#lang: es\nx = "hola"')
        tokens = lexer.tokenizar()
        assert TokenID.STRING in [t.tipo for t in tokens]
        assert any(t.valor == "hola" for t in tokens)
    
    def test_cadena_comillas_simples(self):
        """Test cadena con comillas simples"""
        lexer = Lexer("#lang: es\nx = 'mundo'")
        tokens = lexer.tokenizar()
        assert TokenID.STRING in [t.tipo for t in tokens]
        assert any(t.valor == "mundo" for t in tokens)
    
    def test_cadena_vacia(self):
        """Test cadena vacía"""
        lexer = Lexer('#lang: es\nx = ""')
        tokens = lexer.tokenizar()
        assert any(t.tipo == TokenID.STRING and t.valor == "" for t in tokens)
    
    def test_cadena_sin_cerrar(self):
        """Test cadena sin cerrar lanza error"""
        with pytest.raises(SynapseError, match="Cadena sin cerrar"):
            lexer = Lexer('#lang: es\nx = "abierto')
            lexer.tokenizar()


class TestLexerOperadores:
    """Tests de tokenización de operadores"""
    
    def test_operadores_aritmeticos(self):
        """Test operadores aritméticos básicos"""
        lexer = Lexer("#lang: es\nx = 1 + 2 - 3 * 4 / 5 % 6")
        tokens = lexer.tokenizar()
        operadores = [t.tipo for t in tokens if t.tipo in (TokenID.PLUS, TokenID.MINUS, 
                                                             TokenID.STAR, TokenID.SLASH, 
                                                             TokenID.MODULO)]
        assert TokenID.PLUS in operadores
        assert TokenID.MINUS in operadores
        assert TokenID.STAR in operadores
        assert TokenID.SLASH in operadores
        assert TokenID.MODULO in operadores
    
    def test_operadores_comparacion(self):
        """Test operadores de comparación"""
        lexer = Lexer("#lang: es\nx = 1 > 2 < 3 == 4 != 5 <= 6 >= 7")
        tokens = lexer.tokenizar()
        assert TokenID.GREATER in [t.tipo for t in tokens]
        assert TokenID.LESS in [t.tipo for t in tokens]
        assert TokenID.EQUALS in [t.tipo for t in tokens]
        assert TokenID.NOT_EQUALS in [t.tipo for t in tokens]
        assert TokenID.LESS_EQUALS in [t.tipo for t in tokens]
        assert TokenID.GREATER_EQUALS in [t.tipo for t in tokens]
    
    def test_operador_asignacion(self):
        """Test operador de asignación"""
        lexer = Lexer("#lang: es\nx = 1")
        tokens = lexer.tokenizar()
        assert TokenID.ASSIGN in [t.tipo for t in tokens]
    
    def test_operador_arrow(self):
        """Test operador arrow"""
        lexer = Lexer("#lang: es\nfuncion f(x: int) -> int:")
        tokens = lexer.tokenizar()
        assert TokenID.ARROW in [t.tipo for t in tokens]
    
    def test_operador_unario(self):
        """Test operador unario menos"""
        lexer = Lexer("#lang: es\nx = -5")
        tokens = lexer.tokenizar()
        assert TokenID.MINUS in [t.tipo for t in tokens]


class TestLexerIdentificadores:
    """Tests de tokenización de identificadores"""
    
    def test_identificador_simple(self):
        """Test identificador simple"""
        lexer = Lexer("#lang: es\nx = 1")
        tokens = lexer.tokenizar()
        assert TokenID.IDENTIFIER in [t.tipo for t in tokens]
        assert any(t.valor == "x" for t in tokens)
    
    def test_identificador_con_guion_bajo(self):
        """Test identificador con guion bajo"""
        lexer = Lexer("#lang: es\nmi_var = 1")
        tokens = lexer.tokenizar()
        assert any(t.tipo == TokenID.IDENTIFIER and t.valor == "mi_var" for t in tokens)
    
    def test_identificador_con_numeros(self):
        """Test identificador con números"""
        lexer = Lexer("#lang: es\nvar123 = 1")
        tokens = lexer.tokenizar()
        assert any(t.tipo == TokenID.IDENTIFIER and t.valor == "var123" for t in tokens)


class TestLexerKeywords:
    """Tests de tokenización de keywords poliglota"""
    
    def test_keywords_espanol(self):
        """Test keywords en español"""
        lexer = Lexer("#lang: es\nsi x > 0:\n    funcion f():\n        retornar 1")
        tokens = lexer.tokenizar()
        assert TokenID.IF in [t.tipo for t in tokens]
        assert TokenID.FUNCTION in [t.tipo for t in tokens]
        assert TokenID.RETURN in [t.tipo for t in tokens]
    
    def test_keywords_ingles(self):
        """Test keywords en inglés"""
        lexer = Lexer("#lang: en\nif x > 0:\n    function f():\n        return 1")
        tokens = lexer.tokenizar()
        assert TokenID.IF in [t.tipo for t in tokens]
        assert TokenID.FUNCTION in [t.tipo for t in tokens]
        assert TokenID.RETURN in [t.tipo for t in tokens]
    
    def test_keywords_mientras(self):
        """Test keyword mientras/while"""
        lexer = Lexer("#lang: es\nmientras x > 0:\n    x = x - 1")
        tokens = lexer.tokenizar()
        assert TokenID.WHILE in [t.tipo for t in tokens]
    
    def test_keywords_lanzar(self):
        """Test keyword lanzar/spawn"""
        lexer = Lexer("#lang: es\nlanzar f()")
        tokens = lexer.tokenizar()
        assert TokenID.SPAWN in [t.tipo for t in tokens]
    
    def test_keywords_escuchar(self):
        """Test keyword escuchar/listen"""
        lexer = Lexer("#lang: es\nescuchar canal -> respuesta()")
        tokens = lexer.tokenizar()
        assert TokenID.LISTEN in [t.tipo for t in tokens]
    
    def test_keywords_recuperar(self):
        """Test keyword recuperar/recover"""
        lexer = Lexer("#lang: es\naccion_critica() recuperar: plan_b()")
        tokens = lexer.tokenizar()
        assert TokenID.RECOVER in [t.tipo for t in tokens]
    
    def test_keywords_romper(self):
        """Test keyword romper/break"""
        lexer = Lexer("#lang: es\nmientras True:\n    romper")
        tokens = lexer.tokenizar()
        assert TokenID.BREAK in [t.tipo for t in tokens]
    
    def test_keywords_siguiente(self):
        """Test keyword siguiente/continue"""
        lexer = Lexer("#lang: es\nmientras True:\n    siguiente")
        tokens = lexer.tokenizar()
        assert TokenID.CONTINUE in [t.tipo for t in tokens]
    
    def test_keywords_importar(self):
        """Test keyword importar/import"""
        lexer = Lexer("#lang: es\nimportar std.io")
        tokens = lexer.tokenizar()
        assert TokenID.IMPORT in [t.tipo for t in tokens]
    
    def test_keywords_estructura(self):
        """Test keyword estructura/struct"""
        lexer = Lexer("#lang: es\nestructura Punto:")
        tokens = lexer.tokenizar()
        assert TokenID.STRUCT in [t.tipo for t in tokens]


class TestLexerIndentacion:
    """Tests de procesamiento de indentación"""
    
    def test_indentacion_correcta(self):
        """Test indentación correcta genera INDENT/DEDENT"""
        lexer = Lexer("#lang: es\nsi True:\n    x = 1\ny = 2")
        tokens = lexer.tokenizar()
        assert TokenID.INDENT in [t.tipo for t in tokens]
        assert TokenID.DEDENT in [t.tipo for t in tokens]
    
    def test_indentacion_invalida(self):
        """Test indentación no múltiplo de 4 lanza error"""
        with pytest.raises(SynapseError, match="múltiplo de 4 espacios"):
            lexer = Lexer("#lang: es\nsi True:\n  x = 1")
            lexer.tokenizar()
    
    def test_indentacion_inconsistente(self):
        """Test indentación inconsistente lanza error"""
        with pytest.raises(SynapseError, match="múltiplo de 4 espacios"):
            lexer = Lexer("#lang: es\nsi True:\n    x = 1\n  y = 2")
            lexer.tokenizar()
    
    def test_indentacion_multiple_niveles(self):
        """Test múltiples niveles de indentación"""
        lexer = Lexer("#lang: es\nsi True:\n    si False:\n        x = 1\n    y = 2")
        tokens = lexer.tokenizar()
        indent_count = sum(1 for t in tokens if t.tipo == TokenID.INDENT)
        dedent_count = sum(1 for t in tokens if t.tipo == TokenID.DEDENT)
        assert indent_count == 2
        assert dedent_count == 2


class TestLexerComentarios:
    """Tests de procesamiento de comentarios"""
    
    def test_comentario_linea(self):
        """Test comentario de línea"""
        lexer = Lexer("#lang: es\nx = 1 // esto es un comentario\ny = 2")
        tokens = lexer.tokenizar()
        # El comentario debe ser ignorado
        assert not any("esto es un comentario" in str(t) for t in tokens)
    
    def test_comentario_inicio_linea(self):
        """Test comentario al inicio de línea"""
        lexer = Lexer("#lang: es\n// comentario completo\nx = 1")
        tokens = lexer.tokenizar()
        assert len([t for t in tokens if t.tipo == TokenID.NUMBER]) == 1
    
    def test_comentario_doble_slash(self):
        """Test comentario con //"""
        lexer = Lexer("#lang: es\nx = 1 // comentario con doble slash")
        tokens = lexer.tokenizar()
        # El comentario debe ser ignorado
        assert not any("comentario con doble slash" in str(t) for t in tokens)


class TestLexerPuntuacion:
    """Tests de tokenización de puntuación"""
    
    def test_parentesis(self):
        """Test paréntesis"""
        lexer = Lexer("#lang: es\nx = f(1, 2)")
        tokens = lexer.tokenizar()
        assert TokenID.LPAREN in [t.tipo for t in tokens]
        assert TokenID.RPAREN in [t.tipo for t in tokens]
    
    def test_coma(self):
        """Test coma"""
        lexer = Lexer("#lang: es\nx = f(1, 2)")
        tokens = lexer.tokenizar()
        assert TokenID.COMMA in [t.tipo for t in tokens]
    
    def test_dos_puntos(self):
        """Test dos puntos"""
        lexer = Lexer("#lang: es\nsi True:")
        tokens = lexer.tokenizar()
        assert TokenID.COLON in [t.tipo for t in tokens]
    
    def test_punto(self):
        """Test punto para acceso a campo"""
        lexer = Lexer("#lang: es\nx = obj.campo")
        tokens = lexer.tokenizar()
        assert TokenID.DOT in [t.tipo for t in tokens]


class TestLexerEOF:
    """Tests de token EOF"""
    
    def test_token_eof(self):
        """Test que siempre se genera token EOF"""
        lexer = Lexer("#lang: es\nx = 1")
        tokens = lexer.tokenizar()
        assert tokens[-1].tipo == TokenID.EOF


class TestLexerNewline:
    """Tests de token NEWLINE"""
    
    def test_token_newline(self):
        """Test que se generan tokens NEWLINE"""
        lexer = Lexer("#lang: es\nx = 1\ny = 2")
        tokens = lexer.tokenizar()
        newline_count = sum(1 for t in tokens if t.tipo == TokenID.NEWLINE)
        assert newline_count >= 2


class TestLexerCaracterInvalido:
    """Tests de caracteres inválidos"""
    
    def test_caracter_invalido(self):
        """Test carácter inválido lanza error"""
        with pytest.raises(SynapseError, match="Carácter inesperado"):
            lexer = Lexer("#lang: es\nx = @")
            lexer.tokenizar()
