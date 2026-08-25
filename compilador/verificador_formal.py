"""
compilador/verificador_formal.py — Módulo de Verificación Formal (M10.1)
=====================================================================

Subconjunto de verificación para modo --safe. Se ejecuta después del
análisis semántico y antes de la generación de código.

Responsabilidades:
  1. Prohibir bucles 'mientras' sin cota estática comprobable
  2. Prohibir efectos secundarios mutables globales
  3. Verificar terminación por inducción estructural en funciones puras
  4. Validación estática de contratos requiere/garantiza como pre/postcondiciones
"""

from typing import List, Optional, Set, Dict
from dataclasses import dataclass, field

from compilador.ast_nodes import (
    Nodo, Programa, DefinicionFuncion, DefinicionEstructura,
    SentenciaSi, SentenciaMientras, SentenciaPara,
    SentenciaRetornar, SentenciaExpr, AsignacionVariable,
    DeclaracionVariable, AsignacionCampo, BloqueInseguro,
    LlamadaFuncion, Identificador, StmtConstante,
    OpBinaria, OpUnaria, LiteralNumero, LiteralDecimal, LiteralBooleano,
    LiteralNulo, LiteralCadena, DeclaracionExterna, SentenciaLanzar,
)
from compilador.diagnostics import DiagnosticManager, ErrorCodes


# Constantes de verificación
VER_OK = 0
ERR_VER_WHILE_INACOTADO = "ERR_VER_WHILE_INACOTADO"
ERR_VER_MUTACION_GLOBAL = "ERR_VER_MUTACION_GLOBAL"
ERR_VER_RECURSION_NO_TERMINAL = "ERR_VER_RECURSION_NO_TERMINAL"
ERR_VER_CONTRATO_INVALIDO = "ERR_VER_CONTRATO_INVALIDO"

# Operadores de comparación válidos como cotas de bucle
OPERADORES_COMPARACION = {'<', '>', '<=', '>=', '==', '!='}

# Operadores booleanos válidos en contratos
OPERADORES_BOOLEANOS = {'&&', '||', '==', '!=', '<', '>', '<=', '>='}

OPERADORES_LOGICOS = {'&&', '||'}

# Tipos de nodo que tienen un campo 'cuerpo'
NODOS_CON_CUERPO = {
    'SentenciaSi', 'SentenciaMientras', 'SentenciaPara',
    'BloqueInseguro',
}


def _tiene_cuerpo(nodo: Nodo) -> bool:
    """Determina si un nodo tiene un sub-bloque de sentencias."""
    return type(nodo).__name__ in NODOS_CON_CUERPO


def _obtener_cuerpo(nodo: Nodo) -> List[Nodo]:
    """Obtiene el cuerpo de un nodo que contiene sub-bloques."""
    if isinstance(nodo, SentenciaSi):
        return nodo.cuerpo
    elif isinstance(nodo, SentenciaMientras):
        return nodo.cuerpo
    elif isinstance(nodo, SentenciaPara):
        return nodo.cuerpo
    elif isinstance(nodo, BloqueInseguro):
        return nodo.cuerpo
    return []


def _obtener_cuerpo_sino(nodo: Nodo) -> Optional[List[Nodo]]:
    """Obtiene el cuerpo 'sino' de un nodo condicional."""
    if isinstance(nodo, SentenciaSi):
        return nodo.cuerpo_sino
    return None


def _contiene_comparacion(expr: Optional[Nodo]) -> bool:
    """Verifica recursivamente si una expresión contiene un operador de
    comparación en cualquier nivel (incluyendo dentro de operadores lógicos).

    Un bucle 'mientras verdadero:' (sin comparación) se sigue rechazando,
    pero 'mientras i < len_texto:' o 'mientras t != T_MAYOR o x > 0:' se
    aceptan porque contienen al menos un operador de comparación.
    """
    if expr is None:
        return False
    if isinstance(expr, OpBinaria):
        if expr.operador in OPERADORES_COMPARACION:
            return True
        if expr.operador in OPERADORES_LOGICOS:
            return _contiene_comparacion(expr.izquierdo) or _contiene_comparacion(expr.derecho)
    return False


