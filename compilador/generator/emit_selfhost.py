"""
Generacion de codigo C auto-hospedado (tokenizer, parser, code generator).
Funciones migradas del original generator.py con adaptacion al patron
Composicion + Contexto.
"""

from .context import GeneratorContext



def emitir_token_defs(ctx: GeneratorContext, _unused=None):
        if ctx._gen_defs_emitido:
            return
        ctx._gen_defs_emitido = True
        ctx.lineas.extend([
            "// --- Token IDs ---",
            "#define T_IF 1",
            "#define T_ELSE 2",
            "#define T_FUNC 3",
            "#define T_RET 4",
            "#define T_SPAWN 5",
            "#define T_RECOVER 6",
            "#define T_LISTEN 7",
            "#define T_WHILE 8",
            "#define T_IMPORT 9",
            "#define T_BREAK 49",
            "#define T_CONTINUE 11",
            "#define T_DOT 12",
            "#define T_IDENT 13",
            "#define T_NUM 14",
            "#define T_STR 15",
            "#define T_GT 16",
            "#define T_LT 17",
            "#define T_EQ 25",
            "#define T_NE 26",
            "#define T_LE 27",
            "#define T_GE 28",
            "#define T_ASSIGN 29",
            "#define T_PLUS 30",
            "#define T_MINUS 31",
            "#define T_MUL 32",
            "#define T_DIV 33",
            "#define T_MOD 34",
            "#define T_ARROW 35",
            "#define T_LPAREN 38",
            "#define T_RPAREN 39",
            "#define T_COLON 40",
            "#define T_COMMA 41",
            "#define T_NL 42",
            "#define T_INDENT 43",
            "#define T_DEDENT 44",
            "#define T_EOF 57",
            "#define T_STRUCT 10",
            "#define T_AND 14",
            "#define T_OR 15",
            "#define T_NOT 16",
            "#define T_TRUE 17",
            "#define T_FALSE 18",
            "#define T_INSEGURO 46",
            "#define T_IMPORTAR_C 47",
            "#define T_AMPERSAND 45",
            "#define T_EXTERNO 48",
            "#define T_PIPE 58",
            "#define T_LET 59",
            "#define T_DELEGAR 60",
            "#define T_EXPORT 61",
            "#define T_ARC 62",
            "#define T_DEBIL 63",
            "#define T_RC 64",
            "#define T_MODULO 65",
            "",
            "#define MAX_TOKS 65536",
            "typedef struct { int tipo; int linea; int col; char val[1024]; } _P_Token;",
            "_P_Token _P_tks[MAX_TOKS];",
            "int _P_ntks = 0, _P_tpos = 0, _P_p_err = 0;",
            "int _P_pila_indent[64], _P_nivel_pila = 0;",
            "",
        ])

