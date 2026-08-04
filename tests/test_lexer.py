import pytest
from compilador.lexer import Lexer, DICCIONARIOS, TOKEN_UNICARACTER, TOKEN_BICARACTER
from compilador.ast_nodes import TokenID, Token


class TestLexerBasico:
    """Tests b??sicos de tokenizaci??n"""
    
    def test_tokenizar_vacio(self):
        """Test que archivo vac??o lanza error"""
        with pytest.raises(SyntaxError, match="Error Crítico: Falta declaración de idioma"):
            lexer = Lexer("")
            lexer.tokenizar()
    
    def test_falta_lang(self):
        """Test que falta #lang lanza error"""
        with pytest.raises(SyntaxError, match="Error Crítico: Falta declaración de idioma"):
            lexer = Lexer("x = 1")
            lexer.tokenizar()
    
    def test_lang_vacio(self):
        """Test que #lang vac??o lanza error"""
        with pytest.raises(SyntaxError, match="Error Crítico: Código de idioma vacío"):
            lexer = Lexer("#lang:")
            lexer.tokenizar()
    
    def test_lang_no_soportado(self):
        """Test que idioma no soportado lanza error"""
        with pytest.raises(SyntaxError, match="Error Crítico: Idioma 'xx' no soportado"):
            lexer = Lexer("#lang: xx")
            lexer.tokenizar()


class TestLexerNumeros:
    """Tests de tokenizaci??n de n??meros"""
    
    def test_entero_simple(self):
        """Test tokenizaci??n de entero simple"""
        lexer = Lexer("#lang: es\nx = 42")
        tokens = lexer.tokenizar()
        assert TokenID.NUMBER in [t.tipo for t in tokens]
        assert any(t.valor == 42 for t in tokens)
    
    def test_decimal_simple(self):
        """Test tokenizaci??n de decimal simple"""
        lexer = Lexer("#lang: es\nx = 3.14")
        tokens = lexer.tokenizar()
        assert TokenID.FLOAT in [t.tipo for t in tokens]
        assert any(t.valor == 3.14 for t in tokens)
    
    def test_entero_cero(self):
        """Test tokenizaci??n de cero"""
        lexer = Lexer("#lang: es\nx = 0")
        tokens = lexer.tokenizar()
        assert any(t.tipo == TokenID.NUMBER and t.valor == 0 for t in tokens)
    
    def test_decimal_cero(self):
        """Test tokenizaci??n de 0.0"""
        lexer = Lexer("#lang: es\nx = 0.0")
        tokens = lexer.tokenizar()
        assert any(t.tipo == TokenID.FLOAT and t.valor == 0.0 for t in tokens)


class TestLexerCadenas:
    """Tests de tokenizaci??n de cadenas"""
    
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
        """Test cadena vac??a"""
        lexer = Lexer('#lang: es\nx = ""')
        tokens = lexer.tokenizar()
        assert any(t.tipo == TokenID.STRING and t.valor == "" for t in tokens)
    
    def test_cadena_sin_cerrar(self):
        """Test cadena sin cerrar lanza error"""
        with pytest.raises(SyntaxError, match="Error Léxico.*Cadena sin cerrar"):
            lexer = Lexer('#lang: es\nx = "abierto')
            lexer.tokenizar()


class TestLexerOperadores:
    """Tests de tokenizaci??n de operadores"""
    
    def test_operadores_aritmeticos(self):
        """Test operadores aritm??ticos b??sicos"""
        lexer = Lexer("#lang: es\nx = 1 + 2 - 3 * 4 / 5 % 6")
        tokens = lexer.tokenizar()
        operadores = [t.tipo for t in tokens if t.tipo in (TokenID.PLUS, TokenID.MINUS, 
                                                             TokenID.STAR, TokenID.SLASH, 
                                                             TokenID.MOD)]
        assert TokenID.PLUS in operadores
        assert TokenID.MINUS in operadores
        assert TokenID.STAR in operadores
        assert TokenID.SLASH in operadores
        assert TokenID.MOD in operadores
    
    def test_operadores_comparacion(self):
        """Test operadores de comparaci??n"""
        lexer = Lexer("#lang: es\nx = 1 > 2 < 3 == 4 != 5 <= 6 >= 7")
        tokens = lexer.tokenizar()
        assert TokenID.GREATER in [t.tipo for t in tokens]
        assert TokenID.LESS in [t.tipo for t in tokens]
        assert TokenID.EQUALS in [t.tipo for t in tokens]
        assert TokenID.NOT_EQUALS in [t.tipo for t in tokens]
        assert TokenID.LESS_EQUALS in [t.tipo for t in tokens]
        assert TokenID.GREATER_EQUALS in [t.tipo for t in tokens]
    
    def test_operador_asignacion(self):
        """Test operador de asignaci??n"""
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
    """Tests de tokenizaci??n de identificadores"""
    
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
        """Test identificador con n??meros"""
        lexer = Lexer("#lang: es\nvar123 = 1")
        tokens = lexer.tokenizar()
        assert any(t.tipo == TokenID.IDENTIFIER and t.valor == "var123" for t in tokens)


