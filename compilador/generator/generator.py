from compilador.ast_nodes import (
    Nodo, Programa,
    DefinicionFuncion, DefinicionEstructura,
    SentenciaSi, SentenciaMientras, SentenciaPara,
    SentenciaLanzar, SentenciaRecuperar,
    SentenciaRetornar, SentenciaEscuchar,
    SentenciaRomper, SentenciaSiguiente,
    SentenciaExpr, DeclaracionVariable,
    AsignacionVariable, AsignacionCampo, LogLlamada,
    SentenciaDelegar, DeclaracionExport,
    BloqueInseguro, NodoCoincidir,
    ImportarC, DeclaracionExterna, StmtConstante,
    SentenciaEnviarCanal, DeclaracionTipo,
    ExprAsm,
)
from .context import GeneratorContext, _dividir_args_tipo
from .emit_control import visitar_si, visitar_mientras, visitar_para, visitar_coincidir
from .emit_declarations import (
    visitar_funcion, visitar_estructura,
    visitar_declaracion, visitar_asignacion,
    visitar_asignacion_campo, visitar_enviar_canal,
    visitar_import_c, visitar_externa, visitar_constante,
    visitar_retornar, visitar_lanzar, visitar_recuperar, visitar_escuchar,
    visitar_delegar,
    visitar_declaracion_tipo,
    _emitir_typedefs_instancias,
)
from .emit_expressions import (
    expr_a_c, tipo_de_expr, visitar_log,
)
from .emit_contracts import emit_contract_header


def _recolectar_instancias_adt(ctx: GeneratorContext):
    """D-2 (FASE A/A5): monomorfización de ADT genéricos (Opción A del
    Arquitecto, Manual 2 §4.2 L279-280 `tipo Resultado<T, E> = ok(T) | err(E)`).

    Escanea el AST por tipos instanciados `Base<A,B>` (retornos, parámetros,
    declaraciones `let x: Base<A,B>`, campos) y registra en ctx._instancias_adt
    cada instanciación única: (base, args) -> {'nombre_c': struct especializado,
    'campos': [(ctor, tipo_concreto), ...]}. El codegen emite un struct C tipado
    por instanciación (nada de void*) y traducir_tipo_c/constructores/`?`/coincidir
    resuelven contra él.
    """
    from compilador.ast_nodes import (
        DefinicionFuncion, DeclaracionVariable, DefinicionEstructura,
        DeclaracionExterna, DeclaracionExport, BloqueInseguro,
    )

    def _sane(a: str) -> str:
        return ''.join(ch if ch.isalnum() or ch == '_' else '_' for ch in a)

    def _registrar(tipo_syn: str):
        if not tipo_syn or '<' not in tipo_syn or not tipo_syn.endswith('>'):
            return
        base, _, resto = tipo_syn.partition('<')
        if base not in ctx._adt_parametros:
            return
        params = ctx._adt_parametros[base]
        args = tuple(_dividir_args_tipo(resto[:-1]))
        if len(args) != len(params):
            return
        # D-2: registrar PRIMERO las instanciaciones anidadas de los argumentos
        # (`Resultado<Resultado<entero,texto>,texto>` registra antes
        # `Resultado<entero,texto>` para que el campo C del contenedor resuelva
        # contra el struct especializado — cero placeholders, Manual 2 §4.2
        # L279-280). Paridad con el scan nativo (orquestador.syn, cola FIFO
        # con post-orden). El split de args respeta el anidamiento.
        for a in args:
            _registrar(a)
        clave = (base, args)
        if clave in ctx._instancias_adt:
            return

        def _mangle_arg(a: str) -> str:
            # D-2: un arg anidado termina en '>' (Resultado<entero,texto>);
            # _sane lo convierte en '_' final -> artefacto de doble guion bajo.
            return _sane(a[:-1] if a.endswith('>') else a)

        nombre_c = base + '_' + '_'.join(_mangle_arg(a) for a in args)
        campos = []
        for ctor, t_syn in ctx._adt_constructores.get(base, []):
            t_conc = args[params.index(t_syn)] if t_syn in params else t_syn
            campos.append((ctor, t_conc))
        ctx._instancias_adt[clave] = {'nombre_c': nombre_c, 'campos': campos}

    def _walk(nodo):
        if isinstance(nodo, DefinicionFuncion):
            _registrar(nodo.tipo_retorno)
            for p in nodo.parametros:
                _registrar(p.tipo)
            if getattr(nodo, 'cuerpo', None):
                for s in nodo.cuerpo:
                    _walk(s)
        elif isinstance(nodo, DeclaracionVariable):
            _registrar(nodo.tipo)
            if nodo.expresion:
                _walk(nodo.expresion)
        elif isinstance(nodo, DefinicionEstructura):
            for c in nodo.campos:
                _registrar(c.tipo)
        elif isinstance(nodo, DeclaracionExterna):
            _registrar(nodo.tipo_retorno)
            for p in nodo.parametros:
                _registrar(p.tipo)
        elif isinstance(nodo, DeclaracionExport):
            if nodo.funcion is not None:
                _walk(nodo.funcion)
        else:
            for attr in ('cuerpo', 'cuerpo_sino', 'sentencias', 'argumentos',
                         'expresion', 'objeto', 'condicion', 'accion_critica',
                         'plan_b', 'inicializacion', 'incremento', 'casos',
                         'valor', 'canal'):
                hijo = getattr(nodo, attr, None)
                if hijo is None:
                    continue
                if isinstance(hijo, list):
                    for h in hijo:
                        if hasattr(h, '__dict__'):
                            _walk(h)
                elif hasattr(hijo, '__dict__'):
                    _walk(hijo)

    for s in ctx.programa.sentencias:
        _walk(s)

    # R28: fixpoint — derivar instancias de ADT desde ctors en EXPRESIONES
    # (`let r = ok(ok(42))` sin anotacion y `r = ok(ok(42))` implicita).
    # El scan anterior solo registraba instancias nombradas en firmas/let
    # anotados; un ctor puro en una expresion quedaba sin registrar -> el
    # let sin anotacion caia a int64_t/base y el C quedaba invalido.
    # Convencion R20/R25: los parametros no acotados del ctor (E en
    # Resultado<T,E>) se rellenan con la PRIMERA instancia registrada del
    # base; el arg 0 es concreto (literal o ctor anidado recursivo).
    from compilador.ast_nodes import (
        LlamadaFuncion, LiteralNumero, LiteralDecimal, LiteralCadena,
        LiteralNulo, BloqueInseguro,
    )

    def _tipo_literal_syn(n):
        if isinstance(n, LiteralNumero):
            return 'entero'
        if isinstance(n, LiteralDecimal):
            return 'decimal'
        if isinstance(n, LiteralCadena):
            return 'texto'
        if isinstance(n, LiteralNulo):
            return 'puntero'
        return None

    def _resolver_ctor_syn(n, depth=0):
        """Tipo Synapse de una cadena de ctors (ok(ok(42)) ->
        Resultado<Resultado<entero,texto>,texto>) o None si no resoluble."""
        if depth > 8 or not isinstance(n, LlamadaFuncion):
            return None
        nombre = n.nombre
        if nombre not in ctx._constructores_adt:
            return None
        base, _tag, _tipo_syn = ctx._constructores_adt[nombre]
        if base not in ctx._adt_parametros:
            return None
        params = ctx._adt_parametros[base]
        if not params:
            return base
        if not getattr(n, 'argumentos', None):
            return None
        arg0 = n.argumentos[0]
        arg_syn = _tipo_literal_syn(arg0)
        if arg_syn is None:
            arg_syn = _resolver_ctor_syn(arg0, depth + 1)
        if arg_syn is None:
            return None
        resto = None
        for (_b, args), _inst in ctx._instancias_adt.items():
            if _b == base:
                resto = list(args)[1:len(params)]
                break
        if resto is None:
            return None
        args_syn = [arg_syn] + resto
        if len(args_syn) != len(params):
            return None
        # sin espacios: el AST escribe Resultado<A,B> sin espacio y el mangle
        # C (nombre_c) no los tolera (doble guion bajo)
        return f"{base}<{','.join(args_syn)}>"

    def _scan_expr_ctors(stmts, out):
        for st in stmts:
            if isinstance(st, (DeclaracionVariable, AsignacionVariable)):
                expr = getattr(st, 'expresion', None)
                if expr is not None:
                    t = _resolver_ctor_syn(expr)
                    if t:
                        out.append(t)
            if isinstance(st, BloqueInseguro):
                _scan_expr_ctors(getattr(st, 'cuerpo', []), out)
            elif hasattr(st, 'cuerpo') and isinstance(getattr(st, 'cuerpo'), list):
                _scan_expr_ctors(getattr(st, 'cuerpo'), out)
            if hasattr(st, 'cuerpo_sino') and getattr(st, 'cuerpo_sino'):
                _scan_expr_ctors(getattr(st, 'cuerpo_sino'), out)

    for _paso in range(4):
        _nuevos = []
        for _s in ctx.programa.sentencias:
            if isinstance(_s, DefinicionFuncion) and getattr(_s, 'cuerpo', None):
                _scan_expr_ctors(_s.cuerpo, _nuevos)
        _antes = len(ctx._instancias_adt)
        for _t in _nuevos:
            _registrar(_t)
        if len(ctx._instancias_adt) == _antes:
            break


def _preprocess_lanzar(ctx: GeneratorContext):
    """Pre-scan: recorre el AST en busca de SentenciaLanzar con LlamadaFuncion y args,
    pre-poblando _deferred_typedefs y _deferred_wrap_decls usando el MISMO contador
    que usara visitar_lanzar durante la emision.

    Construye un mapa de variables local al escanear cuerpos de funcion,
    para resolver tipos correctamente (no hardcodear 'int').
    """
    from compilador.ast_nodes import (
        SentenciaLanzar, LlamadaFuncion,
        ArgumentoTransferido, Identificador,
        DeclaracionVariable, AsignacionVariable, BloqueInseguro,
    )

    def _col_vars_local(nodo):
        """Recolecta declaraciones/asignaciones en un ambito para inferir tipos."""
        local_vars = {}
        def _scan_local(stmts):
            for st in stmts:
                if isinstance(st, DeclaracionVariable):
                    if st.expresion:
                        t_syn = tipo_de_expr(ctx, st.expresion)
                        local_vars[st.nombre] = t_syn
                    elif st.tipo:
                        local_vars[st.nombre] = st.tipo
                elif isinstance(st, AsignacionVariable):
                    if st.nombre not in local_vars:
                        t_syn = tipo_de_expr(ctx, st.expresion)
                        local_vars[st.nombre] = t_syn
                if isinstance(st, BloqueInseguro):
                    _scan_local(st.cuerpo)
                elif hasattr(st, 'cuerpo') and isinstance(getattr(st, 'cuerpo'), list):
                    _scan_local(st.cuerpo)
                if hasattr(st, 'cuerpo_sino') and getattr(st, 'cuerpo_sino'):
                    _scan_local(st.cuerpo_sino)
        _scan_local(nodo)
        return local_vars

    def _scan_node(nodo, local_vars=None):
        if isinstance(nodo, SentenciaLanzar):
            # F4.4: el contador avanza para TODO lanzar (paridad estricta con
            # visitar_lanzar, que hace += 1 incondicional); solo los que llevan
            # argumentos crean wrapper (_wrap_N/_args_N_t). Antes solo se
            # contaban los de args: un programa mixto (args + sin-args)
            # desalineaba los nombres (latente pre-F4.4, destapado al probar
            # el probe mixto).
            ctx._contador_thread += 1
            if isinstance(nodo.llamada, LlamadaFuncion):
                args = nodo.llamada.argumentos
                if args:
                    tid = ctx._contador_thread
                    arg_type_names = []
                    for i, arg in enumerate(args):
                        if isinstance(arg, ArgumentoTransferido) and isinstance(arg.expr, Identificador):
                            var_name = arg.expr.nombre
                            # Try local_vars first, then ctx._variables, fallback void*
                            if local_vars and var_name in local_vars:
                                arg_t = local_vars[var_name]
                            else:
                                arg_t = ctx._variables.get(var_name, 'void*')
                            arg_type_names.append(ctx.traducir_tipo_c(arg_t))
                        else:
                            # For non-transfer args: try local_vars + Identificador lookup
                            if isinstance(arg, Identificador) and local_vars and arg.nombre in local_vars:
                                arg_t = local_vars[arg.nombre]
                            elif isinstance(arg, Identificador) and arg.nombre in ctx._variables:
                                arg_t = ctx._variables[arg.nombre]
                            else:
                                arg_t = tipo_de_expr(ctx, arg)
                            arg_type_names.append(ctx.traducir_tipo_c(arg_t))

                    args_type_name = f"_args_{tid}_t"
                    wrapper_name = f"_wrap_{tid}"

                    fields_str = " ".join(f"{tn} v{i};" for i, tn in enumerate(arg_type_names))
                    td_line = f"typedef struct {{ {fields_str} }} {args_type_name};"
                    if td_line not in ctx._emitted_typedefs:
                        ctx._deferred_typedefs.append(td_line)
                        ctx._emitted_typedefs.add(td_line)
                    wd_line = f"static void {wrapper_name}(void* arg);"
                    if wd_line not in ctx._emitted_wrap_decls:
                        ctx._deferred_wrap_decls.append(wd_line)
                        ctx._emitted_wrap_decls.add(wd_line)
        if hasattr(nodo, 'cuerpo') and isinstance(getattr(nodo, 'cuerpo'), list):
            # Collect variable types from this block to resolve lanzar argument types
            child_vars = _col_vars_local(nodo.cuerpo)
            # Incluir parametros de funcion (DefinicionFuncion.parametros)
            if hasattr(nodo, 'parametros'):
                for p in nodo.parametros:
                    if p.nombre not in child_vars:
                        child_vars[p.nombre] = p.tipo
            merged = {**(local_vars or {}), **child_vars}
            for s in nodo.cuerpo:
                _scan_node(s, merged)
        if hasattr(nodo, 'cuerpo_sino') and getattr(nodo, 'cuerpo_sino'):
            for s in nodo.cuerpo_sino:
                _scan_node(s, local_vars)

    # F4.4: el pre-scan recorre en el MISMO orden que la emision
    # (_emit_cuerpos: no-funciones en parse order + funciones alfabeticas,
    # patron _contar_escuchar_emision) para que el contador coincida.
    for s in ctx.programa.sentencias:
        if isinstance(s, DefinicionFuncion):
            continue
        _scan_node(s)
    for s in sorted(
        [s for s in ctx.programa.sentencias if isinstance(s, DefinicionFuncion)],
        key=lambda f: f.nombre
    ):
        _scan_node(s)


