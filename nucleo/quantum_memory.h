// quantum_memory.h — Quantum Memory & Decoherence Simulation (M16.4)
// ======================================================================
// Canales de ruido estocástico sobre vector de estado cuántico:
//   T1 (Amplitude Damping): decaimiento |1> -> |0>
//   T2 (Phase Damping): pérdida de coherencia fuera de diagonal
// Integración con QEC: Shor 9-qubit (M16.2) + Surface Code (M16.3)
//
// Zero-telemetry: todo el proceso es local y soberano.
// ======================================================================

#ifndef QUANTUM_MEMORY_H
#define QUANTUM_MEMORY_H

#include "quantum_runtime.h"

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================
// Constantes
// ============================================================
#define QM_MAGIC_HEADER         0x514D454D  // "QMEM"
#define QM_VERSION              1
#define QM_MAX_QUBITS           QC_MAX_QUBITS
#define QM_DEFAULT_T1           1000.0  // microsegundos
#define QM_DEFAULT_T2           500.0   // microsegundos

// ============================================================
// Tipos
// ============================================================

// Canal de ruido
typedef struct {
    double t1;                  // Tiempo de relajacion T1 (us)
    double t2;                  // Tiempo de desfase T2 (us)
    double gamma_1;             // Tasa de decaimiento actual (1 - e^(-t/T1))
    double gamma_2;             // Tasa de desfase actual (1 - e^(-t/T2))
    double tiempo_transcurrido; // Tiempo desde ultima actualizacion (us)
    int errores_t1;             // Contador de eventos T1
    int errores_t2;             // Contador de eventos T2
} QMChannel;

// Resultado de simulacion de memoria
typedef struct {
    double fidelidad_fisica;    // Fidelidad del qubit fisico despues del ruido
    double fidelidad_logica;    // Fidelidad del qubit logico despues de QEC
    double t1_efectivo;         // T1 efectivo con correccion (us)
    double t2_efectivo;         // T2 efectivo con correccion (us)
    int errores_t1;             // Eventos T1 ocurridos
    int errores_t2;             // Eventos T2 ocurridos
    int errores_corregidos;     // Errores corregidos por QEC
    char descripcion[128];      // Descripcion textual
} QMResultado;

// ============================================================
// API publica — 10 funciones
// ============================================================

// --- Configuracion del canal ---
QMChannel qm_crear_canal(double t1, double t2);
void qm_actualizar_tiempo(QMChannel* canal, double tiempo_transcurrido_us);

// --- Aplicacion de ruido ---
int qm_aplicar_t1(EstadoCuantico* sistema, QMChannel* canal);
int qm_aplicar_t2(EstadoCuantico* sistema, QMChannel* canal);
int qm_aplicar_ruido(EstadoCuantico* sistema, QMChannel* canal);

// --- Integracion con QEC ---
QMResultado qm_simular_con_qec(EstadoCuantico* sistema, QMChannel* canal,
                                 int usar_shor, int usar_surface,
                                 int num_qubits_logicos);

// --- Verificacion ---
double qm_fidelidad_fisica(EstadoCuantico* sistema);
double qm_calcular_t1_efectivo(QMChannel* canal);

// --- Utilidades ---
void qm_imprimir_canal(const QMChannel* canal);

// ============================================================
// Wrappers _syn_qm_* para enlace con std.quantum_memory
// ============================================================
int _syn_qm_aplicar_t1(void* sistema, double t1, double tiempo);
int _syn_qm_aplicar_t2(void* sistema, double t2, double tiempo);
int _syn_qm_simular_con_qec(void* sistema, double t1, double t2, double tiempo);

#ifdef __cplusplus
}
#endif

#endif // QUANTUM_MEMORY_H
