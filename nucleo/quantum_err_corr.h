// quantum_err_corr.h — Quantum Error Correction (M16.2)
// ======================================================================
// Implementa subsistema de tolerancia a fallos cuanticos simulados sobre
// el runtime quantum_runtime.c (M16.1).
//
// Codigo de Shor de 9 qubits: protege 1 qubit logico contra errores
// de bit-flip (X) y phase-flip (Z) en cualquier qubit fisico.
//
// Zero-telemetry: todo el proceso es local y soberano.
// ======================================================================

#ifndef QUANTUM_ERR_CORR_H
#define QUANTUM_ERR_CORR_H

#include <stdint.h>
#include "quantum_runtime.h"

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================
// Constantes
// ============================================================
#define QEC_SHOR_NUM_QUBITS     9   // Qubits fisicos para 1 logico
#define QEC_MAGIC_HEADER         0x51454344  // "QECD"
#define QEC_VERSION              1
#define QEC_MAX_SYNDROMES        16

// Tipos de error
#define QEC_ERROR_NONE           0
#define QEC_ERROR_BIT_FLIP       1   // Error X (bit-flip)
#define QEC_ERROR_PHASE_FLIP     2   // Error Z (phase-flip)
#define QEC_ERROR_BOTH           3   // Error X+Z (both)

// Estados de correccion
#define QEC_CORRECTED            0
#define QEC_DEGENERATE           1
#define QEC_FAILED              -1

// ============================================================
// Tipos
// ============================================================

// Medicion de sindrome: detecta tipo y posicion del error
typedef struct {
    int tipo_error;            // QEC_ERROR_NONE / BIT_FLIP / PHASE_FLIP / BOTH
    int qubit_afectado;        // Indice del qubit con error (-1 si ninguno)
    int sindromes_bit[3];      // Sindrome bit-flip por bloque (0/1)
    int sindromes_fase[3];     // Sindrome phase-flip por bloque (0/1)
    double fidelidad;          // Fidelidad de la correccion (0..1)
    int estado_correccion;     // QEC_CORRECTED / DEGENERATE / FAILED
} MedicionSindromes;

// Resultado de correccion de errores
typedef struct {
    int exito;                 // 1 si la correccion fue exitosa
    double fidelidad_final;    // Fidelidad despues de la correccion
    int errores_corregidos;    // Numero de errores detectados y corregidos
    char descripcion[128];     // Descripcion textual del resultado
} ResultadoCorreccion;

// ============================================================
// API publica — 15 funciones
// ============================================================

// --- Codificacion/Decodificacion ---
int qec_codificar_logico(EstadoCuantico* sistema, int qubit_logico,
                         const Complejo* amplitud_0, const Complejo* amplitud_1);
int qec_decodificar_logico(EstadoCuantico* sistema, int qubit_logico,
                            Complejo* amplitud_0, Complejo* amplitud_1);

// --- Inyeccion de errores ---
int qec_inyectar_bit_flip(EstadoCuantico* sistema, int qubit_fisico);
int qec_inyectar_phase_flip(EstadoCuantico* sistema, int qubit_fisico);

// --- Medicion de sindromes ---
MedicionSindromes qec_medir_sindromes(EstadoCuantico* sistema);

// --- Correccion activa ---
ResultadoCorreccion qec_corregir_errores(EstadoCuantico* sistema,
                                          const MedicionSindromes* sindromes);
int qec_aplicar_correccion(EstadoCuantico* sistema,
                            int tipo_error, int qubit_afectado);

// --- Ciclo completo de proteccion ---
ResultadoCorreccion qec_proteger_qubit(EstadoCuantico* sistema,
                                        const Complejo* amp_0,
                                        const Complejo* amp_1,
                                        int tipo_error_inyectado,
                                        int qubit_error);

// --- Verificacion ---
double qec_calcular_fidelidad(EstadoCuantico* sistema,
                               const Complejo* amp_0_original,
                               const Complejo* amp_1_original);

// --- Utilidades ---
int qec_inicializar_estado_logico(EstadoCuantico* sistema, int valor);
int qec_verificar_estado_logico(EstadoCuantico* sistema, int valor_esperado);
void qec_imprimir_resultado(const ResultadoCorreccion* resultado);

// ============================================================
// Wrappers _syn_qec_* para enlace con std.quantum_err_corr
// ============================================================
int _syn_qec_inicializar_estado_logico(void* sistema, int valor);
int _syn_qec_inyectar_bit_flip(void* sistema, int qubit);
int _syn_qec_inyectar_phase_flip(void* sistema, int qubit);
int _syn_qec_corregir_errores(void* sistema);
int _syn_qec_verificar_estado_logico(void* sistema, int valor_esperado);

#ifdef __cplusplus
}
#endif

#endif // QUANTUM_ERR_CORR_H
