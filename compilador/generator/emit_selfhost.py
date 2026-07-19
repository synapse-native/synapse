"""
Emisores de auto-hospedaje — generan código C para el tokenizador, parser,
y generador embebidos. Corazón del bootstrap.
Cada función recibe (ctx) siguiendo el patrón Composición + Contexto.
"""

from compilador.ast_nodes import DefinicionFuncion
from .context import GeneratorContext, MAPA_TIPOS_C
from .emit_expressions import emitir_token_defs


def emitir_parsear(ctx: GeneratorContext, nodo: DefinicionFuncion):
    """Genera la función parsear() — parser embebido."""
    emitir_token_defs(ctx)
    gen_tok_c(ctx)
    gen_parse(ctx)
    ctx.write_line("struct Programa parsear(CadenaSegura fuente) {")
    ctx.inc_indent()
    ctx.write_line("_P_ntks = 0; _P_tpos = 0; _P_p_err = 0; _P_nivel_pila = 0;")
    ctx.write_line("int _P_pila_indent_local[64] = {0};")
    ctx.write_line("memcpy(_P_pila_indent, _P_pila_indent_local, sizeof(_P_pila_indent_local));")
    ctx.write_line("_P_tokenizar(fuente.datos, fuente.longitud);")
    ctx.write_line("_P_procesar_indentacion_final();")
    ctx.write_line("struct Programa _prog = _P_programa();")
    ctx.write_line("return _prog;")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")


def emitir_volcar_ast(ctx, nodo):
    """Genera función volcar_ast() — volcado recursivo del AST."""
    ctx.write_line("void _volcar_nodo(struct Nodo* nodo, int nivel) {")
    ctx.inc_indent()
    ctx.write_line("if (!nodo) return;")
    ctx.write_line('for (int _i = 0; _i < nivel; _i++) fprintf(stderr, "  ");')
    ctx.write_line('fprintf(stderr, "%%s\\n", nodo->tipo.longitud > 0 ? nodo->tipo.datos : "?");')
    ctx.write_line("nivel++;")
    for nombre, info in ctx._estructuras.items():
        if nombre in ('Nodo', 'Parser', 'Token', 'ListaNodo', 'ListaParametro'):
            continue
        ctx.write_line(f'if (strcmp(nodo->tipo.datos, "{nombre}") == 0) {{')
        ctx.inc_indent()
        ctx.write_line(f"struct {nombre}* _n = (struct {nombre}*)nodo;")
        for c_nombre, c_tipo in info.get('campos', []):
            if c_tipo in ('entero', 'int'):
                ctx.write_line(
                    f'fprintf(stderr, "%*s%s = %d\\n", '
                    f'nivel*2, "", "{c_nombre}", _n->{c_nombre});'
                )
            elif c_tipo in ('cadena', 'texto'):
                ctx.write_line(
                    f'fprintf(stderr, "%*s%s = %.*s\\n", '
                    f'nivel*2, "", "{c_nombre}", '
                    f'_n->{c_nombre}.longitud, _n->{c_nombre}.datos);'
                )
            else:
                ctx.write_line(f'_volcar_nodo((struct Nodo*)_n->{c_nombre}, nivel);')
        ctx.dec_indent()
        ctx.write_line("return;")
        ctx.write_line("}")
    ctx.write_line("// tipo desconocido")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")
    ctx.write_line("void volcar_ast(struct Nodo* nodo, int nivel) {")
    ctx.inc_indent()
    ctx.write_line("_volcar_nodo(nodo, nivel);")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")


