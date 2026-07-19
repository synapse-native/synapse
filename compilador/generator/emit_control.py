"""
Generación de código C para estructuras de control de flujo.
Cada función recibe (ctx, nodo) siguiendo el patrón Composición + Contexto.
Usa import tardío para evitar dependencias circulares con _visitar().
"""

from compilador.ast_nodes import (
    SentenciaSi, SentenciaMientras, SentenciaPara,
    NodoCoincidir, NodoCaso,
)
from .context import GeneratorContext
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
            ctx.write_line(f"case TAG_{tag.upper()}:")
        ctx.write_line("{")  # Wrap body in {} to allow declarations after label
        ctx.inc_indent()
        ctx.push_scope()
        if "(" in patron and ")" in patron:
            var_name = patron.split("(")[1].rstrip(")")
            # Look up field type + actual union field name from ADT struct
            bound_type = 'int'  # fallback
            campo_dato = 'valor'  # default fallback field name
            adt_name = tipo_syn.replace("struct ", "") if tipo_syn.startswith("struct ") else ""
            if adt_name in ctx._estructuras:
                for cname, ctype in ctx._estructuras[adt_name].get('campos', []):
                    if cname != 'tag':
                        if campo_dato == 'valor':
                            campo_dato = cname  # first non-tag field as default
                        if cname == var_name:
                            campo_dato = cname
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
