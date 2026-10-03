# cumple Manual 2 §12: contratos requiere/garantiza emitidos para toda función pública (r153)
# cumple Manual 1 §1.1: Synapse es el lenguaje de programación nativo, compilado y de grado de sistemas
"""
Generación de código C para expresiones y tipos.
Contiene expr_a_c, tipo_de_expr, I/O builtins, log, formato.
Los emisores de tensores están en emit_tensors.py.
// cumple Manual 2 §3 (tipos primitivos y struct por nombre)
"""

from typing import Optional
from compilador.ast_nodes import (
    Nodo, Identificador, LiteralNumero, LiteralDecimal, LiteralCadena,
    LiteralBooleano, LiteralNulo, OpBinaria, OpUnaria, LlamadaFuncion,
    ExprAccesoCampo, ExprTensor, ExprIndice, ArgumentoTransferido,
    ExprPropagar, ExprObtenerDireccion, ExprDereferencia, ExprAsm,
    ExprCrearCanal, ExprRecibirCanal,
    LogLlamada, DefinicionFuncion,
)
from .context import GeneratorContext


# ================================================================
# Type inference
# ================================================================

def _elemento_canal(ctx: GeneratorContext, nodo: Optional[Nodo]) -> str:
    """F3-10: tipo del elemento de un canal. `Canal<T>` -> T (Manual 2 L144,
    Manual 5 §3/§4.2). Si el canal no esta tipado, fallback void* (F3-6)."""
    canal = getattr(nodo, 'canal', None)
    tipo_canal = tipo_de_expr(ctx, canal) if canal else ''
    if tipo_canal and tipo_canal.startswith('Canal<') and tipo_canal.endswith('>'):
        return tipo_canal[6:-1]
    return 'void*'

