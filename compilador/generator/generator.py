import re

from compilador.ast_nodes import (
    Nodo, Programa,
    DefinicionFuncion, DefinicionEstructura,
    SentenciaSi, SentenciaMientras, SentenciaPara,
    SentenciaLanzar, SentenciaRecuperar,
    SentenciaRetornar, SentenciaEscuchar,
    SentenciaRomper, SentenciaSiguiente,
    SentenciaExpr, DeclaracionVariable,
    AsignacionVariable, AsignacionCampo, LogLlamada,
    BloqueInseguro, NodoCoincidir,
    ImportarC, DeclaracionExterna, StmtConstante,
    SentenciaEnviarCanal,
    ExprAsm,
)
from .context import GeneratorContext
from .emit_control import visitar_si, visitar_mientras, visitar_para, visitar_coincidir
from .emit_declarations import (
    visitar_funcion, visitar_estructura,
    visitar_declaracion, visitar_asignacion,
    visitar_asignacion_campo, visitar_enviar_canal,
    visitar_import_c, visitar_externa, visitar_constante,
    visitar_retornar, visitar_lanzar, visitar_recuperar, visitar_escuchar,
)
from .emit_expressions import (
    expr_a_c, tipo_de_expr, visitar_log,
)
from .emit_contracts import emit_contract_header


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
            if isinstance(nodo.llamada, LlamadaFuncion):
                args = nodo.llamada.argumentos
                if args:
                    ctx._contador_thread += 1
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
                    wd_line = f"static void* {wrapper_name}(void* arg);"
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

    for s in ctx.programa.sentencias:
        _scan_node(s)


def _extract_listener_name(func_str: str) -> str:
    m = re.search(r'\*\s+(\w+)\s*\(', func_str)
    if m:
        return m.group(1)
    return ''


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
    elif isinstance(nodo, LogLlamada):
        visitar_log(ctx, nodo)
    elif isinstance(nodo, AsignacionCampo):
        visitar_asignacion_campo(ctx, nodo)
    elif isinstance(nodo, SentenciaEnviarCanal):
        visitar_enviar_canal(ctx, nodo)
    elif isinstance(nodo, DefinicionEstructura):
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
    """Emite #define T_* desde TokenID enum (Manual 2 §2.3)."""
    from compilador.ast_nodes import TokenID
    _T_MAP = {
        'IF':'T_IF','ELSE':'T_ELSE','FUNCTION':'T_FUNCION','RETURN':'T_RETORNAR',
        'SPAWN':'T_LANZAR','RECOVER':'T_RECUPERAR','LISTEN':'T_ESCUCHAR',
        'WHILE':'T_MIENTRAS','IMPORT':'T_IMPORTAR','STRUCT':'T_ESTRUCTURA',
        'BREAK':'T_ROMPER','CONTINUE':'T_SIGUIENTE','AND':'T_Y','OR':'T_O',
        'NOT':'T_NO','TRUE':'T_VERDADERO','FALSE':'T_FALSO',
        'IDENTIFIER':'T_IDENTIFICADOR','NUMBER':'T_NUMERO','FLOAT':'T_FLOTANTE',
        'STRING':'T_CADENA','GREATER':'T_MAYOR','LESS':'T_MENOR',
        'EQUALS':'T_IGUAL','NOT_EQUALS':'T_DISTINTO','LESS_EQUALS':'T_MENOR_IGUAL',
        'GREATER_EQUALS':'T_MAYOR_IGUAL','ASSIGN':'T_ASIGNAR','PLUS':'T_MAS',
        'MINUS':'T_MENOS','STAR':'T_POR','SLASH':'T_DIV','MODULO':'T_MOD',
        'ARROW':'T_FLECHA','MATCH':'T_COINCIDIR','ARROW_RIGHT':'T_FLECHA_DER',
        'LPAREN':'T_PAREN_IZQ','RPAREN':'T_PAREN_DER','COLON':'T_DOSPUNTOS',
        'COMMA':'T_COMA','NEWLINE':'T_NUEVALINEA','INDENT':'T_INDENTAR',
        'DEDENT':'T_DESINDENTAR','AMPERSAND':'T_AMPERSAND','INSEGURO':'T_INSEGURO',
        'IMPORTAR_C':'T_IMPORTAR_C','EXTERNO':'T_EXTERNO','ARROW_LEFT':'T_FLECHA_IZQ',
        'REQUIERE':'T_REQUIERE','GARANTIZA':'T_GARANTIZA','CANAL':'T_CANAL',
        'ASM':'T_ASM','CONSTANTE':'T_CONSTANTE','SEMICOLON':'T_PUNTOCOMA',
        'PARA':'T_PARA','LBRACKET':'T_CORCH_IZQ','RBRACKET':'T_CORCH_DER',
        'EOF':'T_FIN','DOT':'T_PUNTO',
    }
    ctx.write_line("// --- Token ID constants (Manual 2 §2.3) ---")
    for name in TokenID._member_names_:
        cname = _T_MAP.get(name, f'T_{name}')
        val = TokenID[name].value
        ctx.write_line(f"#define {cname} ({val})")
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
    ]
    ctx.write_line("// --- Nodo type constants (AST node types) ---")
    for name, val in NODOS:
        ctx.write_line(f"#define {name} ({val})")
    ctx.write_line("")