def gen_tok_c(ctx: GeneratorContext):
        if ctx._gen_tok_emitido:
            return
        ctx._gen_tok_emitido = True
        P = '_P_'
        ctx.lineas.extend([
            "void " + P + "tokenizar(const char* s, int len) {",
            "    int i = 0, li = 1, co = 1;",
            "    while (i < len && " + P + "ntks < MAX_TOKS - 1) {",
            "        if (" + P + "ntks >= MAX_TOKS - 1) { fprintf(stderr,\"FATAL: MAX_TOKS (%d) superado en tokenizador.\\n\",MAX_TOKS); exit(1); }",
            "        char c = s[i];",
            "        if (c == ' ' || c == '\\t') { i++; co++; continue; }",
"        if (c == '\\r') { i++; continue; }",
            "        if (c == '\\n') {",
            "            " + P + "tks[" + P + "ntks].tipo = T_NL; " + P + "tks[" + P + "ntks].linea = li; " + P + "tks[" + P + "ntks].col = 0;",
            "            " + P + "ntks++; i++; li++; co = 1;",
            "            if (i < len && s[i] == '\\r') { i++; }  // CRLF: saltar el \\r inicial de la siguiente linea",
            "            while (i < len && (s[i]==' '||s[i]=='\\t')) { if(s[i]==' ')co++; else co+=4; i++; }",
            "            if (i < len && s[i]=='\\n') continue;",
            "            if (i < len && s[i]=='#') { while(i<len&&s[i]!='\\n')i++; continue; }",
            "            if (i < len && s[i]=='/' && i+1<len && s[i+1]=='/') { while(i<len&&s[i]!='\\n')i++; continue; }",
            "            { int _sp = co-1;",
            "            if (_sp > " + P + "pila_indent[" + P + "nivel_pila]) {",
            "                " + P + "nivel_pila++; " + P + "pila_indent[" + P + "nivel_pila] = _sp;",
            "                " + P + "tks[" + P + "ntks].tipo = T_INDENT; " + P + "tks[" + P + "ntks].linea = li; " + P + "tks[" + P + "ntks].col = 0;",
            "                " + P + "ntks++;",
            "            } else if (_sp < " + P + "pila_indent[" + P + "nivel_pila]) {",
            "                while (" + P + "nivel_pila > 0 && _sp < " + P + "pila_indent[" + P + "nivel_pila]) {",
            "                    " + P + "tks[" + P + "ntks].tipo = T_DEDENT; " + P + "tks[" + P + "ntks].linea = li; " + P + "tks[" + P + "ntks].col = 0;",
            "                    " + P + "ntks++; " + P + "nivel_pila--;",
            "                }",
            "            } }",
            "            continue;",
            "        }",
            "        if (c == '/' && i+1 < len && s[i+1] == '/') {",
            "            while (i < len && s[i] != '\\n') i++; continue;",
            "        }",
            "        if (c == '#') {",
            "            while (i < len && s[i] != '\\n') i++; continue;",
            "        }",
"        if (c == '\"' || c == '\\'') {",
"            char q = c; int st = i; int scol = co; i++; co++;",
"            while (i < len && s[i] != q) { if (s[i] == '\\\\' && i+1 < len) { i++; co++; } i++; co++; }",
"            if (i >= len) break;",
"            i++; co++;",
            "            int _rlen = (i - st - 2) < 1023 ? (i - st - 2) : 1023;",
            "            char _tmp[1024]; strncpy(_tmp, s + st + 1, _rlen); _tmp[_rlen] = 0;",
            "            int _un = 0;",
            "            for (int _si = 0; _tmp[_si] && _un < 1022; _si++) {",
"                if (_tmp[_si] == 92 && _tmp[_si+1]) {",
"                    switch (_tmp[_si+1]) {",
            "                    case 34: " + P + "tks[" + P + "ntks].val[_un++] = 34; _si++; break;",
            "                    case 39: " + P + "tks[" + P + "ntks].val[_un++] = 39; _si++; break;",
            "                    case 92: " + P + "tks[" + P + "ntks].val[_un++] = 92; _si++; break;",
            "                    case 110: " + P + "tks[" + P + "ntks].val[_un++] = 10; _si++; break;",
            "                    case 116: " + P + "tks[" + P + "ntks].val[_un++] = 9; _si++; break;",
            "                    case 114: " + P + "tks[" + P + "ntks].val[_un++] = 13; _si++; break;",
            "                    case 48: " + P + "tks[" + P + "ntks].val[_un++] = 0; _si++; break;",
            "                    default: " + P + "tks[" + P + "ntks].val[_un++] = _tmp[_si]; break;",
"                    }",
"                } else {",
            "                    " + P + "tks[" + P + "ntks].val[_un++] = _tmp[_si];",
"                }",
"            }",
            "            " + P + "tks[" + P + "ntks].val[_un] = 0;",
            "            " + P + "tks[" + P + "ntks].tipo = T_STR; " + P + "tks[" + P + "ntks].linea = li; " + P + "tks[" + P + "ntks].col = scol;",
            "            " + P + "ntks++; continue;",

            "        }",
"        if (c >= '0' && c <= '9') {",
"            int st = i; int scol = co; while (i < len && s[i] >= '0' && s[i] <= '9') i++;",
"            if (i < len && s[i] == '.') { i++; while (i < len && s[i] >= '0' && s[i] <= '9') i++; }",
            "            int vl = (i - st) < 1023 ? (i - st) : 1023;",
            "            strncpy(" + P + "tks[" + P + "ntks].val, s + st, vl); " + P + "tks[" + P + "ntks].val[vl] = 0;",
            "            " + P + "tks[" + P + "ntks].tipo = T_NUM; " + P + "tks[" + P + "ntks].linea = li; " + P + "tks[" + P + "ntks].col = scol;",
            "            " + P + "ntks++; co += (i - st); continue;",
            "        }",
"        if ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || c == '_') {",
"            int st = i; int scol = co;",
"            // F1.2d: identificadores con bytes >= 0x80 (UTF-8) para keywords",
"            // acentuadas del Manual 2 S3 (p.ej. 'debil'); el resto ASCII puro.",
"            while (i < len && (((s[i] >= 'a' && s[i] <= 'z') || (s[i] >= 'A' && s[i] <= 'Z') || (s[i] >= '0' && s[i] <= '9') || s[i] == '_') || (unsigned char)s[i] >= 0x80)) i++;",
            "            int vl = (i - st) < 1023 ? (i - st) : 1023;",
            "            strncpy(" + P + "tks[" + P + "ntks].val, s + st, vl); " + P + "tks[" + P + "ntks].val[vl] = 0;",
            "            " + P + "tks[" + P + "ntks].linea = li; " + P + "tks[" + P + "ntks].col = scol;",
            '            typedef struct { const char* p; int t; } _KW;',
            '            const _KW _ks[] = {',
            '                {"si",T_IF},{"if",T_IF},{"se",T_IF},{"wenn",T_IF},',
            '                {"sino",T_ELSE},{"else",T_ELSE},{"sinon",T_ELSE},{"senao",T_ELSE},{"sonst",T_ELSE},{"altrimenti",T_ELSE},',
            '                {"funcion",T_FUNC},{"function",T_FUNC},{"fonction",T_FUNC},{"funcao",T_FUNC},{"funktion",T_FUNC},{"funzione",T_FUNC},',
            '                {"retornar",T_RET},{"return",T_RET},{"retourner",T_RET},{"retornar",T_RET},{"rueckgabe",T_RET},{"restituisci",T_RET},',
            '                {"lanzar",T_SPAWN},{"spawn",T_SPAWN},{"lancer",T_SPAWN},{"lancar",T_SPAWN},{"starten",T_SPAWN},{"lancia",T_SPAWN},',
            '                {"recuperar",T_RECOVER},{"recover",T_RECOVER},{"recuperer",T_RECOVER},{"recuperar",T_RECOVER},{"wiederherstellen",T_RECOVER},{"recupera",T_RECOVER},',
            '                {"escuchar",T_LISTEN},{"listen",T_LISTEN},{"ecouter",T_LISTEN},{"escutar",T_LISTEN},{"hoeren",T_LISTEN},{"ascolta",T_LISTEN},',
            '                {"mientras",T_WHILE},{"while",T_WHILE},{"tantque",T_WHILE},{"enquanto",T_WHILE},{"waehrend",T_WHILE},{"mentre",T_WHILE},',
            '                {"importar",T_IMPORT},{"import",T_IMPORT},{"importer",T_IMPORT},{"importar",T_IMPORT},{"importieren",T_IMPORT},{"importa",T_IMPORT},',
            '                {"romper",T_BREAK},{"break",T_BREAK},{"rompre",T_BREAK},{"parar",T_BREAK},{"abbrechen",T_BREAK},{"interrompi",T_BREAK},',
            '                {"siguiente",T_CONTINUE},{"continue",T_CONTINUE},{"continuer",T_CONTINUE},{"continuar",T_CONTINUE},{"fortsetzen",T_CONTINUE},{"continua",T_CONTINUE},',
            '                {"estructura",T_STRUCT},{"struct",T_STRUCT},{"structure",T_STRUCT},{"estrutura",T_STRUCT},{"struktur",T_STRUCT},{"struttura",T_STRUCT},',
            '                {"y",T_AND},{"and",T_AND},{"et",T_AND},{"e",T_AND},{"und",T_AND},',
            '                {"o",T_OR},{"or",T_OR},{"ou",T_OR},{"oder",T_OR},',
            '                {"no",T_NOT},{"not",T_NOT},{"non",T_NOT},{"nao",T_NOT},{"nicht",T_NOT},',
            '                {"verdadero",T_TRUE},{"true",T_TRUE},{"vrai",T_TRUE},{"verdadeiro",T_TRUE},{"wahr",T_TRUE},{"vero",T_TRUE},',
            '                {"falso",T_FALSE},{"false",T_FALSE},{"faux",T_FALSE},{"falsch",T_FALSE},',
            '                {"inseguro",T_INSEGURO},{"unsafe",T_INSEGURO},',
            '                {"importar_c",T_IMPORTAR_C},{"import_c",T_IMPORTAR_C},{"importer_c",T_IMPORTAR_C},{"importa_c",T_IMPORTAR_C},',
            '                {"externo",T_EXTERNO},{"extern",T_EXTERNO},{"externe",T_EXTERNO},{"esterno",T_EXTERNO},',
            '                {"let",T_LET},{"let",T_LET},{"let",T_LET},{"let",T_LET},',
            '                {"delegar",T_DELEGAR},{"delegate",T_DELEGAR},{"déléguer",T_DELEGAR},{"delegar",T_DELEGAR},',
            '                {"arc",T_ARC},{"arc",T_ARC},{"arc",T_ARC},{"arc",T_ARC},',
            '                {"débil",T_DEBIL},{"weak",T_DEBIL},{"faible",T_DEBIL},{"fraco",T_DEBIL},',
            '                // F1.4: rc/modulo (Manual 2 S3 L249/L255). Keywords contextuales:',
            '                // el parser los acepta tambien donde un identificador vale',
            '                // (variable rc, parametro modulo) — paridad con S1.',
            '                {"rc",T_RC},{"rc",T_RC},{"rc",T_RC},{"rc",T_RC},',
            '                {"modulo",T_MODULO},{"module",T_MODULO},{"module",T_MODULO},{"modulo",T_MODULO},',
            '                {NULL,0}',
            '            };',
            '            int _kt = T_IDENT;',
            '            for (int _ki = 0; _ks[_ki].p; _ki++) {',
            '                if (strcmp(' + P + 'tks[' + P + 'ntks].val, _ks[_ki].p) == 0) { _kt = _ks[_ki].t; break; }',
            '            }',
            '            ' + P + 'tks[' + P + 'ntks].tipo = _kt;',
            "            " + P + "ntks++; co += (i - st); continue;",
            "        }",
            "        if (c == '@') {",
            "            int st = i; int scol = co;",
            "            i++;",
            "            // F1.2d: identificadores con bytes >= 0x80 (UTF-8) para keywords",
"            // acentuadas del Manual 2 S3 (p.ej. 'debil'); el resto ASCII puro.",
"            while (i < len && (((s[i] >= 'a' && s[i] <= 'z') || (s[i] >= 'A' && s[i] <= 'Z') || (s[i] >= '0' && s[i] <= '9') || s[i] == '_') || (unsigned char)s[i] >= 0x80)) i++;",
            "            int vl = (i - st) < 1023 ? (i - st) : 1023;",
            "            strncpy(" + P + "tks[" + P + "ntks].val, s + st, vl); " + P + "tks[" + P + "ntks].val[vl] = 0;",
            "            " + P + "tks[" + P + "ntks].linea = li; " + P + "tks[" + P + "ntks].col = scol;",
            "            if (strcmp(" + P + "tks[" + P + "ntks].val, \"@export\") == 0) {",
            "                " + P + "tks[" + P + "ntks].tipo = T_EXPORT;",
            "            } else {",
            '                fprintf(stderr,"Error Lexico: caracter inesperado \'%s\' en linea %d\\n",' + P + 'tks[' + P + 'ntks].val, li); exit(1);',
            "            }",
            "            " + P + "ntks++; co += (i - st); continue;",
            "        }",
            "        if ((unsigned char)c >= 0x80) { i++; continue; }",
"        if (i+1 < len) {",
            "            if (c == '-' && s[i+1] == '>') {",
            "                " + P + "tks[" + P + "ntks].tipo = T_ARROW; " + P + "tks[" + P + "ntks].linea = li; " + P + "tks[" + P + "ntks].col = co;",
            "                " + P + "ntks++; i+=2; co+=2; continue;",
            "            }",
            "            if (c == '=' && s[i+1] == '=') {",
            "                " + P + "tks[" + P + "ntks].tipo = T_EQ; " + P + "tks[" + P + "ntks].linea = li; " + P + "tks[" + P + "ntks].col = co;",
            "                " + P + "ntks++; i+=2; co+=2; continue;",
            "            }",
            "            if (c == '!' && s[i+1] == '=') {",
            "                " + P + "tks[" + P + "ntks].tipo = T_NE; " + P + "tks[" + P + "ntks].linea = li; " + P + "tks[" + P + "ntks].col = co;",
            "                " + P + "ntks++; i+=2; co+=2; continue;",
            "            }",
            "            if (c == '<' && s[i+1] == '=') {",
            "                " + P + "tks[" + P + "ntks].tipo = T_LE; " + P + "tks[" + P + "ntks].linea = li; " + P + "tks[" + P + "ntks].col = co;",
            "                " + P + "ntks++; i+=2; co+=2; continue;",
            "            }",
            "            if (c == '>' && s[i+1] == '=') {",
            "                " + P + "tks[" + P + "ntks].tipo = T_GE; " + P + "tks[" + P + "ntks].linea = li; " + P + "tks[" + P + "ntks].col = co;",
            "                " + P + "ntks++; i+=2; co+=2; continue;",
            "            }",
            "        }",
            "        {",
            "            int tt = T_EOF;",
            "            if (c == '=') tt = T_ASSIGN;",
            "            else if (c == '+') tt = T_PLUS;",
            "            else if (c == '-') tt = T_MINUS;",
            "            else if (c == '*') tt = T_MUL;",
            "            else if (c == '/') tt = T_DIV;",
            "            else if (c == '%') tt = T_MOD;",
            "            else if (c == '(') tt = T_LPAREN;",
            "            else if (c == ')') tt = T_RPAREN;",
            "            else if (c == ':') tt = T_COLON;",
            "            else if (c == ',') tt = T_COMMA;",
            "            else if (c == '.') tt = T_DOT;",
            "            else if (c == '>') tt = T_GT;",
            "            else if (c == '<') tt = T_LT;",
            "            else if (c == '&') tt = T_AMPERSAND;",
            "            else if (c == '|') tt = T_PIPE;",
            "            if (tt == T_EOF) { fprintf(stderr,\"Error Lexico: caracter inesperado '%%c'(%%d) en linea %%d\\n\",c,c,li); exit(1); }",
            "            " + P + "tks[" + P + "ntks].tipo = tt; " + P + "tks[" + P + "ntks].linea = li; " + P + "tks[" + P + "ntks].col = co;",
            "            " + P + "ntks++; i++; co++;",
            "        }",
            "    }",
            "    while (" + P + "nivel_pila > 0) {",
            "        " + P + "tks[" + P + "ntks].tipo = T_DEDENT; " + P + "tks[" + P + "ntks].linea = li; " + P + "tks[" + P + "ntks].col = 0;",
            "        " + P + "ntks++; " + P + "nivel_pila--;",
            "    }",
            "    " + P + "tks[" + P + "ntks].tipo = T_EOF; " + P + "tks[" + P + "ntks].linea = li; " + P + "tks[" + P + "ntks].col = 0;",
            "    " + P + "ntks++;",
            "}",
            "",
            "void " + P + "procesar_indentacion_final() {",
            "    while (" + P + "nivel_pila > 0) {",
            "        " + P + "tks[" + P + "ntks].tipo = T_DEDENT; " + P + "tks[" + P + "ntks].linea = " + P + "tks[" + P + "ntks-1].linea; " + P + "tks[" + P + "ntks].col = 0;",
            "        " + P + "ntks++; " + P + "nivel_pila--;",
            "    }",
            "}",
            "",
        ])
