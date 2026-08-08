"""
Generación de código C para declaraciones: funciones, structs, variables,
declaraciones externas, asignaciones de campo, envío de canales, etc.
"""

from typing import Optional
from compilador.ast_nodes import (
    Nodo, DefinicionFuncion, DefinicionEstructura,
    DeclaracionVariable, AsignacionVariable, AsignacionCampo,
    DeclaracionExterna, ImportarC, StmtConstante,
    SentenciaEnviarCanal, SentenciaLanzar, SentenciaRecuperar,
    SentenciaRetornar, SentenciaEscuchar, SentenciaDelegar,
    BloqueInseguro, SentenciaExpr,
    ExprAsm, Identificador, LlamadaFuncion, ArgumentoTransferido,
    DeclaracionTipo,
)
from .context import GeneratorContext, MAPA_TIPOS_C
from .emit_expressions import (
    expr_a_c, tipo_de_expr,
)
from .emit_selfhost import (
    emitir_volcar_ast,
)


# FASE A (A4.5): retirada COMPLETA del espejo _P_* — el map ya NO enruta
# tokenizar/parsear a los emisores del espejo (emitir_parsear, la última emisora
# viva, se conserva solo como referencia del harness native_puente_paridad.py;
# emitir_tokenizar fue retirado en A4 por quedar sin uso).
# Paridad con el hook ME-B7 del orquestador nativo (nucleo/generador/orquestador.syn):
#   - tokenizar: NO se intercepta — se emite el cuerpo nativo de lexer.syn
#     (A4.5 fix: la supresion dejaba el unity SIN definicion de tokenizar).
#   - parsear: wrapper NATIVO (paridad literal con gen_emitir_frontend_nativo,
#     nucleo/generador/frontend_nativo.syn) — pipeline tokenizar -> parsear_nativo
#     -> puente_construir_programa. El espejo emitir_parsear quedaba ocultando
#     bugs del frontend nativo (asignacion de campo, T_TIPO, si inline).
#   - volcar_ast: utilidad de volcado (no es el espejo; se mantiene).
# I/O y tensor functions están en synapse_rt.o y se linkean.
# (No incluirlas aquí causa multiple-definition linker errors)
def _emitir_parsear_nativo(ctx: GeneratorContext, nodo: DefinicionFuncion):
    """A4.5: wrapper NATIVO de parsear (paridad gen_emitir_frontend_nativo)."""
    ctx.write_line("int _P_ntks = 0, _P_tpos = 0, _P_p_err = 0;")
    ctx.write_line("struct Programa parsear(CadenaSegura fuente) {")
    ctx.write_line("    int _nt = tokenizar(fuente);")
    ctx.write_line("    if (_nt < 0) { struct Programa _e = {0}; return _e; }")
    ctx.write_line("    struct ParserEst _pe = {0};")
    ctx.write_line("    parsear_nativo(&_pe);")
    ctx.write_line("    struct Programa* _pr = (struct Programa*)puente_construir_programa();")
    ctx.write_line("    if (!_pr) { struct Programa _e = {0}; return _e; }")
    ctx.write_line("    return *_pr;")
    ctx.write_line("}")


_BUILTIN_EMITTER_MAP = {
    'parsear': _emitir_parsear_nativo,
    'volcar_ast': emitir_volcar_ast,
}


def _visitar_stmt(ctx, nodo):
    """Import tardío para evitar ciclo."""
    from . import visitar as _v
    return _v(ctx, nodo)


# ================================================================
# Variable / assignment
# ================================================================

def visitar_declaracion(ctx: GeneratorContext, nodo: DeclaracionVariable):
    """Genera código C para declaración de variable. F1.2c: el tipo es opcional
    (`let x = 5`); se infiere de la expresión (Manual 2 §2 L134)."""
    tipo_syn = nodo.tipo
    if not tipo_syn:
        tipo_syn = tipo_de_expr(ctx, nodo.expresion) if nodo.expresion else 'int'
    tipo_c = ctx.traducir_tipo_c(tipo_syn)
    if nodo.expresion:
        val = expr_a_c(ctx, nodo.expresion)
        ctx.write_line(f"{tipo_c} {nodo.nombre} = {val};")
    else:
        ctx.write_line(f"{tipo_c} {nodo.nombre} = {{0}};")
    ctx._variables[nodo.nombre] = tipo_syn  # Store Synapse type (consistent)
    if tipo_syn == 'CanalConcurrencia*':
        ctx._canal_vars_concurrencia.add(nodo.nombre)
    elif tipo_syn == 'Canal':
        ctx._canal_vars.add(nodo.nombre)
    elif tipo_syn == 'Tensor':
        ctx._tensor_vars.add(nodo.nombre)


