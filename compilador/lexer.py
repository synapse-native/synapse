# cumple Manual 1 §6: infraestructura Python del compilador Synapse (r153)
from typing import List, Optional, Dict
from compilador.ast_nodes import TokenID, Token
from exceptions import SynapseError


DICCIONARIOS: Dict[str, Dict[str, TokenID]] = {
    'es': {
        'si': TokenID.SI,
        'sino': TokenID.SINO,
        'funcion': TokenID.FUNCION,
        'retornar': TokenID.RETORNAR,
        'lanzar': TokenID.LANZAR,
        'recuperar': TokenID.RECUPERAR,
        'escuchar': TokenID.ESCUCHAR,
        'mientras': TokenID.MIENTRAS,
        'romper': TokenID.ROMPER,
        'siguiente': TokenID.SIGUIENTE,
        'importar': TokenID.IMPORTAR,
        'estructura': TokenID.ESTRUCTURA,
        'y': TokenID.AND,
        'o': TokenID.OR,
        'no': TokenID.NOT,
        'verdadero': TokenID.VERDADERO,
        'falso': TokenID.FALSO,
        'inseguro': TokenID.INSEGURO,
        'importar_c': TokenID.IMPORTAR_C,
        'externo': TokenID.EXTERNO,
        'coincidir': TokenID.COINCIDIR,
        'requiere': TokenID.REQUIERE,
        'garantiza': TokenID.GARANTIZA,
        'canal': TokenID.CANAL,
        'asm': TokenID.ASM,
        'constante': TokenID.CONSTANTE,
        'para': TokenID.PARA,
        # AUDITORIA F1 (H22): keywords del Manual 2 §3 conectados al lexer.
        # F1.2 (D-F1 resuelta): activados tipo/tensor/nulo/ok/err/algun/ninguno
        # con soporte de parser contextual (declaración `tipo X = ...`, `tensor()`
        # como expresión, `nulo` literal/tipo, constructores ADT en coincidir).
        # F1.4 (D-F1 cerrada): rc/modulo activados como keywords CONTEXTUALES —
        # colisionan con identificadores reales (rc = variable de retorno en
        # std/cluster.syn:149; modulo = parámetro en nucleo/generator.syn:343),
        # por lo que el parser los acepta también donde un identificador vale
        # (ver TOKENS_CONTEXTUALES y parser_base.es_token_identificador).
        'let': TokenID.LET,
        'delegar': TokenID.DELEGAR,
        'arc': TokenID.ARC,
        'débil': TokenID.DEBIL,
        '@export': TokenID.EXPORT,
        'rc': TokenID.RC,
        'modulo': TokenID.MODULO,
        'tipo': TokenID.TIPO,
        'tensor': TokenID.TENSOR,
        'nulo': TokenID.NULO,
        'ok': TokenID.OK,
        'err': TokenID.ERR,
        'algun': TokenID.ALGUN,
        'ninguno': TokenID.NINGUNO,
    },
    'en': {
        'if': TokenID.SI,
        'else': TokenID.SINO,
        'function': TokenID.FUNCION,
        'return': TokenID.RETORNAR,
        'spawn': TokenID.LANZAR,
        'recover': TokenID.RECUPERAR,
        'listen': TokenID.ESCUCHAR,
        'while': TokenID.MIENTRAS,
        'break': TokenID.ROMPER,
        'continue': TokenID.SIGUIENTE,
        'import': TokenID.IMPORTAR,
        'struct': TokenID.ESTRUCTURA,
        'and': TokenID.AND,
        'or': TokenID.OR,
        'not': TokenID.NOT,
        'true': TokenID.VERDADERO,
        'false': TokenID.FALSO,
        'unsafe': TokenID.INSEGURO,
        'import_c': TokenID.IMPORTAR_C,
        'extern': TokenID.EXTERNO,
        'match': TokenID.COINCIDIR,
        'asm': TokenID.ASM,
        'constant': TokenID.CONSTANTE,
        'for': TokenID.PARA,
        'let': TokenID.LET,
        'delegate': TokenID.DELEGAR,
        'arc': TokenID.ARC,
        'weak': TokenID.DEBIL,
        '@export': TokenID.EXPORT,
        'rc': TokenID.RC,
        'module': TokenID.MODULO,
        'type': TokenID.TIPO,
        'tensor': TokenID.TENSOR,
        'null': TokenID.NULO,
        'ok': TokenID.OK,
        'err': TokenID.ERR,
        'some': TokenID.ALGUN,
        'none': TokenID.NINGUNO,
    },
    'fr': {
        'si': TokenID.SI,
        'sinon': TokenID.SINO,
        'fonction': TokenID.FUNCION,
        'retourner': TokenID.RETORNAR,
        'lancer': TokenID.LANZAR,
        'recuperer': TokenID.RECUPERAR,
        'ecouter': TokenID.ESCUCHAR,
        'tantque': TokenID.MIENTRAS,
        'rompre': TokenID.ROMPER,
        'continuer': TokenID.SIGUIENTE,
        'importer': TokenID.IMPORTAR,
        'structure': TokenID.ESTRUCTURA,
        'et': TokenID.AND,
        'ou': TokenID.OR,
        'non': TokenID.NOT,
        'vrai': TokenID.VERDADERO,
        'faux': TokenID.FALSO,
        'dangereux': TokenID.INSEGURO,
        'importer_c': TokenID.IMPORTAR_C,
        'externe': TokenID.EXTERNO,
        'correspondre': TokenID.COINCIDIR,
        'asm': TokenID.ASM,
        'constante': TokenID.CONSTANTE,
        'pour': TokenID.PARA,
        'let': TokenID.LET,
        'déléguer': TokenID.DELEGAR,
        'arc': TokenID.ARC,
        'faible': TokenID.DEBIL,
        '@export': TokenID.EXPORT,
        'rc': TokenID.RC,
        'module': TokenID.MODULO,
        'type': TokenID.TIPO,
        'tenseur': TokenID.TENSOR,
        'nul': TokenID.NULO,
        'ok': TokenID.OK,
        'err': TokenID.ERR,
        'some': TokenID.ALGUN,
        'aucun': TokenID.NINGUNO,
    },
    'pt': {
        'se': TokenID.SI,
        'senao': TokenID.SINO,
        'funcao': TokenID.FUNCION,
        'retornar': TokenID.RETORNAR,
        'lancar': TokenID.LANZAR,
        'recuperar': TokenID.RECUPERAR,
        'escutar': TokenID.ESCUCHAR,
        'enquanto': TokenID.MIENTRAS,
        'parar': TokenID.ROMPER,
        'continuar': TokenID.SIGUIENTE,
        'importar': TokenID.IMPORTAR,
        'estrutura': TokenID.ESTRUCTURA,
        'e': TokenID.AND,
        'ou': TokenID.OR,
        'nao': TokenID.NOT,
        'verdadeiro': TokenID.VERDADERO,
        'falso': TokenID.FALSO,
        'inseguro': TokenID.INSEGURO,
        'importar_c': TokenID.IMPORTAR_C,
        'externo': TokenID.EXTERNO,
        'coincidir': TokenID.COINCIDIR,
        'asm': TokenID.ASM,
        'constante': TokenID.CONSTANTE,
        'fuer': TokenID.PARA,
        'let': TokenID.LET,
        'delegar': TokenID.DELEGAR,
        'arc': TokenID.ARC,
        'fraco': TokenID.DEBIL,
        '@export': TokenID.EXPORT,
        'rc': TokenID.RC,
        'modulo': TokenID.MODULO,
        'tipo': TokenID.TIPO,
        'tensor': TokenID.TENSOR,
        'nulo': TokenID.NULO,
        'ok': TokenID.OK,
        'err': TokenID.ERR,
        'algum': TokenID.ALGUN,
        'nenhum': TokenID.NINGUNO,
    },
    'de': {
        'wenn': TokenID.SI,
        'sonst': TokenID.SINO,
        'funktion': TokenID.FUNCION,
        'rueckgabe': TokenID.RETORNAR,
        'starten': TokenID.LANZAR,
        'wiederherstellen': TokenID.RECUPERAR,
        'hoeren': TokenID.ESCUCHAR,
        'waehrend': TokenID.MIENTRAS,
        'abbrechen': TokenID.ROMPER,
        'fortsetzen': TokenID.SIGUIENTE,
        'importieren': TokenID.IMPORTAR,
        'struktur': TokenID.ESTRUCTURA,
        'und': TokenID.AND,
        'oder': TokenID.OR,
        'nicht': TokenID.NOT,
        'wahr': TokenID.VERDADERO,
        'falsch': TokenID.FALSO,
        'unsicher': TokenID.INSEGURO,
        'import_c': TokenID.IMPORTAR_C,
        'extern': TokenID.EXTERNO,
        'entsprechen': TokenID.COINCIDIR,
        'asm': TokenID.ASM,
        'konstante': TokenID.CONSTANTE,
        # de/it no están en la tabla del Manual 2 §3 (solo es/en/fr/pt):
        # fallback EN documentado.
        'let': TokenID.LET,
        'delegate': TokenID.DELEGAR,
        'arc': TokenID.ARC,
        'weak': TokenID.DEBIL,
        '@export': TokenID.EXPORT,
        'rc': TokenID.RC,
        'module': TokenID.MODULO,
        'type': TokenID.TIPO,
        'tensor': TokenID.TENSOR,
        'null': TokenID.NULO,
        'ok': TokenID.OK,
        'err': TokenID.ERR,
        'some': TokenID.ALGUN,
        'none': TokenID.NINGUNO,
    },
    'it': {
        'se': TokenID.SI,
        'altrimenti': TokenID.SINO,
        'funzione': TokenID.FUNCION,
        'restituisci': TokenID.RETORNAR,
        'lancia': TokenID.LANZAR,
        'recupera': TokenID.RECUPERAR,
        'ascolta': TokenID.ESCUCHAR,
        'mentre': TokenID.MIENTRAS,
        'interrompi': TokenID.ROMPER,
        'continua': TokenID.SIGUIENTE,
        'importa': TokenID.IMPORTAR,
        'struttura': TokenID.ESTRUCTURA,
        'e': TokenID.AND,
        'o': TokenID.OR,
        'non': TokenID.NOT,
        'vero': TokenID.VERDADERO,
        'falso': TokenID.FALSO,
        'non_sicuro': TokenID.INSEGURO,
        'importa_c': TokenID.IMPORTAR_C,
        'esterno': TokenID.EXTERNO,
        'corrispondere': TokenID.COINCIDIR,
        'asm': TokenID.ASM,
        'costante': TokenID.CONSTANTE,
        'per': TokenID.PARA,
        'let': TokenID.LET,
        'delegate': TokenID.DELEGAR,
        'arc': TokenID.ARC,
        'weak': TokenID.DEBIL,
        '@export': TokenID.EXPORT,
        'rc': TokenID.RC,
        'module': TokenID.MODULO,
        'type': TokenID.TIPO,
        'tensor': TokenID.TENSOR,
        'null': TokenID.NULO,
        'ok': TokenID.OK,
        'err': TokenID.ERR,
        'some': TokenID.ALGUN,
        'none': TokenID.NINGUNO,
    },
}

