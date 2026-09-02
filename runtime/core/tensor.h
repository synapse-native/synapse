// cumple Manual 6 §3: tensor runtime
// synapse_rt_tensor.h — Public API of runtime/core/tensor.c
// Extraido de synapse_rt.c (deuda D-9(d), corte 2 tras io.c F3-1/F3-2).
#ifndef SYNAPSE_RT_TENSOR_H
#define SYNAPSE_RT_TENSOR_H

#include "synapse_rt_types.h"

#ifdef __cplusplus
extern "C" {
#endif

// std.math / std.tensor / std.simd (IA nativa)
Tensor crear_tensor(int filas, int columnas);
Tensor suma_tensor(Tensor a, Tensor b);
Tensor producto_punto(Tensor a, Tensor b);
Tensor relu(Tensor a);

void _syn_llenar_tensor_constante(Tensor t, float valor);
Tensor _syn_multiplicar_matrices(Tensor a, Tensor b);
void _syn_multiplicar_matrices_transpuesta_b(Tensor a, Tensor b, Tensor salida);
void _syn_extraer_fila(Tensor salida, Tensor tabla_embeddings, int indice_token);
void _syn_rmsnorm(Tensor salida, Tensor entrada, Tensor peso_normalizacion, float epsilon);
void _syn_silu(Tensor salida, Tensor entrada);
void _syn_rope(Tensor tensor, int posicion_token, int head_dim, float theta_base);
void _syn_softmax_escalado(Tensor tensor, float factor_escala);

void _simd_detectar(void);
int _syn_simd_disponible(void);
CadenaSegura _syn_simd_tipo(void);
void _syn_simd_llenar_tensor_constante(Tensor t, float valor);
Tensor _syn_simd_multiplicar_matrices(Tensor a, Tensor b);
void _syn_simd_multiplicar_matrices_transpuesta_b(Tensor a, Tensor b, Tensor salida);
void _syn_simd_rmsnorm(Tensor salida, Tensor entrada, Tensor peso_normalizacion, float epsilon);
void _syn_simd_silu(Tensor salida, Tensor entrada);
void _syn_simd_softmax_escalado(Tensor tensor, float factor_escala);

// std.math (alias) / std.mem
Tensor suma(Tensor a, Tensor b);
Tensor producto(Tensor a, Tensor b);
Tensor reserva(int tamano);
void libera(Tensor bloque);

#ifdef __cplusplus
}
#endif

#endif /* SYNAPSE_RT_TENSOR_H */
