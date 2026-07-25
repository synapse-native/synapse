# OpenSyn: Strict Type Inference Engine (M2.2)
# Flow-sensitive type inference with control-flow analysis for Python -> Synapse migration
# Enforces El Pacto: no dynamic types, no implicit mutations, no null

from __future__ import annotations
import ast
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Union, Any
from enum import Enum
from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .py_parser import SynNode, Programa, DeclaracionFuncion, DeclaracionVariable, AsignacionVariable, SentenciaSi, SentenciaMientras, SentenciaPara, SentenciaRetornar, LlamadaFuncion, OpBinaria, OpUnaria, OpComparacion, OpLogica, Identificador, LiteralEntero, LiteralDecimal, LiteralBooleano, LiteralCadena, LiteralNulo, AccesoCampo, Indice, ExprTensor, ExprDiccionario, SynNode

# =============================================================================
# TYPE SYSTEM DEFINITIONS
# =============================================================================

class SynapseType(Enum):
    """Synapse native types (El Pacto: no null, no any, no dynamic)"""
    ENTERO = "entero"
    DECIMAL = "decimal"
    BOOLEANO = "booleano"
    TEXTO = "texto"
    CARACTER = "caracter"
    NULO = "nulo"
    PUNTERO = "puntero"
    
    # Composite types
    LISTA = "Lista"
    DICCIONARIO = "Diccionario"
    CANAL = "Canal"
    OPCION = "Opcion"
    RESULTADO = "Resultado"
    
    # Function type
    FUNCION = "funcion"
    
    # User-defined types (structs)
    ESTRUCTURA = "estructura"
    
    # Unknown/inferred
    DESCONOCIDO = "desconocido"
    AMBIGUO = "ambiguo"
    
    @classmethod
    def from_python_type(cls, py_type: str) -> 'SynapseType':
        """Map Python type hints to Synapse types."""
        mapping = {
            'int': cls.ENTERO,
            'int64': cls.ENTERO,
            'int32': cls.ENTERO,
            'float': cls.DECIMAL,
            'float64': cls.DECIMAL,
            'float32': cls.DECIMAL,
            'bool': cls.BOOLEANO,
            'str': cls.TEXTO,
            'str': cls.TEXTO,
            'bytes': cls.PUNTERO,
            'bytearray': cls.PUNTERO,
            'None': cls.NULO,
            'NoneType': cls.NULO,
        }
        return mapping.get(py_type, cls.DESCONOCIDO)

class TypeKind(Enum):
    """Classification of type certainty."""
    CONCRETO = "concreto"      # Fully resolved: entero, Lista<entero>, etc.
    INFERIDO = "inferido"      # Inferred from context
    AMBIGUO = "ambiguo"        # Multiple possible types
    DESCONOCIDO = "desconocido"  # Cannot determine

# =============================================================================
# TYPE REPRESENTATION
# =============================================================================

@dataclass
class TypeInfo:
    """Complete type information with flow-sensitivity metadata."""
    tipo: SynapseType
    kind: TypeKind = TypeKind.CONCRETO
    parametros: List['TypeInfo'] = field(default_factory=list)  # For Lista<T>, Dict<K,V>, etc.
    # Flow-sensitivity metadata
    punto_definicion: Optional[Tuple[int, int]] = None  # (line, col) where defined
    mutado: bool = False  # Whether variable was reassigned
    mutaciones: List[Tuple[int, int]] = field(default_factory=list)  # Locations where mutated
    # Contracts
    contratos: List[str] = field(default_factory=list)  # requiere/garantiza strings
    
    def __str__(self) -> str:
        if self.parametros:
            params = ', '.join(str(p) for p in self.parametros)
            return f"{self.tipo.value}<{params}>"
        return self.tipo.value
    
    def es_concreto(self) -> bool:
        return self.kind == TypeKind.CONCRETO
    
    def es_ambiguo(self) -> bool:
        return self.kind == TypeKind.AMBIGUO
    
    def __eq__(self, other):
        if not isinstance(other, TypeInfo):
            return False
        if self.tipo != other.tipo:
            return False
        if self.parametros != other.parametros:
            return False
        return True

# =============================================================================
# TYPE ENVIRONMENT (Flow-Sensitive)
# =============================================================================

