# ============================================================
# puente_canonico.py — SemNodo[] plano → AST tipado del S1 (R90)
# ============================================================
# Convierte el JSON plano que emite syq_frontend.exe
# (syquex/syq_json.syn, esquema "syquex_flat":"2") al Programa
# tipado de compilador/ast_nodes que consume el pipeline S1
# (pipeline.compilar_desde_canonico, Manual 1 §3.1: backend
# compartido tras el traductor; Manual 6 §1.2 ABI v1; Manual 3
# §11.1 mapeo de nodos).
#
# Campos del registro plano:
#   [0] tipo  [1] linea [2] col  [3] valor_int
#   [4] hijo_izq  [5] hijo_der  [6] hermano  [7] reservado
#   [8] span1(bytes|null)  [9] span2(bytes|null)
#
# Nodos sin equivalente en el AST tipado actual levantan
# PuenteError con el id y el nombre canónico (fail-fast, sin
# pérdida silenciosa): INTENTO(54), LISTA_LIT(55), MAPA_LIT(56),
# PARA_EN(57) — cableado backend pendiente, registrado como
# hallazgo H-R90-1.
# ============================================================

import json
from typing import Optional

from compilador.ast_nodes import (
    Programa, Parametro,
    DefinicionFuncion, DefinicionEstructura, DeclaracionExterna,
    DeclaracionExport, DeclaracionTipo, ConstructorTipo, StmtConstante,
    SentenciaSi, SentenciaMientras, SentenciaLanzar, SentenciaEscuchar,
    SentenciaRecuperar, SentenciaRetornar, SentenciaExpr, SentenciaRomper,
    SentenciaSiguiente, SentenciaDelegar, SentenciaPara,
    DeclaracionVariable, AsignacionVariable,
    AsignacionCampo, OpBinaria, OpUnaria, LlamadaFuncion, Identificador,
    LiteralNumero, LiteralDecimal, LiteralCadena, LiteralBooleano,
    LiteralNulo, ExprAccesoCampo, ExprIndice, ExprPropagar,
    ExprObtenerDireccion, ExprCrearCanal, SentenciaEnviarCanal,
    ExprRecibirCanal,
    ArgumentoTransferido, NodoCoincidir, NodoCaso,
)

SCHEMA = "2"

NOMBRE_NODO = {
    1: "PROGRAMA", 2: "FUNCION", 3: "SI", 4: "MIENTRAS", 5: "RETORNAR",
    6: "EXPR", 7: "ASIGNACION", 8: "IDENTIFICADOR", 9: "NUMERO",
    10: "DECIMAL", 11: "CADENA_LIT", 12: "BINARIA", 13: "UNARIA",
    14: "LLAMADA", 15: "PARAMETRO", 16: "ESTRUCTURA", 17: "IMPORTAR",
    18: "LANZAR", 19: "ESCUCHAR", 20: "ROMPER", 21: "SIGUIENTE",
    22: "BOOLEANO", 23: "CONSTANTE", 24: "INSEGURO", 25: "IMPORTAR_C",
    26: "EXTERNO", 27: "RECUPERAR", 28: "TENSOR", 29: "INDICE",
    30: "TRANSFERIDO", 31: "ACCESO_CAMPO", 32: "ASIGNACION_CAMPO",
    33: "PARRAFO", 34: "DECLARACION", 35: "LOG", 36: "PUNTERO",
    37: "DEREF", 38: "COINCIDIR", 39: "CASO",
    40: "ASM", 41: "CANAL_CREAR", 42: "ENVIAR_CANAL", 43: "RECIBIR_CANAL",
    44: "VACIO", 45: "PARA", 46: "CONTRATO", 47: "NULO", 48: "LET",
    49: "DELEGAR", 50: "EXPORT", 51: "DECLARACION_TIPO", 52: "CONSTRUCTOR",
    53: "PROPAGAR", 54: "INTENTO", 55: "LISTA_LIT", 56: "MAPA_LIT",
    57: "PARA_EN", 58: "BLOQUE_SQ",
}

