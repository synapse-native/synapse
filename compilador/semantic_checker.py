import re
from typing import Dict

from compilador.ast_nodes import (
    Nodo, DefinicionFuncion, DefinicionEstructura,
    AsignacionVariable, DeclaracionVariable, StmtConstante,
    AsignacionCampo, SentenciaSi, SentenciaMientras, SentenciaPara,
    SentenciaRetornar, SentenciaLanzar, SentenciaExpr,
    SentenciaEscuchar, SentenciaRecuperar, BloqueInseguro,
    SentenciaEnviarCanal, LogLlamada, NodoCoincidir, Identificador,
    LlamadaFuncion, DeclaracionExterna, ArgumentoTransferido,
)
from compilador.diagnostics import ErrorCodes
from compilador.symbol_table import Simbolo
from compilador.semantic_scope import _tipo_normalizado, _FUNCIONES_BUILTIN
from compilador.semantic_types import AnalizadorSemanticoTypes


# --- Lifetime/Region type constants (Manual 4.3) ---
LT_ESTATICO = 0       # 'static
LT_LOCAL = 1          # Variable local
LT_PARAMETRICO = 2    # Parametro de funcion
LT_ELIDIDO = 3        # Elided (sera inferido)

REGION_OUTLIVES = 0   # 'a: 'b
REGION_EQUALS = 1     # 'a == 'b
REGION_SUBSCOPE = 2   # 'a <: 'b


class Lifetime:
    """Representa un lifetime en el sistema de regiones (Manual 4.3)."""
    def __init__(self, kind: int, ambito: int = -1, indice: int = -1, padre: int = -1):
        self.kind = kind
        self.ambito = ambito
        self.indice = indice
        self.padre = padre

    def es_valido(self) -> bool:
        return 0 <= self.kind <= 3

    def es_estatico(self) -> bool:
        return self.kind == LT_ESTATICO

    def es_elidido(self) -> bool:
        return self.kind == LT_ELIDIDO

    def __repr__(self) -> str:
        if self.kind == LT_ESTATICO: return "'static"
        if self.kind == LT_LOCAL: return f"'local({self.ambito})"
        if self.kind == LT_PARAMETRICO: return f"'param({self.indice})"
        return "'elided"


class RegionConstraint:
    """Restriccion en el grafo de regiones entre dos lifetimes."""
    def __init__(self, tipo: int, origen: Lifetime, destino: Lifetime, linea: int = 0):
        self.tipo = tipo
        self.origen = origen
        self.destino = destino
        self.linea = linea


class RegionGraph:
    """Grafo de restricciones de regiones (Manual 4.3).
    
    Almacena todas las restricciones entre lifetimes para su
    posterior resolucion mediante el algoritmo de unificacion.
    """
    def __init__(self):
        self.constraints: list[RegionConstraint] = []

    def agregar_restriccion(self, tipo: int, origen: Lifetime, destino: Lifetime, linea: int = 0):
        self.constraints.append(RegionConstraint(tipo, origen, destino, linea))

    def resolver(self) -> list[RegionConstraint]:
        """Resuelve el grafo de restricciones (placeholder para M21.2)."""
        return self.constraints