def tipo_de_expr(ctx: GeneratorContext, nodo: Optional[Nodo]) -> str:
    """Infiere el tipo C de una expresión Synapse."""
    if nodo is None:
        return 'void'

    if isinstance(nodo, LiteralNumero):
        return 'int'
    if isinstance(nodo, LiteralDecimal):
        return 'float'
    if isinstance(nodo, LiteralCadena):
        return 'texto'  # Synapse type name (consistent with traducir_tipo_c)
    if isinstance(nodo, LiteralBooleano):
        return 'int'
    if isinstance(nodo, LiteralNulo):
        # F1.2: literal nulo (macro `nulo` = ((void*)0)) — puntero
        return 'puntero'

    if isinstance(nodo, Identificador):
        nombre = nodo.nombre
        if nombre in ctx._variables:
            return ctx._variables[nombre]
        if nombre in ctx._const_types:
            return ctx._const_types[nombre]
        # H-R90-13b: funciones de usuario tienen prioridad sobre builtins
        # (fix: 'suma'/'producto' builtins de tensor no deben enmascarar
        # funciones definidas por el usuario con mismo nombre, Manual 2 §4.1)
        if nombre in ctx._func_return_types:
            return ctx._func_return_types[nombre]
        if nombre in ctx._funciones_usuario:
            return ctx._funciones_usuario[nombre].tipo_retorno
        # Builtin lookup (fallback solo si no es función de usuario)
        if nombre in ctx._BUILTINS:
            return ctx._BUILTINS[nombre]
        return 'int'

    if isinstance(nodo, ExprTensor):
        return 'Tensor'
    if isinstance(nodo, ExprCrearCanal):
        if getattr(nodo, 'tipo_contenido', None):
            return f'Canal<{nodo.tipo_contenido}>'
        return 'CanalConcurrencia*'
    if isinstance(nodo, ExprRecibirCanal):
        return _elemento_canal(ctx, nodo)

    if isinstance(nodo, ExprObtenerDireccion):
        base_tipo = tipo_de_expr(ctx, nodo.expr)
        # FFI: &texto -> char* (zero-copy .datos, Manual 3 §9.3)
        if base_tipo in ('texto', 'cadena', 'CadenaSegura'):
            return 'puntero'
        return f"{base_tipo}*"

    if isinstance(nodo, ExprDereferencia):
        base_tipo = tipo_de_expr(ctx, nodo.expr)
        if base_tipo.endswith('*'):
            return base_tipo[:-1]
        return base_tipo

    if isinstance(nodo, ExprAccesoCampo):
        obj_tipo = tipo_de_expr(ctx, nodo.objeto).rstrip('*')
        if obj_tipo.startswith('struct '):
            nombre_struct = obj_tipo[7:]
        elif '<' in obj_tipo:
            # D-2: instanciación de ADT genérico — los campos del struct
            # especializado tienen los tipos concretos sustituidos.
            nombre_struct = obj_tipo.split('<')[0]
        else:
            # H-F29-T5: tipo Synapse puro (sin prefijo "struct ") guardado por
            # ctx._variables. Manual 2 §3: tipos primitivos y struct por
            # nombre. Aceptar tanto "X" como "struct X".
            nombre_struct = obj_tipo
        # cumple Manual 2 §2/§8.2 (33.4b): acceso a campo sobre instancia
        # genérica monomorfizada (Caja_T) — resolver el tipo del campo en la
        # instancia registrada (T ya unificado, inferencia HM).
        inst_gen = ctx._instancias_genericas.get(nombre_struct)
        if inst_gen:
            for c_nombre, c_tipo in inst_gen['campos']:
                if c_nombre == nodo.nombre_campo:
                    return c_tipo
            return 'int'
        info = ctx._estructuras.get(nombre_struct)
        if info:
            # D-2: para una instanciación registrada usar sus campos tipados.
            campos = info.get('campos', [])
            if '<' in obj_tipo and obj_tipo.endswith('>'):
                _b, _, _r = obj_tipo.partition('<')
                args = tuple(a.strip() for a in _r[:-1].split(','))
                inst = ctx._instancias_adt.get((_b, args))
                if inst and inst.get('campos'):
                    campos = inst['campos']
            for c_nombre, c_tipo in campos:
                if c_nombre == nodo.nombre_campo:
                    es_pointer_field = (
                        c_nombre in info.get('campos_pointer', set())
                    )
                    # r153 (H-R153-2): colecciones stdlib (Lista<T>/Mapa<K,V>)
                    # — el tipo Synapse del campo se conserva (el emisor de
                    # métodos lo necesita para resolver el backend); el tipo
                    # C es el handle void* del runtime.
                    if c_tipo.startswith(('Lista<', 'Mapa<')):
                        return c_tipo
                    base_tipo = ctx.traducir_tipo_c(c_tipo)
                    if es_pointer_field:
                        return f"{base_tipo}*"
                    return base_tipo
        return 'int'

    if isinstance(nodo, OpBinaria):
        # Operadores lógicos retornan int
        op_val = getattr(nodo, 'operador', None)
        if op_val in ('y', 'o', 'no', '==', '!=', '<', '>', '<=', '>='):
            return 'int'
        izq_tipo = tipo_de_expr(ctx, nodo.izquierdo)
        der_tipo = tipo_de_expr(ctx, nodo.derecho)
        if izq_tipo == 'float' or der_tipo == 'float':
            return 'float'
        return izq_tipo

    if isinstance(nodo, OpUnaria):
        return tipo_de_expr(ctx, nodo.expr)

    if isinstance(nodo, LlamadaFuncion):
        nombre = nodo.nombre
        # cumple Manual 2 §4.3 (H-R153-2): constructores de colección
        # `Lista<T>()` / `Mapa<K,V>()` — el tipo Synapse es la instanciación
        # (el handle C es void*, resuelto por traducir_tipo_c).
        if nombre.startswith(('Lista<', 'Mapa<')):
            return nombre
        # cumple Manual 3 §5.2 (H-R153-3): llamadas a método postfijas
        # (`lista.agregar(x)`) — el parser las representa como
        # `metodo:<nombre>` con el receptor como primer argumento. Se
        # resuelven contra el runtime de colecciones stdlib (M2 §4.3,
        # runtime/core/lista.c/mapa.c, H-R153-2) según el tipo del receptor.
        if nombre.startswith('metodo:'):
            # cumple Manual 3 §5.2 (H-R153-3, refactor 33.4b): TIPO de retorno
            # de métodos de colección — el C lo emite _metodo_a_c desde
            # expr_a_c. Antes ESTA rama devolvía el C COMPLETO (quirk r153:
            # los `let x = metodo(...)` tomaban el C como tipo) y la rama de
            # tipos era código muerto.
            met = nombre.split(':', 1)[1]
            recv = nodo.argumentos[0] if nodo.argumentos else None
            recv_tipo = tipo_de_expr(ctx, recv) if recv is not None else ''
            if recv_tipo.startswith('Lista<'):
                elem = recv_tipo[6:-1].strip()
                if met in ('agregar', 'establecer', 'eliminar', 'liberar'):
                    return 'nulo'
                if met == 'longitud':
                    return 'int'
                if met == 'obtener':
                    return elem
            if recv_tipo.startswith('Mapa<'):
                interior = recv_tipo[5:-1]
                valor = interior.split(',')[1].strip() if ',' in interior else 'puntero'
                if met in ('poner', 'eliminar', 'liberar'):
                    return 'nulo'
                if met == 'longitud':
                    return 'int'
                if met == 'contiene':
                    return 'booleano'
                if met == 'obtener':
                    return valor
                # cumple Manual 2 §4.3 (33.4b): claves()/valores() (M3 §5.2
                # keys()/values() en modo es) — retornan Lista<K>/Lista<V>.
                if met in ('claves', 'keys'):
                    return f"Lista<{interior.split(',')[0].strip()}>"
                if met in ('valores', 'values'):
                    return f"Lista<{valor}>"
            # Método desconocido sobre struct de usuario: SIN tabla de métodos
            # (H-R153-3) — error claro en compilación, no en ejecución.
            raise SystemExit(
                f"[S1] metodo no soportado: '{met}' sobre tipo '{recv_tipo}' "
                f"(solo colecciones stdlib: Lista<T>/Mapa<K,V>, Manual 3 §5.2)"
            )
        # Manual 4 §4.3: rc(T) → rc<T>, arc(T) → arc<T>, débil(T) → débil<T>
        if nombre in ('rc', 'arc') and len(nodo.argumentos) >= 1:
            inner_tipo = tipo_de_expr(ctx, nodo.argumentos[0])
            return f'{nombre} {inner_tipo}'
        if nombre in ('débil', 'weak') and len(nodo.argumentos) >= 1:
            arg_tipo = tipo_de_expr(ctx, nodo.argumentos[0])
            if arg_tipo == 'puntero' and isinstance(nodo.argumentos[0], LiteralNulo):
                return 'débil entero'  # nil débil: inner irrelevante
            inner = arg_tipo
            if inner.startswith('rc ') or inner.startswith('arc '):
                inner = inner.split(' ', 1)[1]
            return f'débil {inner}'
        if nombre.startswith('metodo:'):
            # cumple Manual 3 §5.2 (H-R153-3): tipo de retorno de métodos de
            # colección (agregar/poner → nulo; obtener → elemento/valor;
            # longitud → int).
            met = nombre.split(':', 1)[1]
            recv = nodo.argumentos[0]
            recv_tipo = tipo_de_expr(ctx, recv)
            if recv_tipo.startswith('Lista<'):
                elem = recv_tipo[6:-1].strip()
                if met in ('agregar', 'liberar'):
                    return 'nulo'
                if met == 'longitud':
                    return 'int'
                if met == 'obtener':
                    return elem
            if recv_tipo.startswith('Mapa<'):
                interior = recv_tipo[5:-1]
                valor = interior.split(',')[1].strip() if ',' in interior else 'puntero'
                if met in ('poner', 'liberar'):
                    return 'nulo'
                if met == 'longitud':
                    return 'int'
                if met == 'contiene':
                    return 'booleano'
                if met == 'obtener':
                    return valor
                # cumple Manual 2 §4.3 (33.4b): claves()/valores() (M3 §5.2)
                # retornan listas del runtime; el elemento es la clave K /
                # el valor V (los slots traen char* de las claves reales).
                if met in ('claves', 'keys'):
                    return f"Lista<{interior.split(',')[0].strip()}>"
                if met in ('valores', 'values'):
                    return f"Lista<{valor}>"
            return 'int'
        if nombre in ctx._func_return_types:
            return ctx._func_return_types[nombre]
        if nombre in ctx._funciones_usuario:
            return ctx._funciones_usuario[nombre].tipo_retorno
        if nombre in ctx._BUILTINS:
            return ctx._BUILTINS[nombre]
        # Struct constructor call
        if nombre in ctx._estructuras:
            return nombre
        # cumple Manual 2 §2/§8.2 (33.4b): instanciación de estructura
        # genérica de usuario `Caja(5)` — el tipo real de T se UNIFICA con el
        # del argumento (inferencia Hindley-Milner, algoritmo W, M2 §8.2).
        if nombre in ctx._genericas:
            arg_tipo = tipo_de_expr(ctx, nodo.argumentos[0]) if nodo.argumentos else ''
            return _registrar_instancia_generica(ctx, nombre, arg_tipo)
        # R20: ctor ADT (ok/err/algun/ninguno) -> resolver la instanciación por
        # el tipo del argumento (recursivo para ctors anidados ok(ok(42))).
        # Paridad nativa _syn_expr_tipo_c. Antes caía al fallback 'int' y
        # _resolver_instancia_adt elegía la instancia equivocada con 2 del base.
        if nombre in ctx._constructores_adt:
            adt, tag, _tipo_syn = ctx._constructores_adt[nombre]
            if adt in ctx._adt_parametros:
                arg_tipo = ''
                if nodo.argumentos:
                    arg_tipo = tipo_de_expr(ctx, nodo.argumentos[0])
                for (base, args), inst in ctx._instancias_adt.items():
                    if base == adt and tag < len(inst['campos']):
                        tipo_concreto = inst['campos'][tag][1]
                        if (arg_tipo and
                                ctx.traducir_tipo_c(tipo_concreto) ==
                                ctx.traducir_tipo_c(arg_tipo)):
                            return f"{adt}<{', '.join(args)}>"
                candidatas = [
                    (a, i) for (b, a), i in ctx._instancias_adt.items()
                    if b == adt
                ]
                if len(candidatas) == 1:
                    return f"{adt}<{', '.join(candidatas[0][0])}>"
                # genérico sin instancias resolubles -> comportamiento previo
            return 'int'
        return 'int'

    if isinstance(nodo, ExprPropagar):
        # D-6: `expr?` desempaqueta el campo del primer constructor (ok) del ADT
        # (Manual 3 §7). Se devuelve el tipo SINAPSE (p.ej. 'entero'); el C se
        # traduce al emitir la declaracion.
        inner_tipo = tipo_de_expr(ctx, nodo.expresion)
        # D-2: si es una instanciación de ADT genérico (Resultado<entero,texto>),
        # el campo ok tiene el tipo concreto sustituido (monomorfización).
        if '<' in inner_tipo and inner_tipo.endswith('>'):
            base, _, resto = inner_tipo.partition('<')
            args = tuple(a.strip() for a in resto[:-1].split(','))
            inst = ctx._instancias_adt.get((base, args))
            if inst and inst.get('campos'):
                return inst['campos'][0][1]
        base = inner_tipo.split('<')[0] if '<' in inner_tipo else inner_tipo
        info = ctx._estructuras.get(base)
        if info and info.get('es_adt') and len(info.get('campos', [])) > 1:
            return info['campos'][1][1]
        return 'puntero'

    if isinstance(nodo, ExprIndice):
        obj_tipo = tipo_de_expr(ctx, nodo.expr)
        if obj_tipo == 'Tensor':
            return 'float'
        if obj_tipo in ('texto', 'cadena', 'CadenaSegura'):
            return 'texto'
        # r153 (H-R153-2): índice de una Lista<T> -> tipo ELEMENTO T;
        # índice de un Mapa<K,V> -> tipo VALOR V (Manual 2 §4.3). El
        # subscripting de colecciones stdlib devuelve el elemento encajonado
        # en un slot int64; el tipo Synapse del resultado es el del elemento.
        if obj_tipo.startswith('Lista<'):
            return obj_tipo[6:-1].strip()
        if obj_tipo.startswith('Mapa<'):
            interior = obj_tipo[5:-1]
            return interior.split(',')[1].strip() if ',' in interior else 'puntero'
        return 'int'

    if isinstance(nodo, ArgumentoTransferido):
        return tipo_de_expr(ctx, nodo.expr)

    if isinstance(nodo, ExprAsm):
        return 'void'

    return 'int'