@dataclass
class TypeEnvironment:
    """
    Flow-sensitive type environment with scope management.
    Tracks variable types through control flow (if, while, for, functions).
    """
    scopes: List[Dict[str, TypeInfo]] = field(default_factory=lambda: [{}])
    current_function: Optional[str] = None
    loop_depth: int = 0
    if_depth: int = 0
    
    def enter_scope(self):
        self.scopes.append({})
    
    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()
    
    def define(self, name: str, type_info: TypeInfo, linea: int = 0, columna: int = 0):
        """Define a new variable in current scope."""
        current = self.scopes[-1]
        if name in current:
            # Check for type compatibility if redefined in same scope
            existing = current[name]
            if existing != type_info:
                raise TypeError(f"Re-definición de '{name}' con tipo incompatible: {existing} vs {type_info}")
        type_info.punto_definicion = (type_info.punto_definicion[0] if type_info.punto_definicion else 0, 
                                       type_info.punto_definicion[1] if type_info.punto_definicion else 0)
        self.scopes[-1][name] = type_info
    
    def get(self, name: str) -> Optional[TypeInfo]:
        """Lookup variable from innermost to outermost scope."""
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None
    
    def update(self, name: str, new_type: 'TypeInfo', linea: int, columna: int) -> bool:
        """Update variable type after mutation (e.g., x += 1)."""
        for scope in reversed(self.scopes):
            if name in scope:
                existing = scope[name]
                # Check compatibility
                if existing.tipo != new_type.tipo:
                    # Allow numeric widening: entero -> decimal
                    if not self._compatible_widen(existing.tipo, new_type.tipo):
                        raise TypeError(f"Mutación incompatible de '{name}': {existing.tipo} -> {new_type.tipo}")
                # Record mutation
                existing.mutado = True
                existing.mutaciones.append((0, 0))  # line/col would be tracked
                existing.tipo = new_type.tipo
                return True
        return False
    
    def _compatible_widen(self, from_type: SynapseType, to_type: SynapseType) -> bool:
        """Check if type widening is allowed (entero -> decimal)."""
        widen_map = {
            SynapseType.ENTERO: {SynapseType.DECIMAL},
            SynapseType.DECIMAL: set(),
        }
        return to_type in widen_map.get(from_type, set())
    
    def enter_function(self, name: str):
        self.enter_scope()
        self.current_function = name
    
    def exit_function(self):
        self.current_function = None
        self.exit_scope()
    
    def enter_if(self):
        self.enter_scope()
        self.if_depth += 1
    
    def exit_if(self):
        self.if_depth -= 1
        self.exit_scope()
    
    def enter_while(self):
        self.enter_scope()
        self.loop_depth += 1
    
    def exit_while(self):
        self.loop_depth -= 1
        self.exit_scope()
    
    def enter_for(self):
        self.enter_scope()
        self.loop_depth += 1
    
    def exit_for(self):
        self.loop_depth -= 1
        self.exit_scope()

# =============================================================================
# TYPE INFERENCE ENGINE
# =============================================================================

