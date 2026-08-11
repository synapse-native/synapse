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
    """Genera código C para for."""
    init_code = ""
    if nodo.inicializacion:
        if hasattr(nodo.inicializacion, 'nombre'):
            init_code = (
                f"{nodo.inicializacion.nombre}"
                f" = {expr_a_c(ctx, nodo.inicializacion.expresion)}"
            )
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
    ctx.write_line(f"for ({init_code}; {cond_code}; {inc_code}) {{")
    ctx.inc_indent()
    ctx.push_scope()
    for s in nodo.cuerpo:
        _visitar_stmt(ctx, s)
    ctx.pop_scope()
    ctx.dec_indent()
    ctx.write_line("}")


def visitar_coincidir(ctx: GeneratorContext, nodo: NodoCoincidir):
    """Genera código C para match/coincidir (switch sobre ADT tag)."""
    expr = expr_a_c(ctx, nodo.expresion)
    tipo_syn = tipo_de_expr(ctx, nodo.expresion)  # Synapse type
    tipo_c = ctx.traducir_tipo_c(tipo_syn)  # C type for declaration
    ctx.write_line("{")
    ctx.inc_indent()
    var_temp = f"_match_{abs(hash(str(id(nodo))))}"
    ctx.write_line(f"{tipo_c} {var_temp} = {expr};")
    ctx.write_line(f"switch ({var_temp}.tag) {{")
    ctx.inc_indent()
    for caso in nodo.casos:
        if not isinstance(caso, NodoCaso):
            continue
        patron = caso.patron
        if patron == "_":
            ctx.write_line("default:")
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
            for cname, ctype in campos_adt:
                if cname == 'tag':
                    continue
                if campo_dato == 'valor':
                    campo_dato = cname  # default: primer campo no-tag
                if cname == tag:
                    campo_dato = cname  # campo correcto del tag (ok/err/algun)
                    bound_type = ctx.traducir_tipo_c(ctype)
                    break
            ctx.write_line(f"{bound_type} {var_name} = {var_temp}.dato.{campo_dato};")
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
