"""
Generación de código C para estructuras de control de flujo.
Cada función recibe (ctx, nodo) siguiendo el patrón Composición + Contexto.
Usa import tardío para evitar dependencias circulares con _visitar().
"""

from compilador.ast_nodes import (
    SentenciaSi, SentenciaMientras, SentenciaPara,
    NodoCoincidir, NodoCaso,
)
from .context import GeneratorContext, _dividir_args_tipo
from .emit_expressions import expr_a_c, tipo_de_expr


def _visitar_stmt(ctx, nodo):
    """Import tardío de _visitar para evitar ciclo."""
    from . import visitar as _v
    return _v(ctx, nodo)


def visitar_si(ctx: GeneratorContext, nodo: SentenciaSi):
    """Genera código C para if/else."""
    cond = expr_a_c(ctx, nodo.condicion)
    ctx.write_line(f"if ({cond}) {{")
    ctx.inc_indent()
    ctx.push_scope()
    for s in nodo.cuerpo:
        _visitar_stmt(ctx, s)
    ctx.pop_scope()
    ctx.dec_indent()
    ctx.write_line("}")
    if nodo.cuerpo_sino:
        ctx.write_line("else {")
        ctx.inc_indent()
        ctx.push_scope()
        for s in nodo.cuerpo_sino:
            _visitar_stmt(ctx, s)
        ctx.pop_scope()
        ctx.dec_indent()
        ctx.write_line("}")


def visitar_mientras(ctx: GeneratorContext, nodo: SentenciaMientras):
    """Genera código C para while."""
    cond = expr_a_c(ctx, nodo.condicion)
    ctx.write_line(f"while ({cond}) {{")
    ctx.inc_indent()
    ctx.push_scope()
    for s in nodo.cuerpo:
        _visitar_stmt(ctx, s)
    ctx.pop_scope()
    ctx.dec_indent()
    ctx.write_line("}")


def visitar_para(ctx: GeneratorContext, nodo: SentenciaPara):
    """R30 (Manual 2 §2.2 L108): `para i = 0 mientras i < 3:` — la variable de
    bucle se DECLARA en el C (`for (int64_t i = 0; ...)`) y se registra en
    ctx._variables (paridad visitar_declaracion L97). Antes se emitia
    `for (i = 0; ...)` sin declarar -> gcc 'i undeclared' (desvio H-R29-2)."""
    init_code = ""
    var_name = None
    var_tipo_syn = None
    if nodo.inicializacion:
        if hasattr(nodo.inicializacion, 'nombre'):
            var_name = nodo.inicializacion.nombre
            expr_init = nodo.inicializacion.expresion
            if expr_init is not None:
                var_tipo_syn = tipo_de_expr(ctx, expr_init)
                init_code = f"{var_name} = {expr_a_c(ctx, expr_init)}"
            else:
                init_code = f"{var_name} = 0"
        else:
            init_code = expr_a_c(ctx, nodo.inicializacion)
    cond_code = expr_a_c(ctx, nodo.condicion) if nodo.condicion else "1"
    inc_code = ""
    if nodo.incremento:
        if hasattr(nodo.incremento, 'nombre') and hasattr(nodo.incremento, 'expresion'):
            inc_code = (
                f"{nodo.incremento.nombre}"
                f" = {expr_a_c(ctx, nodo.incremento.expresion)}"
            )
        else:
            inc_code = expr_a_c(ctx, nodo.incremento)
    if var_name and var_tipo_syn:
        ctx.write_line(f"for ({ctx.traducir_tipo_c(var_tipo_syn)} {init_code}; "
                       f"{cond_code}; {inc_code}) {{")
        if var_name not in ctx._variables:
            ctx._variables[var_name] = var_tipo_syn
    else:
        ctx.write_line(f"for ({init_code}; {cond_code}; {inc_code}) {{")
    ctx.inc_indent()
    ctx.push_scope()
    for s in nodo.cuerpo:
        _visitar_stmt(ctx, s)
    ctx.pop_scope()
    ctx.dec_indent()
    ctx.write_line("}")