def _contar_escuchar_emision(
        ctx: GeneratorContext, scope_names: set[str] | None = None) -> int:
    """F3-7: cuenta SentenciaEscuchar en el MISMO orden en que visitar() los
    visitará durante _emit_cuerpos (no-funciones en parse order + funciones
    alfabéticas, recorriendo cuerpos anidados). Los externs de los listeners
    se numeran _listener_1..N y _contador_listener los incrementa en ese mismo
    orden, por lo que el conteo debe replicarlo para que los nombres coincidan."""
    total = [0]

    def _walk(nodo):
        if isinstance(nodo, SentenciaEscuchar):
            total[0] += 1
        for attr in ('cuerpo', 'cuerpo_sino', 'sentencias', 'argumentos',
                     'expresion', 'objeto', 'condicion', 'accion_critica',
                     'plan_b', 'inicializacion', 'incremento', 'casos',
                     'valor', 'canal', 'funcion'):
            hijo = getattr(nodo, attr, None)
            if hijo is None:
                continue
            if isinstance(hijo, list):
                for h in hijo:
                    if hasattr(h, '__dict__'):
                        _walk(h)
            elif hasattr(hijo, '__dict__'):
                _walk(hijo)

    funciones = sorted(
        [s for s in ctx.programa.sentencias if isinstance(s, DefinicionFuncion)],
        key=lambda f: f.nombre
    )
    if scope_names is not None:
        funciones = [f for f in funciones if f.nombre in scope_names]
    for s in ctx.programa.sentencias:
        if isinstance(s, DefinicionFuncion):
            continue
        _walk(s)
    for f in funciones:
        _walk(f)
    return total[0]


def visitar(ctx: GeneratorContext, nodo: Nodo):
    _ejecutables = (
        SentenciaSi, SentenciaLanzar, SentenciaRecuperar,
        SentenciaRetornar, SentenciaEscuchar, SentenciaMientras,
        SentenciaRomper, SentenciaSiguiente, SentenciaExpr,
        AsignacionVariable, LogLlamada, AsignacionCampo,
        BloqueInseguro,
    )
    if isinstance(nodo, _ejecutables) and not ctx._in_function_scope:
        raise SyntaxError(
            f"Código ejecutable fuera de ámbito global "
            f"(linea {getattr(nodo, 'linea', '?')})"
        )

    if isinstance(nodo, DefinicionFuncion):
        if ctx._in_function_scope:
            # Hoist nested function to file scope (clang no soporta nested functions)
            _saved = {
                'vars': ctx._variables,
                'tensor': ctx._tensor_vars,
                'canal': ctx._canal_vars,
                'canal_cerradas': ctx._canal_vars_cerradas,
                'canal_conc': ctx._canal_vars_concurrencia,
                'strings': ctx._strings_heap,
                'consumed': ctx._consumed_vars,
                'in_scope': ctx._in_function_scope,
                'ret_type': ctx._current_func_return_type,
            }
            ctx._in_function_scope = False
            visitar_funcion(ctx, nodo)
            ctx._variables = _saved['vars']
            ctx._tensor_vars = _saved['tensor']
            ctx._canal_vars = _saved['canal']
            ctx._canal_vars_cerradas = _saved['canal_cerradas']
            ctx._canal_vars_concurrencia = _saved['canal_conc']
            ctx._strings_heap = _saved['strings']
            ctx._consumed_vars = _saved['consumed']
            ctx._in_function_scope = _saved['in_scope']
            ctx._current_func_return_type = _saved['ret_type']
        else:
            visitar_funcion(ctx, nodo)
    elif isinstance(nodo, SentenciaSi):
        visitar_si(ctx, nodo)
    elif isinstance(nodo, SentenciaLanzar):
        visitar_lanzar(ctx, nodo)
    elif isinstance(nodo, SentenciaRecuperar):
        visitar_recuperar(ctx, nodo)
    elif isinstance(nodo, SentenciaRetornar):
        visitar_retornar(ctx, nodo)
    elif isinstance(nodo, SentenciaEscuchar):
        visitar_escuchar(ctx, nodo)
    elif isinstance(nodo, SentenciaRomper):
        ctx.write_line("break;")
    elif isinstance(nodo, SentenciaSiguiente):
        ctx.write_line("continue;")
    elif isinstance(nodo, SentenciaMientras):
        visitar_mientras(ctx, nodo)
    elif isinstance(nodo, SentenciaPara):
        visitar_para(ctx, nodo)
    elif isinstance(nodo, BloqueInseguro):
        ctx.write_line("{ /* unsafe */")
        ctx.inc_indent()
        ctx.push_scope()
        for s in nodo.cuerpo:
            visitar(ctx, s)
        ctx.pop_scope()
        ctx.dec_indent()
        ctx.write_line("}")
    elif isinstance(nodo, SentenciaExpr):
        val = expr_a_c(ctx, nodo.expr)
        if isinstance(nodo.expr, ExprAsm):
            if nodo.expr.expr is not None:
                expr_c = expr_a_c(ctx, nodo.expr.expr)
                ctx.write_line(f"{{ CadenaSegura _asm_expr = {expr_c}; system(_asm_expr.datos); free(_asm_expr.datos); }}")
            else:
                trimmed = val.rstrip()
                needs_semi = True
                if not trimmed:
                    needs_semi = False
                elif trimmed.startswith('#'):
                    needs_semi = False
                elif trimmed.endswith(';'):
                    needs_semi = False
                elif trimmed.endswith('{'):
                    needs_semi = False
                elif trimmed.endswith('}'):
                    last_brace = trimmed.rfind('}')
                    pre_brace = trimmed[:last_brace].rstrip()
                    if pre_brace.endswith(';'):
                        needs_semi = False
                    else:
                        inner_open = trimmed.rfind('{', 0, last_brace)
                        if inner_open < 0:
                            needs_semi = False
                if needs_semi:
                    val += ';'
                val = val.replace('\n', '\\n')
                ctx.write_line(val)
        else:
            val += ';'
            ctx.write_line(val)
    elif isinstance(nodo, DeclaracionVariable):
        visitar_declaracion(ctx, nodo)
    elif isinstance(nodo, AsignacionVariable):
        visitar_asignacion(ctx, nodo)
    elif isinstance(nodo, SentenciaDelegar):
        visitar_delegar(ctx, nodo)
    elif isinstance(nodo, DeclaracionExport):
        if nodo.funcion is not None:
            visitar(ctx, nodo.funcion)
    elif isinstance(nodo, LogLlamada):
        visitar_log(ctx, nodo)
    elif isinstance(nodo, AsignacionCampo):
        visitar_asignacion_campo(ctx, nodo)
    elif isinstance(nodo, SentenciaEnviarCanal):
        visitar_enviar_canal(ctx, nodo)
    elif isinstance(nodo, DefinicionEstructura):
        pass
    elif isinstance(nodo, DeclaracionTipo):
        # F1.2: el typedef se emite en la sección dedicada de GeneradorC.generar()
        # (tras las estructuras, antes de prototipos), no aquí.
        pass
    elif isinstance(nodo, ImportarC):
        visitar_import_c(ctx, nodo)
    elif isinstance(nodo, DeclaracionExterna):
        visitar_externa(ctx, nodo)
    elif isinstance(nodo, StmtConstante):
        visitar_constante(ctx, nodo)
    elif isinstance(nodo, NodoCoincidir):
        visitar_coincidir(ctx, nodo)