DICCIONARIOS_INVERSO: Dict[str, Dict[TokenID, str]] = {}
for _idioma, _mapa in DICCIONARIOS.items():
    DICCIONARIOS_INVERSO[_idioma] = {v: k for k, v in _mapa.items()}


# AUDITORIA F1.2 (D-F1) + F1.4: keywords CONTEXTUALES del Manual 2 §3. Se
# tokenizan como su TokenID (activación completa del lexer), pero el parser los
# acepta también donde un identificador es válido (campo x.tipo, variable tipo,
# parámetro tensor, patrón ok(...), tipo nulo/tensor, variable rc, parámetro
# modulo). Para eso el lexer conserva el LEXEMA en Token.valor de estos tokens
# (los demás keywords mantienen valor=None como antes).
TOKENS_CONTEXTUALES: frozenset = frozenset({
    TokenID.TIPO, TokenID.TENSOR, TokenID.NULO,
    TokenID.OK, TokenID.ERR, TokenID.ALGUN, TokenID.NINGUNO,
    TokenID.ARC, TokenID.DEBIL, TokenID.RC, TokenID.MODULO,
})


OPERADORES_BINARIOS: dict[TokenID, str] = {
    TokenID.GREATER: '>',
    TokenID.LESS: '<',
    TokenID.EQUALS: '==',
    TokenID.NOT_EQUALS: '!=',
    TokenID.LESS_EQUALS: '<=',
    TokenID.GREATER_EQUALS: '>=',
    TokenID.PLUS: '+',
    TokenID.MINUS: '-',
    TokenID.STAR: '*',
    TokenID.SLASH: '/',
    TokenID.MOD: '%',
    TokenID.AND: '&&',
    TokenID.OR: '||',
}

