// quantum_runtime.h — Quantum-Ready Runtime Simulado (M16.1)
// ======================================================================
// Simulador de vectores de estado cuantico para N qubits (max 8).
// Implementa puertas logicas cuanticas estandar, medicion con colapso,
// y creacion de estados de Bell / algoritmo de Deutsch-Jozsa.
//
// Zero-telemetry: todo el proceso es local y soberano.
// ======================================================================

#ifndef QUANTUM_RUNTIME_H
#define QUANTUM_RUNTIME_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================
// Constantes
// ============================================================
#define QC_MAX_QUBITS           9
#define QC_MAX_AMPLITUDES       (1 << QC_MAX_QUBITS)  // 512 — suficiente para Shor code 9-qubits
#define QC_MAGIC_HEADER         0x514E5452  // "QNTR"
#define QC_VERSION              1
#define QC_SQRT2_INV            0.7071067811865475244  // 1/sqrt(2)

// ============================================================
// Tipos
// ============================================================

// Numero complejo
typedef struct {
    double real;
    double imag;
} Complejo;

// Estado cuantico completo para N qubits
typedef struct {
    int num_qubits;
    int num_amplitudes;
    Complejo* amplitudes;       // Vector de estado de tamano 2^N
    double* probabilidades;     // Probabilidades cacheadas |amp|^2
    int* qubits_medidos;        // -1 si no medido, 0/1 si colapsado
    double entropia_entrelazamiento;  // Medida de entrelazamiento
    int estado_inicializado;
} EstadoCuantico;

// ============================================================
// API publica — 20 funciones
// ============================================================

// --- Ciclo de vida ---
EstadoCuantico* qc_crear_sistema(int num_qubits);
void qc_liberar_sistema(EstadoCuantico* sistema);
void qc_limpiar(EstadoCuantico* sistema);

// --- Inicializacion de estados ---
int qc_inicializar_estado_cero(EstadoCuantico* sistema);   // |000...0>
int qc_inicializar_estado_uniforme(EstadoCuantico* sistema);
int qc_inicializar_base(EstadoCuantico* sistema, int indice_basis);

// --- Puertas de un qubit ---
int qc_aplicar_hadamard(EstadoCuantico* sistema, int qubit);
int qc_aplicar_pauli_x(EstadoCuantico* sistema, int qubit);
int qc_aplicar_pauli_y(EstadoCuantico* sistema, int qubit);
int qc_aplicar_pauli_z(EstadoCuantico* sistema, int qubit);
int qc_aplicar_phase(EstadoCuantico* sistema, int qubit, double angulo);
int qc_aplicar_t(EstadoCuantico* sistema, int qubit);

// --- Puertas de dos qubits ---
int qc_aplicar_cnot(EstadoCuantico* sistema, int control, int target);
int qc_aplicar_swap(EstadoCuantico* sistema, int q1, int q2);

// --- Medicion ---
int qc_medir(EstadoCuantico* sistema, int qubit);
double qc_probabilidad_cero(EstadoCuantico* sistema, int qubit);
double qc_probabilidad_uno(EstadoCuantico* sistema, int qubit);

// --- Estados especiales ---
int qc_crear_estado_bell(EstadoCuantico* sistema, int q1, int q2);
int qc_es_entrelazado(EstadoCuantico* sistema);

// --- Verificacion ---
double qc_probabilidad_conservada(EstadoCuantico* sistema);

// --- Algoritmos cuanticos ---
int qc_deutsch_jozsa(EstadoCuantico* sistema,
                     int (*oraculo)(int entrada),
                     int num_bits_entrada);

// --- Consulta ---
Complejo qc_obtener_amplitud(EstadoCuantico* sistema, int indice_basis);
int qc_obtener_num_qubits(EstadoCuantico* sistema);

// ============================================================
// Wrappers _syn_qc_* para enlace con std.quantum
// ============================================================
void* _syn_qc_crear_sistema(int num_qubits);
void _syn_qc_liberar_sistema(void* sistema);
int _syn_qc_inicializar_estado_cero(void* sistema);
int _syn_qc_inicializar_estado_uniforme(void* sistema);
int _syn_qc_aplicar_hadamard(void* sistema, int qubit);
int _syn_qc_aplicar_pauli_x(void* sistema, int qubit);
int _syn_qc_aplicar_cnot(void* sistema, int control, int target);
int _syn_qc_medir(void* sistema, int qubit);
double _syn_qc_probabilidad_cero(void* sistema, int qubit);
double _syn_qc_probabilidad_conservada(void* sistema);
int _syn_qc_crear_estado_bell(void* sistema, int q1, int q2);

#ifdef __cplusplus
}
#endif

#endif // QUANTUM_RUNTIME_H
