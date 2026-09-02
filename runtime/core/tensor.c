// cumple Manual 6 §3: tensor runtime
// synapse_rt_tensor.c — Tensor math + SIMD module for Synapse runtime
// Extracted from synapse_rt.c (std.math, std.tensor, std.simd, std.mem).
// Deuda D-9(d): segundo corte del monolito synapse_rt.c (patron io.c,
// F3-1/F3-2). Texto de las funciones BYTE-IDENTICO al original.
// Compilar: gcc -c synapse_rt_tensor.c -o synapse_rt_tensor.o

#include "synapse_rt_types.h"
#include "runtime/core/tensor.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>

// --- std.math ---
Tensor crear_tensor(int filas, int columnas) {
    Tensor r;
    r.filas = filas;
    r.columnas = columnas;
    r.es_mapeado = 0;
    r.datos = _pool_malloc(filas * columnas * sizeof(float));
    memset(r.datos, 0, filas * columnas * sizeof(float));
    return r;
}

Tensor suma_tensor(Tensor a, Tensor b) {
    if (a.filas != b.filas || a.columnas != b.columnas) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: dimensiones incompatibles en suma_tensor()\n");
        return (Tensor){ .filas = 0, .columnas = 0, .datos = NULL };
    }
    Tensor r;
    r.filas = a.filas;
    r.columnas = a.columnas;
    r.es_mapeado = 0;
    r.datos = _pool_malloc(r.filas * r.columnas * sizeof(float));
    for (uint32_t _i = 0; _i < r.filas * r.columnas; _i++) {
        r.datos[_i] = a.datos[_i] + b.datos[_i];
    }
    if (!a.es_mapeado) { pool_free(a.datos); }
    if (!b.es_mapeado) { pool_free(b.datos); }
    return r;
}

Tensor producto_punto(Tensor a, Tensor b) {
    if (a.columnas != b.filas) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: dimensiones incompatibles en producto_punto()\n");
        return (Tensor){ .filas = 0, .columnas = 0, .datos = NULL };
    }
    Tensor r;
    r.filas = a.filas;
    r.columnas = b.columnas;
    r.es_mapeado = 0;
    r.datos = (float*)calloc(r.filas * r.columnas, sizeof(float));
    for (uint32_t _i = 0; _i < r.filas; _i++) {
        for (uint32_t _j = 0; _j < r.columnas; _j++) {
            float _sum = 0;
            for (uint32_t _k = 0; _k < a.columnas; _k++) {
                _sum += a.datos[_i * a.columnas + _k] * b.datos[_k * b.columnas + _j];
            }
            r.datos[_i * r.columnas + _j] = _sum;
        }
    }
    if (!a.es_mapeado) { pool_free(a.datos); }
    if (!b.es_mapeado) { pool_free(b.datos); }
    return r;
}

Tensor relu(Tensor a) {
    Tensor r;
    r.filas = a.filas;
    r.columnas = a.columnas;
    r.es_mapeado = 0;
    r.datos = _pool_malloc(a.filas * a.columnas * sizeof(float));
    for (uint32_t _i = 0; _i < a.filas * a.columnas; _i++) {
        r.datos[_i] = (a.datos[_i] > 0) ? a.datos[_i] : 0.0f;
    }
    if (!a.es_mapeado) { pool_free(a.datos); }
    return r;
}

// --- std.tensor (cache-optimized + auto-SIMD bridge) ---
static int _simd_habilitado = -1;  // -1 = no detectado aun

// Todas las funciones escalares consultan _simd_habilitado en runtime
// y delegan a la variante SIMD cuando el hardware lo soporta.
// El bridge es transparente: std.modelo llama a _syn_rmsnorm sin saber
// si la aceleracion esta activa. La semantica de ownership se preserva
// porque las variantes escalar y SIMD tienen el mismo comportamiento
// de pool_free/pasaje por copia.