def gen_tok_c(ctx: GeneratorContext):
    """Genera _P_tokenizar() — lexer embebido."""
    P = "_P_"
    ctx.write_line(f"void {P}tokenizar(const char* s, int len) {{")
    ctx.inc_indent()
    ctx.write_line("int li = 1, co = 1, i = 0;")
    ctx.write_line(f"while (i < len && {P}ntks < MAX_TOKS) {{")
    ctx.inc_indent()
    ctx.write_line("char c = s[i];")
    ctx.write_line("if (c==' '||c=='\\t'){i++;co++;continue;}")
    ctx.write_line("if (c=='\\r'){i++;continue;}")
    ctx.write_line("if (c=='\\n'){")
    ctx.inc_indent()
    ctx.write_line("int _nco = 0; i++; li++;")
    ctx.write_line("while(i<len&&(s[i]==' '||s[i]=='\\t')){if(s[i]=='\\t')_nco+=4;else _nco++;i++;}")
    ctx.write_line(f"if({P}ntks>0&&{P}tks[{P}ntks-1].tipo!=T_NL){{{P}tks[{P}ntks].tipo=T_NL;{P}ntks++;}}")
    ctx.write_line(f"if(_nco>{P}pila_indent[{P}nivel_pila]){{{P}nivel_pila++;{P}pila_indent[{P}nivel_pila]=_nco;{P}tks[{P}ntks].tipo=T_INDENT;{P}ntks++;}}")
    ctx.write_line(f"while(_nco<{P}pila_indent[{P}nivel_pila]){{{P}nivel_pila--;{P}tks[{P}ntks].tipo=T_DEDENT;{P}ntks++;}}")
    ctx.write_line("co=_nco+1; continue;")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("if(c=='/'&&i+1<len&&s[i+1]=='/'){while(i<len&&s[i]!='\\n')i++;continue;}")
    ctx.write_line("if(c=='#'&&i+1<len&&s[i+1]==' '){while(i<len&&s[i]!='\\n')i++;continue;}")
    # String literal
    s_str = (
        "if(c=='\\\"'||c=='\\''){char q=c;int st=i;int scol=co;"
        "i++;co++;while(i<len&&s[i]!=q){i++;co++;}"
        "if(i>=len)break;i++;co++;"
        "int vl=(i-st-2)<255?(i-st-2):255;"
        + f"strncpy({P}tks[{P}ntks].val,s+st+1,vl);"
        + f"{P}tks[{P}ntks].val[vl]=0;"
        + f"{P}tks[{P}ntks].tipo=T_STR;"
        + f"{P}tks[{P}ntks].linea=li;"
        + f"{P}tks[{P}ntks].col=scol;"
        + f"{P}ntks++;continue;}}"
    )
    ctx.write_line(s_str)
    # Number
    n_str = (
        "if(c>='0'&&c<='9'){int st=i;int scol=co;"
        "while(i<len&&s[i]>='0'&&s[i]<='9')i++;"
        "if(i<len&&s[i]=='.'){i++;while(i<len&&s[i]>='0'&&s[i]<='9')i++;}"
        "int vl=(i-st)<255?(i-st):255;"
        + f"strncpy({P}tks[{P}ntks].val,s+st,vl);"
        + f"{P}tks[{P}ntks].val[vl]=0;"
        + f"{P}tks[{P}ntks].tipo=T_NUM;"
        + f"{P}tks[{P}ntks].linea=li;"
        + f"{P}tks[{P}ntks].col=scol;"
        + f"{P}ntks++;co+=i-st;continue;}}"
    )
    ctx.write_line(n_str)
    # Identifier
    id_str = (
        "if((c>='a'&&c<='z')||(c>='A'&&c<='Z')||c=='_'){"
        "int st=i;int scol=co;"
        "while(i<len&&((s[i]>='a'&&s[i]<='z')||(s[i]>='A'&&s[i]<='Z')"
        "||(s[i]>='0'&&s[i]<='9')||s[i]=='_'))i++;"
        "int vl=(i-st)<255?(i-st):255;"
        + f"strncpy({P}tks[{P}ntks].val,s+st,vl);"
        + f"{P}tks[{P}ntks].val[vl]=0;"
        + f"{P}tks[{P}ntks].tipo=T_IDENT;"
        + f"{P}tks[{P}ntks].linea=li;"
        + f"{P}tks[{P}ntks].col=scol;"
        + f"{P}ntks++;co+=i-st;continue;}}"
    )
    ctx.write_line(id_str)
    # Multi-char operators
    op_str = (
        "if((c=='-'&&i+1<len&&s[i+1]=='>')||"
        "(c=='='&&i+1<len&&s[i+1]=='=')||"
        "(c=='!'&&i+1<len&&s[i+1]=='=')||"
        "(c=='<'&&i+1<len&&s[i+1]=='=')||"
        "(c=='>'&&i+1<len&&s[i+1]=='=')){"
        "char _m[3]={c,s[i+1],0};"
        + f"strcpy({P}tks[{P}ntks].val,_m);"
        + f"{P}tks[{P}ntks].linea=li;"
        + f"{P}tks[{P}ntks].col=co;"
        + f"i+=2;co+=2;{P}tks[{P}ntks].tipo=T_ARROW;{P}ntks++;continue;}}"
    )
    ctx.write_line(op_str)
    # Single-char operators
    char_tokens = {
        '+': 'T_PLUS', '-': 'T_MINUS', '*': 'T_MUL', '/': 'T_DIV',
        '%': 'T_MOD', '(': 'T_LPAREN', ')': 'T_RPAREN',
        ':': 'T_COLON', ',': 'T_COMMA', '.': 'T_DOT',
        '=': 'T_ASSIGN', '<': 'T_LT', '>': 'T_GT',
        '&': 'T_AMPERSAND',
    }
    first = True
    for ch, token in char_tokens.items():
        prefix = "if" if first else "else if"
        first = False
        ctx.write_line(
            f"{{{prefix}(c=='{ch}'){{{P}tks[{P}ntks].tipo={token};"
            f"{P}tks[{P}ntks].linea=li;{P}tks[{P}ntks].col=co;"
            f"{P}ntks++;i++;co++;continue;}}}}"
        )
    ctx.write_line(
        "else {fprintf(stderr,\"Lexical Error: caracter inesperado"
        " '%c' L%d:%d\\n\",c,li,co);exit(1);}"
    )
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line(f"while({P}nivel_pila>0){{{P}nivel_pila--;{P}tks[{P}ntks].tipo=T_DEDENT;{P}ntks++;}}")
    ctx.write_line(f"{P}tks[{P}ntks].tipo=T_EOF;{P}ntks++;")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")
    ctx.write_line("void _P_procesar_indentacion_final(void) {")
    ctx.inc_indent()
    ctx.write_line(f"while({P}nivel_pila>0){{{P}nivel_pila--;{P}tks[{P}ntks].tipo=T_DEDENT;{P}ntks++;}}")
    ctx.write_line(f"{P}tks[{P}ntks].tipo=T_EOF;{P}ntks++;")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")