def _emitir_token_defines(ctx: GeneratorContext):
    """Emite #define T_* desde TokenID enum (Manual 2 §2.3).

    Fuente de verdad = el programa compilado: si el AST declara constantes
    T_* propias (compilador auto-hospedado, p.ej. T_FIN = 57 en lexer.syn),
    se usan ESOS valores; el enum Python (EOF=59) queda como fallback para
    programas que no las declaran. Esto elimina de raiz la discrepancia
    T_FIN (57 vs 59) en la compilacion modular.
    """
    from compilador.ast_nodes import TokenID, StmtConstante
    # AUDITORIA F1 (H23): claves = nombres actuales del enum TokenID (renombrados
    # al Manual 2 §3); valores = constantes T_* del compilador auto-hospedado
    # (nucleo/tokens.syn, renombradas T_SI/T_SINO). Incluye los 14 TokenID nuevos (H22).
    _T_MAP = {
        'SI':'T_SI','SINO':'T_SINO','FUNCION':'T_FUNCION','RETORNAR':'T_RETORNAR',
        'LANZAR':'T_LANZAR','RECUPERAR':'T_RECUPERAR','ESCUCHAR':'T_ESCUCHAR',
        'MIENTRAS':'T_MIENTRAS','IMPORTAR':'T_IMPORTAR','ESTRUCTURA':'T_ESTRUCTURA',
        'ROMPER':'T_ROMPER','SIGUIENTE':'T_SIGUIENTE','AND':'T_Y','OR':'T_O',
        'NOT':'T_NO','VERDADERO':'T_VERDADERO','FALSO':'T_FALSO',
        'IDENTIFIER':'T_IDENTIFICADOR','NUMBER':'T_NUMERO','FLOAT':'T_FLOTANTE',
        'STRING':'T_CADENA','GREATER':'T_MAYOR','LESS':'T_MENOR',
        'EQUALS':'T_IGUAL','NOT_EQUALS':'T_DISTINTO','LESS_EQUALS':'T_MENOR_IGUAL',
        'GREATER_EQUALS':'T_MAYOR_IGUAL','ASSIGN':'T_ASIGNAR','PLUS':'T_MAS',
        'MINUS':'T_MENOS','STAR':'T_POR','SLASH':'T_DIV','MOD':'T_MOD',
        'ARROW':'T_FLECHA','COINCIDIR':'T_COINCIDIR','ARROW_RIGHT':'T_FLECHA_DER',
        'LPAREN':'T_PAREN_IZQ','RPAREN':'T_PAREN_DER','COLON':'T_DOSPUNTOS',
        'COMMA':'T_COMA','NEWLINE':'T_NUEVALINEA','INDENT':'T_INDENTAR',
        'DEDENT':'T_DESINDENTAR','AMPERSAND':'T_AMPERSAND','INSEGURO':'T_INSEGURO',
        'IMPORTAR_C':'T_IMPORTAR_C','EXTERNO':'T_EXTERNO','ARROW_LEFT':'T_FLECHA_IZQ',
        'REQUIERE':'T_REQUIERE','GARANTIZA':'T_GARANTIZA','CANAL':'T_CANAL',
        'ASM':'T_ASM','CONSTANTE':'T_CONSTANTE','SEMICOLON':'T_PUNTOCOMA',
        'PARA':'T_PARA','LBRACKET':'T_CORCH_IZQ','RBRACKET':'T_CORCH_DER',
        'EOF':'T_FIN','DOT':'T_PUNTO',
        # H22: 14 TokenID del Manual 2 §3 (activación de keywords en el lexer
        # auto-hospedado pendiente de soporte de parser — ver deuda D-F1).
        'LET':'T_LET','TIPO':'T_TIPO','TENSOR':'T_TENSOR','NULO':'T_NULO',
        'OK':'T_OK','ERR':'T_ERR','ALGUN':'T_ALGUN','NINGUNO':'T_NINGUNO',
        'MODULO':'T_MODULO','DELEGAR':'T_DELEGAR','EXPORT':'T_EXPORT',
        'RC':'T_RC','ARC':'T_ARC','DEBIL':'T_DEBIL',
        'INTERROGACION':'T_INTERROGACION',  # D-6: operador '?' postfijo
    }
    # Valores T_* declarados en el propio programa (fuente de verdad = codigo)
    ast_vals = {}
    for _s in ctx.programa.sentencias:
        if isinstance(_s, StmtConstante) and _s.nombre.startswith('T_'):
            _v = getattr(_s.valor, 'valor', None)
            if isinstance(_v, int):
                ast_vals[_s.nombre] = _v
    ctx.write_line("// --- Token ID constants (Manual 2 §2.3) ---")
    for name in TokenID._member_names_:
        cname = _T_MAP.get(name, f'T_{name}')
        val = ast_vals.get(cname, TokenID[name].value)
        # Usar #ifndef guard para evitar redefinicion en unity file
        ctx.write_line(f"#ifndef {cname}")
        ctx.write_line(f"#define {cname} ({val})")
        ctx.write_line(f"#endif")
    ctx.write_line("")


def _emitir_nodo_defines(ctx: GeneratorContext):
    """Emite #define NODO_* constantes para tipos de nodo AST."""
    NODOS = [
        ("NODO_PROGRAMA",1),("NODO_FUNCION",2),("NODO_SI",3),
        ("NODO_MIENTRAS",4),("NODO_RETORNAR",5),("NODO_EXPR",6),
        ("NODO_ASIGNACION",7),("NODO_IDENTIFICADOR",8),("NODO_NUMERO",9),
        ("NODO_DECIMAL",10),("NODO_CADENA_LIT",11),("NODO_BINARIA",12),
        ("NODO_UNARIA",13),("NODO_LLAMADA",14),("NODO_PARAMETRO",15),
        ("NODO_ESTRUCTURA",16),("NODO_IMPORTAR",17),("NODO_LANZAR",18),
        ("NODO_ESCUCHAR",19),("NODO_ROMPER",20),("NODO_SIGUIENTE",21),
        ("NODO_BOOLEANO",22),("NODO_CONSTANTE",23),("NODO_INSEGURO",24),
        ("NODO_IMPORTAR_C",25),("NODO_EXTERNO",26),("NODO_RECUPERAR",27),
        ("NODO_TENSOR",28),("NODO_INDICE",29),("NODO_TRANSFERIDO",30),
        ("NODO_ACCESO_CAMPO",31),("NODO_ASIGNACION_CAMPO",32),("NODO_PARRAFO",33),
        ("NODO_DECLARACION",34),("NODO_LOG",35),("NODO_PUNTERO",36),
        ("NODO_DEREF",37),("NODO_COINCIDIR",38),("NODO_CASO",39),
        ("NODO_ASM",40),("NODO_CANAL_CREAR",41),("NODO_ENVIAR_CANAL",42),
        ("NODO_RECIBIR_CANAL",43),("NODO_VACIO",44),("NODO_PARA",45),
        ("NODO_CONTRATO",46),
        ("NODO_NULO",47),("NODO_LET",48),("NODO_DELEGAR",49),
        ("NODO_EXPORT",50),("NODO_DECLARACION_TIPO",51),("NODO_CONSTRUCTOR",52),
        ("NODO_PROPAGAR",53),  # D-6: operador '?' postfijo (Manual 3 §7)
    ]
    ctx.write_line("// --- Nodo type constants (AST node types) ---")
    for name, val in NODOS:
        # Usar #ifndef guard para evitar redefinicion
        ctx.write_line(f"#ifndef {name}")
        ctx.write_line(f"#define {name} ({val})")
        ctx.write_line(f"#endif")
    ctx.write_line("")


def _emitir_error_defines(ctx: GeneratorContext):
    """Emite #define ERR_* desde ErrorCodes enum + extras de nucleo/diagnostics.syn."""
    from compilador.diagnostics import ErrorCodes
    ctx.write_line("// --- Error code constants (Manual 3 §3.5) ---")
    for name in ErrorCodes._member_names_:
        val = ErrorCodes[name].value
        # Usar #ifndef guard para evitar redefinicion
        ctx.write_line(f"#ifndef {name}")
        ctx.write_line(f"#define {name} ({val})")
        ctx.write_line(f"#endif")
    # Extras from self-hosted diagnostics.syn (not in Python ErrorCodes)
    for extra_name, extra_val in [
        ("ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED", 33),
        ("ERR_MEM_LIFETIME_MISMATCH", 34),
        ("ERR_MEM_LIFETIME_CYCLE", 35),
    ]:
        ctx.write_line(f"#ifndef {extra_name}")
        ctx.write_line(f"#define {extra_name} ({extra_val})")
        ctx.write_line(f"#endif")
    ctx.write_line("")


def _emitir_constantes_programa(ctx: GeneratorContext):
    """Emite #define para constantes del programa (StmtConstante) que no sean
    T_*/NODO_*/ERR_* (ya emitidas por sus emisores dedicados), p.ej.
    IDIOMA_ES/EN/FR/PT del lexer nativo. Con guards #ifndef para que los
    modulos modulares compartan las constantes sin redefinicion.
    """
    ctx.write_line("// --- Constantes del programa (fuente de verdad = codigo) ---")
    for _s in ctx.programa.sentencias:
        if not isinstance(_s, StmtConstante):
            continue
        _nombre = _s.nombre
        if _nombre.startswith('T_') or _nombre.startswith('NODO_') or _nombre.startswith('ERR_'):
            continue
        _v = getattr(_s.valor, 'valor', None)
        if not isinstance(_v, int):
            continue
        ctx.write_line(f"#ifndef {_nombre}")
        ctx.write_line(f"#define {_nombre} ({_v})")
        ctx.write_line(f"#endif")
    ctx.write_line("")