// Forward declarations: funciones SIMD definidas mas abajo en este archivo,
// pero llamadas por las funciones bridge que estan antes en el orden de compilacion.
// NOTA: NO usar 'static' — las bibliotecas std declaran estas funciones como extern
// y el codigo C generado las referencia directamente desde std/tensor.syn.
void _simd_detectar(void);
int _syn_simd_disponible(void);
CadenaSegura _syn_simd_tipo(void);
void _syn_simd_llenar_tensor_constante(Tensor t, float valor);
Tensor _syn_simd_multiplicar_matrices(Tensor a, Tensor b);
void _syn_simd_multiplicar_matrices_transpuesta_b(Tensor a, Tensor b, Tensor salida);
void _syn_simd_rmsnorm(Tensor salida, Tensor entrada, Tensor peso_normalizacion, float epsilon);
void _syn_simd_silu(Tensor salida, Tensor entrada);
void _syn_simd_softmax_escalado(Tensor tensor, float factor_escala);

void _syn_llenar_tensor_constante(Tensor t, float valor) {
    _simd_detectar();
    if (_simd_habilitado > 0) {
        _syn_simd_llenar_tensor_constante(t, valor);
        return;
    }
    for (int _i = 0; _i < (int)(t.filas * t.columnas); _i++) {
        t.datos[_i] = valor;
    }
}

Tensor _syn_multiplicar_matrices(Tensor a, Tensor b) {
    _simd_detectar();
    if (_simd_habilitado > 0) {
        return _syn_simd_multiplicar_matrices(a, b);
    }
    if (a.columnas != b.filas) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: dimensiones incompatibles en multiplicar_matrices()\n");
        return (Tensor){ .filas = 0, .columnas = 0, .datos = NULL };
    }
    Tensor r;
    r.filas = a.filas;
    r.columnas = b.columnas;
    r.es_mapeado = 0;
    r.datos = (float*)_pool_malloc(r.filas * r.columnas * sizeof(float));
    memset(r.datos, 0, r.filas * r.columnas * sizeof(float));
    for (int _i = 0; _i < (int)r.filas; _i++) {
        for (int _k = 0; _k < (int)a.columnas; _k++) {
            float _a_ik = a.datos[_i * a.columnas + _k];
            for (int _j = 0; _j < (int)r.columnas; _j++) {
                r.datos[_i * r.columnas + _j] += _a_ik * b.datos[_k * b.columnas + _j];
            }
        }
    }
    if (!a.es_mapeado) { pool_free(a.datos); }
    if (!b.es_mapeado) { pool_free(b.datos); }
    return r;
}

// --- std.tensor (Transformer primitives) ---
// extraer_fila: copia una fila de tabla_embeddings(indice_token, :) hacia salida(1, :)
// Sin SIMD equivalente (es memcpy puro)
void _syn_extraer_fila(Tensor salida, Tensor tabla_embeddings, int indice_token) {
    if (indice_token < 0 || indice_token >= (int)tabla_embeddings.filas) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: indice_token %d fuera de rango [0, %u)\n",
                indice_token, tabla_embeddings.filas);
        return;
    }
    uint32_t n = salida.columnas;
    float* src = tabla_embeddings.datos + indice_token * tabla_embeddings.columnas;
    memcpy(salida.datos, src, n * sizeof(float));
}

// rmsnorm: salida[i] = entrada[i] / sqrt(mean(entrada^2) + epsilon) * peso_normalizacion[i]
// Bridge SIMD: mismo ownership (pasaje por copia, sin pool_free)
void _syn_rmsnorm(Tensor salida, Tensor entrada, Tensor peso_normalizacion, float epsilon) {
    _simd_detectar();
    if (_simd_habilitado > 0) {
        _syn_simd_rmsnorm(salida, entrada, peso_normalizacion, epsilon);
        return;
    }
    uint32_t n = entrada.columnas;
    float suma_cuadrados = 0.0f;
    for (uint32_t _i = 0; _i < n; _i++) {
        float v = entrada.datos[_i];
        suma_cuadrados += v * v;
    }
    float rms = sqrtf(suma_cuadrados / (float)n + epsilon);
    for (uint32_t _i = 0; _i < n; _i++) {
        salida.datos[_i] = (entrada.datos[_i] / rms) * peso_normalizacion.datos[_i];
    }
}

// silu (Swish): salida[i] = entrada[i] / (1 + exp(-entrada[i]))
// Bridge SIMD: mismo ownership (pasaje por copia, sin pool_free)
void _syn_silu(Tensor salida, Tensor entrada) {
    _simd_detectar();
    if (_simd_habilitado > 0) {
        _syn_simd_silu(salida, entrada);
        return;
    }
    uint32_t n = entrada.columnas;
    for (uint32_t _i = 0; _i < n; _i++) {
        float x = entrada.datos[_i];
        salida.datos[_i] = x / (1.0f + expf(-x));
    }
}