def gen_parse(ctx: GeneratorContext):
    """Genera funciones del parser recursivo descendente (_P_programa, etc.)."""
    P = "_P_"
    ctx.write_line("// --- AST Builder Helpers ---")
    ctx.write_line(f"static inline CadenaSegura {P}cs(const char* s) {{")
    ctx.inc_indent()
    ctx.write_line("return (CadenaSegura){.longitud=(int)strlen(s),.datos=strdup(s)};")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")
    ctx.write_line(f"static inline struct ListaNodo* {P}mk_list(struct Nodo* c, struct ListaNodo* sig) {{")
    ctx.inc_indent()
    ctx.write_line("struct ListaNodo* l=(struct ListaNodo*)calloc(1,sizeof(struct ListaNodo));")
    ctx.write_line("l->cabeza=c;l->cola=sig;return l;")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")
    ctx.write_line("// --- Parser Primitives ---")
    ctx.write_line(f"static inline _P_Token* {P}mirar() {{ return &{P}tks[{P}tpos]; }}")
    ctx.write_line(f"static inline void {P}avanzar() {{ {P}tpos++; }}")
    ctx.write_line(f"static inline int {P}posible(int t) {{")
    ctx.inc_indent()
    ctx.write_line(f"if ({P}tks[{P}tpos].tipo == t) {{ {P}tpos++; return 1; }}")
    ctx.write_line("return 0;")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")
    ctx.write_line(f"static inline int {P}esperar(int t) {{")
    ctx.inc_indent()
    ctx.write_line(f"if ({P}tks[{P}tpos].tipo == t) {{ {P}tpos++; return 1; }}")
    ctx.write_line('fprintf(stderr, "Se esperaba token %d, obtuvo %d L:%d:%d\\n", t, _P_tks[_P_tpos].tipo, _P_tks[_P_tpos].linea, _P_tks[_P_tpos].col);')
    ctx.write_line(f"{P}p_err = 1;")
    ctx.write_line("return 0;")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")
    ctx.write_line(f"static inline void {P}sinc_skip() {{")
    ctx.inc_indent()
    ctx.write_line(f"while({P}tpos<{P}ntks&&{P}tks[{P}tpos].tipo!=T_NL&&{P}tks[{P}tpos].tipo!=T_DEDENT&&{P}tks[{P}tpos].tipo!=T_EOF){P}tpos++;")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")
    # Forward declarations
    for fn in ["expr", "logica", "comp", "suma", "term", "una", "prim", "sentencia", "bloque", "programa"]:
        ctx.write_line(f"int _{P}{fn}(void);")
    ctx.write_line("")
    # _P_programa
    ctx.write_line(f"int _{P}programa(void) {{")
    ctx.inc_indent()
    ctx.write_line("struct Programa* n=(struct Programa*)calloc(1,sizeof(struct Programa));")
    ctx.write_line('n->tipo=_P_cs("Programa");')
    ctx.write_line("struct ListaNodo* ultimo=NULL;")
    ctx.write_line("while(1){")
    ctx.inc_indent()
    ctx.write_line(f"if({P}tks[{P}tpos].tipo==T_EOF)break;")
    ctx.write_line(f"int st=_{P}sentencia();")
    ctx.write_line("if(st){")
    ctx.inc_indent()
    ctx.write_line("struct Nodo* sn=(struct Nodo*)st;")
    ctx.write_line("if(!ultimo){n->sentencias=_P_mk_list(sn,NULL);ultimo=n->sentencias;}")
    ctx.write_line("else{ultimo->cola=_P_mk_list(sn,NULL);ultimo=ultimo->cola;}")
    ctx.dec_indent()
    ctx.write_line("}else _P_avanzar();")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("return (int)(intptr_t)n;")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")
    # _P_bloque
    ctx.write_line(f"int _{P}bloque(void) {{")
    ctx.inc_indent()
    ctx.write_line("struct ListaNodo* primero=NULL;struct ListaNodo** ccur=&primero;")
    ctx.write_line(f"while({P}tks[{P}tpos].tipo!=T_DEDENT&&{P}tks[{P}tpos].tipo!=T_EOF){{")
    ctx.inc_indent()
    ctx.write_line(f"int st=_{P}sentencia();if(st){{*ccur=_P_mk_list((struct Nodo*)st,NULL);ccur=&(*ccur)->cola;}}else _P_avanzar();")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("return (int)(intptr_t)primero;")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")
    # _P_sentencia (simplified)
    ctx.write_line(f"int _{P}sentencia(void) {{")
    ctx.inc_indent()
    ctx.write_line(f"_P_Token* t={P}mirar();if(!t||t->tipo==T_EOF||t->tipo==T_DEDENT)return 0;")
    # Funcion
    ctx.write_line("if(t->tipo==T_FUNC){_P_avanzar();")
    ctx.inc_indent()
    ctx.write_line(f"if({P}tks[{P}tpos].tipo!=T_IDENT){{_P_sinc_skip();return 0;}}")
    ctx.write_line(f"char _fn[256];strcpy(_fn,{P}tks[{P}tpos].val);_P_avanzar();_P_esperar(T_LPAREN);")
    ctx.write_line("struct ListaParametro* eparams=NULL;struct ListaParametro** epcur=&eparams;")
    ctx.write_line(f"if({P}tks[{P}tpos].tipo!=T_RPAREN){{while(1){{")
    ctx.write_line(f"char _pn[256];strcpy(_pn,{P}tks[{P}tpos].val);_P_avanzar();_P_esperar(T_COLON);")
    ctx.write_line(f"char _pt[256];strcpy(_pt,{P}tks[{P}tpos].val);_P_avanzar();")
    ctx.write_line("struct Parametro* pp=(struct Parametro*)calloc(1,sizeof(struct Parametro));")
    ctx.write_line('pp->tipo=_P_cs("Parametro");pp->nombre=_P_cs(_pn);pp->tipo_param=_P_cs(_pt);pp->es_transferencia=0;')
    ctx.write_line("*epcur=(struct ListaParametro*)_P_mk_list((struct Nodo*)pp,NULL);epcur=&(*epcur)->cola;")
    ctx.write_line(f"if({P}tks[{P}tpos].tipo!=T_COMMA)break;_P_avanzar();}}}}")
    ctx.write_line("_P_esperar(T_RPAREN);_P_esperar(T_ARROW);")
    ctx.write_line(f"char _rt[256];strcpy(_rt,{P}tks[{P}tpos].val);_P_avanzar();_P_esperar(T_COLON);")
    ctx.write_line("struct DefinicionFuncion* n=(struct DefinicionFuncion*)calloc(1,sizeof(struct DefinicionFuncion));")
    ctx.write_line('n->tipo=_P_cs("DefinicionFuncion");n->nombre=_P_cs(_fn);n->parametros=eparams;n->tipo_retorno=_P_cs(_rt);')
    ctx.write_line(f"if({P}tks[{P}tpos].tipo==T_INDENT){{_P_avanzar();n->cuerpo=(struct ListaNodo*)(intptr_t)_{P}bloque();}}")
    ctx.write_line("return (int)(intptr_t)n;")
    ctx.dec_indent()
    ctx.write_line("}")
    # If
    ctx.write_line("if(t->tipo==T_IF){_P_avanzar();")
    ctx.inc_indent()
    ctx.write_line("struct Nodo* cond=(struct Nodo*)(intptr_t)_P_expr();_P_esperar(T_COLON);")
    ctx.write_line(f"struct ListaNodo* cpo=NULL;if({P}tks[{P}tpos].tipo==T_INDENT){{_P_avanzar();cpo=(struct ListaNodo*)(intptr_t)_{P}bloque();}}")
    ctx.write_line(f"struct ListaNodo* sino=NULL;if({P}tks[{P}tpos].tipo==T_ELSE){{_P_avanzar();_P_esperar(T_COLON);if({P}tks[{P}tpos].tipo==T_INDENT){{_P_avanzar();sino=(struct ListaNodo*)(intptr_t)_{P}bloque();}}}}")
    ctx.write_line("struct SentenciaSi* n=(struct SentenciaSi*)calloc(1,sizeof(struct SentenciaSi));")
    ctx.write_line('n->tipo=_P_cs("SentenciaSi");n->condicion=cond;n->cuerpo=cpo;n->cuerpo_sino=sino;')
    ctx.write_line("return (int)(intptr_t)n;")
    ctx.dec_indent()
    ctx.write_line("}")
    # While
    ctx.write_line("if(t->tipo==T_WHILE){_P_avanzar();")
    ctx.inc_indent()
    ctx.write_line("struct Nodo* cond=(struct Nodo*)(intptr_t)_P_expr();_P_esperar(T_COLON);")
    ctx.write_line(f"struct ListaNodo* cpo=NULL;if({P}tks[{P}tpos].tipo==T_INDENT){{_P_avanzar();cpo=(struct ListaNodo*)(intptr_t)_{P}bloque();}}")
    ctx.write_line("struct SentenciaMientras* n=(struct SentenciaMientras*)calloc(1,sizeof(struct SentenciaMientras));")
    ctx.write_line('n->tipo=_P_cs("SentenciaMientras");n->condicion=cond;n->cuerpo=cpo;')
    ctx.write_line("return (int)(intptr_t)n;")
    ctx.dec_indent()
    ctx.write_line("}")
    # Return, Break, Continue, Import
    ctx.write_line("if(t->tipo==T_RET){_P_avanzar();struct Nodo* expr=_P_expr();struct SentenciaRetornar* n=(struct SentenciaRetornar*)calloc(1,sizeof(struct SentenciaRetornar));n->tipo=_P_cs(\"SentenciaRetornar\");n->expr=expr;return (int)(intptr_t)n;}")
    ctx.write_line("if(t->tipo==T_BREAK){_P_avanzar();struct SentenciaRomper* n=(struct SentenciaRomper*)calloc(1,sizeof(struct SentenciaRomper));n->tipo=_P_cs(\"SentenciaRomper\");return (int)(intptr_t)n;}")
    ctx.write_line("if(t->tipo==T_CONTINUE){_P_avanzar();struct SentenciaSiguiente* n=(struct SentenciaSiguiente*)calloc(1,sizeof(struct SentenciaSiguiente));n->tipo=_P_cs(\"SentenciaSiguiente\");return (int)(intptr_t)n;}")
    ctx.write_line("if(t->tipo==T_IMPORT){_P_avanzar();char _im[256];strcpy(_im,_P_tks[_P_tpos].val);_P_avanzar();struct SentenciaImportar* n=(struct SentenciaImportar*)calloc(1,sizeof(struct SentenciaImportar));n->tipo=_P_cs(\"SentenciaImportar\");n->ruta=_P_cs(_im);return (int)(intptr_t)n;}")
    # Expression statement fallback
    ctx.write_line("int _eidx = _P_expr();if(!_eidx)return 0;struct SentenciaExpr* n=(struct SentenciaExpr*)calloc(1,sizeof(struct SentenciaExpr));n->tipo=_P_cs(\"SentenciaExpr\");n->expr=(struct Nodo*)(intptr_t)_eidx;return (int)(intptr_t)n;")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")
    # Expression parsing (recursive descent)
    for fn_name, child_fn in [
        ("expr", "logica"), ("logica", "comp"), ("comp", "suma"),
        ("suma", "term"), ("term", "una"), ("una", "prim"),
    ]:
        ctx.write_line(f"int _{P}{fn_name}(void) {{")
        ctx.inc_indent()
        ctx.write_line(f"int izq=_{P}{child_fn}();while(1){{")
        ctx.inc_indent()
        ctx.write_line(f"_P_Token* t={P}mirar();if(!t)break;")
        ops = []
        if fn_name == "expr":
            ops = [("T_AND", 100), ("T_OR", 101)]
        elif fn_name == "comp":
            ops = [("T_EQ", 202), ("T_NE", 203), ("T_LT", 201), ("T_GT", 200), ("T_LE", 204), ("T_GE", 205)]
        elif fn_name == "suma":
            ops = [("T_PLUS", 300), ("T_MINUS", 301)]
        elif fn_name == "term":
            ops = [("T_MUL", 400), ("T_DIV", 401), ("T_MOD", 402)]
        if ops:
            for tok, val in ops:
                ctx.write_line(f"if(t->tipo=={tok}){{_P_avanzar();break;}}")
            ctx.write_line("else break;")
            ctx.write_line(f"int der=_{P}{child_fn}();")
            ctx.write_line("struct OpBinaria* n=(struct OpBinaria*)calloc(1,sizeof(struct OpBinaria));")
            ctx.write_line('n->tipo=_P_cs("OpBinaria");n->izquierdo=(struct Nodo*)(intptr_t)izq;n->derecho=(struct Nodo*)(intptr_t)der;')
            ctx.write_line("izq=(int)(intptr_t)n;")
        else:
            ctx.write_line("break;")
        ctx.dec_indent()
        ctx.write_line("}")
        ctx.write_line("return izq;")
        ctx.dec_indent()
        ctx.write_line("}")
        ctx.write_line("")
    # _P_prim
    ctx.write_line(f"int _{P}prim(void) {{")
    ctx.inc_indent()
    ctx.write_line(f"_P_Token* t={P}mirar();if(!t)return 0;")
    ctx.write_line("if(t->tipo==T_NUM){int v=atoi(t->val);_P_avanzar();struct LiteralNumero* n=(struct LiteralNumero*)calloc(1,sizeof(struct LiteralNumero));n->tipo=_P_cs(\"LiteralNumero\");n->valor=v;return (int)(intptr_t)n;}")
    ctx.write_line("if(t->tipo==T_STR){char _sv[256];strcpy(_sv,t->val);_P_avanzar();struct LiteralCadena* n=(struct LiteralCadena*)calloc(1,sizeof(struct LiteralCadena));n->tipo=_P_cs(\"LiteralCadena\");n->valor=_P_cs(_sv);return (int)(intptr_t)n;}")
    ctx.write_line("if(t->tipo==T_IDENT){char _id[256];strcpy(_id,t->val);_P_avanzar();struct Identificador* idn=(struct Identificador*)calloc(1,sizeof(struct Identificador));idn->tipo=_P_cs(\"Identificador\");idn->nombre=_P_cs(_id);t=_P_mirar();if(!t)return (int)(intptr_t)idn;if(t->tipo==T_LPAREN){_P_avanzar();struct LlamadaFuncion* lfn=(struct LlamadaFuncion*)calloc(1,sizeof(struct LlamadaFuncion));lfn->tipo=_P_cs(\"LlamadaFuncion\");lfn->nombre=_P_cs(_id);struct ListaNodo* largs=NULL;struct ListaNodo** lcur=&largs;while(_P_tks[_P_tpos].tipo!=T_RPAREN&&_P_tks[_P_tpos].tipo!=T_EOF){int a=_P_expr();if(a){*lcur=_P_mk_list((struct Nodo*)(intptr_t)a,NULL);lcur=&(*lcur)->cola;}if(_P_tks[_P_tpos].tipo==T_COMMA)_P_avanzar();else break;}_P_esperar(T_RPAREN);lfn->argumentos=largs;return (int)(intptr_t)lfn;}return (int)(intptr_t)idn;}")
    ctx.write_line("if(t->tipo==T_LPAREN){_P_avanzar();int e=_P_expr();_P_esperar(T_RPAREN);return e;}")
    ctx.write_line("return 0;")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")


