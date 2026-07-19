"""
Generación de código C para contratos (requiere/garantiza).
Fase 2: inyección de asserts y validación de contratos en tiempo de desarrollo.
"""

from .context import GeneratorContext


def inject_requires(ctx: GeneratorContext, expr_c: str):
    """Inyecta assert para contrato 'requiere'."""
    ctx.write_line("#ifndef SYNAPSE_RELEASE")
    ctx.write_line(f'assert(({expr_c}) && "Fallo en contrato: requiere");')
    ctx.write_line("#endif")


def inject_ensures(ctx: GeneratorContext, expr_c: str):
    """Inyecta assert para contrato 'garantiza'."""
    ctx.write_line("#ifndef SYNAPSE_RELEASE")
    ctx.write_line(
        f'assert(({expr_c}) && "Fallo en contrato: garantiza");'
    )
    ctx.write_line("#endif")


def emit_contract_header(ctx: GeneratorContext):
    """Emite cabecera de contratos (definiciones de macros de aserción)."""
    ctx.write_line(
        "// --- Contratos (requiere/garantiza) ---"
    )
    ctx.write_line("#ifdef SYNAPSE_RELEASE")
    ctx.write_line("#define assert_contrato(expr, msg) ((void)0)")
    ctx.write_line("#else")
    ctx.write_line(
        '#define assert_contrato(expr, msg) \\'
    )
    ctx.write_line(
        '    do { if (!(expr)) { \\'
    )
    ctx.write_line(
        '        fprintf(stderr, "CONTRATO: %s en %%s:%%d\\\\n", \\'
    )
    ctx.write_line(
        '                msg, __FILE__, __LINE__); \\'
    )
    ctx.write_line("        exit(1); }} while(0)")
    ctx.write_line("#endif")
    ctx.write_line("")