// --- std.tensor (Attention primitives) ---
// rope: aplica Rotary Position Embedding in-place sobre un tensor 1D (1xN)
// Sin SIMD equivalente (operacion pares-impar especializada)
void _syn_rope(Tensor tensor, int posicion_token, int head_dim, float theta_base) {
    uint32_t n = tensor.columnas;
    if (head_dim > (int)n) head_dim = (int)n;
    for (int _i = 0; _i < head_dim; _i += 2) {
        float freq = 1.0f / powf(theta_base, (float)_i / (float)head_dim);
        float cos_v = cosf((float)posicion_token * freq);
        float sin_v = sinf((float)posicion_token * freq);
        float x0 = tensor.datos[_i];
        float x1 = tensor.datos[_i + 1];
        tensor.datos[_i]     = x0 * cos_v - x1 * sin_v;
        tensor.datos[_i + 1] = x0 * sin_v + x1 * cos_v;
    }
}

// softmax_escalado: aplica softmax con factor de escala sobre cada fila (estabilidad: resta max)
// Bridge SIMD: mismo ownership (pasaje por copia, modifica in-place)
void _syn_softmax_escalado(Tensor tensor, float factor_escala) {
    _simd_detectar();
    if (_simd_habilitado > 0) {
        _syn_simd_softmax_escalado(tensor, factor_escala);
        return;
    }
    uint32_t filas = tensor.filas;
    uint32_t cols = tensor.columnas;
    for (uint32_t _f = 0; _f < filas; _f++) {
        float* fila = tensor.datos + _f * cols;
        float max_val = -1e30f;
        for (uint32_t _c = 0; _c < cols; _c++) {
            float v = fila[_c] * factor_escala;
            if (v > max_val) max_val = v;
        }
        float suma = 0.0f;
        for (uint32_t _c = 0; _c < cols; _c++) {
            float e = expf(fila[_c] * factor_escala - max_val);
            fila[_c] = e;
            suma += e;
        }
        if (suma > 0.0f) {
            for (uint32_t _c = 0; _c < cols; _c++) {
                fila[_c] /= suma;
            }
        }
    }
}

// multiplicar_matrices_transpuesta_b: C = A * B^T  (zero-copy, B se lee transpuesto)
// Bridge SIMD: mismo ownership (salida pre-asignada, sin pool_free de entradas)
void _syn_multiplicar_matrices_transpuesta_b(Tensor a, Tensor b, Tensor salida) {
    _simd_detectar();
    if (_simd_habilitado > 0) {
        _syn_simd_multiplicar_matrices_transpuesta_b(a, b, salida);
        return;
    }
    uint32_t M = a.filas;
    uint32_t K = a.columnas;
    uint32_t N = b.filas;
    for (uint32_t _i = 0; _i < M; _i++) {
        for (uint32_t _j = 0; _j < N; _j++) {
            float _sum = 0.0f;
            for (uint32_t _k = 0; _k < K; _k++) {
                _sum += a.datos[_i * K + _k] * b.datos[_j * K + _k];
            }
            salida.datos[_i * N + _j] = _sum;
        }
    }
}

// --- std.simd (Aceleracion SIMD) ---
// Compilar con: gcc -c -O2 -msse -msse2 -msse3 synapse_rt.c -o synapse_rt.o
// SIMD intrinsics headers: __AVX2__ implies __SSE__
// pero en algunos MinGW-w64 __SSE__ no se define con -mavx2.
// Usamos __AVX2__ como condicion mas robusta.
#ifdef __AVX2__
#include <immintrin.h>
#elif defined(__SSE__)
#include <xmmintrin.h>
#include <emmintrin.h>
#include <pmmintrin.h>
#endif

// Deteccion de soporte SIMD (RUN-time via CPUID)
// Unico binario portatil: compilar con -msse -msse3 -mavx,
// pero delegar a codigo escalar si el CPU no soporta SIMD.
static const char* _simd_tipo_str = "NONE";