def visitar_delegar(ctx: GeneratorContext, nodo: SentenciaDelegar):
    """F1.2c: `delegar expr` == `retornar err(expr)` (Manual 2 §2 L132, Manual 3
    §7). Emite el patrón `?` de Resultado: si el tag es err, propaga el valor;
    si es ok, continúa (el valor se descarta)."""
    val = expr_a_c(ctx, nodo.expresion)
    ctx.write_line("{")
    ctx.write_line(f"    Resultado _del = {val};")
    ctx.write_line("    if (_del.tag == 1) return _del;")
    ctx.write_line("}")



def visitar_asignacion(ctx: GeneratorContext, nodo: AsignacionVariable):
    """Genera código C para asignación (con/sin declaración implícita)."""
    tipo_syn = tipo_de_expr(ctx, nodo.expresion)  # Synapse type
    tipo_c = ctx.traducir_tipo_c(tipo_syn)  # C type for output
    val = expr_a_c(ctx, nodo.expresion)
    desde_llamada = isinstance(nodo.expresion, type(None)) is False and hasattr(
        nodo.expresion, 'nombre'
    )
    if nodo.nombre not in ctx._variables:
        ctx._variables[nodo.nombre] = tipo_syn  # Store Synapse type
        ctx.write_line(f"{tipo_c} {nodo.nombre} = {val};")
        if tipo_syn == 'Tensor':
            ctx._tensor_vars.add(nodo.nombre)
        elif tipo_syn == 'Canal':
            ctx._canal_vars.add(nodo.nombre)
        elif tipo_syn == 'CanalConcurrencia*':
            ctx._canal_vars_concurrencia.add(nodo.nombre)
        else:
            ctx.register_var(nodo.nombre, tipo_syn, desde_llamada)
    else:
        old_tipo = ctx._variables.get(nodo.nombre)
        if old_tipo in ctx._destructor_map:
            dtor = ctx._destructor_map[old_tipo]
            ctx.write_line(f"{dtor}({nodo.nombre});")
            ctx.unregister_var(nodo.nombre)
        if nodo.nombre in ctx._tensor_vars and tipo_syn == 'Tensor':
            ctx.write_line(f"{ctx.syn_free(f'{nodo.nombre}.datos')};")
        if tipo_syn == 'CanalConcurrencia*':
            ctx._canal_vars_concurrencia.add(nodo.nombre)
        ctx.write_line(f"{nodo.nombre} = {val};")


# ================================================================
# Struct definition
# ================================================================

