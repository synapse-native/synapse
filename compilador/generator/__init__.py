"""
generator/__init__.py — Orquestador del generador de código C.

Importa los submódulos de dominio (declarations, expressions, control, contracts)
y provee la clase GeneradorC que orquesta el recorrido del AST.
"""

import re
from typing import Optional


# ================================================================
# Helper utilities
# ================================================================

def _extract_listener_name(func_str: str) -> str:
    """Extrae el nombre de la función listener desde su declaración.
    Ej: 'void* _listener_1(void* arg) {' -> '_listener_1'
    """
    m = re.search(r'\*\s+(\w+)\s*\(', func_str)
    if m:
        return m.group(1)
    return ''


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

from .context import GeneratorContext, MAPA_TIPOS_C
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
    emitir_tokenizar, emitir_token_defs,
)
from .emit_contracts import emit_contract_header

# ================================================================
# Main dispatch
# ================================================================

def visitar(ctx: GeneratorContext, nodo: Nodo):
    """Despacha un nodo del AST al generador de código C apropiado."""
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
            if not val.endswith(';'):
                val += ';'
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
        pass  # Emitido en paso topológico previo
    elif isinstance(nodo, ImportarC):
        visitar_import_c(ctx, nodo)
    elif isinstance(nodo, DeclaracionExterna):
        visitar_externa(ctx, nodo)
    elif isinstance(nodo, StmtConstante):
        visitar_constante(ctx, nodo)
    elif isinstance(nodo, NodoCoincidir):
        visitar_coincidir(ctx, nodo)


# ================================================================
# Header emission
# ================================================================

def _emitir_encabezado(ctx: GeneratorContext):
    """Emite las cabeceras C, typedefs y declaraciones externas."""
    ctx.write_line("// salida_metal.c - Generado por Synapse Compilador")
    ctx.write_line("// Lenguaje: Synapse v1.0 (#lang: es)")

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
              'ImportarC', 'DeclaracionExterna', 'BloqueInseguro',
              'ExprObtenerDireccion', 'ExprDereferencia']:
        ctx.write_line(f"struct {t};")
    ctx.write_line("")

    # Typedefs
    typedefs = [
        ("Token", "{ int tipo; CadenaSegura lexema; int linea; int columna; }"),
        ("Nodo", "{ CadenaSegura tipo; }"),
        ("ListaNodo", "{ struct Nodo* cabeza; struct ListaNodo* cola; }"),
        ("Programa", "{ CadenaSegura tipo; struct ListaNodo* sentencias; }"),
    ]
    for name, body in typedefs:
        ctx.write_line(f"typedef struct {name} {body} {name};")
    ctx.write_line("")

    # Pool constants
    ctx.write_line("#define POOL_BLOQUES 64")
    ctx.write_line("#define TAMANO_BLOQUE 4096")
    ctx.write_line("")
    ctx.write_line("#define _GEN_TMP_SIZE (4096)")
    ctx.write_line("#include \"librerias/embedded_libs.h\"")
    ctx.write_line("")
    ctx.write_line("char _gen_tmp_buf[4096];")
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
        ctx.write_line("// --- Helpers de serialización primitiva ---")
        ctx.write_line(
            "inline void* _synapse_box_int(int v) "
            "{ return (void*)(intptr_t)v; }"
        )
        ctx.write_line(
            "inline int _synapse_unbox_int(void* p) "
            "{ return (int)(intptr_t)p; }"
        )
        ctx.write_line(
            "inline void* _synapse_box_float(float v) {"
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
            "inline float _synapse_unbox_float(void* p) {"
        )
        ctx.inc_indent()
        ctx.write_line("float _v = *(float*)p;")
        ctx.write_line("free(p);")
        ctx.write_line("return _v;")
        ctx.dec_indent()
        ctx.write_line("}")
        ctx.write_line("")

    # Runtime externs
    ctx.write_line("extern void pool_init(uint32_t total_blocks, uint32_t block_size);")
    ctx.write_line("extern void pool_free(void* ptr);")
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

    emit_contract_header(ctx)


# ================================================================
# GeneradorC — Main orchestrator class
# ================================================================