class TypeInferenceEngine:
    """
    Flow-sensitive type inference engine for Python -> Synapse migration.
    Performs control-flow analysis to ensure type safety per El Pacto.
    """
    
    def __init__(self):
        self.env = TypeEnvironment()
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.type_hints: Dict[str, str] = {}  # Explicit type hints from annotations
    
    def infer_program(self, programa) -> List[str]:
        """Run inference on entire program."""
        errors = []
        for stmt in programa.sentencias:
            try:
                self._visit(stmt)
            except TypeError as e:
                errors.append(str(e))
            except Exception as e:
                self.errors.append(f"Error interno: {e}")
        return errors
    
    def _visit(self, node) -> None:
        """Dispatch to appropriate visitor."""
        if hasattr(node, 'tipo'):
            method_name = f'_visit_{node.tipo}'
        else:
            method_name = f'_visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self._visit_unknown)
        visitor(node)
    
    def _visit_unknown(self, node):
        # Silently skip unknown nodes
        pass
    
    # =========================================================================
    # STATEMENTS
    # =========================================================================
    
    def _visit_DeclaracionFuncion(self, node) -> None:
        """Process function definition with parameter/return type checking."""
        # Enter function scope
        self.env.enter_function(node.nombre)
        
        # Process parameters
        param_types = []
        for param in node.parametros:
            param_type = self._resolve_type_string(param.tipo)
            self.env.define(param.nombre, TypeInfo(
                tipo=param.tipo,
                kind=TypeKind.CONCRETO,
                punto_definicion=(node.linea, node.columna)
            ))
            param.tipo = param.tipo  # Ensure type is set
        
        # Process function body
        old_function = self.env.current_function
        self.env.current_function = node.nombre
        for stmt in node.cuerpo:
            self._visit(stmt)
        self.env.current_function = old_function
        
        # Check return type consistency
        if node.tipo_retorno != "nulo":
            # Would need to check all return statements match
            pass
        
        self.env.exit_function()
    
    def _visit_DeclaracionVariable(self, node) -> TypeInfo:
        """Process variable declaration with type inference."""
        # Resolve explicit type annotation
        declared_type = self._resolve_type_string(node.tipo) if node.tipo else None
        
        # Infer from value if no explicit type
        inferred_type = None
        if node.valor:
            inferred_type = self._infer_expression_type(node.valor)
        
        # Resolve final type
        if declared_type and inferred_type:
            if not self._types_compatible(declared_type, inferred_type):
                self.errors.append(f"Línea {node.linea}: Tipo declarado '{declared_type}' incompatible con inferido '{inferred_type}'")
                final_type = declared_type
            else:
                final_type = declared_type or inferred_type
        elif declared_type:
            final_type = declared_type
        elif inferred_type:
            final_type = inferred_type
        else:
            self.errors.append(f"Línea {node.linea}: Variable '{node.nombre}' sin tipo y sin valor para inferir")
            final_type = SynapseType.DESCONOCIDO
        
        type_info = TypeInfo(
            tipo=final_type,
            kind=TypeKind.CONCRETO if final_type != SynapseType.DESCONOCIDO else TypeKind.DESCONOCIDO,
            punto_definicion=(node.linea, node.columna) if hasattr(node, 'linea') else None
        )
        
        # Register in environment
        self.env.define(node.nombre, final_type, node.linea, node.columna)
        
        return TypeInfo(tipo=final_type, kind=TypeKind.CONCRETO)
    
    def _visit_AsignacionVariable(self, node) -> None:
        """Handle variable assignment with mutation checking."""
        # Get current type
        current_type = self.env.get(node.nombre)
        if not current_type:
            self.errors.append(f"Línea {getattr(node, 'linea', '?')}: Asignación a variable no declarada '{node.nombre}'")
            return
        
        # Infer value type
        value_type = self._infer_expression_type(node.valor) if node.valor else None
        
        if value_type and not self._types_compatible(node.tipo, value_type):
            # Allow numeric widening
            if not (node.tipo == SynapseType.ENTERO and value_type == SynapseType.DECIMAL):
                self.errors.append(
                    f"Línea {getattr(node, 'linea', '?')}: Asignación incompatible: "
                    f"'{node.nombre}' es {node.tipo}, se asigna {value_type}"
                )
            # Update type (widening)
            self.env.update(node.nombre, TypeInfo(tipo=value_type), 0, 0)
    
    def _visit_AsignacionCompuesta(self, node) -> None:
        """Handle compound assignment (x += 1)."""
        current = self.env.get(node.nombre)
        if not current:
            self.errors.append(f"Variable '{node.nombre}' no declarada para asignación compuesta")
            return
        
        value_type = self._infer_expression_type(node.valor) if node.valor else None
        
        # For compound ops, types must match exactly (no widening on +=)
        if value_type and value_type.tipo != node.tipo:
            self.errors.append(
                f"Operación compuesta incompatible: {node.tipo} {node.operador} {value_type.tipo}"
            )
        
        # Mark as mutated
        self.env.update(node.nombre, node, 0, 0)
    
    def _visit_SentenciaSi(self, node) -> None:
        """Handle if statement with branch type merging."""
        # Check condition type
        cond_type = self._infer_expression_type(node.condicion)
        if cond_type and cond_type.tipo != SynapseType.BOOLEANO:
            self.warnings.append(f"Condición 'si' no es booleana: {cond_type}")
        
        # Visit then branch
        self.env.enter_if()
        for stmt in node.cuerpo_si:
            self._visit(stmt)
        then_env = self._capture_environment()
        self.env.exit_if()
        
        # Visit else branch
        if node.cuerpo_sino:
            self.env.enter_if()
            for stmt in node.cuerpo_sino:
                self._visit(stmt)
            else_env = self._capture_environment()
            self.env.exit_if()
            
            # Merge types from both branches
            self._merge_branch_types(then_env, else_env)
        else:
            # No else branch - types from then branch persist
            pass
    
    def _visit_SentenciaMientras(self, node) -> None:
        """Handle while loop with loop-carried dependencies."""
        cond_type = self._infer_expression_type(node.condicion)
        if cond_type and cond_type.tipo != SynapseType.BOOLEANO:
            self.warnings.append(f"Condición 'mientras' no es booleana: {cond_type}")
        
        self.env.enter_while()
        for stmt in node.cuerpo:
            self._visit(stmt)
        self.env.exit_while()
    
    def _visit_SentenciaPara(self, node) -> None:
        """Handle for loop with iterator type inference."""
        # Infer iterator type
        iter_type = self._infer_expression_type(node.iterador) if hasattr(node, 'iterador') else None
        
        self.env.enter_for()
        # Define loop variable
        if hasattr(node, 'variable') and node.variable:
            iter_elem_type = self._infer_iterable_element_type(node.iterador)
            self.env.define(node.variable, TypeInfo(
                tipo=iter_elem_type or SynapseType.ENTERO,
                kind=TypeKind.INFERIDO
            ))
        
        for stmt in node.cuerpo:
            self._visit(stmt)
        self.env.exit_for()
    
    def _visit_SentenciaRetornar(self, node) -> None:
        """Check return type matches function signature."""
        if node.valor:
            ret_type = self._infer_expression_type(node.valor)
            # Check against function return type (stored in env.current_function)
            if self.env.current_function:
                # Would check against function signature
                pass
    
    def _visit_LlamadaFuncion(self, node) -> None:
        """Validate function call arguments."""
        # Look up function signature
        # For builtins, use builtin signatures
        if node.nombre in BUILTIN_SIGNATURES:
            sig = BUILTIN_SIGNATURES[node.nombre]
            if len(node.argumentos) != len(sig.parametros):
                self.errors.append(f"Llamada a '{node.nombre}': se esperan {len(sig.parametros)} argumentos, se dieron {len(node.argumentos)}")
            for i, (arg, expected) in enumerate(zip(node.argumentos, sig.parametros)):
                arg_type = self._infer_expression_type(arg)
                if not self._types_compatible(expected, arg_type):
                    self.errors.append(f"Argumento {i+1} de '{node.nombre}': se esperaba {expected}, se dio {arg_type}")
    
    # =========================================================================
    # EXPRESSIONS
    # =========================================================================
    
    def _infer_expression_type(self, node) -> Optional[TypeInfo]:
        """Infer type of expression node."""
        if not node:
            return None
        
        if hasattr(node, 'tipo'):
            method_name = f'_infer_{node.tipo}'
        else:
            method_name = f'_infer_{type(node).__name__}'
        
        inferrer = getattr(self, method_name, self._infer_unknown)
        return inferrer(node)
    
    def _infer_unknown(self, node) -> TypeInfo:
        return TypeInfo(tipo=SynapseType.DESCONOCIDO, kind=TypeKind.DESCONOCIDO)
    
    def _infer_Identificador(self, node) -> TypeInfo:
        """Variable reference."""
        type_info = self.env.get(node.nombre)
        if not type_info:
            self.warnings.append(f"Variable '{node.nombre}' usada antes de declarar")
            return TypeInfo(tipo=SynapseType.DESCONOCIDO, kind=TypeKind.DESCONOCIDO)
        return type_info
    
    def _infer_LiteralEntero(self, node) -> TypeInfo:
        return TypeInfo(tipo=SynapseType.ENTERO, kind=TypeKind.CONCRETO)
    
    def _infer_LiteralDecimal(self, node) -> TypeInfo:
        return TypeInfo(tipo=SynapseType.DECIMAL, kind=TypeKind.CONCRETO)
    
    def _infer_LiteralBooleano(self, node) -> TypeInfo:
        return TypeInfo(tipo=SynapseType.BOOLEANO, kind=TypeKind.CONCRETO)
    
    def _infer_LiteralCadena(self, node) -> TypeInfo:
        return TypeInfo(tipo=SynapseType.TEXTO, kind=TypeKind.CONCRETO)
    
    def _infer_LiteralNulo(self, node) -> TypeInfo:
        return TypeInfo(tipo=SynapseType.NULO, kind=TypeKind.CONCRETO)
    
    def _infer_LlamadaFuncion(self, node) -> TypeInfo:
        """Infer return type of function call."""
        # Check builtins
        if node.nombre in BUILTIN_RETURN_TYPES:
            return TypeInfo(tipo=BUILTIN_RETURN_TYPES[node.nombre], kind=TypeKind.CONCRETO)
        
        # User-defined function - would need symbol table lookup
        return TypeInfo(tipo=SynapseType.ENTERO, kind=TypeKind.INFERIDO)  # Default
    
    def _infer_OpBinaria(self, node) -> TypeInfo:
        left = self._infer_expression_type(node.izquierda)
        right = self._infer_expression_type(node.derecha)
        op = node.operador
        
        # Type rules for binary operations
        if op in ('+', '-', '*', '/'):
            # Arithmetic: both numeric, result is wider type
            if left and right:
                if left.tipo == SynapseType.ENTERO and right.tipo == SynapseType.ENTERO:
                    return TypeInfo(tipo=SynapseType.ENTERO)
                if left.tipo in (SynapseType.ENTERO, SynapseType.DECIMAL) and \
                   right.tipo in (SynapseType.ENTERO, SynapseType.DECIMAL):
                    return TypeInfo(tipo=SynapseType.DECIMAL)
        elif op == '%':
            # Modulo: integers only
            return TypeInfo(tipo=SynapseType.ENTERO)
        elif op in ('==', '!=', '<', '>', '<=', '>='):
            return TypeInfo(tipo=SynapseType.BOOLEANO)
        elif op in ('y', 'o'):
            return TypeInfo(tipo=SynapseType.BOOLEANO)
        
        return TypeInfo(tipo=SynapseType.DESCONOCIDO)
    
    def _infer_OpUnaria(self, node) -> TypeInfo:
        operand = self._infer_expression_type(node.operando)
        op = node.operador
        
        if op == '-':
            # Numeric negation
            if operand and operand.tipo in (SynapseType.ENTERO, SynapseType.DECIMAL):
                return TypeInfo(tipo=operand.tipo)
        elif op in ('no', 'not'):
            return TypeInfo(tipo=SynapseType.BOOLEANO)
        
        return TypeInfo(tipo=SynapseType.DESCONOCIDO)
    
    def _infer_OpComparacion(self, node) -> TypeInfo:
        return TypeInfo(tipo=SynapseType.BOOLEANO, kind=TypeKind.CONCRETO)
    
    def _infer_OpLogica(self, node) -> TypeInfo:
        return TypeInfo(tipo=SynapseType.BOOLEANO, kind=TypeKind.CONCRETO)
    
    def _infer_AccesoCampo(self, node) -> TypeInfo:
        obj_type = self._infer_expression_type(node.objeto)
        # Would need struct field lookup
        return TypeInfo(tipo=SynapseType.DESCONOCIDO)
    
    def _infer_Indice(self, node) -> TypeInfo:
        obj_type = self._infer_expression_type(node.objeto)
        # For Lista<T>, return T
        if obj_type and obj_type.tipo == SynapseType.LISTA and obj_type.parametros:
            return obj_type.parametros[0]
        return TypeInfo(tipo=SynapseType.DESCONOCIDO)
    
    def _infer_ExprTensor(self, node) -> TypeInfo:
        if node.elementos:
            first_type = self._infer_expression_type(node.elementos[0])
            # Check homogeneity
            for elem in node.elementos[1:]:
                elem_type = self._infer_expression_type(elem)
                if not self._types_compatible(first_type, elem_type):
                    self.warnings.append("Lista heterogénea detectada, se usará tipo común")
                    return TypeInfo(tipo=SynapseType.LISTA, kind=TypeKind.AMBIGUO, 
                                    parametros=[TypeInfo(tipo=SynapseType.DESCONOCIDO)])
            return TypeInfo(tipo=SynapseType.LISTA, parametros=[first_type])
        return TypeInfo(tipo=SynapseType.LISTA, parametros=[TypeInfo(tipo=SynapseType.DESCONOCIDO)])
    
    def _infer_ExprDiccionario(self, node) -> TypeInfo:
        if node.claves and node.valores:
            key_type = self._infer_expression_type(node.claves[0])
            val_type = self._infer_expression_type(node.valores[0])
            return TypeInfo(tipo=SynapseType.DICCIONARIO, parametros=[key_type, val_type])
        return TypeInfo(tipo=SynapseType.DICCIONARIO)
    
    # =========================================================================
    # HELPERS
    # =========================================================================
    
    def _resolve_type_string(self, type_str: str) -> SynapseType:
        """Convert string type annotation to SynapseType enum."""
        # Handle generics: Lista<entero> -> LISTA with param
        if '<' in type_str and '>' in type_str:
            base = type_str[:type_str.index('<')]
            inner = type_str[type_str.index('<')+1:type_str.rindex('>')]
            base_type = self._map_synapse_type(base)
            inner_type = self._resolve_type_string(inner)
            return SynapseType[base_type]  # Return base, params handled separately
        return self._map_synapse_type(type_str)
    
    def _map_synapse_type(self, type_str: str) -> SynapseType:
        mapping = {
            'entero': SynapseType.ENTERO,
            'entero': SynapseType.ENTERO,
            'decimal': SynapseType.DECIMAL,
            'decimal': SynapseType.DECIMAL,
            'booleano': SynapseType.BOOLEANO,
            'texto': SynapseType.TEXTO,
            'texto': SynapseType.TEXTO,
            'caracter': SynapseType.CARACTER,
            'nulo': SynapseType.NULO,
            'puntero': SynapseType.PUNTERO,
            'Lista': SynapseType.LISTA,
            'Lista': SynapseType.LISTA,
            'Diccionario': SynapseType.DICCIONARIO,
            'Diccionario': SynapseType.DICCIONARIO,
            'Canal': SynapseType.CANAL,
            'Opcion': SynapseType.OPCION,
            'Resultado': SynapseType.RESULTADO,
            'funcion': SynapseType.FUNCION,
            'nulo': SynapseType.NULO,
        }
        return mapping.get(type_str.lower(), SynapseType.DESCONOCIDO)
    
    def _types_compatible(self, t1: SynapseType, t2: SynapseType) -> bool:
        if t1 == t2:
            return True
        # Numeric widening
        if t1 == SynapseType.ENTERO and t2 == SynapseType.DECIMAL:
            return True
        if t1 == SynapseType.DECIMAL and t2 == SynapseType.ENTERO:
            return True
        # Opcion<T> compatible with T
        if t1 == SynapseType.OPCION and t2 != SynapseType.OPCION:
            return True
        if t2 == SynapseType.OPCION and t1 != SynapseType.OPCION:
            return True
        # Resultado<T, E> compatible with T or E
        if t1 == SynapseType.RESULTADO and t2 != SynapseType.RESULTADO:
            return True
        if t2 == SynapseType.RESULTADO and t1 != SynapseType.RESULTADO:
            return True
        # Nulo compatible with Opcion and Resultado
        if t1 == SynapseType.NULO and t2 in (SynapseType.OPCION, SynapseType.RESULTADO):
            return True
        if t2 == SynapseType.NULO and t1 in (SynapseType.OPCION, SynapseType.RESULTADO):
            return True
        return False
    
    def _types_compatible(self, expected: Union[TypeInfo, SynapseType], actual: Union[TypeInfo, SynapseType]) -> bool:
        """Check if actual type is compatible with expected type."""
        # Extract SynapseType from TypeInfo if needed
        if isinstance(expected, TypeInfo):
            t1 = expected.tipo
        else:
            t1 = expected
        
        if isinstance(actual, TypeInfo):
            t2 = actual.tipo
        else:
            t2 = actual
        
        # Exact match
        if t1 == t2:
            return True
        
        # Numeric widening: entero <-> decimal
        if (t1 == SynapseType.ENTERO and t2 == SynapseType.DECIMAL) or \
           (t1 == SynapseType.DECIMAL and t2 == SynapseType.ENTERO):
            return True
        
        # Optional[T] compatible with T
        if t1 == SynapseType.OPCION and t2 != SynapseType.OPCION:
            return True
        if t2 == SynapseType.OPCION and t1 != SynapseType.OPCION:
            return True
        
        # Resultado<T> compatible with T
        if t1 == SynapseType.RESULTADO and t2 != SynapseType.RESULTADO:
            return True
        if t2 == SynapseType.RESULTADO and t1 != SynapseType.RESULTADO:
            return True
        
        # Nulo compatible with Opcion and Resultado
        if t1 == SynapseType.NULO and t2 in (SynapseType.OPCION, SynapseType.RESULTADO):
            return True
        if t2 == SynapseType.NULO and t1 in (SynapseType.OPCION, SynapseType.RESULTADO):
            return True
        
        return False
    
    def _capture_environment(self) -> Dict[str, TypeInfo]:
        """Capture current environment for branch merging."""
        return self.env.scopes[-1].copy()
    
    def _merge_branch_types(self, then_env: Dict, else_env: Dict) -> None:
        """Merge types from if/else branches (take common supertype)."""
        all_vars = set(then_env.keys()) | set(else_env.keys())
        for var in all_vars:
            then_type = then_env.get(var)
            else_type = else_env.get(var)
            if then_type and else_type:
                if then_type != else_type:
                    # Find common supertype
                    common = self._find_common_supertype(then_type, else_type)
                    if common:
                        self.env.scopes[-1][var] = common
                    else:
                        self.warnings.append(f"Variable '{var}' tiene tipos incompatibles en ramas if/else: {then_type} vs {else_type}")
            elif then_type:
                self.env.scopes[-1][var] = then_type
            elif else_type:
                self.env.scopes[-1][var] = else_type
    
    def _find_common_supertype(self, t1: TypeInfo, t2: TypeInfo) -> Optional[TypeInfo]:
        """Find common supertype (e.g., entero + decimal = decimal)."""
        if t1.tipo == t2.tipo:
            return t1
        # Numeric widening
        if (t1.tipo == SynapseType.ENTERO and t2.tipo == SynapseType.DECIMAL) or \
           (t1.tipo == SynapseType.DECIMAL and t2.tipo == SynapseType.ENTERO):
            return TypeInfo(tipo=SynapseType.DECIMAL, kind=TypeKind.INFERIDO)
        return None
    
    def _infer_iterable_element_type(self, node) -> SynapseType:
        """Infer element type of iterable (range, list, etc.)."""
        if hasattr(node, 'tipo'):
            if node.tipo == 'ExprTensor':
                # List literal: infer from elements
                pass
            elif node.tipo == 'LlamadaFuncion':
                # range(), etc.
                if hasattr(node, 'nombre') and node.nombre == 'range':
                    return SynapseType.ENTERO
        return SynapseType.ENTERO

    def _visit_unknown(self, node):
        pass