def visitar_estructura(ctx: GeneratorContext, nodo: DefinicionEstructura):
    """Genera código C para definición de estructura.
    Skopea solo los 4 tipos ya definidos en el header (Token, Nodo, ListaNodo, Programa).
    El resto de tipos OO necesitan definiciones completas para sizeof() y
    declaraciones de variables en el código C auto-hospedado.
    """
    campos_pointer = set()
    for c in nodo.campos:
        if c.tipo in ctx._estructuras or c.tipo == nodo.nombre:
            campos_pointer.add(c.nombre)
    es_adt = any(
        c.nombre == 'tag' and c.tipo in ('entero', 'int')
        for c in nodo.campos
    )
    ctx._estructuras[nodo.nombre] = {
        'campos': [(c.nombre, c.tipo) for c in nodo.campos],
        'campos_pointer': campos_pointer,
        'es_adt': es_adt,
    }
    # Solo skipear los 4 tipos con definición completa en el header
    if nodo.nombre in ctx._HEADER_DEFINED_TYPES:
        return
    ctx.write_line(f"typedef struct {nodo.nombre} {{")
    ctx.inc_indent()
    if es_adt:
        for c in nodo.campos:
            if c.nombre == 'tag' and c.tipo in ('entero', 'int'):
                ctx.write_line("int tag;")
                break
        ctx.write_line("union {")
        ctx.inc_indent()
        for c in nodo.campos:
            if c.nombre == 'tag' and c.tipo in ('entero', 'int'):
                continue
            if c.nombre in campos_pointer:
                ctx.write_line(f"struct {c.tipo}* {c.nombre};")
            else:
                tipo_c = MAPA_TIPOS_C.get(c.tipo)
                if tipo_c is not None:
                    ctx.write_line(f"{tipo_c} {c.nombre};")
                else:
                    ctx.write_line(f"struct {c.tipo}* {c.nombre};")
        ctx.dec_indent()
        ctx.write_line("} dato;")
    else:
        for c in nodo.campos:
            if c.nombre in campos_pointer:
                ctx.write_line(f"struct {c.tipo}* {c.nombre};")
            elif c.nombre in ctx._ARRAY_OVERRIDE_FIELDS:
                arr_base, arr_size = ctx._ARRAY_OVERRIDE_FIELDS[c.nombre]
                ctx.write_line(f"{arr_base} {c.nombre}[{arr_size}];")
            else:
                tipo_c = ctx.traducir_tipo_c(c.tipo)
                ctx.write_line(f"{tipo_c} {c.nombre};")
    ctx.dec_indent()
    ctx.write_line(f"}} {nodo.nombre};")
    ctx.write_line("")


# ================================================================
# Type declaration (Manual 2 §2 declaracion_tipo / §4.2)
# ================================================================

def visitar_declaracion_tipo(ctx: GeneratorContext, nodo: DeclaracionTipo):
    """F1.2: emite el typedef de una declaración de tipo.
    - Alias simple (`tipo X = entero`): `typedef <c> X;`
    - Tipo algebraico (`tipo X = ok(entero) | err(texto)`): tagged union
      `typedef struct X { int64_t tag; union {...} dato; } X;` compatible con
      visitar_coincidir (switch sobre .tag + TAG_*) y ExprAccesoCampo (.dato.).
    El registro de ctx._tipo_aliases / ctx._estructuras lo hace el pre-pass
    de GeneradorC.generar() (antes de prototipos/uso).
    """
    if nodo.constructores:
        partes = []
        for c in nodo.constructores:
            if not c.tipos:
                continue
            tipo_campo = c.tipos[0]
            # placeholder para parámetros de tipo no instanciados (T, E)
            if tipo_campo in nodo.parametros_tipo:
                tipo_campo = 'puntero'
            tipo_c = ctx.traducir_tipo_c(tipo_campo)
            if tipo_c.startswith('struct '):
                tipo_c += '*'
            partes.append(f"{tipo_c} {c.nombre};")
        if not partes:
            partes.append("int _unidad;")
        td = (f"typedef struct {nodo.nombre} {{ int64_t tag; "
              f"union {{ {' '.join(partes)} }} dato; }} {nodo.nombre};")
        if td not in ctx._emitted_typedefs:
            ctx._emitted_typedefs.add(td)
            ctx.write_line(td)
            ctx.write_line("")
    elif nodo.tipo_base:
        td = f"typedef {ctx.traducir_tipo_c(nodo.tipo_base)} {nodo.nombre};"
        if td not in ctx._emitted_typedefs:
            ctx._emitted_typedefs.add(td)
            ctx.write_line(td)
            ctx.write_line("")


# ================================================================
# Import, extern, constants
# ================================================================

def visitar_import_c(ctx: GeneratorContext, nodo: ImportarC):
    """Genera código C para #include."""
    if nodo.es_sistema:
        ctx.write_line(f'#include <{nodo.ruta}>')
        if nodo.ruta == 'winsock2.h':
            ctx._linker_libs.add('ws2_32')
    else:
        ctx.write_line(f'#include "{nodo.ruta}"')


def visitar_externa(ctx: GeneratorContext, nodo: DeclaracionExterna):
    """Genera código C para declaración externa de función."""
    ctx._externas[nodo.nombre] = [p.tipo for p in nodo.parametros]
    if not ctx._in_function_scope:
        tipo_ret_c = (
            ctx.traducir_tipo_c(nodo.tipo_retorno.replace('*', ''))
            + ('*' if '*' in nodo.tipo_retorno else '')
        )
        params_c_parts = []
        for p in nodo.parametros:
            base_tipo = p.tipo.replace('*', '')
            es_puntero = '*' in p.tipo
            tipo_c = ctx.traducir_tipo_c(base_tipo)
            if es_puntero:
                tipo_c += '*'
            params_c_parts.append(f"{tipo_c} {p.nombre}")
        params_c = ", ".join(params_c_parts) if params_c_parts else "void"
        ctx.write_line(f"extern {tipo_ret_c} {nodo.nombre}({params_c});")


