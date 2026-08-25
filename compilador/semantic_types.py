import re
from typing import Dict, Optional, Set

from compilador.ast_nodes import (
    Nodo, LiteralNumero, LiteralDecimal, LiteralCadena, LiteralBooleano,
    LiteralNulo, Identificador, OpBinaria, OpUnaria, LlamadaFuncion, ExprTensor,
    ArgumentoTransferido, ExprAsm, ExprObtenerDireccion, ExprDereferencia,
    ExprAccesoCampo, ExprCrearCanal, ExprRecibirCanal, ExprIndice,
    ExprPropagar, DefinicionFuncion, Parametro,
)
from compilador.diagnostics import ErrorCodes
from compilador.semantic_scope import _tipo_normalizado, _FUNCIONES_BUILTIN, AnalizadorSemanticoScope
# 2.4: Hindley-Milner (Manual 2 §8.2) — representación estructurada de tipos
# (TipoKind) y unificación con occurs check para validar argumentos de tipo.
from compilador.tipos import (
    ContadorTVar, UnificadorHM, tipo_desde_cadena, tipo_a_cadena,
    es_tipo_conocido, _dividir_argumentos,
)

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
        elif isinstance(nodo, LiteralNulo):
            # F1.2: literal nulo = puntero (paridad con el tratamiento previo
            # del identificador 'nulo' en _inferir_tipo).
            return 'puntero'
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

                # F3-10: centinela de cierre de canal (Manual 5 §4.2): comparar el
                # valor recibido (`ch ->`, tipo del elemento) con nulo.
                if nodo.operador in ('==', '!=') and (
                    isinstance(nodo.izquierdo, LiteralNulo) or isinstance(nodo.derecho, LiteralNulo)
                ):
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
            # D-2: normalizar la base de una instanciación de ADT genérico
            # (Resultado<entero,texto> -> Resultado) y usar sus campos concretos.
            inst_campos = None
            if '<' in base_tipo and base_tipo.endswith('>'):
                _b, _, _r = base_tipo.partition('<')
                args = tuple(a.strip() for a in _r[:-1].split(','))
                if hasattr(self, '_adt_parametros') and _b in self._adt_parametros:
                    params = self._adt_parametros[_b]
                    ctors = self._adt_constructores.get(_b, [])
                    if len(args) == len(params):
                        inst_campos = [Parametro(nombre='tag', tipo='entero')]
                        for c_nombre, c_tipo in ctors:
                            t_conc = args[params.index(c_tipo)] if c_tipo in params else c_tipo
                            inst_campos.append(Parametro(nombre=c_nombre, tipo=t_conc))
                base_tipo = _b
            struct = self._estructuras.get(base_tipo)
            if struct is None:
                self.diag.reportar(
                    ErrorCodes.ERR_SEM_ESTRUCTURA_NO_DEFINIDA,
                    self._token(nodo.linea, nodo.columna),
                    nombre=base_tipo
                )
                return None
            campos = inst_campos or struct.campos
            campo = next((c for c in campos if c.nombre == nodo.nombre_campo), None)
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
            # F3-10: el canal se tipa por su elemento (Manual 2 L144 Canal<T>,
            # Manual 5 §3 canales tipados). El elemento lo usa el receive `ch ->`.
            if getattr(nodo, 'tipo_contenido', None):
                return f'Canal<{nodo.tipo_contenido}>'
            return 'CanalConcurrencia*'
        elif isinstance(nodo, ExprRecibirCanal):
            # F3-10: el receive hereda el tipo del elemento del canal (Manual 5
            # §4.2 `valor = canal ->`). Fallback void* si el canal no esta tipado.
            tipo_canal = self._inferir_tipo(nodo.canal)
            if tipo_canal and tipo_canal.startswith('Canal<') and tipo_canal.endswith('>'):
                return tipo_canal[6:-1]
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
        elif isinstance(nodo, ExprPropagar):
            # D-6: `expr?` desempaqueta el campo del primer constructor (ok) del
            # ADT Resultado (Manual 3 §7 L331-342).
            tipo_inner = self._inferir_tipo(nodo.expresion)
            if not tipo_inner:
                return None
            base_tipo = tipo_inner.rstrip('*')
            # D-2: si es una instanciación de ADT genérico (Resultado<entero,texto>),
            # el campo ok tiene el tipo concreto sustituido (monomorfización).
            if '<' in base_tipo and base_tipo.endswith('>'):
                _b, _, _r = base_tipo.partition('<')
                args = tuple(a.strip() for a in _r[:-1].split(','))
                if hasattr(self, '_adt_parametros') and _b in self._adt_parametros:
                    params = self._adt_parametros[_b]
                    ctors = self._adt_constructores.get(_b, [])
                    if len(args) == len(params) and ctors:
                        c_nombre, c_tipo = ctors[0]
                        return args[params.index(c_tipo)] if c_tipo in params else c_tipo
                base_tipo = _b
            struct = self._estructuras.get(base_tipo)
            if struct is not None:
                for campo in struct.campos[1:]:  # saltar el campo tag
                    return campo.tipo
            return None
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
            # 2.4: Hindley-Milner (Manual 2 §8.2) — si la firma usa parámetros
            # de tipo (T/E) o instanciaciones de ADT genéricos, validar con
            # unificación de TVar y occurs check.
            if self._firma_generica(def_func):
                return self._inferir_llamada_hm(nodo, def_func)
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
            # Manual 2 L60: parámetros con -> transfieren ownership (move)
            for arg, param in zip(nodo.argumentos, def_func.parametros):
                if param.es_transferencia and isinstance(arg, Identificador):
                    if self.tabla.esta_movido(arg.nombre):
                        self.diag.reportar(
                            ErrorCodes.ERR_SEM_VAR_MOVIDA,
                            self._token(arg.linea, arg.columna),
                            nombre=arg.nombre
                        )
                    self.tabla.marcar_movido(arg.nombre)
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
                    # F3-7 (paridad nativo): `canal ->` devuelve void*; el canal
                    # es tipado en el Manual (Canal<int>, Manual 5 §3.2), así que
                    # el valor recibido se usa como su tipo base (cast implícito).
                    if tipo_arg == 'void*' and esperado in ('int', 'float', 'decimal'):
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

        # D-6/F1.2: constructores ADT (ok/err/algun/ninguno) — devuelven el ADT
        # (Manual 2 §2 L75; std/err.syn los documenta como nativos).
        if nodo.nombre in self._constructores_adt:
            for a in nodo.argumentos:
                self._inferir_tipo(a)
            return self._constructores_adt[nodo.nombre]

        if sim is None:
            self.diag.reportar(
                ErrorCodes.ERR_SEM_FUNC_NO_DEFINIDA,
                self._token(nodo.linea, nodo.columna),
                nombre=nodo.nombre
            )
            return None

        return sim.tipo

    # ------------------------------------------------------------------
    # 2.4: Hindley-Milner (Manual 2 §8.2) — TVar, unificación con occurs
    # check, validación de aridad de ADT y ERR_SEM_TYPE_AMBIGUOUS.
    # ------------------------------------------------------------------

    def _recolectar_tvars_firma(self, def_func: DefinicionFuncion) -> Set[str]:
        """Identifica los parámetros de tipo (T/E) de una firma de función.

        Regla (Manual 2 §8.2 + fixtures D-2): solo un identificador en
        mayúscula que aparece como TIPO DESNUDO en la firma (parámetro o
        retorno exacto, tras quitar &/*) es una variable de tipo TVar.
        Los identificadores dentro de `<...>` son SIEMPRE tipos concretos de
        una instanciación de ADT y deben ser conocidos (se validan en
        `_validar_aridad_instanciaciones`); no se promueven a TVar."""
        nombres: Set[str] = set()
        conocidos = set(self._estructuras) | set(self._adt_parametros)
        cadenas = [p.tipo for p in def_func.parametros] + [def_func.tipo_retorno]
        for c in cadenas:
            s = (c or '').strip()
            if s.startswith('&mut '):
                s = s[5:].strip()
            elif s.startswith('&'):
                s = s[1:].strip()
            if s.endswith('*') and s != 'void*':
                s = s[:-1].strip()
            if (s and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', s)
                    and s[0].isupper() and s not in conocidos
                    and not es_tipo_conocido(s, conocidos, self._adt_parametros)):
                nombres.add(s)
        return nombres

    def _firma_generica(self, def_func: DefinicionFuncion) -> bool:
        """True si la firma usa parámetros de tipo desnudos (T/E) — solo
        entonces la llamada requiere unificación Hindley-Milner. Las firmas
        con instanciaciones CONCRETAS de ADT (`Resultado<entero,texto>`) se
        validan en pasada 2 (`_validar_firma_funcion`) y se tratan como
        monomórficas (Opción A del Arquitecto, D-2)."""
        return bool(self._recolectar_tvars_firma(def_func))

    def _validar_aridad_instanciaciones(self, cadena: str, linea: int,
                                        tvars: Set[str]) -> None:
        """Valida las instanciaciones de ADT genéricos de un tipo (Manual 2
        §8.2/§4.2): aridad contra los parámetros declarados del ADT y
        argumentos de tipo conocidos. Recursivo para tipos anidados
        (p. ej. `Resultado<Resultado<int,texto>,float>`)."""
        if not cadena or not cadena.strip():
            return
        s = cadena.strip()
        if s.startswith('&mut ') or s.startswith('&'):
            self._validar_aridad_instanciaciones(
                s[5:].strip() if s.startswith('&mut ') else s[1:].strip(),
                linea, tvars)
            return
        if s.endswith('*') and s != 'void*':
            self._validar_aridad_instanciaciones(s[:-1].strip(), linea, tvars)
            return
        if '<' in s and s.endswith('>'):
            nombre = s.split('<')[0].strip()
            cuerpo = s[len(nombre) + 1:-1]
            args = _dividir_argumentos(cuerpo)
            if nombre in self._adt_parametros:
                esperados = len(self._adt_parametros[nombre])
                if len(args) != esperados:
                    self.diag.reportar(
                        ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE,
                        self._token(linea, 0),
                        tipo1=s, tipo2=f"{nombre} con {esperados} argumento(s) de tipo",
                        operacion='instanciacion'
                    )
            elif not es_tipo_conocido(nombre, set(self._estructuras),
                                      self._adt_parametros):
                # Base no registrada (typo, p. ej. 'Resultados' en vez de
                # 'Resultado'): la instanciación completa es inválida.
                self.diag.reportar(
                    ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE,
                    self._token(linea, 0),
                    tipo1=nombre, tipo2='tipo conocido',
                    operacion='instanciacion'
                )
            for a in args:
                if a not in tvars and not es_tipo_conocido(
                        a, set(self._estructuras), self._adt_parametros):
                    self.diag.reportar(
                        ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE,
                        self._token(linea, 0),
                        tipo1=a, tipo2='tipo conocido',
                        operacion='instanciacion'
                    )
                self._validar_aridad_instanciaciones(a, linea, tvars)

    def _validar_firma_funcion(self, def_func: DefinicionFuncion) -> None:
        """2.4: valida la firma de una función (parámetros y retorno): aridad
        de las instanciaciones de ADT y argumentos de tipo conocidos."""
        tvars = self._recolectar_tvars_firma(def_func)
        cadenas = [p.tipo for p in def_func.parametros] + [def_func.tipo_retorno]
        for c in cadenas:
            self._validar_aridad_instanciaciones(c, def_func.linea, tvars)

    def _validar_contratos_tipos(self, def_func: DefinicionFuncion) -> None:
        """Manual 2 §5.1: valida que las expresiones de requiere/garantiza
        sean booleanas. Se ejecuta en modo normal (no solo --safe)."""
        from compilador.verificador_formal import _es_expresion_booleana_valida
        for expr in def_func.requiere:
            if not _es_expresion_booleana_valida(expr):
                self.diag.reportar(
                    ErrorCodes.ERR_VER_CONTRATO_INVALIDO,
                    self._token(getattr(expr, 'linea', def_func.linea),
                                getattr(expr, 'columna', def_func.columna)),
                    nombre=def_func.nombre,
                    detalle="Expresión inválida en cláusula 'requiere': debe ser una condición lógica",
                )
        for expr in def_func.garantiza:
            if not _es_expresion_booleana_valida(expr):
                self.diag.reportar(
                    ErrorCodes.ERR_VER_CONTRATO_INVALIDO,
                    self._token(getattr(expr, 'linea', def_func.linea),
                                getattr(expr, 'columna', def_func.columna)),
                    nombre=def_func.nombre,
                    detalle="Expresión inválida en cláusula 'garantiza': debe ser una condición lógica",
                )

    def _inferir_llamada_hm(self, nodo: LlamadaFuncion,
                            def_func: DefinicionFuncion) -> Optional[str]:
        """2.4: llamada a función con parámetros de tipo (T/E) o ADT
        genérico — algoritmo W: TVar frescos por llamada, unificación de los
        argumentos reales contra los parámetros (con occurs check) e
        instanciación del tipo de retorno. Si el retorno queda con un TVar
        sin resolver se emite ERR_SEM_TYPE_AMBIGUOUS (Manual 2 §8.2)."""
        tvars = self._recolectar_tvars_firma(def_func)
        contador = ContadorTVar()
        uf = UnificadorHM()
        tvar_cache: Dict[str, int] = {}  # mismo nombre -> mismo TVar (algoritmo W)
        # La firma ya se validó en pasada 2 (_analizar_funcion ->
        # _validar_firma_funcion); no repetir aquí para evitar duplicados.
        conocidos = set(self._estructuras) | set(self._adt_parametros)
        if len(nodo.argumentos) != len(def_func.parametros):
            self.diag.reportar(
                ErrorCodes.ERR_SEM_ARGUMENTOS_INVALIDOS,
                self._token(nodo.linea, nodo.columna),
                nombre=nodo.nombre, esperados=len(def_func.parametros)
            )
            return self._instanciar_retorno(def_func, uf, contador, tvars,
                                            tvar_cache, conocidos,
                                            nodo.linea, nodo.columna)
        for arg, param in zip(nodo.argumentos, def_func.parametros):
            tipo_arg = self._inferir_tipo(arg)
            if tipo_arg is None:
                continue
            tipo_param = tipo_desde_cadena(param.tipo, contador, tvars,
                                           tvar_cache, conocidos)
            if tipo_param is None:
                continue
            tipo_arg_t = tipo_desde_cadena(_tipo_normalizado(tipo_arg),
                                           contador, tvars, tvar_cache,
                                           conocidos)
            if not uf.unificar(tipo_arg_t, tipo_param):
                # Exenciones de compatibilidad del flujo clásico (ABI void*,
                # concatenación texto) — paridad con _inferir_tipo_llamada.
                norm_param = _tipo_normalizado(param.tipo)
                norm_arg = _tipo_normalizado(tipo_arg)
                exento = (
                    (norm_param == 'void*' and norm_arg in ('int', 'float'))
                    or (norm_param == 'void*' and norm_arg in ('texto', 'CadenaSegura'))
                    or (norm_param == 'texto' and norm_arg in ('int', 'float')
                        and nodo.nombre == 'concat')
                )
                if not exento:
                    self.diag.reportar(
                        ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE,
                        self._token(getattr(arg, 'linea', nodo.linea),
                                    getattr(arg, 'columna', 0)),
                        tipo1=tipo_arg, tipo2=param.tipo, operacion=nodo.nombre
                    )
        return self._instanciar_retorno(def_func, uf, contador, tvars,
                                        tvar_cache, conocidos,
                                        nodo.linea, nodo.columna)

    def _instanciar_retorno(self, def_func: DefinicionFuncion, uf: UnificadorHM,
                            contador: ContadorTVar, tvars: Set[str],
                            tvar_cache: Dict[str, int],
                            conocidos: Set[str],
                            linea: int = 0, columna: int = 0) -> Optional[str]:
        """Instancia el tipo de retorno con la sustitución HM acumulada. Para
        firmas concretas (sin TVar) se preserva la cadena original; si un TVar
        queda sin resolver se reporta ERR_SEM_TYPE_AMBIGUOUS en el sitio de
        llamada (la expresión ambigua, Manual 2 §8.2)."""
        if not tvars:
            return def_func.tipo_retorno
        ret_t = tipo_desde_cadena(def_func.tipo_retorno, contador, tvars,
                                  tvar_cache, conocidos)
        inst = uf.instanciar(ret_t)
        cadena = tipo_a_cadena(inst)
        if 'TVar(' in cadena:
            self.diag.reportar(
                ErrorCodes.ERR_SEM_TYPE_AMBIGUOUS,
                self._token(linea or def_func.linea, columna or def_func.columna),
                tipo=cadena
            )
            return None
        return cadena
