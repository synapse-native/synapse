"""Generación de código C para contratos (requiere/garantiza).

// cumple Manual 2 §5.1/§5.2 (ME r192_deuda_barrido): toda cláusula
// `requiere` / `garantiza` se emite como `assert_contrato(expr, msg)` en el
// cuerpo C generado; el mensaje es literal "Fallo en contrato: requiere" /
// "Fallo en contrato: garantiza" (convención de paridad con los emisores
// nativos en nucleo/generador/funciones.syn y nodos_flujo.syn, oráculo E2E).
// cumple Manual 2 §5.3: modo release define NDEBUG en el C generado — las aserciones
// se eliminan (costo cero); assert() ya se reduce a ((void)0) preprocesado.
// S1 ya emite #include <assert.h> (generator.py L754).
"""


def emit_contract_header(ctx):
    """Emite cabecera de contratos: macro única que delega en assert()."""
    ctx.write_line("// --- Contratos (requiere/garantiza) — cumple Manual 2 §5.1/§5.2 (ME r192) ---")
    ctx.write_line("// cumple Manual 2 §5.3: en release NDEBUG elimina la aserción (costo cero).")
    ctx.write_line('#define assert_contrato(expr, msg) assert((expr) && msg)')
    ctx.write_line("")