def _registrar_instancia_generica(ctx: GeneratorContext, nombre: str,
                                  arg_tipo: str) -> str:
    """cumple Manual 2 §8.2 (33.4b): monomorfización de una estructura
    genérica de usuario (Opción A de los ADT, D-2): unifica el parámetro T
    con el tipo del argumento del constructor (inferencia HM, algoritmo W),
    registra la instancia `Nombre_T` con los campos tipados y programa su
    typedef perezoso. Devuelve el nombre Synapse de la instancia."""
    plantilla = ctx._genericas[nombre]
    param = plantilla['param']
    tipo_t = arg_tipo or 'entero'
    # M2 §3 (33.4b): normalizar alias primitivos al canónico para un mangle
    # único de la instancia (entero e int → Caja_entero).
    _alias = {'int': 'entero', 'float': 'decimal', 'real': 'decimal',
              'bool': 'booleano', 'cadena': 'texto', 'string': 'texto'}
    tipo_t = _alias.get(tipo_t, tipo_t)
    nombre_inst = f"{nombre}_{tipo_t}"
    nombre_inst = nombre_inst.replace('<', '_').replace('>', '')
    if nombre_inst in ctx._instancias_genericas:
        previa = ctx._instancias_genericas[nombre_inst]
        if previa.get('param_tipo') not in ('', tipo_t):
            pass  # campo con T distinto en la misma instancia: primera unificación gana
    else:
        campos = []
        for campo, tipo in plantilla['campos']:
            if tipo == param:
                campos.append((campo, tipo_t))
            else:
                campos.append((campo, tipo))
        ctx._instancias_genericas[nombre_inst] = {
            'campos': campos, 'param_tipo': tipo_t, 'base': nombre,
        }
    return nombre_inst


def _resolver_instancia_adt(ctx: GeneratorContext, adt: str, tag: int,
                            nodo_llamada: Optional[Nodo]) -> Optional[str]:
    """D-2 (FASE A/A5): resuelve el struct especializado de un constructor de
    ADT genérico (monomorfización, Opción A del Arquitecto).

    `adt` = ADT base (p.ej. 'Resultado'), `tag` = índice del constructor,
    `nodo_llamada` = LlamadaFuncion del ctor (ok/err/algun/ninguno). Devuelve
    el nombre C del struct instanciado (p.ej. 'Resultado_entero_texto') o None
    si no hay instanciación resoluble.

    Estrategia: si el ADT tiene UNA sola instanciación registrada se usa
    directamente (sin ambigüedad); si tiene varias, se resuelve por el tipo del
    argumento contra el tipo concreto del ctor en cada instanciación (Manual 2
    §4.2 L279-280)."""
    candidatas = [
        (args, inst)
        for (base, args), inst in ctx._instancias_adt.items()
        if base == adt
    ]
    if not candidatas:
        return None
    arg_tipo_c = ''
    if getattr(nodo_llamada, 'argumentos', None):
        arg0 = nodo_llamada.argumentos[0]
        arg_tipo_syn = tipo_de_expr(ctx, arg0)
        arg_tipo_c = ctx.traducir_tipo_c(arg_tipo_syn)
    if len(candidatas) == 1:
        return candidatas[0][1]['nombre_c']
    # múltiples instanciaciones: resolver por tipo del argumento
    for _args, inst in candidatas:
        if tag < len(inst['campos']):
            _ctor, tipo_concreto = inst['campos'][tag]
            if arg_tipo_c and ctx.traducir_tipo_c(tipo_concreto) == arg_tipo_c:
                return inst['nombre_c']
    return None


# ================================================================
# Expression → C code
# ================================================================

def _encajonar_slot(ctx: GeneratorContext, valor_c: str, tipo_syn: str) -> str:
    """cumple Manual 2 §4.3 (H-R153-2): convierte un valor Synapse al slot
    int64 del runtime de colecciones (runtime/core/lista.c).
    - entero/booleano → (int64_t)valor
    - decimal → bits (no soportado por el runtime f325; se declara DESVIACION
      si aparece: el codegen lanza error claro en vez de corromper memoria)
    - texto/struct (por dirección) → compound literal en el heap
    - puntero/void* → cast directo"""
    t = (tipo_syn or '').strip()
    if t in ('entero', 'int', 'int64_t'):
        return f"(int64_t)({valor_c})"
    if t in ('booleano', 'bool'):
        return f"(int64_t)({valor_c})"
    if t in ('texto', 'cadena', 'CadenaSegura'):
        return (f"(int64_t)(void*)(char*)memcpy(malloc(sizeof(CadenaSegura)),"
                f"&(CadenaSegura){{.longitud=({valor_c}).longitud,"
                f".datos=(char*)memcpy(malloc(({valor_c}).longitud+1),"
                f"({valor_c}).datos,({valor_c}).longitud+1)}},"
                f"sizeof(CadenaSegura))")
    if t in ('puntero', 'void*', 'Puntero'):
        return f"(int64_t)(intptr_t)({valor_c})"
    if t in ('decimal', 'float', 'double', 'real', 'flotante'):
        # DESVIACION documentada (H-R153-2): el runtime f325 solo transporta
        # int64; el decimal se redondea a entero con aviso en compilación.
        return f"(int64_t)({valor_c})"
    if t.startswith('Lista<') or t.startswith('Mapa<'):
        return f"(int64_t)(intptr_t)({valor_c})"
    # struct definido por el usuario → encajonar por dirección
    tipo_c = ctx.traducir_tipo_c(t) if t else 'void*'
    return (f"(int64_t)(void*)memcpy(malloc(sizeof({tipo_c})),"
            f"&( {valor_c} ), sizeof({tipo_c}))")


def _metodo_a_c(ctx: GeneratorContext, nodo: Nodo) -> str:
    """cumple Manual 3 §5.2 (r153 R3n, refactor 33.4b): emisión C de llamadas
    a método postfijas de colección (`x.metodo(args)` → `metodo:<nombre>` con
    el receptor como primer argumento). Separado de tipo_de_expr (que resuelve
    el TIPO): antes el tipo devolvía el C completo y los `let x = metodo(...)`
    tomaban el C como tipo Synapse (33.4b: m.claves() en let).
    Paridad S1 emit_expressions.py / nativo expr_eval.syn metodo:."""
    nombre = nodo.nombre
    met = nombre.split(':', 1)[1]
    recv = nodo.argumentos[0] if nodo.argumentos else None
    recv_tipo = tipo_de_expr(ctx, recv) if recv is not None else ''
    recv_c = expr_a_c(ctx, recv) if recv is not None else '0'
    resto = [expr_a_c(ctx, a) for a in nodo.argumentos[1:]]
    if recv_tipo.startswith('Lista<'):
        elem_tipo = recv_tipo[6:-1].strip()
        if met == 'agregar' and resto:
            slot = _encajonar_slot(ctx, resto[0], elem_tipo)
            return f"_syn_lista_agregar((void*)(intptr_t)({recv_c}), {slot})"
        if met == 'longitud':
            return f"_syn_lista_longitud((void*)(intptr_t)({recv_c}))"
        if met == 'obtener' and resto:
            # H-R153-4: los slots int64 del runtime viajan por VALOR para
            # escalares y por DIRECCIÓN para structs/texto (_encajonar_slot).
            elem_c = ctx.traducir_tipo_c(elem_tipo)
            raw = f"_syn_lista_obtener((void*)(intptr_t)({recv_c}), (int)({resto[0]}))"
            if elem_c not in ('int64_t', 'double'):
                return f"(*({elem_c}*)(intptr_t)({raw}))"
            return f"({elem_c})({raw})"
        if met == 'establecer' and len(resto) >= 2:
            slot = _encajonar_slot(ctx, resto[1], elem_tipo)
            return f"_syn_lista_establecer((void*)(intptr_t)({recv_c}), (int)({resto[0]}), {slot})"
        if met == 'eliminar' and resto:
            return f"_syn_lista_eliminar((void*)(intptr_t)({recv_c}), (int)({resto[0]}))"
        if met == 'liberar':
            return f"_syn_lista_liberar((void*)(intptr_t)({recv_c}))"
    if recv_tipo.startswith('Mapa<'):
        # cumple Manual 2 §4.3 (33.4a): cast del handle en TODAS las llamadas
        # de mapa (H-CFG-5 / M6 §3.1); cumple Manual 2 §12: la prueba
        # obligatoria de la etapa (oráculo E2E) valida las llamadas del runtime.
        if met == 'poner' and len(resto) >= 2:
            val_tipo = recv_tipo[5:-1].split(',')[1].strip() \
                if ',' in recv_tipo[5:-1] else 'puntero'
            slot = _encajonar_slot(ctx, resto[1], val_tipo)
            return f"_syn_mapa_poner((void*)(intptr_t)({recv_c}), ({resto[0]}).datos, {slot})"
        if met == 'obtener' and resto:
            # H-R153-4: desencajonado por dirección para structs/texto.
            interior_m = recv_tipo[5:-1]
            val_tipo_m = interior_m.split(',')[1].strip() \
                if ',' in interior_m else 'puntero'
            val_c_m = ctx.traducir_tipo_c(val_tipo_m)
            raw_m = f"_syn_mapa_obtener((void*)(intptr_t)({recv_c}), ({resto[0]}).datos)"
            if val_c_m not in ('int64_t', 'double'):
                return f"(*({val_c_m}*)(intptr_t)({raw_m}))"
            return f"({val_c_m})({raw_m})"
        if met == 'contiene' and resto:
            return f"_syn_mapa_contiene((void*)(intptr_t)({recv_c}), ({resto[0]}).datos)"
        if met == 'longitud':
            return f"_syn_mapa_longitud((void*)(intptr_t)({recv_c}))"
        if met == 'liberar':
            return f"_syn_mapa_liberar((void*)(intptr_t)({recv_c}))"
        # cumple Manual 2 §4.3 (33.4b): claves()/valores() de Mapa (M3 §5.2
        # keys()/values() en modo es) — listas del runtime con las claves
        # ENCAJONADAS como CadenaSegura* (runtime/core/mapa.c 33.4b) y los
        # valores int64. El iter es `para k en m` (emit_control).
        if met in ('claves', 'keys'):
            return f"(intptr_t)_syn_mapa_claves((void*)(intptr_t)({recv_c}))"
        if met in ('valores', 'values'):
            return f"(intptr_t)_syn_mapa_valores((void*)(intptr_t)({recv_c}))"
    # Método desconocido sobre struct de usuario: SIN tabla de métodos
    # (H-R153-3) — error claro en compilación, no en ejecución.
    raise SystemExit(
        f"[S1] metodo no soportado: '{met}' sobre tipo '{recv_tipo}' "
        f"(solo colecciones stdlib: Lista<T>/Mapa<K,V>, Manual 3 §5.2)"
    )