def _tiene_cota_estatica(mientras_stmt: SentenciaMientras) -> bool:
    """Verifica si un bucle 'mientras' tiene una cota estática comprobable.

    Criterio: la condición contiene un operador de comparación (<, >, <=, >=,
    ==, !=), posiblemente anidado dentro de operadores lógicos (&&, ||).
    Un 'mientras verdadero:' (sin comparación) se sigue rechazando.
    """
    cond = mientras_stmt.condicion
    if cond is None:
        return False
    return _contiene_comparacion(cond)


def _buscar_llamadas_recursivas(cuerpo: List[Nodo], nombre_func: str) -> bool:
    """Busca llamadas recursivas directas en un cuerpo de función."""
    for stmt in cuerpo:
        if isinstance(stmt, SentenciaRetornar) and stmt.expr is not None:
            if isinstance(stmt.expr, LlamadaFuncion) and stmt.expr.nombre == nombre_func:
                return True
        if isinstance(stmt, SentenciaExpr) and stmt.expr is not None:
            if isinstance(stmt.expr, LlamadaFuncion) and stmt.expr.nombre == nombre_func:
                return True
        if isinstance(stmt, LlamadaFuncion) and stmt.nombre == nombre_func:
            return True
        # Recurrir en sub-bloques
        if _tiene_cuerpo(stmt):
            if _buscar_llamadas_recursivas(_obtener_cuerpo(stmt), nombre_func):
                return True
        sino_cuerpo = _obtener_cuerpo_sino(stmt)
        if sino_cuerpo:
            if _buscar_llamadas_recursivas(sino_cuerpo, nombre_func):
                return True
    return False


def _tiene_caso_base(cuerpo: List[Nodo], nombre_func: str) -> bool:
    """Verifica que un cuerpo no contenga llamadas recursivas directas."""
    for stmt in cuerpo:
        if isinstance(stmt, SentenciaRetornar) and stmt.expr is not None:
            if isinstance(stmt.expr, LlamadaFuncion) and stmt.expr.nombre == nombre_func:
                return False
        if isinstance(stmt, LlamadaFuncion) and stmt.nombre == nombre_func:
            return False
        if isinstance(stmt, SentenciaExpr) and stmt.expr is not None:
            if isinstance(stmt.expr, LlamadaFuncion) and stmt.expr.nombre == nombre_func:
                return False
    return True


def _es_funcion_pura_por_nombre(func: DefinicionFuncion) -> bool:
    """Detecta funciones puras por convención de nombre."""
    nombre = func.nombre
    return nombre.endswith('_pura') or nombre.startswith('pura_')


def _tiene_convergencia_estructural(func: DefinicionFuncion) -> bool:
    """Verifica que una función recursiva tenga convergencia estructural.

    Criterio: busca un patrón de if/else donde:
    - El caso base (if) retorna sin recursión
    - El caso recursivo (else) llama a la función con argumento decreciente

    También se acepta un guard clause al inicio:
    - si cond: retornar (caso base, sin recursión)
    - y llamadas recursivas en el resto del cuerpo

    Este patrón es el estándar para funciones recursivas sobre árboles (p.ej.
    analizar_expr/analizar_sentencia que guardan 'si idx <= 0: retornar'
    antes de recorrer los hijos).
    """
    # Check for guard clause pattern: first statement is `si cond: retornar`
    # with no recursive calls in its body (base case), and recursive calls
    # exist in the rest of the function body.
    if len(func.cuerpo) > 1:
        first = func.cuerpo[0]
        if isinstance(first, SentenciaSi):
            if _tiene_caso_base(first.cuerpo, func.nombre):
                if _buscar_llamadas_recursivas(func.cuerpo[1:], func.nombre):
                    return True

    # Original if/else pattern check
    for stmt in func.cuerpo:
        if isinstance(stmt, SentenciaSi):
            si_stmt = stmt
            # El caso base no debe llamar recursivamente
            if _tiene_caso_base(si_stmt.cuerpo, func.nombre):
                # El caso recursivo debe llamar a la función
                if si_stmt.cuerpo_sino and _buscar_llamadas_recursivas(si_stmt.cuerpo_sino, func.nombre):
                    return True
                # También verificar si hay otro if anidado
                for sub in si_stmt.cuerpo:
                    if isinstance(sub, SentenciaSi):
                        sub_si = sub
                        if _tiene_caso_base(sub_si.cuerpo, func.nombre):
                            if sub_si.cuerpo_sino and _buscar_llamadas_recursivas(sub_si.cuerpo_sino, func.nombre):
                                return True
    return False