def visitar_constante(ctx: GeneratorContext, nodo: StmtConstante):
    """Genera código C para constante (#define o const)."""
    valor_c = expr_a_c(ctx, nodo.valor)
    tipo_inferido = nodo.tipo if nodo.tipo else tipo_de_expr(ctx, nodo.valor)
    tipo_c = ctx.traducir_tipo_c(tipo_inferido or 'int')
    if not ctx._in_function_scope:
        ctx.write_line(f"#define {nodo.nombre} ({valor_c})")
    else:
        ctx.write_line(f"const {tipo_c} {nodo.nombre} = {valor_c};")
    # Store Synapse type for consistency with tipo_de_expr
    ctx._const_types[nodo.nombre] = tipo_inferido or 'int'


# ================================================================
# Field assignment
# ================================================================

def visitar_asignacion_campo(ctx: GeneratorContext, nodo: AsignacionCampo):
    """Genera código C para asignación a campo de struct."""
    if not ctx._in_function_scope:
        raise SyntaxError(
            f"Asignación de campo fuera de ámbito global (linea {nodo.linea})"
        )
    obj = expr_a_c(ctx, nodo.objeto)
    val = expr_a_c(ctx, nodo.expresion)
    obj_tipo = tipo_de_expr(ctx, nodo.objeto)
    es_puntero = obj_tipo.endswith('*')
    nombre_struct = ''
    if not es_puntero and obj_tipo.startswith('struct '):
        nombre_struct = obj_tipo[7:]
    sep = '->' if es_puntero else '.'
    es_adt = bool(ctx._estructuras.get(nombre_struct, {}).get('es_adt'))
    campo_es_tag = (nodo.nombre_campo == 'tag' and es_adt)
    if es_adt and not campo_es_tag:
        ctx.write_line(f"{obj}{sep}dato.{nodo.nombre_campo} = {val};")
    else:
        ctx.write_line(f"{obj}{sep}{nodo.nombre_campo} = {val};")


# ================================================================
# Channel send
# ================================================================

def visitar_enviar_canal(ctx: GeneratorContext, nodo: SentenciaEnviarCanal):
    """Genera código C para envío a canal."""
    canal = expr_a_c(ctx, nodo.canal)
    valor = expr_a_c(ctx, nodo.valor)
    tipo_valor = tipo_de_expr(ctx, nodo.valor)
    if tipo_valor == 'int':
        ctx.write_line(f"canal_enviar({canal}, {ctx.prim_int_to_ptr(valor)});")
    elif tipo_valor == 'float':
        ctx.write_line(
            f"canal_enviar({canal}, {ctx.prim_float_to_ptr(valor)});"
        )
    else:
        ctx.write_line(f"canal_enviar({canal}, (void*)({valor}));")
    if (
        isinstance(nodo.valor, Identificador)
        and tipo_valor in ctx._destructor_map
    ):
        ctx.write_line(f"{valor} = ({{0}});")
        ctx.unregister_var(nodo.valor.nombre)


# ================================================================
# Function definition (main visitor)
# ================================================================