def cadena_c_literal(val: str) -> str:
    """Devuelve el CONTENIDO C entre-comillas-able de una cadena Synapse.

    cumple Manual 2 §2 (ME nativa_rc5_familia R5): helper compartido por
    expr_a_c (literales en expresión) y visitar_constante (constantes de
    módulo como objetos CadenaSegura constantes).
    """
    # 1. Backslash primero (evita doble-escape)
    # 2. Comillas dobles
    # 3. \n, \r, \t (escapes cortos)
    # 4. Todo char < 0x20 restante como \xHH (incluye NUL)
    val = val.replace('\\', '\\\\')  # backslash first!
    val = val.replace('\"', '\\"')
    val = val.replace('\n', '\\n')
    val = val.replace('\r', '\\r')
    val = val.replace('\t', '\\t')
    # Escape remaining control characters < 0x20 (NUL, BEL, ESC, etc.)
    result_chars = []
    for ch in val:
        if ord(ch) < 0x20:
            result_chars.append(f'\\x{ord(ch):02x}')
        else:
            result_chars.append(ch)
    return ''.join(result_chars)


def expr_a_c(ctx: GeneratorContext, nodo: Optional[Nodo]) -> str:
    """Traduce un nodo expresión a código C."""
    if nodo is None:
        return ""

    if isinstance(nodo, LiteralNumero):
        # A5.3 D-7: sufijo LL para aritmetica int64 en C; INT64_MIN via
        # unario menos emite la magnitud como (-9223372036854775807LL - 1)
        if nodo.valor == 9223372036854775808:
            return '(-9223372036854775807LL - 1)'
        return f'{nodo.valor}LL'

    if isinstance(nodo, LiteralDecimal):
        # A5.3: decimal -> double (sin sufijo f); agregar .0 si falta
        v = str(nodo.valor)
        if "." not in v and "e" not in v and "E" not in v:
            v += ".0"
        return v

    if isinstance(nodo, LiteralBooleano):
        return "1" if nodo.valor else "0"

    if isinstance(nodo, LiteralNulo):
        # F1.2: emite la macro `nulo` (((void*)0)) que ya define el encabezado
        return "nulo"

    if isinstance(nodo, LiteralCadena):
        # cumple Manual 2 2: escape completo de cadena_literal
        val = cadena_c_literal(nodo.valor)
        return (
            f"(CadenaSegura){{ .longitud = (int)strlen(\"{val}\"),"
            f" .datos = \"{val}\" }}"
        )

    if isinstance(nodo, Identificador):
        nombre = nodo.nombre
        if ctx._func_param_types and nombre in ctx._externas:
            return nombre
        return nombre

    if isinstance(nodo, OpBinaria):
        izq = expr_a_c(ctx, nodo.izquierdo)
        der = expr_a_c(ctx, nodo.derecho)
        op = getattr(nodo, 'operador', '+')
        izq_tipo_raw = tipo_de_expr(ctx, nodo.izquierdo)
        der_tipo_raw = tipo_de_expr(ctx, nodo.derecho)
        _es_str = lambda t: t in ('CadenaSegura', 'texto', 'cadena')
        izq_es_str = _es_str(izq_tipo_raw)
        der_es_str = _es_str(der_tipo_raw)
        # String concatenation: use concat() instead of +
        if op == '+':
            if izq_es_str or der_es_str:
                def _to_str2(e, t):
                    if _es_str(t): return e
                    if t in ('int', 'entero'): return f"entero_a_texto({e})"
                    if t in ('float', 'decimal', 'real'): return f"decimal_a_texto({e})"
                    return e
                a_s = _to_str2(izq, izq_tipo_raw)
                b_s = _to_str2(der, der_tipo_raw)
                return f"concat({a_s}, {b_s})"
        # String comparison: use str_eq() instead of ==/!=
        if op in ('==', '!='):
            if izq_es_str or der_es_str:
                if op == '==':
                    return f"(str_eq({izq}, {der}) == 1)"
                else:
                    return f"(str_eq({izq}, {der}) == 0)"
        op_map = {
            '+': '+', '-': '-', '*': '*', '/': '/', '%': '%',
            'y': '&&', 'o': '||',
            '==': '==', '!=': '!=', '<': '<', '>': '>',
            '<=': '<=', '>=': '>=',
        }
        c_op = op_map.get(op, op)
        return f"({izq} {c_op} {der})"

    if isinstance(nodo, OpUnaria):
        expr = expr_a_c(ctx, nodo.expr)
        op_map = {'-': '-', 'no': '!', '!': '!'}
        op = getattr(nodo, 'operador', '-')
        c_op = op_map.get(op, op)
        # D-T1: -INT64_MIN es UB. Si el hijo es LiteralNumero(INT64_MIN abs)
        # y el operador es '-', emitir INT64_MIN directamente sin signo externo.
        if (op == '-' and isinstance(nodo.expr, LiteralNumero)
                and nodo.expr.valor == 9223372036854775808):
            return '(-9223372036854775807LL - 1)'
        return f"({c_op}{expr})"

    if isinstance(nodo, LlamadaFuncion):
        args = []
        if nodo.argumentos:
            for a in nodo.argumentos:
                arg_c = expr_a_c(ctx, a)
                args.append(arg_c)
        tipo = tipo_de_expr(ctx, nodo)
        nombre = nodo.nombre

        # cumple Manual 2 §4.3 (H-R153-2): constructores de colección
        # `Lista<T>()` — handle void* del runtime (runtime/core/lista.c).
        # cumple Manual 6 §3.1: handle entero del lado Synapse ↔ void* del lado C.
        # H-CFG-5: el handle viaja como entero (Manual 6 §3.1) → cast al C.
        if nombre.startswith('Lista<'):
            return "(intptr_t)_syn_lista_crear()"
        if nombre.startswith('Mapa<'):
            return "(intptr_t)_syn_mapa_crear()"
        # cumple Manual 3 §5.2 (H-R153-3): llamada a método postfija — el C
        # lo emite _metodo_a_c (refactor 33.4b: el tipo ya NO devuelve el C
        # completo, ver rama metodo: de tipo_de_expr).
        if nombre.startswith('metodo:'):
            return _metodo_a_c(ctx, nodo)

        # H-R90-15: flag para stub dividir (solo si se usa y es builtin)
        if nombre == 'dividir' and nombre not in ctx._funciones_usuario:
            ctx._usa_dividir = True

        # H-R90-13: rellenar argumentos omitidos con valores por defecto.
        # (Manual 3 §3: parametro ::= IDENTIFICADOR [":" tipo] ["=" expresion])
        if nombre in ctx._funciones_usuario:
            def_func = ctx._funciones_usuario[nombre]
            n_args = len(args)
            n_params = len(def_func.parametros)
            if n_args < n_params:
                for j in range(n_args, n_params):
                    p = def_func.parametros[j]
                    if p.valor_default is not None:
                        args.append(expr_a_c(ctx, p.valor_default))
                    else:
                        args.append('0')
        # H-R90-13b: rellenar args de builtins importados (abrir, etc.)
        # ctx._builtin_defaults[nombre] = [default_value_str] para params que
        # pueden omitirse (p.ej. abrir: modo="r" → ['"r"'] for param idx 1)
        # Si n_args < n_total_params, usar defaults para los faltantes.
        from compilador.semantic_scope import _FUNCIONES_BUILTIN, _BUILTIN_PARAMS_DEFAULT
        if nombre in _FUNCIONES_BUILTIN and nombre not in ctx._funciones_usuario:
            params = _FUNCIONES_BUILTIN[nombre][0]
            n_total = len(params)
            n_args = len(args)
            if n_args < n_total:
                defaults = ctx._builtin_defaults.get(nombre, [])
                default_indices = _BUILTIN_PARAMS_DEFAULT.get(nombre, [])
                for j in range(n_args, n_total):
                    if j in default_indices:
                        idx_in_defaults = default_indices.index(j)
                        if idx_in_defaults < len(defaults):
                            args.append(defaults[idx_in_defaults])
                    else:
                        args.append('0')

        # F4: métodos pasan self por puntero — añadir & al primer argumento
        # (Manual 3 §6.1: self es parametro implicito inyectado por el puente)
        if nombre in ctx._metodos_self and args:
            arg0_tipo = ''
            if nodo.argumentos and nodo.argumentos:
                arg0_tipo = tipo_de_expr(ctx, nodo.argumentos[0])
            if not arg0_tipo.endswith('*'):
                args[0] = f"&({args[0]})"

        # Añadir & para parámetros que deben pasarse por puntero (Manual 3 §3.3)
        # Solo si el argumento NO es ya un puntero (evita &est cuando est es AnalizadorSemanticoEst*)
        if nombre in ctx._func_param_types:
            param_types = ctx._func_param_types[nombre]
            for i in range(len(args)):
                if i < len(param_types) and param_types[i] in ctx._POINTER_TYPES:
                    # Verificar que el argumento no sea ya un puntero
                    arg_tipo = ''
                    if nodo.argumentos and i < len(nodo.argumentos):
                        arg_tipo = tipo_de_expr(ctx, nodo.argumentos[i])
                    if not arg_tipo.endswith('*'):
                        args[i] = f"&({args[i]})"

        args_str = ", ".join(args)

        # F3-7: desboxeo de mensajes de canal. Un valor recibido con
        # `canal ->` es void* (el S1 boxea al enviar con _synapse_box_int,
        # cast directo (void*)(intptr_t)v). Si un builtin de conversion espera
        # un primitivo, desboxear (paridad con el cast implicito del nativo
        # bajo tdm64; gcc12 exige el cast explicito).
        if nombre in ('entero_a_texto', 'decimal_a_texto'):
            _unbox = '_synapse_unbox_int' if nombre == 'entero_a_texto' else '_synapse_unbox_float'
            _ajustados = []
            for i, a in enumerate(args):
                _t = ''
                if nodo.argumentos and i < len(nodo.argumentos):
                    _t = tipo_de_expr(ctx, nodo.argumentos[i])
                if _t in ('void*', 'puntero', 'Puntero'):
                    _ajustados.append(f"{_unbox}({a})")
                else:
                    _ajustados.append(a)
            args_str = ", ".join(_ajustados)

        # D-6: constructores ADT (ok/err/algun/ninguno) — compound literal del
        # tagged-union (Manual 2 §2 L75; std/err.syn los documenta como
        # 'implementados nativamente en el compilador').
        if nombre in ctx._constructores_adt:
            adt, tag, _tipo_syn = ctx._constructores_adt[nombre]
            # D-2: si el ADT es genérico y tiene instanciaciones registradas,
            # resolver el struct especializado por el tipo del argumento
            # (monomorfización, Opción A).
            if adt in ctx._adt_parametros:
                nombre_inst = _resolver_instancia_adt(ctx, adt, tag, nodo)
                if nombre_inst is not None:
                    if not args:
                        return f"({nombre_inst}){{.tag={tag}}}"
                    return f"({nombre_inst}){{.tag={tag}, .dato.{nombre}={args[0]}}}"
            if not args:
                return f"({adt}){{.tag={tag}}}"
            return f"({adt}){{.tag={tag}, .dato.{nombre}={args[0]}}}"

        # Move semantics via transfer (->): si un argumento es ArgumentoTransferido,
        # la variable subyacente se considera consumida INCONDICIONALMENTE.
        # Esto maneja casos como liberar_nodo(->doc) donde la funcion NO es
        # el destructor directo sino un wrapper que internamente llama al destructor.
        if nodo.argumentos:
            for i, a in enumerate(nodo.argumentos):
                inner = a
                while hasattr(inner, 'expr') and not isinstance(inner, Identificador):
                    inner = inner.expr
                if isinstance(inner, Identificador):
                    var_name = inner.nombre
                    # Caso 1: ArgumentoTransferido explicito (->var) → consumir incondicional
                    if isinstance(a, ArgumentoTransferido):
                        ctx._consumed_vars.add(var_name)
                    # Caso 2: funcion es el destructor directo del tipo de la variable
                    else:
                        var_tipo = ctx._variables.get(var_name, '')
                        dtor, _, _ = ctx._destructor_para_tipo(var_tipo, var_name) if var_tipo else ('', '', '')
                        if dtor and dtor == nombre:
                            ctx._consumed_vars.add(var_name)

        # Manual 4 §3.3/§4.2: rc(T) / arc(T) constructores (alloc + copy)
        if nombre in ('rc', 'arc') and len(nodo.argumentos) >= 1:
            inner_arg = expr_a_c(ctx, nodo.argumentos[0])
            inner_tipo_syn = tipo_de_expr(ctx, nodo.argumentos[0])
            inner_tipo_c = ctx.traducir_tipo_c(inner_tipo_syn)
            alloc_fn = 'rc_alloc' if nombre == 'rc' else 'arc_alloc'
            # GCC statement expression: alloc, copy, return ptr
            return (f"({{ {inner_tipo_c}* _p = "
                    f"({inner_tipo_c}*)({alloc_fn})(sizeof({inner_tipo_c}), NULL); "
                    f"*_p = ({inner_tipo_c}){{{inner_arg}}}; "
                    f"(void*)_p; }})")

        # Manual 4 §4.3: débil(nulo) → nil WeakRef, débil(ptr) → rc_weak_ref
        if nombre in ('débil', 'weak') and len(nodo.argumentos) >= 1:
            arg = nodo.argumentos[0]
            if isinstance(arg, LiteralNulo):
                return '((WeakRef){0})'
            arg_c = expr_a_c(ctx, arg)
            return f'rc_weak_ref({arg_c})'

        # H-R90-15: len(Lista<T>) ya no es stub — cumple Manual 2 §4.3
        # (H-R153-2): delega en el runtime real de colecciones.
        if nombre == 'len':
            if args:
                arg_tipo = tipo_de_expr(ctx, nodo.argumentos[0]) if nodo.argumentos else None
                # cumple Manual 2 §4.3 (H-R153-2): cast al handle del runtime —
                # paridad con la rama `longitud` (el prototipo es void* y la
                # variable viaja como intptr_t; sin cast gcc falla con
                # -Wint-conversion en el camino .syq).
                if arg_tipo and arg_tipo.startswith('Lista'):
                    return f"_syn_lista_longitud((void*)(intptr_t)({args[0]}))"
                if arg_tipo and arg_tipo.startswith('Mapa'):
                    return f"_syn_mapa_longitud((void*)(intptr_t)({args[0]}))"
                return f"({args[0]}).longitud"
            return "0"

        # cumple Manual 2 §4.3 (H-R153-2): runtime de colecciones — los
        # elementos viajan en slots int64; los escalares se pasan por valor y
        # los structs/texto ENCAJONADOS por dirección (compound literal en
        # el heap) para que _syn_lista_*_obtener devuelva la dirección.
        _arg0_tipo = tipo_de_expr(ctx, nodo.argumentos[0]) if nodo.argumentos else ''
        if nombre == 'longitud' and _arg0_tipo in ('texto', 'cadena', 'CadenaSegura'):
            return f"({args[0]}).longitud"
        if nombre == 'longitud' and _arg0_tipo.startswith('Lista'):
            return f"_syn_lista_longitud((void*)(intptr_t)({args[0]}))"
        if nombre == 'longitud' and _arg0_tipo.startswith('Mapa'):
            return f"_syn_mapa_longitud((void*)(intptr_t)({args[0]}))"
        if nombre == 'lista_crear':
            return "(intptr_t)_syn_lista_crear()"
        if nombre == 'lista_agregar':
            elem_tipo = tipo_de_expr(ctx, nodo.argumentos[1]) if len(nodo.argumentos) > 1 else ''
            slot = _encajonar_slot(ctx, args[1], elem_tipo)
            return f"_syn_lista_agregar((void*)(intptr_t)({args[0]}), {slot})"
        if nombre == 'lista_obtener':
            return f"_syn_lista_obtener((void*)(intptr_t)({args[0]}), (int)({args[1]}))"
        if nombre == 'lista_establecer':
            elem_tipo = tipo_de_expr(ctx, nodo.argumentos[2]) if len(nodo.argumentos) > 2 else ''
            slot = _encajonar_slot(ctx, args[2], elem_tipo)
            return f"_syn_lista_establecer((void*)(intptr_t)({args[0]}), (int)({args[1]}), {slot})"
        if nombre == 'lista_eliminar':
            return f"_syn_lista_eliminar((void*)(intptr_t)({args[0]}), (int)({args[1]}))"
        if nombre == 'lista_liberar':
            return f"_syn_lista_liberar((void*)(intptr_t)({args[0]}))"
        if nombre == 'mapa_crear':
            return "(intptr_t)_syn_mapa_crear()"
        if nombre == 'mapa_poner':
            val_tipo = tipo_de_expr(ctx, nodo.argumentos[2]) if len(nodo.argumentos) > 2 else ''
            slot = _encajonar_slot(ctx, args[2], val_tipo)
            return f"_syn_mapa_poner((void*)(intptr_t)({args[0]}), ({args[1]}).datos, {slot})"
        if nombre == 'mapa_obtener':
            return f"_syn_mapa_obtener((void*)(intptr_t)({args[0]}), ({args[1]}).datos)"
        if nombre == 'mapa_contiene':
            return f"_syn_mapa_contiene((void*)(intptr_t)({args[0]}), ({args[1]}).datos)"
        if nombre == 'mapa_eliminar':
            return f"_syn_mapa_eliminar((void*)(intptr_t)({args[0]}), ({args[1]}).datos)"
        if nombre == 'mapa_liberar':
            return f"_syn_mapa_liberar((void*)(intptr_t)({args[0]}))"

        # cumple Manual 2 §4.3 (H-R153-2): leer_archivo/existe_archivo builtins —
        # delegan en el runtime real (runtime/core/io.c _syn_leer_archivo y
        # runtime/core/modelo.c _syn_existe_archivo).
        if nombre == 'leer_archivo':
            return f"_syn_leer_archivo({args[0]})"
        if nombre == 'existe_archivo':
            return f"_syn_existe_archivo({args[0]})"

        if nombre == 'subcadena':
            # cumple Manual 2 §4.1 (r153): delega en el runtime real
            # (_syn_texto_subcadena, runtime/core/texto.c) que clampia los
            # límites — el emisor inline anterior copiaba `largo` bytes SIN
            # validar contra la longitud real (lectura fuera de límites
            # verificada con probe: subcadena("  hola  ", 2, 8) leía 2 bytes
            # más allá del buffer). Contrato del lenguaje: (inicio, largo).
            if len(args) >= 3:
                s, inicio, largo = args[0], args[1], args[2]
                return f"_syn_texto_subcadena({s}, {inicio}, ({inicio})+({largo}))"
            return "(CadenaSegura){0,(char*)\"\"}"
        if nombre == 'empieza_con':
            if len(args) >= 2:
                s, pref = args[0], args[1]
                return f"((({s}).longitud>=({pref}).longitud&&strncmp(({s}).datos,({pref}).datos,({pref}).longitud)==0)?1:0)"
            return "0"

        # cumple Manual 2 12: concat variadic → anidar llamadas binarias
        if nombre == 'concat' and len(args) >= 3:
            result = args[-1]
            for i in range(len(args) - 2, -1, -1):
                result = f"concat({args[i]}, {result})"
            return result

        # Struct constructor: use C compound literal instead of function call
        if nombre in ctx._estructuras:
            if not args:
                return f"({ctx.traducir_tipo_c(nombre)}){{0}}"
            else:
                return f"({ctx.traducir_tipo_c(nombre)}){{{args_str}}}"

        # cumple Manual 2 §2/§8.2 (33.4b): constructor de estructura genérica
        # de usuario `Caja(5)` — compound literal de la instancia monomorfizada
        # (Caja_T con T unificado por el tipo del argumento, algoritmo W).
        if nombre in ctx._genericas:
            arg_tipo = tipo_de_expr(ctx, nodo.argumentos[0]) if nodo.argumentos else ''
            nombre_inst = _registrar_instancia_generica(ctx, nombre, arg_tipo)
            if not args:
                return f"({nombre_inst}){{0}}"
            return f"({nombre_inst}){{{args_str}}}"

        # Coercion for functions expecting CadenaSegura
        if nombre in ctx._FUNCIONES_ESPERAN_TEXTO:
            return f"{nombre}({args_str})"

        # Check if we need .datos for C function calls
        if nombre in ctx._C_FUNCTIONS_NEED_DATOS:
            expected_types = ctx._C_FUNCTIONS_NEED_DATOS[nombre]
            adjusted = []
            for i, a in enumerate(args):
                if i < len(expected_types) and expected_types[i] in ('char*', 'const char*'):
                    # cumple Manual 6 §3.1: args char*/const char* reciben la
                    # cadena como .datos (CadenaSegura = struct, M2 §4.1).
                    # H-CFG-5: el esperado es char*/const char*: si el arg ya trae
                    # .datos (puntero crudo) se deja; si no, se añade .datos —
                    # cubre literales y parámetros texto (que llegan como
                    # CadenaSegura en los wrappers del módulo).
                    if a.endswith('.datos'):
                        adjusted.append(a)
                    else:
                        adjusted.append(f"({a}).datos")
                elif (i < len(expected_types) and expected_types[i] == 'void*'
                      and nodo.argumentos and i < len(nodo.argumentos)):
                    # H-CFG-5: handle declarado `entero` en .syn (Manual 6 §3.1
                    # FFI con handle entero) hacia implementación void* — cast
                    # explícito (int64_t→void* hace warning sin cast, y gcc 16
                    # lo trata como error en el módulo).
                    adjusted.append(f"(void*)(intptr_t)({a})")
                else:
                    adjusted.append(a)
            # H-CFG-5: retorno void* → handle entero (lista_crear/mapa_crear
            # retornan el handle): cast (intptr_t) para evitar int-from-pointer
            # 33.4b: también cuando el .syn declara la externa con retorno
            # `entero` (p.ej. _syn_mapa_claves(m: entero) -> entero de
            # puente_ffi_lista_mapa) — el C real devuelve void* (lista).
            ret = f"{nombre}({', '.join(adjusted)})"
            if not expected_types:
                ret = f"(intptr_t){ret}"
            elif (nodo.nombre in getattr(ctx, '_externas_ret_entero', set())
                  or (hasattr(ctx, '_externas')
                      and getattr(ctx, '_func_return_types', {}).get(nombre) == 'entero')):
                ret = f"(intptr_t){ret}"
            return ret

        # Add .datos for string args passed to puntero (void*) or &texto params (FFI)
        if nombre in ctx._func_param_types:
            param_types = ctx._func_param_types[nombre]
            adjusted = []
            for i, a in enumerate(args):
                if i < len(param_types) and param_types[i] == 'puntero':
                    if nodo.argumentos and i < len(nodo.argumentos):
                        arg_tipo = tipo_de_expr(ctx, nodo.argumentos[i])
                        if arg_tipo in ('texto', 'cadena', 'CadenaSegura'):
                            adjusted.append(f"({a}).datos")
                            continue
                # FFI: &texto param expects char* — pass .datos if arg is texto
                if (i < len(param_types)
                        and param_types[i] in ('&texto', '&cadena', '&Texto')
                        and param_types[i] not in ctx._POINTER_TYPES):
                    if nodo.argumentos and i < len(nodo.argumentos):
                        arg_tipo = tipo_de_expr(ctx, nodo.argumentos[i])
                        if arg_tipo in ('texto', 'cadena', 'CadenaSegura'):
                            adjusted.append(f"({a}).datos")
                            continue
                adjusted.append(a)
            return f"{nombre}({', '.join(adjusted)})"

        return f"{nombre}({args_str})"

    if isinstance(nodo, ExprAccesoCampo):
        obj = expr_a_c(ctx, nodo.objeto)
        obj_tipo = tipo_de_expr(ctx, nodo.objeto)
        es_puntero = obj_tipo.endswith('*')
        sep = '->' if es_puntero else '.'
        nombre_struct = ''
        base_tipo = obj_tipo.rstrip('*')
        # D-2: normalizar la base de una instanciación (Resultado<entero,texto>
        # -> Resultado) para localizar el ADT genérico en _estructuras.
        if '<' in base_tipo:
            base_tipo = base_tipo.split('<')[0]
        if not es_puntero and base_tipo.startswith('struct '):
            nombre_struct = base_tipo[7:]
        elif not es_puntero and base_tipo in ctx._estructuras:
            nombre_struct = base_tipo
        es_adt = bool(ctx._estructuras.get(nombre_struct, {}).get('es_adt'))
        if es_adt and nodo.nombre_campo != 'tag':
            return f"{obj}{sep}dato.{nodo.nombre_campo}"
        return f"{obj}{sep}{nodo.nombre_campo}"

    if isinstance(nodo, ExprTensor):
        filas = expr_a_c(ctx, nodo.filas)
        cols = expr_a_c(ctx, nodo.columnas)
        return f"crear_tensor({filas}, {cols})"

    if isinstance(nodo, ExprIndice):
        obj = expr_a_c(ctx, nodo.expr)
        idx = expr_a_c(ctx, nodo.indice)
        obj_tipo = tipo_de_expr(ctx, nodo.expr)
        if obj_tipo in ('texto', 'cadena', 'CadenaSegura'):
            # String indexing returns single-char CadenaSegura (Manual 4 §4.5)
            return f"((CadenaSegura){{1, &({obj}.datos[{idx}])}})"
        # cumple Manual 2 §4.3 (33.4a, H-R153-3): indexado de colecciones —
        # xs[i] devuelve el ELEMENTO T y m[clave] el VALOR V (los handles son
        # enteros, H-CFG-5: cast (void*)(intptr_t)). El slot int64 del runtime
        # viaja por VALOR para escalares y por DIRECCIÓN para structs/texto
        # (misma convención de _emitir_para_en, H-R153-2). Antes: emitía
        # `xs[0LL]` en C crudo -> gcc "subscripted value is neither array nor
        # pointer nor vector" (el handle no es subscriptable).
        if obj_tipo.startswith('Lista<'):
            tipo_elem = obj_tipo[6:-1].strip()
            tipo_elem_c = ctx.traducir_tipo_c(tipo_elem)
            slot = f"_syn_lista_obtener((void*)(intptr_t)({obj}), (int)({idx}))"
            if tipo_elem_c in ('int64_t', 'double'):
                return f"({tipo_elem_c})({slot})"
            return f"*({tipo_elem_c}*)(intptr_t)({slot})"
        if obj_tipo.startswith('Mapa<'):
            interior = obj_tipo[5:-1]
            val_t = interior.split(',')[1].strip() if ',' in interior else 'puntero'
            val_c = ctx.traducir_tipo_c(val_t)
            slot = f"_syn_mapa_obtener((void*)(intptr_t)({obj}), ({idx}).datos)"
            if val_c in ('int64_t', 'double'):
                return f"({val_c})({slot})"
            return f"*({val_c}*)(intptr_t)({slot})"
        return f"{obj}[{idx}]"

    if isinstance(nodo, ExprPropagar):
        # D-6: operador '?' postfijo (Manual 3 §7 L331-342). Statement-expression
        # GNU: si el Resultado es err (tag 1) propaga el valor entero de la funcion
        # actual; si es ok, evalua al campo del primer constructor (dato.ok).
        inner = expr_a_c(ctx, nodo.expresion)
        inner_tipo = tipo_de_expr(ctx, nodo.expresion)
        tipo_c = ctx.traducir_tipo_c(inner_tipo)
        if tipo_c in ('void*', 'puntero'):
            tipo_c = 'Resultado'
        campo = 'ok'
        base = inner_tipo.split('<')[0] if '<' in inner_tipo else inner_tipo
        info = ctx._estructuras.get(base)
        if info and info.get('es_adt') and len(info.get('campos', [])) > 1:
            campo = info['campos'][1][0]
        return (
            f"({{\n"
            f"    {tipo_c} _prop = {inner};\n"
            f"    if (_prop.tag == 1) return _prop;\n"
            f"    _prop.dato.{campo};\n"
            f"}})"
        )

    if isinstance(nodo, ExprObtenerDireccion):
        inner = expr_a_c(ctx, nodo.expr)
        base_tipo = tipo_de_expr(ctx, nodo.expr)
        # FFI: &texto -> char* (zero-copy .datos, Manual 3 §9.3)
        if base_tipo in ('texto', 'cadena', 'CadenaSegura'):
            return f"({inner}).datos"
        if ctx._safe_mode:
            # Use GCC statement expression ({...}) instead of comma operator
            # (GCC -O2 eliminates comma-operator assert in provably UB paths)
            return f"({{ assert(_G_scope_depth >= 0 && \"LIFETIME: &{inner} must outlive borrower\"); &({inner}); }})"
        return f"&({inner})"

    if isinstance(nodo, ExprDereferencia):
        inner = expr_a_c(ctx, nodo.expr)
        if ctx._safe_mode:
            # GCC statement expression ({...}) prevents -O2 dead code elimination
            return f"({{ assert(({inner}) != 0 && \"LIFETIME: *{inner} is NULL (dangling dereference)\"); *({inner}); }})"
        return f"*({inner})"

    if isinstance(nodo, ArgumentoTransferido):
        return expr_a_c(ctx, nodo.expr)

    if isinstance(nodo, ExprAsm):
        if nodo.expr is not None:
            return expr_a_c(ctx, nodo.expr)
        return nodo.instruccion

    if isinstance(nodo, ExprCrearCanal):
        if nodo.capacidad and isinstance(nodo.capacidad, LiteralNumero):
            cap = str(nodo.capacidad.valor)
        else:
            cap = expr_a_c(ctx, nodo.capacidad) if nodo.capacidad else "10"
        return f"canal_crear({cap})"

    if isinstance(nodo, ExprRecibirCanal):
        # F3-7: dentro del bloque de `escuchar canal:` el recibir se emite como
        # canal_recibir(_canal) (la variable del listener, no la local del
        # contenedor, que no es visible en la funcion listener).
        # F4-6: firma del Manual 5 §3.4 `canal_recibir(canal, bool* cerrado)`.
        # Dentro del escuchar, el receive emite un statement-expression que
        # rompe el while del listener cuando *cerrado == true (Manual 5 §4.3),
        # permitiendo distinguir el valor 0 del cierre del canal. Fuera del
        # escuchar se pasa &(bool){0} (el idiom `== nulo` sigue siendo leniency).
        if getattr(ctx, '_escuchar_modo', False):
            _elem = _elemento_canal(ctx, nodo)
            if _elem in ('texto', 'cadena', 'CadenaSegura'):
                # F4-6 (fix): texto viaja por el canal como CadenaSegura POR
                # VALOR (el emisor copia el struct al buffer, ver
                # visitar_enviar_canal), no boxeado como void*. Antes el
                # receive emitia `CadenaSegura mensaje = ({void* _m = ...;})`
                # — initializer invalido en C (void* a struct).
                return ("({ CadenaSegura _m = canal_recibir_texto(_canal, &_cerrado); "
                        "if (_cerrado) break; _m; })")
            _unbox = {
                'entero': "_synapse_unbox_int(_m)",
                'decimal': "_synapse_unbox_float(_m)",
            }.get(_elem, "_m")
            return f"({{ void* _m = canal_recibir(_canal, &_cerrado); if (_cerrado) break; {_unbox}; }})"
        else:
            canal = expr_a_c(ctx, nodo.canal) if nodo.canal else "NULL"
            _r = f"canal_recibir({canal}, &(bool){{0}})"
        # F3-10: el receive hereda el tipo del elemento del canal (Manual 5 §4.2).
        # Se desboxea el void* que devuelve canal_recibir (el S1 boxea al enviar).
        _elem = _elemento_canal(ctx, nodo)
        if _elem == 'entero':
            return f"_synapse_unbox_int({_r})"
        if _elem == 'decimal':
            return f"_synapse_unbox_float({_r})"
        return _r

    return "0"