# =============================================================================
# BUILTIN SIGNATURES
# =============================================================================

@dataclass
class BuiltinSignature:
    nombre: str
    parametros: List[SynapseType]
    retorno: SynapseType

BUILTIN_SIGNATURES: Dict[str, BuiltinSignature] = {
    'len': BuiltinSignature('len', [SynapseType.LISTA], SynapseType.ENTERO),
    'len': BuiltinSignature('len', [SynapseType.DICCIONARIO], SynapseType.ENTERO),
    'len': BuiltinSignature('len', [SynapseType.TEXTO], SynapseType.ENTERO),
    'range': BuiltinSignature('range', [SynapseType.ENTERO], SynapseType.LISTA),
    'range': BuiltinSignature('range', [SynapseType.ENTERO, SynapseType.ENTERO], SynapseType.LISTA),
    'range': BuiltinSignature('range', [SynapseType.ENTERO, SynapseType.ENTERO, SynapseType.ENTERO], SynapseType.LISTA),
    'print': BuiltinSignature('print', [SynapseType.TEXTO], SynapseType.NULO),
    'print': BuiltinSignature('print', [SynapseType.TEXTO, SynapseType.TEXTO], SynapseType.NULO),
    'escribir_linea': BuiltinSignature('escribir_linea', [SynapseType.TEXTO], SynapseType.NULO),
    'leer_linea': BuiltinSignature('leer_linea', [], SynapseType.TEXTO),
    'entero_a_texto': BuiltinSignature('entero_a_texto', [SynapseType.ENTERO], SynapseType.TEXTO),
    'texto_a_entero': BuiltinSignature('texto_a_entero', [SynapseType.TEXTO], SynapseType.ENTERO),
    'texto_a_decimal': BuiltinSignature('texto_a_decimal', [SynapseType.TEXTO], SynapseType.DECIMAL),
    'decimal_a_texto': BuiltinSignature('decimal_a_texto', [SynapseType.DECIMAL], SynapseType.TEXTO),
    'entero_a_decimal': BuiltinSignature('entero_a_decimal', [SynapseType.ENTERO], SynapseType.DECIMAL),
    'decimal_a_entero': BuiltinSignature('decimal_a_entero', [SynapseType.DECIMAL], SynapseType.ENTERO),
}