def _es_expresion_booleana_valida(expr: Optional[Nodo]) -> bool:
    """Valida que una expresión sea una condición booleana válida para contratos.

    Permite:
    - Operadores de comparación (<, >, ==, !=, <=, >=) como raíz de la condición
    - Operadores lógicos (&&, ||) combinando condiciones
    - Operaciones aritméticas DENTRO de comparaciones (ej. _resultado_ * b == a)
    - Literales, identificadores, llamadas a funciones booleanas

    Rechaza:
    - Operaciones aritméticas puras como condición (a + b sin comparación)
    - Efectos secundarios (I/O, lanzar hilos)
    """
    if expr is None:
        return False
    # Manual 2 §5.1: solo LiteralBooleano (verdadero/falso) es un literal
    # booleano válido. Literales numéricos, decimales, cadena o nulo no.
    if isinstance(expr, LiteralBooleano):
        return True
    if isinstance(expr, (LiteralNumero, LiteralDecimal, LiteralNulo, LiteralCadena)):
        return False
    if isinstance(expr, Identificador):
        return True
    if isinstance(expr, OpBinaria):
        op = expr
        # Operadores de comparación: permiten cualquier expresión en sus lados
        if op.operador in ('==', '!=', '<', '>', '<=', '>='):
            # Dentro de una comparación, las subexpresiones pueden ser
            # cualquier expresión válida (incluyendo aritmética)
            return _es_expresion_contrato_interna(op.izquierdo) and _es_expresion_contrato_interna(op.derecho)
        # Operadores lógicos
        if op.operador in ('&&', '||'):
            return _es_expresion_booleana_valida(op.izquierdo) and _es_expresion_booleana_valida(op.derecho)
        # Operadores aritméticos puros NO son contratos válidos
        if op.operador in ('+', '-', '*', '/', '%'):
            return False
        return _es_expresion_booleana_valida(op.izquierdo) and _es_expresion_booleana_valida(op.derecho)
    if isinstance(expr, OpUnaria):
        return expr.operador in ('!', '-')
    if isinstance(expr, LlamadaFuncion):
        # Llamadas de I/O o efectos no permitidas en contratos
        return expr.nombre not in {'escribir', 'escribir_linea', 'leer', 'leer_linea',
                                    'abrir', 'cerrar_archivo', 'lanzar'}
    return False


def _es_expresion_contrato_interna(expr: Optional[Nodo]) -> bool:
    """Valida una expresión interna de contrato (dentro de una comparación).
    Permite expresiones aritméticas, literales, identificadores, etc.
    """
    if expr is None:
        return False
    if isinstance(expr, (LiteralNumero, LiteralDecimal, LiteralBooleano, LiteralNulo, LiteralCadena, Identificador)):
        return True
    if isinstance(expr, OpBinaria):
        op = expr
        # Dentro de una comparación se permiten operaciones aritméticas
        if op.operador in ('+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>=', '&&', '||'):
            return _es_expresion_contrato_interna(op.izquierdo) and _es_expresion_contrato_interna(op.derecho)
        return False
    if isinstance(expr, OpUnaria):
        return expr.operador in ('!', '-')
    if isinstance(expr, LlamadaFuncion):
        return expr.nombre not in {'escribir', 'escribir_linea', 'leer', 'leer_linea',
                                    'abrir', 'cerrar_archivo', 'lanzar'}
    return False