TOKEN_UNICARACTER: dict[str, TokenID] = {
    '>': TokenID.GREATER,
    '<': TokenID.LESS,
    '=': TokenID.ASSIGN,
    '+': TokenID.PLUS,
    '-': TokenID.MINUS,
    '*': TokenID.STAR,
    '/': TokenID.SLASH,
    '%': TokenID.MOD,
    '(': TokenID.LPAREN,
    ')': TokenID.RPAREN,
    ':': TokenID.COLON,
    ',': TokenID.COMMA,
    '.': TokenID.DOT,
    '&': TokenID.AMPERSAND,
    ';': TokenID.SEMICOLON,
    '!': TokenID.NOT,
    '[': TokenID.LBRACKET,
    ']': TokenID.RBRACKET,
    '|': TokenID.PIPE,  # Manual 2 §2: separador de constructores en declaracion_tipo
    '?': TokenID.INTERROGACION,  # D-6: operador '?' postfijo (Manual 3 §7 L331-342)
}

TOKEN_BICARACTER: dict[str, TokenID] = {
    '->': TokenID.ARROW,
    '=>': TokenID.ARROW_RIGHT,
    '==': TokenID.EQUALS,
    '!=': TokenID.NOT_EQUALS,
    '<=': TokenID.LESS_EQUALS,
    '>=': TokenID.GREATER_EQUALS,
    '<-': TokenID.ARROW_LEFT,
}


