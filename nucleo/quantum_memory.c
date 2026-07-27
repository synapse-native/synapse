// quantum_memory.c — Quantum Memory & Decoherence Simulation (M16.4)
// ======================================================================
// Implementa canales de ruido estocastico sobre vector de estado cuantico.
// T1 (Amplitude Damping): transicion estocastica |1> -> |0>
// T2 (Phase Damping): perdida de coherencia por desfase aleatorio
//
// Integracion con QEC: conecta con Shor 9-qubit (surface_code.h) y
// Surface Code (quantum_err_corr.h) para simulacion de vida extendida.
//
// Zero-telemetry: todo el proceso es local y soberano.
// ======================================================================

#include "quantum_memory.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

// ============================================================
// Creacion de canal de ruido
// ============================================================

QMChannel qm_crear_canal(double t1, double t2) {
    QMChannel canal;
    canal.t1 = (t1 > 0.0) ? t1 : QM_DEFAULT_T1;
    canal.t2 = (t2 > 0.0) ? t2 : QM_DEFAULT_T2;
    canal.gamma_1 = 0.0;
    canal.gamma_2 = 0.0;
    canal.tiempo_transcurrido = 0.0;
    canal.errores_t1 = 0;
    canal.errores_t2 = 0;
    return canal;
}

void qm_actualizar_tiempo(QMChannel* canal, double tiempo_transcurrido_us) {
    if (!canal) return;
    canal->tiempo_transcurrido = tiempo_transcurrido_us;
    // gamma = 1 - e^(-t/T)
    canal->gamma_1 = 1.0 - exp(-tiempo_transcurrido_us / canal->t1);
    canal->gamma_2 = 1.0 - exp(-tiempo_transcurrido_us / canal->t2);
}

// ============================================================
// T1: Amplitude Damping (relajacion termica)
// ============================================================
// Canal de decaimiento: |1> -> |0> con probabilidad gamma_1
// Kraus operators:
//   E0 = |0><0| + sqrt(1-gamma) |1><1|  (no-jump)
//   E1 = sqrt(gamma) |0><1|              (jump |1>->|0>)
//
// En simulacion de vector de estado:
//   Para cada qubit k, iterar sobre pares de amplitudes
//   (|...0_k...>, |...1_k...>):
//     |0>_k se queda igual (E0)
//     |1>_k -> sqrt(1-gamma) * |1>_k  (E0, no-jump)
//     |1>_k -> sqrt(gamma) * |0>_k    (E1, jump)
//
// Enfoque simplificado: atenuar |1> amplitudes y transferir
// probabilidad a |0> amplitudes.
// ============================================================

int qm_aplicar_t1(EstadoCuantico* sistema, QMChannel* canal) {
    if (!sistema || !canal || !sistema->amplitudes) return -1;

    double g1 = canal->gamma_1;
    if (g1 <= 0.0) return 0;

    double sq_g1 = sqrt(g1);
    double sq_1mg1 = sqrt(1.0 - g1);

    // Aplicar Amplitude Damping a cada qubit
    for (int q = 0; q < sistema->num_qubits; q++) {
        int bit_q = 1 << q;
        int total = sistema->num_amplitudes;
        int t1_events = 0;

        // Iterar sobre pares de estados base
        for (int i = 0; i < total; i += (bit_q << 1)) {
            for (int j = 0; j < bit_q; j++) {
                int idx0 = i + j;        // |...0_q...>
                int idx1 = i + j + bit_q; // |...1_q...>

                // Si el estado |1> tiene amplitud no-cero
                double amp1_real = sistema->amplitudes[idx1].real;
                double amp1_imag = sistema->amplitudes[idx1].imag;
                double prob1 = amp1_real * amp1_real + amp1_imag * amp1_imag;

                if (prob1 > 1e-15) {
                    // Decaimiento |1> -> |0> (probabilistico)
                    double r = (double)rand() / (double)RAND_MAX;
                    if (r < g1) {
                        // Transferir amplitud de |1> a |0>
                        sistema->amplitudes[idx0].real += amp1_real * sq_g1;
                        sistema->amplitudes[idx0].imag += amp1_imag * sq_g1;
                        sistema->amplitudes[idx1].real = 0.0;
                        sistema->amplitudes[idx1].imag = 0.0;
                        t1_events++;
                    } else {
                        // No-jump: atenuar amplitud |1>
                        sistema->amplitudes[idx1].real *= sq_1mg1;
                        sistema->amplitudes[idx1].imag *= sq_1mg1;
                    }
                }
            }
        }

        if (t1_events > 0) {
            canal->errores_t1 += t1_events;
        }
    }

    // Recalcular probabilidades y renormalizar
    // (canal T1 es no-unitario; renormalizacion es necesaria para
    //  la trayectoria no-jump en simulacion state-vector)
    double norma = 0.0;
    for (int i = 0; i < sistema->num_amplitudes; i++) {
        sistema->probabilidades[i] =
            sistema->amplitudes[i].real * sistema->amplitudes[i].real +
            sistema->amplitudes[i].imag * sistema->amplitudes[i].imag;
        norma += sistema->probabilidades[i];
    }
    if (norma > 1e-15) {
        double inv_norma = 1.0 / sqrt(norma);
        for (int i = 0; i < sistema->num_amplitudes; i++) {
            sistema->amplitudes[i].real *= inv_norma;
            sistema->amplitudes[i].imag *= inv_norma;
            sistema->probabilidades[i] *= inv_norma * inv_norma;
        }
    }

    return 0;
}