def _emitir_error_defines(ctx: GeneratorContext):
    """Emite #define ERR_* desde ErrorCodes enum + extras de nucleo/diagnostics.syn."""
    from compilador.diagnostics import ErrorCodes
    ctx.write_line("// --- Error code constants (Manual 3 §3.5) ---")
    for name in ErrorCodes._member_names_:
        val = ErrorCodes[name].value
        ctx.write_line(f"#define {name} ({val})")
    # Extras from self-hosted diagnostics.syn (not in Python ErrorCodes)
    ctx.write_line("#define ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED (33)")
    ctx.write_line("#define ERR_MEM_LIFETIME_MISMATCH (34)")
    ctx.write_line("#define ERR_MEM_LIFETIME_CYCLE (35)")
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
        ctx.write_line("#include <pthread.h>")
        ctx.write_line("#include <string.h>")
        ctx.write_line("#include <assert.h>")
    else:
        ctx.write_line("#include <stdint.h>")
        ctx.write_line("#include <stddef.h>")
    ctx.write_line("")
    ctx.write_line(
        "typedef struct { int longitud; const char* datos; } CadenaSegura;"
    )
    ctx.write_line("")
    ctx.write_line(
        "typedef struct { uint32_t filas; uint32_t columnas; "
        "float* datos; } Tensor;"
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
    # Emit T_*, NODO_*, ERR_* constants for modular compilation
    _emitir_token_defines(ctx)
    _emitir_nodo_defines(ctx)
    _emitir_error_defines(ctx)
    # NOTA: _syn_* y _toml_* externs ya estan en #include "librerias/embedded_libs.h"
    ctx.write_line("extern char _gen_tmp_buf[4096];")
    ctx.write_line("")
    ctx.write_line("extern char _G_emit_buf[1048576];")
    ctx.write_line("extern int _G_emit_pos;")
    ctx.write_line("extern FILE* _G_fp;")
    ctx.write_line("")
    ctx.write_line("// PGO variables (defined in self-hosted parser module)")
    ctx.write_line("extern int _P_ntks, _P_tpos, _P_p_err;")
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
        ctx.write_line("static inline void* _synapse_box_int(int v) "
            "{ return (void*)(intptr_t)v; }"
        )
        ctx.write_line(
            "static inline int _synapse_unbox_int(void* p) "
            "{ return (int)(intptr_t)p; }"
        )
        ctx.write_line(
            "static inline void* _synapse_box_float(float v) {"
        )
        ctx.inc_indent()
        ctx.write_line("float* _p = (float*)malloc(sizeof(float));")
        ctx.write_line(
            'if (!_p) { fprintf(stderr, '
            '"ESCAPA_DEL_ALCANCE: malloc fallo\\\\n"); exit(1); }'
        )
        ctx.write_line("*_p = v;")
        ctx.write_line("return (void*)_p;")
        ctx.dec_indent()
        ctx.write_line("}")
        ctx.write_line(
            "static inline float _synapse_unbox_float(void* p) {"
        )
        ctx.inc_indent()
        ctx.write_line("float _v = *(float*)p;")
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
            "void cerrar(Canal canal)",
            "Tensor crear_tensor(int filas, int columnas)",
            "Tensor suma_tensor(Tensor a, Tensor b)",
            "Tensor producto_punto(Tensor a, Tensor b)",
            "Tensor relu(Tensor a)",
            "Tensor reserva(int tamano)",
            "void libera(Tensor bloque)",
            "Tensor suma(Tensor a, Tensor b)",
            "Tensor producto(Tensor a, Tensor b)",
            "int texto_a_entero(CadenaSegura str)",
            "float texto_a_decimal(CadenaSegura str)",
            "CadenaSegura decimal_a_texto(float n)",
            "CadenaSegura entero_a_texto(int n)",
            "int str_eq(CadenaSegura a, CadenaSegura b)",
            "void synapse_lanzar_hilo(void* (*fn)(void*), void* arg)",
            "void synapse_esperar_hilos(void)",
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
            "void* canal_recibir(CanalConcurrencia* canal)",
            "void canal_destruir(CanalConcurrencia* canal)",
            "void cerrar_canal(CanalConcurrencia* canal)",
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
            'tokenizar': 'int tokenizar(CadenaSegura fuente)',
            'parsear': 'struct Programa parsear(CadenaSegura fuente)',
            'volcar_ast': 'void volcar_ast(struct Nodo* nodo, int nivel)',
            'generar': 'int generar(struct Programa programa, CadenaSegura ruta)',
        }
        # Manual 8 §8.2: orden alfabético estricto por nombre
        funciones = sorted(
            [s for s in ctx.programa.sentencias if isinstance(s, DefinicionFuncion) and s.nombre not in ctx._RUNTIME_BUILTINS],
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
            else:
                ctx.write_line(f"return {principal}();")
            ctx.write_line("synapse_esperar_hilos();")
            ctx.write_line("pool_destroy();")
            ctx.write_line("return 0;")
            ctx.dec_indent()
            ctx.write_line("}")

    def _emit_cuerpos(self, ctx, scope_names: set[str] | None = None):
        """Helper: emite cuerpos de funciones + listeners + wrappers.
        Manual 8 §8.2: orden alfabético estricto por nombre para funciones.
        Si scope_names no es None, solo emite funciones cuyos nombres estén en el conjunto."""
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
        for s in ctx.programa.sentencias:
            if isinstance(s, DefinicionFuncion):
                continue
            if scope_names is not None and hasattr(s, 'nombre') and getattr(s, 'nombre', None) not in scope_names:
                continue
            visitar(ctx, s)
        # Functions en orden alfabético
        for s in funciones:
            visitar(ctx, s)
        for func in ctx._listener_funciones:
            name = _extract_listener_name(func)
            if name:
                ctx.write_line(f"extern void* {name}(void* arg);")
        if ctx._listener_funciones:
            ctx.write_line("")
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

        for s in ctx.programa.sentencias:
            if isinstance(s, DefinicionFuncion):
                ctx._func_return_types[s.nombre] = s.tipo_retorno
                ctx._func_param_types[s.nombre] = [p.tipo for p in s.parametros]
            elif isinstance(s, DeclaracionExterna):
                ctx._func_return_types[s.nombre] = s.tipo_retorno

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

        if modo == 'header':
            # Solo cabecera: #includes, tipos, prototipos + extern declarations
            # IMPORTANTE: NO llamar _emit_cabecera_comun (emite DEFINICIONES _g_argc/_argc/salir/concat)
            # M22.2: Declarar extern de variables de scope RAII
            ctx.write_line("extern int _G_scope_depth;")
            ctx.write_line("extern int _G_scope_vars_depth[256];")
            ctx.write_line("extern char _G_scope_vars_names[256][64];")
            ctx.write_line("extern int _G_scope_vars_total;")
            ctx.write_line("extern int _G_safe_mode;  // M22.5: --safe flag")
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
            # Prototipos de funciones
            self._emit_prototipos_funciones(ctx)
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