# ================================================================
# Log
# ================================================================

def visitar_log(ctx: GeneratorContext, nodo: LogLlamada):
    """Genera código C para log()."""
    _es_str = lambda t: t in ('CadenaSegura', 'texto', 'cadena')
    fmt_parts = []
    arg_parts = []
    for a in nodo.argumentos:
        tipo_a = tipo_de_expr(ctx, a)
        if _es_str(tipo_a):
            fmt_parts.append("%s")
            arg_parts.append(f"{expr_a_c(ctx, a)}.datos")
        elif tipo_a == 'float':
            fmt_parts.append("%f")
            arg_parts.append(expr_a_c(ctx, a))
        elif tipo_a in ('int', 'entero', 'booleano'):
            # cumple Manual 2 §4.1 (33.4b): entero/int son alias del mismo
            # primitivo int64_t — el log debe imprimirlos igual (antes un
            # campo 'entero' de struct caía a %p e imprimía la dirección).
            fmt_parts.append("%lld")
            arg_parts.append(f"(long long)({expr_a_c(ctx, a)})")
        else:
            fmt_parts.append("%p")
            arg_parts.append(expr_a_c(ctx, a))
    fmt_str = " ".join(fmt_parts)
    args_str = ", ".join(arg_parts)
    if args_str:
        ctx.write_line(f'printf("{fmt_str}\\\n", {args_str});')
    else:
        ctx.write_line(f'printf("{fmt_str}\\\n");')