void _simd_detectar(void) {
    if (_simd_habilitado >= 0) return;  // ya detectado
    unsigned int eax, ebx, ecx, edx;
    eax = 1;
#if defined(__x86_64__) || defined(__i386__)
    #if defined(__GNUC__) || defined(__clang__)
        __asm__ volatile(
            "cpuid"
            : "=a"(eax), "=b"(ebx), "=c"(ecx), "=d"(edx)
            : "a"(eax)
        );
    #else
        _simd_habilitado = 0;
        _simd_tipo_str = "NONE";
        return;
    #endif
#else
    _simd_habilitado = 0;
    _simd_tipo_str = "NONE";
    return;
#endif
    _simd_habilitado = 0;  // default: no SIMD hasta que se detecte
    _simd_tipo_str = "NONE";
    if (edx & (1 << 25)) {  // bit 25 = SSE
        _simd_habilitado = 1;
        _simd_tipo_str = "SSE";
    }
    if (ecx & (1 << 28)) {  // bit 28 = AVX
        _simd_habilitado = 1;
        _simd_tipo_str = "AVX";
    }
    // AVX2: CPUID leaf 7, EBX bit 5
    if (ecx & (1 << 28)) {
        eax = 7; ebx = 0; ecx = 0; edx = 0;
#if defined(__x86_64__) || defined(__i386__)
        #if defined(__GNUC__) || defined(__clang__)
            __asm__ volatile(
                "cpuid"
                : "=a"(eax), "=b"(ebx), "=c"(ecx), "=d"(edx)
                : "a"(eax), "c"(ecx)
            );
        #endif
#endif
        if (ebx & (1 << 5)) {
            _simd_tipo_str = "AVX2";
        }
    }
}

int _syn_simd_disponible(void) {
    _simd_detectar();
    return _simd_habilitado > 0 ? 1 : 0;
}

CadenaSegura _syn_simd_tipo(void) {
    _simd_detectar();
    return (CadenaSegura){ .longitud = (int)strlen(_simd_tipo_str), .datos = _simd_tipo_str };
}

#if defined(__x86_64__) || defined(__i386__)
// --- SIMD: llenar_tensor_constante (vectorizado con SSE) ---
void _syn_simd_llenar_tensor_constante(Tensor t, float valor) {
    _simd_detectar();
    if (_simd_habilitado > 0) {
        __m128 v4 = _mm_set1_ps(valor);
        uint32_t n = t.filas * t.columnas;
        uint32_t i = 0;
        for (; i + 4 <= n; i += 4) {
            _mm_storeu_ps(t.datos + i, v4);
        }
        for (; i < n; i++) {
            t.datos[i] = valor;
        }
    } else {
        for (uint32_t _i = 0; _i < t.filas * t.columnas; _i++) {
            t.datos[_i] = valor;
        }
    }
}

// --- SIMD: multiplicar_matrices (SSE: 4-floats por iteracion interna) ---
Tensor _syn_simd_multiplicar_matrices(Tensor a, Tensor b) {
    if (a.columnas != b.filas) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: dimensiones incompatibles en simd_multiplicar_matrices()\n");
        return (Tensor){ .filas = 0, .columnas = 0, .datos = NULL };
    }
    Tensor r;
    r.filas = a.filas;
    r.columnas = b.columnas;
    r.es_mapeado = 0;
    r.datos = (float*)_pool_malloc(r.filas * r.columnas * sizeof(float));
    memset(r.datos, 0, r.filas * r.columnas * sizeof(float));

    _simd_detectar();
    if (_simd_habilitado > 0) {
        for (uint32_t _i = 0; _i < r.filas; _i++) {
            for (uint32_t _k = 0; _k < a.columnas; _k++) {
                __m128 _a_ik = _mm_set1_ps(a.datos[_i * a.columnas + _k]);
                uint32_t _j = 0;
                for (; _j + 4 <= r.columnas; _j += 4) {
                    __m128 _b_kj = _mm_loadu_ps(b.datos + _k * b.columnas + _j);
                    __m128 _r_ij = _mm_loadu_ps(r.datos + _i * r.columnas + _j);
                    _r_ij = _mm_add_ps(_r_ij, _mm_mul_ps(_a_ik, _b_kj));
                    _mm_storeu_ps(r.datos + _i * r.columnas + _j, _r_ij);
                }
                for (; _j < r.columnas; _j++) {
                    r.datos[_i * r.columnas + _j] += a.datos[_i * a.columnas + _k] * b.datos[_k * b.columnas + _j];
                }
            }
        }
    } else {
        for (uint32_t _i = 0; _i < r.filas; _i++) {
            for (uint32_t _k = 0; _k < a.columnas; _k++) {
                float _a_ik = a.datos[_i * a.columnas + _k];
                for (uint32_t _j = 0; _j < r.columnas; _j++) {
                    r.datos[_i * r.columnas + _j] += _a_ik * b.datos[_k * b.columnas + _j];
                }
            }
        }
    }
    if (!a.es_mapeado) { pool_free(a.datos); }
    if (!b.es_mapeado) { pool_free(b.datos); }
    return r;
}