class Lexer:
    def __init__(self, fuente: str, diccionario: Optional[Dict[str, TokenID]] = None,
                 idioma: Optional[str] = None):
        self.fuente = fuente
        self.lineas = fuente.split('\n')
        # Limpiar BOM UTF-8 si está presente (Manual 1 §4)
        if self.lineas and self.lineas[0].startswith('\ufeff'):
            self.lineas[0] = self.lineas[0].lstrip('\ufeff')
        self.tokens: List[Token] = []
        self.linea_actual = 0
        self.pila_indent = [0]
        self.diccionario = diccionario
        self.idioma = idioma
        self.is_no_std = False
        # cumple Manual 8 §4.1 (r153 H-R153-4): continuación de llamadas
        # multilínea — los módulos canónicos (lint/formatter/reports) parten
        # llamadas entre líneas dentro de paréntesis/corchetes. Mientras haya
        # un ( [ abierto, la línea siguiente NO emite NEWLINE/INDENT/DEDENT.
        self.profundidad = 0

    def tokenizar(self) -> List[Token]:
        self._detectar_idioma()
        self._procesar_lineas()
        while self.pila_indent[-1] > 0:
            self.pila_indent.pop()
            self.tokens.append(Token(TokenID.DEDENT, linea=self.linea_actual, columna=0))
        self.tokens.append(Token(TokenID.EOF, linea=self.linea_actual, columna=0))
        # H-F1.4-1: cumple Manual 1 §3.1 — el lexer SOLO tokeniza; la
        # validación de cuerpo-bloque tras 'funcion:' es del PARSER (fase de
        # AST). El método _validar_cuerpos del lexer se ELIMINA (código muerto;
        # regla de gobernanza: "código muerto se elimina"); TestParserFunciones
        # y RecuperacionErrores conservan la cobertura en la fase correcta.
        return self.tokens

    def _detectar_idioma(self):
        if not self.fuente.strip():
            # F1.4: cumple Manual 2 §2 — misma familia de error que 'falta
            # #lang': sin declaracion de idioma el lexer no puede seleccionar
            # diccionario (grupo de entrada del _detectar_idioma).
            raise SynapseError(
                "Error Crítico: Falta declaración de idioma '#lang: <codigo>' en la línea 1", 1, 0
            )
        primera = self.lineas[0].strip()
        if not primera.startswith('#lang:'):
            raise SynapseError(
                "Error Crítico: Falta declaración de idioma '#lang: <codigo>' en la línea 1", 1, 0
            )
        codigo = primera[len('#lang:'):].strip()
        if not codigo:
            raise SynapseError("Error Crítico: Código de idioma vacío en #lang:", 1, 0)
        self.idioma = codigo
        if self.diccionario is None:
            if codigo not in DICCIONARIOS:
                raise SynapseError(
                    f"Error Crítico: Idioma '{codigo}' no soportado. Soporte: {', '.join(DICCIONARIOS)}", 1, 0
                )
            self.diccionario = DICCIONARIOS[codigo]

        if len(self.lineas) >= 2:
            segunda = self.lineas[1].strip()
            if segunda == '#pragma: no_std':
                self.is_no_std = True

    def _procesar_lineas(self):
        for i, linea in enumerate(self.lineas):
            self.linea_actual = i + 1
            texto = linea.strip()
            if not texto or texto.startswith('//') or texto.startswith('#'):
                continue

            # cumple Manual 8 §4.1 (r153 H-R153-4): en continuación (paréntesis
            # abierto de una llamada partida entre líneas) no se procesa la
            # indentación — los tokens fluyen como una sola expresión.
            if self.profundidad == 0:
                self._procesar_indentacion(linea)
            self._tokenizar_linea(texto)
            if self.profundidad > 0:
                continue
            self.tokens.append(Token(TokenID.NEWLINE, linea=self.linea_actual, columna=0))

    def _procesar_indentacion(self, linea: str):
        espacios_ini = len(linea) - len(linea.lstrip(' '))
        if espacios_ini % 4 != 0:
            raise SynapseError(
                "Error Léxico: La indentación debe ser múltiplo de 4 espacios", self.linea_actual, 0
            )
        nivel = espacios_ini // 4

        if nivel > self.pila_indent[-1]:
            self.pila_indent.append(nivel)
            self.tokens.append(Token(TokenID.INDENT, linea=self.linea_actual, columna=0))
        elif nivel < self.pila_indent[-1]:
            while self.pila_indent and nivel < self.pila_indent[-1]:
                self.pila_indent.pop()
                self.tokens.append(Token(TokenID.DEDENT, linea=self.linea_actual, columna=0))
            if nivel != self.pila_indent[-1]:
                raise SynapseError(
                    "Nivel de indentación inconsistente", self.linea_actual, 0
                )

    def _tokenizar_linea(self, texto: str):
        i = 0
        despues_de_punto = False
        while i < len(texto):
            if texto[i] == ' ':
                i += 1
                continue

            if texto[i:i+2] == '//':
                break

            if texto[i] in ('"', "'"):
                comilla = texto[i]
                inicio = i
                escapando = False
                valor_chars = []
                i += 1
                while i < len(texto):
                    ch = texto[i]
                    if escapando:
                        if ch == 'n':
                            valor_chars.append('\n')
                        elif ch == 't':
                            valor_chars.append('\t')
                        elif ch == 'r':
                            valor_chars.append('\r')
                        elif ch == '\\':
                            valor_chars.append('\\')
                        elif ch == comilla:
                            valor_chars.append(comilla)
                        elif ch == 'u':
                            # Escape Unicode: \uXXXX
                            hex_str = ''
                            for _ in range(4):
                                i += 1
                                if i < len(texto) and texto[i] in '0123456789abcdefABCDEF':
                                    hex_str += texto[i]
                                else:
                                    raise SynapseError(
                                        "Error Léxico: Escape Unicode incompleto, se esperan 4 dígitos hexadecimales",
                                        self.linea_actual, inicio
                                    )
                            codepoint = int(hex_str, 16)
                            valor_chars.append(chr(codepoint))
                        else:
                            valor_chars.append('\\' + ch)
                        escapando = False
                        i += 1
                        continue
                    if ch == '\\':
                        escapando = True
                        i += 1
                        continue
                    if ch == comilla:
                        i += 1
                        break
                    valor_chars.append(ch)
                    i += 1
                else:
                    raise SynapseError(
                        "Error Léxico: Cadena sin cerrar", self.linea_actual, inicio
                    )
                valor = ''.join(valor_chars)
                self.tokens.append(
                    Token(TokenID.STRING, linea=self.linea_actual, columna=inicio, valor=valor)
                )
                continue

            bicar = texto[i:i+2]
            if bicar in TOKEN_BICARACTER:
                self.tokens.append(
                    Token(TOKEN_BICARACTER[bicar], linea=self.linea_actual, columna=i)
                )
                i += 2
                continue

            if texto[i] == '@':
                # AUDITORIA F1 (H22): @export (T_EXPORT, Manual 2 §3).
                # '@' seguido de una palabra conocida (p.ej. '@export'); si no
                # hay palabra o no está en el diccionario -> error (paridad
                # con el comportamiento previo de '@' como carácter inesperado).
                inicio = i
                i += 1
                while i < len(texto) and (texto[i].isalnum() or texto[i] == '_'):
                    i += 1
                palabra = texto[inicio:i]
                if self.diccionario and palabra in self.diccionario:
                    self.tokens.append(
                        Token(self.diccionario[palabra], linea=self.linea_actual, columna=inicio)
                    )
                    continue
                # Reportar el token desconocido completo ('@' suelto o '@foo').
                raise SynapseError(
                    f"Error Léxico: Carácter inesperado '{palabra}'", self.linea_actual, inicio
                )

            if texto[i] in TOKEN_UNICARACTER:
                tok = Token(TOKEN_UNICARACTER[texto[i]], linea=self.linea_actual, columna=i)
                self.tokens.append(tok)
                # cumple Manual 8 §4.1 (r153 H-R153-4): seguir la profundidad de
                # ( y [ para permitir llamadas multilínea (los corchetes de
                # cadena no cuentan: ya se consumieron como STRING).
                if tok.tipo == TokenID.LPAREN or tok.tipo == TokenID.LBRACKET:
                    self.profundidad += 1
                elif tok.tipo == TokenID.RPAREN or tok.tipo == TokenID.RBRACKET:
                    if self.profundidad > 0:
                        self.profundidad -= 1
                if tok.tipo == TokenID.DOT:
                    despues_de_punto = True
                else:
                    despues_de_punto = False
                i += 1
                continue

            if texto[i].isdigit():
                inicio = i
                es_float = False
                while i < len(texto) and texto[i].isdigit():
                    i += 1
                if i < len(texto) and texto[i] == '.':
                    es_float = True
                    i += 1
                    while i < len(texto) and texto[i].isdigit():
                        i += 1
                # Notación científica: 1e3, 1.2e-3, 1.5E+2
                if i < len(texto) and texto[i] in ('e', 'E'):
                    es_float = True
                    i += 1
                    if i < len(texto) and texto[i] in ('+', '-'):
                        i += 1
                    while i < len(texto) and texto[i].isdigit():
                        i += 1
                if es_float:
                    valor = float(texto[inicio:i])
                    self.tokens.append(
                        Token(TokenID.FLOAT, linea=self.linea_actual, columna=inicio, valor=valor)
                    )
                else:
                    valor = int(texto[inicio:i])
                    self.tokens.append(
                        Token(TokenID.NUMBER, linea=self.linea_actual, columna=inicio, valor=valor)
                    )
                continue

            if texto[i].isalpha() or texto[i] == '_':
                inicio = i
                while i < len(texto) and (texto[i].isalnum() or texto[i] == '_'):
                    i += 1
                palabra = texto[inicio:i]
                # cumple Manual 2 2: después de DOT, tratar como identificador
                # (no keyword) para soportar acceso a campos como p.y, p.x, etc.
                # Si la palabra es un keyword seguida de '=' (asignación, no '=='),
                # también tratarla como identificador (e.g. 'y = 5' donde 'y' es
                # el keyword AND en español).
                # cumple Manual 2 §3 (ME r184_r185_e2e, H-R181-3): keyword + ':' →
                # identificador (posición de campo 'y: entero' y de parámetro
                # 'crear_punto(x, y)'), salvo abridores de bloque que legítimamente
                # preceden a ':' (sino:/requiere:/garantiza:/inseguro:/recuperar: —
                # el último con patrón: 'texto_a_entero(v) recuperar: -1').
                es_contexto_id = despues_de_punto
                # F1.4: cumple Manual 2 §3 — keywords CONTEXTUALES con paridad del
                # auto-hospedado (H-F1.4-2): 'modulo'/'module'/'rc' en posición
                # variable/parámetro ('modulo = 5', 'rc = f()', 'modulo: puntero')
                # emiten su TokenID preservando el lexema en .valor — el parser
                # los acepta como identificador. NO se degradan a IDENTIFIER
                # genérico (el oráculo test_keyword_* exige TokenID + lexema).
                tok_kw_contextual = self.diccionario.get(palabra) if self.diccionario else None
                es_kw_contextual = tok_kw_contextual in (
                    TokenID.MODULO, TokenID.RC, TokenID.ARC,
                )
                if not es_contexto_id and self.diccionario and palabra in self.diccionario:
                    _peek = i
                    while _peek < len(texto) and texto[_peek] == ' ':
                        _peek += 1
                    if _peek < len(texto) and texto[_peek] == '=':
                        if _peek + 1 < len(texto) and texto[_peek + 1] == '=':
                            pass  # es comparación ==, mantener keyword
                        else:
                            es_contexto_id = True  # asignación: 'y = ...' → identifier
                    elif _peek < len(texto) and texto[_peek] == ':':
                        if self.diccionario[palabra] not in (
                            TokenID.SINO, TokenID.REQUIERE, TokenID.GARANTIZA,
                            TokenID.INSEGURO, TokenID.RECUPERAR,
                            TokenID.VERDADERO, TokenID.FALSO, TokenID.NULO,
                        ):
                            es_contexto_id = True  # campo/parámetro: 'y: entero' → identifier
                if es_contexto_id and self.diccionario and palabra in self.diccionario:
                    if es_kw_contextual:
                        # F1.4: contexto de identificador → TokenID contextual con lexema
                        self.tokens.append(
                            Token(tok_kw_contextual, linea=self.linea_actual, columna=inicio, valor=palabra)
                        )
                    else:
                        self.tokens.append(
                            Token(TokenID.IDENTIFIER, linea=self.linea_actual, columna=inicio, valor=palabra)
                        )
                    despues_de_punto = False
                elif self.diccionario and palabra in self.diccionario:
                    tok_tipo = self.diccionario[palabra]
                    valor = palabra
                    self.tokens.append(
                        Token(tok_tipo, linea=self.linea_actual, columna=inicio, valor=valor)
                    )
                    despues_de_punto = False
                else:
                    self.tokens.append(
                        Token(TokenID.IDENTIFIER, linea=self.linea_actual, columna=inicio, valor=palabra)
                    )
                    despues_de_punto = False
                continue

            raise SynapseError(
                f"Error Léxico: Carácter inesperado '{texto[i]}'", self.linea_actual, i
            )
