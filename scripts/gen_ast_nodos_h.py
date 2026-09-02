#!/usr/bin/env python3
"""
gen_ast_nodos_h.py — Regenera runtime/core/ast_nodos.h desde parser_constantes.syn.

Fuente de verdad: nucleo/parser_constantes.syn (TokenID T_* y NodoID NODO_*).
Header canónico C: runtime/core/ast_nodos.h

Uso:
    python scripts/gen_ast_nodos_h.py            # regenera el header
    python scripts/gen_ast_nodos_h.py --check      # verifica sin escribir (CI)

Este script elimina el hardcodeo de valores en generator.py: el header es
la representación C de parser_constantes.syn, y el generador emite
#include "runtime/core/ast_nodos.h" en lugar de bloques #ifndef duplicados.
"""
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYN_SOURCE = os.path.join(RAIZ, "nucleo", "parser_constantes.syn")
C_HEADER = os.path.join(RAIZ, "runtime", "core", "ast_nodos.h")

RE_CONSTANTE = re.compile(r"^\s*constante\s+(T_[A-Z_]+|NODO_[A-Z_]+)\s*=\s*(\d+)\s*(?:\#.*)?$")


def parse_syn(path):
    """Extrae OrderedDict de constantes T_*/NODO_* desde parser_constantes.syn."""
    vals = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = RE_CONSTANTE.match(line)
            if m:
                vals[m.group(1)] = int(m.group(2))
    return vals


def format_value(val):
    return f"({val}LL)"


def group_constants(vals):
    tokens = {k: v for k, v in vals.items() if k.startswith("T_")}
    nodos = {k: v for k, v in vals.items() if k.startswith("NODO_")}
    return tokens, nodos


def generate_header(vals):
    tokens, nodos = group_constants(vals)
    lines = [
        "#ifndef AST_NODOS_H",
        "#define AST_NODOS_H",
        "// cumple Manual 2 3: tabla canónica de tokens AST",
        "// cumple Manual 2 7: tabla canónica de nodos AST",
        "",
        "/*",
        " * ast_nodos.h — Tabla canónica de constantes AST para el runtime C.",
        " *",
        " * Fuente única de verdad: nucleo/parser_constantes.syn",
        " *   - TokenID (T_*): Manual 2 §3 / Manual 2 §2.3",
        " *   - NodoID (NODO_*): Manual 2 §7.2 (extracto ilustrativo) / Manual 2 §7.3",
        " *",
        " * ABI v1 CONGELADA (F22/R85, nucleo/ast_abi.syn).",
        " * Los valores del Manual 2 §7.2 \"(Extracto)\" son ILUSTRATIVOS;",
        " * los valores canónicos vigentes están en parser_constantes.syn.",
        " *",
        " * AUTO-VERIFICADO por tests/unit/test_ast_nodos_consistency.py",
        " * NO EDITAR MANUALMENTE — regenere con scripts/gen_ast_nodos_h.py.",
        " *",
        " * Incluir como:  #include \"runtime/core/ast_nodos.h\"",
        " */",
        "",
        "/* === Token ID constants (Manual 2 §3) === */",
    ]
    for name, val in tokens.items():
        lines.append(f"#define {name:<20} {format_value(val)}")
    lines.append("")
    lines.append("/* === AST node type constants (Manual 2 §7.2/§7.3) === */")
    for name, val in nodos.items():
        lines.append(f"#define {name:<24} {format_value(val)}")
    lines.append("")
    lines.append("#endif /* AST_NODOS_H */")
    return "\n".join(lines) + "\n"


def main():
    if not os.path.isfile(SYN_SOURCE):
        print(f"ERROR: fuente de verdad no encontrada: {SYN_SOURCE}", file=sys.stderr)
        return 1
    vals = parse_syn(SYN_SOURCE)
    if not vals:
        print("ERROR: no se parsearon constantes de parser_constantes.syn", file=sys.stderr)
        return 1

    header = generate_header(vals)
    tokens, nodos = group_constants(vals)
    print(f"parser_constantes.syn: {len(vals)} constantes ({len(tokens)} T_*, {len(nodos)} NODO_*)")

    if "--check" in sys.argv:
        existing = ""
        if os.path.isfile(C_HEADER):
            with open(C_HEADER, encoding="utf-8") as f:
                existing = f.read()
        if existing != header:
            print(f"FALLÓ --check: {C_HEADER} está desactualizado.", file=sys.stderr)
            return 1
        print(f"[OK] {C_HEADER} está sincronizado ({len(vals)} constantes)")
        return 0

    os.makedirs(os.path.dirname(C_HEADER), exist_ok=True)
    with open(C_HEADER, "w", encoding="utf-8") as f:
        f.write(header)
    print(f"[OK] {C_HEADER} regenerado ({len(vals)} constantes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
