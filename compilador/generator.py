from typing import List, Optional, Set
from compilador.ast_nodes import (
    Nodo, Programa, Parametro,
    DefinicionFuncion, DefinicionEstructura, ExprAccesoCampo, AsignacionCampo,
    StmtConstante,
    SentenciaSi, SentenciaLanzar, SentenciaRecuperar,
    SentenciaRetornar, SentenciaEscuchar, SentenciaMientras, SentenciaPara,
    SentenciaRomper, SentenciaSiguiente,
    SentenciaExpr, AsignacionVariable, DeclaracionVariable, LogLlamada,
    OpBinaria, OpUnaria, LlamadaFuncion, Identificador,
    LiteralNumero, LiteralDecimal, LiteralCadena, LiteralBooleano, ExprTensor, ArgumentoTransferido,
    BloqueInseguro, ExprObtenerDireccion, ExprDereferencia,
    ImportarC, DeclaracionExterna,
    NodoCaso, NodoCoincidir,
    ExprCrearCanal, SentenciaEnviarCanal, ExprRecibirCanal,
    ExprAsm,
)


MAPA_TIPOS_C: dict[str, str] = {
    'entero': 'int',
    'int': 'int',
    'vacio': 'void',
    'nulo': 'void',
    'decimal': 'float',
    'real': 'float',
    'flotante': 'float',
    'Tensor': 'Tensor',
    'tensor': 'Tensor',
    'Canal': 'Canal',
    'canal': 'Canal',
    'texto': 'CadenaSegura',
    'cadena': 'CadenaSegura',
    'booleano': 'int',
    'logico': 'int',
    'void': 'void',
    'char': 'char',
    'double': 'double',
    'puntero': 'void*',
}


_BUILTINS: dict[str, str] = {
    'reserva': 'Tensor',
    'libera': 'void',
    'crear_tensor': 'Tensor',
    'suma_tensor': 'Tensor',
    'producto_punto': 'Tensor',
    'abrir': 'Canal',
    'leer': 'CadenaSegura',
    'escribir': 'void',
    'escribir_linea': 'void',
    'leer_linea': 'CadenaSegura',
    'cerrar': 'void',
    'suma': 'Tensor',
    'producto': 'Tensor',
    'relu': 'Tensor',
    'tokenizar': 'int',
    'parsear': 'struct Programa',
    'generar': 'int',
    'concat': 'CadenaSegura',
    '_argc': 'int',
    '_argv': 'CadenaSegura',
    'salir': 'void',
    'canal_crear': 'CanalConcurrencia*',
    'canal_enviar': 'void',
    'canal_recibir': 'void*',
    'cerrar_canal': 'void',
    'texto_a_entero': 'int',
    'texto_a_decimal': 'float',
    'decimal_a_texto': 'CadenaSegura',
    'entero_a_texto': 'CadenaSegura',
}

_RUNTIME_BUILTINS: frozenset = frozenset({
    'escribir', 'escribir_linea', 'leer_linea', 'abrir', 'leer', 'cerrar',
    'math_crear_tensor', 'math_suma_tensor', 'math_producto_punto', 'math_relu',
    'mem_reserva', 'mem_libera', 'math_suma', 'math_producto',
    'crear_tensor', 'suma_tensor', 'producto_punto', 'relu',
    'reserva', 'libera', 'suma', 'producto',
    'texto_a_entero', 'texto_a_decimal', 'decimal_a_texto',
    'salir', 'canal_crear', 'canal_enviar', 'canal_recibir', 'cerrar_canal',
})


def _prim_int_to_ptr(value: str) -> str:
    return f"_synapse_box_int({value})"


def _prim_float_to_ptr(value: str) -> str:
    return f"_synapse_box_float({value})"


def _ptr_to_prim_int(ptr: str) -> str:
    return f"_synapse_unbox_int({ptr})"


def _ptr_to_prim_float(ptr: str) -> str:
    return f"_synapse_unbox_float({ptr})"

# Tabla de coerción: (tipo_origen, tipo_destino) -> funcion_coercion
_TABLA_COERCION: dict[tuple[str, str], str] = {
    ('float', 'CadenaSegura'): 'decimal_a_texto',
    ('int', 'CadenaSegura'): 'entero_a_texto',
}

# Funciones cuyos parametros esperan CadenaSegura — coercion automatica desde float
_FUNCIONES_ESPERAN_TEXTO: set[str] = {
    'escribir', 'escribir_linea', 'abrir', 'concat',
}

# Funciones nativas de C cuyos parámetros CadenaSegura necesitan .datos
_C_FUNCTIONS_NEED_DATOS: dict[str, list[str]] = {
    'strcmp': ['char*', 'char*'],
    'strncpy': ['char*', 'char*'],
    'strcpy': ['char*', 'char*'],
    'strcat': ['char*', 'char*'],
    'strlen': ['char*'],
    'strcspn': ['char*', 'char*'],
    'strchr': ['char*', 'int'],
    'strstr': ['char*', 'char*'],
    'strncmp': ['char*', 'char*'],
    'strncpy': ['char*', 'char*', 'int'],
    'memcpy': ['void*', 'void*', 'size_t'],
    'memset': ['void*', 'int', 'size_t'],
    'memmove': ['void*', 'void*', 'size_t'],
    'fopen': ['char*', 'char*'],
    'fclose': ['FILE*'],
    'fgets': ['char*', 'int', 'FILE*'],
    'fputs': ['char*', 'FILE*'],
    'fprintf': ['FILE*', 'char*'],
    'printf': ['char*'],
    'sprintf': ['char*', 'char*'],
    'fread': ['void*', 'size_t', 'size_t', 'FILE*'],
    'fwrite': ['void*', 'size_t', 'size_t', 'FILE*'],
    'fseek': ['FILE*', 'long', 'int'],
    'ftell': ['FILE*'],
    'rewind': ['FILE*'],
    'remove': ['char*'],
    'rename': ['char*', 'char*'],
    'qsort': ['void*', 'size_t', 'size_t', 'void*'],
    'bsearch': ['void*', 'void*', 'size_t', 'size_t', 'void*'],
    'atoi': ['char*'],
    'atol': ['char*'],
    'atof': ['char*'],
    'strtol': ['char*', 'char**', 'int'],
    'strtod': ['char*', 'char**'],
    'strtok': ['char*', 'char*'],
    'perror': ['char*'],
}


def _traducir_tipo_c(tipo_synapse: str) -> str:
    if tipo_synapse.startswith('Canal<') and tipo_synapse.endswith('>'):
        return 'CanalConcurrencia*'
    if tipo_synapse.startswith('Resultado<'):
        return 'Resultado_T'
    tipo_c = MAPA_TIPOS_C.get(tipo_synapse)
    if tipo_c is not None:
        return tipo_c
    return f"struct {tipo_synapse}"


def _aplicar_coercion(expr_c: str, tipo_origen: str, tipo_destino: str, linea: int = 0) -> str:
    clave = (tipo_origen, tipo_destino)
    if clave in _TABLA_COERCION:
        return f"{_TABLA_COERCION[clave]}({expr_c})"
    if tipo_origen == tipo_destino:
        return expr_c
    raise SyntaxError(
        f"Error semántico: no se puede coercer {tipo_origen} a {tipo_destino} (línea {linea})")