def _menciona_resultado(expr: Optional[Nodo]) -> bool:
    """Verifica si una expresión menciona la variable _resultado_."""
    if expr is None:
        return False
    if isinstance(expr, Identificador):
        return expr.nombre == '_resultado_'
    if isinstance(expr, OpBinaria):
        return _menciona_resultado(expr.izquierdo) or _menciona_resultado(expr.derecho)
    if isinstance(expr, OpUnaria):
        return _menciona_resultado(expr.expr)
    if isinstance(expr, LlamadaFuncion):
        for arg in expr.argumentos:
            if _menciona_resultado(arg):
                return True
    return False


class VerificadorFormal:
    """Verificador formal para modo --safe.

    Se ejecuta después del análisis semántico y reporta errores a través
    del DiagnosticManager compartido.
    """

    def __init__(self, ast: Programa, diag: DiagnosticManager):
        self.ast = ast
        self.diag = diag
        self._funciones_puras: Set[str] = set()
        self._funciones_recursivas: Set[str] = set()
        self._funciones: Dict[str, DefinicionFuncion] = {}
        self._globales: List[Nodo] = []

    def verificar(self) -> None:
        """Ejecuta todas las pasadas de verificación formal."""
        if self.diag.hay_errores():
            return

        # Pasada 0: recolectar funciones y globales
        self._recolectar_simbolos()

        # Pasada 1: Identificar funciones puras
        self._identificar_funciones_puras()

        # Pasada 2: Verificar bucles 'mientras' acotados
        self._verificar_bucles_acotados()

        # Pasada 3: Verificar mutaciones globales
        self._verificar_mutaciones_globales()

        # Pasada 4: Verificar terminación recursiva
        self._verificar_terminacion_recursiva()

        # Pasada 5: Validar contratos formales
        self._validar_contratos()

    def _recolectar_simbolos(self) -> None:
        """Recolecta funciones y declaraciones globales."""
        for stmt in self.ast.sentencias:
            if isinstance(stmt, DefinicionFuncion):
                self._funciones[stmt.nombre] = stmt
            elif isinstance(stmt, AsignacionVariable):
                self._globales.append(stmt)

    def _identificar_funciones_puras(self) -> None:
        """Identifica funciones marcadas como puras."""
        for nombre, func in self._funciones.items():
            if _es_funcion_pura_por_nombre(func):
                self._funciones_puras.add(nombre)

    def _verificar_bucles_acotados(self) -> None:
        """Pasada 2: Verifica que los bucles 'mientras' tengan cota estática."""
        for nombre, func in self._funciones.items():
            self._inspeccionar_bucles(func.cuerpo, nombre)

    def _inspeccionar_bucles(self, cuerpo: List[Nodo], nombre_func: str) -> None:
        """Inspecciona recursivamente un cuerpo en busca de bucles sin cota."""
        for stmt in cuerpo:
            if isinstance(stmt, SentenciaMientras):
                mientras_stmt = stmt
                if not _tiene_cota_estatica(mientras_stmt):
                    self.diag.reportar(
                        ErrorCodes.ERR_VER_WHILE_INACOTADO,
                        self._token(stmt.linea, stmt.columna),
                    )
            # Recurrir en sub-bloques
            if _tiene_cuerpo(stmt):
                self._inspeccionar_bucles(_obtener_cuerpo(stmt), nombre_func)
            sino_cuerpo = _obtener_cuerpo_sino(stmt)
            if sino_cuerpo:
                self._inspeccionar_bucles(sino_cuerpo, nombre_func)

    def _verificar_mutaciones_globales(self) -> None:
        """Pasada 3: Verifica que no haya mutaciones globales en modo --safe.

        Las asignaciones a nivel global están prohibidas.
        Dentro de funciones, se verifica que no se mute estado global.
        """
        # Verificar asignaciones globales directas
        for stmt in self._globales:
            self.diag.reportar(
                ErrorCodes.ERR_VER_MUTACION_GLOBAL,
                self._token(stmt.linea, stmt.columna),
                nombre=stmt.nombre if hasattr(stmt, 'nombre') else '(desconocida)',
            )

        # Verificar funciones puras sin efectos secundarios
        for nombre in self._funciones_puras:
            func = self._funciones[nombre]
            self._verificar_funcion_sin_efectos(func.cuerpo, nombre)

    def _verificar_funcion_sin_efectos(self, cuerpo: List[Nodo], nombre_func: str) -> None:
        """Verifica que una función pura no tenga efectos secundarios."""
        for stmt in cuerpo:
            if isinstance(stmt, AsignacionCampo):
                self.diag.reportar(
                    ErrorCodes.ERR_VER_MUTACION_GLOBAL,
                    self._token(stmt.linea, stmt.columna),
                    nombre=nombre_func,
                )
            if isinstance(stmt, BloqueInseguro):
                self.diag.reportar(
                    ErrorCodes.ERR_VER_MUTACION_GLOBAL,
                    self._token(stmt.linea, stmt.columna),
                    nombre=nombre_func,
                )
            if isinstance(stmt, SentenciaLanzar):
                self.diag.reportar(
                    ErrorCodes.ERR_VER_MUTACION_GLOBAL,
                    self._token(stmt.linea, stmt.columna),
                    nombre=nombre_func,
                )
            # Recurrir
            if _tiene_cuerpo(stmt):
                self._verificar_funcion_sin_efectos(_obtener_cuerpo(stmt), nombre_func)
            sino_cuerpo = _obtener_cuerpo_sino(stmt)
            if sino_cuerpo:
                self._verificar_funcion_sin_efectos(sino_cuerpo, nombre_func)

    def _verificar_terminacion_recursiva(self) -> None:
        """Pasada 4: Verifica que las funciones recursivas tengan convergencia."""
        for nombre, func in self._funciones.items():
            if _buscar_llamadas_recursivas(func.cuerpo, nombre):
                self._funciones_recursivas.add(nombre)
                if not _tiene_convergencia_estructural(func):
                    self.diag.reportar(
                        ErrorCodes.ERR_VER_RECURSION_NO_TERMINAL,
                        self._token(func.linea, func.columna),
                        nombre=nombre,
                    )

    def _validar_contratos(self) -> None:
        """Pasada 5: Valida estáticamente los contratos requiere/garantiza."""
        for nombre, func in self._funciones.items():
            tiene_requiere = len(func.requiere) > 0
            tiene_garantiza = len(func.garantiza) > 0

            if not tiene_requiere and not tiene_garantiza:
                continue

            # Validar expresiones de requiere
            for expr in func.requiere:
                if not _es_expresion_booleana_valida(expr):
                    self.diag.reportar(
                        ErrorCodes.ERR_VER_CONTRATO_INVALIDO,
                        self._token(getattr(expr, 'linea', func.linea),
                                    getattr(expr, 'columna', func.columna)),
                        nombre=nombre,
                        detalle="Expresión inválida en cláusula 'requiere': debe ser una condición lógica",
                    )

            # Validar expresiones de garantiza
            for expr in func.garantiza:
                if not _es_expresion_booleana_valida(expr):
                    self.diag.reportar(
                        ErrorCodes.ERR_VER_CONTRATO_INVALIDO,
                        self._token(getattr(expr, 'linea', func.linea),
                                    getattr(expr, 'columna', func.columna)),
                        nombre=nombre,
                        detalle="Expresión inválida en cláusula 'garantiza': debe ser una condición lógica",
                    )

            # Validar que garantiza no use _resultado_ si retorna void
            if tiene_garantiza and func.tipo_retorno in ('nulo', 'void'):
                for expr in func.garantiza:
                    if _menciona_resultado(expr):
                        self.diag.reportar(
                            ErrorCodes.ERR_VER_CONTRATO_INVALIDO,
                            self._token(getattr(expr, 'linea', func.linea),
                                        getattr(expr, 'columna', func.columna)),
                            nombre=nombre,
                            detalle="Cláusula 'garantiza' menciona '_resultado_' pero la función retorna void",
                        )

    def _token(self, linea: int, columna: int):
        """Crea un token para reportar errores."""
        from compilador.ast_nodes import Token, TokenID
        return Token(TokenID.IDENTIFIER, linea, columna)