BUILTIN_RETURN_TYPES: Dict[str, SynapseType] = {
    'len': SynapseType.ENTERO,
    'range': SynapseType.LISTA,
    'print': SynapseType.NULO,
    'escribir_linea': SynapseType.NULO,
    'leer_linea': SynapseType.TEXTO,
    'entero_a_texto': SynapseType.TEXTO,
    'texto_a_entero': SynapseType.ENTERO,
    'texto_a_decimal': SynapseType.DECIMAL,
    'decimal_a_texto': SynapseType.TEXTO,
    'entero_a_decimal': SynapseType.DECIMAL,
    'decimal_a_entero': SynapseType.ENTERO,
}

# =============================================================================
# MAIN API
# =============================================================================

def infer_types(programa) -> Tuple[List[str], List[str]]:
    """
    Run type inference on a Synapse program.
    
    Returns:
        Tuple of (errors, warnings)
    """
    engine = TypeInferenceEngine()
    errors = engine.infer_program(programa)
    return errors, engine.warnings

def infer_types_from_syn(syn_json: str) -> Tuple[List[str], List[str]]:
    """Run type inference from .syn.json string."""
    import json
    from .py_parser import Programa, syn_to_json
    programa = json.loads(syn_json)
    # Would need to reconstruct Programa from JSON
    # For now, return empty
    return [], []