def emitir_generar(ctx: GeneratorContext, nodo: DefinicionFuncion):
    """Genera la función generar() — AST walker y generador C auto-hospedado."""
    P = "_G_"
    emitir_token_defs(ctx)
    gen_tok_c(ctx)
    gen_parse(ctx)
    ctx.write_line("// --- AST Walker (auto-generado) ---")
    ctx.write_line("int _G_indent = 0;")
    ctx.write_line("FILE* _G_out = NULL;")
    ctx.write_line(f"char {P}vn[1024][64] = {{0}};")
    ctx.write_line(f"int {P}vc = 0;")
    ctx.write_line("")
    # _G_emit
    ctx.write_line(f"void {P}emit(const char* s) {{")
    ctx.inc_indent()
    ctx.write_line("for(int i=0;i<_G_indent;i++) fprintf(_G_out,\"    \");")
    ctx.write_line('fprintf(_G_out,"%s\\n",s);')
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")
    # _G_mt
    ctx.write_line(f"const char* {P}mt(const char* st) {{")
    ctx.inc_indent()
    for syn_type, c_type in [
        ("entero", "int"), ("int", "int"),
        ("decimal", "float"), ("real", "float"),
        ("texto", "CadenaSegura"), ("cadena", "CadenaSegura"),
        ("booleano", "int"), ("logico", "int"),
        ("nulo", "void*"), ("vacio", "void"),
        ("Tensor", "Tensor"), ("tensor", "Tensor"),
        ("Canal", "Canal"), ("canal", "Canal"),
        ("puntero", "void*"),
    ]:
        ctx.write_line(f'if(strcmp(st,"{syn_type}")==0)return "{c_type}";')
    ctx.write_line("return st;")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")
    # _G_cp
    ctx.write_line(f"void {P}cp(char* dst, CadenaSegura src) {{")
    ctx.inc_indent()
    ctx.write_line("int ml = src.longitud < 255 ? src.longitud : 255;")
    ctx.write_line("memcpy(dst, src.datos, ml); dst[ml] = 0;")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")
    # _G_ea
    ctx.write_line(f"void {P}ea(struct Nodo* n, char* b, int bs) {{")
    ctx.inc_indent()
    ctx.write_line("if(!n||!n->tipo.datos){b[0]=0;return;}")
    ctx.write_line("char _nb[256];_G_cp(_nb,n->tipo);")
    ctx.write_line('if(strcmp(_nb,"Identificador")==0){struct Identificador* _id=(struct Identificador*)n;_G_cp(b,_id->nombre);return;}')
    ctx.write_line('if(strcmp(_nb,"LiteralNumero")==0){struct LiteralNumero* _ln=(struct LiteralNumero*)n;snprintf(b,bs,"%d",_ln->valor);return;}')
    ctx.write_line('if(strcmp(_nb,"LiteralCadena")==0){struct LiteralCadena* _lc=(struct LiteralCadena*)n;snprintf(b,bs,"(CadenaSegura){%%d,\\"%%s\\"}",_lc->valor.longitud,_lc->valor.datos);return;}')
    ctx.write_line('if(strcmp(_nb,"OpBinaria")==0){struct OpBinaria* _op=(struct OpBinaria*)n;char _izq[512],_der[512];_G_ea(_op->izquierdo,_izq,512);_G_ea(_op->derecho,_der,512);snprintf(b,bs,"(%s %s %s)",_izq,"+",_der);return;}')
    ctx.write_line('if(strcmp(_nb,"LlamadaFuncion")==0){struct LlamadaFuncion* _lf=(struct LlamadaFuncion*)n;char _fn[256];_G_cp(_fn,_lf->nombre);b[0]=0;struct ListaNodo* _la=_lf->argumentos;while(_la){char _ab[512];_G_ea(_la->cabeza,_ab,512);if(b[0])strcat(b,",");strcat(b,_ab);_la=_la->cola;}snprintf(b,bs,"%s(%s)",_fn,b);return;}')
    ctx.write_line("b[0]=0;")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")
    # _G_v
    ctx.write_line(f"void {P}v(struct Nodo* n) {{")
    ctx.inc_indent()
    ctx.write_line("if(!n)return;char _nb[256];_G_cp(_nb,n->tipo);char b[4096],v[4096],b2[4096];")
    ctx.write_line('if(strcmp(_nb,"DefinicionFuncion")==0){struct DefinicionFuncion* _f=(struct DefinicionFuncion*)n;char _fn[256];_G_cp(_fn,_f->nombre);for(int _fi=0;_fi<_G_vc;_fi++)if(strcmp(_G_vn[_fi],_fn)==0)return;strcpy(_G_vn[_G_vc],_fn);_G_vc++;char _rt[64];strcpy(_rt,_G_mt(_f->tipo_retorno.datos));char _ps[1024]="void";struct ListaParametro* _lp=_f->parametros;if(_lp){_ps[0]=0;while(_lp){struct Parametro* _p=(struct Parametro*)_lp->cabeza;char _pn[256];_G_cp(_pn,_p->nombre);char _pt[256];snprintf(_pt,256,"%s",_G_mt(_p->tipo_param.datos));if(_ps[0])strcat(_ps,",");strcat(_ps,_pt);strcat(_ps," ");strcat(_ps,_pn);_lp=_lp->cola;}}snprintf(b,4096,"%s %s(%s) {",_rt,_fn,_ps);_G_emit(b);_G_indent++;struct ListaNodo* _cuerpo=_f->cuerpo;while(_cuerpo){_G_v(_cuerpo->cabeza);_cuerpo=_cuerpo->cola;}_G_indent--;_G_emit("}");}')
    ctx.write_line('if(strcmp(_nb,"SentenciaSi")==0){struct SentenciaSi* _s=(struct SentenciaSi*)n;char _cd[512];_G_ea(_s->condicion,_cd,512);snprintf(b,4096,"if (%s) {",_cd);_G_emit(b);_G_indent++;struct ListaNodo* _cl=_s->cuerpo;while(_cl){_G_v(_cl->cabeza);_cl=_cl->cola;}_G_indent--;_G_emit("}");if(_s->cuerpo_sino){_G_emit("else {");_G_indent++;struct ListaNodo* _sl=_s->cuerpo_sino;while(_sl){_G_v(_sl->cabeza);_sl=_sl->cola;}_G_indent--;_G_emit("}");}}')
    ctx.write_line('if(strcmp(_nb,"SentenciaExpr")==0){struct SentenciaExpr* _se=(struct SentenciaExpr*)n;_G_ea(_se->expr,b,4096);snprintf(b2,4096,"%s;",b);_G_emit(b2);}')
    ctx.write_line('if(strcmp(_nb,"AsignacionVariable")==0){struct AsignacionVariable* _a=(struct AsignacionVariable*)n;char _an[256];_G_cp(_an,_a->nombre);_G_ea(_a->expresion,b,4096);snprintf(b2,4096,"%s = %s;",_an,b);_G_emit(b2);}')
    ctx.write_line('if(strcmp(_nb,"SentenciaRetornar")==0){struct SentenciaRetornar* _r=(struct SentenciaRetornar*)n;if(_r->expr){_G_ea(_r->expr,b,4096);snprintf(b2,4096,"return %s;",b);_G_emit(b2);}else _G_emit("return;");}')
    ctx.write_line("// Otros tipos omitidos por ahora")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")
    # generar()
    ctx.write_line("int generar(struct Programa programa, CadenaSegura ruta) {")
    ctx.inc_indent()
    ctx.write_line('_G_out = fopen(ruta.datos, "w");')
    ctx.write_line('if (!_G_out) { fprintf(stderr, "Error: No se pudo abrir %s\\n", ruta.datos); return 1; }')
    ctx.write_line('fprintf(_G_out, "#include <stdio.h>\\n");')
    ctx.write_line('fprintf(_G_out, "#include <stdlib.h>\\n");')
    ctx.write_line('fprintf(_G_out, "#include <string.h>\\n");')
    ctx.write_line('fprintf(_G_out, "#include <stdint.h>\\n");')
    ctx.write_line('fprintf(_G_out, "typedef struct { int longitud; const char* datos; } CadenaSegura;\\n");')
    ctx.write_line('fprintf(_G_out, "#define nulo ((void*)0)\\n");')
    ctx.write_line("")
    ctx.write_line("struct ListaNodo* _stmts = programa.sentencias;")
    ctx.write_line("while (_stmts) { _G_v(_stmts->cabeza); _stmts = _stmts->cola; }")
    ctx.write_line("")
    ctx.write_line('fprintf(_G_out, "int main(int argc, char** argv) {\\n");')
    ctx.write_line('fprintf(_G_out, "    (void)argc; (void)argv;\\n");')
    ctx.write_line('fprintf(_G_out, "    fprintf(stderr, \\"Synapse v2.0 -- Auto-generado\\\\n\\");\\n");')
    ctx.write_line('fprintf(_G_out, "    return 0;\\n");')
    ctx.write_line('fprintf(_G_out, "}\\n");')
    ctx.write_line("fclose(_G_out);")
    ctx.write_line('fprintf(stderr, "[OK] Codigo C generado: %s\\n", ruta.datos);')
    ctx.write_line("return 0;")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")