def visitar_funcion(ctx: GeneratorContext, nodo: DefinicionFuncion):
    """Genera código C para definición de función."""
    if nodo.nombre in ctx._funciones_emitidas:
        return
    ctx._funciones_emitidas.add(nodo.nombre)

    # Builtins: emitir implementación C inline
    # Check emitter map FIRST (includes self-hosting emitters)
    if nodo.nombre in _BUILTIN_EMITTER_MAP:
        _BUILTIN_EMITTER_MAP[nodo.nombre](ctx, nodo)
        return
    # Skip runtime builtins (linked from synapse_rt.o)
    if nodo.nombre in ctx._RUNTIME_BUILTINS:
        return

    ctx._in_function_scope = True
    ctx._variables = {}
    ctx._tensor_vars = set()
    ctx._tensor_vars_transferidas = set()
    ctx._canal_vars = set()
    ctx._canal_vars_cerradas = set()
    ctx._canal_vars_concurrencia = set()
    ctx._strings_heap = set()
    ctx._consumed_vars = set()

    # Register parameters (store Synapse type for consistency with tipo_de_expr)
    for p in nodo.parametros:
        if p.tipo in ctx._POINTER_TYPES:
            ctx._variables[p.nombre] = p.tipo + '*'
        else:
            ctx._variables[p.nombre] = p.tipo

    ctx._current_func_return_type = nodo.tipo_retorno
    tipo = ctx.traducir_tipo_c(nodo.tipo_retorno)
    params = ", ".join(
        f"{ctx.traducir_tipo_c(p.tipo)}{'*' if p.tipo in ctx._POINTER_TYPES else ''} {p.nombre}"
        for p in nodo.parametros
    ) if nodo.parametros else "void"
    ctx.write_line(f"{tipo} {nodo.nombre}({params}) {{")
    ctx.inc_indent()
    ctx.push_scope()

    # Register transfer parameters
    for p in nodo.parametros:
        if p.es_transferencia:
            if p.tipo in ctx._destructor_map:
                ctx._scope_stack[-1][p.nombre] = p.tipo

    # Contract requires → asserts
    for expr in nodo.requiere:
        expr_c = expr_a_c(ctx, expr)
        ctx.write_line("#ifndef SYNAPSE_RELEASE")
        ctx.write_line(f'assert(({expr_c}) && "Fallo en contrato: requiere");')
        ctx.write_line("#endif")

    ctx._garantizas_actuales = nodo.garantiza

    # Pre-pass: hoist variable declarations
    _explicit_vars = set()
    _auto_vars = []  # (nombre, tipo_syn) - variables auto-declaradas izadas al scope funcion
    def _collect_vars(stmts):
        for s in stmts:
            if isinstance(s, DeclaracionVariable):
                _explicit_vars.add(s.nombre)
            elif (
                isinstance(s, AsignacionVariable)
                and s.nombre not in ctx._variables
                and s.nombre not in _explicit_vars
            ):
                t_syn = tipo_de_expr(ctx, s.expresion)  # Synapse type
                # Hoist ALL auto-declared variables to function scope
                _auto_vars.append((s.nombre, t_syn))
                ctx._variables[s.nombre] = t_syn
            if isinstance(s, BloqueInseguro):
                _collect_vars(s.cuerpo)
            elif hasattr(s, 'cuerpo') and isinstance(
                getattr(s, 'cuerpo'), list
            ):
                _collect_vars(s.cuerpo)
            if hasattr(s, 'cuerpo_sino') and s.cuerpo_sino:
                _collect_vars(s.cuerpo_sino)

    _collect_vars(nodo.cuerpo)
    for vn, vt_syn in _auto_vars:
        vt_c = ctx.traducir_tipo_c(vt_syn)  # C type for output
        # Zero-initialize if type has destructor (evita _syn_texto_liberar() en garbage)
        if vt_syn in ctx._destructor_map:
            ctx.write_line(f"{vt_c} {vn} = {{0}};")
        else:
            ctx.write_line(f"{vt_c} {vn};")

    # Inyectar _simd_detectar() al inicio de principal() para diagnóstico SIMD
    if nodo.nombre == 'principal' and not ctx.is_no_std():
        ctx.write_line("_simd_detectar();")

    for s in nodo.cuerpo:
        _visitar_stmt(ctx, s)

    # Garantiza assertions at function exit (implicit return in void)
    if nodo.tipo_retorno == "nada" or nodo.tipo_retorno == "":
        for expr in ctx._garantizas_actuales:
            expr_c = expr_a_c(ctx, expr)
            ctx.write_line("#ifndef SYNAPSE_RELEASE")
            ctx.write_line(f'assert(({expr_c}) && "Fallo en contrato: garantiza (final)");')
            ctx.write_line("#endif")

    # Tensor cleanup
    for var in ctx._tensor_vars:
        if var not in ctx._tensor_vars_transferidas:
            ctx.write_line(
                f"if (!{var}.es_mapeado) "
                f"{{ {ctx.syn_pool_free(f'{var}.datos')}; }}"
            )
    # Canal cleanup (IO struct)
    for var in ctx._canal_vars:
        if var not in ctx._canal_vars_cerradas:
            ctx.write_line(
                f"if ({var}.stream) {{ fclose({var}.stream); "
                f"{var}.es_valido = 0; }}"
            )
    # CanalConcurrencia cleanup (concurrency channels)
    for var in ctx._canal_vars_concurrencia:
        ctx.write_line(f"canal_destruir({var});")

    ctx.pop_scope()
    ctx._tensor_vars.clear()
    ctx._tensor_vars_transferidas.clear()
    ctx._canal_vars.clear()
    ctx._canal_vars_cerradas.clear()
    ctx._canal_vars_concurrencia.clear()
    ctx._garantizas_actuales = []
    ctx._in_function_scope = False
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")