def gen_parse(ctx: GeneratorContext):
        if ctx._gen_parse_emitido:
            return
        ctx._gen_parse_emitido = True
        # Write parser C code with _P_ prefix
        _P = '_P_'
        ctx.lineas.extend([
            "// --- AST builder helpers ---",
            "CadenaSegura " + _P + "cs(const char* s) {",
            "    CadenaSegura c; c.longitud = (int)strlen(s);",
            "    char* d = (char*)malloc(c.longitud + 1); strcpy(d, s); c.datos = d; return c;",
            "}",
            "struct ListaNodo* " + _P + "mk_list(struct Nodo* h, struct ListaNodo* t) {",
            "    struct ListaNodo* n = (struct ListaNodo*)calloc(1,sizeof(struct ListaNodo));",
            "    n->cabeza = h; n->cola = t; return n;",
            "}",
            "",
        ])
        # Helper + globals
        ctx.lineas.extend([
            "" + _P + "Token* " + _P + "mirar() { return &" + _P + "tks[" + _P + "tpos]; }",
            "void " + _P + "avanzar() { if (" + _P + "tpos < " + _P + "ntks) " + _P + "tpos++; }",
            "int " + _P + "posible(int t) { return " + _P + "mirar()->tipo == t ? 1 : 0; }",
            "int " + _P + "esperar(int t) {",
            "    if (" + _P + "mirar()->tipo == t) { " + _P + "avanzar(); return 1; }",
            '    fprintf(stderr, "[PARSER] L%d:%d: esperaba token %d, encontre %d\\n",',
            "            " + _P + "mirar()->linea, " + _P + "mirar()->col, t, " + _P + "mirar()->tipo);",
            "    exit(1);",
            "}",
            "void " + _P + "sinc_skip() {",
            "    while (" + _P + "tpos < " + _P + "ntks) {",
            "        int tt = " + _P + "mirar()->tipo;",
            "        if (tt == T_NL || tt == T_DEDENT || tt == T_EOF || tt == T_COMMA || tt == T_RPAREN || tt == T_COLON) break;",
            "        " + _P + "avanzar();",
            "    }",
            "}",
            "",
            "// Forward declarations",
            "struct Nodo* " + _P + "expr();",
            "struct Nodo* " + _P + "logica();",
            "struct ListaNodo* " + _P + "bloque();",
            "struct Nodo* " + _P + "sentencia();",
            "struct Nodo* " + _P + "comp();",
            "struct Nodo* " + _P + "suma();",
            "struct Nodo* " + _P + "term();",
            "struct Nodo* " + _P + "una();",
            "struct Nodo* " + _P + "prim();",
            "void " + _P + "leer_constructores(struct ListaNodo** ccur);",
            "struct Nodo* " + _P + "decl_tipo();",
            "struct Programa " + _P + "programa();",
        ])
        # Now emit the function bodies using a clean string template
        B = """
struct ListaNodo* """ + _P + """bloque() {
    if (!""" + _P + """esperar(T_NL)) { """ + _P + """sinc_skip(); return NULL; }
    while (""" + _P + """mirar()->tipo == T_NL) { """ + _P + """avanzar(); }
    if (!""" + _P + """esperar(T_INDENT)) { """ + _P + """sinc_skip(); return NULL; }
    struct ListaNodo* lst = NULL;
    struct ListaNodo** cur = &lst;
    while (""" + _P + """mirar()->tipo != T_DEDENT && """ + _P + """mirar()->tipo != T_EOF) {
        if (""" + _P + """mirar()->tipo == T_NL) { """ + _P + """avanzar(); continue; }
        struct Nodo* st=""" + _P + """sentencia();
        if (st) { *cur=""" + _P + """mk_list(st,NULL); cur=&(*cur)->cola; }
    }
    """ + _P + """esperar(T_DEDENT);
    return lst;
}
void """ + _P + """leer_constructores(struct ListaNodo** ccur) {
    while (1) {            if (""" + _P + """mirar()->tipo != T_IDENT && """ + _P + """mirar()->tipo != T_RC && """ + _P + """mirar()->tipo != T_MODULO) break;
        char _cn[256]; strncpy(_cn, """ + _P + """mirar()->val, sizeof(_cn)-1); _cn[sizeof(_cn)-1] = '\\0';
        """ + _P + """avanzar();
        struct ConstructorTipo* c = (struct ConstructorTipo*)calloc(1,sizeof(struct ConstructorTipo));
        c->tipo = """ + _P + """cs("ConstructorTipo"); c->nombre = """ + _P + """cs(_cn);
        c->tipos = NULL;
        if (""" + _P + """mirar()->tipo == T_LPAREN) {
            """ + _P + """avanzar();
            struct ListaNodo** tccur = &(c->tipos);
            while (""" + _P + """mirar()->tipo != T_RPAREN && """ + _P + """mirar()->tipo != T_EOF && """ + _P + """mirar()->tipo != T_NL) {
                char _tpb[256]; _tpb[0] = '\\0';
                if (""" + _P + """mirar()->tipo == T_AMPERSAND) {
                    """ + _P + """avanzar();
                    strncat(_tpb, "&", sizeof(_tpb)-1-(int)strlen(_tpb));
                    if (""" + _P + """mirar()->tipo == T_IDENT && strcmp(""" + _P + """mirar()->val, "mut") == 0) {
                        strncat(_tpb, "mut ", sizeof(_tpb)-1-(int)strlen(_tpb));
                        """ + _P + """avanzar();
                    }
                }
                if (""" + _P + """mirar()->tipo != T_IDENT && """ + _P + """mirar()->tipo != T_RC && """ + _P + """mirar()->tipo != T_MODULO) break;
                strncat(_tpb, """ + _P + """mirar()->val, sizeof(_tpb)-1-(int)strlen(_tpb));
                """ + _P + """avanzar();
                while (""" + _P + """mirar()->tipo == T_MUL) { strncat(_tpb, "*", sizeof(_tpb)-1-(int)strlen(_tpb)); """ + _P + """avanzar(); }
                struct Identificador* tip = (struct Identificador*)calloc(1,sizeof(struct Identificador));
                tip->tipo = """ + _P + """cs("Identificador"); tip->nombre = """ + _P + """cs(_tpb);
                *tccur = """ + _P + """mk_list((struct Nodo*)tip, NULL); tccur = &(*tccur)->cola;
                if (""" + _P + """mirar()->tipo == T_COMMA) { """ + _P + """avanzar(); }
                else break;
            }
            """ + _P + """esperar(T_RPAREN);
        }
        *ccur = """ + _P + """mk_list((struct Nodo*)c, NULL); ccur = &(*ccur)->cola;
        if (""" + _P + """mirar()->tipo == T_PIPE) { """ + _P + """avanzar(); continue; }
        break;
    }
}
struct Nodo* """ + _P + """decl_tipo() {
    """ + _P + """avanzar(); /* consume 'tipo' */
    if (""" + _P + """mirar()->tipo != T_IDENT && """ + _P + """mirar()->tipo != T_RC && """ + _P + """mirar()->tipo != T_MODULO) { """ + _P + """sinc_skip(); return NULL; }
    char _tdn[256]; strncpy(_tdn, """ + _P + """mirar()->val, sizeof(_tdn)-1); _tdn[sizeof(_tdn)-1] = '\\0';
    """ + _P + """avanzar();
    struct ListaNodo* tparams = NULL;
    struct ListaNodo** tpcur = &tparams;
    if (""" + _P + """mirar()->tipo == T_LT) {
        """ + _P + """avanzar();
        while (""" + _P + """mirar()->tipo != T_GT && """ + _P + """mirar()->tipo != T_EOF && """ + _P + """mirar()->tipo != T_NL) {
            if (""" + _P + """mirar()->tipo != T_IDENT && """ + _P + """mirar()->tipo != T_RC && """ + _P + """mirar()->tipo != T_MODULO) break;
            struct Identificador* tp = (struct Identificador*)calloc(1,sizeof(struct Identificador));
            tp->tipo = """ + _P + """cs("Identificador"); tp->nombre = """ + _P + """cs(""" + _P + """mirar()->val);
            *tpcur = """ + _P + """mk_list((struct Nodo*)tp, NULL); tpcur = &(*tpcur)->cola;
            """ + _P + """avanzar();
            if (""" + _P + """mirar()->tipo == T_COMMA) { """ + _P + """avanzar(); }
            else break;
        }
        """ + _P + """esperar(T_GT);
    }
    """ + _P + """esperar(T_ASSIGN);
    char _tbase[1024]; _tbase[0] = '\\0';
    struct ListaNodo* ctors = NULL;
    struct ListaNodo** ccur = &ctors;
    if (""" + _P + """mirar()->tipo == T_LPAREN) {
        """ + _P + """avanzar();
        """ + _P + """leer_constructores(ccur);
        """ + _P + """esperar(T_RPAREN);
    } else if (""" + _P + """mirar()->tipo == T_PIPE) {
        """ + _P + """leer_constructores(ccur);
    } else if (""" + _P + """mirar()->tipo == T_IDENT || """ + _P + """mirar()->tipo == T_RC || """ + _P + """mirar()->tipo == T_MODULO) {
        int _sig = (""" + _P + """tpos + 1 < """ + _P + """ntks) ? """ + _P + """tks[""" + _P + """tpos + 1].tipo : T_EOF;
        if (_sig == T_PIPE || _sig == T_LPAREN) {
            """ + _P + """leer_constructores(ccur);
        } else {
            if (""" + _P + """mirar()->tipo == T_AMPERSAND) {
                """ + _P + """avanzar();
                strncat(_tbase, "&", sizeof(_tbase)-1-(int)strlen(_tbase));
                if (""" + _P + """mirar()->tipo == T_IDENT && strcmp(""" + _P + """mirar()->val, "mut") == 0) {
                    strncat(_tbase, "mut ", sizeof(_tbase)-1-(int)strlen(_tbase));
                    """ + _P + """avanzar();
                }
            }
            if (""" + _P + """mirar()->tipo != T_IDENT && """ + _P + """mirar()->tipo != T_RC && """ + _P + """mirar()->tipo != T_MODULO) { """ + _P + """sinc_skip(); return NULL; }
            strncat(_tbase, """ + _P + """mirar()->val, sizeof(_tbase)-1-(int)strlen(_tbase));
            """ + _P + """avanzar();
            while (""" + _P + """mirar()->tipo == T_MUL) { strncat(_tbase, "*", sizeof(_tbase)-1-(int)strlen(_tbase)); """ + _P + """avanzar(); }
            if (""" + _P + """mirar()->tipo == T_LT) {
                """ + _P + """avanzar();
                strncat(_tbase, "<", sizeof(_tbase)-1-(int)strlen(_tbase));
                if (""" + _P + """mirar()->tipo == T_IDENT || """ + _P + """mirar()->tipo == T_RC || """ + _P + """mirar()->tipo == T_MODULO) { strncat(_tbase, """ + _P + """mirar()->val, sizeof(_tbase)-1-(int)strlen(_tbase)); """ + _P + """avanzar(); }
                """ + _P + """esperar(T_GT);
                strncat(_tbase, ">", sizeof(_tbase)-1-(int)strlen(_tbase));
            }
        }
    }
    struct DeclaracionTipo* n = (struct DeclaracionTipo*)calloc(1,sizeof(struct DeclaracionTipo));
    n->tipo = """ + _P + """cs("DeclaracionTipo"); n->nombre = """ + _P + """cs(_tdn);
    n->parametros_tipo = tparams; n->tipo_base = """ + _P + """cs(_tbase); n->constructores = ctors;
    return (struct Nodo*)n;
}
struct Nodo* """ + _P + """sentencia() {
#ifdef SYN_DEBUG_PARSE
    fprintf(stderr, "PARSE S tok=%d pos=%d/%d\\n", """ + _P + """mirar()->tipo, """ + _P + """tpos, """ + _P + """ntks);
    fflush(stderr);
#endif
    while (""" + _P + """mirar()->tipo == T_NL) { """ + _P + """avanzar(); }
_P_retry:;
    """ + _P + """Token* t = """ + _P + """mirar();
    if (t->tipo == T_FUNC) {
        """ + _P + """avanzar();
        if (""" + _P + """mirar()->tipo != T_IDENT && """ + _P + """mirar()->tipo != T_RC && """ + _P + """mirar()->tipo != T_MODULO) { """ + _P + """sinc_skip(); return NULL; }
        char _nm[256]; strncpy(_nm, """ + _P + """mirar()->val, sizeof(_nm)-1); _nm[sizeof(_nm)-1] = '\\0';
        """ + _P + """avanzar();
        """ + _P + """esperar(T_LPAREN);
        struct ListaNodo* params = NULL;
        struct ListaNodo** pcur = &params;
        if (""" + _P + """mirar()->tipo != T_RPAREN) {
            while (1) {
                int is_transfer = 0;
                if (""" + _P + """mirar()->tipo == T_ARROW) { is_transfer=1; """ + _P + """avanzar(); }
                if (""" + _P + """mirar()->tipo != T_IDENT && """ + _P + """mirar()->tipo != T_RC && """ + _P + """mirar()->tipo != T_MODULO) break;
                char _pn[256]; strncpy(_pn, """ + _P + """mirar()->val, sizeof(_pn)-1); _pn[sizeof(_pn)-1] = '\\0';
                """ + _P + """avanzar();
                """ + _P + """esperar(T_COLON);
                if (""" + _P + """mirar()->tipo != T_IDENT && """ + _P + """mirar()->tipo != T_ARC && """ + _P + """mirar()->tipo != T_DEBIL && """ + _P + """mirar()->tipo != T_RC && """ + _P + """mirar()->tipo != T_MODULO) break;
                char _pt[256]; strncpy(_pt, """ + _P + """mirar()->val, sizeof(_pt)-1); _pt[sizeof(_pt)-1] = '\\0';
                """ + _P + """avanzar();
                if (""" + _P + """mirar()->tipo == T_LT) { int _gtl=(int)strlen(_pt); if(_gtl<255){ _pt[_gtl]='<'; _pt[_gtl+1]='\\0'; } """ + _P + """avanzar();
                    while (""" + _P + """mirar()->tipo != T_GT && """ + _P + """mirar()->tipo != T_EOF && """ + _P + """mirar()->tipo != T_NL && """ + _P + """mirar()->tipo != T_RPAREN && """ + _P + """mirar()->tipo != T_COMMA) {
                        int _gl=(int)strlen(_pt);
                        if(_gl<255){ if(""" + _P + """mirar()->tipo==T_IDENT||""" + _P + """mirar()->tipo==T_ARC||""" + _P + """mirar()->tipo==T_DEBIL||""" + _P + """mirar()->tipo==T_RC||""" + _P + """mirar()->tipo==T_MODULO){ int _k=0; while(""" + _P + """mirar()->val[_k]&&_gl<255){ _pt[_gl++]=""" + _P + """mirar()->val[_k++]; } _pt[_gl]='\\0'; } else if(""" + _P + """mirar()->tipo==T_LT){ _pt[_gl]='<'; _pt[_gl+1]='\\0'; } }
                        """ + _P + """avanzar();
                    }
                    if (""" + _P + """mirar()->tipo == T_GT) { int _gl=(int)strlen(_pt); if(_gl<255){ _pt[_gl]='>'; _pt[_gl+1]='\\0'; } """ + _P + """avanzar(); }
                }
                while (""" + _P + """mirar()->tipo == T_MUL) { { int _pl = (int)strlen(_pt); if (_pl < 255) { _pt[_pl] = '*'; _pt[_pl+1] = '\\0'; } } """ + _P + """avanzar(); }
                struct Parametro* pp = (struct Parametro*)calloc(1,sizeof(struct Parametro));
                pp->tipo=""" + _P + """cs("Parametro");
                pp->nombre=""" + _P + """cs(_pn); pp->tipo_param=""" + _P + """cs(_pt);
                pp->es_transferencia = is_transfer;
                *pcur=""" + _P + """mk_list((struct Nodo*)pp,NULL); pcur=&(*pcur)->cola;
                if (""" + _P + """mirar()->tipo != T_COMMA) break;
                """ + _P + """avanzar();
            }
        }
        """ + _P + """esperar(T_RPAREN); """ + _P + """esperar(T_ARROW);
        if (""" + _P + """mirar()->tipo != T_IDENT && """ + _P + """mirar()->tipo != T_ARC && """ + _P + """mirar()->tipo != T_DEBIL && """ + _P + """mirar()->tipo != T_RC && """ + _P + """mirar()->tipo != T_MODULO) { """ + _P + """sinc_skip(); return NULL; }
        char _rt[256]; strcpy(_rt, """ + _P + """mirar()->val);
        """ + _P + """avanzar();
        if (""" + _P + """mirar()->tipo == T_LT) { int _gtl=(int)strlen(_rt); if(_gtl<255){ _rt[_gtl]='<'; _rt[_gtl+1]='\\0'; } """ + _P + """avanzar();
            while (""" + _P + """mirar()->tipo != T_GT && """ + _P + """mirar()->tipo != T_EOF && """ + _P + """mirar()->tipo != T_NL && """ + _P + """mirar()->tipo != T_COLON) {
                int _gl=(int)strlen(_rt);
                if(_gl<255){ if(""" + _P + """mirar()->tipo==T_IDENT||""" + _P + """mirar()->tipo==T_ARC||""" + _P + """mirar()->tipo==T_DEBIL||""" + _P + """mirar()->tipo==T_RC||""" + _P + """mirar()->tipo==T_MODULO){ int _k=0; while(""" + _P + """mirar()->val[_k]&&_gl<255){ _rt[_gl++]=""" + _P + """mirar()->val[_k++]; } _rt[_gl]='\\0'; } else if(""" + _P + """mirar()->tipo==T_LT){ _rt[_gl]='<'; _rt[_gl+1]='\\0'; } }
                """ + _P + """avanzar();
            }
            if (""" + _P + """mirar()->tipo == T_GT) { int _gl=(int)strlen(_rt); if(_gl<255){ _rt[_gl]='>'; _rt[_gl+1]='\\0'; } """ + _P + """avanzar(); }
        }
        """ + _P + """esperar(T_COLON);
        struct ListaNodo* body=""" + _P + """bloque();
        struct DefinicionFuncion* n = (struct DefinicionFuncion*)calloc(1,sizeof(struct DefinicionFuncion));
        n->tipo=""" + _P + """cs("DefinicionFuncion");
        n->nombre=""" + _P + """cs(_nm); n->parametros=(struct ListaParametro*)params;
        n->tipo_retorno=""" + _P + """cs(_rt); n->cuerpo=body;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_STRUCT) {
        """ + _P + """avanzar();
        if (""" + _P + """mirar()->tipo != T_IDENT && """ + _P + """mirar()->tipo != T_RC && """ + _P + """mirar()->tipo != T_MODULO) { """ + _P + """sinc_skip(); return NULL; }
        char _snm[256]; strcpy(_snm, """ + _P + """mirar()->val);
        """ + _P + """avanzar();
        """ + _P + """esperar(T_COLON);
        if (!""" + _P + """esperar(T_NL)) { """ + _P + """sinc_skip(); return NULL; }
        while (""" + _P + """mirar()->tipo == T_NL) { """ + _P + """avanzar(); }
        if (!""" + _P + """esperar(T_INDENT)) { """ + _P + """sinc_skip(); return NULL; }
        struct ListaParametro* campos = NULL;
        struct ListaParametro** ccur = &campos;
        while (""" + _P + """mirar()->tipo != T_DEDENT && """ + _P + """mirar()->tipo != T_EOF) {
            if (""" + _P + """mirar()->tipo == T_NL) { """ + _P + """avanzar(); continue; }
            if (""" + _P + """mirar()->tipo == T_DEDENT || """ + _P + """mirar()->tipo == T_EOF || """ + _P + """mirar()->tipo == T_COLON) break;
            char _pn[256]; strncpy(_pn, """ + _P + """mirar()->val, sizeof(_pn)-1); _pn[sizeof(_pn)-1] = '\\0';
            """ + _P + """avanzar();
            """ + _P + """esperar(T_COLON);
            if (""" + _P + """mirar()->tipo != T_IDENT && """ + _P + """mirar()->tipo != T_ARC && """ + _P + """mirar()->tipo != T_DEBIL && """ + _P + """mirar()->tipo != T_RC && """ + _P + """mirar()->tipo != T_MODULO) { """ + _P + """sinc_skip(); break; }
            char _pt[256]; strncpy(_pt, """ + _P + """mirar()->val, sizeof(_pt)-1); _pt[sizeof(_pt)-1] = '\\0';
            """ + _P + """avanzar();
            if (""" + _P + """mirar()->tipo == T_LT) { int _gtl=(int)strlen(_pt); if(_gtl<255){ _pt[_gtl]='<'; _pt[_gtl+1]='\\0'; } """ + _P + """avanzar();
                while (""" + _P + """mirar()->tipo != T_GT && """ + _P + """mirar()->tipo != T_EOF && """ + _P + """mirar()->tipo != T_NL && """ + _P + """mirar()->tipo != T_DEDENT) {
                    int _gl=(int)strlen(_pt);
                    if(_gl<255){ if(""" + _P + """mirar()->tipo==T_IDENT||""" + _P + """mirar()->tipo==T_ARC||""" + _P + """mirar()->tipo==T_DEBIL||""" + _P + """mirar()->tipo==T_RC||""" + _P + """mirar()->tipo==T_MODULO){ int _k=0; while(""" + _P + """mirar()->val[_k]&&_gl<255){ _pt[_gl++]=""" + _P + """mirar()->val[_k++]; } _pt[_gl]='\\0'; } else if(""" + _P + """mirar()->tipo==T_LT){ _pt[_gl]='<'; _pt[_gl+1]='\\0'; } }
                    """ + _P + """avanzar();
                }
                if (""" + _P + """mirar()->tipo == T_GT) { int _gl=(int)strlen(_pt); if(_gl<255){ _pt[_gl]='>'; _pt[_gl+1]='\\0'; } """ + _P + """avanzar(); }
            }
            struct Parametro* pp=(struct Parametro*)calloc(1,sizeof(struct Parametro));
            pp->tipo=""" + _P + """cs("Parametro"); pp->nombre=""" + _P + """cs(_pn); pp->tipo_param=""" + _P + """cs(_pt); pp->es_transferencia=0;
            *ccur=(struct ListaParametro*)""" + _P + """mk_list((struct Nodo*)pp,NULL); ccur=&(*ccur)->cola;
        }
        """ + _P + """esperar(T_DEDENT);
        struct DefinicionEstructura* n = (struct DefinicionEstructura*)calloc(1,sizeof(struct DefinicionEstructura));
        n->tipo=""" + _P + """cs("DefinicionEstructura"); n->nombre=""" + _P + """cs(_snm); n->campos=campos;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_IF) {
        """ + _P + """avanzar();
        struct Nodo* cond=""" + _P + """expr();
        """ + _P + """esperar(T_COLON);
        struct ListaNodo* cpo=NULL;
        if (""" + _P + """mirar()->tipo == T_NL) {
            cpo=""" + _P + """bloque();
        } else {
            struct Nodo* _st=""" + _P + """sentencia();
            if (_st) { cpo=""" + _P + """mk_list(_st,NULL); }
        }
        struct ListaNodo* sino = NULL;
        if (""" + _P + """mirar()->tipo == T_ELSE) { """ + _P + """avanzar(); """ + _P + """esperar(T_COLON);
            if (""" + _P + """mirar()->tipo == T_NL) {
                sino=""" + _P + """bloque();
            } else {
                struct Nodo* _st=""" + _P + """sentencia();
                if (_st) { sino=""" + _P + """mk_list(_st,NULL); }
            }
        }
        struct SentenciaSi* n = (struct SentenciaSi*)calloc(1,sizeof(struct SentenciaSi));
        n->tipo=""" + _P + """cs("SentenciaSi"); n->condicion=cond;
        n->cuerpo=cpo; n->cuerpo_sino=sino;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_WHILE) {
        """ + _P + """avanzar();
        struct Nodo* cond=""" + _P + """expr();
        """ + _P + """esperar(T_COLON);
        struct ListaNodo* cpo=NULL;
        if (""" + _P + """mirar()->tipo == T_NL) {
            cpo=""" + _P + """bloque();
        } else {
            struct Nodo* _st=""" + _P + """sentencia();
            if (_st) { cpo=""" + _P + """mk_list(_st,NULL); }
        }
        struct SentenciaMientras* n = (struct SentenciaMientras*)calloc(1,sizeof(struct SentenciaMientras));
        n->tipo=""" + _P + """cs("SentenciaMientras"); n->condicion=cond; n->cuerpo=cpo;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_RET) {
        """ + _P + """avanzar();
        struct Nodo* expr = NULL;
        if (""" + _P + """mirar()->tipo == T_ARROW) { """ + _P + """avanzar(); expr=""" + _P + """expr(); }
        else if (""" + _P + """mirar()->tipo != T_NL && """ + _P + """mirar()->tipo != T_DEDENT && """ + _P + """mirar()->tipo != T_EOF) { expr=""" + _P + """expr(); }
        struct SentenciaRetornar* n = (struct SentenciaRetornar*)calloc(1,sizeof(struct SentenciaRetornar));
        n->tipo=""" + _P + """cs("SentenciaRetornar"); n->expr=expr;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_SPAWN) { """ + _P + """avanzar();
        struct Nodo* ll=""" + _P + """expr();
        struct SentenciaLanzar* n = (struct SentenciaLanzar*)calloc(1,sizeof(struct SentenciaLanzar));
        n->tipo=""" + _P + """cs("SentenciaLanzar"); n->llamada=ll;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_RECOVER) { """ + _P + """avanzar();
        struct Nodo* ac=""" + _P + """expr(); """ + _P + """esperar(T_COLON);
        struct Nodo* pb=""" + _P + """expr();
        struct SentenciaRecuperar* n = (struct SentenciaRecuperar*)calloc(1,sizeof(struct SentenciaRecuperar));
        n->tipo=""" + _P + """cs("SentenciaRecuperar"); n->accion_critica=ac; n->plan_b=pb;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_LISTEN) { """ + _P + """avanzar();
        struct Nodo* cn=""" + _P + """expr(); """ + _P + """esperar(T_COLON);
        struct ListaNodo* cpo=NULL;
        if (""" + _P + """mirar()->tipo == T_NL) {
            cpo=""" + _P + """bloque();
        } else {
            struct Nodo* _st=""" + _P + """sentencia();
            if (_st) { cpo=""" + _P + """mk_list(_st,NULL); }
        }
        struct SentenciaEscuchar* n = (struct SentenciaEscuchar*)calloc(1,sizeof(struct SentenciaEscuchar));
        n->tipo=""" + _P + """cs("SentenciaEscuchar"); n->canal=cn; n->cuerpo=cpo;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_BREAK) { """ + _P + """avanzar();
        struct SentenciaRomper* n = (struct SentenciaRomper*)calloc(1,sizeof(struct SentenciaRomper));
        n->tipo=""" + _P + """cs("SentenciaRomper");
        return (struct Nodo*)n;
    }
    if (t->tipo == T_CONTINUE) { """ + _P + """avanzar();
        struct SentenciaSiguiente* n = (struct SentenciaSiguiente*)calloc(1,sizeof(struct SentenciaSiguiente));
        n->tipo=""" + _P + """cs("SentenciaSiguiente");
        return (struct Nodo*)n;
    }
    if (t->tipo == T_IMPORT) { """ + _P + """avanzar();
        if (""" + _P + """mirar()->tipo != T_IDENT && """ + _P + """mirar()->tipo != T_RC && """ + _P + """mirar()->tipo != T_MODULO) { """ + _P + """sinc_skip(); return NULL; }
        char _imp[256]; strncpy(_imp, """ + _P + """mirar()->val, sizeof(_imp)-1); _imp[sizeof(_imp)-1] = '\\0'; int _iml = (int)strlen(_imp);
        """ + _P + """avanzar();
        while (""" + _P + """mirar()->tipo == T_DOT) { """ + _P + """avanzar(); if (""" + _P + """mirar()->tipo != T_IDENT && """ + _P + """mirar()->tipo != T_RC && """ + _P + """mirar()->tipo != T_MODULO) break; { int _il = (int)strlen(_imp); if (_il < 254) { _imp[_il] = '.'; _imp[_il+1] = '\\0'; } if ((int)strlen(_imp) + (int)strlen(""" + _P + """mirar()->val) < 255) { strncat(_imp, """ + _P + """mirar()->val, 255 - (int)strlen(_imp) - 1); } } """ + _P + """avanzar(); }
        struct SentenciaImportar* n = (struct SentenciaImportar*)calloc(1,sizeof(struct SentenciaImportar));
        n->tipo=""" + _P + """cs("SentenciaImportar"); n->ruta=""" + _P + """cs(_imp);
        return (struct Nodo*)n;
    }
    if (t->tipo == T_IMPORTAR_C) { """ + _P + """avanzar();
        if (""" + _P + """mirar()->tipo != T_STR) { """ + _P + """sinc_skip(); return NULL; }
        char _hc[256]; strcpy(_hc, """ + _P + """mirar()->val);
        int _hsys = (_hc[0]=='<' && _hc[strlen(_hc)-1]=='>');
        if(_hsys){{ memmove(_hc,_hc+1,strlen(_hc)-2); _hc[strlen(_hc)-2]=0; }}
        """ + _P + """avanzar();
        struct ImportarC* n = (struct ImportarC*)calloc(1,sizeof(struct ImportarC));
        n->tipo=""" + _P + """cs("ImportarC"); n->ruta=""" + _P + """cs(_hc); n->es_sistema=_hsys;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_EXTERNO) { """ + _P + """avanzar();
        if (""" + _P + """mirar()->tipo != T_FUNC) { """ + _P + """sinc_skip(); return NULL; }
        """ + _P + """avanzar();
        if (""" + _P + """mirar()->tipo != T_IDENT && """ + _P + """mirar()->tipo != T_RC && """ + _P + """mirar()->tipo != T_MODULO) { """ + _P + """sinc_skip(); return NULL; }
        char _enm[256]; strcpy(_enm, """ + _P + """mirar()->val);
        """ + _P + """avanzar();
        """ + _P + """esperar(T_LPAREN);
        struct ListaParametro* eparams = NULL;
        struct ListaParametro** epcur = &eparams;
        if (""" + _P + """mirar()->tipo != T_RPAREN) {
            while (1) {
                if (""" + _P + """mirar()->tipo != T_IDENT && """ + _P + """mirar()->tipo != T_RC && """ + _P + """mirar()->tipo != T_MODULO) break;
                char _epn[256]; strcpy(_epn, """ + _P + """mirar()->val);
                """ + _P + """avanzar();
                """ + _P + """esperar(T_COLON);
                if (""" + _P + """mirar()->tipo != T_IDENT && """ + _P + """mirar()->tipo != T_RC && """ + _P + """mirar()->tipo != T_MODULO) break;
                char _ept[256]; strcpy(_ept, """ + _P + """mirar()->val);
                """ + _P + """avanzar();
                while (""" + _P + """mirar()->tipo == T_MUL) { strcat(_ept,"*"); """ + _P + """avanzar(); }
                struct Parametro* epp=(struct Parametro*)calloc(1,sizeof(struct Parametro));
                epp->tipo=""" + _P + """cs("Parametro"); epp->nombre=""" + _P + """cs(_epn); epp->tipo_param=""" + _P + """cs(_ept); epp->es_transferencia=0;
                *epcur=(struct ListaParametro*)""" + _P + """mk_list((struct Nodo*)epp,NULL); epcur=&(*epcur)->cola;
                if (""" + _P + """mirar()->tipo != T_COMMA) break;
                """ + _P + """avanzar();
            }
        }
        """ + _P + """esperar(T_RPAREN); """ + _P + """esperar(T_ARROW);
        if (""" + _P + """mirar()->tipo != T_IDENT && """ + _P + """mirar()->tipo != T_RC && """ + _P + """mirar()->tipo != T_MODULO) { """ + _P + """sinc_skip(); return NULL; }
        char _ert[256]; strcpy(_ert, """ + _P + """mirar()->val);
        """ + _P + """avanzar();
        struct DeclaracionExterna* n = (struct DeclaracionExterna*)calloc(1,sizeof(struct DeclaracionExterna));
        n->tipo=""" + _P + """cs("DeclaracionExterna"); n->nombre=""" + _P + """cs(_enm);
        n->parametros=eparams; n->tipo_retorno=""" + _P + """cs(_ert);
        return (struct Nodo*)n;
    }
    if (t->tipo == T_INSEGURO) { """ + _P + """avanzar();
        """ + _P + """esperar(T_COLON);
        struct ListaNodo* cpo=NULL;
        if (""" + _P + """mirar()->tipo == T_NL) {
            cpo=""" + _P + """bloque();
        } else {
            struct Nodo* _st=""" + _P + """sentencia();
            if (_st) { cpo=""" + _P + """mk_list(_st,NULL); }
        }
        struct BloqueInseguro* n = (struct BloqueInseguro*)calloc(1,sizeof(struct BloqueInseguro));
        n->tipo=""" + _P + """cs("BloqueInseguro"); n->cuerpo=cpo;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_LET) {  // F1.2c: let IDENT [':' tipo] ['=' expresion] (Manual 2 §2 L134)
        """ + _P + """avanzar();
        if (""" + _P + """mirar()->tipo != T_IDENT && """ + _P + """mirar()->tipo != T_RC && """ + _P + """mirar()->tipo != T_MODULO) { """ + _P + """sinc_skip(); return NULL; }
        char _lvn[256]; strcpy(_lvn, """ + _P + """mirar()->val);
        """ + _P + """avanzar();
        char _ltp[256]; _ltp[0] = 0;
        if (""" + _P + """mirar()->tipo == T_COLON) {
            """ + _P + """avanzar();
            if (""" + _P + """mirar()->tipo != T_IDENT && """ + _P + """mirar()->tipo != T_ARC && """ + _P + """mirar()->tipo != T_DEBIL && """ + _P + """mirar()->tipo != T_RC && """ + _P + """mirar()->tipo != T_MODULO) { """ + _P + """sinc_skip(); return NULL; }
            strcpy(_ltp, """ + _P + """mirar()->val);
            """ + _P + """avanzar();
            if (""" + _P + """mirar()->tipo == T_LT) { int _gtl=(int)strlen(_ltp); if(_gtl<255){ _ltp[_gtl]='<'; _ltp[_gtl+1]='\\0'; } """ + _P + """avanzar();
                while (""" + _P + """mirar()->tipo != T_GT && """ + _P + """mirar()->tipo != T_EOF && """ + _P + """mirar()->tipo != T_NL) {
                    int _gl=(int)strlen(_ltp);
                    if(_gl<255){ if(""" + _P + """mirar()->tipo==T_IDENT||""" + _P + """mirar()->tipo==T_ARC||""" + _P + """mirar()->tipo==T_DEBIL||""" + _P + """mirar()->tipo==T_RC||""" + _P + """mirar()->tipo==T_MODULO){ int _k=0; while(""" + _P + """mirar()->val[_k]&&_gl<255){ _ltp[_gl++]=""" + _P + """mirar()->val[_k++]; } _ltp[_gl]='\\0'; } else if(""" + _P + """mirar()->tipo==T_LT){ _ltp[_gl]='<'; _ltp[_gl+1]='\\0'; } }
                    """ + _P + """avanzar();
                }
                if (""" + _P + """mirar()->tipo == T_GT) { int _gl=(int)strlen(_ltp); if(_gl<255){ _ltp[_gl]='>'; _ltp[_gl+1]='\\0'; } """ + _P + """avanzar(); }
            }
            while (""" + _P + """mirar()->tipo == T_MUL) { strcat(_ltp,"*"); """ + _P + """avanzar(); }
        }
        struct Nodo* _lexpr = NULL;
        if (""" + _P + """mirar()->tipo == T_ASSIGN) {
            """ + _P + """avanzar();
            _lexpr = """ + _P + """expr();
        }
        struct DeclaracionVariable* _ldv = (struct DeclaracionVariable*)calloc(1,sizeof(struct DeclaracionVariable));
        _ldv->tipo=""" + _P + """cs("DeclaracionVariable");
        _ldv->nombre=""" + _P + """cs(_lvn); _ldv->tipo_param=""" + _P + """cs(_ltp); _ldv->expresion=_lexpr;
        return (struct Nodo*)_ldv;
    }
    if (t->tipo == T_DELEGAR) {  // F1.2c: delegar expresion -> retornar err(...) (Manual 2 §2 L132)
        """ + _P + """avanzar();
        struct Nodo* _dexpr = """ + _P + """expr();
        struct SentenciaDelegar* _ndl = (struct SentenciaDelegar*)calloc(1,sizeof(struct SentenciaDelegar));
        _ndl->tipo=""" + _P + """cs("SentenciaDelegar"); _ndl->expresion=_dexpr;
        return (struct Nodo*)_ndl;
    }
    if (t->tipo == T_EXPORT) {  // F1.2d: @export ( IDENT ) funcion (Manual 2 §2 L81)
        """ + _P + """avanzar();
        """ + _P + """esperar(T_LPAREN);
        if (""" + _P + """mirar()->tipo != T_IDENT && """ + _P + """mirar()->tipo != T_RC && """ + _P + """mirar()->tipo != T_MODULO) { """ + _P + """sinc_skip(); return NULL; }
        char _xdn[256]; strncpy(_xdn, """ + _P + """mirar()->val, sizeof(_xdn)-1); _xdn[sizeof(_xdn)-1] = '\\0';
        """ + _P + """avanzar();
        """ + _P + """esperar(T_RPAREN);
        struct Nodo* _xfn = """ + _P + """sentencia();
        struct DeclaracionExport* _xne = (struct DeclaracionExport*)calloc(1,sizeof(struct DeclaracionExport));
        _xne->tipo=""" + _P + """cs("DeclaracionExport"); _xne->destino=""" + _P + """cs(_xdn); _xne->funcion=_xfn;
        return (struct Nodo*)_xne;
    }
    // F1.4: la variable rc (y modulo) son keywords CONTEXTUALES — asignacion
    // rc = ... valida (paridad S1, Manual 2 S3 L249/L255).
    if ((t->tipo == T_IDENT || t->tipo == T_RC || t->tipo == T_MODULO) && """ + _P + """tpos + 1 < """ + _P + """ntks && """ + _P + """tks[""" + _P + """tpos + 1].tipo == T_ASSIGN) {
        char _vn[256]; strcpy(_vn, t->val);
        """ + _P + """avanzar(); """ + _P + """avanzar();
        struct Nodo* val=""" + _P + """expr();
        struct AsignacionVariable* n = (struct AsignacionVariable*)calloc(1,sizeof(struct AsignacionVariable));
        n->tipo=""" + _P + """cs("AsignacionVariable");
        n->nombre=""" + _P + """cs(_vn); n->expresion=val;
        return (struct Nodo*)n;
    }
    // D-F1: declaracion_tipo (Manual 2 §2). El guard replica el del parser Python:
    // 'tipo' + IDENTIFICADOR + ('=' | '<' | '|' | '(')
    if (t->tipo == T_IDENT && strcmp(t->val, "tipo") == 0 && """ + _P + """tpos + 2 < """ + _P + """ntks && (""" + _P + """tks[""" + _P + """tpos + 1].tipo == T_IDENT || """ + _P + """tks[""" + _P + """tpos + 1].tipo == T_RC || """ + _P + """tks[""" + _P + """tpos + 1].tipo == T_MODULO) && (""" + _P + """tks[""" + _P + """tpos + 2].tipo == T_ASSIGN || """ + _P + """tks[""" + _P + """tpos + 2].tipo == T_LT || """ + _P + """tks[""" + _P + """tpos + 2].tipo == T_PIPE || """ + _P + """tks[""" + _P + """tpos + 2].tipo == T_LPAREN)) {
        return """ + _P + """decl_tipo();
    }
    // Guard: skip stray INDENT/DEDENT/NL and retry keyword matching
    if (""" + _P + """mirar()->tipo == T_INDENT || """ + _P + """mirar()->tipo == T_DEDENT || """ + _P + """mirar()->tipo == T_NL) {
        """ + _P + """avanzar();
        goto _P_retry;
    }
    if (""" + _P + """mirar()->tipo == T_EOF) { return NULL; }
    { struct Nodo* e=""" + _P + """expr();
        if (e && """ + _P + """mirar()->tipo == T_ASSIGN) {
            """ + _P + """avanzar();
            struct Nodo* val=""" + _P + """expr();
            if (strcmp(e->tipo.datos,"Identificador")==0) {
                struct AsignacionVariable* n = (struct AsignacionVariable*)calloc(1,sizeof(struct AsignacionVariable));
                n->tipo=""" + _P + """cs("AsignacionVariable");
                n->nombre=((struct Identificador*)e)->nombre; n->expresion=val;
                return (struct Nodo*)n;
            }
            if (strcmp(e->tipo.datos,"ExprAccesoCampo")==0) {
                struct AsignacionCampo* n = (struct AsignacionCampo*)calloc(1,sizeof(struct AsignacionCampo));
                n->tipo=""" + _P + """cs("AsignacionCampo");
                n->objeto=((struct ExprAccesoCampo*)e)->objeto; n->nombre_campo=((struct ExprAccesoCampo*)e)->nombre_campo; n->expresion=val;
                return (struct Nodo*)n;
            }
        }
        struct SentenciaExpr* n = (struct SentenciaExpr*)calloc(1,sizeof(struct SentenciaExpr));
        n->tipo=""" + _P + """cs("SentenciaExpr"); n->expr=e;
        return (struct Nodo*)n;
    }
}
struct Nodo* """ + _P + """expr() { return """ + _P + """logica(); }

struct Nodo* """ + _P + """logica() {
    struct Nodo* izq=""" + _P + """comp();
    while (1) {
        int tt=""" + _P + """mirar()->tipo;
        if (tt!=T_AND&&tt!=T_OR) break;
        """ + _P + """avanzar();
        struct Nodo* der=""" + _P + """comp();
        struct OpBinaria* n=(struct OpBinaria*)calloc(1,sizeof(struct OpBinaria));
        n->tipo=""" + _P + """cs("OpBinaria"); n->izquierdo=izq; n->derecho=der;
        n->operador=(struct Token*)calloc(1,sizeof(struct Token)); n->operador->tipo=tt; n->operador->linea=0; n->operador->columna=0;
        n->operador->lexema=""" + _P + """cs(tt==T_AND?"&&":"||");
        izq=(struct Nodo*)n;
    }
    return izq;
}

struct Nodo* """ + _P + """comp() {
    struct Nodo* izq=""" + _P + """suma();
    while (1) {
        int tt=""" + _P + """mirar()->tipo;
        if (tt!=T_EQ&&tt!=T_NE&&tt!=T_LT&&tt!=T_GT&&tt!=T_LE&&tt!=T_GE) break;
        """ + _P + """avanzar();
        struct Nodo* der=""" + _P + """suma();
        struct OpBinaria* n=(struct OpBinaria*)calloc(1,sizeof(struct OpBinaria));
        n->tipo=""" + _P + """cs("OpBinaria"); n->izquierdo=izq; n->derecho=der;
        n->operador=(struct Token*)calloc(1,sizeof(struct Token)); n->operador->tipo=tt; n->operador->linea=0; n->operador->columna=0;
        {char _b[4]={0,0,0,0};if(tt==T_EQ){_b[0]='=';_b[1]='=';}
        else if(tt==T_NE){_b[0]='!';_b[1]='=';}
        else if(tt==T_LE){_b[0]='<';_b[1]='=';}
        else if(tt==T_GE){_b[0]='>';_b[1]='=';}
        else if(tt==T_LT){_b[0]='<';}else{_b[0]='>';}
        n->operador->lexema=""" + _P + """cs(_b);}
        izq=(struct Nodo*)n;
    }
    return izq;
}
struct Nodo* """ + _P + """suma() {
    struct Nodo* izq=""" + _P + """term();
    while (""" + _P + """mirar()->tipo==T_PLUS||""" + _P + """mirar()->tipo==T_MINUS) {
        int tt=""" + _P + """mirar()->tipo; """ + _P + """avanzar();
        struct Nodo* der=""" + _P + """term();
        struct OpBinaria* n=(struct OpBinaria*)calloc(1,sizeof(struct OpBinaria));
        n->tipo=""" + _P + """cs("OpBinaria"); n->izquierdo=izq; n->derecho=der;
        n->operador=(struct Token*)calloc(1,sizeof(struct Token)); n->operador->tipo=tt; n->operador->linea=0; n->operador->columna=0;
        n->operador->lexema=""" + _P + """cs(tt==T_PLUS?"+":"-");
        izq=(struct Nodo*)n;
    }
    return izq;
}
struct Nodo* """ + _P + """term() {
    struct Nodo* izq=""" + _P + """una();
    while (""" + _P + """mirar()->tipo==T_MUL||""" + _P + """mirar()->tipo==T_DIV||""" + _P + """mirar()->tipo==T_MOD) {
        int tt=""" + _P + """mirar()->tipo; """ + _P + """avanzar();
        struct Nodo* der=""" + _P + """una();
        struct OpBinaria* n=(struct OpBinaria*)calloc(1,sizeof(struct OpBinaria));
        n->tipo=""" + _P + """cs("OpBinaria"); n->izquierdo=izq; n->derecho=der;
        n->operador=(struct Token*)calloc(1,sizeof(struct Token)); n->operador->tipo=tt; n->operador->linea=0; n->operador->columna=0;
        n->operador->lexema=""" + _P + """cs(tt==T_MUL?"*":tt==T_DIV?"/":"%");
        izq=(struct Nodo*)n;
    }
    return izq;
}
struct Nodo* """ + _P + """una() {
    if (""" + _P + """mirar()->tipo==T_MINUS||""" + _P + """mirar()->tipo==T_PLUS) {
        int tt=""" + _P + """mirar()->tipo; """ + _P + """avanzar();
        struct Nodo* e=""" + _P + """una();
        struct OpUnaria* n=(struct OpUnaria*)calloc(1,sizeof(struct OpUnaria));
        n->tipo=""" + _P + """cs("OpUnaria"); n->expr=e;
        n->operador=(struct Token*)calloc(1,sizeof(struct Token)); n->operador->tipo=tt; n->operador->linea=0; n->operador->columna=0;
        n->operador->lexema=""" + _P + """cs(tt==T_PLUS?"+":"-");
        return (struct Nodo*)n;
    }
    if (""" + _P + """mirar()->tipo==T_NOT) {
        int tt=""" + _P + """mirar()->tipo; """ + _P + """avanzar();
        struct Nodo* e=""" + _P + """una();
        struct OpUnaria* n=(struct OpUnaria*)calloc(1,sizeof(struct OpUnaria));
        n->tipo=""" + _P + """cs("OpUnaria"); n->expr=e;
        n->operador=(struct Token*)calloc(1,sizeof(struct Token)); n->operador->tipo=tt; n->operador->linea=0; n->operador->columna=0;
        n->operador->lexema=""" + _P + """cs("!");
        return (struct Nodo*)n;
    }    if ("""+_P+"""mirar()->tipo==T_AMPERSAND) {
        """+_P+"""avanzar();
        int _emut = 0;
        if ("""+_P+"""mirar()->tipo==T_IDENT && strcmp("""+_P+"""mirar()->val,"mut")==0) { _emut = 1; """+_P+"""avanzar(); }
        struct Nodo* e="""+_P+"""una();
        struct ExprObtenerDireccion* n=(struct ExprObtenerDireccion*)calloc(1,sizeof(struct ExprObtenerDireccion));
        n->tipo="""+_P+"""cs("ExprObtenerDireccion"); n->expr=e; n->es_mutable=_emut;
        return (struct Nodo*)n;
    }
    if (""" + _P + """mirar()->tipo==T_MUL) {
        """ + _P + """avanzar();
        struct Nodo* e=""" + _P + """una();
        struct ExprDereferencia* n=(struct ExprDereferencia*)calloc(1,sizeof(struct ExprDereferencia));
        n->tipo=""" + _P + """cs("ExprDereferencia"); n->expr=e;
        return (struct Nodo*)n;
    }
    return """ + _P + """prim();
}
struct Nodo* """ + _P + """prim() {
    """ + _P + """Token* t=""" + _P + """mirar();
    if (t->tipo==T_NUM) {
        if (strchr(t->val, '.') != NULL) {
            struct LiteralDecimal* n=(struct LiteralDecimal*)calloc(1,sizeof(struct LiteralDecimal));
            n->tipo=""" + _P + """cs("LiteralDecimal"); n->valor=atof(t->val);
            """ + _P + """avanzar(); return (struct Nodo*)n;
        }
        struct LiteralNumero* n=(struct LiteralNumero*)calloc(1,sizeof(struct LiteralNumero));
        n->tipo=""" + _P + """cs("LiteralNumero"); n->valor=atoi(t->val);
        """ + _P + """avanzar(); return (struct Nodo*)n;
    }
    if (t->tipo==T_STR) {
        struct LiteralCadena* n=(struct LiteralCadena*)calloc(1,sizeof(struct LiteralCadena));
        n->tipo=""" + _P + """cs("LiteralCadena"); n->valor=""" + _P + """cs(t->val);
        """ + _P + """avanzar(); return (struct Nodo*)n;
    }
    if (t->tipo==T_TRUE) {
        """ + _P + """avanzar();
        struct LiteralNumero* n=(struct LiteralNumero*)calloc(1,sizeof(struct LiteralNumero));
        n->tipo=""" + _P + """cs("LiteralNumero"); n->valor=1;
        return (struct Nodo*)n;
    }
    if (t->tipo==T_FALSE) {
        """ + _P + """avanzar();
        struct LiteralNumero* n=(struct LiteralNumero*)calloc(1,sizeof(struct LiteralNumero));
        n->tipo=""" + _P + """cs("LiteralNumero"); n->valor=0;
        return (struct Nodo*)n;
    }
    // F1.4: rc/modulo son keywords contextuales — tambien expresiones primarias.
    if (t->tipo==T_IDENT || t->tipo==T_RC || t->tipo==T_MODULO) {
        // D-F1: 'nulo' -> LiteralNulo y 'tensor(filas, columnas)' -> ExprTensor (Manual 2 §4.1/§4.3)
        if (strcmp(t->val, "nulo") == 0) {
            """ + _P + """avanzar();
            struct LiteralNulo* _ln=(struct LiteralNulo*)calloc(1,sizeof(struct LiteralNulo));
            _ln->tipo=""" + _P + """cs("LiteralNulo");
            return (struct Nodo*)_ln;
        }
        if (strcmp(t->val, "tensor") == 0 && """ + _P + """tpos + 1 < """ + _P + """ntks && """ + _P + """tks[""" + _P + """tpos + 1].tipo == T_LPAREN) {
            """ + _P + """avanzar(); """ + _P + """avanzar();
            struct Nodo* _fl=""" + _P + """expr();
            """ + _P + """esperar(T_COMMA);
            struct Nodo* _cl=""" + _P + """expr();
            """ + _P + """esperar(T_RPAREN);
            struct ExprTensor* _tn=(struct ExprTensor*)calloc(1,sizeof(struct ExprTensor));
            _tn->tipo=""" + _P + """cs("ExprTensor"); _tn->filas=_fl; _tn->columnas=_cl;
            return (struct Nodo*)_tn;
        }
        char _nm[256]; strncpy(_nm, t->val, sizeof(_nm)-1); _nm[sizeof(_nm)-1] = '\\0';
        """ + _P + """avanzar();
        if (""" + _P + """mirar()->tipo==T_LPAREN) {
            """ + _P + """avanzar();
            struct ListaNodo* args=NULL; struct ListaNodo** acur=&args;
            if (""" + _P + """mirar()->tipo!=T_RPAREN) {
                while (1) {
                    if (""" + _P + """mirar()->tipo==T_ARROW) {
                        """ + _P + """avanzar();
                        struct Nodo* ae=""" + _P + """expr();
                        struct ArgumentoTransferido* at=(struct ArgumentoTransferido*)calloc(1,sizeof(struct ArgumentoTransferido));
                        at->tipo=""" + _P + """cs("ArgumentoTransferido"); at->expr=ae;
                        *acur=""" + _P + """mk_list((struct Nodo*)at,NULL);
                    } else { *acur=""" + _P + """mk_list(""" + _P + """expr(),NULL); }
                    acur=&(*acur)->cola;
                    if (""" + _P + """mirar()->tipo!=T_COMMA) break;
                    """ + _P + """avanzar();
                }
            }
            """ + _P + """esperar(T_RPAREN);
            if(strcmp(_nm,"log")==0) {
                struct LogLlamada* n=(struct LogLlamada*)calloc(1,sizeof(struct LogLlamada));
                n->tipo=""" + _P + """cs("LogLlamada"); n->argumentos=args;
                return (struct Nodo*)n;
            }
            struct LlamadaFuncion* n=(struct LlamadaFuncion*)calloc(1,sizeof(struct LlamadaFuncion));
            n->tipo=""" + _P + """cs("LlamadaFuncion"); n->nombre=""" + _P + """cs(_nm); n->argumentos=args;
            return (struct Nodo*)n;
        }
        if (""" + _P + """mirar()->tipo==T_DOT) {
            /* Build chain: a.b.c -> ExprAccesoCampo(ExprAccesoCampo(Ident("a"), "b"), "c") */
            struct Nodo* prev=(struct Nodo*)NULL;
            while (""" + _P + """mirar()->tipo==T_DOT) {
                """ + _P + """avanzar();
                if (""" + _P + """mirar()->tipo!=T_IDENT && """ + _P + """mirar()->tipo!=T_RC && """ + _P + """mirar()->tipo!=T_MODULO) break;
                if (!prev) {
                    struct Identificador* obj=(struct Identificador*)calloc(1,sizeof(struct Identificador));
                    obj->tipo=""" + _P + """cs("Identificador"); obj->nombre=""" + _P + """cs(_nm);
                    prev=(struct Nodo*)obj;
                }
                strncpy(_nm, """ + _P + """mirar()->val, sizeof(_nm)-1); _nm[sizeof(_nm)-1] = '\\0'; """ + _P + """avanzar();
                if (""" + _P + """mirar()->tipo==T_LPAREN && """ + _P + """tpos + 1 < """ + _P + """ntks && """ + _P + """tks[""" + _P + """tpos + 1].tipo!=T_DOT) {
                    /* method call on last segment */
                    if(prev) free(prev);
                    """ + _P + """avanzar();
                    struct ListaNodo* args=NULL; struct ListaNodo** acur=&args;
                    if (""" + _P + """mirar()->tipo!=T_RPAREN) {
                        while (1) {
                            if (""" + _P + """mirar()->tipo==T_ARROW) {
                                """ + _P + """avanzar();
                                struct Nodo* ae=""" + _P + """expr();
                                struct ArgumentoTransferido* at=(struct ArgumentoTransferido*)calloc(1,sizeof(struct ArgumentoTransferido));
                                at->tipo=""" + _P + """cs("ArgumentoTransferido"); at->expr=ae;
                                *acur=""" + _P + """mk_list((struct Nodo*)at,NULL);
                            } else { *acur=""" + _P + """mk_list(""" + _P + """expr(),NULL); }
                            acur=&(*acur)->cola;
                            if (""" + _P + """mirar()->tipo!=T_COMMA) break;
                            """ + _P + """avanzar();
                        }
                    }
                    """ + _P + """esperar(T_RPAREN);
                    struct LlamadaFuncion* n=(struct LlamadaFuncion*)calloc(1,sizeof(struct LlamadaFuncion));
                    n->tipo=""" + _P + """cs("LlamadaFuncion"); n->nombre=""" + _P + """cs(_nm); n->argumentos=args;
                    return (struct Nodo*)n;
                }
                struct ExprAccesoCampo* ac=(struct ExprAccesoCampo*)calloc(1,sizeof(struct ExprAccesoCampo));
                ac->tipo=""" + _P + """cs("ExprAccesoCampo"); ac->objeto=prev; ac->nombre_campo=""" + _P + """cs(_nm);
                prev=(struct Nodo*)ac;
                if (""" + _P + """mirar()->tipo!=T_DOT) break;
            }
            return prev;
        }
        struct Identificador* n=(struct Identificador*)calloc(1,sizeof(struct Identificador));
        n->tipo=""" + _P + """cs("Identificador"); n->nombre=""" + _P + """cs(_nm);
        return (struct Nodo*)n;
    }
    if (t->tipo==T_LPAREN) { """ + _P + """avanzar(); struct Nodo* e=""" + _P + """expr(); """ + _P + """esperar(T_RPAREN); return e; }
    fprintf(stderr,"[PARSER] L%d:%d: expresion inesperada token=%d\\n",t->linea,t->col,t->tipo);
    exit(1);
}
struct Programa """ + _P + """programa() {
    struct ListaNodo* lst=NULL; struct ListaNodo** cur=&lst;
    while (""" + _P + """mirar()->tipo!=T_EOF) {
        if (""" + _P + """mirar()->tipo==T_NL||""" + _P + """mirar()->tipo==T_DEDENT) { """ + _P + """avanzar(); continue; }
        struct Nodo* st=""" + _P + """sentencia();
        if (st) { *cur=""" + _P + """mk_list(st,NULL); cur=&(*cur)->cola; }
    }
    struct Programa p; memset(&p,0,sizeof(p));
    p.tipo=""" + _P + """cs("Programa"); p.sentencias=lst;
    return p;
}
"""
        for ln in B.strip().split('\n'):
            ctx.lineas.append(ln)