class GeneradorC:
    """Generador de código C a partir del AST de Synapse.

    Orquesta los módulos de dominio (declarations, expressions, control, contracts)
    usando GeneratorContext como estado centralizado.
    """

    def __init__(self, programa: Programa):
        self.ctx = GeneratorContext(programa)

    @property
    def _destructor_map(self):
        return self.ctx._destructor_map

    def generar(self) -> str:
        """Punto de entrada principal: genera código C completo."""
        ctx = self.ctx
        ctx._variables = {}
        ctx._func_return_types = {}
        ctx._func_param_types = {}

        # Pre-pass: collect function return types and param types
        for s in ctx.programa.sentencias:
            if isinstance(s, DefinicionFuncion):
                ctx._func_return_types[s.nombre] = s.tipo_retorno
                ctx._func_param_types[s.nombre] = [p.tipo for p in s.parametros]
            elif isinstance(s, DeclaracionExterna):
                ctx._func_return_types[s.nombre] = s.tipo_retorno

        _emitir_encabezado(ctx)

        # System builtins (skip in no_std)
        if not ctx.is_no_std():
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

        # Pre-pass: register struct definitions
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
        # Second pass: compute campos_pointer
        for nombre, info in ctx._estructuras.items():
            for c_nombre, c_tipo in info['campos']:
                if (
                    c_tipo in ctx._estructuras
                    or c_tipo.rstrip('*') in ctx._estructuras
                    or c_tipo == nombre
                ):
                    info['campos_pointer'].add(c_nombre)

        # Forward declarations for structs
        for s in ctx.programa.sentencias:
            if isinstance(s, DefinicionEstructura):
                ctx.write_line(f"struct {s.nombre};")
        if any(
            isinstance(s, DefinicionEstructura)
            for s in ctx.programa.sentencias
        ):
            ctx.write_line("")

        # Struct definitions (topological)
        for s in ctx.programa.sentencias:
            if isinstance(s, DefinicionEstructura):
                visitar_estructura(ctx, s)

        # Function prototypes
        _SPECIAL_SIGS = {
            'tokenizar': 'int tokenizar(CadenaSegura fuente)',
            'parsear': 'struct Programa parsear(CadenaSegura fuente)',
            'volcar_ast': 'void volcar_ast(struct Nodo* nodo, int nivel)',
            'generar': 'int generar(struct Programa programa, CadenaSegura ruta)',
        }
        for s in ctx.programa.sentencias:
            if (
                isinstance(s, DefinicionFuncion)
                and s.nombre not in ctx._RUNTIME_BUILTINS
            ):
                if s.nombre in _SPECIAL_SIGS:
                    ctx.write_line(f"{_SPECIAL_SIGS[s.nombre]};")
                else:
                    tipo_ret = ctx.traducir_tipo_c(s.tipo_retorno)
                    params = ", ".join(
                        f"{ctx.traducir_tipo_c(p.tipo)} {p.nombre}"
                        for p in s.parametros
                    ) if s.parametros else "void"
                    ctx.write_line(f"{tipo_ret} {s.nombre}({params});")
        if any(
            isinstance(s, DefinicionFuncion)
            and s.nombre not in ctx._RUNTIME_BUILTINS
            for s in ctx.programa.sentencias
        ):
            ctx.write_line("")

        # Main program pass: visit all statements
        for s in ctx.programa.sentencias:
            visitar(ctx, s)

        # Forward declarations for listener functions
        for func in ctx._listener_funciones:
            name = _extract_listener_name(func)
            if name:
                ctx.write_line(f"extern void* {name}(void* arg);")
        if ctx._listener_funciones:
            ctx.write_line("")
        
        # Listener function definitions
        for func in ctx._listener_funciones:
            ctx.lineas.append(func)
            ctx.lineas.append("")

        # Main function
        principal = ctx.encontrar_principal()
        if ctx.is_no_std():
            ctx.write_line("int main(void) {")
            ctx.inc_indent()
            if principal:
                ctx.write_line(f"{principal}();")
            ctx.write_line("return 0;")
            ctx.dec_indent()
            ctx.write_line("}")
        else:
            ctx.write_line("int main(int argc, char** argv) {")
            ctx.inc_indent()
            ctx.write_line("_g_argc = argc;")
            ctx.write_line("_g_argv = argv;")
            ctx.write_line("pool_init(POOL_BLOQUES, TAMANO_BLOQUE);")
            if principal:
                ret_tipo = ctx._func_return_types.get(principal, 'int')
                if ret_tipo in ('nulo', 'void'):
                    ctx.write_line(f"{principal}();")
                else:
                    ctx.write_line(f"return {principal}();")
            ctx.write_line("synapse_esperar_hilos();")
            ctx.write_line("return 0;")
            ctx.dec_indent()
            ctx.write_line("}")

        return ctx.generar()

    @property
    def linker_flags(self) -> str:
        """Retorna flags de linker necesarios."""
        if self.ctx._linker_libs:
            return " " + " ".join(
                f"-l{lib}" for lib in self.ctx._linker_libs
            )
        return ""
