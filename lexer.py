from typing import List, Optional, Dict
from ast_nodes import TokenID, Token


DICCIONARIOS: Dict[str, Dict[str, TokenID]] = {
    'es': {
        'si': TokenID.IF,
        'sino': TokenID.ELSE,
        'funcion': TokenID.FUNCTION,
        'retornar': TokenID.RETURN,
        'lanzar': TokenID.SPAWN,
        'recuperar': TokenID.RECOVER,
        'escuchar': TokenID.LISTEN,
        'mientras': TokenID.WHILE,
        'romper': TokenID.BREAK,
        'siguiente': TokenID.CONTINUE,
        'importar': TokenID.IMPORT,
        'estructura': TokenID.STRUCT,
        'y': TokenID.AND,
        'o': TokenID.OR,
        'no': TokenID.NOT,
        'verdadero': TokenID.TRUE,
        'falso': TokenID.FALSE,
        'inseguro': TokenID.INSEGURO,
        'importar_c': TokenID.IMPORTAR_C,
        'externo': TokenID.EXTERNO,
        'coincidir': TokenID.MATCH,
    },
    'en': {
        'if': TokenID.IF,
        'else': TokenID.ELSE,
        'function': TokenID.FUNCTION,
        'return': TokenID.RETURN,
        'spawn': TokenID.SPAWN,
        'recover': TokenID.RECOVER,
        'listen': TokenID.LISTEN,
        'while': TokenID.WHILE,
        'break': TokenID.BREAK,
        'continue': TokenID.CONTINUE,
        'import': TokenID.IMPORT,
        'struct': TokenID.STRUCT,
        'and': TokenID.AND,
        'or': TokenID.OR,
        'not': TokenID.NOT,
        'true': TokenID.TRUE,
        'false': TokenID.FALSE,
        'unsafe': TokenID.INSEGURO,
        'import_c': TokenID.IMPORTAR_C,
        'extern': TokenID.EXTERNO,
        'match': TokenID.MATCH,
    },
    'fr': {
        'si': TokenID.IF,
        'sinon': TokenID.ELSE,
        'fonction': TokenID.FUNCTION,
        'retourner': TokenID.RETURN,
        'lancer': TokenID.SPAWN,
        'recuperer': TokenID.RECOVER,
        'ecouter': TokenID.LISTEN,
        'tantque': TokenID.WHILE,
        'rompre': TokenID.BREAK,
        'continuer': TokenID.CONTINUE,
        'importer': TokenID.IMPORT,
        'structure': TokenID.STRUCT,
        'et': TokenID.AND,
        'ou': TokenID.OR,
        'non': TokenID.NOT,
        'vrai': TokenID.TRUE,
        'faux': TokenID.FALSE,
        'dangereux': TokenID.INSEGURO,
        'importer_c': TokenID.IMPORTAR_C,
        'externe': TokenID.EXTERNO,
        'correspondre': TokenID.MATCH,
    },
    'pt': {
        'se': TokenID.IF,
        'senao': TokenID.ELSE,
        'funcao': TokenID.FUNCTION,
        'retornar': TokenID.RETURN,
        'lancar': TokenID.SPAWN,
        'recuperar': TokenID.RECOVER,
        'escutar': TokenID.LISTEN,
        'enquanto': TokenID.WHILE,
        'parar': TokenID.BREAK,
        'continuar': TokenID.CONTINUE,
        'importar': TokenID.IMPORT,
        'estrutura': TokenID.STRUCT,
        'e': TokenID.AND,
        'ou': TokenID.OR,
        'nao': TokenID.NOT,
        'verdadeiro': TokenID.TRUE,
        'falso': TokenID.FALSE,
        'inseguro': TokenID.INSEGURO,
        'importar_c': TokenID.IMPORTAR_C,
        'externo': TokenID.EXTERNO,
        'coincidir': TokenID.MATCH,
    },
    'de': {
        'wenn': TokenID.IF,
        'sonst': TokenID.ELSE,
        'funktion': TokenID.FUNCTION,
        'rueckgabe': TokenID.RETURN,
        'starten': TokenID.SPAWN,
        'wiederherstellen': TokenID.RECOVER,
        'hoeren': TokenID.LISTEN,
        'waehrend': TokenID.WHILE,
        'abbrechen': TokenID.BREAK,
        'fortsetzen': TokenID.CONTINUE,
        'importieren': TokenID.IMPORT,
        'struktur': TokenID.STRUCT,
        'und': TokenID.AND,
        'oder': TokenID.OR,
        'nicht': TokenID.NOT,
        'wahr': TokenID.TRUE,
        'falsch': TokenID.FALSE,
        'unsicher': TokenID.INSEGURO,
        'import_c': TokenID.IMPORTAR_C,
        'extern': TokenID.EXTERNO,
        'entsprechen': TokenID.MATCH,
    },
    'it': {
        'se': TokenID.IF,
        'altrimenti': TokenID.ELSE,
        'funzione': TokenID.FUNCTION,
        'restituisci': TokenID.RETURN,
        'lancia': TokenID.SPAWN,
        'recupera': TokenID.RECOVER,
        'ascolta': TokenID.LISTEN,
        'mentre': TokenID.WHILE,
        'interrompi': TokenID.BREAK,
        'continua': TokenID.CONTINUE,
        'importa': TokenID.IMPORT,
        'struttura': TokenID.STRUCT,
        'e': TokenID.AND,
        'o': TokenID.OR,
        'non': TokenID.NOT,
        'vero': TokenID.TRUE,
        'falso': TokenID.FALSE,
        'non_sicuro': TokenID.INSEGURO,
        'importa_c': TokenID.IMPORTAR_C,
        'esterno': TokenID.EXTERNO,
        'corrispondere': TokenID.MATCH,
    },
}

