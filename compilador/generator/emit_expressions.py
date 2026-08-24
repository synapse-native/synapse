"""
Generación de código C para expresiones y tipos.
Contiene expr_a_c, tipo_de_expr, I/O builtins, log, formato.
Los emisores de tensores están en emit_tensors.py.
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
        # Builtin lookup
        if nombre in ctx._BUILTINS:
            return ctx._BUILTINS[nombre]
        if nombre in ctx._func_return_types:
            return ctx._func_return_types[nombre]
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
        if nombre in ctx._BUILTINS:
            return ctx._BUILTINS[nombre]
        if nombre in ctx._func_return_types:
            return ctx._func_return_types[nombre]
        # Struct constructor call
        if nombre in ctx._estructuras:
            return nombre
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
        return 'int'

    if isinstance(nodo, ArgumentoTransferido):
        return tipo_de_expr(ctx, nodo.expr)

    if isinstance(nodo, ExprAsm):
        return 'void'

    return 'int'


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
        # Escapar la cadena para C: \n, \r, \t, \\, \"
        val = nodo.valor
        val = val.replace('\\', '\\\\')  # backslash first!
        val = val.replace('\"', '\\"')
        val = val.replace('\n', '\\n')
        val = val.replace('\r', '\\r')
        val = val.replace('\t', '\\t')
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
                        dtor, _ = ctx._destructor_para_tipo(var_tipo, var_name) if var_tipo else ('', '')
                        if dtor and dtor == nombre:
                            ctx._consumed_vars.add(var_name)

        # len, subcadena, empieza_con builtins
        if nombre == 'len':
            if args:
                return f"({args[0]}).longitud"
            return "0"
        if nombre == 'subcadena':
            if len(args) >= 3:
                s, inicio, largo = args[0], args[1], args[2]
                return f"((CadenaSegura){{.longitud={largo}, .datos=((char*)memcpy(malloc({largo}+1),({s}).datos+{inicio},{largo}))}})"
            return "(CadenaSegura){0,(char*)\"\"}"
        if nombre == 'empieza_con':
            if len(args) >= 2:
                s, pref = args[0], args[1]
                return f"((({s}).longitud>=({pref}).longitud&&strncmp(({s}).datos,({pref}).datos,({pref}).longitud)==0)?1:0)"
            return "0"

        # Struct constructor: use C compound literal instead of function call
        if nombre in ctx._estructuras:
            if not args:
                return f"({ctx.traducir_tipo_c(nombre)}){{0}}"
            else:
                return f"({ctx.traducir_tipo_c(nombre)}){{{args_str}}}"

        # Coercion for functions expecting CadenaSegura
        if nombre in ctx._FUNCIONES_ESPERAN_TEXTO:
            return f"{nombre}({args_str})"

        # Check if we need .datos for C function calls
        if nombre in ctx._C_FUNCTIONS_NEED_DATOS:
            expected_types = ctx._C_FUNCTIONS_NEED_DATOS[nombre]
            adjusted = []
            for i, a in enumerate(args):
                if i < len(expected_types) and expected_types[i] == 'char*':
                    # Skip .datos if arg is already char* (ExprObtenerDireccion
                    # of texto produces .datos → tipo_de_expr returns 'puntero')
                    arg_tipo = ''
                    if nodo.argumentos and i < len(nodo.argumentos):
                        arg_tipo = tipo_de_expr(ctx, nodo.argumentos[i])
                    if arg_tipo == 'puntero':
                        adjusted.append(a)
                    else:
                        adjusted.append(f"({a}).datos")
                else:
                    adjusted.append(a)
            return f"{nombre}({', '.join(adjusted)})"

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
        elif tipo_a == 'int':
            fmt_parts.append("%d")
            arg_parts.append(expr_a_c(ctx, a))
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