# Categorías de nodos no mapeados directamente en _nodo().
# - NO_SOPORTADOS: backend pendiente (ME-4/5/8/Fase 23+/Fase 24)
# - ELIMINADOS_POR_TRADUCTOR: nunca llegan al puente (traductor.syn los elimina)
# - FUSIONADOS: manejados inline dentro de otro nodo (ej. CONTRATO en FUNCION)
# - NO_PRODUCIDOS: el frontend SyQuex no genera estos tipos (runtime nativo sí)
# - PENDIENTE_BACKEND: feature futura del roadmap
# cumple Manual 3 11.1: todos los NODO_* estan categorizados (sin nodo sin categoria)
NO_SOPORTADOS = {
    54: "INTENTO (backend pendiente, hallazgo H-R90-1)",
    55: "LISTA_LIT (backend Fase 24 lib/lista)",
    56: "MAPA_LIT (backend Fase 24 lib/mapa)",
    57: "PARA_EN (backend pendiente, hallazgo H-R90-1)",
}

ELIMINADOS_POR_TRADUCTOR = {
    58: "BLOQUE_SQ — desenrollado por traductor.sin::trad_stmts (líneas 458-472)",
}

FUSIONADOS = {
    46: "CONTRATO — fusionado en slot extra [7] de NODO_FUNCION (puente línea 244)",
    32: "ASIGNACION_CAMPO — manejado vía ASIGNACION(7)+ACCESO_CAMPO(31) (puente línea 274)",
}

NO_PRODUCIDOS = {
    35: "LOG — 'log(...)' se parsea como NODO_LLAMADA (Manual 3 §L303/L378)",
    25: "IMPORTAR_C — import sintaxis C no producida por SyQuex frontend",
    24: "INSEGURO — 'inseguro:' es bloque, no nodo (Manual 3 §3 L106)",
    37: "DEREF — '*p' usa T_POR como binaria/unaria, no NODO_DEREF",
    45: "PARA — 'para i=a; cond; paso' desugareado a MIENTRAS (parser.syn:861)",
    33: "PARRAFO — nodo runtime nativo, no producido por SyQuex",
    44: "VACIO — tipo nativo, no producido como nodo por SyQuex",
}

PENDIENTE_BACKEND = {
    27: "RECUPERAR — recovery handler (try/catch completo, pendiente ME-8)",
    28: "TENSOR — tipo tensor (Fase 4, Manual 3 §4.3)",
    40: "ASM — bloque asm (Manual 3 §3 L106)",
    41: "CANAL_CREAR — ExprCrearCanal (channel runtime, pendiente backend nativo)",
    42: "ENVIAR_CANAL — SentenciaEnviarCanal (channel runtime, pendiente backend nativo)",
    43: "RECIBIR_CANAL — ExprRecibirCanal (channel runtime, pendiente backend nativo)",
}

# Códigos de operador de syquex/expr.syn (fallback cuando el lexema no
# quedó en slot1, p. ej. binarias del desugar para-rango).
CODIGO_OPS = {
    100: "y", 101: "o",
    200: ">", 201: "<", 202: "==", 203: "!=", 204: "<=", 205: ">=",
    300: "+", 301: "-",
    400: "*", 401: "/", 402: "%",
}


class PuenteError(Exception):
    pass


def cargar_flat(ruta_json: str) -> dict:
    with open(ruta_json, "r", encoding="utf-8") as f:
        flat = json.load(f)
    if flat.get("syquex_flat") != SCHEMA:
        raise PuenteError(
            f"esquema syquex_flat={flat.get('syquex_flat')!r} "
            f"no soportado (esperado {SCHEMA!r})")
    return flat


