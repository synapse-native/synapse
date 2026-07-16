from typing import List, Optional, Dict, Tuple

from compilador.ast_nodes import (
    Nodo, Programa, DefinicionFuncion, DefinicionEstructura,
    ExprAccesoCampo, AsignacionCampo, StmtConstante,
    SentenciaSi, SentenciaLanzar,
    SentenciaRecuperar, SentenciaRetornar, SentenciaEscuchar,
    SentenciaMientras, SentenciaRomper, SentenciaSiguiente,
    SentenciaImportar, AsignacionVariable, SentenciaExpr, LogLlamada,
    OpBinaria, OpUnaria, LlamadaFuncion, Identificador,
    LiteralNumero, LiteralDecimal, LiteralCadena, ExprTensor, ArgumentoTransferido,
    Token, TokenID, DeclaracionExterna,
    BloqueInseguro, ExprObtenerDireccion, ExprDereferencia,
    NodoCoincidir, NodoCaso,
    SentenciaEnviarCanal, ExprRecibirCanal, ExprCrearCanal,
    ExprAsm,
)
from compilador.diagnostics import DiagnosticManager, ErrorCodes
from compilador.symbol_table import SymbolTable, Simbolo, Propiedad
from compilador.generator import MAPA_TIPOS_C


_FUNCIONES_BUILTIN: Dict[str, Tuple[List[str], str]] = {
    'reserva': (['int'], 'tensor'),
    'libera': (['tensor'], 'nulo'),
    'crear_tensor': (['int', 'int'], 'tensor'),
    'suma_tensor': (['tensor', 'tensor'], 'tensor'),
    'producto_punto': (['tensor', 'tensor'], 'tensor'),
    'abrir': (['texto', 'texto'], 'Canal'),
    'leer': (['Canal'], 'texto'),
    'escribir': (['texto'], 'nulo'),
    'escribir_linea': (['texto'], 'nulo'),
    'leer_linea': ([], 'texto'),
    'cerrar': (['Canal'], 'nulo'),
    'suma': (['tensor', 'tensor'], 'tensor'),
    'producto': (['tensor', 'tensor'], 'tensor'),
    'relu': (['tensor'], 'tensor'),
    'tokenizar': (['texto'], 'int'),
    'parsear': (['texto'], 'Programa'),
    'generar': (['Programa', 'texto'], 'int'),
    '_argc': ([], 'int'),
    '_argv': (['int'], 'texto'),
    'salir': (['int'], 'nulo'),
    'concat': (['texto', 'texto'], 'texto'),
    'texto_a_entero': (['texto'], 'int'),
    'texto_a_decimal': (['texto'], 'decimal'),
    'entero_a_texto': (['int'], 'texto'),
    'decimal_a_texto': (['decimal'], 'texto'),
    'volcar_ast': (['Programa', 'int'], 'nulo'),
    'crear_analizador': (['Programa'], 'int'),
    'analizar': (['int'], 'nulo'),
    'canal_crear': (['int'], 'CanalConcurrencia*'),
    'canal_enviar': (['CanalConcurrencia*', 'void*'], 'nulo'),
    'canal_recibir': (['CanalConcurrencia*'], 'void*'),
}


def _tipo_normalizado(tipo: str) -> str:
    return MAPA_TIPOS_C.get(tipo, tipo)