def visitar_coincidir(ctx: GeneratorContext, nodo: NodoCoincidir):
    """Genera código C para match/coincidir (switch sobre ADT tag o valor primitivo)."""
    expr = expr_a_c(ctx, nodo.expresion)
    tipo_syn = tipo_de_expr(ctx, nodo.expresion)  # Synapse type
    tipo_c = ctx.traducir_tipo_c(tipo_syn)  # C type for declaration
    # H-R90-6: tipos primitivos no tienen .tag — switch sobre el valor directo
    PRIMITIVOS = {'entero', 'decimal', 'booleano', 'texto', 'cadena',
                  'int', 'float', 'logico', 'real', 'flotante'}
    es_primitivo = tipo_syn in PRIMITIVOS
    ctx.write_line("{")
    ctx.inc_indent()
    var_temp = f"_match_{abs(hash(str(id(nodo))))}"
    ctx.write_line(f"{tipo_c} {var_temp} = {expr};")
    if es_primitivo:
        ctx.write_line(f"switch ({var_temp}) {{")
    else:
        ctx.write_line(f"switch ({var_temp}.tag) {{")
    ctx.inc_indent()
    for caso in nodo.casos:
        if not isinstance(caso, NodoCaso):
            continue
        patron = caso.patron
        if patron == "_":
            ctx.write_line("default:")
        elif es_primitivo:
            # H-R90-6: patron literal como case value directo
            ctx.write_line(f"case {patron}:")
        else:
            tag = patron.split("(")[0] if "(" in patron else patron
            # F1.2: el tag del ADT Opcion es TAG_ALGUNO (Manual 2 §4.2 / encabezado
            # emite #define TAG_ALGUNO 0); 'algun'.upper() daría TAG_ALGUN inexistente.
            _TAG_MAP = {
                'ok': 'TAG_OK', 'err': 'TAG_ERR',
                'algun': 'TAG_ALGUNO', 'ninguno': 'TAG_NINGUNO',
            }
            tag_c = _TAG_MAP.get(tag, f"TAG_{tag.upper()}")
            ctx.write_line(f"case {tag_c}:")
        ctx.write_line("{")  # Wrap body in {} to allow declarations after label
        ctx.inc_indent()
        ctx.push_scope()
        if "(" in patron and ")" in patron:
            var_name = patron.split("(")[1].rstrip(")")
            # R17: el miembro del union es el nombre del CONSTRUCTOR del tag
            # (ok/err/algun) y el tipo ligado se resuelve con la instancia
            # (campos sustituidos) o el ADT genérico. Paridad con el codegen
            # nativo (nodos_flujo.syn NodoCoincidir: `.dato.<tag>`).
            bound_type = 'int64_t'  # fallback
            campo_dato = 'valor'  # fallback (solo si no hay campos resolubles)
            # FIX R17: el ternario previo devolvía '' cuando tipo_syn no
            # empezaba con 'struct ' (todos los tipos Synapse) -> lookup
            # muerto -> `.dato.valor` en C inválido para todo match sobre ADT.
            adt_name = tipo_syn.replace("struct ", "")
            # D-2: normalizar la base de una instanciación (Resultado<entero,texto>
            # -> Resultado) para localizar el ADT genérico en _estructuras y usar
            # los tipos concretos sustituidos (monomorfización).
            adt_base = adt_name.split('<')[0] if '<' in adt_name else adt_name
            inst_campos = None
            if '<' in adt_name and adt_name.endswith('>'):
                _b, _, _r = adt_name.partition('<')
                # R17: usar _dividir_args_tipo (split depth-aware, R16) y NO
                # split(',') naive — rompia los anidados
                # (Resultado<Resultado<entero,texto>,texto> -> 3 args) y la
                # instancia no resolvia -> binding del generico (void*).
                args = tuple(_dividir_args_tipo(_r[:-1]))
                inst = ctx._instancias_adt.get((_b, args))
                if inst:
                    inst_campos = inst.get('campos')
            campos_adt = (inst_campos or
                          ctx._estructuras.get(adt_base, {}).get('campos', []))
            bound_syn = None
            for cname, ctype in campos_adt:
                if cname == 'tag':
                    continue
                if campo_dato == 'valor':
                    campo_dato = cname  # default: primer campo no-tag
                if cname == tag:
                    campo_dato = cname  # campo correcto del tag (ok/err/algun)
                    bound_type = ctx.traducir_tipo_c(ctype)
                    bound_syn = ctype
                    break
            ctx.write_line(f"{bound_type} {var_name} = {var_temp}.dato.{campo_dato};")
            # R28: registrar la variable ligada del caso (paridad nativo
            # nodos_flujo.syn — antes el S1 no la registraba en ctx._variables
            # y un `coincidir` ANIDADO sobre la variable ligada (tipo ADT)
            # caia a int64_t -> C invalido). Solo instancias concretas.
            if inst_campos is not None and bound_syn is not None:
                ctx._variables[var_name] = bound_syn
        if hasattr(caso, 'cuerpo') and caso.cuerpo:
            for s in caso.cuerpo:
                _visitar_stmt(ctx, s)
        ctx.write_line("break;")
        ctx.pop_scope()
        ctx.dec_indent()
        ctx.write_line("}")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.dec_indent()
    ctx.write_line("}")