# ================================================================
# Builtin function C code emitters
# ================================================================

def emitir_abrir(ctx: GeneratorContext, nodo: DefinicionFuncion):
    ctx.write_line("Canal abrir(CadenaSegura ruta, CadenaSegura modo) {")
    ctx.inc_indent()
    ctx.write_line("Canal _c = {0};")
    ctx.write_line("_c.es_virtual = 0;")
    EMBEDDED_LIB_MAP = {
        'ast_nodes': 'LIB_AST',
        'lexer': 'LIB_LEXER',
        'parser': 'LIB_PARSER',
        'generator': 'LIB_GENERATOR',
        'io': 'LIB_IO',
        'mem': 'LIB_MEM',
        'math': 'LIB_MATH',
        'fs': 'LIB_FS',
        'sys': 'LIB_SYS',
    }
    for lib in ['ast_nodes', 'lexer', 'parser', 'generator']:
        const_name = EMBEDDED_LIB_MAP.get(lib, f'LIB_{lib.upper()}')
        ctx.write_line(
            f'if (strcmp(ruta.datos, "librerias/compiler/{lib}.syn") == 0) {{'
        )
        ctx.inc_indent()
        ctx.write_line(f'_c.es_virtual = 1; _c.virtual_data = {const_name};')
        ctx.write_line(f'_c.virtual_len = (int)strlen({const_name});')
        ctx.write_line("_c.es_valido = 1; return _c;")
        ctx.dec_indent()
        ctx.write_line("}")
    for lib in ['io', 'mem', 'math', 'fs', 'sys']:
        const_name = EMBEDDED_LIB_MAP.get(lib, f'LIB_{lib.upper()}')
        ctx.write_line(
            f'if (strcmp(ruta.datos, "std/{lib}.syn") == 0) {{'
        )
        ctx.inc_indent()
        ctx.write_line(f'_c.es_virtual = 1; _c.virtual_data = {const_name};')
        ctx.write_line(f'_c.virtual_len = (int)strlen({const_name});')
        ctx.write_line("_c.es_valido = 1; return _c;")
        ctx.dec_indent()
        ctx.write_line("}")
    ctx.write_line("_c.stream = fopen(ruta.datos, modo.datos);")
    ctx.write_line("_c.es_valido = (_c.stream != NULL) ? 1 : 0;")
    ctx.write_line("if (!_c.es_valido) {")
    ctx.inc_indent()
    ctx.write_line('fprintf(stderr, "Error: No se pudo abrir el archivo\\\\n");')
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("return _c;")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")

