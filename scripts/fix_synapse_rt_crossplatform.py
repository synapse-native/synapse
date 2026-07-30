#!/usr/bin/env python3
"""Synapse Runtime Cross-Platform Fix v5 - SIMD block wrapper"""

SYNAPSE_RT = "synapse_rt.c"

def main():
    with open(SYNAPSE_RT, "r", encoding="utf-8") as f:
        content = f.read()
    original = content
    changes = []

    # =====================================================================
    # FIX 1: Guard CPUID in _simd_detectar()
    # =====================================================================
    # Already applied via git history — verify
    pattern1 = (
        '#if defined(__GNUC__) || defined(__clang__)\n'
        '    __asm__ volatile(\n'
        '        "cpuid"\n'
        '        : "=a"(eax), "=b"(ebx), "=c"(ecx), "=d"(edx)\n'
        '        : "a"(eax)\n'
        '    );\n'
        '#else\n'
        '    // Fallback: asumir no SIMD en compiladores desconocidos\n'
        '    _simd_habilitado = 0;\n'
        '    _simd_tipo_str = "NONE";\n'
        '    return;\n'
        '#endif'
    )
    arch1 = (
        '#if defined(__x86_64__) || defined(__i386__)\n'
        '    #if defined(__GNUC__) || defined(__clang__)\n'
        '        __asm__ volatile(\n'
        '            "cpuid"\n'
        '            : "=a"(eax), "=b"(ebx), "=c"(ecx), "=d"(edx)\n'
        '            : "a"(eax)\n'
        '        );\n'
        '    #else\n'
        '        _simd_habilitado = 0;\n'
        '        _simd_tipo_str = "NONE";\n'
        '        return;\n'
        '    #endif\n'
        '#else\n'
        '    _simd_habilitado = 0;\n'
        '    _simd_tipo_str = "NONE";\n'
        '    return;\n'
        '#endif'
    )
    if pattern1 in content:
        content = content.replace(pattern1, arch1, 1)
        changes.append("Fix 1: CPUID leaf 1 arch-guarded")
    
    pattern2 = (
        '#if defined(__GNUC__) || defined(__clang__)\n'
        '        __asm__ volatile(\n'
        '            "cpuid"\n'
        '            : "=a"(eax), "=b"(ebx), "=c"(ecx), "=d"(edx)\n'
        '            : "a"(eax), "c"(ecx)\n'
        '        );\n'
        '#endif'
    )
    arch2 = (
        '#if defined(__x86_64__) || defined(__i386__)\n'
        '        #if defined(__GNUC__) || defined(__clang__)\n'
        '            __asm__ volatile(\n'
        '                "cpuid"\n'
        '                : "=a"(eax), "=b"(ebx), "=c"(ecx), "=d"(edx)\n'
        '                : "a"(eax), "c"(ecx)\n'
        '            );\n'
        '        #endif\n'
        '#endif'
    )
    if pattern2 in content:
        content = content.replace(pattern2, arch2, 1)
        changes.append("Fix 2: CPUID leaf 7 arch-guarded")

    # =====================================================================
    # FIX 3: Guard SIMD functions — wrap ENTIRE block with arch guard
    # =====================================================================
    # Find boundaries of the SIMD implementation block
    simd_start_marker = "// --- SIMD: llenar_tensor_constante (vectorizado con SSE) ---"
    simd_end_marker = "// --- std.math (alias) ---"
    
    simd_start = content.find(simd_start_marker)
    simd_end = content.find(simd_end_marker)
    
    if simd_start != -1 and simd_end != -1 and simd_start < simd_end:
        before = content[:simd_start]
        simd_block = content[simd_start:simd_end]
        after = content[simd_end:]
        
        # Create stubs for non-x86
        stubs = '''
#else
// Non-x86 architecture stubs (SIMD not available — _simd_habilitado=0 ensures these are never called)
#include <unistd.h>

void _simd_detectar(void) {
    if (_simd_habilitado >= 0) return;
    _simd_habilitado = 0;
    _simd_tipo_str = "NONE";
}

int _syn_simd_disponible(void) { return 0; }
CadenaSegura _syn_simd_tipo(void) { return (CadenaSegura){ .longitud = 4, .datos = "NONE" }; }

void _syn_simd_llenar_tensor_constante(Tensor t, float valor) {
    _simd_detectar();
    for (uint32_t _i = 0; _i < t.filas * t.columnas; _i++) t.datos[_i] = valor;
}

Tensor _syn_simd_multiplicar_matrices(Tensor a, Tensor b) {
    Tensor r = {0}; return r;  // never called on non-x86
}

void _syn_simd_multiplicar_matrices_transpuesta_b(Tensor a, Tensor b, Tensor salida) {
    (void)a; (void)b; (void)salida;
}

void _syn_simd_rmsnorm(Tensor salida, Tensor entrada, Tensor peso_normalizacion, float epsilon) {
    _simd_detectar();
    uint32_t n = entrada.columnas;
    float suma_cuadrados = 0.0f;
    for (uint32_t _i = 0; _i < n; _i++) { float v = entrada.datos[_i]; suma_cuadrados += v * v; }
    float rms = sqrtf(suma_cuadrados / (float)n + epsilon);
    for (uint32_t _i = 0; _i < n; _i++) salida.datos[_i] = (entrada.datos[_i] / rms) * peso_normalizacion.datos[_i];
}

void _syn_simd_silu(Tensor salida, Tensor entrada) {
    uint32_t n = entrada.columnas;
    for (uint32_t _i = 0; _i < n; _i++) {
        float x = entrada.datos[_i];
        salida.datos[_i] = x / (1.0f + expf(-x));
    }
}

void _syn_simd_softmax_escalado(Tensor tensor, float factor_escala) {
    _simd_detectar();
    uint32_t filas = tensor.filas;
    uint32_t cols = tensor.columnas;
    for (uint32_t _f = 0; _f < filas; _f++) {
        float* fila = tensor.datos + _f * cols;
        float max_val = -1e30f;
        for (uint32_t _c = 0; _c < cols; _c++) { float v = fila[_c] * factor_escala; if (v > max_val) max_val = v; }
        float suma = 0.0f;
        for (uint32_t _c = 0; _c < cols; _c++) { float e = expf(fila[_c] * factor_escala - max_val); fila[_c] = e; suma += e; }
        if (suma > 0.0f) { for (uint32_t _c = 0; _c < cols; _c++) fila[_c] /= suma; }
    }
}
#endif
'''
        # Wrap the block: #if x86...original...#else...stubs...#endif
        wrapped = f'#if defined(__x86_64__) || defined(__i386__)\n{simd_block}{stubs}'
        content = before + wrapped + after
        changes.append("Fix 3: SIMD implementation block wrapped with arch guard + stubs")
    else:
        changes.append(f"WARN: SIMD markers not found ({simd_start}, {simd_end})")

    # =====================================================================
    # FIX 4: Guard DWORD/GetCurrentDirectoryA
    # =====================================================================
    dword_line = '    DWORD len = GetCurrentDirectoryA(4096, buf);'
    if dword_line in content:
        content = content.replace(
            dword_line,
            '#ifdef _WIN32\n    DWORD len = GetCurrentDirectoryA(4096, buf);\n#else\n    char* _cwd = getcwd(buf, 4096);\n    int len = _cwd ? (int)strlen(buf) : 0;\n#endif',
            1
        )
        changes.append("Fix 4: GetCurrentDirectoryA -> _WIN32 guarded")

    # =====================================================================
    # FIX 5: Guard Sleep(DWORD)
    # =====================================================================
    sleep_line = '        Sleep((DWORD)ms);'
    if sleep_line in content:
        content = content.replace(
            sleep_line,
            '#ifdef _WIN32\n        Sleep((DWORD)ms);\n#else\n        struct timespec ts = { .tv_sec = ms / 1000, .tv_nsec = (ms % 1000) * 1000000 };\n        nanosleep(&ts, NULL);\n#endif',
            1
        )
        changes.append("Fix 5: Sleep(DWORD) -> _WIN32 + nanosleep")

    # Save
    if original != content:
        with open(SYNAPSE_RT, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"OK synapse_rt.c saved ({len(changes)} changes)")
        for c in changes:
            print(f"  {c}")
    else:
        print("NO CHANGES — all patterns may already be applied")
        import sys; sys.exit(1)

if __name__ == "__main__":
    main()