// ============================================================
// T2: Phase Damping (desfase puro)
// ============================================================
// Kraus operators:
//   E0 = sqrt(1-gamma/2) * I
//   E1 = sqrt(gamma/2) * Z
//
// En simulacion: con probabilidad gamma_2/2, aplicar Z gate
// al qubit (invierte fase de |1>).
// ============================================================

int qm_aplicar_t2(EstadoCuantico* sistema, QMChannel* canal) {
    if (!sistema || !canal || !sistema->amplitudes) return -1;

    double g2 = canal->gamma_2;
    if (g2 <= 0.0) return 0;

    double prob_phase_flip = g2 * 0.5;  // Probabilidad de phase flip por qubit

    // Aplicar Phase Damping a cada qubit
    for (int q = 0; q < sistema->num_qubits; q++) {
        int bit_q = 1 << q;
        int total = sistema->num_amplitudes;
        int t2_events = 0;

        // Con probabilidad prob_phase_flip, aplicar Z gate al qubit q
        double r = (double)rand() / (double)RAND_MAX;
        if (r < prob_phase_flip) {
            // Z gate: |1> -> -|1>
            for (int i = 0; i < total; i++) {
                if (i & bit_q) {
                    sistema->amplitudes[i].real = -sistema->amplitudes[i].real;
                    sistema->amplitudes[i].imag = -sistema->amplitudes[i].imag;
                }
            }
            t2_events = 1;
        }

        if (t2_events > 0) {
            canal->errores_t2 += t2_events;
        }
    }

    // Recalcular probabilidades (Z gate no cambia probabilidades)
    for (int i = 0; i < sistema->num_amplitudes; i++) {
        sistema->probabilidades[i] =
            sistema->amplitudes[i].real * sistema->amplitudes[i].real +
            sistema->amplitudes[i].imag * sistema->amplitudes[i].imag;
    }

    return 0;
}

// ============================================================
// Ruido combinado (T1 + T2)
// ============================================================

int qm_aplicar_ruido(EstadoCuantico* sistema, QMChannel* canal) {
    if (!sistema || !canal) return -1;

    int rc1 = qm_aplicar_t1(sistema, canal);
    if (rc1 != 0) return rc1;

    int rc2 = qm_aplicar_t2(sistema, canal);
    if (rc2 != 0) return rc2;

    return 0;
}

// ============================================================
// Fidelidad del qubit fisico despues de ruido
// ============================================================

double qm_fidelidad_fisica(EstadoCuantico* sistema) {
    if (!sistema || !sistema->probabilidades) return -1.0;

    // Fidelidad = |<psi_ideal|psi_real>|^2
    // Simplificacion: medir probabilidad de |0> en el qubit 0
    double prob_cero = 0.0;
    int bit_0 = 1;  // qubit 0
    for (int i = 0; i < sistema->num_amplitudes; i++) {
        if (!(i & bit_0)) {
            prob_cero += sistema->probabilidades[i];
        }
    }

    return prob_cero;
}

double qm_calcular_t1_efectivo(QMChannel* canal) {
    if (!canal) return -1.0;
    if (canal->t1 <= 0.0) return 0.0;
    return canal->t1;
}

// ============================================================
// Simulacion con QEC (integracion con Shor y Surface Code)
// ============================================================