class TestLexerKeywords:
    """Tests de tokenizaci??n de keywords poliglota"""
    
    def test_keywords_espanol(self):
        """Test keywords en espa??ol"""
        lexer = Lexer("#lang: es\nsi x > 0:\n    funcion f():\n        retornar 1")
        tokens = lexer.tokenizar()
        assert TokenID.SI in [t.tipo for t in tokens]
        assert TokenID.FUNCION in [t.tipo for t in tokens]
        assert TokenID.RETORNAR in [t.tipo for t in tokens]
    
    def test_keywords_ingles(self):
        """Test keywords en ingl??s"""
        lexer = Lexer("#lang: en\nif x > 0:\n    function f():\n        return 1")
        tokens = lexer.tokenizar()
        assert TokenID.SI in [t.tipo for t in tokens]
        assert TokenID.FUNCION in [t.tipo for t in tokens]
        assert TokenID.RETORNAR in [t.tipo for t in tokens]
    
    def test_keywords_mientras(self):
        """Test keyword mientras/while"""
        lexer = Lexer("#lang: es\nmientras x > 0:\n    x = x - 1")
        tokens = lexer.tokenizar()
        assert TokenID.MIENTRAS in [t.tipo for t in tokens]
    
    def test_keywords_lanzar(self):
        """Test keyword lanzar/spawn"""
        lexer = Lexer("#lang: es\nlanzar f()")
        tokens = lexer.tokenizar()
        assert TokenID.LANZAR in [t.tipo for t in tokens]
    
    def test_keywords_escuchar(self):
        """Test keyword escuchar/listen"""
        lexer = Lexer("#lang: es\nescuchar canal -> respuesta()")
        tokens = lexer.tokenizar()
        assert TokenID.ESCUCHAR in [t.tipo for t in tokens]
    
    def test_keywords_recuperar(self):
        """Test keyword recuperar/recover"""
        lexer = Lexer("#lang: es\naccion_critica() recuperar: plan_b()")
        tokens = lexer.tokenizar()
        assert TokenID.RECUPERAR in [t.tipo for t in tokens]
    
    def test_keywords_romper(self):
        """Test keyword romper/break"""
        lexer = Lexer("#lang: es\nmientras True:\n    romper")
        tokens = lexer.tokenizar()
        assert TokenID.ROMPER in [t.tipo for t in tokens]
    
    def test_keywords_siguiente(self):
        """Test keyword siguiente/continue"""
        lexer = Lexer("#lang: es\nmientras True:\n    siguiente")
        tokens = lexer.tokenizar()
        assert TokenID.SIGUIENTE in [t.tipo for t in tokens]
    
    def test_keywords_importar(self):
        """Test keyword importar/import"""
        lexer = Lexer("#lang: es\nimportar std.io")
        tokens = lexer.tokenizar()
        assert TokenID.IMPORTAR in [t.tipo for t in tokens]
    
    def test_keywords_estructura(self):
        """Test keyword estructura/struct"""
        lexer = Lexer("#lang: es\nestructura Punto:")
        tokens = lexer.tokenizar()
        assert TokenID.ESTRUCTURA in [t.tipo for t in tokens]