def _emitir_encabezado(ctx: GeneratorContext):
    ctx.write_line("// salida_metal.c - Generado por Synapse Compilador")
    ctx.write_line("// Lenguaje: Synapse v1.0 (#lang: es)")

    # Suppress known-safe warnings from generated code
    ctx.write_line("#pragma GCC diagnostic ignored \"-Wint-to-pointer-cast\"")
    ctx.write_line("#pragma GCC diagnostic ignored \"-Wdiscarded-qualifiers\"")
    ctx.write_line("")

    if not ctx.is_no_std():
        ctx.write_line("#include <stdio.h>")
        ctx.write_line("#include <stdlib.h>")
        ctx.write_line("#include <stdint.h>")
        ctx.write_line("#include <stdbool.h>")
        ctx.write_line("#include <pthread.h>")
        ctx.write_line("#include <string.h>")
        ctx.write_line("#include <assert.h>")
        # F3-15: escaneo de runtime/core/ en generar_etapa (sin hardcoding) —
        # _findfirst (Windows) / opendir (POSIX), guardados por plataforma.
        ctx.write_line("#ifdef _WIN32")
        ctx.write_line("#include <io.h>")
        ctx.write_line("#else")
        ctx.write_line("#include <dirent.h>")
        ctx.write_line("#endif")
    else:
        ctx.write_line("#include <stdint.h>")
        ctx.write_line("#include <stddef.h>")
    ctx.write_line("")
    ctx.write_line(
        "typedef struct { int longitud; const char* datos; } CadenaSegura;"
    )
    ctx.write_line("")
    # A2.4 (paridad con synapse_rt_types.h:14 / generator.c:2501): el runtime
    # de lifetimes (emit_declarations.py:430) accede `t.es_mapeado`; el typedef
    # emitido en n.h/synapse_unity.c debe incluirlo o el E2E S1 falla en gcc
    # con "no member named es_mapeado" (deuda previamente skip en test_a23).
    ctx.write_line(
        "typedef struct { uint32_t filas; uint32_t columnas; "
        "float* datos; int es_mapeado; } Tensor;"
    )
    ctx.write_line("")
    if not ctx.is_no_std():
        ctx.write_line(
            "typedef struct { FILE* stream; int es_valido; "
            "int es_virtual; const char* virtual_data; "
            "int virtual_len; } Canal;"
        )
        ctx.write_line("")

    ctx.write_line("#define nulo ((void*)0)")
    ctx.write_line("#define verdadero 1")
    ctx.write_line("#define falso 0")
    ctx.write_line("")
    ctx.write_line("// --- OO AST node types ---")
    for t in ['Token', 'Nodo', 'ListaNodo', 'Programa',
              'Identificador', 'LiteralNumero', 'LiteralCadena',
              'OpBinaria', 'OpUnaria', 'LlamadaFuncion',
              'ExprAccesoCampo', 'AsignacionVariable', 'AsignacionCampo',
              'SentenciaSi', 'SentenciaMientras', 'SentenciaRetornar',
              'SentenciaExpr', 'LogLlamada',
              'Parametro', 'ListaParametro',
              'DefinicionFuncion', 'DefinicionEstructura',
              'SentenciaRomper', 'SentenciaSiguiente',
              'SentenciaLanzar', 'SentenciaRecuperar', 'SentenciaEscuchar',
              'ExprTensor', 'ExprIndice', 'ArgumentoTransferido',
              'SentenciaImportar',
              'ImportarC', 'DeclaracionExterna', 'DeclaracionVariable', 'BloqueInseguro',
              'ExprObtenerDireccion', 'ExprDereferencia']:
        ctx.write_line(f"struct {t};")
    ctx.write_line("")

    typedefs = [
        ("Token", "{ int tipo; CadenaSegura lexema; int linea; int columna; }"),
        ("Nodo", "{ CadenaSegura tipo; }"),
        ("ListaNodo", "{ struct Nodo* cabeza; struct ListaNodo* cola; }"),
        ("Programa", "{ CadenaSegura tipo; struct ListaNodo* sentencias; }"),
    ]
    for name, body in typedefs:
        ctx.write_line(f"typedef struct {name} {body} {name};")
    ctx.write_line("")

    ctx.write_line("#define POOL_BLOQUES 64")
    ctx.write_line("#define TAMANO_BLOQUE 4096")
    ctx.write_line("")
    ctx.write_line("#define _GEN_TMP_SIZE (4096)")
    ctx.write_line("#include \"librerias/embedded_libs.h\"")
    ctx.write_line("")
    # Emit T_*, NODO_*, ERR_*, y constantes del programa para compilacion modular
    _emitir_token_defines(ctx)
    _emitir_nodo_defines(ctx)
    _emitir_error_defines(ctx)
    _emitir_constantes_programa(ctx)
    # NOTA: _syn_* y _toml_* externs ya estan en #include "librerias/embedded_libs.h"
    ctx.write_line("extern char _gen_tmp_buf[4096];")
    ctx.write_line("")
    ctx.write_line("extern char _G_emit_buf[1048576];")
    ctx.write_line("extern int _G_emit_pos;")
    ctx.write_line("extern FILE* _G_fp;")
    ctx.write_line("")
    ctx.write_line("// ME-B4: nombres de estructuras definidas (para constructores en C nativo)")
    ctx.write_line("extern char _G_native_structs[256][64];")
    ctx.write_line("extern int _G_native_structs_count;")
    ctx.write_line("extern int _G_native_es_estructura(const char* n);")
    ctx.write_line("")
    # F3-13: campos de struct con tipo Synapse (paridad orquestador.syn — el
    # generador nativo consulta el tipo del campo para detectar texto).
    ctx.write_line("extern char _G_native_struct_campos[256][64][64];")
    ctx.write_line("extern char _G_native_struct_campos_tipo[256][64][64];")
    ctx.write_line("extern int _G_native_struct_campos_count[256];")
    ctx.write_line("extern int _G_native_campo_tipo(const char* sn, const char* cn, char* out);")
    ctx.write_line("")
    ctx.write_line("// ME-B6: tipos de retorno de funciones definidas (inferencia de tipos nativa)")
    ctx.write_line("extern char _G_native_func_returns[512][64];")
    ctx.write_line("extern int _G_native_func_returns_count;")
    ctx.write_line("extern int _G_native_tipo_retorno(const char* fn, char* out);")
    ctx.write_line("")
    # ME-D6: constructores ADT (ok/err/algun/ninguno) — paridad orquestador.syn
    ctx.write_line("extern char _G_native_adt_ctrs[256][64];")
    ctx.write_line("extern char _G_native_adt_ctrs_adt[256][64];")
    ctx.write_line("extern int _G_native_adt_ctrs_tag[256];")
    ctx.write_line("extern char _G_native_adt_ctrs_tipo[256][64];")
    ctx.write_line("extern int _G_native_adt_ctrs_count;")
    ctx.write_line("extern int _G_native_es_adt_ctr(const char* c);")
    ctx.write_line("extern int _G_native_adt_ctr_info(const char* c, char* adt_out, int* tag_out, char* tipo_out);")
    ctx.write_line("extern int _G_native_adt_unwrap_tipo(const char* adt, char* tipo_out);")
    ctx.write_line("extern int _G_native_adt_unwrap_field(const char* adt, char* field_out);")
    # ME-D2: instanciaciones de ADT genéricos (monomorfización, Opción A)
    ctx.write_line("extern char _G_native_adt_gen[64][64];")
    ctx.write_line("extern int _G_native_adt_gen_nparams[64];")
    ctx.write_line("extern char _G_native_adt_gen_params[64][8][64];")
    ctx.write_line("extern int _G_native_adt_gen_count;")
    ctx.write_line("extern int _G_native_adt_gen_es(const char* n);")
    ctx.write_line("extern char _G_native_adt_inst_type[64][64];")
    ctx.write_line("extern char _G_native_adt_inst_c[64][64];")
    ctx.write_line("extern char _G_native_adt_inst_base[64][64];")
    ctx.write_line("extern char _G_native_adt_inst_fields_c[64][8][64];")
    ctx.write_line("extern int _G_native_adt_inst_nfields[64];")
    ctx.write_line("extern int _G_native_adt_inst_count;")
    ctx.write_line("extern int _G_native_adt_inst_ctr(const char* base, int tag, const char* tipo_c, char* out);")
    ctx.write_line("")
    ctx.write_line("// ME-B7: dedup de funciones emitidas y hoisting de variables (paridad orquestador nativo)")
    ctx.write_line("extern char _G_emit_func_names[2048][64];")
    ctx.write_line("extern int _G_emit_func_count;")
    ctx.write_line("extern char _G_fn_vars[2048][64];")
    ctx.write_line("extern int _G_fn_vars_count;")
    ctx.write_line("extern void* _G_fn_var_src[2048];")
    ctx.write_line("extern int _G_fn_var_auto[2048];")
    ctx.write_line("extern char _G_fn_var_tipos[2048][64];  // ME-C4: tipo inferido por hoisting")
    ctx.write_line("extern char _G_fn_ptr_vars[64][64];  // ME-B9.x: parametros puntero"
)
    ctx.write_line("extern int _G_fn_ptr_vars_count;")
    # F3-10: elemento (Canal<T>) de cada variable canal para el receive `ch ->`
    ctx.write_line("extern char _G_native_canal_names[512][64];")
    ctx.write_line("extern char _G_native_canal_elem[512][64];")
    ctx.write_line("extern int _G_native_canal_count;")
    ctx.write_line("extern void _G_native_canal_elem_set(const char* _cname, const char* _celem);")
    ctx.write_line("extern int _G_native_canal_elem_tipo(const char* _cname, char* _cout);")
    # F3-7: funciones listener de `escuchar` (Manual 2 L113) — paridad orquestador nativo
    ctx.write_line("extern char _G_listeners[8][16384];")
    ctx.write_line("extern int _G_listeners_count;")
    ctx.write_line("extern int _G_listener_modo;")
    # F4.4: wrappers de `lanzar` (fibras M:N, Manual 5 §2.6) — paridad orquestador nativo
    ctx.write_line("extern char _G_lanzar_wrappers[8][4096];")
    ctx.write_line("extern int _G_lanzar_wrappers_count;")
    ctx.write_line("extern int _G_lanzar_count;")
    # ME-F1.2b: alias de tipo declarados (`tipo X = Y`) — paridad orquestador nativo
    ctx.write_line("extern char _G_tipo_aliases[128][64];")
    ctx.write_line("extern char _G_tipo_aliases_base[128][64];")
    ctx.write_line("extern int _G_tipo_aliases_count;")
    # R5 (F2-2.4c): senal de error de parseo del wrapper parsear() -> pipeline aborte
    ctx.write_line("extern int _G_parse_error;")
    ctx.write_line("")
    ctx.write_line("extern int _G_indent;")
    ctx.write_line("")
    ctx.write_line("const char* _G_mt(const char* st);")
    ctx.write_line("void _G_vest(struct DefinicionEstructura* n);")
    ctx.write_line("")
    ctx.write_line("#define TAG_OK 0")
    ctx.write_line("#define TAG_ERR 1")
    ctx.write_line("#define TAG_ALGUNO 0")
    ctx.write_line("#define TAG_NINGUNO 1")
    ctx.write_line("")

    if not ctx.is_no_std():
        ctx.write_line("// --- Helpers de serializaci\u00f3n primitiva ---")
        ctx.write_line("static inline void* _synapse_box_int(int64_t v) "
            "{ return (void*)(intptr_t)v; }"
        )
        ctx.write_line(
            "static inline int64_t _synapse_unbox_int(void* p) "
            "{ return (int64_t)(intptr_t)p; }"
        )
        ctx.write_line(
            "static inline void* _synapse_box_float(double v) {"
        )
        ctx.inc_indent()
        ctx.write_line("double* _p = (double*)malloc(sizeof(double));")
        ctx.write_line(
            'if (!_p) { fprintf(stderr, '
            '"ESCAPA_DEL_ALCANCE: malloc fallo\\\\n"); exit(1); }'
        )
        ctx.write_line("*_p = v;")
        ctx.write_line("return (void*)_p;")
        ctx.dec_indent()
        ctx.write_line("}")
        ctx.write_line(
            "static inline double _synapse_unbox_float(void* p) {"
        )
        ctx.inc_indent()
        ctx.write_line("double _v = *(double*)p;")
        ctx.write_line("free(p);")
        ctx.write_line("return _v;")
        ctx.dec_indent()
        ctx.write_line("}")
        ctx.write_line("")

    ctx.write_line("extern void pool_init(uint32_t total_blocks, uint32_t block_size);")
    ctx.write_line("extern void pool_free(void* ptr);")
    ctx.write_line("extern void* pool_alloc(size_t size);")
    ctx.write_line("extern void pool_destroy(void);")
    if ctx.is_no_std():
        ctx.write_line("extern void* __syn_asignar(int tamano);")
        ctx.write_line("extern void __syn_liberar(void* ptr);")
        ctx.write_line("")

    if not ctx.is_no_std():
        for ext in [
            "void escribir(CadenaSegura contenido)",
            "void escribir_linea(CadenaSegura contenido)",
            "CadenaSegura leer_linea(void)",
            "Canal abrir(CadenaSegura ruta, CadenaSegura modo)",
            "CadenaSegura leer(Canal canal)",
            "void cerrar_archivo(Canal canal)",
            "Tensor crear_tensor(int filas, int columnas)",
            "Tensor suma_tensor(Tensor a, Tensor b)",
            "Tensor producto_punto(Tensor a, Tensor b)",
            "Tensor relu(Tensor a)",
            "Tensor reserva(int tamano)",
            "void libera(Tensor bloque)",
            "Tensor suma(Tensor a, Tensor b)",
            "Tensor producto(Tensor a, Tensor b)",
            "int64_t texto_a_entero(CadenaSegura str)",
            "double texto_a_decimal(CadenaSegura str)",
            "CadenaSegura decimal_a_texto(double n)",
            "CadenaSegura entero_a_texto(int64_t n)",
            "int str_eq(CadenaSegura a, CadenaSegura b)",
            "void synapse_lanzar_hilo(void* (*fn)(void*), void* arg)",
            "void synapse_esperar_hilos(void)",
            "void synapse_esperar_fibras(void)",
            "void scheduler_iniciar(int num_hilos_os)",
            "void scheduler_detener(void)",
            "void fibra_crear(void (*func)(void*), void* arg, size_t stack_size)",
            "void fibra_esperar(int fibra_id)",
            "void fibra_terminar(void* resultado)",
            "void _syn_texto_liberar(CadenaSegura s)",
        ]:
            ctx.write_line(f"extern {ext};")

        ctx.write_line("")
        ctx.write_line("typedef struct { int es_ok; union {")
        ctx.write_line("void* ok_valor; const char* err_mensaje;")
        ctx.write_line("} datos; } Resultado_T;")
        ctx.write_line("typedef struct CanalConcurrencia CanalConcurrencia;")
        for ext in [
            "CanalConcurrencia* canal_crear(uint32_t capacidad)",
            "void canal_enviar(CanalConcurrencia* canal, void* paquete)",
            "void* canal_recibir(CanalConcurrencia* canal, bool* cerrado)",
            "void canal_destruir(CanalConcurrencia* canal)",
            "void cerrar(CanalConcurrencia* canal)",
        ]:
            ctx.write_line(f"extern {ext};")

    # _simd_detectar(): deteccion SIMD unificada via runtime (synapse_rt.o)
    # NOTA: _syn_simd_disponible y _syn_simd_tipo NO se declaran aqui porque
    # sus declaraciones estan en las bibliotecas std (e.g. std/tensor.syn) que
    # las emite como extern CadenaSegura/CadenaSegura. Duplicarlas aqui causa
    # conflictos de tipos (const char* vs CadenaSegura).
    if not ctx.is_no_std():
        ctx.write_line("// --- Deteccion SIMD unificada (delegada al runtime synapse_rt.o) ---")
        ctx.write_line("extern void _simd_detectar(void);")
        ctx.write_line("")

    emit_contract_header(ctx)