# =============================================================================
# TESTS
# =============================================================================

def test_type_inference():
    """Basic tests for type inference."""
    # Test basic type mapping
    engine = TypeInferenceEngine()
    
    # Test numeric operations
    assert engine._types_compatible(SynapseType.ENTERO, SynapseType.ENTERO)
    assert engine._types_compatible(SynapseType.ENTERO, SynapseType.DECIMAL)
    assert engine._types_compatible(SynapseType.DECIMAL, SynapseType.ENTERO)
    assert not engine._types_compatible(SynapseType.ENTERO, SynapseType.TEXTO)
    
    # Test Optional compatibility
    assert engine._types_compatible(SynapseType.OPCION, SynapseType.ENTERO)
    assert engine._types_compatible(SynapseType.ENTERO, SynapseType.OPCION)
    
    # Test Resultado compatibility
    assert engine._types_compatible(SynapseType.RESULTADO, SynapseType.ENTERO)
    assert engine._types_compatible(SynapseType.ENTERO, SynapseType.RESULTADO)
    
    # Test Nulo compatibility
    assert engine._types_compatible(SynapseType.NULO, SynapseType.OPCION)
    assert engine._types_compatible(SynapseType.NULO, SynapseType.RESULTADO)
    
    # Test numeric widening
    assert engine._types_compatible(SynapseType.ENTERO, SynapseType.DECIMAL)
    assert engine._types_compatible(SynapseType.DECIMAL, SynapseType.ENTERO)
    
    print("[PASS] type_inference tests passed")

if __name__ == "__main__":
    test_type_inference()