class AnalizadorSemantico:
    def __init__(self, programa: Programa, diag: DiagnosticManager):
        self.programa = programa
        self.diag = diag
        self.tabla = SymbolTable()
        self._func_retorno: Optional[str] = None
        self._func_actual: Optional[str] = None
        self._estructuras: Dict[str, DefinicionEstructura] = {}
        self._en_coincidir: bool = False
        self._dentro_de_inseguro: bool = False

    def _token(self, linea: int, columna: int) -> Token:
        return Token(TokenID.IDENTIFIER, linea, columna)

    def analizar(self):
        # First pass: register struct definitions
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
        # Second pass: register functions and extern declarations
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
        # Third pass: analyze function bodies
        for s in self.programa.sentencias:
            if isinstance(s, DefinicionFuncion) and s.nombre not in _FUNCIONES_BUILTIN:
                self._analizar_funcion(s)

    def _analizar_funcion(self, nodo: DefinicionFuncion):
        self.tabla.entrar_scope()
        self._func_retorno = nodo.tipo_retorno
        self._func_actual = nodo.nombre
        # Rastrear asignaciones de campos para inferencia de tipos en coincidir
        self._asignaciones_campos: Dict[str, Dict[str, str]] = {}  # var -> campo -> tipo
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
            # Check if variable already exists and is constant
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
                self.tabla.declarar(nodo.nombre, tipo_expr, nodo)
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
                        # Rastrear asignación de campo para inferencia en coincidir
                        if isinstance(nodo.objeto, Identificador):
                            var_nombre = nodo.objeto.nombre
                            if var_nombre not in self._asignaciones_campos:
                                self._asignaciones_campos[var_nombre] = {}
                            self._asignaciones_campos[var_nombre][nodo.nombre_campo] = campo_val.tipo
        elif isinstance(nodo, SentenciaSi):
            tipo_cond = self._inferir_tipo(nodo.condicion)
            if tipo_cond and _tipo_normalizado(tipo_cond) not in ('int', 'float'):
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
            if tipo_cond and _tipo_normalizado(tipo_cond) not in ('int', 'float'):
                self.diag.reportar(
                    ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE,
                    self._token(nodo.linea, nodo.columna),
                    tipo1=tipo_cond, tipo2='int', operacion='condicion mientras'
                )
            self.tabla.entrar_scope()
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
        elif isinstance(nodo, SentenciaExpr):
            self._inferir_tipo(nodo.expr)
        elif isinstance(nodo, SentenciaEscuchar):
            self._inferir_tipo(nodo.canal) if nodo.canal else None
            self._inferir_tipo(nodo.respuesta) if nodo.respuesta else None
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
            
            # Para cada caso, extraer el nombre de variable y asignar tipo
            import re
            for caso in nodo.casos:
                if caso.patron == '_':
                    self.tabla.entrar_scope()
                    for stmt in caso.cuerpo:
                        self._analizar_sentencia(stmt)
                    self.tabla.salir_scope()
                    continue
                match = re.match(r'(\w+)\((\w+)\)', caso.patron)
                if match:
                    var_nombre = match.group(2)  # ej. "v" en "ok(v)"
                    
                    # Inferir tipo del valor extraído
                    # Heurística mejorada: buscar asignaciones de campos específicas
                    tipo_extraido = 'int'  # fallback
                    
                    if tipo_expr:
                        # Extraer nombre de struct (con o sin prefijo 'struct ')
                        nombre_struct = tipo_expr
                        if nombre_struct.startswith('struct '):
                            nombre_struct = nombre_struct[7:]
                        if nombre_struct in self._estructuras:
                            struct_def = self._estructuras[nombre_struct]
                            # Priorizar campos de tipo texto, luego decimal
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
                    
                    # Almacenar el tipo resuelto en el nodo AST
                    caso.tipo_extraido = tipo_extraido
                    
                    # Declarar la variable en la tabla de símbolos
                    self.tabla.declarar(var_nombre, tipo_extraido, nodo)
                    
                    # Analizar el cuerpo del caso
                    self.tabla.entrar_scope()
                    for stmt in caso.cuerpo:
                        self._analizar_sentencia(stmt)
                    self.tabla.salir_scope()

            self._en_coincidir = False

    def _inferir_tipo(self, nodo: Nodo) -> Optional[str]:
        if isinstance(nodo, LiteralNumero):
            return 'int'
        elif isinstance(nodo, LiteralDecimal):
            return 'decimal'
        elif isinstance(nodo, LiteralCadena):
            return 'texto'
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
                
                # Operadores lógicos (&&, ||)
                if nodo.operador in ('&&', '||'):
                    # Ambos operandos deben ser tipos que pueden evaluarse como booleanos
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
                    return 'int'  # Resultado es int (0 o 1)
                
                # Operadores aritméticos y comparación
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
            if tipo_expr and _tipo_normalizado(tipo_expr) not in ('int', 'float'):
                self.diag.reportar(
                    ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE,
                    self._token(nodo.linea, nodo.columna),
                    tipo1=tipo_expr, tipo2='int', operacion=nodo.operador
                )
                return None
            # Operador NOT (!) siempre retorna int
            if nodo.operador == '!':
                return 'int'
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
            if not self._en_coincidir:
                self.diag.reportar(
                    ErrorCodes.ERR_SEM_RESULTADO_SIN_DESEMPAQUETAR,
                    self._token(nodo.linea, nodo.columna)
                )
            return 'Resultado'
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
                        continue  # coercion implicita float -> texto
                    if tipo_arg == 'int' and esperado == 'texto':
                        continue  # coercion implicita int -> texto
                    self.diag.reportar(
                        ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE,
                        self._token(getattr(arg, 'linea', 0), getattr(arg, 'columna', 0)),
                        tipo1=tipo_arg, tipo2=esperado, operacion=nodo.nombre
                    )
            return tipo_retorno

        # Struct constructor
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
                    self.diag.reportar(
                        ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE,
                        self._token(getattr(arg, 'linea', 0), getattr(arg, 'columna', 0)),
                        tipo1=tipo_arg, tipo2=param.tipo, operacion=nodo.nombre
                    )
        return sim.tipo