// --- SIMD: multiplicar_matrices_transpuesta_b (SSE: 4-floats en acumulacion) ---
void _syn_simd_multiplicar_matrices_transpuesta_b(Tensor a, Tensor b, Tensor salida) {
    uint32_t M = a.filas;
    uint32_t K = a.columnas;
    uint32_t N = b.filas;
    _simd_detectar();
    if (_simd_habilitado > 0) {
        for (uint32_t _i = 0; _i < M; _i++) {
            for (uint32_t _j = 0; _j < N; _j++) {
                __m128 _sum4 = _mm_setzero_ps();
                uint32_t _k = 0;
                for (; _k + 4 <= K; _k += 4) {
                    __m128 _a4 = _mm_loadu_ps(a.datos + _i * K + _k);
                    __m128 _b4 = _mm_loadu_ps(b.datos + _j * K + _k);
                    _sum4 = _mm_add_ps(_sum4, _mm_mul_ps(_a4, _b4));
                }
                float _sum = _sum4[0] + _sum4[1] + _sum4[2] + _sum4[3];
                for (; _k < K; _k++) {
                    _sum += a.datos[_i * K + _k] * b.datos[_j * K + _k];
                }
                salida.datos[_i * N + _j] = _sum;
            }
        }
    } else {
        for (uint32_t _i = 0; _i < M; _i++) {
            for (uint32_t _j = 0; _j < N; _j++) {
                float _sum = 0.0f;
                for (uint32_t _k = 0; _k < K; _k++) {
                    _sum += a.datos[_i * K + _k] * b.datos[_j * K + _k];
                }
                salida.datos[_i * N + _j] = _sum;
            }
        }
    }
}

// --- SIMD: rmsnorm (SSE: sumacuadrados vectorizada + normalizacion 4-wide) ---
void _syn_simd_rmsnorm(Tensor salida, Tensor entrada, Tensor peso_normalizacion, float epsilon) {
    uint32_t n = entrada.columnas;
    _simd_detectar();
    if (_simd_habilitado > 0) {
        __m128 _sum4 = _mm_setzero_ps();
        uint32_t i = 0;
        for (; i + 4 <= n; i += 4) {
            __m128 _v = _mm_loadu_ps(entrada.datos + i);
            _sum4 = _mm_add_ps(_sum4, _mm_mul_ps(_v, _v));
        }
        float suma_cuadrados = _sum4[0] + _sum4[1] + _sum4[2] + _sum4[3];
        for (; i < n; i++) {
            float v = entrada.datos[i];
            suma_cuadrados += v * v;
        }
        float rms = sqrtf(suma_cuadrados / (float)n + epsilon);
        __m128 _rms4 = _mm_set1_ps(rms);
        i = 0;
        for (; i + 4 <= n; i += 4) {
            __m128 _e = _mm_loadu_ps(entrada.datos + i);
            __m128 _w = _mm_loadu_ps(peso_normalizacion.datos + i);
            _mm_storeu_ps(salida.datos + i, _mm_mul_ps(_mm_div_ps(_e, _rms4), _w));
        }
        for (; i < n; i++) {
            salida.datos[i] = (entrada.datos[i] / rms) * peso_normalizacion.datos[i];
        }
    } else {
        float suma_cuadrados = 0.0f;
        for (uint32_t _i = 0; _i < n; _i++) {
            float v = entrada.datos[_i];
            suma_cuadrados += v * v;
        }
        float rms = sqrtf(suma_cuadrados / (float)n + epsilon);
        for (uint32_t _i = 0; _i < n; _i++) {
            salida.datos[_i] = (entrada.datos[_i] / rms) * peso_normalizacion.datos[_i];
        }
    }
}