def emitir_parsear(ctx, nodo):
        emitir_token_defs(ctx)
        gen_tok_c(ctx)
        gen_parse(ctx)
        ctx.write_line("struct Programa parsear(CadenaSegura fuente) {")
        ctx.indent += 1
        ctx.write_line("_P_ntks = 0; _P_tpos = 0; _P_p_err = 0; _P_nivel_pila = 0;")
        ctx.write_line("_P_pila_indent[0] = 0;")
        ctx.write_line("_P_tokenizar(fuente.datos, fuente.longitud);")
        ctx.write_line("{ int _has_det = 0; for (int _di = 0; _di < _P_ntks; _di++) { if (strcmp(_P_tks[_di].val, \"detectar_ciclo_outlives\") == 0) { _has_det = 1; break; } } if (_has_det) { for (int _di = 0; _di < _P_ntks; _di++) { fprintf(stderr, \"TK %d tipo=%d val='%s' L%d\\n\", _di, _P_tks[_di].tipo, _P_tks[_di].val, _P_tks[_di].linea); } fflush(stderr); } }")
        ctx.write_line("_P_procesar_indentacion_final();")
        ctx.write_line("struct Programa _prog = _P_programa();")
        ctx.write_line("return _prog;")
        ctx.indent -= 1
        ctx.write_line("}")
        ctx.write_line("")

