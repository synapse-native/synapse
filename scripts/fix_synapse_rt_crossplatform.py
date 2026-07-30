#!/usr/bin/env python3
"""Synapse Cross-Platform Fix v7 — clean fix for CI release_matrix.yml"""

import sys

# ======================================================================
# Fix 1: tweetnacl.c — randombytes extern declaration
# ======================================================================
with open("tweetnacl.c", "r", encoding="utf-8") as f:
    tn = f.read()

old_rb = "//extern void randombytes(u8 *,u64);"
new_rb = "extern void randombytes(unsigned char* x, unsigned long long xlen);"

if old_rb in tn:
    tn = tn.replace(old_rb, new_rb, 1)
    with open("tweetnacl.c", "w", encoding="utf-8") as f:
        f.write(tn)
    print("[FIX] tweetnacl.c: randombytes declaration uncommented")
elif new_rb in tn:
    print("[OK] tweetnacl.c: randombytes already declared")
else:
    print("[WARN] tweetnacl.c: randombytes pattern not found")

# ======================================================================
# Fix 2: synapse_rt.c — Remove redundant stubs from #else block
# ======================================================================
with open("synapse_rt.c", "r", encoding="utf-8") as f:
    rt = f.read()
original_rt = rt

# The committed version wraps the SIMD block from 
# "// --- SIMD: llenar_tensor_constante..." to "// --- std.math (alias) ---"
# The #else block has stubs including _simd_detectar, _syn_simd_disponible, _syn_simd_tipo.
# These three functions are ALSO defined OUTSIDE the arch guard (original definitions),
# causing redefinition errors on ARM64.
#
# Fix: Remove the 3 stub definitions from the #else block.
# The originals are safe because CPUID is already guarded with arch check.

stub_patterns = [
    # Remove _simd_detectar stub
    (
        "\nvoid _simd_detectar(void) {\n"
        "    if (_simd_habilitado >= 0) return;\n"
        "    _simd_habilitado = 0;\n"
        "    _simd_tipo_str = \"NONE\";\n"
        "}\n",
        ""
    ),
    # Remove _syn_simd_disponible stub  
    (
        "\nint _syn_simd_disponible(void) { return 0; }\n",
        ""
    ),
    # Remove _syn_simd_tipo stub
    (
        "\nCadenaSegura _syn_simd_tipo(void) { return (CadenaSegura){ .longitud = 4, .datos = \"NONE\" }; }\n",
        ""
    ),
]

for old, new in stub_patterns:
    count = rt.count(old)
    if count >= 1:
        rt = rt.replace(old, new, 1)
        print(f"[FIX] Removed 1 redundant stub definition ({count} remaining)")
    elif count == 0:
        # Try without leading newline
        alt_old = old.lstrip('\n')
        if alt_old in rt:
            rt = rt.replace(alt_old, "", 1)
            print(f"[FIX] Removed 1 redundant stub (alt match)")

# After removing stubs, we might have double-newlines or empty #else blocks
# Clean up: replace `#else\n\n#endif` with just `#endif`
rt = rt.replace("#else\n\n#endif", "#endif", 10)
rt = rt.replace("#else\n#endif", "#endif", 10)

if rt != original_rt:
    with open("synapse_rt.c", "w", encoding="utf-8") as f:
        f.write(rt)
    print("[FIX] synapse_rt.c: redundant stubs removed")
else:
    print("[OK] synapse_rt.c: no changes needed")

print("\nDone.")