class TestLexerKeywordsNuevos:
    """AUDITORIA F1 (H22/H22-F1.2): keywords del Manual 2 §3 conectados al lexer
    Python. F1.2: tipo/tensor/nulo/ok/err/algun/ninguno ACTIVADOS con soporte de
    parser contextual (declaración `tipo X = ...`, `tensor()` expresión, `nulo`
    literal/tipo, constructores ADT en coincidir). NO conectados: rc (variable de
    retorno ubicua) y modulo (parámetro en nucleo/generator.syn:343) — requieren
    diseño de parser propio (deuda D-F1 restante, ver docs/AUDITORIA_ALINEACION_MANUALES.md).
    """

    def test_keyword_let(self):
        """Test keyword let"""
        lexer = Lexer("#lang: es\nlet x = 1")
        tokens = lexer.tokenizar()
        assert TokenID.LET in [t.tipo for t in tokens]

    def test_keyword_delegar(self):
        """Test keyword delegar"""
        lexer = Lexer("#lang: es\ndelegar f()")
        tokens = lexer.tokenizar()
        assert TokenID.DELEGAR in [t.tipo for t in tokens]

    def test_modulo_sigue_siendo_identificador(self):
        """modulo NO es keyword: colisión con el parámetro 'modulo' de
        nucleo/generator.syn (gen_emitir_traza) — rompería el bootstrap.
        El operador % sigue siendo T_MOD."""
        lexer = Lexer("#lang: es\nmodulo = 5")
        tokens = lexer.tokenizar()
        assert any(t.tipo == TokenID.IDENTIFIER and t.valor == "modulo" for t in tokens)
        lexer2 = Lexer("#lang: es\nx = 1 % 2")
        assert TokenID.MOD in [t.tipo for t in lexer2.tokenizar()]

    def test_keyword_arc(self):
        """Test keyword arc"""
        lexer = Lexer("#lang: es\nx = arc(1)")
        tokens = lexer.tokenizar()
        assert TokenID.ARC in [t.tipo for t in tokens]

    def test_keyword_debil(self):
        """Test keyword débil (Manual 2 §3: es='débil')"""
        lexer = Lexer("#lang: es\nx = débil puntero")
        tokens = lexer.tokenizar()
        assert TokenID.DEBIL in [t.tipo for t in tokens]

    def test_keyword_export(self):
        """Test keyword @export (T_EXPORT)"""
        lexer = Lexer("#lang: en\n@export(web) function f():")
        tokens = lexer.tokenizar()
        assert TokenID.EXPORT in [t.tipo for t in tokens]

    def test_export_requiere_palabra(self):
        """'@' suelto sigue siendo error (paridad con test_caracter_invalido)"""
        with pytest.raises(SyntaxError, match="Error Léxico.*Carácter inesperado"):
            Lexer("#lang: es\nx = @").tokenizar()

    def test_rc_sigue_siendo_identificador(self):
        """rc NO es keyword (colisión con variable de retorno en std/cluster.syn)"""
        lexer = Lexer("#lang: es\nrc = cluster_iniciar_nodo(0)")
        tokens = lexer.tokenizar()
        assert TokenID.IDENTIFIER in [t.tipo for t in tokens]
        assert any(t.tipo == TokenID.IDENTIFIER and t.valor == "rc" for t in tokens)

    def test_keyword_tipo(self):
        """F1.2: keyword tipo (T_TIPO, Manual 2 §3 es='tipo')"""
        lexer = Lexer("#lang: es\ntipo Edad = entero")
        tokens = lexer.tokenizar()
        assert TokenID.TIPO in [t.tipo for t in tokens]

    def test_keyword_tensor(self):
        """F1.2: keyword tensor (T_TENSOR, Manual 2 §3 es='tensor')"""
        lexer = Lexer("#lang: es\nx = tensor(2, 3)")
        tokens = lexer.tokenizar()
        assert TokenID.TENSOR in [t.tipo for t in tokens]

    def test_keyword_nulo(self):
        """F1.2: keyword nulo (T_NULO, Manual 2 §3 es='nulo')"""
        lexer = Lexer("#lang: es\nsi x == nulo:")
        tokens = lexer.tokenizar()
        assert TokenID.NULO in [t.tipo for t in tokens]

    def test_keywords_adts(self):
        """F1.2: constructores ADT ok/err/algun/ninguno (Manual 2 §4.2)"""
        lexer = Lexer("#lang: es\nok(v) =>\nerr(e) =>\nalgun(v) =>\nninguno")
        tokens = lexer.tokenizar()
        tipos = [t.tipo for t in tokens]
        assert TokenID.OK in tipos
        assert TokenID.ERR in tipos
        assert TokenID.ALGUN in tipos
        assert TokenID.NINGUNO in tipos

    def test_keywords_contextuales_conservan_lexema(self):
        """F1.2: los keywords contextuales conservan su lexema en Token.valor
        para que el parser los use como campo/variable/tipo."""
        lexer = Lexer('#lang: es\nsi tipo == "x":\n    m = tensor(1, 1)')
        tokens = lexer.tokenizar()
        t_tipo = [t for t in tokens if t.tipo == TokenID.TIPO][0]
        assert t_tipo.valor == "tipo"
        t_tensor = [t for t in tokens if t.tipo == TokenID.TENSOR][0]
        assert t_tensor.valor == "tensor"

    def test_tipo_multiidioma_en(self):
        """F1.2: Manual 2 §3 en: type/tensor/null/ok/err/some/none"""
        lexer = Lexer("#lang: en\ntype X = int\nif x == null:")
        tokens = lexer.tokenizar()
        tipos = [t.tipo for t in tokens]
        assert TokenID.TIPO in tipos
        assert TokenID.NULO in tipos
        lexer2 = Lexer("#lang: en\nsome(v) =>\nnone")
        tipos2 = [t.tipo for t in lexer2.tokenizar()]
        assert TokenID.ALGUN in tipos2
        assert TokenID.NINGUNO in tipos2

    def test_tipo_multiidioma_fr_pt(self):
        """F1.2: Manual 2 §3 fr (tenseur/nul/aucun) y pt (algum/nenhum)"""
        lexer_fr = Lexer("#lang: fr\ntype X = tenseur\nx = nul")
        tipos_fr = [t.tipo for t in lexer_fr.tokenizar()]
        assert TokenID.TENSOR in tipos_fr
        assert TokenID.NULO in tipos_fr
        lexer_pt = Lexer("#lang: pt\nalgum(v) =>\nnenhum")
        tipos_pt = [t.tipo for t in lexer_pt.tokenizar()]
        assert TokenID.ALGUN in tipos_pt
        assert TokenID.NINGUNO in tipos_pt

    def test_token_pipe(self):
        """F1.2: '|' tokeniza como PIPE (separador de constructores, Manual 2 §2)"""
        lexer = Lexer("#lang: es\ntipo X = ok(entero) | err(texto)")
        tokens = lexer.tokenizar()
        assert TokenID.PIPE in [t.tipo for t in tokens]