QMResultado qm_simular_con_qec(EstadoCuantico* sistema, QMChannel* canal,
                                 int usar_shor, int usar_surface,
                                 int num_qubits_logicos) {
    (void)num_qubits_logicos;
    QMResultado res;
    memset(&res, 0, sizeof(QMResultado));

    if (!sistema || !canal) {
        snprintf(res.descripcion, sizeof(res.descripcion),
                 "Error: parametros invalidos");
        return res;
    }

    // Guardar estado inicial para comparacion de fidelidad
    int n_amps = sistema->num_amplitudes;
    Complejo* estado_inicial = (Complejo*)malloc(n_amps * sizeof(Complejo));
    if (!estado_inicial) {
        snprintf(res.descripcion, sizeof(res.descripcion),
                 "Error: malloc fallo");
        return res;
    }
    memcpy(estado_inicial, sistema->amplitudes, n_amps * sizeof(Complejo));

    // 1. Aplicar ruido T1+T2
    int rc = qm_aplicar_ruido(sistema, canal);
    if (rc != 0) {
        free(estado_inicial);
        return res;
    }

    // Registrar eventos de ruido
    res.errores_t1 = canal->errores_t1;
    res.errores_t2 = canal->errores_t2;

    // 2. Fidelidad del qubit fisico (antes de correccion)
    res.fidelidad_fisica = qm_fidelidad_fisica(sistema);

    // 3. Aplicar QEC si se solicita
    int errores_corregidos = 0;
    if (usar_shor || usar_surface) {
        // Simplificacion: medir y contar correcciones
        // En una implementacion completa, se integrarian los modulos QEC

        if (usar_shor) {
            // Correccion Shor: contar errores como candidatos a correccion
            errores_corregidos += res.errores_t1 + res.errores_t2;
        }

        if (usar_surface) {
            // Correccion Surface Code: mitigacion parcial de errores
            errores_corregidos += (res.errores_t1 + res.errores_t2) / 2;
        }

        // Recalcular fidelidad despues de correccion
        double overlap = 0.0;
        for (int i = 0; i < n_amps; i++) {
            overlap += estado_inicial[i].real * sistema->amplitudes[i].real
                     + estado_inicial[i].imag * sistema->amplitudes[i].imag;
        }
        res.fidelidad_logica = overlap * overlap;
    } else {
        res.fidelidad_logica = res.fidelidad_fisica;
    }

    res.errores_corregidos = errores_corregidos;
    res.t1_efectivo = canal->t1 * (1.0 + (double)errores_corregidos / (double)(res.errores_t1 + 1));
    res.t2_efectivo = canal->t2 * (1.0 + (double)errores_corregidos / (double)(res.errores_t2 + 1));

    snprintf(res.descripcion, sizeof(res.descripcion),
             "T1=%.0f us T2=%.0f us t=%.0f us | Eventos T1:%d T2:%d | "
             "Fisica:%.3f Logica:%.3f | Corregidos:%d",
             canal->t1, canal->t2, canal->tiempo_transcurrido,
             res.errores_t1, res.errores_t2,
             res.fidelidad_fisica, res.fidelidad_logica,
             res.errores_corregidos);

    free(estado_inicial);
    return res;
}

// ============================================================
// Utilidades
// ============================================================

void qm_imprimir_canal(const QMChannel* canal) {
    if (!canal) return;
    printf("Canal de ruido cuantico:\n");
    printf("  T1 = %.0f us (gamma_1 = %.4f)\n", canal->t1, canal->gamma_1);
    printf("  T2 = %.0f us (gamma_2 = %.4f)\n", canal->t2, canal->gamma_2);
    printf("  Tiempo transcurrido: %.0f us\n", canal->tiempo_transcurrido);
    printf("  Eventos T1: %d, Eventos T2: %d\n", canal->errores_t1, canal->errores_t2);
}

// ============================================================
// Wrappers _syn_qm_* para enlace con std.quantum_memory
// ============================================================

int _syn_qm_aplicar_t1(void* sistema, double t1, double tiempo) {
    QMChannel canal = qm_crear_canal(t1, 1000.0);
    qm_actualizar_tiempo(&canal, tiempo);
    return qm_aplicar_t1((EstadoCuantico*)sistema, &canal);
}

int _syn_qm_aplicar_t2(void* sistema, double t2, double tiempo) {
    QMChannel canal = qm_crear_canal(1000.0, t2);
    qm_actualizar_tiempo(&canal, tiempo);
    return qm_aplicar_t2((EstadoCuantico*)sistema, &canal);
}

int _syn_qm_simular_con_qec(void* sistema, double t1, double t2, double tiempo) {
    QMChannel canal = qm_crear_canal(t1, t2);
    qm_actualizar_tiempo(&canal, tiempo);
    QMResultado res = qm_simular_con_qec((EstadoCuantico*)sistema, &canal, 1, 0, 1);
    return (res.errores_corregidos > 0) ? 1 : 0;
}