class GeneradorC:
    def __init__(self, programa: Programa):
        self.programa = programa
        self.lineas: List[str] = []
        self.indent = 0
        self._contador_thread = 0
        self._contador_listener = 0
        self._variables: dict[str, str] = {}
        self._const_types: dict[str, str] = {}
        self._funciones_emitidas: set[str] = set()
        self._tensor_vars: set[str] = set()
        self._tensor_vars_transferidas: set[str] = set()
        self._canal_vars: set[str] = set()
        self._canal_vars_cerradas: set[str] = set()
        self._listener_funciones: List[str] = []
        self._scope_stack: list[dict[str, str]] = []
        self._destructor_map: dict[str, str] = {
            'CadenaSegura': '_syn_texto_liberar',
            'NodoJson': '_json_nodo_liberar',
            'struct NodoJson': '_json_nodo_liberar',
            'NodoToml': '_toml_nodo_liberar',
            'struct NodoToml': '_toml_nodo_liberar',
        }
        self._gen_tok_emitido = False
        self._externas: dict[str, List[str]] = {}
        self._gen_parse_emitido = False
        self._linker_libs: set[str] = set()
        self._gen_defs_emitido = False
        self._estructuras: dict[str, list] = {}
        self._func_return_types: dict[str, str] = {}
        self._in_function_scope = False
        self._garantizas_actuales: List[Nodo] = []

    # --- Allocator helper: redirects to __syn_asignar/__syn_liberar in no_std ---
    def _syn_malloc(self, size_expr: str) -> str:
        if self.programa.is_no_std:
            return f'__syn_asignar({size_expr})'
        return f'malloc({size_expr})'

    def _syn_calloc(self, n_expr: str, size_expr: str) -> str:
        if self.programa.is_no_std:
            return f'__syn_asignar({n_expr} * {size_expr})'
        return f'calloc({n_expr}, {size_expr})'

    def _syn_free(self, ptr_expr: str) -> str:
        if self.programa.is_no_std:
            return f'__syn_liberar({ptr_expr})'
        return f'free({ptr_expr})'

    def _syn_pool_alloc(self, size_expr: str) -> str:
        if self.programa.is_no_std:
            return f'__syn_asignar({size_expr})'
        return f'_pool_malloc({size_expr})'

    def _syn_pool_free(self, ptr_expr: str) -> str:
        if self.programa.is_no_std:
            return f'__syn_liberar({ptr_expr})'
        return f'pool_free({ptr_expr})'

    def _push(self, linea: str = ""):
        if linea == "":
            self.lineas.append("")
        else:
            self.lineas.append("    " * self.indent + linea)

    def _push_expr(self, expr: str):
        self._push(expr)

    def _push_scope(self):
        self._scope_stack.append({})

    def _pop_scope(self):
        scope = self._scope_stack.pop() if self._scope_stack else {}
        for var_name in reversed(list(scope.keys())):
            dtor = self._destructor_map.get(scope[var_name])
            if dtor:
                self._push(f"{dtor}({var_name});")

    def _emit_all_destructors(self, exclude_var: str = ''):
        for scope in reversed(self._scope_stack):
            for var_name in reversed(list(scope.keys())):
                if var_name == exclude_var:
                    continue
                dtor = self._destructor_map.get(scope[var_name])
                if dtor:
                    self._push(f"{dtor}({var_name});")
        for scope in self._scope_stack:
            scope.clear()

    def _register_var(self, nombre: str, tipo: str, desde_llamada: bool):
        if self._scope_stack and desde_llamada and tipo in self._destructor_map:
            self._scope_stack[-1][nombre] = tipo

    def _unregister_var(self, nombre: str):
        for scope in self._scope_stack:
            scope.pop(nombre, None)

    def _encontrar_principal(self) -> Optional[str]:
        for s in self.programa.sentencias:
            if isinstance(s, DefinicionFuncion) and s.nombre == 'principal':
                return s.nombre
        return None

    def generar(self) -> str:
        self._variables = {}
        self._func_return_types = {}
        for s in self.programa.sentencias:
            if isinstance(s, DefinicionFuncion):
                self._func_return_types[s.nombre] = s.tipo_retorno
            elif isinstance(s, DeclaracionExterna):
                self._func_return_types[s.nombre] = s.tipo_retorno
        self._emitir_encabezado()
        # Builtins de sistema (omitir en modo no_std/bare-metal)
        if not self.programa.is_no_std:
            self._push("static int _g_argc;")
            self._push("static char** _g_argv;")
            self._push("int _argc() { return _g_argc; }")
            self._push("")
            self._push("CadenaSegura _argv(int i) {")
            self.indent += 1
            self._push("if (i < 0 || i >= _g_argc) return (CadenaSegura){0, \"\"};")
            self._push("return (CadenaSegura){ .longitud = (int)strlen(_g_argv[i]), .datos = _g_argv[i] };")
            self.indent -= 1
            self._push("}")
            self._push("")
            self._push("void salir(int codigo) { exit(codigo); }")
            self._push("")
            self._push("CadenaSegura concat(CadenaSegura a, CadenaSegura b) {")
            self.indent += 1
            self._push("int _tl = a.longitud + b.longitud;")
            self._push("char* _buf = (char*)malloc(_tl + 1);")
            self._push('if (!_buf) { fprintf(stderr,"Error: Asignación de memoria falló en concat()\\n"); exit(1); }')
            self._push("memcpy(_buf, a.datos, a.longitud);")
            self._push("memcpy(_buf + a.longitud, b.datos, b.longitud);")
            self._push("_buf[_tl] = 0;")
            self._push("CadenaSegura _r = { .longitud = _tl, .datos = _buf };")
            self._push("return _r;")
            self.indent -= 1
            self._push("}")
            self._push("")
        # Pre-pass: register all struct definitions
        for s in self.programa.sentencias:
            if isinstance(s, DefinicionEstructura):
                es_adt = any(c.nombre == 'tag' and c.tipo in ('entero', 'int') for c in s.campos)
                self._estructuras[s.nombre] = {
                    'campos': [(c.nombre, c.tipo) for c in s.campos],
                    'campos_pointer': set(),
                    'es_adt': es_adt,
                }
        # Second pass: compute campos_pointer with full _estructuras available
        for nombre, info in self._estructuras.items():
            for c_nombre, c_tipo in info['campos']:
                if c_tipo in self._estructuras or c_tipo == nombre:
                    info['campos_pointer'].add(c_nombre)
        # Forward declarations for structs
        for s in self.programa.sentencias:
            if isinstance(s, DefinicionEstructura):
                self._push(f"struct {s.nombre};")
        if any(isinstance(s, DefinicionEstructura) for s in self.programa.sentencias):
            self._push("")
        # Function prototypes (pre-pass)
        for s in self.programa.sentencias:
            if isinstance(s, DefinicionFuncion) and s.nombre not in _RUNTIME_BUILTINS:
                tipo_ret = _traducir_tipo_c(s.tipo_retorno)
                params = ", ".join(
                    f"{_traducir_tipo_c(p.tipo)} {p.nombre}" for p in s.parametros
                ) if s.parametros else "void"
                self._push(f"{tipo_ret} {s.nombre}({params});")
        if any(isinstance(s, DefinicionFuncion) and s.nombre not in _RUNTIME_BUILTINS for s in self.programa.sentencias):
            self._push("")
        for s in self.programa.sentencias:
            self._visitar(s)
        for func in self._listener_funciones:
            self._push(func)
            self._push("")
        principal = self._encontrar_principal()
        if self.programa.is_no_std:
            # Bare-metal minimal entry point: no argc/argv, no pool, no thread sync
            self._push("int main(void) {")
            self.indent += 1
            if principal:
                self._push(f"{principal}();")
            self._push("return 0;")
            self.indent -= 1
            self._push("}")
        else:
            self._push("int main(int argc, char** argv) {")
            self.indent += 1
            self._push("_g_argc = argc;")
            self._push("_g_argv = argv;")
            self._push("pool_init(POOL_BLOQUES, TAMANO_BLOQUE);")
            if principal:
                self._push(f"{principal}();")
            self._push("synapse_esperar_hilos();")
            self._push("return 0;")
            self.indent -= 1
            self._push("}")
        return "\n".join(self.lineas)

    def _emitir_encabezado(self):
        self._push("// salida_metal.c - Generado por Synapse Compilador")
        self._push("// Lenguaje: Synapse v1.0 (#lang: es)")
        
        # Conditionally include system headers based on no_std mode
        if not self.programa.is_no_std:
            self._push("#include <stdio.h>")
            self._push("#include <stdlib.h>")
            self._push("#include <stdint.h>")
            self._push("#include <pthread.h>")
            self._push("#include <string.h>")
            self._push("#include <assert.h>")
        else:
            # In no_std mode, only include minimal headers needed for bare-metal
            self._push("#include <stdint.h>")
            self._push("#include <stddef.h>")
        self._push("")
        self._push("typedef struct { int longitud; const char* datos; } CadenaSegura;")
        self._push("")
        self._push("typedef struct { uint32_t filas; uint32_t columnas; float* datos; int es_mapeado; } Tensor;")
        self._push("")
        if not self.programa.is_no_std:
            self._push("typedef struct { FILE* stream; int es_valido; int es_virtual; const char* virtual_data; int virtual_len; } Canal;")
            self._push("")
        self._push("// Constantes del pool de memoria (definidas en synapse_rt.c)")
        self._push("#define POOL_BLOQUES 64")
        self._push("#define TAMANO_BLOQUE 4096")
        self._push("")
        self._push("// Constantes de tags para uniones etiquetadas (ADTs)")
        self._push("#define TAG_OK 0")
        self._push("#define TAG_ERR 1")
        self._push("#define TAG_ALGUNO 0")
        self._push("#define TAG_NINGUNO 1")
        self._push("")
        if not self.programa.is_no_std:
            self._push("// --- Helpers de serialización primitiva para canales (Zero-Copy) ---")
            self._push("static inline void* _synapse_box_int(int v) { return (void*)(intptr_t)v; }")
            self._push("static inline int _synapse_unbox_int(void* p) { return (int)(intptr_t)p; }")
            self._push("static inline void* _synapse_box_float(float v) {")
            self._push("    float* _p = (float*)malloc(sizeof(float));")
            self._push('    if (!_p) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en _synapse_box_float\\n"); exit(1); }')
            self._push("    *_p = v;")
            self._push("    return (void*)_p;")
            self._push("}")
            self._push("static inline float _synapse_unbox_float(void* p) {")
            self._push("    float _v = *(float*)p;")
            self._push("    free(p);")
            self._push("    return _v;")
            self._push("}")
            self._push("")
        self._push("// --- Declaraciones extern del runtime precompilado (synapse_rt.o) ---")
        self._push("extern void pool_init(uint32_t total_blocks, uint32_t block_size);")
        self._push("extern void pool_free(void* ptr);")
        if self.programa.is_no_std:
            self._push("// --- Hooks de asignacion global (proporcionados por el desarrollador del SO) ---")
            self._push("extern void* __syn_asignar(int tamano);")
            self._push("extern void __syn_liberar(void* ptr);")
            self._push("")
        
        # Only include stdlib-dependent functions in non-no_std mode
        if not self.programa.is_no_std:
            self._push("extern void escribir(CadenaSegura contenido);")
            self._push("extern void escribir_linea(CadenaSegura contenido);")
            self._push("extern CadenaSegura leer_linea(void);")
            self._push("extern Canal abrir(CadenaSegura ruta, CadenaSegura modo);")
            self._push("extern CadenaSegura leer(Canal canal);")
            self._push("extern void cerrar(Canal canal);")
            self._push("extern Tensor crear_tensor(int filas, int columnas);")
            self._push("extern Tensor suma_tensor(Tensor a, Tensor b);")
            self._push("extern Tensor producto_punto(Tensor a, Tensor b);")
            self._push("extern Tensor relu(Tensor a);")
            self._push("extern Tensor reserva(int tamano);")
            self._push("extern void libera(Tensor bloque);")
            self._push("extern Tensor suma(Tensor a, Tensor b);")
            self._push("extern Tensor producto(Tensor a, Tensor b);")
            self._push("extern int texto_a_entero(CadenaSegura str);")
            self._push("extern float texto_a_decimal(CadenaSegura str);")
            self._push("extern CadenaSegura decimal_a_texto(float n);")
            self._push("extern CadenaSegura entero_a_texto(int n);")
            self._push("extern void synapse_lanzar_hilo(void* (*fn)(void*), void* arg);")
            self._push("extern void synapse_esperar_hilos(void);")
            self._push("extern void _syn_texto_liberar(CadenaSegura s);")
        if not self.programa.is_no_std:
            self._push("")
            self._push("// --- Declaraciones extern de canales (CanalConcurrencia) ---")
            self._push("typedef struct { int es_ok; union { void* ok_valor; const char* err_mensaje; } datos; } Resultado_T;")
            self._push("typedef struct CanalConcurrencia CanalConcurrencia;")
            self._push("extern CanalConcurrencia* canal_crear(uint32_t capacidad);")
            self._push("extern void canal_enviar(CanalConcurrencia* canal, void* paquete);")
            self._push("extern void* canal_recibir(CanalConcurrencia* canal);")
            self._push("extern void canal_destruir(CanalConcurrencia* canal);")
            self._push("extern void cerrar_canal(CanalConcurrencia* canal);")

    def _visitar(self, nodo: Nodo):
        _ejecutables = (SentenciaSi, SentenciaLanzar, SentenciaRecuperar,
                        SentenciaRetornar, SentenciaEscuchar, SentenciaMientras,
                        SentenciaRomper, SentenciaSiguiente, SentenciaExpr,
                        AsignacionVariable, LogLlamada, AsignacionCampo,
                        BloqueInseguro)
        if isinstance(nodo, _ejecutables) and not self._in_function_scope:
            raise SyntaxError(
                f"Código ejecutable fuera de ámbito global (linea {getattr(nodo, 'linea', '?')})")
        if isinstance(nodo, DefinicionFuncion):
            self._visitar_funcion(nodo)
        elif isinstance(nodo, SentenciaSi):
            self._visitar_si(nodo)
        elif isinstance(nodo, SentenciaLanzar):
            self._visitar_lanzar(nodo)
        elif isinstance(nodo, SentenciaRecuperar):
            self._visitar_recuperar(nodo)
        elif isinstance(nodo, SentenciaRetornar):
            self._visitar_retornar(nodo)
        elif isinstance(nodo, SentenciaEscuchar):
            self._visitar_escuchar(nodo)
        elif isinstance(nodo, SentenciaRomper):
            self._push("break;")
        elif isinstance(nodo, SentenciaSiguiente):
            self._push("continue;")
        elif isinstance(nodo, SentenciaMientras):
            self._visitar_mientras(nodo)
        elif isinstance(nodo, SentenciaPara):
            self._visitar_para(nodo)
        elif isinstance(nodo, BloqueInseguro):
            self._push("{ /* unsafe */")
            self.indent += 1
            self._push_scope()
            for s in nodo.cuerpo:
                self._visitar(s)
            self._pop_scope()
            self.indent -= 1
            self._push("}")
        elif isinstance(nodo, SentenciaExpr):
            self._push(self._expr_a_c(nodo.expr) + ";")
        elif isinstance(nodo, DeclaracionVariable):
            self._visitar_declaracion(nodo)
        elif isinstance(nodo, AsignacionVariable):
            self._visitar_asignacion(nodo)
        elif isinstance(nodo, LogLlamada):
            self._visitar_log(nodo)
        elif isinstance(nodo, SentenciaEnviarCanal):
            canal = self._expr_a_c(nodo.canal)
            valor = self._expr_a_c(nodo.valor)
            tipo_valor = self._tipo_de_expr(nodo.valor)
            if tipo_valor == 'int':
                self._push(f"canal_enviar({canal}, {_prim_int_to_ptr(valor)});")
            elif tipo_valor == 'float':
                self._push(f"canal_enviar({canal}, {_prim_float_to_ptr(valor)});")
            else:
                self._push(f"canal_enviar({canal}, (void*)({valor}));")
            # Move semantics: null out variable after channel send to prevent double-free
            if isinstance(nodo.valor, Identificador) and tipo_valor in self._destructor_map:
                self._push(f"{valor} = ({{0}});")
                self._unregister_var(nodo.valor.nombre)
        elif isinstance(nodo, DefinicionEstructura):
            self._visitar_estructura(nodo)
        elif isinstance(nodo, ImportarC):
            if nodo.es_sistema:
                self._push(f'#include <{nodo.ruta}>')
                if nodo.ruta == 'winsock2.h':
                    self._linker_libs.add('ws2_32')
            else:
                self._push(f'#include "{nodo.ruta}"')
        elif isinstance(nodo, DeclaracionExterna):
            self._externas[nodo.nombre] = [p.tipo for p in nodo.parametros]
            if not self._in_function_scope:
                tipo_ret_c = _traducir_tipo_c(nodo.tipo_retorno.replace('*', '')) + ('*' if '*' in nodo.tipo_retorno else '')
                params_c_parts = []
                for p in nodo.parametros:
                    base_tipo = p.tipo.replace('*', '')
                    es_puntero = '*' in p.tipo
                    tipo_c = _traducir_tipo_c(base_tipo)
                    if es_puntero:
                        tipo_c += '*'
                    params_c_parts.append(f"{tipo_c} {p.nombre}")
                params_c = ", ".join(params_c_parts) if params_c_parts else "void"
                self._push(f"extern {tipo_ret_c} {nodo.nombre}({params_c});")

        elif isinstance(nodo, StmtConstante):
            valor_c = self._expr_a_c(nodo.valor)
            tipo_inferido = nodo.tipo if nodo.tipo else self._tipo_de_expr(nodo.valor)
            tipo_c = _traducir_tipo_c(tipo_inferido or 'int')
            if not self._in_function_scope:
                self._push(f"#define {nodo.nombre} ({valor_c})")
            else:
                self._push(f"const {tipo_c} {nodo.nombre} = {valor_c};")
            self._const_types[nodo.nombre] = tipo_inferido or 'int'

        elif isinstance(nodo, AsignacionCampo):
            if not self._in_function_scope:
                raise SyntaxError(
                    f"Asignación de campo fuera de ámbito global (linea {nodo.linea})")
            obj = self._expr_a_c(nodo.objeto)
            val = self._expr_a_c(nodo.expresion)
            obj_tipo = self._tipo_de_expr(nodo.objeto)
            es_puntero = obj_tipo.endswith('*')
            nombre_struct = ''
            if not es_puntero and obj_tipo.startswith('struct '):
                nombre_struct = obj_tipo[7:]
                info = self._estructuras.get(nombre_struct)
                if info and nodo.nombre_campo in info.get('campos_pointer', set()):
                    es_puntero = True
            sep = '->' if es_puntero else '.'
            # ADT: encerrar campo de datos dentro de .dato.
            es_adt = bool(self._estructuras.get(nombre_struct, {}).get('es_adt'))
            campo_es_tag = (nodo.nombre_campo == 'tag' and es_adt)
            if es_adt and not campo_es_tag:
                self._push(f"{obj}{sep}dato.{nodo.nombre_campo} = {val};")
            else:
                self._push(f"{obj}{sep}{nodo.nombre_campo} = {val};")
        elif isinstance(nodo, NodoCoincidir):
            self._visitar_coincidir(nodo)

    def _visitar_funcion(self, nodo: DefinicionFuncion):
        if nodo.nombre in self._funciones_emitidas:
            return
        self._funciones_emitidas.add(nodo.nombre)

        if nodo.nombre in ('tokenizar', 'parsear', 'generar', 'volcar_ast'):
            getattr(self, f'_emitir_{nodo.nombre}')(nodo)
            return
        if nodo.nombre in _RUNTIME_BUILTINS:
            return  # Implementaciones en synapse_rt.c (linkar con synapse_rt.o)

        self._in_function_scope = True
        self._variables = {}
        self._tensor_vars = set()
        self._tensor_vars_transferidas = set()
        self._canal_vars = set()
        self._canal_vars_cerradas = set()
        self._strings_heap = set()
        for p in nodo.parametros:
            tipo_c = _traducir_tipo_c(p.tipo)
            self._variables[p.nombre] = tipo_c
        tipo = _traducir_tipo_c(nodo.tipo_retorno)
        params = ", ".join(f"{_traducir_tipo_c(p.tipo)} {p.nombre}" for p in nodo.parametros) if nodo.parametros else "void"
        self._push(f"{tipo} {nodo.nombre}({params}) {{")
        self.indent += 1
        self._push_scope()
        
        # Register transfer parameters (->) that own heap memory
        for p in nodo.parametros:
            if p.es_transferencia:
                tipo_c = _traducir_tipo_c(p.tipo)
                if tipo_c in self._destructor_map:
                    self._scope_stack[-1][p.nombre] = tipo_c
        
        # Inyectar asertos de contrato (requiere)
        for expr in nodo.requiere:
            expr_c = self._expr_a_c(expr)
            self._push("#ifndef SYNAPSE_RELEASE")
            self._push(f"assert(({expr_c}) && \"Fallo en contrato: requiere\");")
            self._push("#endif")
        
        # Guardar los contratos garantiza para usar en retornos
        self._garantizas_actuales = nodo.garantiza
        
        for s in nodo.cuerpo:
            self._visitar(s)
        for var in self._tensor_vars:
            if var not in self._tensor_vars_transferidas:
                self._push(f"if (!{var}.es_mapeado) {{ {self._syn_pool_free(f'{var}.datos')}; }}")
        for var in self._canal_vars:
            if var not in self._canal_vars_cerradas:
                self._push(f"/* ADVERTENCIA: canal '{var}' no fue cerrado explicitamente */")
                self._push(f"if ({var}.stream) {{ fclose({var}.stream); {var}.es_valido = 0; }}")
        self._pop_scope()
        self._tensor_vars.clear()
        self._tensor_vars_transferidas.clear()
        self._canal_vars.clear()
        self._canal_vars_cerradas.clear()
        self._garantizas_actuales = []
        self._in_function_scope = False
        self.indent -= 1
        self._push("}")
        self._push("")

    def _emitir_reserva(self, nodo: DefinicionFuncion):
        tam = nodo.parametros[0].nombre if nodo.parametros else 'tamano'
        self._push("Tensor reserva(int tamano) {")
        self.indent += 1
        self._push("Tensor _bloque;")
        self._push("_bloque.filas = tamano;")
        self._push("_bloque.columnas = 1;")
        self._push(f"_bloque.datos = {self._syn_pool_alloc('tamano')};")
        self._push("return _bloque;")
        self.indent -= 1
        self._push("}")
        self._push("")

    def _emitir_libera(self, nodo: DefinicionFuncion):
        bloque = nodo.parametros[0].nombre if nodo.parametros else 'bloque'
        self._push("void libera(Tensor bloque) {")
        self.indent += 1
        self._push("if (bloque.datos) {")
        self.indent += 1
        self._push(f"{self._syn_pool_free('bloque.datos')};")
        self.indent -= 1
        self._push("}")
        self.indent -= 1
        self._push("}")
        self._push("")

    def _emitir_abrir(self, nodo: DefinicionFuncion):
        self._push("Canal abrir(CadenaSegura ruta, CadenaSegura modo) {")
        self.indent += 1
        self._push("Canal _c = {0};")
        self._push('_c.es_virtual = 0;')
        self._push('if (strcmp(ruta.datos, "librerias/compiler/ast_nodes.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_AST; _c.virtual_len = (int)strlen(LIB_AST); _c.es_valido = 1; return _c; }')
        self._push('if (strcmp(ruta.datos, "librerias/compiler/lexer.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_LEXER; _c.virtual_len = (int)strlen(LIB_LEXER); _c.es_valido = 1; return _c; }')
        self._push('if (strcmp(ruta.datos, "librerias/compiler/parser.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_PARSER; _c.virtual_len = (int)strlen(LIB_PARSER); _c.es_valido = 1; return _c; }')
        self._push('if (strcmp(ruta.datos, "librerias/compiler/generator.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_GENERATOR; _c.virtual_len = (int)strlen(LIB_GENERATOR); _c.es_valido = 1; return _c; }')
        self._push('if (strcmp(ruta.datos, "librerias/std/io.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_IO; _c.virtual_len = (int)strlen(LIB_IO); _c.es_valido = 1; return _c; }')
        self._push('if (strcmp(ruta.datos, "librerias/std/mem.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_MEM; _c.virtual_len = (int)strlen(LIB_MEM); _c.es_valido = 1; return _c; }')
        self._push('if (strcmp(ruta.datos, "librerias/std/math.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_MATH; _c.virtual_len = (int)strlen(LIB_MATH); _c.es_valido = 1; return _c; }')
        self._push('if (strcmp(ruta.datos, "librerias/std/fs.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_FS; _c.virtual_len = (int)strlen(LIB_FS); _c.es_valido = 1; return _c; }')
        self._push('if (strcmp(ruta.datos, "librerias/std/sys.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_SYS; _c.virtual_len = (int)strlen(LIB_SYS); _c.es_valido = 1; return _c; }')
        self._push("_c.stream = fopen(ruta.datos, modo.datos);")
        self._push("_c.es_valido = (_c.stream != NULL) ? 1 : 0;")
        self._push("if (!_c.es_valido) {")
        self.indent += 1
        self._push('fprintf(stderr, "Error: No se pudo abrir el archivo en abrir()\\n");')
        self.indent -= 1
        self._push("}")
        self._push("return _c;")
        self.indent -= 1
        self._push("}")
        self._push("")

    def _emitir_leer(self, nodo: DefinicionFuncion):
        self._push("CadenaSegura leer(Canal canal) {")
        self.indent += 1
        self._push('if (!canal.es_valido) { return (CadenaSegura){ .longitud = 0, .datos = "" }; }')
        self._push("if (canal.es_virtual) {")
        self.indent += 1
        self._push("char* _buf = (char*)malloc(canal.virtual_len + 1);")
        self._push('if (!_buf) { return (CadenaSegura){ .longitud = 0, .datos = "" }; }')
        self._push("memcpy(_buf, canal.virtual_data, canal.virtual_len);")
        self._push("_buf[canal.virtual_len] = '\\0';")
        self._push("return (CadenaSegura){ .longitud = canal.virtual_len, .datos = (const char*)_buf };")
        self.indent -= 1
        self._push("}")
        self._push("fseek(canal.stream, 0, SEEK_END);")
        self._push("long _tam = ftell(canal.stream);")
        self._push("rewind(canal.stream);")
        self._push("char* _buf = (char*)malloc(_tam + 1);")
        self._push('if (!_buf) { return (CadenaSegura){ .longitud = 0, .datos = "" }; }')
        self._push("size_t _leido = fread(_buf, 1, _tam, canal.stream);")
        self._push("_buf[_leido] = '\\0';")
        self._push("return (CadenaSegura){ .longitud = (int)_leido, .datos = (const char*)_buf };")
        self.indent -= 1
        self._push("}")
        self._push("")

    def _emitir_escribir(self, nodo: DefinicionFuncion):
        self._push("void escribir(CadenaSegura contenido) {")
        self.indent += 1
        self._push("fwrite(contenido.datos, 1, contenido.longitud, stdout);")
        self._push("fflush(stdout);")
        self.indent -= 1
        self._push("}")
        self._push("")

    def _emitir_escribir_linea(self, nodo: DefinicionFuncion):
        self._push("void escribir_linea(CadenaSegura contenido) {")
        self.indent += 1
        self._push("fwrite(contenido.datos, 1, contenido.longitud, stdout);")
        self._push("fwrite(\"\\n\", 1, 1, stdout);")
        self._push("fflush(stdout);")
        self.indent -= 1
        self._push("}")
        self._push("")

    def _emitir_leer_linea(self, nodo: DefinicionFuncion):
        self._push("CadenaSegura leer_linea() {")
        self.indent += 1
        self._push("static char _buf[4096];")
        self._push("if (fgets(_buf, 4096, stdin)) {")
        self.indent += 1
        self._push("int _len = (int)strlen(_buf);")
        self._push("if (_len > 0 && _buf[_len - 1] == '\\n') { _buf[_len - 1] = '\\0'; _len--; }")
        self._push("char* _dup = (char*)malloc(_len + 1);")
        self._push("if (!_dup) { return (CadenaSegura){ .longitud = 0, .datos = \"\" }; }")
        self._push("memcpy(_dup, _buf, _len + 1);")
        self._push("return (CadenaSegura){ .longitud = _len, .datos = _dup };")
        self.indent -= 1
        self._push("}")
        self._push("return (CadenaSegura){ .longitud = 0, .datos = \"\" };")
        self.indent -= 1
        self._push("}")
        self._push("")

    def _emitir_cerrar(self, nodo: DefinicionFuncion):
        self._push("void cerrar(Canal canal) {")
        self.indent += 1
        self._push("if (canal.es_virtual) { return; }")
        self._push("if (canal.stream) {")
        self.indent += 1
        self._push("fclose(canal.stream);")
        self.indent -= 1
        self._push("}")
        self.indent -= 1
        self._push("}")
        self._push("")

    def _emitir_suma(self, nodo: DefinicionFuncion):
        self._push("Tensor suma(Tensor a, Tensor b) {")
        self.indent += 1
        self._push("if (a.filas != b.filas || a.columnas != b.columnas) {")
        self.indent += 1
        self._push('fprintf(stderr, "Error: Dimensiones incompatibles en suma() - las matrices deben tener el mismo tamaño\\n");')
        self._push('return (Tensor){ .filas = 0, .columnas = 0, .datos = NULL };')
        self.indent -= 1
        self._push("}")
        self._push("Tensor r;")
        self._push("r.filas = a.filas;")
        self._push("r.columnas = a.columnas;")
        self._push(f"r.datos = {self._syn_pool_alloc('r.filas * r.columnas * sizeof(float)')};")
        self._push("for (int _i = 0; _i < r.filas * r.columnas; _i++) {")
        self.indent += 1
        self._push("r.datos[_i] = a.datos[_i] + b.datos[_i];")
        self.indent -= 1
        self._push("}")
        self._push(f"{self._syn_pool_free('a.datos')};")
        self._push(f"{self._syn_pool_free('b.datos')};")
        self._push("return r;")
        self.indent -= 1
        self._push("}")
        self._push("")

    def _emitir_producto(self, nodo: DefinicionFuncion):
        self._push("Tensor producto(Tensor a, Tensor b) {")
        self.indent += 1
        self._push("if (a.columnas != b.filas) {")
        self.indent += 1
        self._push('fprintf(stderr, "Error: Dimensiones incompatibles en producto() - columnas de A deben igualar filas de B\\n");')
        self._push('return (Tensor){ .filas = 0, .columnas = 0, .datos = NULL };')
        self.indent -= 1
        self._push("}")
        self._push("Tensor r;")
        self._push("r.filas = a.filas;")
        self._push("r.columnas = b.columnas;")
        _calloc = self._syn_calloc('r.filas * r.columnas', 'sizeof(float)')
        self._push(f"r.datos = (float*){_calloc};")
        self._push("for (int _i = 0; _i < r.filas; _i++) {")
        self.indent += 1
        self._push("for (int _j = 0; _j < r.columnas; _j++) {")
        self.indent += 1
        self._push("float _sum = 0;")
        self._push("for (int _k = 0; _k < a.columnas; _k++) {")
        self.indent += 1
        self._push("_sum += a.datos[_i * a.columnas + _k] * b.datos[_k * b.columnas + _j];")
        self.indent -= 1
        self._push("}")
        self._push("r.datos[_i * r.columnas + _j] = _sum;")
        self.indent -= 1
        self._push("}")
        self.indent -= 1
        self._push("}")
        self._push(f"{self._syn_pool_free('a.datos')};")
        self._push(f"{self._syn_pool_free('b.datos')};")
        self._push("return r;")
        self.indent -= 1
        self._push("}")
        self._push("")

    def _emitir_relu(self, nodo: DefinicionFuncion):
        self._push("Tensor relu(Tensor a) {")
        self.indent += 1
        self._push("Tensor r;")
        self._push("r.filas = a.filas;")
        self._push("r.columnas = a.columnas;")
        self._push(f"r.datos = {self._syn_pool_alloc('a.filas * a.columnas * sizeof(float)')};")
        self._push("for (int _i = 0; _i < a.filas * a.columnas; _i++) {")
        self.indent += 1
        self._push("r.datos[_i] = (a.datos[_i] > 0) ? a.datos[_i] : 0.0f;")
        self.indent -= 1
        self._push("}")
        self._push(f"{self._syn_pool_free('a.datos')};")
        self._push("return r;")
        self.indent -= 1
        self._push("}")
        self._push("")

    def _emitir_crear_tensor(self, nodo: DefinicionFuncion):
        self._push("Tensor crear_tensor(int filas, int columnas) {")
        self.indent += 1
        self._push("Tensor r;")
        self._push("r.filas = filas;")
        self._push("r.columnas = columnas;")
        self._push(f"r.datos = {self._syn_pool_alloc('filas * columnas * sizeof(float)')};")
        self._push("memset(r.datos, 0, filas * columnas * sizeof(float));")
        self._push("return r;")
        self.indent -= 1
        self._push("}")
        self._push("")

    def _emitir_suma_tensor(self, nodo: DefinicionFuncion):
        self._push("Tensor suma_tensor(Tensor a, Tensor b) {")
        self.indent += 1
        self._push("if (a.filas != b.filas || a.columnas != b.columnas) {")
        self.indent += 1
        self._push('fprintf(stderr, "Error: Dimensiones incompatibles en suma_tensor() - las matrices deben tener el mismo tamaño\\n");')
        self._push('return (Tensor){ .filas = 0, .columnas = 0, .datos = NULL };')
        self.indent -= 1
        self._push("}")
        self._push("Tensor r;")
        self._push("r.filas = a.filas;")
        self._push("r.columnas = a.columnas;")
        self._push(f"r.datos = {self._syn_pool_alloc('r.filas * r.columnas * sizeof(float)')};")
        self._push("for (int _i = 0; _i < r.filas * r.columnas; _i++) {")
        self.indent += 1
        self._push("r.datos[_i] = a.datos[_i] + b.datos[_i];")
        self.indent -= 1
        self._push("}")
        self._push(f"{self._syn_pool_free('a.datos')};")
        self._push(f"{self._syn_pool_free('b.datos')};")
        self._push("return r;")
        self.indent -= 1
        self._push("}")
        self._push("")

    def _emitir_producto_punto(self, nodo: DefinicionFuncion):
        self._push("Tensor producto_punto(Tensor a, Tensor b) {")
        self.indent += 1
        self._push("if (a.columnas != b.filas) {")
        self.indent += 1
        self._push('fprintf(stderr, "Error: Dimensiones incompatibles en producto_punto() - columnas de A deben igualar filas de B\\n");')
        self._push('return (Tensor){ .filas = 0, .columnas = 0, .datos = NULL };')
        self.indent -= 1
        self._push("}")
        self._push("Tensor r;")
        self._push("r.filas = a.filas;")
        self._push("r.columnas = b.columnas;")
        _calloc = self._syn_calloc('r.filas * r.columnas', 'sizeof(float)')
        self._push(f"r.datos = (float*){_calloc};")
        self._push("for (int _i = 0; _i < r.filas; _i++) {")
        self.indent += 1
        self._push("for (int _j = 0; _j < r.columnas; _j++) {")
        self.indent += 1
        self._push("float _sum = 0;")
        self._push("for (int _k = 0; _k < a.columnas; _k++) {")
        self.indent += 1
        self._push("_sum += a.datos[_i * a.columnas + _k] * b.datos[_k * b.columnas + _j];")
        self.indent -= 1
        self._push("}")
        self._push("r.datos[_i * r.columnas + _j] = _sum;")
        self.indent -= 1
        self._push("}")
        self.indent -= 1
        self._push("}")
        self._push(f"{self._syn_pool_free('a.datos')};")
        self._push(f"{self._syn_pool_free('b.datos')};")
        self._push("return r;")
        self.indent -= 1
        self._push("}")
        self._push("")

    def _emitir_tokenizar(self, nodo: DefinicionFuncion):
        self._push("int tokenizar(CadenaSegura fuente) {")
        self.indent += 1
        self._push("int _i = 0;")
        self._push("int _linea = 1;")
        self._push("int _columna = 1;")
        self._push("int _token_count = 0;")
        self._push("while (_i < fuente.longitud) {")
        self.indent += 1
        self._push("char _c = fuente.datos[_i];")
        self._push("if (_c == ' ' || _c == '\\t') { _i++; _columna++; continue; }")
        self._push("if (_c == '\\r') { _i++; continue; }")
        self._push("if (_c == '\\n') { _i++; _linea++; _columna = 1; continue; }")
        self._push("if (_c == '/' && _i + 1 < fuente.longitud && fuente.datos[_i + 1] == '/') {")
        self.indent += 1
        self._push("while (_i < fuente.longitud && fuente.datos[_i] != '\\n') { _i++; }")
        self._push("continue;")
        self.indent -= 1
        self._push("}")
        self._push("if (_c == '\"' || _c == '\\'') {")
        self.indent += 1
        self._push("char _q = _c; int _start = _i; _i++; _columna++;")
        self._push("while (_i < fuente.longitud && fuente.datos[_i] != _q) { _i++; _columna++; }")
        self._push("if (_i >= fuente.longitud) {")
        self.indent += 1
        self._push('fprintf(stderr, "  TOKEN STRING_UNCLOSED L%d:%d\\n", _linea, _columna);')
        self._push("break;")
        self.indent -= 1
        self._push("}")
        self._push("_i++; _columna++;")
        self._push("_token_count++;")
        self._push('fprintf(stderr, "  TOKEN STRING L%d:%d\\n", _linea, _columna);')
        self.indent -= 1
        self._push("}")
        self._push("else if (_c >= '0' && _c <= '9') {")
        self.indent += 1
        self._push("int _start = _i;")
        self._push("while (_i < fuente.longitud && fuente.datos[_i] >= '0' && fuente.datos[_i] <= '9') { _i++; }")
        self._push("_columna += _i - _start;")
        self._push("_token_count++;")
        self._push('fprintf(stderr, "  TOKEN NUMBER L%d:%d\\n", _linea, _columna);')
        self.indent -= 1
        self._push("}")
        self._push("else if ((_c >= 'a' && _c <= 'z') || (_c >= 'A' && _c <= 'Z') || _c == '_') {")
        self.indent += 1
        self._push("int _start = _i;")
        self._push("while (_i < fuente.longitud && (")
        self._push("    (fuente.datos[_i] >= 'a' && fuente.datos[_i] <= 'z') ||")
        self._push("    (fuente.datos[_i] >= 'A' && fuente.datos[_i] <= 'Z') ||")
        self._push("    (fuente.datos[_i] >= '0' && fuente.datos[_i] <= '9') ||")
        self._push("    fuente.datos[_i] == '_'")
        self._push(")) { _i++; }")
        self._push("int _len_id = _i - _start;")
        self._push("char _buf_id[256]; int _clip = _len_id < 255 ? _len_id : 255;")
        self._push("strncpy(_buf_id, fuente.datos + _start, _clip); _buf_id[_clip] = 0;")
        self._push("_columna += _len_id;")
        self._push("_token_count++;")
        self._push("typedef struct { const char* p; int t; } _KWE;")
        self._push("static const _KWE _kws[] = {")
        self._push('    {"si",1},{"if",1},{"se",1},{"wenn",1},')
        self._push('    {"sino",2},{"else",2},{"sinon",2},{"senao",2},{"sonst",2},{"altrimenti",2},')
        self._push('    {"funcion",3},{"function",3},{"fonction",3},{"funcao",3},{"funktion",3},{"funzione",3},')
        self._push('    {"retornar",4},{"return",4},{"retourner",4},{"rueckgabe",4},{"restituisci",4},')
        self._push('    {"lanzar",5},{"spawn",5},{"lancer",5},{"lancar",5},{"starten",5},{"lancia",5},')
        self._push('    {"recuperar",6},{"recover",6},{"recuperer",6},{"wiederherstellen",6},{"recupera",6},')
        self._push('    {"escuchar",7},{"listen",7},{"ecouter",7},{"escutar",7},{"hoeren",7},{"ascolta",7},')
        self._push('    {"mientras",8},{"while",8},{"tantque",8},{"enquanto",8},{"waehrend",8},{"mentre",8},')
        self._push('    {"importar",9},{"import",9},{"importer",9},{"importieren",9},{"importa",9},')
        self._push('    {"romper",10},{"break",10},{"rompre",10},{"parar",10},{"abbrechen",10},{"interrompi",10},')
        self._push('    {"siguiente",11},{"continue",11},{"continuer",11},{"continuar",11},{"fortsetzen",11},{"continua",11},')
        self._push('    {"estructura",37},{"struct",37},{"structure",37},{"estrutura",37},{"struktur",37},{"struttura",37},')
        self._push('    {"y",38},{"and",38},{"et",38},{"e",38},{"und",38},')
        self._push('    {"o",39},{"or",39},{"ou",39},{"oder",39},')
        self._push('    {"no",40},{"not",40},{"non",40},{"nao",40},{"nicht",40},')
        self._push('    {"verdadero",41},{"true",41},{"vrai",41},{"verdadeiro",41},{"wahr",41},{"vero",41},')
        self._push('    {"falso",42},{"false",42},{"faux",42},{"falsch",42},')
        self._push('    {"inseguro",43},{"unsafe",43},')
        self._push('    {"importar_c",44},{"import_c",44},{"importer_c",44},{"importa_c",44},')
        self._push('    {"externo",46},{"extern",46},{"externe",46},{"esterno",46},')
        self._push("    {NULL,0}")
        self._push("};")
        self._push("int _kt = 0;")
        self._push("for (int _ki = 0; _kws[_ki].p; _ki++) {")
        self._push("    if (strcmp(_buf_id, _kws[_ki].p) == 0) { _kt = _kws[_ki].t; break; }")
        self._push("}")
        self._push("if (_kt)")
        self._push('    fprintf(stderr, "  TOKEN %d L%d:%d\\n", _kt, _linea, _columna);')
        self._push("else")
        self._push('    fprintf(stderr, "  TOKEN IDENTIFIER L%d:%d\\n", _linea, _columna);')
        self.indent -= 1
        self._push("}")
        self._push("else {")
        self.indent += 1
        self._push("_i++; _columna++;")
        self._push("_token_count++;")
        self._push('fprintf(stderr, "  TOKEN CHAR(%c) L%d:%d\\n", _c, _linea, _columna);')
        self.indent -= 1
        self._push("}")
        self.indent -= 1
        self._push("}")
        self._push('fprintf(stderr, "Total tokens: %d\\n", _token_count);')
        self._push("return _token_count;")
        self.indent -= 1
        self._push("}")
        self._push("")

    def _emitir_token_defs(self):
        if self._gen_defs_emitido:
            return
        self._gen_defs_emitido = True
        self.lineas.extend([
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
            "static _P_Token _P_tks[MAX_TOKS];",
            "static int _P_ntks = 0, _P_tpos = 0, _P_p_err = 0;",
            "static int _P_pila_indent[64], _P_nivel_pila = 0;",
            "",
        ])

    def _emitir_parsear(self, nodo: DefinicionFuncion):
        self._emitir_token_defs()
        self._gen_tok_c()
        self._gen_parse()
        self._push("struct Programa parsear(CadenaSegura fuente) {")
        self.indent += 1
        self._push("_P_ntks = 0; _P_tpos = 0; _P_p_err = 0; _P_nivel_pila = 0;")
        self._push("_P_pila_indent[0] = 0;")
        self._push("_P_tokenizar(fuente.datos, fuente.longitud);")
        self._push("_P_procesar_indentacion_final();")
        self._push("struct Programa _prog = _P_programa();")
        self._push("return _prog;")
        self.indent -= 1
        self._push("}")
        self._push("")

    def _emitir_volcar_ast(self, nodo: DefinicionFuncion):
        self._push("void _volcar_nodo(struct Nodo* nodo, int nivel) {")
        self.indent += 1
        self._push('if (!nodo) { printf("(null)\\n"); return; }')
        self._push("for (int _i = 0; _i < nivel; _i++) printf(\"  \");")
        self._push('printf("[%s]\\n", nodo->tipo.datos);')
        branches = []
        for nombre, info in self._estructuras.items():
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
                self._push(f'if (strcmp(nodo->tipo.datos, "{nombre}") == 0) {{')
            else:
                self._push(f'else if (strcmp(nodo->tipo.datos, "{nombre}") == 0) {{')
            self.indent += 1
            for c_nombre, c_tipo in printable:
                if c_tipo == 'CadenaSegura':
                    self._push(f'printf("  {c_nombre}: %s\\n", ((struct {nombre}*)nodo)->{c_nombre}.datos);')
                else:
                    self._push(f'printf("  {c_nombre}: %d\\n", ((struct {nombre}*)nodo)->{c_nombre});')
            for c_nombre in children_single:
                self._push(f'_volcar_nodo(((struct {nombre}*)nodo)->{c_nombre}, nivel + 1);')
            for c_nombre, c_tipo in children_list:
                self._push(f'{{ struct {c_tipo}* _cur = ((struct {nombre}*)nodo)->{c_nombre}; while (_cur) {{ _volcar_nodo(_cur->cabeza, nivel + 1); _cur = _cur->cola; }} }}')
            self.indent -= 1
            self._push("}")
        self._push('else { printf("  (tipo desconocido)\\n"); }')
        self.indent -= 1
        self._push("}")
        self._push("")
        self._externas['volcar_ast'] = ['struct Nodo*', 'int']
        self._push("void volcar_ast(struct Nodo* nodo, int nivel) { _volcar_nodo(nodo, nivel); }")
        self._push("")

    def _gen_tok_c(self):
        if self._gen_tok_emitido:
            return
        self._gen_tok_emitido = True
        P = '_P_'
        self.lineas.extend([
            "static void " + P + "tokenizar(const char* s, int len) {",
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
"            while (i < len && s[i] != q) { i++; co++; }",
"            if (i >= len) break;",
"            i++; co++;",
"            int vl = (i - st - 2) < 255 ? (i - st - 2) : 255;",
"            strncpy(" + P + "tks[" + P + "ntks].val, s + st + 1, vl); " + P + "tks[" + P + "ntks].val[vl] = 0;",
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
            '            static const _KW _ks[] = {',
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
            "static void " + P + "procesar_indentacion_final() {",
            "    while (" + P + "nivel_pila > 0) {",
            "        " + P + "tks[" + P + "ntks].tipo = T_DEDENT; " + P + "tks[" + P + "ntks].linea = " + P + "tks[" + P + "ntks-1].linea; " + P + "tks[" + P + "ntks].col = 0;",
            "        " + P + "ntks++; " + P + "nivel_pila--;",
            "    }",
            "}",
            "",
        ])
    def _gen_parse(self):
        if self._gen_parse_emitido:
            return
        self._gen_parse_emitido = True
        # Write parser C code with _P_ prefix
        _P = '_P_'
        self.lineas.extend([
            "// --- AST builder helpers ---",
            "static CadenaSegura " + _P + "cs(const char* s) {",
            "    CadenaSegura c; c.longitud = (int)strlen(s);",
            "    char* d = (char*)malloc(c.longitud + 1); strcpy(d, s); c.datos = d; return c;",
            "}",
            "static struct ListaNodo* " + _P + "mk_list(struct Nodo* h, struct ListaNodo* t) {",
            "    struct ListaNodo* n = (struct ListaNodo*)calloc(1,sizeof(struct ListaNodo));",
            "    n->cabeza = h; n->cola = t; return n;",
            "}",
            "",
        ])
        # Helper + globals
        self.lineas.extend([
            "static " + _P + "Token* " + _P + "mirar() { return &" + _P + "tks[" + _P + "tpos]; }",
            "static void " + _P + "avanzar() { if (" + _P + "tpos < " + _P + "ntks) " + _P + "tpos++; }",
            "static int " + _P + "posible(int t) { return " + _P + "mirar()->tipo == t ? 1 : 0; }",
            "static int " + _P + "esperar(int t) {",
            "    if (" + _P + "mirar()->tipo == t) { " + _P + "avanzar(); return 1; }",
            '    fprintf(stderr, "[PARSER] L%d:%d: esperaba token %d, encontre %d\\n",',
            "            " + _P + "mirar()->linea, " + _P + "mirar()->col, t, " + _P + "mirar()->tipo);",
            "    exit(1);",
            "}",
            "static void " + _P + "sinc_skip() {",
            "    while (" + _P + "tpos < " + _P + "ntks) {",
            "        int tt = " + _P + "mirar()->tipo;",
            "        if (tt == T_NL || tt == T_DEDENT || tt == T_EOF || tt == T_COMMA || tt == T_RPAREN || tt == T_COLON) break;",
            "        " + _P + "avanzar();",
            "    }",
            "}",
            "",
            "// Forward declarations",
            "static struct Nodo* " + _P + "expr();",
            "static struct Nodo* " + _P + "logica();",
            "static struct ListaNodo* " + _P + "bloque();",
            "static struct Nodo* " + _P + "sentencia();",
            "static struct Nodo* " + _P + "comp();",
            "static struct Nodo* " + _P + "suma();",
            "static struct Nodo* " + _P + "term();",
            "static struct Nodo* " + _P + "una();",
            "static struct Nodo* " + _P + "prim();",
            "static struct Programa " + _P + "programa();",
        ])
        # Now emit the function bodies using a clean string template
        B = """
static struct ListaNodo* """ + _P + """bloque() {
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
static struct Nodo* """ + _P + """sentencia() {
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
static struct Nodo* """ + _P + """expr() { return """ + _P + """logica(); }

static struct Nodo* """ + _P + """logica() {
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

static struct Nodo* """ + _P + """comp() {
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
static struct Nodo* """ + _P + """suma() {
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
static struct Nodo* """ + _P + """term() {
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
static struct Nodo* """ + _P + """una() {
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
static struct Nodo* """ + _P + """prim() {
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
static struct Programa """ + _P + """programa() {
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
            self.lineas.append(ln)

    def _emitir_generar(self, nodo: DefinicionFuncion):
        self.lineas.extend(["// --- Generador de C ---"])
        self._emitir_token_defs()
        self._gen_tok_c()
        self._gen_parse()
        # Use a placeholder that won't collide with C braces
        _PH = '@@P@@'
        H = f"""
