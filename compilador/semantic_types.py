from typing import Optional

from compilador.ast_nodes import (
    Nodo, LiteralNumero, LiteralDecimal, LiteralCadena, LiteralBooleano,
    Identificador, OpBinaria, OpUnaria, LlamadaFuncion, ExprTensor,
    ArgumentoTransferido, ExprAsm, ExprObtenerDireccion, ExprDereferencia,
    ExprAccesoCampo, ExprCrearCanal, ExprRecibirCanal, ExprIndice,
    DefinicionFuncion,
)
from compilador.diagnostics import ErrorCodes
from compilador.semantic_scope import _tipo_normalizado, _FUNCIONES_BUILTIN, AnalizadorSemanticoScope

# M21.3: Lifetime constants for constraint generation (Manual 4.3)
LT_ESTATICO = 0
LT_LOCAL = 1
LT_PARAMETRICO = 2
LT_ELIDIDO = 3
REGION_OUTLIVES = 0
REGION_EQUALS = 1
REGION_SUBSCOPE = 2


class Lifetime:
    """Representa un lifetime en el sistema de regiones (Manual 4.3)."""
    def __init__(self, kind: int, ambito: int = -1, indice: int = -1, padre: int = -1):
        self.kind = kind
        self.ambito = ambito
        self.indice = indice
        self.padre = padre


class RegionConstraint:
    """Restriccion entre dos lifetimes."""
    def __init__(self, tipo: int, origen: Lifetime, destino: Lifetime, linea: int = 0):
        self.tipo = tipo
        self.origen = origen
        self.destino = destino
        self.linea = linea


