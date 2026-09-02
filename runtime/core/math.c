// cumple Manual 6 3: math runtime
// runtime/core/math.c — Math module for Syquex standard library
// Manual 3 §12.1: lib/math.syq — Matemáticas y estadísticas
// Implements externs: _syn_potencia, _syn_sqrt, _syn_sen, _syn_cos,
//   _syn_tan, _syn_round, _syn_ceil, _syn_floor, _syn_log
// Compilar: gcc -c runtime/core/math.c -o math.o -lm

#include <math.h>
#include <stdint.h>

// ============================================================
// §12.1 — Potencia y raíz
// ============================================================

double _syn_potencia(double base, double exponente) {
    return pow(base, exponente);
}

double _syn_sqrt(double x) {
    return sqrt(x);
}

// ============================================================
// §12.1 — Trigonometría
// ============================================================

double _syn_sen(double x) {
    return sin(x);
}

double _syn_cos(double x) {
    return cos(x);
}

double _syn_tan(double x) {
    return tan(x);
}

// ============================================================
// §12.1 — Redondeo
// ============================================================

int64_t _syn_round(double x) {
    return (int64_t)round(x);
}

int64_t _syn_ceil(double x) {
    return (int64_t)ceil(x);
}

int64_t _syn_floor(double x) {
    return (int64_t)floor(x);
}

// ============================================================
// §12.1 — Logaritmos
// ============================================================

double _syn_log(double x) {
    return log(x);
}