// --- AST Walker ---
static int {_PH}indent = 0;
static FILE* {_PH}out = NULL;
static char {_PH}vn[1024][64];
static char {_PH}vt[1024][64];
static int {_PH}nv = 0;
static char {_PH}ret_type[64];
static char {_PH}extern_names[64][64];
static char {_PH}extern_params[64][256];
static int {_PH}nextern = 0;
static char {_PH}snames[64][64];
static int {_PH}nsnames = 0;

static void {_PH}reset() {{ {_PH}nv = 0; }}
static int {_PH}find(const char* n) {{ for(int i=0;i<{_PH}nv;i++) if(strcmp({_PH}vn[i],n)==0) return i; return -1; }}
static const char* {_PH}decl(const char* n, const char* t) {{
    int i={_PH}find(n); if(i>=0) return {_PH}vt[i];
    if({_PH}nv<1024){{ strcpy({_PH}vn[{_PH}nv],n); strcpy({_PH}vt[{_PH}nv],t); {_PH}nv++; }}
    return t;
}}

static void {_PH}emit(const char* s) {{
    for(int i=0;i<{_PH}indent;i++) fprintf({_PH}out,"    ");
    fprintf({_PH}out,"%s\\n",s);
}}

static void {_PH}cp(char* d, CadenaSegura cs) {{ memcpy(d,cs.datos,cs.longitud); d[cs.longitud]=0; }}