class AnalizadorSemanticoTypes(AnalizadorSemanticoScope):
    def _inferir_tipo(self, nodo: Nodo) -> Optional[str]:
        if isinstance(nodo, LiteralNumero):
            return 'int'
        elif isinstance(nodo, LiteralDecimal):
            return 'decimal'
        elif isinstance(nodo, LiteralCadena):
            return 'texto'
        elif isinstance(nodo, LiteralBooleano):
            return 'booleano'
        elif isinstance(nodo, Identificador):
            if nodo.nombre == 'nulo':
                return 'puntero'
            sim = self.tabla.buscar(nodo.nombre)
            if sim is None:
                self.diag.reportar(
                    ErrorCodes.ERR_SEM_VAR_NO_DECLARADA,
                    self._token(nodo.linea, nodo.columna),
                    nombre=nodo.nombre
                )
                return None
            if self.tabla.esta_movido(nodo.nombre):
                self.diag.reportar(
                    ErrorCodes.ERR_SEM_VAR_MOVIDA,
                    self._token(nodo.linea, nodo.columna),
                    nombre=nodo.nombre
                )
            # Manual 4 §4.2: auto-deref al leer una referencia (&T / &mut T)
            if sim.tipo.startswith('&mut '):
                return sim.tipo[5:]
            if sim.tipo.startswith('&'):
                return sim.tipo[1:]
            return sim.tipo
        elif isinstance(nodo, OpBinaria):
            tipo_izq = self._inferir_tipo(nodo.izquierdo)
            tipo_der = self._inferir_tipo(nodo.derecho)
            if tipo_izq and tipo_der:
                norm_izq = _tipo_normalizado(tipo_izq)
                norm_der = _tipo_normalizado(tipo_der)

                if nodo.operador in ('&&', '||'):
                    if norm_izq not in ('int', 'float'):
                        self.diag.reportar(
                            ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE,
                            self._token(nodo.linea, nodo.columna),
                            tipo1=tipo_izq, tipo2='int/float', operacion=nodo.operador
                        )
                        return None
                    if norm_der not in ('int', 'float'):
                        self.diag.reportar(
                            ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE,
                            self._token(nodo.linea, nodo.columna),
                            tipo1=tipo_der, tipo2='int/float', operacion=nodo.operador
                        )
                        return None
                    return 'int'

                if (tipo_izq == 'booleano' and tipo_der != 'booleano') or (tipo_izq != 'booleano' and tipo_der == 'booleano'):
                    self.diag.reportar(
                        ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE,
                        self._token(nodo.linea, nodo.columna),
                        tipo1=tipo_izq, tipo2=tipo_der, operacion=nodo.operador
                    )
                    return None

                if norm_izq == 'float' and norm_der == 'int':
                    return 'decimal'
                if norm_izq == 'int' and norm_der == 'float':
                    return 'decimal'
                if norm_izq == 'float' and norm_der == 'float':
                    return 'decimal'
                if norm_izq == 'CadenaSegura' and norm_der == 'CadenaSegura' and nodo.operador in ('==', '!='):
                    return 'int'
                if norm_izq == 'CadenaSegura' and norm_der == 'CadenaSegura' and nodo.operador == '+':
                    return 'texto'
                if norm_izq != norm_der:
                    self.diag.reportar(
                        ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE,
                        self._token(nodo.linea, nodo.columna),
                        tipo1=tipo_izq, tipo2=tipo_der, operacion=nodo.operador
                    )
                    return None
                if norm_izq in ('int', 'float'):
                    return 'decimal' if (norm_izq == 'float' or norm_der == 'float') else 'int'
                return None
        elif isinstance(nodo, OpUnaria):
            tipo_expr = self._inferir_tipo(nodo.expr)
            if tipo_expr and _tipo_normalizado(tipo_expr) not in ('int', 'float', 'booleano'):
                self.diag.reportar(
                    ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE,
                    self._token(nodo.linea, nodo.columna),
                    tipo1=tipo_expr, tipo2='int', operacion=nodo.operador
                )
                return None
            if nodo.operador == '!':
                return 'booleano'
            return 'decimal' if (tipo_expr and _tipo_normalizado(tipo_expr) == 'float') else 'int'
        elif isinstance(nodo, LlamadaFuncion):
            return self._inferir_tipo_llamada(nodo)
        elif isinstance(nodo, ExprTensor):
            tipo_f = self._inferir_tipo(nodo.filas)
            tipo_c = self._inferir_tipo(nodo.columnas)
            if tipo_f and _tipo_normalizado(tipo_f) != 'int':
                self.diag.reportar(
                    ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE,
                    self._token(nodo.linea, nodo.columna),
                    tipo1=tipo_f, tipo2='int', operacion='tensor(filas, columnas)'
                )
            if tipo_c and _tipo_normalizado(tipo_c) != 'int':
                self.diag.reportar(
                    ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE,
                    self._token(nodo.linea, nodo.columna),
                    tipo1=tipo_c, tipo2='int', operacion='tensor(filas, columnas)'
                )
            return 'tensor'
        elif isinstance(nodo, ArgumentoTransferido):
            return self._inferir_tipo(nodo.expr)
        elif isinstance(nodo, ExprAsm):
            if not self._dentro_de_inseguro:
                self.diag.reportar(
                    ErrorCodes.ERR_SEM_ASM_FUERA_INSEGURO,
                    self._token(nodo.linea, nodo.columna),
                )
            return 'nulo'
        elif isinstance(nodo, ExprObtenerDireccion):
            tipo_base = self._inferir_tipo(nodo.expr)
            # Manual 4 S4.2: verificar coexistencia de prestamos (borrow checker)
            self._verificar_prestamo(nodo)
            # M21.3: Generar constraint de borrow si lifetime tracking esta activo
            if tipo_base and hasattr(self, '_region_graph'):
                lt_borrow = Lifetime(LT_LOCAL, self.tabla.scope_nivel, self._proximo_lifetime, -1)
                lt_original = Lifetime(LT_LOCAL, 0, 0, -1)
                self._region_graph.agregar_restriccion(REGION_OUTLIVES, lt_original, lt_borrow, nodo.linea)
                self._proximo_lifetime += 1
            if tipo_base:
                return f"{tipo_base}*"
            return None
        elif isinstance(nodo, ExprDereferencia):
            tipo_base = self._inferir_tipo(nodo.expr)
            if tipo_base:
                return tipo_base.rstrip('*')
            return None
        elif isinstance(nodo, ExprAccesoCampo):
            tipo_obj = self._inferir_tipo(nodo.objeto)
            if tipo_obj is None:
                return None
            base_tipo = tipo_obj.rstrip('*')
            struct = self._estructuras.get(base_tipo)
            if struct is None:
                self.diag.reportar(
                    ErrorCodes.ERR_SEM_ESTRUCTURA_NO_DEFINIDA,
                    self._token(nodo.linea, nodo.columna),
                    nombre=base_tipo
                )
                return None
            campo = next((c for c in struct.campos if c.nombre == nodo.nombre_campo), None)
            if campo is None:
                self.diag.reportar(
                    ErrorCodes.ERR_SEM_CAMPO_NO_EXISTE,
                    self._token(nodo.linea, nodo.columna),
                    struct=base_tipo, campo=nodo.nombre_campo
                )
                return None
            return campo.tipo
        elif isinstance(nodo, ExprCrearCanal):
            if nodo.capacidad:
                self._inferir_tipo(nodo.capacidad)
            return 'CanalConcurrencia*'
        elif isinstance(nodo, ExprRecibirCanal):
            self._inferir_tipo(nodo.canal)
            return 'void*'
        elif isinstance(nodo, ExprIndice):
            tipo_base = self._inferir_tipo(nodo.expr)
            self._inferir_tipo(nodo.indice)
            # Si el tipo base es texto/CadenaSegura, indexar devuelve un caracter (texto)
            if tipo_base:
                norm = _tipo_normalizado(tipo_base)
                if norm == 'CadenaSegura':
                    return 'texto'
            return 'int'
        return None

    def _verificar_prestamo(self, nodo: ExprObtenerDireccion):
        """Manual 4 §4.2: reglas de coexistencia de prestamos (borrow checker).

        &T inmutable: multiples prestamos inmutables simultaneos permitidos.
        &mut T mutable: un solo prestamo mutable a la vez, sin coexistir con inmutables.
        Los prestamos se registran por scope (SymbolTable._prestamos) y se liberan
        al salir del ambito.
        """
        if not hasattr(self, '_prestamos_registrados'):
            self._prestamos_registrados = set()
        if id(nodo) in self._prestamos_registrados:
            return  # idempotencia: cada nodo de prestamo se verifica una sola vez
        expr = nodo.expr
        if not isinstance(expr, Identificador):
            return  # solo se rastrean prestamos sobre identificadores
        nombre = expr.nombre
        if self.tabla.buscar(nombre) is None:
            return  # variable no declarada: ya fue reportado por _inferir_tipo
        self._prestamos_registrados.add(id(nodo))
        if not self.tabla.registrar_prestamo(nombre, nodo.es_mutable):
            tipo = '&mut' if nodo.es_mutable else '&'
            self.diag.reportar(
                ErrorCodes.ERR_MEM_BORROW_CONFLICT,
                self._token(nodo.linea, nodo.columna),
                nombre=nombre,
                tipo=tipo,
            )

    def _inferir_tipo_llamada(self, nodo: LlamadaFuncion) -> Optional[str]:
        if nodo.nombre == 'log':
            for a in nodo.argumentos:
                self._inferir_tipo(a)
            return 'nulo'

        sim = self.tabla.buscar(nodo.nombre)
        # Las funciones definidas por el usuario tienen precedencia sobre los builtins
        if sim is not None and isinstance(sim.nodo, DefinicionFuncion):
            def_func = sim.nodo
            if len(nodo.argumentos) != len(def_func.parametros):
                self.diag.reportar(
                    ErrorCodes.ERR_SEM_ARGUMENTOS_INVALIDOS,
                    self._token(nodo.linea, nodo.columna),
                    nombre=nodo.nombre,
                    esperados=len(def_func.parametros)
                )
                return def_func.tipo_retorno
            for i, (arg, param) in enumerate(zip(nodo.argumentos, def_func.parametros)):
                tipo_arg = self._inferir_tipo(arg)
                if tipo_arg and _tipo_normalizado(tipo_arg) != _tipo_normalizado(param.tipo):
                    if _tipo_normalizado(param.tipo) == 'void*' and 'CadenaSegura' in (_tipo_normalizado(tipo_arg), tipo_arg):
                        continue
                    self.diag.reportar(
                        ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE,
                        self._token(getattr(arg, 'linea', 0), getattr(arg, 'columna', 0)),
                        tipo1=tipo_arg, tipo2=param.tipo, operacion=nodo.nombre
                    )
            return def_func.tipo_retorno

        if nodo.nombre in _FUNCIONES_BUILTIN:
            sig = _FUNCIONES_BUILTIN[nodo.nombre]
            tipos_esperados, tipo_retorno = sig
            if len(nodo.argumentos) != len(tipos_esperados):
                self.diag.reportar(
                    ErrorCodes.ERR_SEM_ARGUMENTOS_INVALIDOS,
                    self._token(nodo.linea, nodo.columna),
                    nombre=nodo.nombre,
                    esperados=len(tipos_esperados)
                )
                return tipo_retorno
            for i, (arg, esperado) in enumerate(zip(nodo.argumentos, tipos_esperados)):
                tipo_arg = self._inferir_tipo(arg)
                if tipo_arg and _tipo_normalizado(tipo_arg) != _tipo_normalizado(esperado):
                    # Allow int/decimal -> texto only for concat (string interpolation)
                    if esperado == 'texto' and tipo_arg in ('int', 'decimal') and nodo.nombre == 'concat':
                        continue
                    # Allow void* to accept numeric types (pointer arithmetic)
                    if esperado == 'void*' and tipo_arg in ('int', 'float', 'decimal'):
                        continue
                    self.diag.reportar(
                        ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE,
                        self._token(getattr(arg, 'linea', 0), getattr(arg, 'columna', 0)),
                        tipo1=tipo_arg, tipo2=esperado, operacion=nodo.nombre
                    )
            return tipo_retorno

        if nodo.nombre in self._estructuras:
            if len(nodo.argumentos) != 0:
                self.diag.reportar(
                    ErrorCodes.ERR_SEM_ARGUMENTOS_INVALIDOS,
                    self._token(nodo.linea, nodo.columna),
                    nombre=nodo.nombre,
                    esperados=0
                )
            return nodo.nombre

        if sim is None:
            self.diag.reportar(
                ErrorCodes.ERR_SEM_FUNC_NO_DEFINIDA,
                self._token(nodo.linea, nodo.columna),
                nombre=nodo.nombre
            )
            return None

        return sim.tipo
