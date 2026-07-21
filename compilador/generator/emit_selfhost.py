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
            "#define T_BREAK 10",
            "#define T_CONTINUE 11",
            "#define T_DOT 12",
            "#define T_IDENT 13",
            "#define T_NUM 14",
            "#define T_STR 15",
            "#define T_GT 16",
            "#define T_LT 17",
            "#define T_EQ 18",
            "#define T_NE 19",
            "#define T_LE 20",
            "#define T_GE 21",
            "#define T_ASSIGN 22",
            "#define T_PLUS 23",
            "#define T_MINUS 24",
            "#define T_MUL 25",
            "#define T_DIV 26",
            "#define T_MOD 27",
            "#define T_ARROW 28",
            "#define T_LPAREN 29",
            "#define T_RPAREN 30",
            "#define T_COLON 31",
            "#define T_COMMA 32",
            "#define T_NL 33",
            "#define T_INDENT 34",
            "#define T_DEDENT 35",
            "#define T_EOF 36",
            "#define T_STRUCT 37",
            "#define T_AND 38",
            "#define T_OR 39",
            "#define T_NOT 40",
            "#define T_TRUE 41",
            "#define T_FALSE 42",
            "#define T_INSEGURO 43",
            "#define T_IMPORTAR_C 44",
            "#define T_AMPERSAND 45",
            "#define T_EXTERNO 46",
            "",
            "#define MAX_TOKS 16384",
            "typedef struct { int tipo; int linea; int col; char val[256]; } _P_Token;",
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
            "        char c = s[i];",
            "        if (c == ' ' || c == '\\t') { i++; co++; continue; }",
"        if (c == '\\r') { i++; continue; }",
            "        if (c == '\\n') {",
            "            " + P + "tks[" + P + "ntks].tipo = T_NL; " + P + "tks[" + P + "ntks].linea = li; " + P + "tks[" + P + "ntks].col = 0;",
            "            " + P + "ntks++; i++; li++; co = 1;",
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
"            int _rlen = (i - st - 2) < 255 ? (i - st - 2) : 255;",
"            char _tmp[256]; strncpy(_tmp, s + st + 1, _rlen); _tmp[_rlen] = 0;",
"            int _un = 0;",
"            for (int _si = 0; _tmp[_si] && _un < 254; _si++) {",
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
"            int vl = (i - st) < 255 ? (i - st) : 255;",
"            strncpy(" + P + "tks[" + P + "ntks].val, s + st, vl); " + P + "tks[" + P + "ntks].val[vl] = 0;",
"            " + P + "tks[" + P + "ntks].tipo = T_NUM; " + P + "tks[" + P + "ntks].linea = li; " + P + "tks[" + P + "ntks].col = scol;",
            "            " + P + "ntks++; co += (i - st); continue;",
            "        }",