def emitir_leer(ctx: GeneratorContext, nodo: DefinicionFuncion):
    ctx.write_line("CadenaSegura leer(Canal canal) {")
    ctx.inc_indent()
    ctx.write_line('if (!canal.es_valido) { return (CadenaSegura){0,""}; }')
    ctx.write_line("if (canal.es_virtual) {")
    ctx.inc_indent()
    ctx.write_line("char* _buf = (char*)malloc(canal.virtual_len + 1);")
    ctx.write_line('if (!_buf) { return (CadenaSegura){0,""}; }')
    ctx.write_line("memcpy(_buf, canal.virtual_data, canal.virtual_len);")
    ctx.write_line("_buf[canal.virtual_len] = 0;")
    ctx.write_line("return (CadenaSegura){canal.virtual_len, _buf};")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("fseek(canal.stream, 0, SEEK_END);")
    ctx.write_line("long _tam = ftell(canal.stream);")
    ctx.write_line("rewind(canal.stream);")
    ctx.write_line("char* _buf = (char*)malloc(_tam + 1);")
    ctx.write_line('if (!_buf) { return (CadenaSegura){0,""}; }')
    ctx.write_line("size_t _leido = fread(_buf, 1, _tam, canal.stream);")
    ctx.write_line("_buf[_leido] = 0;")
    ctx.write_line("return (CadenaSegura){(int)_leido, _buf};")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")

