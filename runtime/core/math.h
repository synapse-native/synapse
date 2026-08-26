// runtime/core/math.h — Math module declarations for Syquex standard library
// Manual 3 §12.1: lib/math.syq

#ifndef SYNAPSE_RT_MATH_H
#define SYNAPSE_RT_MATH_H

#include <stdint.h>

// §12.1 — Potencia y raíz
double _syn_potencia(double base, double exponente);
double _syn_sqrt(double x);

// §12.1 — Trigonometría
double _syn_sen(double x);
double _syn_cos(double x);
double _syn_tan(double x);

// §12.1 — Redondeo
int64_t _syn_round(double x);
int64_t _syn_ceil(double x);
int64_t _syn_floor(double x);

// §12.1 — Logaritmos
double _syn_log(double x);

#endif // SYNAPSE_RT_MATH_H