class _Puente:
    def __init__(self, flat: dict):
        self.nodos = flat["nodos"]
        self._build_contexto()

    def _build_contexto(self):
        """Pre-pase H-R90-5: construye mapas struct→metodos y var→tipo
        para el lowering de call-sites OOP (Manual 6 §1.3: el traductor
        hoistea metodos como NODO_FUNCION con nombre decorado
        'Struct_method'; el puente resuelve el tipo del receptor y
        genera LlamadaFuncion con self inyectado)."""
        self._struct_nombres: set = set()
        self._struct_metodos: dict = {}   # struct -> {method_name -> func_name}
        # H-R90-5b: métodos builtin del runtime para tipos no-struct (Manual 3 §5.1).
        # obj.metodo() → funcion_builtin(obj). Registro desde runtime/core/*.syn
        # y _G_rt_builtin_fns (nucleo/analizador_semantico.syn L393).
        self._builtin_metodos: dict = {}  # tipo -> {method_name -> func_name}
        self._struct_ctores: dict = {}    # struct -> "__init__" func name (ME-9)
        self._struct_campos: dict = {}   # struct -> {field_name -> field_type} (ME-10)
        self._var_tipo: dict = {}       # var_name -> Synapse type
        self._func_retorno: dict = {}   # func_name -> return type
        # H-R90-5c: funciones builtin del runtime (nucleo/analizador_semantico.syn
        # L387-420) — se registran para inferir tipos de retorno desde funciones
        # importadas (importar std.io) que no aparecen como nodo FUNCION.
        # (Manual 3 §7: funciones como abrir→Canal, leer→texto, etc.)
        _BUILTIN_RET: dict = {
            'abrir': 'Canal', 'leer': 'texto', 'leer_linea': 'texto',
            'escribir': 'nulo', 'escribir_linea': 'nulo', 'cerrar_archivo': 'nulo',
            'cerrar': 'nulo', 'concat': 'texto', 'entero_a_texto': 'texto',
            'decimal_a_texto': 'texto', 'texto_a_entero': 'entero',
            'texto_a_decimal': 'decimal', 'subcadena': 'texto',
            'salir': 'nulo', '_argc': 'entero', '_argv': 'texto',
            'reserva': 'tensor', 'libera': 'nulo', 'crear_tensor': 'tensor',
            'suma_tensor': 'tensor', 'producto_punto': 'tensor', 'suma': 'tensor',
            'producto': 'tensor', 'relu': 'tensor', 'len': 'entero',
            'empieza_con': 'entero',
        }
        self._func_retorno.update(_BUILTIN_RET)
        n = self.nodos
        for i, nodo in enumerate(n):
            if len(nodo) < 10:
                continue
            t = nodo[0]
            if t == 16:   # ESTRUCTURA
                nombre = self.txt(i)
                if nombre:
                    self._struct_nombres.add(nombre)
                    self._struct_metodos[nombre] = {}
                    self._struct_ctores[nombre] = None
                    # ME-10: registrar campos del struct (Manual 3 §6.2)
                    self._struct_campos[nombre] = {}
                    for c in self.cadena_ids(nodo[4]):
                        cnombre = self.txt(c)
                        ctipo = self.txt2(c)
                        if cnombre and ctipo:
                            self._struct_campos[nombre][cnombre] = ctipo
            elif t == 2:  # FUNCION
                nombre = self.txt(i)
                if not nombre:
                    continue
                vi = self.nodos[i][3]   # valor_int: 0 = libre, >0 = método/ctor (índice del struct)
                if vi > 0 and self.tipo(vi) == 16:  # ESTRUCTURA marcado (ME-9)
                    struct = self.txt(vi)
                    if struct in self._struct_nombres:
                        if nombre == "__init__":
                            self._struct_ctores[struct] = nombre
                        else:
                            method = nombre[len(struct) + 1:] if nombre.startswith(struct + "_") else nombre
                            self._struct_metodos[struct][method] = nombre
                elif vi == 0:
                    # Compatibilidad: funciones con valor_int=0 que usan
                    # decoración "Struct_method" (fixture de test heredado).
                    # Probamos prefijos de struct mas largos (ME-9: handles _).
                    for struct in sorted(self._struct_nombres, key=len, reverse=True):
                        prefixo = struct + "_"
                        if nombre.startswith(prefixo):
                            method = nombre[len(prefixo):]
                            if struct not in self._struct_metodos:
                                self._struct_metodos[struct] = {}
                            self._struct_metodos[struct][method] = nombre
                            break
                # ME-10: poblar _var_tipo desde parámetros de función
                # (Manual 3 §6.2: param.metodo() requiere tipo del param).
                for p in self.cadena_ids(nodo[4]):
                    pnombre = self.txt(p)
                    ptipo = self.txt2(p)
                    if pnombre and ptipo:
                        self._var_tipo[pnombre] = ptipo
                ret = self.txt2(i)
                if ret:
                    self._func_retorno[nombre] = ret
            elif t in (34, 48):  # DECLARACION / LET
                var = self.txt(i)
                t2 = self.txt2(i)
                if var and t2:
                    self._var_tipo[var] = t2
                elif var and i + 1 < len(n) and n[i][5] > 0:
                    # inferir tipo del constructor: let p = Punto(3)
                    arg_idx = n[i][5]
                    if arg_idx < len(n) and n[arg_idx][0] == 14:  # LLAMADA
                        ctor = self.txt(arg_idx)
                        if ctor in self._struct_nombres:
                            self._var_tipo[var] = ctor
                        # ME-10: inferir tipo desde retorno de función
                        # (Manual 3 §6.3: x = factory() → tipo retorno)
                        elif ctor in self._func_retorno:
                            ret_tipo = self._func_retorno[ctor]
                            if ret_tipo:
                                self._var_tipo[var] = ret_tipo

        # H-R90-5b: métodos builtin para tipos primitivos y Canal
        # (Manual 3 §8.1: id.texto(), canal.leer()).
        # obj.metodo() → funcion_builtin(obj)
        self._builtin_metodos = {
            'Canal': {'leer': 'leer'},
            'entero': {'texto': 'entero_a_texto'},
            'decimal': {'texto': 'decimal_a_texto'},
            'Lista': {'len': 'len'},
        }

    # ---- helpers de registro ----
    def txt(self, i: int) -> str:
        campo = self.nodos[i][8]
        return "" if campo is None else bytes(campo).decode("utf-8")

    def txt2(self, i: int) -> str:
        campo = self.nodos[i][9]
        return "" if campo is None else bytes(campo).decode("utf-8")

    def tipo(self, i: int) -> int:
        return self.nodos[i][0]

    def _tipo_objeto(self, idx: int) -> Optional[str]:
        """Resuelve el tipo Synapse de una expresión base (H-R90-5).
        Identificador: lookup en _var_tipo. ACCESO_CAMPO: lookup de campo
        en _estructuras. LLAMADA a struct: el propio struct. None si
        no resoluble (fallara al final en el call-site lowering)."""
        if idx <= 0 or idx >= len(self.nodos):
            return None
        t = self.nodos[idx][0]
        if t == 8:   # IDENTIFICADOR
            tipo = self._var_tipo.get(self.txt(idx))
            # H-R90-15: normalizar tipo genérico (Lista<decimal> → Lista)
            if tipo and '<' in tipo:
                return tipo.split('<')[0].strip()
            return tipo
        if t == 31:   # ACCESO_CAMPO
            nombre_campo = self.txt(idx)
            obj_idx = self.nodos[idx][4]
            obj_tipo = self._tipo_objeto(obj_idx)
            if obj_tipo and obj_tipo in self._struct_campos:
                campos = self._struct_campos[obj_tipo]
                return campos.get(nombre_campo)
            return None
        if t == 14:   # LLAMADA (posible constructor)
            nombre = self.txt(idx)
            if nombre in self._struct_nombres:
                return nombre
            return self._func_retorno.get(nombre)
        return None

    # ---- cadenas por hermano ([6]) ----
    def cadena(self, idx: int):
        out = []
        visitados = set()
        while idx > 0:
            if idx >= len(self.nodos):
                raise PuenteError(f"indice fuera de rango en cadena: {idx}")
            if idx in visitados:
                raise PuenteError(f"bucle detectado en cadena de hermanos: {idx}")
            visitados.add(idx)
            n = self._nodo(idx)
            if n is not None:
                out.append(n)
            idx = self.nodos[idx][6]
        return out

    def _parametro(self, i: int) -> Parametro:
        nombre = self.txt(i)
        tipo = self.txt2(i) or "entero"
        valor_default = None
        # H-R90-13: valor por defecto en params (n[5]=hijo_der idx default value)
        der = self.nodos[i][5]
        if der > 0 and der < len(self.nodos):
            valor_default = self._nodo(der)
        return Parametro(nombre=nombre, tipo=tipo, valor_default=valor_default)

    # ---- despacho principal ----
    def _nodo(self, i: int):
        n = self.nodos[i]
        t, vi = n[0], n[3]
        izq, der, extra = n[4], n[5], n[7]
        lin, col = n[1], n[2]

        def con(nodo):
            nodo.linea = lin
            nodo.columna = col
            return nodo

        if t == 1:   # PROGRAMA
            prog = Programa(sentencias=self.cadena(izq))
            return prog
        if t == 2:   # FUNCION
            req, gar = [], []
            if extra > 0 and self.tipo(extra) == 46:   # CONTRATO fusionado
                req = self.cadena(self.nodos[extra][4])
                gar = self.cadena(self.nodos[extra][5])
            # M3 §3 L91: [ "->" tipo ] es OPCIONAL en metodo/crear; sin
            # flecha el procedimiento retorna 'nulo' (convención del
            # parser S1, que exige anotación explícita y mapea a void).
            return con(DefinicionFuncion(
                nombre=self.txt(i),
                parametros=[self._parametro(p) for p in self.cadena_ids(izq)],
                tipo_retorno=self.txt2(i) or "nulo",
                requiere=req,
                garantiza=gar,
                cuerpo=self.cadena(der)))
        if t == 3:   # SI
            sino = self.cadena(extra) if extra > 0 else None
            return con(SentenciaSi(condicion=self._nodo(izq),
                                   cuerpo=self.cadena(der),
                                   cuerpo_sino=sino))
        if t == 4:   # MIENTRAS (incluye desugar para-rango R87)
            return con(SentenciaMientras(condicion=self._nodo(izq),
                                         cuerpo=self.cadena(der)))
        if t == 5:   # RETORNAR
            return con(SentenciaRetornar(expr=self._nodo_opt(izq),
                                         es_transferencia=bool(vi)))
        if t == 6:   # EXPR
            return con(SentenciaExpr(expr=self._nodo(izq)))
        if t == 7:   # ASIGNACION (despacha por forma del LHS)
            destino = izq
            dt = self.tipo(destino)
            val = self._nodo(der)
            if dt == 31:   # ACCESO_CAMPO
                return con(AsignacionCampo(
                    objeto=self._nodo(self.nodos[destino][4]),
                    nombre_campo=self.txt(destino),
                    expresion=val))
            if dt == 29:   # INDICE
                raise PuenteError(
                    "asignacion indexada (a[i] = ...) sin clase en el AST "
                    "tipado S1 (H-R90-2)")
            return con(AsignacionVariable(nombre=self.txt(destino),
                                          expresion=val))
        if t == 8:
            if der > 0:
                # Tras el fix R90 del postfix, una llamada sobre
                # identificador es NODO_LLAMADA; si esto aparece, el parser
                # regresó a la forma antigua — fallar, no perder args.
                raise PuenteError(
                    "IDENTIFICADOR con argumentos (llamada sin NODO_LLAMADA) "
                    "— regression del parser Syquex")
            return con(Identificador(nombre=self.txt(i)))
        if t == 9:
            return con(LiteralNumero(valor=int(self.txt(i))))
        if t == 10:
            return con(LiteralDecimal(valor=float(self.txt(i))))
        if t == 11:
            return con(LiteralCadena(valor=self.txt(i)))
        if t == 12:   # BINARIA
            op = self.txt(i) or CODIGO_OPS.get(vi, "?")
            return con(OpBinaria(izquierdo=self._nodo(izq), operador=op,
                                 derecho=self._nodo(der)))
        if t == 13:   # UNARIA
            return con(OpUnaria(operador=self.txt(i) or "-",
                                expr=self._nodo(izq)))
        if t == 14:   # LLAMADA (args en hijo_der — convención sq_args)
            nombre = self.txt(i)
            args = self.cadena(der)
            if nombre == "Canal":
                # H-R90-7: Canal<T>(N) → ExprCrearCanal
                # txt2(i) tiene el span genérico <T> (ej. "<texto>" → "texto")
                tipo_contenido = self.txt2(i).strip().strip("<>")
                capacidad = args[0] if args else None
                return con(ExprCrearCanal(tipo_contenido=tipo_contenido,
                                          capacidad=capacidad))
            return con(LlamadaFuncion(nombre=nombre,
                                      argumentos=args))
        if t == 15:   # PARAMETRO suelto (miembro de estructura)
            return con(_campo_como_parametro(self, i))
        if t == 16:   # ESTRUCTURA
            campos = [_campo_como_parametro(self, c)
                      for c in self.cadena_ids(izq)]
            return con(DefinicionEstructura(nombre=self.txt(i),
                                            campos=campos))
        if t == 17:
            from compilador.ast_nodes import SentenciaImportar
            return con(SentenciaImportar(ruta=self.txt(i)))
        if t == 18:
            return con(SentenciaLanzar(llamada=self._nodo(izq)))
        if t == 19:
            return con(SentenciaEscuchar(canal=self._nodo(izq),
                                         cuerpo=self.cadena(der)))
        if t == 20:
            return con(SentenciaRomper())
        if t == 21:
            return con(SentenciaSiguiente())
        if t == 22:
            return con(LiteralBooleano(valor=bool(vi)))
        if t == 23:   # CONSTANTE
            return con(StmtConstante(nombre=self.txt(i), tipo='',
                                     valor=self._nodo_opt(der)))
        if t == 26:   # EXTERNO (vi: 0 funcion / 1 estructura / 2 constante)
            if vi == 0:
                return con(DeclaracionExterna(
                    nombre=self.txt(i),
                    parametros=[self._parametro(p)
                                for p in self.cadena_ids(izq)],
                    tipo_retorno=self.txt2(i)))
            if vi == 1:   # externo estructura (H-R90-3)
                return con(DeclaracionExterna(
                    nombre=self.txt(i),
                    parametros=[],
                    tipo_retorno="__extern_struct"))
            if vi == 2:
                return con(StmtConstante(nombre=self.txt(i), tipo='',
                                         valor=self._nodo_opt(der)))
            raise PuenteError("externo sin tipo reconocido (vi no 0/1/2)")
        if t == 29:
            return con(ExprIndice(expr=self._nodo(izq),
                                  indice=self._nodo(der)))
        if t == 30:
            return con(ArgumentoTransferido(expr=self._nodo(izq)))
        if t == 31:
            if vi == 1 or der > 0:
                # H-R90-5: lowering de method call obj.metodo(args).
                # vi==1 (marcador R91) distingue la llamada del acceso
                # simple incluso con argumentos vacíos (hijo_der=0).
                obj = self._nodo(izq)
                obj_tipo = self._tipo_objeto(izq)
                nombre_metodo = self.txt(i)  # e.g. "leer", "texto"
                # 1. Structs normales (definidos por el usuario)
                if obj_tipo and obj_tipo in self._struct_metodos:
                    metodos = self._struct_metodos[obj_tipo]
                    func_decorada = metodos.get(nombre_metodo)
                    if func_decorada:
                        args = [obj] + self.cadena(der)
                        return con(LlamadaFuncion(
                            nombre=func_decorada,
                            argumentos=args))
                    raise PuenteError(
                        f"metodo '{nombre_metodo}' no encontrado en "
                        f"estructura '{obj_tipo}' (H-R90-5)")
                # 2. Builtins de tipos primitivos / Canal (H-R90-5b)
                if obj_tipo and obj_tipo in self._builtin_metodos:
                    metodos = self._builtin_metodos[obj_tipo]
                    func_builtin = metodos.get(nombre_metodo)
                    if func_builtin:
                        args = [obj] + self.cadena(der)
                        return con(LlamadaFuncion(
                            nombre=func_builtin,
                            argumentos=args))
                    raise PuenteError(
                        f"metodo '{nombre_metodo}' no encontrado en tipo "
                        f"de receptor '{obj_tipo}' (H-R90-5)")
                # 3. Receptor primitivo directo (tipo conocido del runtime)
                if obj_tipo and obj_tipo in self._builtin_metodos and nombre_metodo in self._builtin_metodos[obj_tipo]:
                    func_builtin = self._builtin_metodos[obj_tipo][nombre_metodo]
                    args = [obj] + self.cadena(der)
                    return con(LlamadaFuncion(
                        nombre=func_builtin,
                        argumentos=args))
                raise PuenteError(
                    "llamada a metodo (obj.metodo(args)) sin tipo de "
                    "receptor resoluble — pendiente H-R90-5")
            return con(ExprAccesoCampo(objeto=self._nodo(izq),
                                       nombre_campo=self.txt(i)))
        if t == 36:   # PUNTERO (&T / &mut T — FFI, Manual 3 §9.1/§9.3)
            # D-F22-SEM: valor_int bit 0 = es_mutable (0=& / 1=&mut).
            # El parser SyQuex establece vi=1 cuando ve &mut.
            return con(ExprObtenerDireccion(
                expr=self._nodo(izq),
                es_mutable=bool(vi & 1)))
        if t in (34, 48):   # DECLARACION / LET
            return con(DeclaracionVariable(nombre=self.txt(i),
                                           tipo=self.txt2(i),
                                           expresion=self._nodo_opt(der)))
        if t == 38:   # COINCIDIR
            casos = []
            for c in self.cadena_ids(der):
                # H-R90-3: el traductor (traductor.syn:547-554) reconstruye el
                # patrón como span1 (slot1) y almacena el CUERPO en hijo_izq
                # (índice 4), no en hijo_der — el puente lo lee de hijo_izq.
                caso = NodoCaso(patron=self.txt(c),
                                cuerpo=self.cadena(self.nodos[c][4]))
                caso.linea = self.nodos[c][1]
                casos.append(caso)
            return con(NodoCoincidir(expresion=self._nodo(izq), casos=casos))
        if t == 47:
            return con(LiteralNulo())
        if t == 49:
            return con(SentenciaDelegar(expresion=self._nodo(izq)))
        if t == 50:   # EXPORT
            return con(DeclaracionExport(destino=self.txt(i),
                                         funcion=self._nodo(izq)))
        if t == 51:   # DECLARACION_TIPO (alias o ADT enumeracion)
            ctors = [ConstructorTipo(nombre=self.txt(c), tipos=[])
                     for c in self.cadena_ids(der)] if vi == 1 else []
            alias = self.txt2(i)
            return con(DeclaracionTipo(nombre=self.txt(i),
                                       tipo_base=alias,
                                       constructores=ctors))
        if t == 52:   # CONSTRUCTOR suelto (fuera de DECL_TIPO)
            return con(ConstructorTipo(nombre=self.txt(i), tipos=[]))
        if t == 53:
            return con(ExprPropagar(expresion=self._nodo(izq)))
        if t == 41:   # CANAL_CREAR (producido directamente solo si el frontend lo genera)
            tipo_contenido = self.txt2(i).strip().strip("<>")
            return con(ExprCrearCanal(tipo_contenido=tipo_contenido,
                                      capacidad=self._nodo_opt(izq)))
        if t == 42:   # ENVIAR_CANAL — canal <- valor
            return con(SentenciaEnviarCanal(
                canal=self._nodo(izq),
                valor=self._nodo(der)))
        if t == 43:   # RECIBIR_CANAL — canal ->
            return con(ExprRecibirCanal(
                canal=self._nodo(izq)))
        # 54 INTENTO / 55 LISTA_LIT / 57 PARA_EN: backend pendiente (H-R90-1,
        # Manual 1 §3.1 — sin equivalente en el AST tipado S1). Se rechazan
        # fail-fast en el chequeo NO_SOPORTADOS al final de _nodo.
        if t in (54, 55, 57):
            pass  # cae al chequeo NO_SOPORTADOS

        if t in NO_SOPORTADOS:
            raise PuenteError(
                f"NODO_{NO_SOPORTADOS[t]} — sin equivalente en el AST "
                f"tipado S1 ({NO_SOPORTADOS[t].split('(', 1)[-1]}")
        if t in ELIMINADOS_POR_TRADUCTOR:
            raise PuenteError(
                f"NODO_{ELIMINADOS_POR_TRADUCTOR[t]} — debería haber sido "
                f"eliminado por el traductor antes de llegar al puente")
        if t in FUSIONADOS:
            raise PuenteError(
                f"NODO_{FUSIONADOS[t]} — manejado inline, no debe aparecer individualmente")
        if t in NO_PRODUCIDOS:
            raise PuenteError(
                f"NODO_{NO_PRODUCIDOS[t]} — el frontend SyQuex no genera este nodo")
        if t in PENDIENTE_BACKEND:
            raise PuenteError(
                f"NODO_{PENDIENTE_BACKEND[t]} — mapeado pero backend pendiente")
        nombre = NOMBRE_NODO.get(t, f"id {t}")
        raise PuenteError(f"nodo canonico no mapeado en el puente: {nombre}")

    def _nodo_opt(self, idx: int):
        return self._nodo(idx) if idx > 0 else None

    def cadena_ids(self, idx: int):
        out = []
        visitados = set()
        while idx > 0:
            if idx in visitados:
                raise PuenteError(f"bucle detectado en cadena de params: {idx}")
            visitados.add(idx)
            out.append(idx)
            idx = self.nodos[idx][6]
        return out