def emitir_volcar_ast(ctx, nodo):
        ctx.write_line("void _volcar_nodo(struct Nodo* nodo, int nivel) {")
        ctx.indent += 1
        ctx.write_line('if (!nodo) { printf("(null)\\n"); return; }')
        ctx.write_line("for (int _i = 0; _i < nivel; _i++) printf(\"  \");")
        ctx.write_line('printf("[%s]\\n", nodo->tipo.datos);')
        branches = []
        for nombre, info in ctx._estructuras.items():
            if nombre in ('Nodo', 'ListaSimbolo',
                          'NodoBloque', 'BloqueInseguro', 'ListaToken', 'Simbolo',
                          'Generador', 'AnalizadorSemantico', 'TablaSimbolos', 'Parser'):
                continue
            campos = info.get('campos', [])
            is_adt = info.get('es_adt', False)
            printable = []
            children_list = []
            children_single = []
            for c_nombre, c_tipo in campos:
                if c_nombre in info.get('campos_pointer', set()):
                    if c_tipo in ('ListaNodo', 'ListaParametro', 'ListaToken', 'ListaSimbolo'):
                        children_list.append((c_nombre, c_tipo))
                    else:
                        children_single.append(c_nombre)
                elif c_tipo in ('entero', 'int'):
                    printable.append((c_nombre, 'int'))
                elif c_tipo == 'texto':
                    printable.append((c_nombre, 'CadenaSegura'))
                elif c_tipo == 'booleano':
                    printable.append((c_nombre, 'int'))
            if not printable and not children_list and not children_single:
                continue
            branches.append((nombre, printable, children_list, children_single, is_adt))
        for idx, (nombre, printable, children_list, children_single, is_adt) in enumerate(branches):
            if idx == 0:
                ctx.write_line(f'if (strcmp(nodo->tipo.datos, "{nombre}") == 0) {{')
            else:
                ctx.write_line(f'else if (strcmp(nodo->tipo.datos, "{nombre}") == 0) {{')
            ctx.indent += 1
            for c_nombre, c_tipo in printable:
                if c_tipo == 'CadenaSegura':
                    ctx.write_line(f'printf("  {c_nombre}: %s\\n", ((struct {nombre}*)nodo)->{c_nombre}.datos);')
                else:
                    ctx.write_line(f'printf("  {c_nombre}: %d\\n", ((struct {nombre}*)nodo)->{c_nombre});')
            for c_nombre in children_single:
                ctx.write_line(f'_volcar_nodo(((struct {nombre}*)nodo)->{c_nombre}, nivel + 1);')
            for c_nombre, c_tipo in children_list:
                ctx.write_line(f'{{ struct {c_tipo}* _cur = ((struct {nombre}*)nodo)->{c_nombre}; while (_cur) {{ _volcar_nodo(_cur->cabeza, nivel + 1); _cur = _cur->cola; }} }}')
            ctx.indent -= 1
            ctx.write_line("}")
        ctx.write_line('else { printf("  (tipo desconocido)\\n"); }')
        ctx.indent -= 1
        ctx.write_line("}")
        ctx.write_line("")
        ctx._externas['volcar_ast'] = ['struct Nodo*', 'int']
        ctx.write_line("void volcar_ast(struct Nodo* nodo, int nivel) { _volcar_nodo(nodo, nivel); }")
        ctx.write_line("")

