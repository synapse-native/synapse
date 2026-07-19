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
    'double': 'double', 'puntero': 'void*',
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
            'reserva': 'Tensor', 'libera': 'void',
            'crear_tensor': 'Tensor', 'suma_tensor': 'Tensor',
            'producto_punto': 'Tensor', 'abrir': 'Canal',
            'leer': 'CadenaSegura', 'escribir': 'void',
            'escribir_linea': 'void', 'leer_linea': 'CadenaSegura',
            'cerrar': 'void', 'suma': 'Tensor', 'producto': 'Tensor',
            'relu': 'Tensor', 'tokenizar': 'int',
            'parsear': 'struct Programa', 'generar': 'int',
            'concat': 'CadenaSegura', '_argc': 'int',
            '_argv': 'CadenaSegura', 'salir': 'void',
            'canal_crear': 'CanalConcurrencia*', 'canal_enviar': 'void',
            'canal_recibir': 'void*', 'cerrar_canal': 'void',
            'texto_a_entero': 'int', 'texto_a_decimal': 'float',
            'decimal_a_texto': 'CadenaSegura', 'entero_a_texto': 'CadenaSegura',
        }

        self._RUNTIME_BUILTINS: frozenset = frozenset({
            'escribir', 'escribir_linea', 'leer_linea', 'abrir', 'leer', 'cerrar',
            'math_crear_tensor', 'math_suma_tensor', 'math_producto_punto', 'math_relu',
            'mem_reserva', 'mem_libera', 'math_suma', 'math_producto',
            'crear_tensor', 'suma_tensor', 'producto_punto', 'relu',
            'reserva', 'libera', 'suma', 'producto',
            'texto_a_entero', 'texto_a_decimal', 'decimal_a_texto',
            'salir', 'canal_crear', 'canal_enviar', 'canal_recibir', 'cerrar_canal',
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
        self._listener_funciones: List[str] = []
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

        # Emit flags
        self._gen_tok_emitido = False
        self._gen_parse_emitido = False
        self._gen_defs_emitido = False
        self._externas: Dict[str, List[str]] = {}
        self._linker_libs: set = set()

        # Destructor map for RAII types
        self._destructor_map: Dict[str, str] = {
            'CadenaSegura': '_syn_texto_liberar',
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
            dtor = self._destructor_map.get(scope[var_name])
            if dtor:
                self.write_line(f"{dtor}({var_name});")

    def emit_all_destructors(self, exclude_var: str = ''):
        for scope in reversed(self._scope_stack):
            for var_name in reversed(list(scope.keys())):
                if var_name == exclude_var:
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
        return f'_pool_malloc({size_expr})'

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