# ================================================================
# Statements: return, spawn, recover, listen
# ================================================================

def visitar_retornar(ctx: GeneratorContext, nodo: SentenciaRetornar):
    """Genera código C para return, con variable temporal + destructores.
    Usa el tipo de retorno declarado de la función actual (_current_func_return_type)
    en vez del tipo inferido de la expresión (más robusto para self-hosting).
    """
    excl = ''
    if nodo.expr and isinstance(nodo.expr, Identificador):
        excl = nodo.expr.nombre
        ctx._tensor_vars_transferidas.add(excl)

    # Garantiza assertions before every return
    for expr in ctx._garantizas_actuales:
        expr_c = expr_a_c(ctx, expr)
        ctx.write_line("#ifndef SYNAPSE_RELEASE")
        ctx.write_line(f'assert(({expr_c}) && "Fallo en contrato: garantiza");')
        ctx.write_line("#endif")
    
    if nodo.expr:
        ret_tipo_syn = ctx._current_func_return_type  # Use declared return type
        ret_tipo_c = ctx.traducir_tipo_c(ret_tipo_syn)  # C type for output
        ret_expr = expr_a_c(ctx, nodo.expr)
        if nodo.es_transferencia:
            temp = f"_ret_{nodo.linea or 0}"
            ctx.write_line(f"{ret_tipo_c} {temp} = {ret_expr};")
            ctx.emit_all_destructors(exclude_var=excl)
            ctx.write_line(f"return ->{temp};")
        else:
            ctx.emit_all_destructors(exclude_var=excl)
            ctx.write_line(f"return {ret_expr};")
    else:
        ctx.emit_all_destructors(exclude_var=excl)
        ctx.write_line("return;")


