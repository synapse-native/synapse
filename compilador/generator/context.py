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


def _dividir_args_tipo(resto: str) -> List[str]:
    """Divide los argumentos de una instanciación ADT respetando el anidamiento
    (D-2): `Resultado<Resultado<entero,texto>,texto>` ->
    ['Resultado<entero,texto>', 'texto']. El separador es la coma a nivel 0
    (fuera de los `<...>` internos). Paridad con el scan nativo
    (orquestador.syn _d2pend). Manual 2 §4.2 L279-280.
    """
    args: List[str] = []
    actual: List[str] = []
    prof = 0
    for ch in resto:
        if ch == '<':
            prof += 1
            actual.append(ch)
        elif ch == '>':
            prof -= 1
            actual.append(ch)
        elif ch == ',' and prof == 0:
            args.append(''.join(actual).strip())
            actual = []
        else:
            actual.append(ch)
    if actual:
        args.append(''.join(actual).strip())
    return args


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
            'cerrar_archivo': 'void', 'suma': 'tensor', 'producto': 'tensor',
            'relu': 'tensor', 'tokenizar': 'int',
            'parsear': 'struct Programa', 'generar': 'int',
            'concat': 'texto', '_argc': 'int',
            '_argv': 'texto', 'salir': 'void',
            'canal_crear': 'CanalConcurrencia*', 'canal_enviar': 'void',
            'canal_recibir': 'puntero', 'cerrar': 'void',
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
            'cluster_generar_nonce': 'texto', 'cluster_enviar_hello_firmado': 'int',
            'cluster_canal_remoto_enviar': 'int', 'cluster_recibir_paquete': 'texto',
            'cluster_establecer_clave_sesion': 'nulo', 'cluster_limpiar_clave_sesion': 'nulo',
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
        # H-R90-15: dividir builtin del std.err (std/err.syn §3).
        # Manual 3 §7.1: Resultado<decimal, texto>. Resuelta como return type
        # (no en _RUNTIME_BUILTINS: provee stub inline en el generator).
        'dividir': 'Resultado<decimal, texto>',
        }
        # F1.2d/F1.4 (Manual 4 §3.2-3.3, §4.2, §4.3): rc/arc/débil constructores
        # `rc(T)` → rc<T>, `débil(T)` → débil<T> / `débil(nulo)` → nil WeakRef
        self._BUILTINS['rc'] = 'rc'
        self._BUILTINS['arc'] = 'arc'
        self._BUILTINS['débil'] = 'débil'
        self._BUILTINS['weak'] = 'débil'
        self._BUILTINS['faible'] = 'débil'
        self._BUILTINS['fraco'] = 'débil'

        self._RUNTIME_BUILTINS: frozenset = frozenset({
            'escribir', 'escribir_linea', 'leer_linea', 'str_eq', 'abrir', 'leer', 'cerrar_archivo',
            'math_crear_tensor', 'math_suma_tensor', 'math_producto_punto', 'math_relu',
            'mem_reserva', 'mem_libera', 'math_suma', 'math_producto',
            'crear_tensor', 'suma_tensor', 'producto_punto', 'relu',
            'reserva', 'libera', 'suma', 'producto',
            'texto_a_entero', 'texto_a_decimal', 'decimal_a_texto',
            'salir', 'canal_crear', 'canal_enviar', 'canal_recibir', 'cerrar',
            'debug_registrar_evento', 'debug_trace', 'debug_iniciar_sesion', 'debug_finalizar_sesion',
            'tr_inicializar_recording', 'tr_grabar_bifurcacion',
            'tr_grabar_snapshot', 'tr_grabar_llamada', 'tr_grabar_retorno',
            'tr_grabar_error', 'tr_buscar_evento', 'tr_obtener_evento',
            'tr_reproducir_hasta', 'tr_indice_ultimo_error', 'tr_total_eventos',
            'cluster_generar_par_claves', 'cluster_firmar_mensaje', 'cluster_verificar_firma',
            'cluster_iniciar_nodo', 'cluster_detener_nodo', 'cluster_enviar_hello',
            'cluster_canal_remoto_enviar', 'cluster_recibir_paquete',
            'cluster_establecer_clave_sesion', 'cluster_limpiar_clave_sesion',
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
        self._funciones_usuario: Dict[str, 'DefinicionFuncion'] = {}  # nombre -> DefinicionFuncion (H-R90-13: params con defaults)
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
        # D-6: constructores ADT (ok/err/algun/ninguno) -> (ADT, tag, tipo_campo)
        self._constructores_adt: Dict[str, tuple] = {}
        # D-2: instanciaciones de ADT genéricos (monomorfización, Opción A).
        # Clave: (base, tuple(args)) -> {'nombre_c': str, 'campos': [(ctor, tipo_syn), ...]}
        # p.ej. ('Resultado', ('entero','texto')) -> 'Resultado_entero_texto' con
        # campos [('ok','entero'), ('err','texto')] — tipos SUSTITUIDOS (Manual 2 §4.2).
        self._instancias_adt: Dict[tuple, dict] = {}
        # D-2: parámetros de tipo declarados por ADT (base -> [T, E]) y sus
        # constructores originales (base -> [(ctor, tipo_syn), ...]).
        self._adt_parametros: Dict[str, list] = {}
        self._adt_constructores: Dict[str, list] = {}
        # R24 (hallazgo R22): los ADT genéricos BUILTIN Resultado<T,E>/Opcion<T>
        # se usan en firmas SIN declaración (`funcion f(r: Resultado<entero,
        # texto>)`) — el checker ya los conoce (semantic_scope.py L101-102,
        # paridad de aridad/exhaustividad), así que el generador debe conocerlos
        # también para materializar la instancia monomorfizada
        # (Resultado_entero_texto) en vez del placeholder Resultado_T (C inválido:
        # 'Resultado_T' has no member named 'tag'). Una DeclaracionTipo del
        # usuario sobreescribe estos valores (declaración gana).
        # NOTA (code-reviewer R24): fuente hermana duplicada con semantic_scope.py
        # L101-102 — si se añade un tercer ADT builtin, actualizar AMBOS lados.
        self._adt_parametros['Resultado'] = ['T', 'E']
        self._adt_parametros['Opcion'] = ['T']
        self._adt_constructores['Resultado'] = [('ok', 'T'), ('err', 'E')]
        self._modo: str = 'completo'  # H-R90-8b: track header/body/completo
        self._usa_dividir: bool = False  # H-R90-15: flag para stub dividir
        self._adt_constructores['Opcion'] = [('algun', 'T'), ('ninguno', 'entero')]
        self._consumed_vars: set = set()  # vars already explicitly destroyed (move semantics)
        self._scope_stack: List[Dict[str, str]] = []
        self._strings_heap: set = set()
        self._contador_thread = 0
        self._contador_listener = 0

        # Struct + function tracking
        self._estructuras: Dict[str, dict] = {}

        self._metodos_self: set = set()  # funciones metodo con self ptr (F4: Manual 3 §6.1)
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
        # H-R90-13: valores por defecto para params de builtins omitidos (Manual 3 §3)
        # abrir(ruta, modo="r") — cuando se llama con 1 arg, añade "r"
        self._builtin_defaults: Dict[str, List[str]] = {
            'abrir': ['(CadenaSegura){ .longitud = (int)strlen("r"), .datos = "r" }'],
        }
        # H-R90-15: métodos builtin para tipos Lista y otros (Manual 3 §5.4)
        # obj.metodo() → funcion_builtin(obj)
        self._builtin_metodos: Dict[str, Dict[str, str]] = {
            'Canal': {'leer': 'leer'},
            'entero': {'texto': 'entero_a_texto'},
            'decimal': {'texto': 'decimal_a_texto'},
            'Lista': {'len': 'len'},
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
            dtor, arg, guard = self._destructor_para_tipo(scope[var_name], var_name)
            if dtor:
                if guard:
                    self.write_line(f"if ({guard}) {dtor}({arg});")
                else:
                    self.write_line(f"{dtor}({arg});")

    def enable_safe_mode(self):
        """M22.1: Activa modo --safe, que emite /* BORROW_CHECK */ en &T y *ptr."""
        self._safe_mode = True

    def emit_all_destructors(self, exclude_var: str = ''):
        for scope in reversed(self._scope_stack):
            for var_name in reversed(sorted(scope.keys())):
                if var_name == exclude_var:
                    continue
                if var_name in self._consumed_vars:
                    self._consumed_vars.discard(var_name)
                    continue
                dtor, arg, guard = self._destructor_para_tipo(scope[var_name], var_name)
                if dtor:
                    if guard:
                        self.write_line(f"if ({guard}) {dtor}({arg});")
                    else:
                        self.write_line(f"{dtor}({arg});")
        for scope in self._scope_stack:
            scope.clear()

    def _es_tipo_rc(self, tipo_synapse: str) -> bool:
        """True si tipo_synapse es rc<T> o `rc T` (Manual 4 §3.2, Manual 3 §3)."""
        return tipo_synapse == 'rc' or (
            tipo_synapse.startswith('rc<') and tipo_synapse.endswith('>')
            or tipo_synapse.startswith('rc ')
        )

    def _es_tipo_arc(self, tipo_synapse: str) -> bool:
        """True si tipo_synapse es arc<T> o `arc T` (Manual 4 §3.3)."""
        return tipo_synapse == 'arc' or (
            tipo_synapse.startswith('arc<') and tipo_synapse.endswith('>')
            or tipo_synapse.startswith('arc ')
        )

    def _es_tipo_debil(self, tipo_synapse: str) -> bool:
        """True si tipo_synapse es débil<T>/débil<T>/weak<T>/weak (Manual 4 §4.2)."""
        debil_prefixes = ('débil<', 'weak<', 'faible<', 'fraco<')
        debil_exact = ('débil', 'weak', 'faible', 'fraco')
        return (tipo_synapse.startswith(debil_prefixes)
                or tipo_synapse in debil_exact
                or any(tipo_synapse.startswith(p + ' ') for p in debil_exact))

    def _tipo_tiene_destructor(self, tipo_synapse: str) -> bool:
        """True si el tipo requiere cleanup en scope exit (Manual 4 §5.2)."""
        return (self._destructor_map.get(tipo_synapse) is not None
                or self._es_tipo_rc(tipo_synapse)
                or self._es_tipo_arc(tipo_synapse)
                or self._es_tipo_debil(tipo_synapse))

    def _destructor_para_tipo(self, tipo_synapse: str,
                               var_name: str = '') -> tuple:
        """Devuelve (fn, arg_expr, guard) para el destructor de un tipo,
        o ('', '', ''). Manual 4 §3.2 (rc), §3.3 (arc), §4.2 (débiles),
        §5.2 (cleanup). El 3er elemento es la condición C que guarda against
        nil (Manual 4 §4.1: nulo valor valido; rc_flag bitmask §5.4)."""
        dtor = self._destructor_map.get(tipo_synapse)
        if dtor:
            return (dtor, var_name, '')
        if self._es_tipo_rc(tipo_synapse):
            return ('rc_decrementar', var_name, f'{var_name}')
        if self._es_tipo_arc(tipo_synapse):
            return ('arc_decrementar', var_name, f'{var_name}')
        if self._es_tipo_debil(tipo_synapse):
            # WeakRef: rc_weak_release checks !w->header internally (§4.2)
            return ('rc_weak_release', f'&{var_name}', '')
        return ('', '', '')

    def register_var(self, nombre: str, tipo: str, desde_llamada: bool):
        if self._scope_stack and desde_llamada and self._tipo_tiene_destructor(tipo):
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
            inner = tipo_synapse[5:].lstrip()
            # FFI: &texto/&cadena -> char* (Manual 3 §9.3 zero-copy .datos)
            if inner in ('texto', 'cadena', 'CadenaSegura', 'Texto'):
                return 'char*'
            return self.traducir_tipo_c(inner) + '*'
        if tipo_synapse.startswith('&'):
            inner = tipo_synapse[1:].lstrip()
            # FFI: &texto/&cadena -> char* (Manual 3 §9.3 zero-copy .datos)
            if inner in ('texto', 'cadena', 'CadenaSegura', 'Texto'):
                return 'char*'
            return self.traducir_tipo_c(inner) + '*'
        # F1.2d/F1.4: rc/arc/débil/arena (Manual 4 §3.2-3.3, §4.2-4.4).
        # Sintaxis SyQuex: `rc entero` (espacio, Manual 3 §3 L155-169) — pero
        # también soporta `rc<entero>` (ángulos). ABI: void* en C.
        if self._es_tipo_rc(tipo_synapse) or self._es_tipo_arc(tipo_synapse):
            return 'void*'
        if self._es_tipo_debil(tipo_synapse):
            return 'WeakRef'
        if tipo_synapse.startswith('Canal<') and tipo_synapse.endswith('>'):
            return 'CanalConcurrencia*'
        # D-2: instanciación de ADT genérico registrada (monomorfización).
        # `Resultado<entero,texto>` -> struct especializado `Resultado_entero_texto`
        # (Manual 2 §4.2 L279-280; Manual 3 §5.4). Solo si el pre-pass la registró;
        # si no (ADT sin instanciar), cae al fallback histórico (Resultado_T / void*).
        if '<' in tipo_synapse and tipo_synapse.endswith('>'):
            base, _, resto = tipo_synapse.partition('<')
            args = tuple(_dividir_args_tipo(resto[:-1]))
            if (base, args) in self._instancias_adt:
                return self._instancias_adt[(base, args)]['nombre_c']
            # H-R90-15: Lista<T>/Mapa<K,V> son opaque types (void* en C, Manual 3 §5.2)
            if base in ('Lista', 'Mapa'):
                return 'void*'
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