// --- SIMD: silu (expf escalar, SSE ~2x por carga/almacenamiento de 4 floats) ---
void _syn_simd_silu(Tensor salida, Tensor entrada) {
    uint32_t n = entrada.columnas;
    for (uint32_t _i = 0; _i < n; _i++) {
        float x = entrada.datos[_i];
        salida.datos[_i] = x / (1.0f + expf(-x));
    }
}

// --- SIMD: softmax_escalado (SSE para max-fila y division) ---
void _syn_simd_softmax_escalado(Tensor tensor, float factor_escala) {
    uint32_t filas = tensor.filas;
    uint32_t cols = tensor.columnas;
    for (uint32_t _f = 0; _f < filas; _f++) {
        float* fila = tensor.datos + _f * cols;
        _simd_detectar();
        if (_simd_habilitado > 0) {
            __m128 _max4 = _mm_set1_ps(-1e30f);
            uint32_t _c = 0;
            for (; _c + 4 <= cols; _c += 4) {
                __m128 _v = _mm_mul_ps(_mm_loadu_ps(fila + _c), _mm_set1_ps(factor_escala));
                _max4 = _mm_max_ps(_max4, _v);
            }
            float max_val = _max4[0];
            if (_max4[1] > max_val) max_val = _max4[1];
            if (_max4[2] > max_val) max_val = _max4[2];
            if (_max4[3] > max_val) max_val = _max4[3];
            for (; _c < cols; _c++) {
                float v = fila[_c] * factor_escala;
                if (v > max_val) max_val = v;
            }
            __m128 _sum4 = _mm_setzero_ps();
            _c = 0;
            for (; _c + 4 <= cols; _c += 4) {
                __m128 _e = _mm_set_ps(
                    expf(fila[_c+3] * factor_escala - max_val),
                    expf(fila[_c+2] * factor_escala - max_val),
                    expf(fila[_c+1] * factor_escala - max_val),
                    expf(fila[_c]   * factor_escala - max_val)
                );
                _mm_storeu_ps(fila + _c, _e);
                _sum4 = _mm_add_ps(_sum4, _e);
            }
            float suma = _sum4[0] + _sum4[1] + _sum4[2] + _sum4[3];
            for (; _c < cols; _c++) {
                float e = expf(fila[_c] * factor_escala - max_val);
                fila[_c] = e;
                suma += e;
            }
            if (suma > 0.0f) {
                __m128 _sumv = _mm_set1_ps(suma);
                _c = 0;
                for (; _c + 4 <= cols; _c += 4) {
                    _mm_storeu_ps(fila + _c, _mm_div_ps(_mm_loadu_ps(fila + _c), _sumv));
                }
                for (; _c < cols; _c++) {
                    fila[_c] /= suma;
                }
            }
        } else {
            float max_val = -1e30f;
            for (uint32_t _c = 0; _c < cols; _c++) {
                float v = fila[_c] * factor_escala;
                if (v > max_val) max_val = v;
            }
            float suma = 0.0f;
            for (uint32_t _c = 0; _c < cols; _c++) {
                float e = expf(fila[_c] * factor_escala - max_val);
                fila[_c] = e;
                suma += e;
            }
            if (suma > 0.0f) {
                for (uint32_t _c = 0; _c < cols; _c++) {
                    fila[_c] /= suma;
                }
            }
        }
    }
}


#else
// Non-x86 architecture stubs (SIMD not available — _simd_habilitado=0 ensures these are never called)
#include <unistd.h>
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
// --- std.math (alias) ---
Tensor suma(Tensor a, Tensor b) {
    return suma_tensor(a, b);
}

Tensor producto(Tensor a, Tensor b) {
    return producto_punto(a, b);
}

// --- std.mem ---
Tensor reserva(int tamano) {
    Tensor _bloque;
    _bloque.filas = tamano;
    _bloque.columnas = 1;
    _bloque.es_mapeado = 0;
    _bloque.datos = _pool_malloc(tamano);
    return _bloque;
}

void libera(Tensor bloque) {
    if (bloque.datos && !bloque.es_mapeado) {
        pool_free(bloque.datos);
    }
}
