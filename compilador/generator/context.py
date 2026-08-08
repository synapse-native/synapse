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
    # A5.2 (D-7): ABI Manual 2 §4.1 L267-268 — entero/int → int64_t (8 bytes)
    'entero': 'int64_t', 'int': 'int64_t', 'Entero': 'int64_t',
    'vacio': 'void', 'nulo': 'void', 'Nulo': 'void',
    # A5.2 (D-7): decimal/real/flotante/float → double (8 bytes)
    'decimal': 'double', 'real': 'double', 'flotante': 'double', 'Flotante': 'double', 'Decimal': 'double',
    'float': 'double',
    'Tensor': 'Tensor', 'tensor': 'Tensor',
    'Canal': 'Canal', 'canal': 'Canal',
    'texto': 'CadenaSegura', 'cadena': 'CadenaSegura', 'Texto': 'CadenaSegura',
    'booleano': 'int', 'logico': 'int', 'Booleano': 'int', 'Logico': 'int',
    'void': 'void', 'char': 'char',
    'double': 'double', 'puntero': 'void*', 'Puntero': 'void*', 'void*': 'void*',
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
            'tr_inicializar_recording': 'int', 'tr_grabar_bifurcacion': 'int',
            'tr_grabar_snapshot': 'int', 'tr_grabar_llamada': 'int',
            'tr_grabar_retorno': 'int', 'tr_grabar_error': 'int',
            'tr_buscar_evento': 'int', 'tr_obtener_evento': 'texto',
            'tr_reproducir_hasta': 'int', 'tr_indice_ultimo_error': 'int',
            'tr_total_eventos': 'int',
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
            'cm_inicializar': 'int', 'cm_serializar_checkpoint': 'texto',
            'cm_deserializar_checkpoint': 'texto', 'cm_verificar_integridad': 'int',
            'cm_restaurar_checkpoint': 'int', 'cm_migrar_tarea': 'texto',
            'cm_migrar_entre_nodos': 'int', 'cm_ultima_migracion': 'texto',
            'cm_migraciones_completadas': 'int', 'cm_migraciones_fallidas': 'int',
            'rp_inicializar': 'int', 'rp_establecer_breakpoint': 'int',
            'rp_eliminar_breakpoint': 'int', 'rp_limpiar_breakpoints': 'int',
            'rp_buscar_breakpoint': 'int', 'rp_retroceder': 'int',
            'rp_posicion_actual': 'int', 'rp_ir_a_pre_error': 'int',
            'rp_inspeccionar_variable': 'texto', 'rp_pila_llamadas': 'texto',
            'rp_buscar_cambio_variable': 'int',
            'ms_tomar_en': 'texto', 'ms_diferenciar': 'texto',
            'ms_diff_entre': 'texto', 'ms_snapshot_contar_vars': 'int',
            'ms_snapshot_tamano': 'int', 'ms_snapshot_contiene': 'texto',
            'len': 'int', 'subcadena': 'texto', 'empieza_con': 'int',
        }

        self._RUNTIME_BUILTINS: frozenset = frozenset({
            'escribir', 'escribir_linea', 'leer_linea', 'str_eq', 'abrir', 'leer', 'cerrar',
            'math_crear_tensor', 'math_suma_tensor', 'math_producto_punto', 'math_relu',
            'mem_reserva', 'mem_libera', 'math_suma', 'math_producto',
            'crear_tensor', 'suma_tensor', 'producto_punto', 'relu',
            'reserva', 'libera', 'suma', 'producto',
            'texto_a_entero', 'texto_a_decimal', 'decimal_a_texto',
            'salir', 'canal_crear', 'canal_enviar', 'canal_recibir', 'cerrar_canal',
            'debug_registrar_evento', 'debug_trace', 'debug_iniciar_sesion', 'debug_finalizar_sesion',
            'tr_inicializar_recording', 'tr_grabar_bifurcacion',
            'tr_grabar_snapshot', 'tr_grabar_llamada', 'tr_grabar_retorno',
            'tr_grabar_error', 'tr_buscar_evento', 'tr_obtener_evento',
            'tr_reproducir_hasta', 'tr_indice_ultimo_error', 'tr_total_eventos',
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
            'cm_inicializar', 'cm_serializar_checkpoint',
            'cm_deserializar_checkpoint', 'cm_verificar_integridad',
            'cm_restaurar_checkpoint', 'cm_migrar_tarea',
            'cm_migrar_entre_nodos', 'cm_ultima_migracion',
            'cm_migraciones_completadas', 'cm_migraciones_fallidas',
            'rp_inicializar', 'rp_establecer_breakpoint',
            'rp_eliminar_breakpoint', 'rp_limpiar_breakpoints',
            'rp_buscar_breakpoint', 'rp_retroceder',
            'rp_posicion_actual', 'rp_ir_a_pre_error',
            'rp_inspeccionar_variable', 'rp_pila_llamadas',
            'rp_buscar_cambio_variable',
            'ms_tomar_en', 'ms_diferenciar', 'ms_diff_entre',
            'ms_snapshot_contar_vars', 'ms_snapshot_tamano', 'ms_snapshot_contiene',
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
        # F1.2: alias de tipos declarados con `tipo X = <tipo>` (Manual 2 §2
        # declaracion_tipo). traducir_tipo_c resuelve el alias antes del fallback.
        self._tipo_aliases: Dict[str, str] = {}
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

        # Scope depth tracking for lifetime boundary markers (M22.1)
        self._scope_depth = 0
        self._safe_mode = False  # --safe flag for borrow checking

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



        # Types that MUST be passed by pointer (not by value) per Manual 3 §3.3
        # M21.4: RegionGraph y UnionFind (lifetimes.syn) se pasan por puntero
        # para que region_agregar_restriccion/uf_union muten el grafo real
        # (por valor, g.total_constraints++ se perdería en la copia).
        # FASE A (A2.3): ParserEst (parser.syn) — mismo defecto por valor:
        # est.posicion/total_nodos/hay_error se perdían en cada llamada helper
        # (BUG 4 de la auditoría A2.3: el parser nativo era código muerto).
        # El call-site añade & automáticamente (emit_expressions.py); el acceso
        # de campo emite -> (precedente AnalizadorSemanticoEst).
        self._POINTER_TYPES: frozenset = frozenset({
            'AnalizadorSemanticoEst', 'RegionGraph', 'UnionFind', 'ParserEst',
        })

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
        self._scope_depth += 1

    def pop_scope(self):
        self._scope_depth -= 1
        # M22.1: Emitir marcador de salida de scope ANTES de destructores
        if self._scope_depth >= 0:
            self.write_line(f"  /* [Lifetime Scope: exit depth={self._scope_depth}] */")
        scope = self._scope_stack.pop() if self._scope_stack else {}
        # Manual 3 §3.3: iteración lexicográfica sobre claves de diccionarios
        for var_name in reversed(sorted(scope.keys())):
            # Move semantics: skip vars already explicitly consumed/destroyed
            if var_name in self._consumed_vars:
                self._consumed_vars.discard(var_name)
                continue
            dtor = self._destructor_map.get(scope[var_name])
            if dtor:
                self.write_line(f"{dtor}({var_name});")

    def enable_safe_mode(self):
        """M22.1: Activa modo --safe, que emite /* BORROW_CHECK */ en &T y *ptr."""
        self._safe_mode = True

    def emit_all_destructors(self, exclude_var: str = ''):
        for scope in reversed(self._scope_stack):
            # Manual 3 §3.3: iteración lexicográfica sobre claves de diccionarios
            for var_name in reversed(sorted(scope.keys())):
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
        # Manual 4 §4.2: &T y &mut T son punteros en C
        if tipo_synapse.startswith('&mut '):
            return self.traducir_tipo_c(tipo_synapse[5:]) + '*'
        if tipo_synapse.startswith('&'):
            return self.traducir_tipo_c(tipo_synapse[1:]) + '*'
        # F1.2d + F1.4: rc<T>/arc<T>/débil<T> (Manual 2 §4.3). ABI placeholder
        # (void*) hasta la Fase 23 (runtime real de rc/arc/débil — ROADMAP Fase
        # 23 L213-214). 'rc' se añadió en F1.4 (Manual 2 §4 L151: "rc" tipo).
        if (tipo_synapse.startswith(('rc<', 'arc<', 'débil<', 'weak<', 'faible<', 'fraco<'))
                or tipo_synapse in ('rc', 'arc', 'débil', 'weak', 'faible', 'fraco')):
            return 'void*'
        if tipo_synapse.startswith('Canal<') and tipo_synapse.endswith('>'):
            return 'CanalConcurrencia*'
        if tipo_synapse.startswith('Resultado<'):
            return 'Resultado_T'
        # M22.6: Handle pointer types (e.g. int* -> int*, not struct int*)
        if tipo_synapse.endswith('*') and not tipo_synapse.startswith('struct '):
            base = tipo_synapse[:-1].rstrip()  # Strip trailing * and whitespace
            base_c = self.traducir_tipo_c(base)
            return f"{base_c}*"
        tipo_c = MAPA_TIPOS_C.get(tipo_synapse)
        if tipo_c is not None:
            return tipo_c
        # F1.2: resolver alias de tipo declarados (`tipo X = Y`)
        if tipo_synapse in self._tipo_aliases:
            return self.traducir_tipo_c(self._tipo_aliases[tipo_synapse])
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
