"""
GeneratorContext — Estado centralizado del generador de código C.

Responsabilidad única: mantener el estado mutable (buffer, indentación,
símbolos, scopes, destructores) y proveer métodos atómicos de escritura.
No contiene lógica de AST.
"""

from typing import List, Optional, Set, Dict
from compilador.ast_nodes import (
    Programa, DefinicionFuncion, DefinicionEstructura, Nodo,
)


# ================================================================
# Module-level constants (backward-compatible with old generator.py)
# ================================================================

MAPA_TIPOS_C: Dict[str, str] = {
    'entero': 'int', 'int': 'int',
    'vacio': 'void', 'nulo': 'void',
    'decimal': 'float', 'real': 'float', 'flotante': 'float',
    'Tensor': 'Tensor', 'tensor': 'Tensor',
    'Canal': 'Canal', 'canal': 'Canal',
    'texto': 'CadenaSegura', 'cadena': 'CadenaSegura',
    'booleano': 'int', 'logico': 'int',
    'void': 'void', 'char': 'char',
    'double': 'double', 'puntero': 'void*', 'void*': 'void*',
}


class GeneratorContext:
    """Contexto mutable del generador. Contiene buffer de salida,
    tabla de variables, scopes RAII, mapeo de tipos, etc."""

    def __init__(self, programa: Programa):
        self.programa = programa
        self.lineas: List[str] = []
        self.indent = 0

        # Builtin function signature maps
        self._BUILTINS: Dict[str, str] = {
            'reserva': 'tensor', 'libera': 'void',
            'crear_tensor': 'tensor', 'suma_tensor': 'tensor',
            'producto_punto': 'tensor', 'abrir': 'Canal',
            'leer': 'texto', 'escribir': 'void',
            'escribir_linea': 'void', 'leer_linea': 'texto',
            'cerrar': 'void', 'suma': 'tensor', 'producto': 'tensor',
            'relu': 'tensor', 'tokenizar': 'int',
            'parsear': 'struct Programa', 'generar': 'int',
            'concat': 'texto', '_argc': 'int',
            '_argv': 'texto', 'salir': 'void',
            'canal_crear': 'CanalConcurrencia*', 'canal_enviar': 'void',
            'canal_recibir': 'puntero', 'cerrar_canal': 'void',
            'texto_a_entero': 'int', 'texto_a_decimal': 'float',
            'decimal_a_texto': 'texto', 'entero_a_texto': 'texto',
            'debug_registrar_evento': 'Resultado', 'debug_trace': 'Resultado',
            'debug_iniciar_sesion': 'TraceSession', 'debug_finalizar_sesion': 'Resultado',
            'cluster_generar_par_claves': 'texto', 'cluster_firmar_mensaje': 'texto',
            'cluster_verificar_firma': 'int', 'cluster_iniciar_nodo': 'int',
            'cluster_detener_nodo': 'int', 'cluster_enviar_hello': 'int',
            'cluster_canal_remoto_enviar': 'int', 'cluster_recibir_paquete': 'texto',
            'ws_inicializar': 'int', 'ws_encolar': 'int',
            'ws_desencolar': 'texto', 'ws_profundidad': 'int',
            'ws_carga_estimada': 'int', 'ws_enviar_solicitud_robo': 'int',
            'ws_procesar_mensaje': 'texto', 'ws_ultima_robada': 'texto',
            'ws_reenviar_respuesta': 'int',
            'raft_inicializar': 'int', 'raft_iniciar': 'int',
            'raft_tick': 'int', 'raft_procesar_solicitud_voto': 'int',
            'raft_procesar_respuesta_voto': 'int', 'raft_procesar_heartbeat': 'int',
            'raft_estado': 'int', 'raft_term_actual': 'int',
            'raft_lider_actual': 'int', 'raft_log_entradas': 'int',
            'raft_commit_index': 'int', 'raft_forzar_abdicacion': 'int',
            'raft_agregar_entrada': 'int', 'raft_reiniciar_nodo': 'int',
            'raft_info': 'texto',
        }

        self._RUNTIME_BUILTINS: frozenset = frozenset({
            'escribir', 'escribir_linea', 'leer_linea', 'abrir', 'leer', 'cerrar',
            'math_crear_tensor', 'math_suma_tensor', 'math_producto_punto', 'math_relu',
            'mem_reserva', 'mem_libera', 'math_suma', 'math_producto',
            'crear_tensor', 'suma_tensor', 'producto_punto', 'relu',
            'reserva', 'libera', 'suma', 'producto',
            'texto_a_entero', 'texto_a_decimal', 'decimal_a_texto',
            'salir', 'canal_crear', 'canal_enviar', 'canal_recibir', 'cerrar_canal',
            'debug_registrar_evento', 'debug_trace', 'debug_iniciar_sesion', 'debug_finalizar_sesion',
            'cluster_generar_par_claves', 'cluster_firmar_mensaje', 'cluster_verificar_firma',
            'cluster_iniciar_nodo', 'cluster_detener_nodo', 'cluster_enviar_hello',
            'cluster_canal_remoto_enviar', 'cluster_recibir_paquete',
            'ws_inicializar', 'ws_encolar', 'ws_desencolar',
            'ws_profundidad', 'ws_carga_estimada', 'ws_enviar_solicitud_robo',
            'ws_procesar_mensaje', 'ws_ultima_robada', 'ws_reenviar_respuesta',
            'raft_inicializar', 'raft_iniciar', 'raft_tick',
            'raft_procesar_solicitud_voto', 'raft_procesar_respuesta_voto',
            'raft_procesar_heartbeat', 'raft_estado', 'raft_term_actual',
            'raft_lider_actual', 'raft_log_entradas', 'raft_commit_index',
            'raft_forzar_abdicacion', 'raft_agregar_entrada', 'raft_reiniciar_nodo',
            'raft_info',
        })

        self._TABLA_COERCION: Dict[tuple, str] = {
            ('float', 'CadenaSegura'): 'decimal_a_texto',
            ('int', 'CadenaSegura'): 'entero_a_texto',
        }

        self._FUNCIONES_ESPERAN_TEXTO: set = {
            'escribir', 'escribir_linea', 'abrir', 'concat',
        }

        self._C_FUNCTIONS_NEED_DATOS: Dict[str, list] = {
            'strcmp': ['char*', 'char*'], 'strncpy': ['char*', 'char*'],
            'strcpy': ['char*', 'char*'], 'strcat': ['char*', 'char*'],
            'strlen': ['char*'], 'fopen': ['char*', 'char*'],
            'fclose': ['FILE*'], 'fgets': ['char*', 'int', 'FILE*'],
            'fputs': ['char*', 'FILE*'], 'fprintf': ['FILE*', 'char*'],
            'printf': ['char*'], 'sprintf': ['char*', 'char*'],
            'fread': ['void*', 'size_t', 'size_t', 'FILE*'],
            'fwrite': ['void*', 'size_t', 'size_t', 'FILE*'],
            'fseek': ['FILE*', 'long', 'int'], 'ftell': ['FILE*'],
            'rewind': ['FILE*'], 'remove': ['char*'], 'rename': ['char*', 'char*'],
            'qsort': ['void*', 'size_t', 'size_t', 'void*'],
            'bsearch': ['void*', 'void*', 'size_t', 'size_t', 'void*'],
            'atoi': ['char*'], 'atol': ['char*'], 'atof': ['char*'],
            'strtol': ['char*', 'char**', 'int'], 'strtod': ['char*', 'char**'],
            'strtok': ['char*', 'char*'], 'perror': ['char*'],
            'memcpy': ['void*', 'void*', 'size_t'],
            'memset': ['void*', 'int', 'size_t'],
            'memmove': ['void*', 'void*', 'size_t'],
        }

        # OO types that have FULL typedef definitions in the header
        # (these must be skipped by visitar_estructura to avoid redefinition)
        self._HEADER_DEFINED_TYPES: frozenset = frozenset({
            'Token', 'Nodo', 'ListaNodo', 'Programa',
        })

        # Remaining OO types (only forward-declared in header, need full definitions
        # from visitar_estructura for sizeof() and variable declarations)
        self._OO_TYPES: frozenset = frozenset({
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
            'ExprObtenerDireccion', 'ExprDereferencia',
        })

        # Variable / scope tracking
        self._variables: Dict[str, str] = {}
        self._const_types: Dict[str, str] = {}
        self._funciones_emitidas: set = set()
        self._tensor_vars: set = set()
        self._tensor_vars_transferidas: set = set()
        self._canal_vars: set = set()
        self._canal_vars_cerradas: set = set()
        self._canal_vars_concurrencia: set = set()
        self._listener_funciones: List[str] = []
        self._deferred_wrappers: List[str] = []
        self._deferred_typedefs: List[str] = []
        self._deferred_wrap_decls: List[str] = []
        self._emitted_typedefs: set = set()  # rastreo estricto contra duplicacion estatica
        self._emitted_wrap_decls: set = set()  # idem para forward declarations
        self._consumed_vars: set = set()  # vars already explicitly destroyed (move semantics)
        self._scope_stack: List[Dict[str, str]] = []
        self._strings_heap: set = set()
        self._contador_thread = 0
        self._contador_listener = 0

        # Struct + function tracking
        self._estructuras: Dict[str, dict] = {}
        self._func_return_types: Dict[str, str] = {}
        self._func_param_types: Dict[str, List[str]] = {}
        self._in_function_scope = False
        self._garantizas_actuales: List[Nodo] = []
        self._current_func_return_type: str = 'int'

        # Emit flags
        self._gen_tok_emitido = False
        self._gen_parse_emitido = False
        self._gen_defs_emitido = False
        self._externas: Dict[str, List[str]] = {}
        self._linker_libs: set = set()

        # Fields that should be emitted as arrays (not scalars)
        # Workaround: Synapse asm() blocks access these with subscript,
        # but the struct definition uses a scalar type (entero).
        self._ARRAY_OVERRIDE_FIELDS: Dict[str, tuple] = {
            'pila_indent': ('int', 64),
            '_P_pila_indent': ('int', 64),
        }



        # Destructor map for RAII types
        # NOTE: Use Synapse type names (texto not CadenaSegura) for consistency
        # with tipo_de_expr and _variables which store Synapse types.
        self._destructor_map: Dict[str, str] = {
            'CadenaSegura': '_syn_texto_liberar',
            'texto': '_syn_texto_liberar',
            'cadena': '_syn_texto_liberar',
            'NodoJson': '_json_nodo_liberar',
            'struct NodoJson': '_json_nodo_liberar',
            'NodoToml': '_toml_nodo_liberar',
            'struct NodoToml': '_toml_nodo_liberar',
        }

    # ================================================================
    # Atomic write operations
    # ================================================================

    def write_line(self, linea: str = ""):
        if linea == "":
            self.lineas.append("")
        else:
            self.lineas.append("    " * self.indent + linea)

    def write_line_expr(self, expr: str):
        self.write_line(expr)

    def inc_indent(self):
        self.indent += 1

    def dec_indent(self):
        self.indent -= 1

    # ================================================================
    # Scope management
    # ================================================================

    def push_scope(self):
        self._scope_stack.append({})

    def pop_scope(self):
        scope = self._scope_stack.pop() if self._scope_stack else {}
        for var_name in reversed(list(scope.keys())):
            # Move semantics: skip vars already explicitly consumed/destroyed
            if var_name in self._consumed_vars:
                self._consumed_vars.discard(var_name)
                continue
            dtor = self._destructor_map.get(scope[var_name])
            if dtor:
                self.write_line(f"{dtor}({var_name});")

    def emit_all_destructors(self, exclude_var: str = ''):
        for scope in reversed(self._scope_stack):
            for var_name in reversed(list(scope.keys())):
                if var_name == exclude_var:
                    continue
                # Move semantics: skip vars already explicitly consumed/destroyed
                if var_name in self._consumed_vars:
                    self._consumed_vars.discard(var_name)
                    continue
                dtor = self._destructor_map.get(scope[var_name])
                if dtor:
                    self.write_line(f"{dtor}({var_name});")
        for scope in self._scope_stack:
            scope.clear()

    def register_var(self, nombre: str, tipo: str, desde_llamada: bool):
        if self._scope_stack and desde_llamada and tipo in self._destructor_map:
            self._scope_stack[-1][nombre] = tipo

    def unregister_var(self, nombre: str):
        for scope in self._scope_stack:
            scope.pop(nombre, None)

    def is_no_std(self) -> bool:
        return self.programa.is_no_std

    # ================================================================
    # Allocator helpers (redirect in no_std)
    # ================================================================

    def syn_malloc(self, size_expr: str) -> str:
        if self.is_no_std():
            return f'__syn_asignar({size_expr})'
        return f'malloc({size_expr})'

    def syn_calloc(self, n_expr: str, size_expr: str) -> str:
        if self.is_no_std():
            return f'__syn_asignar({n_expr} * {size_expr})'
        return f'calloc({n_expr}, {size_expr})'

    def syn_free(self, ptr_expr: str) -> str:
        if self.is_no_std():
            return f'__syn_liberar({ptr_expr})'
        return f'free({ptr_expr})'

    def syn_pool_alloc(self, size_expr: str) -> str:
        if self.is_no_std():
            return f'__syn_asignar({size_expr})'
        return f'pool_alloc({size_expr})'

    def syn_pool_free(self, ptr_expr: str) -> str:
        if self.is_no_std():
            return f'__syn_liberar({ptr_expr})'
        return f'pool_free({ptr_expr})'

    # ================================================================
    # Helpers
    # ================================================================

    def encontrar_principal(self) -> Optional[str]:
        for s in self.programa.sentencias:
            if isinstance(s, DefinicionFuncion) and s.nombre == 'principal':
                return s.nombre
        return None

    def traducir_tipo_c(self, tipo_synapse: str) -> str:
        if tipo_synapse.startswith('Canal<') and tipo_synapse.endswith('>'):
            return 'CanalConcurrencia*'
        if tipo_synapse.startswith('Resultado<'):
            return 'Resultado_T'
        tipo_c = MAPA_TIPOS_C.get(tipo_synapse)
        if tipo_c is not None:
            return tipo_c
        return f"struct {tipo_synapse}"

    def aplicar_coercion(self, expr_c: str, tipo_origen: str,
                         tipo_destino: str, linea: int = 0) -> str:
        clave = (tipo_origen, tipo_destino)
        if clave in self._TABLA_COERCION:
            return f"{self._TABLA_COERCION[clave]}({expr_c})"
        if tipo_origen == tipo_destino:
            return expr_c
        raise SyntaxError(
            f"Error semántico: no se puede coercer {tipo_origen} a "
            f"{tipo_destino} (línea {linea})")

    def prim_int_to_ptr(self, value: str) -> str:
        return f"_synapse_box_int({value})"

    def prim_float_to_ptr(self, value: str) -> str:
        return f"_synapse_box_float({value})"

    def ptr_to_prim_int(self, ptr: str) -> str:
        return f"_synapse_unbox_int({ptr})"

    def ptr_to_prim_float(self, ptr: str) -> str:
        return f"_synapse_unbox_float({ptr})"

    def generar(self) -> str:
        """Finalize and return the generated C code."""
        return "\n".join(self.lineas)