def visitar_lanzar(ctx: GeneratorContext, nodo: SentenciaLanzar):
    """Genera código C para spawn/lanzar (crear hilo) con ownership transfer.

    C99 strict: usa wrapper static top-level + struct args con pool allocator (_syn_malloc/_syn_free)
    para evitar desajustes de ciclo de vida heap entre hilo principal e hijo.
    El wrapper se emite como funcion static al final del archivo via _deferred_wrappers.
    """
    ctx._contador_thread += 1
    tid = ctx._contador_thread

    if isinstance(nodo.llamada, LlamadaFuncion):
        fn_name = nodo.llamada.nombre
        args = nodo.llamada.argumentos

        if args:
            # Construir struct args + wrapper top-level
            arg_type_names = []
            arg_c_exprs = []
            for i, arg in enumerate(args):
                if isinstance(arg, ArgumentoTransferido) and isinstance(arg.expr, Identificador):
                    var_name = arg.expr.nombre
                    arg_t = ctx._variables.get(var_name, 'void*')
                    arg_type_names.append(ctx.traducir_tipo_c(arg_t))
                    arg_c_exprs.append(var_name)
                    ctx.unregister_var(var_name)
                else:
                    arg_expr_c = expr_a_c(ctx, arg)
                    arg_t = tipo_de_expr(ctx, arg)
                    arg_type_names.append(ctx.traducir_tipo_c(arg_t))
                    arg_c_exprs.append(arg_expr_c)

            args_type_name = f"_args_{tid}_t"
            wrapper_name = f"_wrap_{tid}"

            # Typedef (emitido antes del cuerpo de la funcion actual)
            # Evitar duplicados via _emitted_typedefs
            fields_str = " ".join(f"{tn} v{i};" for i, tn in enumerate(arg_type_names))
            typedef_line = f"typedef struct {{ {fields_str} }} {args_type_name};"
            if typedef_line not in ctx._emitted_typedefs:
                ctx._deferred_typedefs.append(typedef_line)
                ctx._emitted_typedefs.add(typedef_line)

            # Forward declaration del wrapper (evitar duplicados)
            wrap_decl = f"static void* {wrapper_name}(void* arg);"
            if wrap_decl not in ctx._emitted_wrap_decls:
                ctx._deferred_wrap_decls.append(wrap_decl)
                ctx._emitted_wrap_decls.add(wrap_decl)

            # Wrapper body: liberar ARGS inmediatamente despues de desempaquetar
            # y ANTES de ejecutar el bloque logico de usuario (propiedad estricta).
            # Se usa pool_alloc/pool_free para mantener compatibilidad con el runtime
            # (malloc/free directo causa segfault en hilos por desajuste de ciclo de vida).
            wrap_lines = [f"static void* {wrapper_name}(void* _arg) {{"]
            wrap_lines.append(f"    {args_type_name}* _a = ({args_type_name}*)_arg;")
            wrap_lines.append(f"    {ctx.syn_pool_free('_arg')};")
            unpacked = ", ".join(f"_a->v{i}" for i in range(len(args)))
            wrap_lines.append(f"    {fn_name}({unpacked});")
            wrap_lines.append(f"    return NULL;")
            wrap_lines.append(f"}}")
            ctx._deferred_wrappers.append("\n".join(wrap_lines))

            # Call-site: usar pool_alloc con tamaño exacto (pool_alloc ahora acepta
            # size_t size y deriva a malloc si el tamaño excede el bloque del pool).
            ctx.write_line(f"{args_type_name}* _args_{tid} = ({args_type_name}*){ctx.syn_pool_alloc(f'sizeof({args_type_name})')};")
            for i, expr_c in enumerate(arg_c_exprs):
                ctx.write_line(f"_args_{tid}->v{i} = {expr_c};")
            ctx.write_line(f"synapse_lanzar_hilo({wrapper_name}, _args_{tid});")
        else:
            # Sin argumentos: pasar funcion directamente
            ctx.write_line(
                f"synapse_lanzar_hilo("
                f"(void*(*)(void*)){fn_name}, NULL);"
            )
    else:
        # No es LlamadaFuncion (expresion directa)
        fn = expr_a_c(ctx, nodo.llamada)
        ctx.write_line(
            f"synapse_lanzar_hilo("
            f"(void*(*)(void*)){fn}, NULL);"
        )


def visitar_recuperar(ctx: GeneratorContext, nodo: SentenciaRecuperar):
    """Genera código C para try/recover."""
    accion = expr_a_c(ctx, nodo.accion_critica)
    plan_b = expr_a_c(ctx, nodo.plan_b)
    ctx.write_line("{")
    ctx.inc_indent()
    ctx.write_line(f"if ({accion} != 0) {{ {plan_b}; }}")
    ctx.dec_indent()
    ctx.write_line("}")


def visitar_escuchar(ctx: GeneratorContext, nodo: SentenciaEscuchar):
    """Genera código C para listen/escuchar (canal listener).
    Crea una función listener en background y lanza un hilo.
    """
    canal = expr_a_c(ctx, nodo.canal)
    respuesta = expr_a_c(ctx, nodo.respuesta)
    ctx._contador_listener += 1
    listener_name = f"_listener_{ctx._contador_listener}"
    
    # Build complete listener function as single string
    listener_lines = [
        f"void* {listener_name}(void* arg) {{",
        f"    (void)arg;",
        f"    CanalConcurrencia* _canal = (CanalConcurrencia*){canal};",
        f"    while (1) {{",
        f"        void* _msg = canal_recibir(_canal);",
        f"        if (!_msg) break;",
        f"        {respuesta}(_msg);",
        f"    }}",
        f"    return NULL;",
        f"}}",
    ]
    ctx._listener_funciones.append("\n".join(listener_lines))
    
    # Spawn listener thread inline
    ctx.write_line(
        f"synapse_lanzar_hilo("
        f"(void*(*)(void*)){listener_name}, NULL);"
    )
