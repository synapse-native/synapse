from typing import Optional

from compilador.ast_nodes import (
    Nodo, LiteralNumero, LiteralDecimal, LiteralCadena, LiteralBooleano,
    Identificador, OpBinaria, OpUnaria, LlamadaFuncion, ExprTensor,
    ArgumentoTransferido, ExprAsm, ExprObtenerDireccion, ExprDereferencia,
    ExprAccesoCampo, ExprCrearCanal, ExprRecibirCanal,
    DefinicionFuncion,
)
from compilador.diagnostics import ErrorCodes
from compilador.semantic_scope import _tipo_normalizado, _FUNCIONES_BUILTIN, AnalizadorSemanticoScope


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
        return None

    def _inferir_tipo_llamada(self, nodo: LlamadaFuncion) -> Optional[str]:
        if nodo.nombre == 'log':
            for a in nodo.argumentos:
                self._inferir_tipo(a)
            return 'nulo'

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
                    if tipo_arg == 'decimal' and esperado == 'texto':
                        continue
                    if tipo_arg == 'int' and esperado == 'texto':
                        continue
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

        sim = self.tabla.buscar(nodo.nombre)
        if sim is None:
            self.diag.reportar(
                ErrorCodes.ERR_SEM_FUNC_NO_DEFINIDA,
                self._token(nodo.linea, nodo.columna),
                nombre=nodo.nombre
            )
            return None

        def_func = sim.nodo
        if isinstance(def_func, DefinicionFuncion):
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
        return sim.tipo