"        if ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || c == '_') {",
"            int st = i; int scol = co;",
"            while (i < len && ((s[i] >= 'a' && s[i] <= 'z') || (s[i] >= 'A' && s[i] <= 'Z') || (s[i] >= '0' && s[i] <= '9') || s[i] == '_')) i++;",
"            int vl = (i - st) < 255 ? (i - st) : 255;",
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
            '                {NULL,0}',
            '            };',
            '            int _kt = T_IDENT;',
            '            for (int _ki = 0; _ks[_ki].p; _ki++) {',
            '                if (strcmp(' + P + 'tks[' + P + 'ntks].val, _ks[_ki].p) == 0) { _kt = _ks[_ki].t; break; }',
            '            }',
            '            ' + P + 'tks[' + P + 'ntks].tipo = _kt;',
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
struct Nodo* """ + _P + """sentencia() {
#ifdef SYN_DEBUG_PARSE
    fprintf(stderr, "PARSE S tok=%d pos=%d/%d\\n", """ + _P + """mirar()->tipo, """ + _P + """tpos, """ + _P + """ntks);
    fflush(stderr);
#endif
    while (""" + _P + """mirar()->tipo == T_NL) { """ + _P + """avanzar(); }
    """ + _P + """Token* t = """ + _P + """mirar();
    if (t->tipo == T_FUNC) {
        """ + _P + """avanzar();
        if (""" + _P + """mirar()->tipo != T_IDENT) { """ + _P + """sinc_skip(); return NULL; }
        char _nm[256]; strcpy(_nm, """ + _P + """mirar()->val);
        """ + _P + """avanzar();
        """ + _P + """esperar(T_LPAREN);
        struct ListaNodo* params = NULL;
        struct ListaNodo** pcur = &params;
        if (""" + _P + """mirar()->tipo != T_RPAREN) {
            while (1) {
                int is_transfer = 0;
                if (""" + _P + """mirar()->tipo == T_ARROW) { is_transfer=1; """ + _P + """avanzar(); }
                if (""" + _P + """mirar()->tipo != T_IDENT) break;
                char _pn[256]; strcpy(_pn, """ + _P + """mirar()->val);
                """ + _P + """avanzar();
                """ + _P + """esperar(T_COLON);
                if (""" + _P + """mirar()->tipo != T_IDENT) break;
                char _pt[256]; strcpy(_pt, """ + _P + """mirar()->val);
                """ + _P + """avanzar();
                while (""" + _P + """mirar()->tipo == T_MUL) { strcat(_pt,"*"); """ + _P + """avanzar(); }
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
        if (""" + _P + """mirar()->tipo != T_IDENT) { """ + _P + """sinc_skip(); return NULL; }
        char _rt[256]; strcpy(_rt, """ + _P + """mirar()->val);
        """ + _P + """avanzar();
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
        if (""" + _P + """mirar()->tipo != T_IDENT) { """ + _P + """sinc_skip(); return NULL; }
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
            if (""" + _P + """mirar()->tipo != T_IDENT) { """ + _P + """sinc_skip(); break; }
            char _pn[256]; strcpy(_pn, """ + _P + """mirar()->val);
            """ + _P + """avanzar();
            """ + _P + """esperar(T_COLON);
            if (""" + _P + """mirar()->tipo != T_IDENT) { """ + _P + """sinc_skip(); break; }
            char _pt[256]; strcpy(_pt, """ + _P + """mirar()->val);
            """ + _P + """avanzar();
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
        struct ListaNodo* cpo=""" + _P + """bloque();
        struct ListaNodo* sino = NULL;
        if (""" + _P + """mirar()->tipo == T_ELSE) { """ + _P + """avanzar(); """ + _P + """esperar(T_COLON); sino=""" + _P + """bloque(); }
        struct SentenciaSi* n = (struct SentenciaSi*)calloc(1,sizeof(struct SentenciaSi));
        n->tipo=""" + _P + """cs("SentenciaSi"); n->condicion=cond;
        n->cuerpo=cpo; n->cuerpo_sino=sino;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_WHILE) {
        """ + _P + """avanzar();
        struct Nodo* cond=""" + _P + """expr();
        """ + _P + """esperar(T_COLON);
        struct ListaNodo* cpo=""" + _P + """bloque();
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
        struct Nodo* cn=""" + _P + """expr(); """ + _P + """esperar(T_ARROW);
        struct Nodo* rp=""" + _P + """expr();
        struct SentenciaEscuchar* n = (struct SentenciaEscuchar*)calloc(1,sizeof(struct SentenciaEscuchar));
        n->tipo=""" + _P + """cs("SentenciaEscuchar"); n->canal=cn; n->respuesta=rp;
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
        if (""" + _P + """mirar()->tipo != T_IDENT) { """ + _P + """sinc_skip(); return NULL; }
        char _imp[256]; strcpy(_imp, """ + _P + """mirar()->val); int _iml = (int)strlen(_imp);
        """ + _P + """avanzar();
        while (""" + _P + """mirar()->tipo == T_DOT) { """ + _P + """avanzar(); if (""" + _P + """mirar()->tipo != T_IDENT) break; strcat(_imp,"."); strcat(_imp,""" + _P + """mirar()->val); """ + _P + """avanzar(); }
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
        if (""" + _P + """mirar()->tipo != T_IDENT) { """ + _P + """sinc_skip(); return NULL; }
        char _enm[256]; strcpy(_enm, """ + _P + """mirar()->val);
        """ + _P + """avanzar();
        """ + _P + """esperar(T_LPAREN);
        struct ListaParametro* eparams = NULL;
        struct ListaParametro** epcur = &eparams;
        if (""" + _P + """mirar()->tipo != T_RPAREN) {
            while (1) {
                if (""" + _P + """mirar()->tipo != T_IDENT) break;
                char _epn[256]; strcpy(_epn, """ + _P + """mirar()->val);
                """ + _P + """avanzar();
                """ + _P + """esperar(T_COLON);
                if (""" + _P + """mirar()->tipo != T_IDENT) break;
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
        if (""" + _P + """mirar()->tipo != T_IDENT) { """ + _P + """sinc_skip(); return NULL; }
        char _ert[256]; strcpy(_ert, """ + _P + """mirar()->val);
        """ + _P + """avanzar();
        struct DeclaracionExterna* n = (struct DeclaracionExterna*)calloc(1,sizeof(struct DeclaracionExterna));
        n->tipo=""" + _P + """cs("DeclaracionExterna"); n->nombre=""" + _P + """cs(_enm);
        n->parametros=eparams; n->tipo_retorno=""" + _P + """cs(_ert);
        return (struct Nodo*)n;
    }
    if (t->tipo == T_INSEGURO) { """ + _P + """avanzar();
        """ + _P + """esperar(T_COLON);
        struct ListaNodo* cpo=""" + _P + """bloque();
        struct BloqueInseguro* n = (struct BloqueInseguro*)calloc(1,sizeof(struct BloqueInseguro));
        n->tipo=""" + _P + """cs("BloqueInseguro"); n->cuerpo=cpo;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_IDENT && """ + _P + """tpos + 1 < """ + _P + """ntks && """ + _P + """tks[""" + _P + """tpos + 1].tipo == T_ASSIGN) {
        char _vn[256]; strcpy(_vn, t->val);
        """ + _P + """avanzar(); """ + _P + """avanzar();
        struct Nodo* val=""" + _P + """expr();
        struct AsignacionVariable* n = (struct AsignacionVariable*)calloc(1,sizeof(struct AsignacionVariable));
        n->tipo=""" + _P + """cs("AsignacionVariable");
        n->nombre=""" + _P + """cs(_vn); n->expresion=val;
        return (struct Nodo*)n;
    }
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
    }
    if (""" + _P + """mirar()->tipo==T_AMPERSAND) {
        """ + _P + """avanzar();
        struct Nodo* e=""" + _P + """una();
        struct ExprObtenerDireccion* n=(struct ExprObtenerDireccion*)calloc(1,sizeof(struct ExprObtenerDireccion));
        n->tipo=""" + _P + """cs("ExprObtenerDireccion"); n->expr=e;
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
    if (t->tipo==T_IDENT) {
        char _nm[256]; strcpy(_nm, t->val);
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
                if (""" + _P + """mirar()->tipo!=T_IDENT) break;
                if (!prev) {
                    struct Identificador* obj=(struct Identificador*)calloc(1,sizeof(struct Identificador));
                    obj->tipo=""" + _P + """cs("Identificador"); obj->nombre=""" + _P + """cs(_nm);
                    prev=(struct Nodo*)obj;
                }
                strcpy(_nm, """ + _P + """mirar()->val); """ + _P + """avanzar();
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

def emitir_generar(ctx, nodo):
        ctx.lineas.extend(["// --- Generador de C ---"])
        emitir_token_defs(ctx)
        gen_tok_c(ctx)
        gen_parse(ctx)
        # Use a placeholder that won't collide with C braces
        _PH = '@@P@@'
        H = f"""
// --- AST Walker ---
int {_PH}indent = 0;
FILE* {_PH}out = NULL;
char {_PH}vn[1024][64];
char {_PH}vt[1024][64];
int {_PH}nv = 0;
char {_PH}ret_type[64];
char {_PH}extern_names[64][64];
char {_PH}extern_params[64][256];
int {_PH}nextern = 0;
char {_PH}snames[64][64];
int {_PH}nsnames = 0;

void {_PH}reset() {{ {_PH}nv = 0; }}
int {_PH}find(const char* n) {{ if(!n) return -1; for(int i=0;i<{_PH}nv;i++) if(strcmp({_PH}vn[i],n)==0) return i; return -1; }}
const char* {_PH}decl(const char* n, const char* t) {{
    if(!n||!t) return t?t:"int";
    int i={_PH}find(n); if(i>=0) return {_PH}vt[i];
    if({_PH}nv<1024){{ strncpy({_PH}vn[{_PH}nv],n,63); {_PH}vn[{_PH}nv][63]=0; strncpy({_PH}vt[{_PH}nv],t,63); {_PH}vt[{_PH}nv][63]=0; {_PH}nv++; }}
    return t;
}}

void {_PH}emit(const char* s) {{
    for(int i=0;i<{_PH}indent;i++) fprintf({_PH}out,"    ");
    fprintf({_PH}out,"%s\\n",s);
}}

void {_PH}cp(char* d, CadenaSegura cs) {{ if(!cs.datos||cs.longitud<=0){{ d[0]=0; return; }} int _len=cs.longitud<4095?cs.longitud:4095; memcpy(d,cs.datos,_len); d[_len]=0; }}

const char* {_PH}tex(struct Nodo* n) {{
    if(!n) return "int";
    const char* t=n->tipo.datos;
    if(strcmp(t,"LiteralNumero")==0) return "int";
    if(strcmp(t,"LiteralCadena")==0) return "CadenaSegura";
    if(strcmp(t,"Identificador")==0) {{ struct Identificador* i=(struct Identificador*)n; char m[256]; {_PH}cp(m,i->nombre); int j={_PH}find(m); return j>=0?{_PH}vt[j]:"int"; }}
    if(strcmp(t,"OpBinaria")==0||strcmp(t,"OpUnaria")==0) return "int";
    if(strcmp(t,"LlamadaFuncion")==0) {{
        struct LlamadaFuncion* l=(struct LlamadaFuncion*)n;
        char m[256]; {_PH}cp(m,l->nombre);
        if(strcmp(m,"_argc")==0) return "int";
        if(strcmp(m,"_argv")==0||strcmp(m,"leer")==0||strcmp(m,"leer_linea")==0||strcmp(m,"concat")==0) return "CadenaSegura";
        if(strcmp(m,"abrir")==0) return "Canal";
        if(strcmp(m,"cerrar")==0||strcmp(m,"salir")==0||strcmp(m,"escribir")==0||strcmp(m,"escribir_linea")==0) return "void";
        if(strcmp(m,"reserva")==0||strcmp(m,"suma")==0||strcmp(m,"producto")==0||strcmp(m,"relu")==0
    ||strcmp(m,"crear_tensor")==0||strcmp(m,"suma_tensor")==0||strcmp(m,"producto_punto")==0) return "Tensor";
        if(strcmp(m,"tokenizar")==0) return "int";
        if(strcmp(m,"parsear")==0) return "struct Programa";
        if(strcmp(m,"generar")==0) return "int";
        if(strcmp(m,"libera")==0) return "void";
        if(strcmp(m,"texto_a_entero")==0) return "int";
        if(strcmp(m,"texto_a_decimal")==0) return "float";
        if(strcmp(m,"decimal_a_texto")==0) return "CadenaSegura";
        for(int _si=0;_si<{_PH}nsnames;_si++){{ if(strcmp(m,{_PH}snames[_si])==0) {{ char _sret[64]; snprintf(_sret,sizeof(_sret),"struct %s",m); return _sret; }} }}
        return "int";
    }}
    if(strcmp(t,"ExprAccesoCampo")==0||strcmp(t,"ArgumentoTransferido")==0) return "int";
    if(strcmp(t,"ExprTensor")==0) return "Tensor";
    if(strcmp(t,"ExprObtenerDireccion")==0) return "int*";
    if(strcmp(t,"ExprDereferencia")==0) return "int";
    return "int";
}}

void {_PH}ea(struct Nodo* n, char* b, int sz);
void {_PH}vl(struct ListaNodo* l);
void {_PH}v(struct Nodo* n);

int {_PH}extern_needs_datos(const char* fn, int argidx) {{
    for(int _ei=0;_ei<{_PH}nextern;_ei++){{
        if(strcmp({_PH}extern_names[_ei],fn)==0){{
            int _ec=0,_epos=0;
            char _eb[256]; strcpy(_eb,{_PH}extern_params[_ei]);
            while(_eb[_epos]){{
                int _estart=_epos;
                while(_eb[_epos]&&_eb[_epos]!=',') _epos++;
                _eb[_epos]=0;
                if(_ec==argidx) return strcmp(_eb+_estart,"char*")==0;
                _ec++; _epos++;
            }}
            return 0;
        }}
    }}
    return 0;
}}
void {_PH}vl(struct ListaNodo* l) {{ while(l){{ {_PH}v(l->cabeza); l=l->cola; }} }}

void {_PH}ea(struct Nodo* n, char* b, int sz) {{
    char i[512],d[512],o[512],m[256];
    if(!n){{ snprintf(b,sz,"0"); return; }}
    const char* t=n->tipo.datos;
    if(strcmp(t,"LiteralNumero")==0){{ struct LiteralNumero* x=(struct LiteralNumero*)n; snprintf(b,sz,"%d",x->valor); return; }}
    if(strcmp(t,"LiteralCadena")==0){{ struct LiteralCadena* x=(struct LiteralCadena*)n; snprintf(b,sz,"(CadenaSegura){{.longitud=%d,.datos=\\"%.*s\\"}}",x->valor.longitud,x->valor.longitud,x->valor.datos); return; }}
    if(strcmp(t,"Identificador")==0){{ struct Identificador* x=(struct Identificador*)n; char _tmp_nm[256]; {_PH}cp(_tmp_nm,x->nombre); if(strcmp(_tmp_nm,"nulo")==0) strcpy(b,"NULL"); else strcpy(b,_tmp_nm); return; }}
    if(strcmp(t,"OpBinaria")==0){{ struct OpBinaria* x=(struct OpBinaria*)n; {_PH}ea(x->izquierdo,i,512); {_PH}ea(x->derecho,d,512); char _o[16]; {_PH}cp(_o,x->operador->lexema); snprintf(b,sz,"(%s %s %s)",i,_o,d); return; }}
    if(strcmp(t,"OpUnaria")==0){{ struct OpUnaria* x=(struct OpUnaria*)n; {_PH}ea(x->expr,i,512); char _o[16]; {_PH}cp(_o,x->operador->lexema); snprintf(b,sz,"(%s%s)",_o,i); return; }}
    if(strcmp(t,"LlamadaFuncion")==0){{
        struct LlamadaFuncion* x=(struct LlamadaFuncion*)n; {_PH}cp(m,x->nombre);
        {{ char* _p=m; while(*_p){{ if(*_p=='.') *_p='_'; _p++; }} }}
        int _is_struct = 0;
        for(int _si=0;_si<{_PH}nsnames;_si++){{ if(strcmp(m,{_PH}snames[_si])==0){{ _is_struct=1; break; }} }}
        if(_is_struct && !x->argumentos){{ snprintf(b,sz,"%s_nuevo()",m); return; }}
        int _coer = (strcmp(m,"escribir")==0||strcmp(m,"escribir_linea")==0||strcmp(m,"abrir")==0||strcmp(m,"concat")==0);
        char a[4096]=""; int p=0; int aidx=0; struct ListaNodo* c=x->argumentos;
        while(c){{ if(p>0){{ a[p++]=','; a[p++]=' '; }}
            {_PH}ea(c->cabeza,i,512);
            int _dos = {_PH}extern_needs_datos(m,aidx);
            if(_dos){{ snprintf(o,sizeof(o),"(%s).datos",i); strcpy(i,o); }}
            if(_coer){{ const char* _at = {_PH}tex(c->cabeza);
                if(strcmp(_at,"int")==0){{ char _w[1024]; snprintf(_w,sizeof(_w),"entero_a_texto(%s)",i); int k=0; while(_w[k]) a[p++]=_w[k++]; }}
                else if(strcmp(_at,"float")==0){{ char _w[1024]; snprintf(_w,sizeof(_w),"decimal_a_texto(%s)",i); int k=0; while(_w[k]) a[p++]=_w[k++]; }}
                else{{ int k=0; while(i[k]) a[p++]=i[k++]; }}
            }}else{{ int k=0; while(i[k]) a[p++]=i[k++]; }}
            c=c->cola; aidx++;
        }}
        a[p]=0; snprintf(b,sz,"%s(%s)",m,a); return;
    }}
    if(strcmp(t,"ExprAccesoCampo")==0){{ struct ExprAccesoCampo* x=(struct ExprAccesoCampo*)n; {_PH}ea(x->objeto,o,512); {_PH}cp(m,x->nombre_campo); const char* _ot={_PH}tex(x->objeto); int _isp=(strlen(_ot)>0&&_ot[strlen(_ot)-1]=='*'); snprintf(b,sz,"%s%s%s",o,_isp?"->":".",m); return; }}
    if(strcmp(t,"ExprTensor")==0){{ struct ExprTensor* x=(struct ExprTensor*)n; {_PH}ea(x->filas,i,512); {_PH}ea(x->columnas,d,512); snprintf(b,sz,"(Tensor){{.filas=%s,.columnas=%s,.datos=(float*)calloc(%s*%s,sizeof(float))}}",i,d,i,d); return; }}
    if(strcmp(t,"ArgumentoTransferido")==0){{ struct ArgumentoTransferido* x=(struct ArgumentoTransferido*)n; {_PH}ea(x->expr,b,sz); return; }}
    if(strcmp(t,"ExprObtenerDireccion")==0){{ struct ExprObtenerDireccion* x=(struct ExprObtenerDireccion*)n; {_PH}ea(x->expr,i,512); snprintf(b,sz,"(&%s)",i); return; }}
    if(strcmp(t,"ExprDereferencia")==0){{ struct ExprDereferencia* x=(struct ExprDereferencia*)n; {_PH}ea(x->expr,i,512); snprintf(b,sz,"(*%s)",i); return; }}
    snprintf(b,sz,"/*?*/");
}}

void {_PH}v_log(struct LogLlamada* n) {{
    char f[4096]=""; int fp=0,ap=0,fi=1; char b[512]; char pr[4096]=""; char tn[64]; char tmp[512];
    struct ListaNodo* c=n->argumentos;
    while(c){{ if(!fi){{ f[fp++]=' '; }} fi=0; f[fp++]='%'; f[fp++]='s';
        {_PH}cp(tn,c->cabeza->tipo);
        {_PH}ea(c->cabeza,tmp,512);
        if(strcmp(tn,"LiteralCadena")==0){{ snprintf(b,sizeof(b),"%s.datos",tmp); }}
        else{{ strcpy(b,tmp); }}
        if(ap>0){{ pr[ap++]=','; pr[ap++]=' '; }} int k=0; while(b[k]) pr[ap++]=b[k++]; c=c->cola;
    }}
    f[fp]=0; pr[ap]=0; char ln[4096];
    if(ap>0) snprintf(ln,sizeof(ln),"printf(\\"%s\\\\n\\",%s);",f,pr);
    else snprintf(ln,sizeof(ln),"printf(\\"%s\\\\n\\");",f);
    {_PH}emit(ln);
}}

const char* {_PH}mt(const char* st) {{
    char _mtb[64];
    char _base[64]; strcpy(_base,st);
    int _mlen = strlen(_base);
    int _isptr = (_mlen>0 && _base[_mlen-1]=='*');
    if(_isptr) _base[_mlen-1]=0;
    const char* _r=NULL;
    if(strcmp(_base,"entero")==0||strcmp(_base,"int")==0) _r="int";
    else if(strcmp(_base,"texto")==0||strcmp(_base,"cadena")==0) _r="CadenaSegura";
    else if(strcmp(_base,"nulo")==0||strcmp(_base,"vacio")==0) _r="void";
    else if(strcmp(_base,"decimal")==0||strcmp(_base,"real")==0) _r="float";
    else if(strcmp(_base,"logico")==0||strcmp(_base,"booleano")==0) _r="int";
    else if(strcmp(_base,"Canal")==0||strcmp(_base,"canal")==0) _r="Canal";
    else if(strcmp(_base,"Tensor")==0||strcmp(_base,"tensor")==0) _r="Tensor";
    else if(strcmp(_base,"void")==0) _r="void";
    else if(strcmp(_base,"char")==0) _r="char";
    else if(strcmp(_base,"double")==0) _r="double";
    if(!_r) return NULL;
    if(_isptr){{ snprintf(_mtb,sizeof(_mtb),"%s*",_r); return _mtb; }}
    return _r;
}}
void {_PH}vest(struct DefinicionEstructura* n) {{
    char ln[4096];
    snprintf(ln,sizeof(ln),"typedef struct %s {{",n->nombre.datos); {_PH}emit(ln);
    {_PH}indent++;
    struct ListaParametro* c=n->campos;
    while(c){{ struct Parametro* p=(struct Parametro*)c->cabeza; char pn[256]; {_PH}cp(pn,p->nombre); char pt[256]; {_PH}cp(pt,p->tipo_param); const char* ct={_PH}mt(pt); if(ct){{ snprintf(ln,sizeof(ln),"%s %s;",ct,pn); }}else{{ snprintf(ln,sizeof(ln),"struct %s* %s;",pt,pn); }} {_PH}emit(ln); c=c->cola; }}
    {_PH}indent--; snprintf(ln,sizeof(ln),"}} %s;",n->nombre.datos); {_PH}emit(ln);
    snprintf(ln,sizeof(ln),"inline struct %s %s_nuevo() {{",n->nombre.datos,n->nombre.datos); {_PH}emit(ln);
    {_PH}indent++; snprintf(ln,sizeof(ln),"struct %s _r={{0}}; return _r;",n->nombre.datos); {_PH}emit(ln);
    {_PH}indent--; {_PH}emit("}}");
    if({_PH}nsnames<64){{ strcpy({_PH}snames[{_PH}nsnames],n->nombre.datos); {_PH}nsnames++; }}
}}

void {_PH}v(struct Nodo* n) {{
    if(!n) return;
    char b[4096],b2[4096],m[256],v[4096];
    const char* t=n->tipo.datos;
    if(strcmp(t,"DefinicionFuncion")==0){{
        {_PH}reset();
        struct DefinicionFuncion* f=(struct DefinicionFuncion*)n; {_PH}cp(m,f->nombre);
        {{ char* _p=m; while(*_p){{ if(*_p=='.') *_p='_'; _p++; }} }}
        if(strcmp(m,"escribir")==0||strcmp(m,"escribir_linea")==0||strcmp(m,"leer_linea")==0||strcmp(m,"abrir")==0||strcmp(m,"leer")==0||strcmp(m,"cerrar")==0||strcmp(m,"crear_tensor")==0||strcmp(m,"suma_tensor")==0||strcmp(m,"producto_punto")==0||strcmp(m,"relu")==0||strcmp(m,"reserva")==0||strcmp(m,"libera")==0||strcmp(m,"suma")==0||strcmp(m,"producto")==0||strcmp(m,"math_crear_tensor")==0||strcmp(m,"math_suma_tensor")==0||strcmp(m,"math_producto_punto")==0||strcmp(m,"math_relu")==0||strcmp(m,"mem_reserva")==0||strcmp(m,"mem_libera")==0||strcmp(m,"math_suma")==0||strcmp(m,"math_producto")==0||strcmp(m,"texto_a_entero")==0||strcmp(m,"texto_a_decimal")==0||strcmp(m,"decimal_a_texto")==0) return;
        char ps[4096]="void"; int pp=0,fi=1; struct ListaParametro* pc=f->parametros;
        while(pc){{ struct Parametro* p=(struct Parametro*)pc->cabeza; char pn[256]; {_PH}cp(pn,p->nombre); char pt[256]; {_PH}cp(pt,p->tipo_param);
            if(fi){{ pp=0; fi=0; }}else{{ ps[pp++]=','; ps[pp++]=' '; }}
            const char* _ct={_PH}mt(pt);
            char _tb[64]; if(_ct){{ strcpy(_tb,_ct); }}else{{ snprintf(_tb,sizeof(_tb),"struct %s",pt); }} _ct=_tb;
            int k=0; while(_ct[k]) ps[pp++]=_ct[k++]; ps[pp++]=' '; k=0; while(pn[k]) ps[pp++]=pn[k++];
            {_PH}decl(pn,_ct); pc=pc->cola;
        }}
        ps[pp]=0; char rt[64]; {_PH}cp(rt,f->tipo_retorno);
        {{
            const char* _ct={_PH}mt(rt);
            if(_ct){{ snprintf(b,sizeof(b),"%s %s(%s)",_ct,m,ps); strcpy({_PH}ret_type,_ct); }}
            else{{ snprintf(b,sizeof(b),"struct %s %s(%s)",rt,m,ps); snprintf({_PH}ret_type,sizeof({_PH}ret_type),"struct %s",rt); }}
        }}
        {_PH}emit(b); {_PH}emit("{{"); {_PH}indent++; {_PH}vl(f->cuerpo); {_PH}indent--; {_PH}emit("}}"); return;
    }}
    if(strcmp(t,"SentenciaSi")==0){{
        struct SentenciaSi* s=(struct SentenciaSi*)n; {_PH}ea(s->condicion,b,4096);
        snprintf(b2,sizeof(b2),"if (%s) {{",b); {_PH}emit(b2); {_PH}indent++; {_PH}vl(s->cuerpo); {_PH}indent--;
        if(s->cuerpo_sino){{ {_PH}emit("}} else {{"); {_PH}indent++; {_PH}vl(s->cuerpo_sino); {_PH}indent--; }}
        {_PH}emit("}}"); return;
    }}
    if(strcmp(t,"SentenciaMientras")==0){{
        struct SentenciaMientras* s=(struct SentenciaMientras*)n; {_PH}ea(s->condicion,b,4096);
        snprintf(b2,sizeof(b2),"while (%s) {{",b); {_PH}emit(b2); {_PH}indent++; {_PH}vl(s->cuerpo); {_PH}indent--; {_PH}emit("}}"); return;
    }}
    if(strcmp(t,"AsignacionVariable")==0){{
        struct AsignacionVariable* a=(struct AsignacionVariable*)n; {_PH}cp(m,a->nombre); {_PH}ea(a->expresion,v,4096);
        const char* vt={_PH}tex(a->expresion); if(!vt) vt="int";
        if({_PH}find(m)<0){{ {_PH}decl(m,vt); snprintf(b,sizeof(b),"%s %s = %s;",vt,m,v); }}
        else snprintf(b,sizeof(b),"%s = %s;",m,v);
        {_PH}emit(b); return;
    }}
    if(strcmp(t,"AsignacionCampo")==0){{
        struct AsignacionCampo* a=(struct AsignacionCampo*)n; {_PH}ea(a->objeto,b,4096); {_PH}cp(m,a->nombre_campo); {_PH}ea(a->expresion,v,4096);
        const char* _ot={_PH}tex(a->objeto); int _isp=(strlen(_ot)>0&&_ot[strlen(_ot)-1]=='*');
        snprintf(b2,sizeof(b2),"%s%s%s = %s;",b,_isp?"->":".",m,v); {_PH}emit(b2); return;
    }}
    if(strcmp(t,"SentenciaRetornar")==0){{
        struct SentenciaRetornar* r=(struct SentenciaRetornar*)n;
        if(r->expr){{ {_PH}ea(r->expr,v,4096);
            if(strcmp(v,"nulo")==0||strcmp(v,"0")==0||strcmp(v,"NULL")==0){{ if({_PH}ret_type[0]&&strcmp({_PH}ret_type,"void")!=0){{ snprintf(b,sizeof(b),"return (%s){{0}};",{_PH}ret_type); }}else snprintf(b,sizeof(b),"return;"); }}
            else snprintf(b,sizeof(b),"return %s;",v);
        }}else snprintf(b,sizeof(b),"return;");
        {_PH}emit(b); return;
    }}
    if(strcmp(t,"SentenciaExpr")==0){{ struct SentenciaExpr* e=(struct SentenciaExpr*)n; if(e->expr){{ if(strcmp(e->expr->tipo.datos,"LogLlamada")==0){{ {_PH}v_log((struct LogLlamada*)e->expr); }} else {{ {_PH}ea(e->expr,v,4096); snprintf(b,sizeof(b),"%s;",v); {_PH}emit(b); }} }} return; }}
    if(strcmp(t,"LogLlamada")==0){{ {_PH}v_log((struct LogLlamada*)n); return; }}
    if(strcmp(t,"SentenciaRomper")==0){{ {_PH}emit("break;"); return; }}
    if(strcmp(t,"SentenciaSiguiente")==0){{ {_PH}emit("continue;"); return; }}
    if(strcmp(t,"SentenciaLanzar")==0){{ struct SentenciaLanzar* l=(struct SentenciaLanzar*)n; char fn[256]=""; char ab[512]=""; int ha=0; if(strcmp(l->llamada->tipo.datos,"LlamadaFuncion")==0){{ struct LlamadaFuncion* lf=(struct LlamadaFuncion*)l->llamada; {_PH}cp(fn,lf->nombre); if(lf->argumentos){{ {_PH}ea(lf->argumentos->cabeza,ab,512); ha=1; }} }}else{{ {_PH}ea(l->llamada,fn,256); ha=1; }} if(ha){{ snprintf(b,sizeof(b),"synapse_lanzar_hilo((void*(*)(void*))%s,(void*)(intptr_t)(%s));",fn,ab); }}else{{ snprintf(b,sizeof(b),"synapse_lanzar_hilo((void*(*)(void*))%s,NULL);",fn); }} {_PH}emit(b); return; }}
    if(strcmp(t,"SentenciaRecuperar")==0){{ struct SentenciaRecuperar* r=(struct SentenciaRecuperar*)n; {_PH}ea(r->accion_critica,b,4096); {_PH}ea(r->plan_b,v,4096); {_PH}emit("{{"); {_PH}indent++; snprintf(b2,sizeof(b2),"if(%s!=0){{%s;}}",b,v); {_PH}emit(b2); {_PH}indent--; {_PH}emit("}}"); return; }}
    if(strcmp(t,"SentenciaEscuchar")==0){{ struct SentenciaEscuchar* e=(struct SentenciaEscuchar*)n; {_PH}ea(e->canal,b,4096); {_PH}ea(e->respuesta,v,4096); snprintf(b2,sizeof(b2),"/* escuchar: %s -> %s */",b,v); {_PH}emit(b2); return; }}
    if(strcmp(t,"DefinicionEstructura")==0){{ {_PH}vest((struct DefinicionEstructura*)n); return; }}
    if(strcmp(t,"SentenciaImportar")==0){{ struct SentenciaImportar* i=(struct SentenciaImportar*)n; {_PH}cp(b,i->ruta); snprintf(b2,sizeof(b2),"/* importar %s */",b); {_PH}emit(b2); return; }}
    if(strcmp(t,"ImportarC")==0){{ struct ImportarC* x=(struct ImportarC*)n; {_PH}cp(m,x->ruta); if(x->es_sistema){{ snprintf(b,sizeof(b),"#include <%s>",m); }}else{{ snprintf(b,sizeof(b),"#include \\"%s\\"",m); }} {_PH}emit(b); return; }}
    if(strcmp(t,"DeclaracionExterna")==0){{
        struct DeclaracionExterna* x=(struct DeclaracionExterna*)n;
        char _enm[256]; {_PH}cp(_enm,x->nombre);
        strcpy({_PH}extern_names[{_PH}nextern],_enm);
        char _ebuf[256]=""; int _ep=0;
        struct ListaParametro* _epc=(struct ListaParametro*)x->parametros;
        while(_epc){{
            struct Parametro* p=(struct Parametro*)_epc->cabeza;
            if(_ep>0){{ _ebuf[_ep++]=','; }}
            char _ept[256]; {_PH}cp(_ept,p->tipo_param);
            int _ek=0; while(_ept[_ek]) _ebuf[_ep++]=_ept[_ek++];
            _epc=_epc->cola;
        }}
        _ebuf[_ep]=0;
        strcpy({_PH}extern_params[{_PH}nextern],_ebuf);
        {_PH}nextern++;
        /* C declaration comes from #include via importar_c */
        return;
    }}
    if(strcmp(t,"BloqueInseguro")==0){{ struct BloqueInseguro* x=(struct BloqueInseguro*)n; {_PH}emit("{{ /* unsafe */"); {_PH}indent++; {_PH}vl(x->cuerpo); {_PH}indent--; {_PH}emit("}}"); return; }}
    {_PH}emit("/* ??? */");
}}

int generar(struct Programa programa, CadenaSegura ruta) {{
    char sal[1024]; int sl=ruta.longitud;
    if(sl>4&&ruta.datos[sl-4]=='.'&&(ruta.datos[sl-3]=='s'||ruta.datos[sl-3]=='S')&&(ruta.datos[sl-2]=='y'||ruta.datos[sl-2]=='Y')&&(ruta.datos[sl-1]=='n'||ruta.datos[sl-1]=='N')){{
        memcpy(sal,ruta.datos,sl-4); sal[sl-4]='.'; sal[sl-3]='c'; sal[sl-2]=0;
    }}else snprintf(sal,sizeof(sal),"%.*s.c",ruta.longitud,ruta.datos);
    {_PH}out=fopen(sal,"w"); if(!{_PH}out){{ fprintf(stderr,"Error: no se puede crear %s\\n",sal); return 1; }}
    fprintf({_PH}out,"// Generado por Synapse (auto-hospedado)\\n");
    fprintf({_PH}out,"#include <stdio.h>\\n#include <stdlib.h>\\n#include <stdint.h>\\n#include <string.h>\\n#include <pthread.h>\\n");
    fprintf({_PH}out,"typedef struct {{int longitud;const char* datos;}} CadenaSegura;\\n");
    fprintf({_PH}out,"typedef struct {{uint32_t filas;uint32_t columnas;float* datos;int es_mapeado;}} Tensor;\\n");
    fprintf({_PH}out,"typedef struct {{FILE* stream;int es_valido;int es_virtual;const char* virtual_data;int virtual_len;}} Canal;\\n");
    fprintf({_PH}out,"#define POOL_BLOQUES 64\\n#define TAMANO_BLOQUE 4096\\n");
    fprintf({_PH}out,"#define nulo ((void*)0)\\n");
    fprintf({_PH}out,"// --- Declaraciones extern del runtime precompilado (synapse_rt.o) ---\\n");
    fprintf({_PH}out,"extern void escribir(CadenaSegura contenido);\\n");
    fprintf({_PH}out,"extern void escribir_linea(CadenaSegura contenido);\\n");
    fprintf({_PH}out,"extern CadenaSegura leer_linea(void);\\n");
    fprintf({_PH}out,"extern Canal abrir(CadenaSegura ruta, CadenaSegura modo);\\n");
    fprintf({_PH}out,"extern CadenaSegura leer(Canal canal);\\n");
    fprintf({_PH}out,"extern void cerrar(Canal canal);\\n");
    fprintf({_PH}out,"extern Tensor crear_tensor(int filas, int columnas);\\n");
    fprintf({_PH}out,"extern Tensor suma_tensor(Tensor a, Tensor b);\\n");
    fprintf({_PH}out,"extern Tensor producto_punto(Tensor a, Tensor b);\\n");
    fprintf({_PH}out,"extern Tensor relu(Tensor a);\\n");
    fprintf({_PH}out,"extern Tensor reserva(int tamano);\\n");
    fprintf({_PH}out,"extern void libera(Tensor bloque);\\n");
    fprintf({_PH}out,"extern Tensor suma(Tensor a, Tensor b);\\n");
    fprintf({_PH}out,"extern Tensor producto(Tensor a, Tensor b);\\n");
    fprintf({_PH}out,"extern int texto_a_entero(CadenaSegura str);\\n");
    fprintf({_PH}out,"extern float texto_a_decimal(CadenaSegura str);\\n");
    fprintf({_PH}out,"extern CadenaSegura decimal_a_texto(float n);\\n");
    fprintf({_PH}out,"extern CadenaSegura entero_a_texto(int n);\\n");
    fprintf({_PH}out,"extern void synapse_lanzar_hilo(void* (*fn)(void*), void* arg);\\n");
    fprintf({_PH}out,"extern void synapse_esperar_hilos(void);\\n");
    fprintf({_PH}out,"extern void pool_init(uint32_t total_blocks, uint32_t block_size);\\n");
    fprintf({_PH}out,"extern void pool_free(void* ptr);\\n");
    fprintf({_PH}out,"int _g_argc;\\nchar** _g_argv;\\nint _argc(){{return _g_argc;}}\\n");
    fprintf({_PH}out,"CadenaSegura _argv(int i){{if(i<0||i>=_g_argc)return (CadenaSegura){{0,(char*)\\"\\"}};return (CadenaSegura){{.longitud=(int)strlen(_g_argv[i]),.datos=_g_argv[i]}};}}\\n");
    fprintf({_PH}out,"void salir(int c){{exit(c);}}\\n");
    fprintf({_PH}out,"CadenaSegura concat(CadenaSegura a,CadenaSegura b){{int _tl=a.longitud+b.longitud;char* _buf=(char*)malloc(_tl+1);memcpy(_buf,a.datos,a.longitud);memcpy(_buf+a.longitud,b.datos,b.longitud);_buf[_tl]=0;CadenaSegura _r={{.longitud=_tl,.datos=_buf}};return _r;}}\\n");
    // Forward declarations
    struct ListaNodo* c=programa.sentencias;
    while(c){{ if(c->cabeza&&strcmp(c->cabeza->tipo.datos,"DefinicionEstructura")==0){{ struct DefinicionEstructura* d=(struct DefinicionEstructura*)c->cabeza; fprintf({_PH}out,"struct %s;\\n",d->nombre.datos); }} c=c->cola; }}
    // Function prototypes
    c=programa.sentencias;
    while(c){{ if(c->cabeza&&strcmp(c->cabeza->tipo.datos,"DefinicionFuncion")==0){{ struct DefinicionFuncion* f=(struct DefinicionFuncion*)c->cabeza; char _fn[256]; {_PH}cp(_fn,f->nombre); {{ char* _p=_fn; while(*_p){{ if(*_p=='.') *_p='_'; _p++; }} }} if(strcmp(_fn,"escribir")==0||strcmp(_fn,"escribir_linea")==0||strcmp(_fn,"leer_linea")==0||strcmp(_fn,"abrir")==0||strcmp(_fn,"leer")==0||strcmp(_fn,"cerrar")==0||strcmp(_fn,"crear_tensor")==0||strcmp(_fn,"suma_tensor")==0||strcmp(_fn,"producto_punto")==0||strcmp(_fn,"relu")==0||strcmp(_fn,"reserva")==0||strcmp(_fn,"libera")==0||strcmp(_fn,"suma")==0||strcmp(_fn,"producto")==0||strcmp(_fn,"math_crear_tensor")==0||strcmp(_fn,"math_suma_tensor")==0||strcmp(_fn,"math_producto_punto")==0||strcmp(_fn,"math_relu")==0||strcmp(_fn,"mem_reserva")==0||strcmp(_fn,"mem_libera")==0||strcmp(_fn,"math_suma")==0||strcmp(_fn,"math_producto")==0||strcmp(_fn,"texto_a_entero")==0||strcmp(_fn,"texto_a_decimal")==0||strcmp(_fn,"decimal_a_texto")==0) {{ c=c->cola; continue; }} char _ps[4096]="void"; int _pp=0,_fi=1; struct ListaParametro* _pc=f->parametros; while(_pc){{ struct Parametro* p=(struct Parametro*)_pc->cabeza; char _pn[256]; {_PH}cp(_pn,p->nombre); char _pt[256]; {_PH}cp(_pt,p->tipo_param); if(_fi){{ _pp=0; _fi=0; }}else{{ _ps[_pp++]=','; _ps[_pp++]=' '; }} const char* _ct={_PH}mt(_pt); char _tb[64]; if(_ct){{ strcpy(_tb,_ct); }}else{{ snprintf(_tb,sizeof(_tb),"struct %s",_pt); }} _ct=_tb; int _k=0; while(_ct[_k]) _ps[_pp++]=_ct[_k++]; _ps[_pp++]=' '; _k=0; while(_pn[_k]) _ps[_pp++]=_pn[_k++]; _pc=_pc->cola; }} _ps[_pp]=0; char _rt[64]; {_PH}cp(_rt,f->tipo_retorno); const char* _rct={_PH}mt(_rt); if(_rct){{ fprintf({_PH}out,"%s %s(%s);\\n",_rct,_fn,_ps); }}else{{ fprintf({_PH}out,"struct %s %s(%s);\\n",_rt,_fn,_ps); }} }} c=c->cola; }}
    {_PH}indent=0; c=programa.sentencias;
    while(c){{ {_PH}v(c->cabeza); c=c->cola; }}
    // main()
    {_PH}emit("int main(int argc, char** argv) {{");
    {_PH}indent++;
    {_PH}emit("int _g_argc=argc;");
    {_PH}emit("char** _g_argv=argv;");
    {_PH}emit("pool_init(POOL_BLOQUES, TAMANO_BLOQUE);");
    {_PH}emit("principal();");
    {_PH}emit("synapse_esperar_hilos();");
    {_PH}emit("return 0;");
    {_PH}indent--;
    {_PH}emit("}}");
    fclose({_PH}out);
    char cmd[2048];
    char out_exe[1024];
    int slen = (int)strlen(sal);
    if (slen > 2 && sal[slen-2] == '.' && sal[slen-1] == 'c') {{
        memcpy(out_exe, sal, slen - 2);
        out_exe[slen - 2] = 0;
        strcat(out_exe, ".exe");
    }} else {{
        snprintf(out_exe, sizeof(out_exe), "%s.exe", sal);
    }}
    snprintf(cmd, sizeof(cmd), "gcc -O2 -fno-ident -Wl,--no-insert-timestamp \\"%s\\" synapse_rt.o -o \\"%s\\" -lpthread -lm -lws2_32", sal, out_exe);
    int rc = system(cmd);
    if (rc != 0) {{
        fprintf(stderr, "[LINKER ERROR] gcc fallo con codigo %d\\n", rc);
        exit(1);
    }}
    fprintf(stderr, "OK: %s\\n", out_exe);
    return 0;
}}
"""
        H = H.replace(_PH, '_G_')
        for ln in H.strip().split('\n'):
            ctx.lineas.append(ln)