class GeneradorC:
    def __init__(self, programa: Programa):
        self.ctx = GeneratorContext(programa)

    @property
    def _destructor_map(self):
        return self.ctx._destructor_map

    # ---- M\u00f3dulos de emisi\u00f3n auxiliares ----

    def _emit_cabecera_comun(self, ctx):
        """Helper: _emitir_encabezado + definiciones de vars globales + _g_argc/_argv/salir/concat"""
        _emitir_encabezado(ctx)
        if not ctx.is_no_std():
            # Definiciones de variables globales (declaradas como extern en _emitir_encabezado)
            ctx.write_line("char _gen_tmp_buf[4096];")
            ctx.write_line("")
            ctx.write_line("char _G_emit_buf[1048576];")
            ctx.write_line("int _G_emit_pos;")
            ctx.write_line("FILE* _G_fp;")
            ctx.write_line("int _G_scope_depth;")
            ctx.write_line("int _G_scope_vars_depth[256];")
            ctx.write_line("char _G_scope_vars_names[256][64];")
            ctx.write_line("int _G_scope_vars_total;")
            ctx.write_line("int _G_safe_mode;  // M22.5: --safe flag for lifetime assertions")
            ctx.write_line("char _G_native_structs[256][64];")
            ctx.write_line("int _G_native_structs_count;")
            ctx.write_line("int _G_native_es_estructura(const char* n) {")
            ctx.inc_indent()
            ctx.write_line("if (!n) return 0;")
            ctx.write_line("for (int _i = 0; _i < _G_native_structs_count; _i++) {")
            ctx.inc_indent()
            ctx.write_line("if (strcmp(_G_native_structs[_i], n) == 0) return 1;")
            ctx.dec_indent()
            ctx.write_line("}")
            ctx.write_line("return 0;")
            ctx.dec_indent()
            ctx.write_line("}")
            ctx.write_line("")
            # F3-13: campos de struct con tipo Synapse (paridad orquestador.syn)
            ctx.write_line("char _G_native_struct_campos[256][64][64];")
            ctx.write_line("char _G_native_struct_campos_tipo[256][64][64];")
            ctx.write_line("int _G_native_struct_campos_count[256];")
            ctx.write_line("int _G_native_campo_tipo(const char* sn, const char* cn, char* out) {")
            ctx.inc_indent()
            ctx.write_line("if (!sn || !cn || !out) return 0;")
            ctx.write_line("for (int _i = 0; _i < _G_native_structs_count; _i++) {")
            ctx.inc_indent()
            ctx.write_line("if (strcmp(_G_native_structs[_i], sn) == 0) {")
            ctx.inc_indent()
            ctx.write_line("for (int _j = 0; _j < _G_native_struct_campos_count[_i]; _j++) {")
            ctx.inc_indent()
            ctx.write_line("if (strcmp(_G_native_struct_campos[_i][_j], cn) == 0) {")
            ctx.inc_indent()
            ctx.write_line("strcpy(out, _G_native_struct_campos_tipo[_i][_j]); return 1;")
            ctx.dec_indent()
            ctx.write_line("}")
            ctx.dec_indent()
            ctx.write_line("}")
            ctx.dec_indent()
            ctx.write_line("}")
            ctx.dec_indent()
            ctx.write_line("}")
            ctx.write_line("return 0;")
            ctx.dec_indent()
            ctx.write_line("}")
            ctx.write_line("")
            # ME-B6: tipos de retorno (paridad con el bloque 'modo == modulo')
            ctx.write_line("char _G_native_func_returns[512][64];")
            ctx.write_line("int _G_native_func_returns_count;")
            ctx.write_line("int _G_native_tipo_retorno(const char* fn, char* out) {")
            ctx.inc_indent()
            ctx.write_line("if (!fn || !out) return 0;")
            ctx.write_line("for (int _i = 0; _i < _G_native_func_returns_count; _i++) {")
            ctx.inc_indent()
            ctx.write_line("if (strcmp(_G_native_func_returns[_i], fn) == 0) {")
            ctx.inc_indent()
            ctx.write_line("strcpy(out, _G_native_func_returns[_i + 256]); return 1;")
            ctx.dec_indent()
            ctx.write_line("}")
            ctx.dec_indent()
            ctx.write_line("}")
            ctx.write_line("return 0;")
            ctx.dec_indent()
            ctx.write_line("}")
            ctx.write_line("")
            # ME-D6: constructores ADT (definiciones; paridad orquestador.syn)
            ctx.write_line("char _G_native_adt_ctrs[256][64];")
            ctx.write_line("char _G_native_adt_ctrs_adt[256][64];")
            ctx.write_line("int _G_native_adt_ctrs_tag[256];")
            ctx.write_line("char _G_native_adt_ctrs_tipo[256][64];")
            ctx.write_line("int _G_native_adt_ctrs_count;")
            ctx.write_line("int _G_native_es_adt_ctr(const char* c) {")
            ctx.inc_indent()
            ctx.write_line("if (!c) return 0;")
            ctx.write_line("for (int _i = 0; _i < _G_native_adt_ctrs_count; _i++) {")
            ctx.inc_indent()
            ctx.write_line("if (strcmp(_G_native_adt_ctrs[_i], c) == 0) return 1;")
            ctx.dec_indent()
            ctx.write_line("}")
            ctx.write_line("return 0;")
            ctx.dec_indent()
            ctx.write_line("}")
            ctx.write_line("int _G_native_adt_ctr_info(const char* c, char* adt_out, int* tag_out, char* tipo_out) {")
            ctx.inc_indent()
            ctx.write_line("if (!c) return 0;")
            ctx.write_line("for (int _i = 0; _i < _G_native_adt_ctrs_count; _i++) {")
            ctx.inc_indent()
            ctx.write_line("if (strcmp(_G_native_adt_ctrs[_i], c) == 0) {")
            ctx.inc_indent()
            ctx.write_line("if (adt_out) strcpy(adt_out, _G_native_adt_ctrs_adt[_i]);")
            ctx.write_line("if (tag_out) *tag_out = _G_native_adt_ctrs_tag[_i];")
            ctx.write_line("if (tipo_out) strcpy(tipo_out, _G_native_adt_ctrs_tipo[_i]);")
            ctx.write_line("return 1;")
            ctx.dec_indent()
            ctx.write_line("}")
            ctx.dec_indent()
            ctx.write_line("}")
            ctx.write_line("return 0;")
            ctx.dec_indent()
            ctx.write_line("}")
            ctx.write_line("int _G_native_adt_unwrap_tipo(const char* adt, char* tipo_out) {")
            ctx.inc_indent()
            ctx.write_line("if (!adt || !tipo_out) return 0;")
            ctx.write_line("for (int _i = 0; _i < _G_native_adt_ctrs_count; _i++) {")
            ctx.inc_indent()
            ctx.write_line("if (_G_native_adt_ctrs_tag[_i] == 0 && strcmp(_G_native_adt_ctrs_adt[_i], adt) == 0) {")
            ctx.inc_indent()
            ctx.write_line("strcpy(tipo_out, _G_native_adt_ctrs_tipo[_i]);")
            ctx.write_line("return 1;")
            ctx.dec_indent()
            ctx.write_line("}")
            ctx.dec_indent()
            ctx.write_line("}")
            ctx.write_line("return 0;")
            ctx.dec_indent()
            ctx.write_line("}")
            ctx.write_line("int _G_native_adt_unwrap_field(const char* adt, char* field_out) {")
            ctx.inc_indent()
            ctx.write_line("if (!adt || !field_out) return 0;")
            ctx.write_line("// D-2: normalizar la base de una instanciacion (Resultado<entero,texto> -> Resultado)")
            ctx.write_line("char _ab[64]; int _ai = 0; for (; adt[_ai] && adt[_ai] != '<' && _ai < 62; _ai++) _ab[_ai] = adt[_ai]; _ab[_ai] = 0;")
            ctx.write_line("for (int _i = 0; _i < _G_native_adt_ctrs_count; _i++) {")
            ctx.inc_indent()
            ctx.write_line("if (_G_native_adt_ctrs_tag[_i] == 0 && strcmp(_G_native_adt_ctrs_adt[_i], _ab) == 0) {")
            ctx.inc_indent()
            ctx.write_line("strcpy(field_out, _G_native_adt_ctrs[_i]);")
            ctx.write_line("return 1;")
            ctx.dec_indent()
            ctx.write_line("}")
            ctx.dec_indent()
            ctx.write_line("}")
            ctx.write_line("return 0;")
            ctx.dec_indent()
            ctx.write_line("}")
            ctx.write_line("")
            # ME-D2: instanciaciones de ADT genericos (definiciones; paridad orquestador.syn)
            ctx.write_line("char _G_native_adt_gen[64][64];")
            ctx.write_line("int _G_native_adt_gen_nparams[64];")
            ctx.write_line("char _G_native_adt_gen_params[64][8][64];")
            ctx.write_line("int _G_native_adt_gen_count;")
            ctx.write_line("int _G_native_adt_gen_es(const char* n) {")
            ctx.inc_indent()
            ctx.write_line("if (!n) return 0;")
            ctx.write_line("for (int _i = 0; _i < _G_native_adt_gen_count; _i++) { if (strcmp(_G_native_adt_gen[_i], n) == 0) return 1; }")
            ctx.write_line("return 0;")
            ctx.dec_indent()
            ctx.write_line("}")
            ctx.write_line("char _G_native_adt_inst_type[64][64];")
            ctx.write_line("char _G_native_adt_inst_c[64][64];")
            ctx.write_line("char _G_native_adt_inst_base[64][64];")
            ctx.write_line("char _G_native_adt_inst_fields_c[64][8][64];")
            ctx.write_line("int _G_native_adt_inst_nfields[64];")
            ctx.write_line("int _G_native_adt_inst_count;")
            ctx.write_line("int _G_native_adt_inst_ctr(const char* base, int tag, const char* tipo_c, char* out) {")
            ctx.inc_indent()
            ctx.write_line("if (!base || !out) return 0;")
            ctx.write_line("int _solo = 1; int _ns = 0; for (int _j = 0; _j < _G_native_adt_inst_count; _j++) { if (strcmp(_G_native_adt_inst_base[_j], base) == 0) { _ns++; } }")
            ctx.write_line("if (_ns == 1) _solo = 1; else _solo = 0;")
            ctx.write_line("for (int _i = 0; _i < _G_native_adt_inst_count; _i++) {")
            ctx.inc_indent()
            ctx.write_line("if (strcmp(_G_native_adt_inst_base[_i], base) != 0) continue;")
            ctx.write_line("if (_solo) { strcpy(out, _G_native_adt_inst_c[_i]); return 1; }")
            ctx.write_line("if (tag < _G_native_adt_inst_nfields[_i] && tipo_c && _G_native_adt_inst_fields_c[_i][tag][0] && strcmp(_G_native_adt_inst_fields_c[_i][tag], tipo_c) == 0) { strcpy(out, _G_native_adt_inst_c[_i]); return 1; }")
            ctx.dec_indent()
            ctx.write_line("}")
            ctx.write_line("return 0;")
            ctx.dec_indent()
            ctx.write_line("}")
            ctx.write_line("")
            # ME-B7: dedup de funciones emitidas y hoisting de variables
            ctx.write_line("char _G_emit_func_names[2048][64];")
            ctx.write_line("int _G_emit_func_count;")
            ctx.write_line("char _G_fn_vars[2048][64];")
            ctx.write_line("int _G_fn_vars_count;")
            ctx.write_line("void* _G_fn_var_src[2048];")
            ctx.write_line("int _G_fn_var_auto[2048];")
            ctx.write_line("char _G_fn_var_tipos[2048][64];  // ME-C4: tipo inferido por hoisting")
            ctx.write_line("char _G_fn_ptr_vars[64][64];  // ME-B9.x: parametros puntero"
)
            ctx.write_line("int _G_fn_ptr_vars_count;")
            # F3-10: elemento (Canal<T>) de cada variable canal para el receive `ch ->`
            # (Manual 2 L144 / Manual 5 §4.2). Paridad orquestador nativo.
            ctx.write_line("char _G_native_canal_names[512][64];")
            ctx.write_line("char _G_native_canal_elem[512][64];")
            ctx.write_line("int _G_native_canal_count;")
            ctx.write_line("void _G_native_canal_elem_set(const char* _cname, const char* _celem) {")
            ctx.write_line("    if (!_cname || !_celem) return;")
            ctx.write_line("    for (int _ci = 0; _ci < _G_native_canal_count; _ci++) { if (strcmp(_G_native_canal_names[_ci], _cname) == 0) { strncpy(_G_native_canal_elem[_ci], _celem, 63); _G_native_canal_elem[_ci][63] = 0; return; } }")
            ctx.write_line("    if (_G_native_canal_count < 512) { strncpy(_G_native_canal_names[_G_native_canal_count], _cname, 63); _G_native_canal_names[_G_native_canal_count][63] = 0; strncpy(_G_native_canal_elem[_G_native_canal_count], _celem, 63); _G_native_canal_elem[_G_native_canal_count][63] = 0; _G_native_canal_count++; }")
            ctx.write_line("}")
            ctx.write_line("int _G_native_canal_elem_tipo(const char* _cname, char* _cout) {")
            ctx.write_line("    if (!_cname || !_cout) return 0;")
            ctx.write_line("    for (int _ci = 0; _ci < _G_native_canal_count; _ci++) { if (strcmp(_G_native_canal_names[_ci], _cname) == 0) { strncpy(_cout, _G_native_canal_elem[_ci], 63); _cout[63] = 0; return 1; } }")
            ctx.write_line("    return 0;")
            ctx.write_line("}")
            # F3-7: funciones listener de `escuchar` (Manual 2 L113) acumuladas y
            # flusheadas antes del main (paridad orquestador.syn). _G_listener_modo
            # marca el cuerpo del bloque (ExprRecibirCanal -> canal_recibir(_canal)).
            ctx.write_line("char _G_listeners[8][16384];")
            ctx.write_line("int _G_listeners_count;")
            ctx.write_line("int _G_listener_modo;")
            # F4.4: wrappers de `lanzar` (fibras M:N, Manual 5 §2.6) acumulados y
            # flusheados antes del main (paridad orquestador.syn).
            ctx.write_line("char _G_lanzar_wrappers[8][4096];")
            ctx.write_line("int _G_lanzar_wrappers_count;")
            ctx.write_line("int _G_lanzar_count;")
            ctx.write_line("")
            # ME-F1.2b: alias de tipo declarados (paridad orquestador nativo)
            ctx.write_line("char _G_tipo_aliases[128][64];")
            ctx.write_line("char _G_tipo_aliases_base[128][64];")
            ctx.write_line("int _G_tipo_aliases_count;")
            # R5 (F2-2.4c): definicion de la senal de error de parseo
            ctx.write_line("int _G_parse_error = 0;")
            ctx.write_line("")
            ctx.write_line("")
            ctx.write_line("int _g_argc;")
            ctx.write_line("char** _g_argv;")
            ctx.write_line("int _argc() { return _g_argc; }")
            ctx.write_line("")
            ctx.write_line("CadenaSegura _argv(int i) {")
            ctx.inc_indent()
            ctx.write_line(
                'if (i < 0 || i >= _g_argc) '
                'return (CadenaSegura){0, ""};'
            )
            ctx.write_line(
                "return (CadenaSegura){ .longitud = (int)strlen(_g_argv[i]),"
                " .datos = _g_argv[i] };"
            )
            ctx.dec_indent()
            ctx.write_line("}")
            ctx.write_line("")
            ctx.write_line("void salir(int codigo) { exit(codigo); }")
            ctx.write_line("")
            ctx.write_line("CadenaSegura concat(CadenaSegura a, CadenaSegura b) {")
            ctx.inc_indent()
            ctx.write_line("int _tl = a.longitud + b.longitud;")
            ctx.write_line("char* _buf = (char*)malloc(_tl + 1);")
            ctx.write_line(
                'if (!_buf) { fprintf(stderr,'
                '"Error: malloc fallo en concat()\\\\n"); exit(1); }'
            )
            ctx.write_line("memcpy(_buf, a.datos, a.longitud);")
            ctx.write_line("memcpy(_buf + a.longitud, b.datos, b.longitud);")
            ctx.write_line("_buf[_tl] = 0;")
            ctx.write_line("return (CadenaSegura){_tl, _buf};")
            ctx.dec_indent()
            ctx.write_line("}")
            ctx.write_line("")

    def _emit_prototipos_funciones(self, ctx):
        """Helper: forward-declares de funciones (prototipos) en orden alfabético (Manual 8 §8.2)."""
        _SPECIAL_SIGS = {
            # A5.2 (D-7): tokenizar/generar retornan `entero` (Manual 2 §4.1
            # L267-268) → int64_t en C; 'int' entraba en conflicto con la
            # definicion (conflicting types) tras migrar el mapeo.
            'tokenizar': 'int64_t tokenizar(CadenaSegura fuente)',
            'parsear': 'struct Programa parsear(CadenaSegura fuente)',
            'volcar_ast': 'void volcar_ast(struct Nodo* nodo, int nivel)',
            'generar': 'int64_t generar(struct Programa programa, CadenaSegura ruta)',
        }
        # Manual 8 §8.2: orden alfabético estricto por nombre
        # F1.2d: incluir funciones envueltas en @export (sus llamadas necesitan
        # prototipo cuando el llamador se emite antes que la definición).
        funciones = sorted(
            [s for s in ctx.programa.sentencias if isinstance(s, DefinicionFuncion) and s.nombre not in ctx._RUNTIME_BUILTINS]
            + [s.funcion for s in ctx.programa.sentencias
               if isinstance(s, DeclaracionExport) and isinstance(s.funcion, DefinicionFuncion)],
            key=lambda f: f.nombre
        )
        for s in funciones:
                if s.nombre in _SPECIAL_SIGS:
                    ctx.write_line(f"{_SPECIAL_SIGS[s.nombre]};")
                else:
                    tipo_ret = ctx.traducir_tipo_c(s.tipo_retorno)
                    params = ", ".join(
                        f"{ctx.traducir_tipo_c(p.tipo)}{'*' if p.tipo in ctx._POINTER_TYPES else ''} {p.nombre}"
                        for p in s.parametros
                    ) if s.parametros else "void"
                    ctx.write_line(f"{tipo_ret} {s.nombre}({params});")
        if any(
            isinstance(s, DefinicionFuncion)
            and s.nombre not in ctx._RUNTIME_BUILTINS
            for s in ctx.programa.sentencias
        ):
            ctx.write_line("")

    def _emit_main(self, ctx, scope_names: set[str] | None = None):
        """Helper: emite main() SOLO si existe funci\u00f3n 'principal' en este m\u00f3dulo
        y est\u00e1 dentro del alcance (scope_names)."""
        principal = ctx.encontrar_principal()
        if principal is None:
            return
        if scope_names is not None and principal not in scope_names:
            return
        if ctx.is_no_std():
            ctx.write_line("int main(void) {")
            ctx.inc_indent()
            ctx.write_line(f"{principal}();")
            ctx.write_line("return 0;")
            ctx.dec_indent()
            ctx.write_line("}")
        else:
            ctx.write_line("int main(int argc, char** argv) {")
            ctx.inc_indent()
            ctx.write_line("_g_argc = argc;")
            ctx.write_line("_g_argv = argv;")
            if ctx._safe_mode:
                ctx.write_line("_G_safe_mode = 1;  // --safe activo: aserciones de lifetimes")
            ctx.write_line("pool_init(POOL_BLOQUES, TAMANO_BLOQUE);")
            ret_tipo = ctx._func_return_types.get(principal, 'int')
            if ret_tipo in ('nulo', 'void'):
                ctx.write_line(f"{principal}();")
                ctx.write_line("synapse_esperar_hilos();")
                ctx.write_line("synapse_esperar_fibras();")
                ctx.write_line("pool_destroy();")
                ctx.write_line("return 0;")
            else:
                # F3-7: el main DEBE esperar a los hilos/fibras (listeners y
                # fibras de lanzar) antes de salir — `return principal();`
                # mataba el proceso sin esperar. F4.4: además de los pthreads
                # residuales (synapse_esperar_hilos) espera a las FIBRAS M:N
                # (synapse_esperar_fibras). Paridad con el nativo.
                ctx.write_line(f"int64_t _rc = {principal}();")
                ctx.write_line("synapse_esperar_hilos();")
                ctx.write_line("synapse_esperar_fibras();")
                ctx.write_line("pool_destroy();")
                ctx.write_line("return _rc;")
            ctx.dec_indent()
            ctx.write_line("}")

    def _emit_cuerpos(self, ctx, scope_names: set[str] | None = None):
        """Helper: emite cuerpos de funciones + listeners + wrappers.
        Manual 8 §8.2: orden alfabético estricto por nombre para funciones.
        Si scope_names no es None, solo emite funciones cuyos nombres estén en el conjunto."""
        # F3-7: pre-scan de `escuchar` — emitir los externs de los listeners
        # ANTES de los cuerpos de funciones (antes se emitían tras ellos y gcc
        # fallaba con '_listener_N undeclared' al usarse en synapse_lanzar_hilo
        # dentro de principal). El conteo replica el orden de emisión
        # (no-funciones en parse order + funciones alfabéticas) para que la
        # numeración _listener_1..N coincida con _contador_listener.
        n_listeners = _contar_escuchar_emision(ctx, scope_names)
        for i in range(1, n_listeners + 1):
            ctx.write_line(f"extern void _listener_{i}(void* arg);")
        if n_listeners:
            ctx.write_line("")
        # Manual 8 §8.2: orden alfabético estricto para funciones
        # Primero emitir sentencias no-función (extern, import, constantes) en parse order,
        # luego funciones en orden alfabético — requisito de C: extern/const antes de cuerpos
        funciones = sorted(
            [s for s in ctx.programa.sentencias if isinstance(s, DefinicionFuncion)],
            key=lambda f: f.nombre
        )
        if scope_names is not None:
            funciones = [f for f in funciones if f.nombre in scope_names]
        # Non-function sentencias FIRST (externs, imports, constants before function bodies)
        # ME-R8 (D5): las StmtConstante SIEMPRE se emiten (en modo 'modulo' no se
        # filtran por scope_names) — un modulo que usa SYSTEM_PROMPT/ARCHIVO_CONFIG
        # necesita el #define Y el registro en ctx._const_types para que el hoisting
        # infiera el tipo correcto (antes: identificadores sin definir + vars como int).
        for s in ctx.programa.sentencias:
            if isinstance(s, DefinicionFuncion):
                continue
            if isinstance(s, StmtConstante):
                visitar_constante(ctx, s)
                continue
            if scope_names is not None and hasattr(s, 'nombre') and getattr(s, 'nombre', None) not in scope_names:
                continue
            visitar(ctx, s)
        # Functions en orden alfabético
        for s in funciones:
            visitar(ctx, s)
        # Listener functions: cuerpos acumulados por visitar_escuchar (F3-7);
        # sus externs ya se emitieron arriba, antes de los cuerpos.
        for func in ctx._listener_funciones:
            ctx.lineas.append(func)
            ctx.lineas.append("")
        for wrap in ctx._deferred_wrappers:
            ctx.write_line(wrap)
            ctx.write_line("")

    # ---- Modos de emisi\u00f3n ----

    def generar(self, modo='completo', include_header='',
                scope_names: set[str] | None = None) -> str:
        """
        Genera c\u00f3digo C en tres modos:
        - 'completo': archivo completo (comportamiento original)
        - 'header':   solo cabecera + tipos + prototipos (sin cuerpos, sin main)
        - 'modulo':   #include header + cuerpos de funciones (sin repetir cabecera)
        Si scope_names se proporciona, solo se emiten cuerpos de funciones cuyos
        nombres est\u00e9n en el conjunto (m\u00f3dulos independientes).
        """
        ctx = self.ctx
        ctx._variables = {}
        ctx._func_return_types = {}
        ctx._func_param_types = {}
        # F3-7: reset de listeners (el pre-scan de _emit_cuerpos cuenta en el
        # mismo orden que _contador_listener incrementa; sin reset, una segunda
        # llamada a generar() re-numeraría y los externs no coincidirían).
        ctx._contador_listener = 0
        ctx._listener_funciones = []

        for s in ctx.programa.sentencias:
            if isinstance(s, DefinicionFuncion):
                ctx._func_return_types[s.nombre] = s.tipo_retorno
                ctx._func_param_types[s.nombre] = [p.tipo for p in s.parametros]
            elif isinstance(s, DeclaracionExterna):
                ctx._func_return_types[s.nombre] = s.tipo_retorno
            elif isinstance(s, DeclaracionExport) and isinstance(s.funcion, DefinicionFuncion):
                # F1.2d: registrar retorno/params de funciones envueltas en @export
                # (inferencia de tipos en sitios de llamada, paridad con orquestador ME-B6).
                ctx._func_return_types[s.funcion.nombre] = s.funcion.tipo_retorno
                ctx._func_param_types[s.funcion.nombre] = [p.tipo for p in s.funcion.parametros]

        # Construir mapa de _estructuras
        for s in ctx.programa.sentencias:
            if isinstance(s, DefinicionEstructura):
                es_adt = any(
                    c.nombre == 'tag' and c.tipo in ('entero', 'int')
                    for c in s.campos
                )
                ctx._estructuras[s.nombre] = {
                    'campos': [(c.nombre, c.tipo) for c in s.campos],
                    'campos_pointer': set(),
                    'es_adt': es_adt,
                }
        for nombre, info in ctx._estructuras.items():
            for c_nombre, c_tipo in info['campos']:
                if (
                    c_tipo in ctx._estructuras
                    or c_tipo.rstrip('*') in ctx._estructuras
                    or c_tipo == nombre
                ):
                    info['campos_pointer'].add(c_nombre)

        # F1.2: pre-pass de DeclaracionTipo — registrar alias y ADTs ANTES de
        # prototipos/uso (traducir_tipo_c y visitar_coincidir dependen de ellos).
        for s in ctx.programa.sentencias:
            if not isinstance(s, DeclaracionTipo):
                continue
            if s.constructores:
                campos = [('tag', 'entero')]
                for c in s.constructores:
                    t_campo = c.tipos[0] if c.tipos else 'entero'
                    if t_campo in s.parametros_tipo:
                        t_campo = 'puntero'
                    campos.append((c.nombre, t_campo))
                if s.nombre not in ctx._estructuras:
                    ctx._estructuras[s.nombre] = {
                        'campos': campos,
                        'campos_pointer': set(),
                        'es_adt': True,
                    }
                # D-6: registro de constructores ADT (ok/err/algun/ninguno) para
                # expr_a_c — compound literal del tagged-union (Manual 2 §2 L75).
                for idx, c in enumerate(s.constructores):
                    t_campo = c.tipos[0] if c.tipos else 'entero'
                    if t_campo in s.parametros_tipo:
                        t_campo = 'puntero'
                    ctx._constructores_adt[c.nombre] = (s.nombre, idx, t_campo)
            elif s.tipo_base and s.nombre not in ctx._tipo_aliases:
                ctx._tipo_aliases[s.nombre] = s.tipo_base

        # D-2: registro de parámetros de tipo y constructores originales de ADT
        # genéricos (para la sustitución en la monomorfización).
        for s in ctx.programa.sentencias:
            if isinstance(s, DeclaracionTipo) and s.constructores:
                ctx._adt_parametros[s.nombre] = list(s.parametros_tipo)
                ctx._adt_constructores[s.nombre] = [
                    (c.nombre, c.tipos[0] if c.tipos else 'entero')
                    for c in s.constructores
                ]
        # D-2: monomorfización — recolectar instanciaciones `Base<A,B>` de ADT
        # genéricos en todo el programa (retornos, params, let, campos) y registrar
        # un struct C especializado por cada instanciación concreta.
        _recolectar_instancias_adt(ctx)

        if modo == 'header':
            # Solo cabecera: #includes, tipos, prototipos + extern declarations
            # IMPORTANTE: NO llamar _emit_cabecera_comun (emite DEFINICIONES _g_argc/_argc/salir/concat)
            # M22.2: Declarar extern de variables de scope RAII
            ctx.write_line("extern int _G_scope_depth;")
            ctx.write_line("extern int _G_scope_vars_depth[256];")
            ctx.write_line("extern char _G_scope_vars_names[256][64];")
            ctx.write_line("extern int _G_scope_vars_total;")
            ctx.write_line("extern int _G_safe_mode;  // M22.5: --safe flag")
            # F5-1 (Manual 2 §5.1): garantiza globals del codegen (usados via
            # asm() en funciones.syn/nodos_flujo.syn para emitir asserts)
            ctx.write_line("extern void* _G_fn_garantizas_actuales;  // F5-1")
            ctx.write_line("extern char _G_fn_ret_tipo_c[64];  // F5-1")
            ctx.write_line("")
            _emitir_encabezado(ctx)
            # Extern declarations para runtime helpers (NO definiciones \u2014 son solo para link)
            if not ctx.is_no_std():
                ctx.write_line("extern int _g_argc;")
                ctx.write_line("extern char** _g_argv;")
                ctx.write_line("extern int _argc(void);")
                ctx.write_line("extern CadenaSegura _argv(int i);")
                ctx.write_line("extern void salir(int codigo);")
                ctx.write_line("extern CadenaSegura concat(CadenaSegura a, CadenaSegura b);")
                ctx.write_line("")
            # Estructuras: forward declarations + definiciones completas (Manual 8 §8.2: orden alfabético)
            # R17: typedefs de instanciaciones de ADT ANTES de los structs
            # (un campo que referencia una instancia emitida después rompía el C)
            _emitir_typedefs_instancias(ctx)
            estructuras = sorted(
                [s for s in ctx.programa.sentencias if isinstance(s, DefinicionEstructura)],
                key=lambda e: e.nombre
            )
            for s in estructuras:
                ctx.write_line(f"struct {s.nombre};")
            if estructuras:
                ctx.write_line("")
            for s in estructuras:
                visitar_estructura(ctx, s)
            # F1.2: typedefs de DeclaracionTipo (alias/ADT) en la cabecera
            for s in ctx.programa.sentencias:
                if isinstance(s, DeclaracionTipo):
                    visitar_declaracion_tipo(ctx, s)
            # Prototipos de funciones
            self._emit_prototipos_funciones(ctx)
            # Declaraciones externas (DeclaracionExterna): emitir como extern
            # Necesario para que modulos que importan _syn_*, _toml_* tengan
            # las declaraciones visibles (Manual 8 §8.1: extern antes de uso)
            from .emit_declarations import visitar_externa
            for s in ctx.programa.sentencias:
                if isinstance(s, DeclaracionExterna):
                    visitar_externa(ctx, s)
            # NO emitir cuerpos de funciones, NO emitir main
            return ctx.generar()

        if modo == 'modulo':
            # M\u00f3dulo: #include header + solo cuerpos (sin repetir cabecera)
            if include_header:
                ctx.write_line(f'#include "{include_header}"')
            else:
                ctx.write_line("// -- modulo sin header --")
            ctx.write_line("")
            # Si este m\u00f3dulo es el principal, emitir definiciones de vars globales y runtime helpers
            tiene_principal = ctx.encontrar_principal() is not None
            if scope_names is not None:
                tiene_principal = tiene_principal and 'principal' in scope_names
            if tiene_principal and not ctx.is_no_std():
                ctx.write_line("char _gen_tmp_buf[4096];")
                ctx.write_line("")
                ctx.write_line("char _G_emit_buf[1048576];")
                ctx.write_line("int _G_emit_pos;")
                ctx.write_line("FILE* _G_fp;")
                # M22.2: Scope tracking globals (definiciones)
                ctx.write_line("int _G_scope_depth;")
                ctx.write_line("int _G_scope_vars_depth[256];")
                ctx.write_line("char _G_scope_vars_names[256][64];")
                ctx.write_line("int _G_scope_vars_total;")
                ctx.write_line("int _G_safe_mode;  // M22.5: --safe flag for lifetime assertions")
                ctx.write_line("")
                # ME-B4: nombres de estructuras (definiciones para constructores nativos)
                ctx.write_line("char _G_native_structs[256][64];")
                ctx.write_line("int _G_native_structs_count;")
                ctx.write_line("int _G_native_es_estructura(const char* n) {")
                ctx.inc_indent()
                ctx.write_line("if (!n) return 0;")
                ctx.write_line("for (int _i = 0; _i < _G_native_structs_count; _i++) {")
                ctx.inc_indent()
                ctx.write_line("if (strcmp(_G_native_structs[_i], n) == 0) return 1;")
                ctx.dec_indent()
                ctx.write_line("}")
                ctx.write_line("return 0;")
                ctx.dec_indent()
                ctx.write_line("}")
                ctx.write_line("")
                # F3-13: campos de struct con tipo Synapse (paridad orquestador.syn)
                ctx.write_line("char _G_native_struct_campos[256][64][64];")
                ctx.write_line("char _G_native_struct_campos_tipo[256][64][64];")
                ctx.write_line("int _G_native_struct_campos_count[256];")
                ctx.write_line("int _G_native_campo_tipo(const char* sn, const char* cn, char* out) {")
                ctx.inc_indent()
                ctx.write_line("if (!sn || !cn || !out) return 0;")
                ctx.write_line("for (int _i = 0; _i < _G_native_structs_count; _i++) {")
                ctx.inc_indent()
                ctx.write_line("if (strcmp(_G_native_structs[_i], sn) == 0) {")
                ctx.inc_indent()
                ctx.write_line("for (int _j = 0; _j < _G_native_struct_campos_count[_i]; _j++) {")
                ctx.inc_indent()
                ctx.write_line("if (strcmp(_G_native_struct_campos[_i][_j], cn) == 0) {")
                ctx.inc_indent()
                ctx.write_line("strcpy(out, _G_native_struct_campos_tipo[_i][_j]); return 1;")
                ctx.dec_indent()
                ctx.write_line("}")
                ctx.dec_indent()
                ctx.write_line("}")
                ctx.dec_indent()
                ctx.write_line("}")
                ctx.dec_indent()
                ctx.write_line("}")
                ctx.write_line("return 0;")
                ctx.dec_indent()
                ctx.write_line("}")
                ctx.write_line("")
                # ME-B6: tipos de retorno
                ctx.write_line("char _G_native_func_returns[512][64];")
                ctx.write_line("int _G_native_func_returns_count;")
                ctx.write_line("int _G_native_tipo_retorno(const char* fn, char* out) {")
                ctx.inc_indent()
                ctx.write_line("if (!fn || !out) return 0;")
                ctx.write_line("for (int _i = 0; _i < _G_native_func_returns_count; _i++) {")
                ctx.inc_indent()
                ctx.write_line("if (strcmp(_G_native_func_returns[_i], fn) == 0) {")
                ctx.inc_indent()
                ctx.write_line("strcpy(out, _G_native_func_returns[_i + 256]); return 1;")
                ctx.dec_indent()
                ctx.write_line("}")
                ctx.dec_indent()
                ctx.write_line("}")
                ctx.write_line("return 0;")
                ctx.dec_indent()
                ctx.write_line("}")
                ctx.write_line("")
                # ME-D6: constructores ADT (definiciones; paridad orquestador.syn)
                ctx.write_line("char _G_native_adt_ctrs[256][64];")
                ctx.write_line("char _G_native_adt_ctrs_adt[256][64];")
                ctx.write_line("int _G_native_adt_ctrs_tag[256];")
                ctx.write_line("char _G_native_adt_ctrs_tipo[256][64];")
                ctx.write_line("int _G_native_adt_ctrs_count;")
                ctx.write_line("int _G_native_es_adt_ctr(const char* c) {")
                ctx.inc_indent()
                ctx.write_line("if (!c) return 0;")
                ctx.write_line("for (int _i = 0; _i < _G_native_adt_ctrs_count; _i++) {")
                ctx.inc_indent()
                ctx.write_line("if (strcmp(_G_native_adt_ctrs[_i], c) == 0) return 1;")
                ctx.dec_indent()
                ctx.write_line("}")
                ctx.write_line("return 0;")
                ctx.dec_indent()
                ctx.write_line("}")
                ctx.write_line("int _G_native_adt_ctr_info(const char* c, char* adt_out, int* tag_out, char* tipo_out) {")
                ctx.inc_indent()
                ctx.write_line("if (!c) return 0;")
                ctx.write_line("for (int _i = 0; _i < _G_native_adt_ctrs_count; _i++) {")
                ctx.inc_indent()
                ctx.write_line("if (strcmp(_G_native_adt_ctrs[_i], c) == 0) {")
                ctx.inc_indent()
                ctx.write_line("if (adt_out) strcpy(adt_out, _G_native_adt_ctrs_adt[_i]);")
                ctx.write_line("if (tag_out) *tag_out = _G_native_adt_ctrs_tag[_i];")
                ctx.write_line("if (tipo_out) strcpy(tipo_out, _G_native_adt_ctrs_tipo[_i]);")
                ctx.write_line("return 1;")
                ctx.dec_indent()
                ctx.write_line("}")
                ctx.dec_indent()
                ctx.write_line("}")
                ctx.write_line("return 0;")
                ctx.dec_indent()
                ctx.write_line("}")
                ctx.write_line("int _G_native_adt_unwrap_tipo(const char* adt, char* tipo_out) {")
                ctx.inc_indent()
                ctx.write_line("if (!adt || !tipo_out) return 0;")
                ctx.write_line("for (int _i = 0; _i < _G_native_adt_ctrs_count; _i++) {")
                ctx.inc_indent()
                ctx.write_line("if (_G_native_adt_ctrs_tag[_i] == 0 && strcmp(_G_native_adt_ctrs_adt[_i], adt) == 0) {")
                ctx.inc_indent()
                ctx.write_line("strcpy(tipo_out, _G_native_adt_ctrs_tipo[_i]);")
                ctx.write_line("return 1;")
                ctx.dec_indent()
                ctx.write_line("}")
                ctx.dec_indent()
                ctx.write_line("}")
                ctx.write_line("return 0;")
                ctx.dec_indent()
                ctx.write_line("}")
                ctx.write_line("int _G_native_adt_unwrap_field(const char* adt, char* field_out) {")
                ctx.inc_indent()
                ctx.write_line("if (!adt || !field_out) return 0;")
                ctx.write_line("// D-2: normalizar la base de una instanciacion (Resultado<entero,texto> -> Resultado)")
                ctx.write_line("char _ab[64]; int _ai = 0; for (; adt[_ai] && adt[_ai] != '<' && _ai < 62; _ai++) _ab[_ai] = adt[_ai]; _ab[_ai] = 0;")
                ctx.write_line("for (int _i = 0; _i < _G_native_adt_ctrs_count; _i++) {")
                ctx.inc_indent()
                ctx.write_line("if (_G_native_adt_ctrs_tag[_i] == 0 && strcmp(_G_native_adt_ctrs_adt[_i], _ab) == 0) {")
                ctx.inc_indent()
                ctx.write_line("strcpy(field_out, _G_native_adt_ctrs[_i]);")
                ctx.write_line("return 1;")
                ctx.dec_indent()
                ctx.write_line("}")
                ctx.dec_indent()
                ctx.write_line("}")
                ctx.write_line("return 0;")
                ctx.dec_indent()
                ctx.write_line("}")
                ctx.write_line("")
                # ME-D2: instanciaciones de ADT genericos (definiciones; paridad orquestador.syn)
                ctx.write_line("char _G_native_adt_gen[64][64];")
                ctx.write_line("int _G_native_adt_gen_nparams[64];")
                ctx.write_line("char _G_native_adt_gen_params[64][8][64];")
                ctx.write_line("int _G_native_adt_gen_count;")
                ctx.write_line("int _G_native_adt_gen_es(const char* n) {")
                ctx.inc_indent()
                ctx.write_line("if (!n) return 0;")
                ctx.write_line("for (int _i = 0; _i < _G_native_adt_gen_count; _i++) { if (strcmp(_G_native_adt_gen[_i], n) == 0) return 1; }")
                ctx.write_line("return 0;")
                ctx.dec_indent()
                ctx.write_line("}")
                ctx.write_line("char _G_native_adt_inst_type[64][64];")
                ctx.write_line("char _G_native_adt_inst_c[64][64];")
                ctx.write_line("char _G_native_adt_inst_base[64][64];")
                ctx.write_line("char _G_native_adt_inst_fields_c[64][8][64];")
                ctx.write_line("int _G_native_adt_inst_nfields[64];")
                ctx.write_line("int _G_native_adt_inst_count;")
                ctx.write_line("int _G_native_adt_inst_ctr(const char* base, int tag, const char* tipo_c, char* out) {")
                ctx.inc_indent()
                ctx.write_line("if (!base || !out) return 0;")
                ctx.write_line("int _solo = 1; int _ns = 0; for (int _j = 0; _j < _G_native_adt_inst_count; _j++) { if (strcmp(_G_native_adt_inst_base[_j], base) == 0) { _ns++; } }")
                ctx.write_line("if (_ns == 1) _solo = 1; else _solo = 0;")
                ctx.write_line("for (int _i = 0; _i < _G_native_adt_inst_count; _i++) {")
                ctx.inc_indent()
                ctx.write_line("if (strcmp(_G_native_adt_inst_base[_i], base) != 0) continue;")
                ctx.write_line("if (_solo) { strcpy(out, _G_native_adt_inst_c[_i]); return 1; }")
                ctx.write_line("if (tag < _G_native_adt_inst_nfields[_i] && tipo_c && _G_native_adt_inst_fields_c[_i][tag][0] && strcmp(_G_native_adt_inst_fields_c[_i][tag], tipo_c) == 0) { strcpy(out, _G_native_adt_inst_c[_i]); return 1; }")
                ctx.dec_indent()
                ctx.write_line("}")
                ctx.write_line("return 0;")
                ctx.dec_indent()
                ctx.write_line("}")
                ctx.write_line("")
                # ME-B7: dedup de funciones emitidas y hoisting de variables
                ctx.write_line("char _G_emit_func_names[2048][64];")
                ctx.write_line("int _G_emit_func_count;")
                ctx.write_line("char _G_fn_vars[2048][64];")
                ctx.write_line("int _G_fn_vars_count;")
                ctx.write_line("void* _G_fn_var_src[2048];")
                ctx.write_line("int _G_fn_var_auto[2048];")
                ctx.write_line("char _G_fn_var_tipos[2048][64];  // ME-C4: tipo inferido por hoisting")
                ctx.write_line("char _G_fn_ptr_vars[64][64];  // ME-B9.x: parametros puntero"
)
                ctx.write_line("int _G_fn_ptr_vars_count;")
                # F3-10: elemento (Canal<T>) de cada variable canal para el receive `ch ->`
                # (Manual 2 L144 / Manual 5 §4.2). Paridad orquestador nativo.
                ctx.write_line("char _G_native_canal_names[512][64];")
                ctx.write_line("char _G_native_canal_elem[512][64];")
                ctx.write_line("int _G_native_canal_count;")
                ctx.write_line("void _G_native_canal_elem_set(const char* _cname, const char* _celem) {")
                ctx.write_line("    if (!_cname || !_celem) return;")
                ctx.write_line("    for (int _ci = 0; _ci < _G_native_canal_count; _ci++) { if (strcmp(_G_native_canal_names[_ci], _cname) == 0) { strncpy(_G_native_canal_elem[_ci], _celem, 63); _G_native_canal_elem[_ci][63] = 0; return; } }")
                ctx.write_line("    if (_G_native_canal_count < 512) { strncpy(_G_native_canal_names[_G_native_canal_count], _cname, 63); _G_native_canal_names[_G_native_canal_count][63] = 0; strncpy(_G_native_canal_elem[_G_native_canal_count], _celem, 63); _G_native_canal_elem[_G_native_canal_count][63] = 0; _G_native_canal_count++; }")
                ctx.write_line("}")
                ctx.write_line("int _G_native_canal_elem_tipo(const char* _cname, char* _cout) {")
                ctx.write_line("    if (!_cname || !_cout) return 0;")
                ctx.write_line("    for (int _ci = 0; _ci < _G_native_canal_count; _ci++) { if (strcmp(_G_native_canal_names[_ci], _cname) == 0) { strncpy(_cout, _G_native_canal_elem[_ci], 63); _cout[63] = 0; return 1; } }")
                ctx.write_line("    return 0;")
                ctx.write_line("}")
                # F3-7: funciones listener de `escuchar` (Manual 2 L113) — paridad orquestador nativo
                ctx.write_line("char _G_listeners[8][16384];")
                ctx.write_line("int _G_listeners_count;")
                ctx.write_line("int _G_listener_modo;")
                # F4.4: wrappers de `lanzar` (fibras M:N, Manual 5 §2.6) acumulados y
                # flusheados antes del main (paridad orquestador.syn).
                ctx.write_line("char _G_lanzar_wrappers[8][4096];")
                ctx.write_line("int _G_lanzar_wrappers_count;")
                ctx.write_line("int _G_lanzar_count;")
                ctx.write_line("")
                # F5-1 (Manual 2 §5.1): garantiza globals del codegen (definidos
                # aqui, usados via asm() en funciones.syn/nodos_flujo.syn)
                ctx.write_line("void* _G_fn_garantizas_actuales = 0;")
                ctx.write_line("char _G_fn_ret_tipo_c[64];")
                ctx.write_line("")
                # ME-F1.2b: alias de tipo declarados (paridad orquestador nativo)
                ctx.write_line("char _G_tipo_aliases[128][64];")
                ctx.write_line("char _G_tipo_aliases_base[128][64];")
                ctx.write_line("int _G_tipo_aliases_count;")
                # R5 (F2-2.4c): senal de error de parseo (definicion en el modulo principal)
                ctx.write_line("int _G_parse_error = 0;")
                ctx.write_line("")
                ctx.write_line("")
                ctx.write_line("int _g_argc;")
                ctx.write_line("char** _g_argv;")
                ctx.write_line("int _argc() { return _g_argc; }")
                ctx.write_line("")
                ctx.write_line("CadenaSegura _argv(int i) {")
                ctx.inc_indent()
                ctx.write_line(
                    'if (i < 0 || i >= _g_argc) '
                    'return (CadenaSegura){0, ""};'
                )
                ctx.write_line(
                    "return (CadenaSegura){ .longitud = (int)strlen(_g_argv[i]),"
                    " .datos = _g_argv[i] };"
                )
                ctx.dec_indent()
                ctx.write_line("}")
                ctx.write_line("")
                ctx.write_line("void salir(int codigo) { exit(codigo); }")
                ctx.write_line("")
                ctx.write_line("CadenaSegura concat(CadenaSegura a, CadenaSegura b) {")
                ctx.inc_indent()
                ctx.write_line("int _tl = a.longitud + b.longitud;")
                ctx.write_line("char* _buf = (char*)malloc(_tl + 1);")
                ctx.write_line(
                    'if (!_buf) { fprintf(stderr,'
                    '"Error: malloc fallo en concat()\\\\n"); exit(1); }'
                )
                ctx.write_line("memcpy(_buf, a.datos, a.longitud);")
                ctx.write_line("memcpy(_buf + a.longitud, b.datos, b.longitud);")
                ctx.write_line("_buf[_tl] = 0;")
                ctx.write_line("return (CadenaSegura){_tl, _buf};")
                ctx.dec_indent()
                ctx.write_line("}")
                ctx.write_line("")
            # NO emitir structs \u2014 ya est\u00e1n definidos en el header compartido
            # Pre-pass lanzar y typedefs
            _preprocess_lanzar(ctx)
            ctx._contador_thread = 0
            for td in ctx._deferred_typedefs:
                ctx.write_line(td)
            for decl in ctx._deferred_wrap_decls:
                ctx.write_line(decl)
            if ctx._deferred_typedefs or ctx._deferred_wrap_decls:
                ctx.write_line("")
            # Cuerpos de funciones \u2014 solo las del alcance del m\u00f3dulo
            self._emit_cuerpos(ctx, scope_names)
            # Emitir main solo si este m\u00f3dulo tiene 'principal'
            self._emit_main(ctx, scope_names)
            return ctx.generar()

        # modo == 'completo' (comportamiento original)
        self._emit_cabecera_comun(ctx)

        # R17: typedefs de instanciaciones de ADT ANTES de los structs
        # (un campo que referencia una instancia emitida después rompía el C)
        _emitir_typedefs_instancias(ctx)

        # Manual 8 §8.2: orden alfabético estricto para estructuras
        estructuras = sorted(
            [s for s in ctx.programa.sentencias if isinstance(s, DefinicionEstructura)],
            key=lambda e: e.nombre
        )
        for s in estructuras:
            ctx.write_line(f"struct {s.nombre};")
        if estructuras:
            ctx.write_line("")
        for s in estructuras:
            visitar_estructura(ctx, s)

        # F1.2: typedefs de DeclaracionTipo (alias/ADT) tras las estructuras
        for s in ctx.programa.sentencias:
            if isinstance(s, DeclaracionTipo):
                visitar_declaracion_tipo(ctx, s)

        self._emit_prototipos_funciones(ctx)

        _preprocess_lanzar(ctx)
        ctx._contador_thread = 0
        for td in ctx._deferred_typedefs:
            ctx.write_line(td)
        for decl in ctx._deferred_wrap_decls:
            ctx.write_line(decl)
        if ctx._deferred_typedefs or ctx._deferred_wrap_decls:
            ctx.write_line("")

        self._emit_cuerpos(ctx)
        self._emit_main(ctx)

        return ctx.generar()

    @property
    def linker_flags(self) -> str:
        if self.ctx._linker_libs:
            return " " + " ".join(
                f"-l{lib}" for lib in self.ctx._linker_libs
            )
        return ""