class TestLexerIndentacion:
    """Tests de procesamiento de indentaci??n"""
    
    def test_indentacion_correcta(self):
        """Test indentaci??n correcta genera INDENT/DEDENT"""
        lexer = Lexer("#lang: es\nsi True:\n    x = 1\ny = 2")
        tokens = lexer.tokenizar()
        assert TokenID.INDENT in [t.tipo for t in tokens]
        assert TokenID.DEDENT in [t.tipo for t in tokens]
    
    def test_indentacion_invalida(self):
        """Test indentaci??n no m??ltiplo de 4 lanza error"""
        with pytest.raises(SyntaxError, match="Error.*indentación debe ser múltiplo de 4"):
            lexer = Lexer("#lang: es\nsi True:\n  x = 1")
            lexer.tokenizar()
    
    def test_indentacion_inconsistente(self):
        """Test indentaci??n inconsistente lanza error"""
        with pytest.raises(SyntaxError, match="Error.*La indentación debe ser múltiplo de 4 espacios"):
            lexer = Lexer("#lang: es\nsi True:\n    x = 1\n  y = 2")
            lexer.tokenizar()
    
    def test_indentacion_multiple_niveles(self):
        """Test m??ltiples niveles de indentaci??n"""
        lexer = Lexer("#lang: es\nsi True:\n    si False:\n        x = 1\n    y = 2")
        tokens = lexer.tokenizar()
        indent_count = sum(1 for t in tokens if t.tipo == TokenID.INDENT)
        dedent_count = sum(1 for t in tokens if t.tipo == TokenID.DEDENT)
        assert indent_count == 2
        assert dedent_count == 2


class TestLexerComentarios:
    """Tests de procesamiento de comentarios"""
    
    def test_comentario_linea(self):
        """Test comentario de l??nea"""
        lexer = Lexer("#lang: es\nx = 1 // esto es un comentario\ny = 2")
        tokens = lexer.tokenizar()
        # El comentario debe ser ignorado
        assert not any("esto es un comentario" in str(t) for t in tokens)
    
    def test_comentario_inicio_linea(self):
        """Test comentario al inicio de l??nea"""
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
    """Tests de tokenizaci??n de puntuaci??n"""
    
    def test_parentesis(self):
        """Test par??ntesis"""
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
    """Tests de caracteres inv??lidos"""
    
    def test_caracter_invalido(self):
        """Test car??cter inv??lido lanza error"""
        with pytest.raises(SyntaxError, match="Error Léxico.*Carácter inesperado"):
            lexer = Lexer("#lang: es\nx = @")
            lexer.tokenizar()