def _campo_como_parametro(puente: "_Puente", i: int) -> Parametro:
    """Campo de estructura (PARAMETRO fuente) → Parametro tipado."""
    return Parametro(nombre=puente.txt(i), tipo=puente.txt2(i) or "entero")


def plano_a_programa(flat: dict) -> Programa:
    if flat.get("syquex_flat") != SCHEMA:
        raise PuenteError(
            f"esquema syquex_flat={flat.get('syquex_flat')!r} "
            f"no soportado (esperado {SCHEMA!r})")
    p = _Puente(flat)
    prog = p._nodo(flat["raiz"])
    if not isinstance(prog, Programa):
        raise PuenteError("la raiz del flat no es PROGRAMA")
    # ME-R90-8: si no hay funcion principal(), inyectar un main stub
    # (Manual 1 §3.1: todo programa ejecutable requiere punto de entrada).
    # NOTA: H-R90-8b inyecta principal en el .syq source ANTES del runtime S1;
    # por lo que el plano normalmente ya incluye principal. Este stub es fallback.
    tiene_principal = any(
        isinstance(s, DefinicionFuncion) and s.nombre == 'principal'
        for s in prog.sentencias)
    if not tiene_principal:
        # ME-R90-8: main stub con tipo_retorno 'nulo' y cuerpo mínimo (Manual 1 §3.1).
        # El runtime S1 requiere cuerpo no vacío (R10: SYQ_JSON_ERROR=-3 si empty).
        prog.sentencias.append(
            DefinicionFuncion(
                nombre='principal',
                parametros=[],
                tipo_retorno='nulo',
                cuerpo=[SentenciaRetornar(expr=None)]))
    return prog


def compilar_desde_plano(ruta_json: str) -> Programa:
    return plano_a_programa(cargar_flat(ruta_json))