DICCIONARIOS_INVERSO: Dict[str, Dict[TokenID, str]] = {}
for _idioma, _mapa in DICCIONARIOS.items():
    DICCIONARIOS_INVERSO[_idioma] = {v: k for k, v in _mapa.items()}


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
    TokenID.MODULO: '%',
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
    '%': TokenID.MODULO,
    '(': TokenID.LPAREN,
    ')': TokenID.RPAREN,
    ':': TokenID.COLON,
    ',': TokenID.COMMA,
    '.': TokenID.DOT,
    '&': TokenID.AMPERSAND,
}

TOKEN_BICARACTER: dict[str, TokenID] = {
    '->': TokenID.ARROW,
    '=>': TokenID.ARROW_RIGHT,
    '==': TokenID.EQUALS,
    '!=': TokenID.NOT_EQUALS,
    '<=': TokenID.LESS_EQUALS,
    '>=': TokenID.GREATER_EQUALS,
}


class Lexer:
    def __init__(self, fuente: str, diccionario: Optional[Dict[str, TokenID]] = None,
                 idioma: Optional[str] = None):
        self.fuente = fuente
        self.lineas = fuente.split('\n')
        self.tokens: List[Token] = []
        self.linea_actual = 0
        self.pila_indent = [0]
        self.diccionario = diccionario
        self.idioma = idioma

    def tokenizar(self) -> List[Token]:
        self._detectar_idioma()
        self._procesar_lineas()
        while self.pila_indent[-1] > 0:
            self.pila_indent.pop()
            self.tokens.append(Token(TokenID.DEDENT, linea=self.linea_actual, columna=0))
        self.tokens.append(Token(TokenID.EOF, linea=self.linea_actual, columna=0))
        return self.tokens

    def _detectar_idioma(self):
        if not self.lineas:
            raise SyntaxError("Error Crítico: Archivo vacío")
        primera = self.lineas[0].strip()
        if not primera.startswith('#lang:'):
            raise SyntaxError(
                "Error Crítico: Falta declaración de idioma '#lang: <codigo>' en la línea 1"
            )
        codigo = primera[len('#lang:'):].strip()
        if not codigo:
            raise SyntaxError("Error Crítico: Código de idioma vacío en #lang:")
        self.idioma = codigo
        if self.diccionario is None:
            if codigo not in DICCIONARIOS:
                raise SyntaxError(
                    f"Error Crítico: Idioma '{codigo}' no soportado. Soporte: {', '.join(DICCIONARIOS)}"
                )
            self.diccionario = DICCIONARIOS[codigo]

    def _procesar_lineas(self):
        for i, linea in enumerate(self.lineas):
            self.linea_actual = i + 1
            texto = linea.strip()
            if not texto or texto.startswith('//') or texto.startswith('#'):
                continue

            self._procesar_indentacion(linea)
            self._tokenizar_linea(texto)
            self.tokens.append(Token(TokenID.NEWLINE, linea=self.linea_actual, columna=0))

    def _procesar_indentacion(self, linea: str):
        espacios_ini = len(linea) - len(linea.lstrip(' '))
        if espacios_ini % 4 != 0:
            raise SyntaxError(
                f"Error (línea {self.linea_actual}): La indentación debe ser múltiplo de 4 espacios"
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
                raise SyntaxError(
                    f"Error (línea {self.linea_actual}): Nivel de indentación inconsistente"
                )

    def _tokenizar_linea(self, texto: str):
        i = 0
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
                        elif ch == '\\':
                            valor_chars.append('\\')
                        elif ch == comilla:
                            valor_chars.append(comilla)
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
                    raise SyntaxError(
                        f"Error Léxico (línea {self.linea_actual}): Cadena sin cerrar"
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

            if texto[i] in TOKEN_UNICARACTER:
                self.tokens.append(
                    Token(TOKEN_UNICARACTER[texto[i]], linea=self.linea_actual, columna=i)
                )
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
                if self.diccionario and palabra in self.diccionario:
                    self.tokens.append(
                        Token(self.diccionario[palabra], linea=self.linea_actual, columna=inicio)
                    )
                else:
                    self.tokens.append(
                        Token(TokenID.IDENTIFIER, linea=self.linea_actual, columna=inicio, valor=palabra)
                    )
                continue

            raise SyntaxError(
                f"Error Léxico (línea {self.linea_actual}): Carácter inesperado '{texto[i]}'"
            )