static const char* {_PH}tex(struct Nodo* n) {{
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
        for(int _si=0;_si<{_PH}nsnames;_si++){{ if(strcmp(m,{_PH}snames[_si])==0) {{ static char _sret[64]; snprintf(_sret,sizeof(_sret),"struct %s",m); return _sret; }} }}
        return "int";
    }}
    if(strcmp(t,"ExprAccesoCampo")==0||strcmp(t,"ArgumentoTransferido")==0) return "int";
    if(strcmp(t,"ExprTensor")==0) return "Tensor";
    if(strcmp(t,"ExprObtenerDireccion")==0) return "int*";
    if(strcmp(t,"ExprDereferencia")==0) return "int";
    return "int";
}}

static void {_PH}ea(struct Nodo* n, char* b, int sz);
static void {_PH}vl(struct ListaNodo* l);
static void {_PH}v(struct Nodo* n);

static int {_PH}extern_needs_datos(const char* fn, int argidx) {{
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
static void {_PH}vl(struct ListaNodo* l) {{ while(l){{ {_PH}v(l->cabeza); l=l->cola; }} }}

static void {_PH}ea(struct Nodo* n, char* b, int sz) {{
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

static void {_PH}v_log(struct LogLlamada* n) {{
    char f[4096]=""; int fp=0,ap=0,fi=1; char b[512]; char pr[4096]="";
    struct ListaNodo* c=n->argumentos;
    while(c){{ if(!fi){{ f[fp++]=' '; }} fi=0; f[fp++]='%'; f[fp++]='s';
        {_PH}ea(c->cabeza,b,512); if(ap>0){{ pr[ap++]=','; pr[ap++]=' '; }} int k=0; while(b[k]) pr[ap++]=b[k++]; c=c->cola;
    }}
    f[fp]=0; pr[ap]=0; char ln[4096];
    if(ap>0) snprintf(ln,sizeof(ln),"printf(\\"%s\\\\n\\",%s);",f,pr);
    else snprintf(ln,sizeof(ln),"printf(\\"%s\\\\n\\");",f);
    {_PH}emit(ln);
}}

static const char* {_PH}mt(const char* st) {{
    static char _mtb[64];
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
static void {_PH}vest(struct DefinicionEstructura* n) {{
    char ln[4096];
    snprintf(ln,sizeof(ln),"typedef struct %s {{",n->nombre.datos); {_PH}emit(ln);
    {_PH}indent++;
    struct ListaParametro* c=n->campos;
    while(c){{ struct Parametro* p=(struct Parametro*)c->cabeza; char pn[256]; {_PH}cp(pn,p->nombre); char pt[256]; {_PH}cp(pt,p->tipo_param); const char* ct={_PH}mt(pt); if(ct){{ snprintf(ln,sizeof(ln),"%s %s;",ct,pn); }}else{{ snprintf(ln,sizeof(ln),"struct %s* %s;",pt,pn); }} {_PH}emit(ln); c=c->cola; }}
    {_PH}indent--; snprintf(ln,sizeof(ln),"}} %s;",n->nombre.datos); {_PH}emit(ln);
    snprintf(ln,sizeof(ln),"static inline struct %s %s_nuevo() {{",n->nombre.datos,n->nombre.datos); {_PH}emit(ln);
    {_PH}indent++; snprintf(ln,sizeof(ln),"struct %s _r={{0}}; return _r;",n->nombre.datos); {_PH}emit(ln);
    {_PH}indent--; {_PH}emit("}}");
    if({_PH}nsnames<64){{ strcpy({_PH}snames[{_PH}nsnames],n->nombre.datos); {_PH}nsnames++; }}
}}

static void {_PH}v(struct Nodo* n) {{
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
        const char* vt={_PH}tex(a->expresion);
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
    fprintf({_PH}out,"static int _g_argc;\\nstatic char** _g_argv;\\nint _argc(){{return _g_argc;}}\\n");
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
    snprintf(cmd, sizeof(cmd), "gcc -O2 -fno-ident -Wl,--no-insert-timestamp \\"%s\\" \\"C:\\\\Synapse\\\\lib\\\\synapse_rt.o\\" -o \\"%s\\" -lpthread -lm", sal, out_exe);
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
            self.lineas.append(ln)

    @property
    def linker_flags(self) -> str:
        if not self._linker_libs:
            return ""
        return " ".join(f"-l{lib}" for lib in sorted(self._linker_libs))

    def _visitar_si(self, nodo: SentenciaSi):
        cond = self._expr_a_c(nodo.condicion)
        self._push(f"if ({cond}) {{")
        self.indent += 1
        self._push_scope()
        for s in nodo.cuerpo:
            self._visitar(s)
        self._pop_scope()
        self.indent -= 1
        if nodo.cuerpo_sino:
            self._push("} else {")
            self.indent += 1
            self._push_scope()
            for s in nodo.cuerpo_sino:
                self._visitar(s)
            self._pop_scope()
            self.indent -= 1
        self._push("}")

    def _visitar_coincidir(self, nodo: NodoCoincidir):
        import re
        
        # Evaluar la expresión objetivo y guardarla en variable temporal
        expr_c = self._expr_a_c(nodo.expresion)
        expr_tipo = self._tipo_de_expr(nodo.expresion)
        temp_var = f"_match_tmp_{nodo.linea}"
        self._push(f"/* coincidir: evaluando expresión */")
        self._push(f"{expr_tipo} {temp_var} = {expr_c};")
        
        # Iterar sobre los casos
        for i, caso in enumerate(nodo.casos):
            # Extraer tag y variable del patrón (ej. "ok(v)" -> tag="ok", var="v")
            patron = caso.patron
            match = re.match(r'(\w+)\((\w+)\)', patron)
            if not match:
                raise SyntaxError(f"Patrón inválido en coincidir: {patron}")
            
            tag_nombre = match.group(1)  # ej. "ok" o "err"
            var_nombre = match.group(2)  # ej. "v" o "e"
            
            # Generar bloque C con if/else if
            if expr_tipo == 'Resultado_T':
                if i == 0:
                    self._push(f"if ({temp_var}.es_ok == 1) {{")
                else:
                    self._push(f"else if ({temp_var}.es_ok == 0) {{")
            else:
                if i == 0:
                    self._push(f"if ({temp_var}.tag == TAG_{tag_nombre.upper()}) {{")
                else:
                    self._push(f"else if ({temp_var}.tag == TAG_{tag_nombre.upper()}) {{")
            
            self.indent += 1
            
            # Usar el tipo resuelto del análisis semántico
            tipo_resuelto = caso.tipo_extraido if caso.tipo_extraido else 'int'
            tipo_c = _traducir_tipo_c(tipo_resuelto)
            
            if expr_tipo == 'Resultado_T':
                if tag_nombre == 'ok':
                    if tipo_c == 'CadenaSegura':
                        self._push(f"CadenaSegura {var_nombre} = *({tipo_c}*){temp_var}.datos.ok_valor;")
                    elif tipo_c == 'float':
                        self._push(f"float {var_nombre} = _ptr_to_prim_float({temp_var}.datos.ok_valor);")
                    elif tipo_c == 'int':
                        self._push(f"int {var_nombre} = _ptr_to_prim_int({temp_var}.datos.ok_valor);")
                    else:
                        self._push(f"{tipo_c} {var_nombre} = *({tipo_c}*){temp_var}.datos.ok_valor;")
                else:
                    self._push(f"const char* {var_nombre} = {temp_var}.datos.err_mensaje;")
            else:
                # Generar desempaquetado desde la union .dato.
                if tipo_c == 'CadenaSegura':
                    self._push(f"CadenaSegura {var_nombre} = {temp_var}.dato.valor_str;")
                elif tipo_c == 'float':
                    self._push(f"float {var_nombre} = {temp_var}.dato.valor_float;")
                else:
                    self._push(f"{tipo_c} {var_nombre} = {temp_var}.dato.valor;")
            
            # Registrar la variable extraída para que _tipo_de_expr funcione correctamente
            self._variables[var_nombre] = tipo_c
            
            # Visitar sentencias del cuerpo del caso
            self._push_scope()
            if tipo_c in self._destructor_map:
                self._scope_stack[-1][var_nombre] = tipo_c
            for stmt in caso.cuerpo:
                self._visitar(stmt)
            self._pop_scope()
            
            self.indent -= 1
            self._push("}")

    def _visitar_estructura(self, nodo: DefinicionEstructura):
        campos_pointer: set[str] = set()
        for c in nodo.campos:
            if c.tipo in self._estructuras or c.tipo == nodo.nombre:
                campos_pointer.add(c.nombre)
        # Detectar ADTs (struct con campo 'tag' + campos de datos)
        es_adt = any(c.nombre == 'tag' and c.tipo in ('entero', 'int') for c in nodo.campos)
        self._estructuras[nodo.nombre] = {
            'campos': [(c.nombre, c.tipo) for c in nodo.campos],
            'campos_pointer': campos_pointer,
            'es_adt': es_adt,
        }
        self._push(f"typedef struct {nodo.nombre} {{")
        self.indent += 1
        if es_adt:
            # Emitir tag por separado y union para el resto
            for c in nodo.campos:
                if c.nombre == 'tag' and c.tipo in ('entero', 'int'):
                    self._push(f"int tag;")
                    break
            self._push("union {")
            self.indent += 1
            for c in nodo.campos:
                if c.nombre == 'tag' and c.tipo in ('entero', 'int'):
                    continue
                if c.nombre in campos_pointer:
                    self._push(f"struct {c.tipo}* {c.nombre};")
                else:
                    tipo_c = MAPA_TIPOS_C.get(c.tipo)
                    if tipo_c is not None:
                        self._push(f"{tipo_c} {c.nombre};")
                    else:
                        self._push(f"struct {c.tipo}* {c.nombre};")
            self.indent -= 1
            self._push("} dato;")
        else:
            for c in nodo.campos:
                if c.nombre in campos_pointer:
                    self._push(f"struct {c.tipo}* {c.nombre};")
                else:
                    tipo_c = MAPA_TIPOS_C.get(c.tipo)
                    if tipo_c is not None:
                        self._push(f"{tipo_c} {c.nombre};")
                    else:
                        self._push(f"struct {c.tipo}* {c.nombre};")
        self.indent -= 1
        self._push(f"}} {nodo.nombre};")
        self._push("")
        self._push(f"static inline struct {nodo.nombre} {nodo.nombre}_nuevo() {{")
        self.indent += 1
        self._push(f"struct {nodo.nombre} _r = {{0}};")
        self._push("return _r;")
        self.indent -= 1
        self._push("}")
        self._push("")

    def _visitar_lanzar(self, nodo: SentenciaLanzar):
        if not isinstance(nodo.llamada, LlamadaFuncion):
            return
        func = nodo.llamada.nombre
        if nodo.llamada.argumentos:
            arg = self._expr_a_c(nodo.llamada.argumentos[0])
            self._push("synapse_lanzar_hilo((void*(*)(void*)){0}, (void*)(intptr_t)({1}));".format(func, arg))
        else:
            self._push("synapse_lanzar_hilo((void*(*)(void*)){0}, NULL);".format(func))

    def _visitar_recuperar(self, nodo: SentenciaRecuperar):
        if nodo.accion_critica is None or nodo.plan_b is None:
            return
        accion_str = self._expr_a_c(nodo.accion_critica)
        plan_str = self._expr_a_c(nodo.plan_b)
        self._push("{")
        self.indent += 1
        self._push(f"int _synapse_rc = {accion_str};")
        self._push(f"if (_synapse_rc != 0) {{")
        self.indent += 1
        self._push(f"{plan_str};")
        self.indent -= 1
        self._push("}")
        self.indent -= 1
        self._push("}")

    def _visitar_retornar(self, nodo: SentenciaRetornar):
        excl = ''
        if nodo.expr and isinstance(nodo.expr, Identificador):
            excl = nodo.expr.nombre
            self._tensor_vars_transferidas.add(excl)

        if nodo.expr:
            ret_tipo = self._tipo_de_expr(nodo.expr)
            ret_expr = self._expr_a_c(nodo.expr)
            temp = f"_ret_{nodo.linea or 0}"
            self._push(f"{ret_tipo} {temp} = {ret_expr};")
            self._emit_all_destructors(exclude_var=excl)
            self._push(f"return {temp};")
        else:
            self._emit_all_destructors(exclude_var=excl)
            self._push("return;")

    def _visitar_escuchar(self, nodo: SentenciaEscuchar):
        self._contador_listener += 1
        idx = self._contador_listener

        canal_expr = self._expr_a_c(nodo.canal)

        if isinstance(nodo.respuesta, LlamadaFuncion):
            resp_nombre = nodo.respuesta.nombre
        else:
            resp_nombre = "/* error */"

        func_lines = []
        func_lines.append(f"void* _listener_fn_{idx}(void* arg) {{")
        func_lines.append("    (void)arg;")
        func_lines.append(f"    CanalConcurrencia* _canal = {canal_expr};")
        func_lines.append("    while (1) {")
        func_lines.append("        void* _paquete = canal_recibir(_canal);")
        func_lines.append("        if (!_paquete) break;")
        func_lines.append(f"        {resp_nombre}(_paquete);")
        func_lines.append("    }")
        func_lines.append("    return NULL;")
        func_lines.append("}")
        self._listener_funciones.append("\n".join(func_lines))

        self._push(f'pthread_t _listener_pth_{idx};')
        self._push(f'pthread_create(&_listener_pth_{idx}, NULL, _listener_fn_{idx}, NULL);')
        self._push(f'pthread_detach(_listener_pth_{idx});')

    def _visitar_declaracion(self, nodo: DeclaracionVariable):
        tipo = MAPA_TIPOS_C.get(nodo.tipo, nodo.tipo)
        val = self._expr_a_c(nodo.expresion)
        desde_llamada = isinstance(nodo.expresion, LlamadaFuncion)
        if nodo.nombre not in self._variables:
            self._variables[nodo.nombre] = nodo.tipo
            self._push(f"{tipo} {nodo.nombre} = {val};")
            if tipo == 'Tensor':
                self._tensor_vars.add(nodo.nombre)
            elif tipo == 'Canal':
                self._canal_vars.add(nodo.nombre)
            else:
                self._register_var(nodo.nombre, nodo.tipo, desde_llamada)
        else:
            old_tipo = self._variables.get(nodo.nombre)
            if old_tipo in self._destructor_map:
                dtor = self._destructor_map[old_tipo]
                self._push(f"{dtor}({nodo.nombre});")
                self._unregister_var(nodo.nombre)
            if nodo.nombre in self._tensor_vars and tipo == 'Tensor':
                self._push(f"{self._syn_free(f'{nodo.nombre}.datos')};")
            self._push(f"{nodo.nombre} = {val};")
            self._variables[nodo.nombre] = nodo.tipo
            if tipo == 'Tensor':
                self._tensor_vars.add(nodo.nombre)
            elif tipo == 'Canal':
                self._canal_vars.add(nodo.nombre)
            else:
                self._register_var(nodo.nombre, nodo.tipo, desde_llamada)

    def _visitar_asignacion(self, nodo: AsignacionVariable):
        tipo = self._tipo_de_expr(nodo.expresion)
        val = self._expr_a_c(nodo.expresion)
        desde_llamada = isinstance(nodo.expresion, LlamadaFuncion)
        if nodo.nombre not in self._variables:
            self._variables[nodo.nombre] = tipo
            self._push(f"{tipo} {nodo.nombre} = {val};")
            if tipo == 'Tensor':
                self._tensor_vars.add(nodo.nombre)
            elif tipo == 'Canal':
                self._canal_vars.add(nodo.nombre)
            else:
                self._register_var(nodo.nombre, tipo, desde_llamada)
        else:
            old_tipo = self._variables.get(nodo.nombre)
            if old_tipo in self._destructor_map:
                dtor = self._destructor_map[old_tipo]
                self._push(f"{dtor}({nodo.nombre});")
                self._unregister_var(nodo.nombre)
            if nodo.nombre in self._tensor_vars and tipo == 'Tensor':
                self._push(f"{self._syn_free(f'{nodo.nombre}.datos')};")
            self._push(f"{nodo.nombre} = {val};")
            self._variables[nodo.nombre] = tipo
            if tipo == 'Tensor':
                self._tensor_vars.add(nodo.nombre)
            elif tipo == 'Canal':
                self._canal_vars.add(nodo.nombre)
            else:
                self._register_var(nodo.nombre, tipo, desde_llamada)

    def _visitar_log(self, nodo: LogLlamada):
        fmt_parts: List[str] = []
        printf_args: List[str] = []
        arg_start = 0
        separar = False
        if nodo.argumentos and isinstance(nodo.argumentos[0], LiteralCadena):
            fmt_parts.append(nodo.argumentos[0].valor)
            arg_start = 1
            separar = True
        for i in range(arg_start, len(nodo.argumentos)):
            arg = nodo.argumentos[i]
            tipo = self._tipo_de_expr(arg)
            esp = " " if separar else ""
            fmt_parts.append(f"{esp}{self._formato_espec(tipo)}")
            arg_expr = self._expr_a_c(arg)
            if tipo == 'CadenaSegura':
                arg_expr = f'({arg_expr}).datos'
            printf_args.append(arg_expr)
            separar = True
        fmt_str = "".join(fmt_parts) + "\\n"
        if printf_args:
            self._push(f'printf("{fmt_str}", {", ".join(printf_args)});')
        else:
            self._push(f'printf("{fmt_str}");')

    def _tipo_de_expr(self, nodo: Nodo) -> str:
        if isinstance(nodo, LiteralDecimal):
            return 'float'
        if isinstance(nodo, LiteralNumero):
            return 'int'
        if isinstance(nodo, LiteralCadena):
            return 'CadenaSegura'
        if isinstance(nodo, LiteralBooleano):
            return 'int'
        if isinstance(nodo, ExprTensor):
            return 'Tensor'
        if isinstance(nodo, Identificador):
            if nodo.nombre == 'nulo':
                return 'void*'
            if nodo.nombre in self._variables:
                return self._variables[nodo.nombre]
            if nodo.nombre in self._const_types:
                return self._const_types[nodo.nombre]
            return 'int'
        if isinstance(nodo, ArgumentoTransferido):
            return self._tipo_de_expr(nodo.expr)
        if isinstance(nodo, ExprAccesoCampo):
            obj_tipo = self._tipo_de_expr(nodo.objeto).rstrip('*')
            if obj_tipo.startswith('struct '):
                nombre_struct = obj_tipo[7:]
                info = self._estructuras.get(nombre_struct)
                if info:
                    for c_nombre, c_tipo in info.get('campos', []):
                        if c_nombre == nodo.nombre_campo:
                            if c_tipo in self._estructuras:
                                return f'struct {c_tipo}'
                            return MAPA_TIPOS_C.get(c_tipo, 'int')
            return 'int'
        if isinstance(nodo, OpBinaria):
            tipo_izq = self._tipo_de_expr(nodo.izquierdo)
            tipo_der = self._tipo_de_expr(nodo.derecho)
            if tipo_izq == 'CadenaSegura' and tipo_der == 'CadenaSegura' and nodo.operador == '+':
                return 'CadenaSegura'
            if 'float' in (tipo_izq, tipo_der):
                return 'float'
            return 'int'
        if isinstance(nodo, OpUnaria):
            tipo_in = self._tipo_de_expr(nodo.expr)
            if tipo_in == 'float':
                return 'float'
            return 'int'
        if isinstance(nodo, ExprObtenerDireccion):
            return f"{self._tipo_de_expr(nodo.expr)}*"
        if isinstance(nodo, ExprDereferencia):
            return self._tipo_de_expr(nodo.expr).rstrip('*')
        if isinstance(nodo, ExprAsm):
            return 'void'
        if isinstance(nodo, ExprCrearCanal):
            return 'CanalConcurrencia*'
        if isinstance(nodo, ExprRecibirCanal):
            return 'Resultado_T'
        if isinstance(nodo, LlamadaFuncion):
            if nodo.nombre in _BUILTINS:
                return _BUILTINS[nodo.nombre]
            if nodo.nombre in self._estructuras:
                return f'struct {nodo.nombre}'
            if nodo.nombre in self._func_return_types:
                tipo = self._func_return_types[nodo.nombre]
                if tipo in ('nulo', 'vacio', 'void'):
                    return 'void'
                tipo_c = MAPA_TIPOS_C.get(tipo)
                if tipo_c is not None:
                    return tipo_c
                return f'struct {tipo}'
            return self._variables.get(nodo.nombre, 'int')
        if isinstance(nodo, AsignacionVariable):
            return self._tipo_de_expr(nodo.expresion)
        if isinstance(nodo, DeclaracionVariable):
            return nodo.tipo
        if isinstance(nodo, LiteralBooleano):
            return 'booleano'
        return 'int'

    def _formato_espec(self, tipo: str) -> str:
        if tipo == 'Canal':
            return '%d'
        if tipo == 'CadenaSegura' or 'char*' in tipo:
            return '%s'
        if tipo in ('float', 'double'):
            return '%f'
        return '%d'

    def _visitar_mientras(self, nodo: SentenciaMientras):
        cond = self._expr_a_c(nodo.condicion)
        self._push(f"while ({cond}) {{")
        self.indent += 1
        self._push_scope()
        for s in nodo.cuerpo:
            self._visitar(s)
        self._pop_scope()
        self.indent -= 1
        self._push("}")

    def _visitar_para(self, nodo: SentenciaPara):
        init_var = nodo.inicializacion.nombre if nodo.inicializacion else ''
        init_val = self._expr_a_c(nodo.inicializacion.expresion) if nodo.inicializacion else ''
        init_tipo = self._tipo_de_expr(nodo.inicializacion.expresion) if nodo.inicializacion else 'int'
        cond = self._expr_a_c(nodo.condicion) if nodo.condicion else '1'
        inc_val = self._expr_a_c(nodo.incremento.expresion) if nodo.incremento else ''
        if init_var and init_var not in self._variables:
            self._variables[init_var] = init_tipo
            self._push(f"{init_tipo} {init_var} = {init_val};")
        else:
            self._push(f"{init_var} = {init_val};")
        self._push(f"for (; {cond}; {init_var} = {inc_val}) {{")
        self.indent += 1
        self._push_scope()
        for s in nodo.cuerpo:
            self._visitar(s)
        self._pop_scope()
        self.indent -= 1
        self._push("}")

    def _expr_a_c(self, nodo: Nodo, ctx_func: str = '') -> str:
        if isinstance(nodo, LiteralNumero):
            return str(nodo.valor)
        if isinstance(nodo, LiteralDecimal):
            return f"{nodo.valor}f"
        if isinstance(nodo, LiteralBooleano):
            return '1' if nodo.valor else '0'
        if isinstance(nodo, LiteralCadena):
            val = nodo.valor.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
            encoded = nodo.valor.encode('utf-8')
            return f'(CadenaSegura){{ .longitud = {len(encoded)}, .datos = "{val}" }}'
        if isinstance(nodo, Identificador):
            return "NULL" if nodo.nombre == "nulo" else nodo.nombre
        if isinstance(nodo, ExprTensor):
            filas = self._expr_a_c(nodo.filas)
            cols = self._expr_a_c(nodo.columnas)
            _calloc = self._syn_calloc(f'{filas} * {cols}', 'sizeof(float)')
            return f'(Tensor){{ .filas = {filas}, .columnas = {cols}, .datos = (float*){_calloc} }}'
        if isinstance(nodo, LlamadaFuncion):
            if nodo.nombre in self._estructuras and not nodo.argumentos:
                return f"{nodo.nombre}_nuevo()"
            args_parts = []
            extern_params = self._externas.get(nodo.nombre, [])
            if not extern_params and nodo.nombre in _C_FUNCTIONS_NEED_DATOS:
                extern_params = _C_FUNCTIONS_NEED_DATOS[nodo.nombre]
            for i, a in enumerate(nodo.argumentos):
                if isinstance(a, ArgumentoTransferido):
                    if isinstance(a.expr, Identificador):
                        self._tensor_vars_transferidas.add(a.expr.nombre)
                        if a.expr.nombre in self._canal_vars:
                            self._canal_vars_cerradas.add(a.expr.nombre)
                    arg_expr = self._expr_a_c(a.expr)
                    tipo_arg = self._tipo_de_expr(a.expr)
                    if i < len(extern_params) and extern_params[i] == 'char*' and tipo_arg == 'CadenaSegura':
                        arg_expr = f"({arg_expr}).datos"
                    elif i < len(extern_params) and extern_params[i].endswith('*') and tipo_arg.startswith('struct '):
                        ep_base = extern_params[i].rstrip('*')
                        if MAPA_TIPOS_C.get(ep_base) is None and not tipo_arg.endswith('*'):
                            arg_expr = f"(&{arg_expr})"
                    if nodo.nombre in _FUNCIONES_ESPERAN_TEXTO:
                        try:
                            arg_expr = _aplicar_coercion(arg_expr, tipo_arg, 'CadenaSegura', getattr(nodo, 'linea', 0))
                        except SyntaxError as e:
                            raise e
                    args_parts.append(arg_expr)
                else:
                    arg_expr = self._expr_a_c(a)
                    tipo_arg = self._tipo_de_expr(a)
                    if i < len(extern_params) and extern_params[i] == 'char*' and tipo_arg == 'CadenaSegura':
                        arg_expr = f"({arg_expr}).datos"
                    elif i < len(extern_params) and extern_params[i].endswith('*') and tipo_arg.startswith('struct '):
                        ep_base = extern_params[i].rstrip('*')
                        if MAPA_TIPOS_C.get(ep_base) is None and not tipo_arg.endswith('*'):
                            arg_expr = f"(&{arg_expr})"
                    if nodo.nombre in _FUNCIONES_ESPERAN_TEXTO:
                        try:
                            arg_expr = _aplicar_coercion(arg_expr, tipo_arg, 'CadenaSegura', getattr(nodo, 'linea', 0))
                        except SyntaxError as e:
                            raise e
                    args_parts.append(arg_expr)
            args = ", ".join(args_parts)
            _nombre = nodo.nombre.replace('.', '_')
            return f"{_nombre}({args})"
        if isinstance(nodo, ArgumentoTransferido):
            return self._expr_a_c(nodo.expr)
        if isinstance(nodo, ExprAccesoCampo):
            obj = self._expr_a_c(nodo.objeto)
            obj_tipo = self._tipo_de_expr(nodo.objeto)
            es_puntero = obj_tipo.endswith('*')
            nombre_struct = ''
            if not es_puntero and obj_tipo.startswith('struct '):
                nombre_struct = obj_tipo[7:]
                info = self._estructuras.get(nombre_struct)
                if info and nodo.nombre_campo in info.get('campos_pointer', set()):
                    es_puntero = True
            sep = '->' if es_puntero else '.'
            es_adt = bool(self._estructuras.get(nombre_struct, {}).get('es_adt'))
            campo_es_tag = (nodo.nombre_campo == 'tag' and es_adt)
            if es_adt and not campo_es_tag:
                return f"{obj}{sep}dato.{nodo.nombre_campo}"
            return f"{obj}{sep}{nodo.nombre_campo}"
        if isinstance(nodo, OpBinaria):
            izq = self._expr_a_c(nodo.izquierdo)
            der = self._expr_a_c(nodo.derecho)
            tipo_izq = self._tipo_de_expr(nodo.izquierdo)
            tipo_der = self._tipo_de_expr(nodo.derecho)
            if nodo.operador in ('==', '!=') and tipo_izq == 'CadenaSegura' and tipo_der == 'CadenaSegura':
                op = '!=' if nodo.operador == '!=' else '=='
                return f"(strcmp({izq}.datos, {der}.datos) {op} 0)"
            if nodo.operador == '+' and tipo_izq == 'CadenaSegura' and tipo_der == 'CadenaSegura':
                return f"concat({izq}, {der})"
            return f"({izq} {nodo.operador} {der})"
        if isinstance(nodo, OpUnaria):
            return f"({nodo.operador}{self._expr_a_c(nodo.expr)})"
        if isinstance(nodo, ExprObtenerDireccion):
            return f"(&{self._expr_a_c(nodo.expr)})"
        if isinstance(nodo, ExprDereferencia):
            return f"(*{self._expr_a_c(nodo.expr)})"
        if isinstance(nodo, ExprAsm):
            import re
            result = nodo.instruccion
            result = re.sub(r'\bretornar\b', 'return', result)
            result = re.sub(r'\bverdadero\b', '1', result)
            result = re.sub(r'\bfalso\b', '0', result)
            def _asm_strcmp(m):
                v = m.group(1)
                if v in self._variables and self._variables[v] == 'CadenaSegura':
                    return f'strcmp({v}.datos,'
                return f'strcmp({v},'
            result = re.sub(r'\bstrcmp\((\w+)\s*,', _asm_strcmp, result)
            return result
        if isinstance(nodo, ExprCrearCanal):
            cap = self._expr_a_c(nodo.capacidad) if nodo.capacidad else "10"
            return f"canal_crear({cap})"
        if isinstance(nodo, ExprRecibirCanal):
            canal = self._expr_a_c(nodo.canal)
            return f"(Resultado_T){{ .es_ok = 1, .datos = {{ .ok_valor = canal_recibir({canal}) }} }}"
        return "/* error en traduccion */"