class AnalizadorSemanticoChecker(AnalizadorSemanticoTypes):
    def analizar(self):
        for s in self.programa.sentencias:
            if isinstance(s, DefinicionEstructura):
                if s.nombre in self._estructuras:
                    self.diag.reportar(
                        ErrorCodes.ERR_SEM_REDEFINICION,
                        self._token(s.linea, s.columna),
                        nombre=s.nombre
                    )
                else:
                    self._estructuras[s.nombre] = s
        for s in self.programa.sentencias:
            if isinstance(s, DefinicionFuncion):
                if not self.tabla.declarar(s.nombre, s.tipo_retorno, s):
                    self.diag.reportar(
                        ErrorCodes.ERR_SEM_REDEFINICION,
                        self._token(s.linea, s.columna),
                        nombre=s.nombre
                    )
            elif isinstance(s, DeclaracionExterna):
                if not self.tabla.declarar(s.nombre, s.tipo_retorno, s):
                    self.diag.reportar(
                        ErrorCodes.ERR_SEM_REDEFINICION,
                        self._token(s.linea, s.columna),
                        nombre=s.nombre
                    )
            elif isinstance(s, StmtConstante):
                tipo_const = self._inferir_tipo(s.valor)
                if tipo_const:
                    sim = Simbolo(s.nombre, tipo_const, s, es_constante=True)
                    cur = self.tabla._scopes[-1]
                    if s.nombre in cur:
                        self.diag.reportar(
                            ErrorCodes.ERR_SEM_REDEFINICION,
                            self._token(s.linea, s.columna),
                            nombre=s.nombre
                        )
                    else:
                        cur[s.nombre] = sim
        for s in self.programa.sentencias:
            if isinstance(s, DefinicionFuncion) and s.nombre not in _FUNCIONES_BUILTIN:
                self._analizar_funcion(s)

    def _analizar_funcion(self, nodo: DefinicionFuncion):
        self.tabla.entrar_scope()
        self._func_retorno = nodo.tipo_retorno
        self._func_actual = nodo.nombre
        self._asignaciones_campos: Dict[str, Dict[str, str]] = {}
        for p in nodo.parametros:
            self.tabla.declarar(p.nombre, p.tipo, nodo)
        for s in nodo.cuerpo:
            self._analizar_sentencia(s)
        self.tabla.salir_scope()
        self._func_retorno = None
        self._func_actual = None
        self._asignaciones_campos = {}

    def _analizar_sentencia(self, nodo: Nodo):
        if isinstance(nodo, AsignacionVariable):
            sim_existente = self.tabla.buscar(nodo.nombre)
            if sim_existente and sim_existente.es_constante:
                self.diag.reportar(
                    ErrorCodes.ERR_SEM_CONSTANTE_INMUTABLE,
                    self._token(nodo.linea, nodo.columna),
                    nombre=nodo.nombre
                )
                return
            tipo_expr = self._inferir_tipo(nodo.expresion)
            if tipo_expr:
                if sim_existente:
                    # Variable already declared: validate type compatibility
                    norm_existente = _tipo_normalizado(sim_existente.tipo)
                    norm_expr = _tipo_normalizado(tipo_expr)
                    if norm_existente != norm_expr:
                        self.diag.reportar(
                            ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE,
                            self._token(nodo.linea, nodo.columna),
                            tipo1=tipo_expr, tipo2=sim_existente.tipo,
                            operacion="asignacion"
                        )
                else:
                    # First declaration in this scope
                    self.tabla.declarar(nodo.nombre, tipo_expr, nodo)
        elif isinstance(nodo, DeclaracionVariable):
            sim_existente = self.tabla.buscar(nodo.nombre)
            if sim_existente and sim_existente.es_constante:
                self.diag.reportar(
                    ErrorCodes.ERR_SEM_CONSTANTE_INMUTABLE,
                    self._token(nodo.linea, nodo.columna),
                    nombre=nodo.nombre
                )
                return
            tipo_expr = self._inferir_tipo(nodo.expresion)
            if tipo_expr:
                norm_decl = _tipo_normalizado(nodo.tipo)
                norm_expr = _tipo_normalizado(tipo_expr)
                if norm_decl != norm_expr:
                    self.diag.reportar(
                        ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE,
                        self._token(nodo.linea, nodo.columna),
                        tipo1=tipo_expr, tipo2=nodo.tipo, operacion='declaracion'
                    )
                else:
                    self.tabla.declarar(nodo.nombre, nodo.tipo, nodo)
        elif isinstance(nodo, StmtConstante):
            tipo_const = self._inferir_tipo(nodo.valor)
            if tipo_const:
                sim = Simbolo(nodo.nombre, tipo_const, nodo, es_constante=True)
                cur = self.tabla._scopes[-1]
                if nodo.nombre in cur:
                    self.diag.reportar(
                        ErrorCodes.ERR_SEM_REDEFINICION,
                        self._token(nodo.linea, nodo.columna),
                        nombre=nodo.nombre
                    )
                else:
                    cur[nodo.nombre] = sim
        elif isinstance(nodo, AsignacionCampo):
            tipo_obj = self._inferir_tipo(nodo.objeto)
            if tipo_obj:
                base_tipo = tipo_obj.rstrip('*')
                struct = self._estructuras.get(base_tipo)
                if struct is None:
                    self.diag.reportar(
                        ErrorCodes.ERR_SEM_ESTRUCTURA_NO_DEFINIDA,
                        self._token(nodo.linea, nodo.columna),
                        nombre=base_tipo
                    )
                else:
                    campo_val = next((c for c in struct.campos if c.nombre == nodo.nombre_campo), None)
                    if campo_val is None:
                        self.diag.reportar(
                            ErrorCodes.ERR_SEM_CAMPO_NO_EXISTE,
                            self._token(nodo.linea, nodo.columna),
                            struct=base_tipo, campo=nodo.nombre_campo
                        )
                    else:
                        tipo_expr = self._inferir_tipo(nodo.expresion)
                        if tipo_expr and _tipo_normalizado(tipo_expr) != _tipo_normalizado(campo_val.tipo):
                            self.diag.reportar(
                                ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE,
                                self._token(nodo.linea, nodo.columna),
                                tipo1=tipo_expr, tipo2=campo_val.tipo, operacion='asignacion campo'
                            )
                        if isinstance(nodo.objeto, Identificador):
                            var_nombre = nodo.objeto.nombre
                            if var_nombre not in self._asignaciones_campos:
                                self._asignaciones_campos[var_nombre] = {}
                            self._asignaciones_campos[var_nombre][nodo.nombre_campo] = campo_val.tipo
        elif isinstance(nodo, SentenciaSi):
            tipo_cond = self._inferir_tipo(nodo.condicion)
            if tipo_cond and _tipo_normalizado(tipo_cond) not in ('int', 'float', 'booleano'):
                self.diag.reportar(
                    ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE,
                    self._token(nodo.linea, nodo.columna),
                    tipo1=tipo_cond, tipo2='int', operacion='condicion si'
                )
            self.tabla.entrar_scope()
            for s in nodo.cuerpo:
                self._analizar_sentencia(s)
            self.tabla.salir_scope()
            if nodo.cuerpo_sino:
                self.tabla.entrar_scope()
                for s in nodo.cuerpo_sino:
                    self._analizar_sentencia(s)
                self.tabla.salir_scope()
        elif isinstance(nodo, SentenciaMientras):
            tipo_cond = self._inferir_tipo(nodo.condicion)
            if tipo_cond and _tipo_normalizado(tipo_cond) not in ('int', 'float', 'booleano'):
                self.diag.reportar(
                    ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE,
                    self._token(nodo.linea, nodo.columna),
                    tipo1=tipo_cond, tipo2='int', operacion='condicion mientras'
                )
            self.tabla.entrar_scope()
            for s in nodo.cuerpo:
                self._analizar_sentencia(s)
            self.tabla.salir_scope()
        elif isinstance(nodo, SentenciaPara):
            self.tabla.entrar_scope()
            if nodo.inicializacion:
                self._analizar_sentencia(nodo.inicializacion)
            if nodo.condicion:
                tipo_cond = self._inferir_tipo(nodo.condicion)
                if tipo_cond and _tipo_normalizado(tipo_cond) not in ('int', 'float', 'booleano'):
                    self.diag.reportar(
                        ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE,
                        self._token(nodo.linea, nodo.columna),
                        tipo1=tipo_cond, tipo2='int', operacion='condicion para'
                    )
            if nodo.incremento:
                self._analizar_sentencia(nodo.incremento)
            for s in nodo.cuerpo:
                self._analizar_sentencia(s)
            self.tabla.salir_scope()
        elif isinstance(nodo, SentenciaRetornar):
            if nodo.expr:
                tipo_ret = self._inferir_tipo(nodo.expr)
                if tipo_ret and _tipo_normalizado(tipo_ret) != _tipo_normalizado(self._func_retorno or 'nulo'):
                    self.diag.reportar(
                        ErrorCodes.ERR_SEM_TIPO_RETORNO,
                        self._token(nodo.linea, nodo.columna),
                        esperado=self._func_retorno or 'nulo',
                        obtenido=tipo_ret
                    )
            elif self._func_retorno and _tipo_normalizado(self._func_retorno) != 'void':
                self.diag.reportar(
                    ErrorCodes.ERR_SEM_TIPO_RETORNO,
                    self._token(nodo.linea, nodo.columna),
                    esperado=self._func_retorno,
                    obtenido='nulo'
                )
        elif isinstance(nodo, SentenciaLanzar):
            self._inferir_tipo(nodo.llamada)
            if isinstance(nodo.llamada, LlamadaFuncion):
                for arg in nodo.llamada.argumentos:
                    if isinstance(arg, ArgumentoTransferido) and isinstance(arg.expr, Identificador):
                        self.tabla.marcar_movido(arg.expr.nombre)
        elif isinstance(nodo, SentenciaExpr):
            self._inferir_tipo(nodo.expr)
        elif isinstance(nodo, SentenciaEscuchar):
            self._inferir_tipo(nodo.canal) if nodo.canal else None
            if nodo.respuesta and isinstance(nodo.respuesta, LlamadaFuncion):
                sim = self.tabla.buscar(nodo.respuesta.nombre)
                if sim and isinstance(sim.nodo, DefinicionFuncion):
                    pass
                self._inferir_tipo(nodo.respuesta)
        elif isinstance(nodo, SentenciaRecuperar):
            self._inferir_tipo(nodo.accion_critica) if nodo.accion_critica else None
            self._inferir_tipo(nodo.plan_b) if nodo.plan_b else None
        elif isinstance(nodo, BloqueInseguro):
            self.tabla.entrar_scope()
            _prev_inseguro = self._dentro_de_inseguro
            self._dentro_de_inseguro = True
            for s in nodo.cuerpo:
                self._analizar_sentencia(s)
            self._dentro_de_inseguro = _prev_inseguro
            self.tabla.salir_scope()
        elif isinstance(nodo, SentenciaEnviarCanal):
            self._inferir_tipo(nodo.canal) if nodo.canal else None
            if nodo.valor and isinstance(nodo.valor, Identificador):
                self._inferir_tipo(nodo.valor)
                self.tabla.marcar_movido(nodo.valor.nombre)
        elif isinstance(nodo, LogLlamada):
            for a in nodo.argumentos:
                self._inferir_tipo(a)
        elif isinstance(nodo, NodoCoincidir):
            self._en_coincidir = True
            tipo_expr = self._inferir_tipo(nodo.expresion)
            variantes_cubiertas = set()
            tiene_comodin = False
            for caso in nodo.casos:
                if caso.patron == '_':
                    tiene_comodin = True
                    self.tabla.entrar_scope()
                    for stmt in caso.cuerpo:
                        self._analizar_sentencia(stmt)
                    self.tabla.salir_scope()
                    continue
                match = re.match(r'(\w+)\((\w+)\)', caso.patron)
                if match:
                    var_nombre = match.group(2)
                    tag_nombre = match.group(1)
                    variantes_cubiertas.add(tag_nombre)
                    tipo_extraido = 'int'
                    if tipo_expr:
                        nombre_struct = tipo_expr
                        if nombre_struct.startswith('struct '):
                            nombre_struct = nombre_struct[7:]
                        if nombre_struct in self._estructuras:
                            struct_def = self._estructuras[nombre_struct]
                            for campo in struct_def.campos:
                                if campo.tipo == 'texto':
                                    tipo_extraido = 'texto'
                                    break
                                elif campo.tipo == 'decimal' and tipo_extraido == 'int':
                                    tipo_extraido = 'decimal'
                    elif tipo_expr == 'texto':
                        tipo_extraido = 'texto'
                    elif tipo_expr == 'decimal':
                        tipo_extraido = 'decimal'
                    caso.tipo_extraido = tipo_extraido
                    self.tabla.declarar(var_nombre, tipo_extraido, nodo)
                    self.tabla.entrar_scope()
                    for stmt in caso.cuerpo:
                        self._analizar_sentencia(stmt)
                    self.tabla.salir_scope()
            # Manual 2 S2.4: Verificar exhaustividad de patrones
            if not tiene_comodin:
                variantes_esperadas = set()
                if tipo_expr:
                    tipo_base = tipo_expr.replace('struct ', '')
                    # Resultado<T,E> tiene variantes: ok, err
                    # Opcion<T> tiene variantes: algun, ninguno
                    if tipo_base == 'Resultado' or tipo_base == 'Resultado_T':
                        variantes_esperadas = {'ok', 'err'}
                    elif tipo_base == 'Opcion' or tipo_base == 'Opcion_T':
                        variantes_esperadas = {'algun', 'ninguno'}
                if variantes_esperadas:
                    faltantes = variantes_esperadas - variantes_cubiertas
                    if faltantes:
                        self.diag.reportar(
                            ErrorCodes.ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED,
                            self._token(nodo.linea, nodo.columna),
                            faltan=', '.join(sorted(faltantes))
                        )
            self._en_coincidir = False