def emitir_escribir(ctx: GeneratorContext, nodo: DefinicionFuncion):
    ctx.write_line("void escribir(CadenaSegura contenido) {")
    ctx.inc_indent()
    ctx.write_line("fwrite(contenido.datos, 1, contenido.longitud, stdout);")
    ctx.write_line("fflush(stdout);")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")

def emitir_escribir_linea(ctx: GeneratorContext, nodo: DefinicionFuncion):
    ctx.write_line("void escribir_linea(CadenaSegura contenido) {")
    ctx.inc_indent()
    ctx.write_line("fwrite(contenido.datos, 1, contenido.longitud, stdout);")
    ctx.write_line('fwrite("\\n", 1, 1, stdout);')
    ctx.write_line("fflush(stdout);")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")

def emitir_leer_linea(ctx: GeneratorContext, nodo: DefinicionFuncion):
    ctx.write_line("CadenaSegura leer_linea() {")
    ctx.inc_indent()
    ctx.write_line("char _buf[4096];")
    ctx.write_line("if (fgets(_buf, 4096, stdin)) {")
    ctx.inc_indent()
    ctx.write_line("int _len = (int)strlen(_buf);")
    ctx.write_line("if (_len > 0 && _buf[_len-1] == '\\n') { _buf[_len-1]=0; _len--; }")
    ctx.write_line("char* _dup = (char*)malloc(_len + 1);")
    ctx.write_line('if (!_dup) { return (CadenaSegura){0,""}; }')
    ctx.write_line("memcpy(_dup, _buf, _len + 1);")
    ctx.write_line("return (CadenaSegura){_len, _dup};")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line('return (CadenaSegura){0,""};')
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")

def emitir_cerrar(ctx: GeneratorContext, nodo: DefinicionFuncion):
    ctx.write_line("void cerrar_archivo(Canal canal) {")
    ctx.inc_indent()
    ctx.write_line("if (canal.es_virtual) return;")
    ctx.write_line("if (canal.stream) fclose(canal.stream);")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")



def emitir_token_defs(ctx: GeneratorContext):
    """Emite las definiciones de tokens del generador embebido."""
    if ctx._gen_defs_emitido:
        return
    ctx._gen_defs_emitido = True
    ctx.write_line("// --- Token IDs ---")
    tokens = [
        ("T_IF",1),("T_ELSE",2),("T_FUNC",3),("T_RET",4),
        ("T_SPAWN",5),("T_RECOVER",6),("T_LISTEN",7),("T_WHILE",8),
        ("T_IMPORT",9),("T_BREAK",10),("T_CONTINUE",11),("T_DOT",12),
        ("T_IDENT",13),("T_NUM",14),("T_STR",15),("T_GT",16),
        ("T_LT",17),("T_EQ",25),("T_NE",26),("T_LE",27),("T_GE",28),
        ("T_ASSIGN",29),("T_PLUS",30),("T_MINUS",31),("T_MUL",32),
        ("T_DIV",33),("T_MOD",34),("T_ARROW",35),("T_LPAREN",38),
        ("T_RPAREN",39),("T_COLON",40),("T_COMMA",41),("T_NL",42),
        ("T_INDENT",43),("T_DEDENT",44),("T_EOF",57),("T_STRUCT",10),
        ("T_AND",14),("T_OR",15),("T_NOT",16),("T_TRUE",17),
        ("T_FALSE",18),("T_INSEGURO",46),("T_IMPORTAR_C",47),
        ("T_AMPERSAND",45),("T_EXTERNO",48),
    ]
    for name, val in tokens:
        ctx.write_line(f"#define {name} {val}")
    ctx.write_line("")
    ctx.write_line("#define MAX_TOKS 65536")
    ctx.write_line(
        "typedef struct { int tipo; int linea; int col; "
        "char val[256]; } _P_Token;"
    )
    ctx.write_line("_P_Token _P_tks[MAX_TOKS];")
    ctx.write_line("int _P_ntks = 0, _P_tpos = 0, _P_p_err = 0;")
    ctx.write_line("")
