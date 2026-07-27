// quantum_err_corr.c — Correccion de Errores Cuanticos (M16.2)
// ======================================================================
// Implementa el codigo de Shor de 9 qubits para proteger 1 qubit logico
// contra errores de bit-flip (X) y phase-flip (Z).
//
// Codificacion de Shor:
//   |0>_L = (|000> + |111>)(|000> + |111>)(|000> + |111>) / (2*sqrt(2))
//   |1>_L = (|000> - |111>)(|000> - |111>)(|000> - |111>) / (2*sqrt(2))
//
// Zero-telemetry: todo el proceso es local y soberano.
// ======================================================================

#include "quantum_err_corr.h"
#include "quantum_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

// ============================================================
// Helpers locales
// ============================================================
static double _c_mod2_local(Complejo a) {
    return a.real * a.real + a.imag * a.imag;
}

static int _sistema_valido(EstadoCuantico* s) {
    return s != NULL && s->amplitudes != NULL && s->num_qubits >= QEC_SHOR_NUM_QUBITS;
}

// ============================================================
// Codificacion logica de Shor (9 qubits)
// ============================================================
int qec_codificar_logico(EstadoCuantico* sistema, int qubit_logico,
                         const Complejo* amplitud_0, const Complejo* amplitud_1) {
    if (!_sistema_valido(sistema)) return -1;
    if (qubit_logico != 0) return -1; // Solo soportamos qubit logico en posicion 0
    if (!amplitud_0 || !amplitud_1) return -1;
    if (sistema->num_qubits < 9) return -1;

    // Codigo de Shor de 9 qubits (concatenacion de bit-flip + phase-flip):
    // |0>_L = (|000>+|111>)(|000>+|111>)(|000>+|111>) / (2*sqrt(2))
    // |1>_L = (|000>-|111>)(|000>-|111>)(|000>-|111>) / (2*sqrt(2))
    //
    // Codificacion:
    //   1. CNOT(0,1), CNOT(0,2)  — bit-flip encode a 3 qubits
    //   2. H(0), H(1), H(2)      — convertir a base phase-flip
    //   3. CNOT(0,3), CNOT(0,4)  — expandir qubit 0 a 3
    //      CNOT(1,5), CNOT(1,6)  — expandir qubit 1 a 3
    //      CNOT(2,7), CNOT(2,8)  — expandir qubit 2 a 3

    int rc;

    // 1. Inicializar en |000000000>
    rc = qc_inicializar_estado_cero(sistema);
    if (rc != 0) return rc;

    // 2. Si amplitud_1 tiene magnitud significativa, aplicar X al qubit 0
    if (_c_mod2_local(*amplitud_1) > 1e-12) {
        rc = qc_aplicar_pauli_x(sistema, 0);
        if (rc != 0) return rc;
    }

    // 3. Bit-flip encoding: CNOT(0,1), CNOT(0,2)
    rc = qc_aplicar_cnot(sistema, 0, 1);
    if (rc != 0) return rc;
    rc = qc_aplicar_cnot(sistema, 0, 2);
    if (rc != 0) return rc;

    // 4. Phase-flip encoding: H(0), H(1), H(2)
    rc = qc_aplicar_hadamard(sistema, 0);
    if (rc != 0) return rc;
    rc = qc_aplicar_hadamard(sistema, 1);
    if (rc != 0) return rc;
    rc = qc_aplicar_hadamard(sistema, 2);
    if (rc != 0) return rc;

    // 5. Expandir cada qubit a 3 usando CNOTs
    rc = qc_aplicar_cnot(sistema, 0, 3);
    if (rc != 0) return rc;
    rc = qc_aplicar_cnot(sistema, 0, 4);
    if (rc != 0) return rc;

    rc = qc_aplicar_cnot(sistema, 1, 5);
    if (rc != 0) return rc;
    rc = qc_aplicar_cnot(sistema, 1, 6);
    if (rc != 0) return rc;

    rc = qc_aplicar_cnot(sistema, 2, 7);
    if (rc != 0) return rc;
    rc = qc_aplicar_cnot(sistema, 2, 8);
    if (rc != 0) return rc;

    return 0;
}

// ============================================================
// Inicializar estado logico (0 o 1)
// ============================================================
int qec_inicializar_estado_logico(EstadoCuantico* sistema, int valor) {
    if (!_sistema_valido(sistema)) return -1;

    // Crear estado de Shor para |0>_L o |1>_L
    Complejo amp_0, amp_1;
    if (valor == 0) {
        amp_0.real = 1.0; amp_0.imag = 0.0;
        amp_1.real = 0.0; amp_1.imag = 0.0;
    } else {
        amp_0.real = 0.0; amp_0.imag = 0.0;
        amp_1.real = 1.0; amp_1.imag = 0.0;
    }

    return qec_codificar_logico(sistema, 0, &amp_0, &amp_1);
}

// ============================================================
// Inyeccion de errores
// ============================================================

int qec_inyectar_bit_flip(EstadoCuantico* sistema, int qubit_fisico) {
    if (!_sistema_valido(sistema)) return -1;
    if (qubit_fisico < 0 || qubit_fisico >= sistema->num_qubits) return -1;
    return qc_aplicar_pauli_x(sistema, qubit_fisico);
}

int qec_inyectar_phase_flip(EstadoCuantico* sistema, int qubit_fisico) {
    if (!_sistema_valido(sistema)) return -1;
    if (qubit_fisico < 0 || qubit_fisico >= sistema->num_qubits) return -1;
    return qc_aplicar_pauli_z(sistema, qubit_fisico);
}

// ============================================================
// Medicion de sindromes
// ============================================================
MedicionSindromes qec_medir_sindromes(EstadoCuantico* sistema) {
    MedicionSindromes m;
    memset(&m, 0, sizeof(MedicionSindromes));
    m.qubit_afectado = -1;
    m.fidelidad = 0.0;
    m.estado_correccion = QEC_FAILED;

    if (!_sistema_valido(sistema)) return m;

    // Detectar errores bit-flip dentro de cada bloque de 3 qubits
    // Principio: en un bloque sin error, los 3 qubits son identicos
    // Sindrome bit 0: comparar bloque 1 con bloque 2
    // Sindrome bit 1: comparar bloque 1 con bloque 3

    // Para simplificar: medir sindromes comparando paridades
    // En un estado |000> o |111>, la paridad es uniforme

    double prob_error_bloque[3] = {0.0, 0.0, 0.0};

    // Detectar bit-flips: verificar si los bloques estan sincronizados
    // En Shor code, la deteccion de bit-flip usa el patron de 3 qubits por bloque
    // Si un qubit en el bloque tiene fase opuesta, es un bit-flip

    // Bloque 1 (qubits 0,1,2): verificar coherencia
    // Si los qubits 0 y 1 tienen probabilidades |1> significativamente diferentes
    // hay un error en alguno de ellos
    double p1_b0 = qc_probabilidad_uno(sistema, 0);
    double p1_b1 = qc_probabilidad_uno(sistema, 1);
    double p1_b2 = qc_probabilidad_uno(sistema, 2);

    if (fabs(p1_b0 - p1_b1) > 0.1) {
        m.sindromes_bit[0] = 1;
        prob_error_bloque[0] = fabs(p1_b0 - p1_b1);
    }
    if (fabs(p1_b0 - p1_b2) > 0.1) {
        m.sindromes_bit[1] = 1;
        prob_error_bloque[0] = fmax(prob_error_bloque[0], fabs(p1_b0 - p1_b2));
    }

    // Bloque 2 (qubits 3,4,5)
    double p1_b3 = qc_probabilidad_uno(sistema, 3);
    double p1_b4 = qc_probabilidad_uno(sistema, 4);
    double p1_b5 = qc_probabilidad_uno(sistema, 5);

    if (fabs(p1_b3 - p1_b4) > 0.1) {
        m.sindromes_bit[0] = 1;
        prob_error_bloque[1] = fabs(p1_b3 - p1_b4);
    }
    if (fabs(p1_b3 - p1_b5) > 0.1) {
        m.sindromes_bit[0] = 1;
        prob_error_bloque[1] = fmax(prob_error_bloque[1], fabs(p1_b3 - p1_b5));
    }

    // Bloque 3 (qubits 6,7,8)
    double p1_b6 = qc_probabilidad_uno(sistema, 6);
    double p1_b7 = qc_probabilidad_uno(sistema, 7);
    double p1_b8 = qc_probabilidad_uno(sistema, 8);

    if (fabs(p1_b6 - p1_b7) > 0.1) {
        m.sindromes_bit[1] = 1;
        prob_error_bloque[2] = fabs(p1_b6 - p1_b7);
    }
    if (fabs(p1_b6 - p1_b8) > 0.1) {
        m.sindromes_bit[1] = 1;
        prob_error_bloque[2] = fmax(prob_error_bloque[2], fabs(p1_b6 - p1_b8));
    }

    // Detectar phase-flips: verificar signos entre bloques
    // Los tres bloques deben tener la misma fase (+++ o ---)
    // Phase-flip se detecta comparando los signos

    // Determinar signo de cada bloque
    double signo_bloque[3] = {0.0, 0.0, 0.0};

    for (int i = 0; i < sistema->num_amplitudes; i++) {
        int b0 = i & 0x7;        // qubits 0,1,2
        int b1 = (i >> 3) & 0x7; // qubits 3,4,5
        int b2 = (i >> 6) & 0x7; // qubits 6,7,8

        if ((b0 == 0 || b0 == 7) && (b1 == 0 || b1 == 7) && (b2 == 0 || b2 == 7)) {
            double prob = sistema->probabilidades[i];
            if (prob > 1e-10) {
                if (b0 == 0) signo_bloque[0] += sistema->amplitudes[i].real;
                else signo_bloque[0] -= sistema->amplitudes[i].real;

                if (b1 == 0) signo_bloque[1] += sistema->amplitudes[i].real;
                else signo_bloque[1] -= sistema->amplitudes[i].real;

                if (b2 == 0) signo_bloque[2] += sistema->amplitudes[i].real;
                else signo_bloque[2] -= sistema->amplitudes[i].real;
            }
        }
    }

    // Detectamos phase-flip si los signos entre bloques difieren significativamente
    if (signo_bloque[0] * signo_bloque[1] < -0.1) m.sindromes_fase[0] = 1;
    if (signo_bloque[0] * signo_bloque[2] < -0.1) m.sindromes_fase[1] = 1;

    // Determinar tipo de error y qubit afectado
    int tiene_bit_flip = m.sindromes_bit[0] || m.sindromes_bit[1];
    int tiene_phase_flip = m.sindromes_fase[0] || m.sindromes_fase[1];

    if (tiene_bit_flip && tiene_phase_flip) {
        m.tipo_error = QEC_ERROR_BOTH;
    } else if (tiene_bit_flip) {
        m.tipo_error = QEC_ERROR_BIT_FLIP;
    } else if (tiene_phase_flip) {
        m.tipo_error = QEC_ERROR_PHASE_FLIP;
    } else {
        m.tipo_error = QEC_ERROR_NONE;
    }

    // Localizar qubit afectado (aproximacion por sindrome)
    if (tiene_bit_flip) {
        // Buscar en que bloque esta el desbalance de paridad
        for (int b = 0; b < 3; b++) {
            if (prob_error_bloque[b] > 0.05) {
                m.qubit_afectado = b * 3; // Aproximacion: primer qubit del bloque
                break;
            }
        }
    } else if (tiene_phase_flip) {
        m.qubit_afectado = 0; // Phase-flip afecta al primer qubit del bloque
    }

    m.fidelidad = 1.0 - (double)(tiene_bit_flip || tiene_phase_flip) * 0.5;
    m.estado_correccion = (m.tipo_error == QEC_ERROR_NONE) ? QEC_CORRECTED : QEC_DEGENERATE;

    return m;
}

// ============================================================
// Aplicar correccion a un qubit especifico
// ============================================================
int qec_aplicar_correccion(EstadoCuantico* sistema,
                            int tipo_error, int qubit_afectado) {
    if (!_sistema_valido(sistema)) return -1;
    if (qubit_afectado < 0 || qubit_afectado >= sistema->num_qubits) return -1;

    int rc = 0;

    if (tipo_error == QEC_ERROR_BIT_FLIP || tipo_error == QEC_ERROR_BOTH) {
        rc = qc_aplicar_pauli_x(sistema, qubit_afectado);
        if (rc != 0) return rc;
    }

    if (tipo_error == QEC_ERROR_PHASE_FLIP || tipo_error == QEC_ERROR_BOTH) {
        rc = qc_aplicar_pauli_z(sistema, qubit_afectado);
        if (rc != 0) return rc;
    }

    return rc;
}

// ============================================================
// Correccion basada en sindromes
// ============================================================
ResultadoCorreccion qec_corregir_errores(EstadoCuantico* sistema,
                                          const MedicionSindromes* sindromes) {
    ResultadoCorreccion res;
    memset(&res, 0, sizeof(ResultadoCorreccion));

    if (!_sistema_valido(sistema) || !sindromes) {
        res.exito = 0;
        snprintf(res.descripcion, sizeof(res.descripcion),
                 "Error: parametros invalidos");
        return res;
    }

    if (sindromes->tipo_error == QEC_ERROR_NONE) {
        res.exito = 1;
        res.fidelidad_final = 1.0;
        res.errores_corregidos = 0;
        snprintf(res.descripcion, sizeof(res.descripcion),
                 "Sin errores detectados");
        return res;
    }

    // Corregir errores detectados
    int qubit = sindromes->qubit_afectado;
    if (qubit < 0) qubit = 0; // Fallback

    int rc = qec_aplicar_correccion(sistema, sindromes->tipo_error, qubit);
    if (rc != 0) {
        res.exito = 0;
        snprintf(res.descripcion, sizeof(res.descripcion),
                 "Fallo al aplicar correccion en qubit %d", qubit);
        return res;
    }

    res.exito = 1;
    res.fidelidad_final = qc_probabilidad_conservada(sistema);
    res.errores_corregidos = 1;

    const char* tipo_str = "desconocido";
    switch (sindromes->tipo_error) {
        case QEC_ERROR_BIT_FLIP: tipo_str = "bit-flip"; break;
        case QEC_ERROR_PHASE_FLIP: tipo_str = "phase-flip"; break;
        case QEC_ERROR_BOTH: tipo_str = "bit-flip+phase-flip"; break;
    }

    snprintf(res.descripcion, sizeof(res.descripcion),
             "Corregido error %s en qubit fisico %d (fidelidad=%.4f)",
             tipo_str, qubit, res.fidelidad_final);

    return res;
}

// ============================================================
// Ciclo completo: codificar, inyectar error, corregir, verificar
// ============================================================
ResultadoCorreccion qec_proteger_qubit(EstadoCuantico* sistema,
                                        const Complejo* amp_0,
                                        const Complejo* amp_1,
                                        int tipo_error_inyectado,
                                        int qubit_error) {
    ResultadoCorreccion res;
    memset(&res, 0, sizeof(ResultadoCorreccion));

    if (!_sistema_valido(sistema)) {
        snprintf(res.descripcion, sizeof(res.descripcion),
                 "Error: sistema invalido");
        return res;
    }

    // 1. Codificar qubit logico
    int rc = qec_codificar_logico(sistema, 0, amp_0, amp_1);
    if (rc != 0) {
        snprintf(res.descripcion, sizeof(res.descripcion),
                 "Error en codificacion: %d", rc);
        return res;
    }

    // 2. Inyectar error (si se especifica)
    if (tipo_error_inyectado & QEC_ERROR_BIT_FLIP) {
        rc = qec_inyectar_bit_flip(sistema, qubit_error);
        if (rc != 0) return res;
    }
    if (tipo_error_inyectado & QEC_ERROR_PHASE_FLIP) {
        rc = qec_inyectar_phase_flip(sistema, qubit_error);
        if (rc != 0) return res;
    }

    // 3. Medir sindromes y corregir
    MedicionSindromes m = qec_medir_sindromes(sistema);
    res = qec_corregir_errores(sistema, &m);

    return res;
}

// ============================================================
// Verificar estado logico
// ============================================================
int qec_verificar_estado_logico(EstadoCuantico* sistema, int valor_esperado) {
    if (!_sistema_valido(sistema)) return -1;

    // Verificar que el estado sea |0>_L o |1>_L
    // El estado de Shor tiene amplitudes solo en estados
    // donde cada bloque es |000> o |111>

    double prob_estados_correctos = 0.0;
    double prob_estados_incorrectos = 0.0;

    for (int i = 0; i < sistema->num_amplitudes; i++) {
        int b0 = i & 0x7;
        int b1 = (i >> 3) & 0x7;
        int b2 = (i >> 6) & 0x7;

        // Estados validos: cada bloque es 000 (0) o 111 (7)
        int b0_valido = (b0 == 0 || b0 == 7);
        int b1_valido = (b1 == 0 || b1 == 7);
        int b2_valido = (b2 == 0 || b2 == 7);

        if (b0_valido && b1_valido && b2_valido) {
            prob_estados_correctos += sistema->probabilidades[i];

            // Determinar si es |0>_L (paridad par) o |1>_L (paridad impar)
            // |0>_L: numero par de bloques |111>
            // |1>_L: numero impar de bloques |111>
            int num_111 = (b0 == 7 ? 1 : 0) + (b1 == 7 ? 1 : 0) + (b2 == 7 ? 1 : 0);
            int valor_logico = (num_111 % 2 == 0) ? 0 : 1;

            if (valor_logico != valor_esperado) {
                prob_estados_incorrectos += sistema->probabilidades[i];
            }
        } else {
            prob_estados_incorrectos += sistema->probabilidades[i];
        }
    }

    // Si >90% de la probabilidad esta en el estado esperado, exito
    if (prob_estados_correctos > 0.9 && prob_estados_incorrectos < 0.1) {
        return 1;
    }

    return 0;
}

// ============================================================
// Fidelidad contra estado original
// ============================================================
double qec_calcular_fidelidad(EstadoCuantico* sistema,
                               const Complejo* amp_0_original,
                               const Complejo* amp_1_original) {
    if (!_sistema_valido(sistema) || !amp_0_original || !amp_1_original) return -1.0;

    // Fidelidad = |<psi_original|psi_final>|^2
    // Para el codigo de Shor, esto es la probabilidad de medir
    // el estado logico original

    double prob_0L = 0.0;
    double prob_1L = 0.0;

    for (int i = 0; i < sistema->num_amplitudes; i++) {
        int b0 = i & 0x7;
        int b1 = (i >> 3) & 0x7;
        int b2 = (i >> 6) & 0x7;

        if ((b0 == 0 || b0 == 7) && (b1 == 0 || b1 == 7) && (b2 == 0 || b2 == 7)) {
            int num_111 = (b0 == 7 ? 1 : 0) + (b1 == 7 ? 1 : 0) + (b2 == 7 ? 1 : 0);
            if (num_111 % 2 == 0) {
                prob_0L += sistema->probabilidades[i];
            } else {
                prob_1L += sistema->probabilidades[i];
            }
        }
    }

    // Fidelidad = |alpha|^2 * P(0L) + |beta|^2 * P(1L)
    double norm_0 = _c_mod2_local(*amp_0_original);
    double norm_1 = _c_mod2_local(*amp_1_original);

    return norm_0 * prob_0L + norm_1 * prob_1L;
}

// ============================================================
// Decodificar qubit logico
// ============================================================
int qec_decodificar_logico(EstadoCuantico* sistema, int qubit_logico,
                            Complejo* amplitud_0, Complejo* amplitud_1) {
    if (!_sistema_valido(sistema)) return -1;
    if (!amplitud_0 || !amplitud_1) return -1;
    (void)qubit_logico; // La decodificacion siempre usa qubit 0 como logico

    // Decodificar invirtiendo la codificacion de Shor

    // 1. Deshacer phase-flip: H en qubits 0,3,6
    qc_aplicar_hadamard(sistema, 0);
    if (3 < sistema->num_qubits) qc_aplicar_hadamard(sistema, 3);
    if (6 < sistema->num_qubits) qc_aplicar_hadamard(sistema, 6);

    // 2. Deshacer bit-flip: CNOT desde qubits 0→1, 0→2, 3→4, 3→5, 6→7, 6→8
    qc_aplicar_cnot(sistema, 0, 1);
    qc_aplicar_cnot(sistema, 0, 2);
    if (3 < sistema->num_qubits) qc_aplicar_cnot(sistema, 3, 4);
    if (3 < sistema->num_qubits) qc_aplicar_cnot(sistema, 3, 5);
    if (6 < sistema->num_qubits) qc_aplicar_cnot(sistema, 6, 7);
    if (6 < sistema->num_qubits) qc_aplicar_cnot(sistema, 6, 8);

    // 3. Extraer amplitudes del qubit logico (qubit 0)
    amplitud_0->real = 0.0; amplitud_0->imag = 0.0;
    amplitud_1->real = 0.0; amplitud_1->imag = 0.0;

    for (int i = 0; i < sistema->num_amplitudes; i++) {
        if (sistema->probabilidades[i] > 1e-10) {
            int q0 = i & 1;  // Qubit logico (bit 0)
            if (q0 == 0) {
                amplitud_0->real += sistema->amplitudes[i].real;
                amplitud_0->imag += sistema->amplitudes[i].imag;
            } else {
                amplitud_1->real += sistema->amplitudes[i].real;
                amplitud_1->imag += sistema->amplitudes[i].imag;
            }
        }
    }

    return 0;
}

// ============================================================
// Imprimir resultado
// ============================================================
void qec_imprimir_resultado(const ResultadoCorreccion* resultado) {
    if (!resultado) return;
    printf("[QEC] %s\n", resultado->descripcion);
    printf("[QEC] Exito: %s, Fidelidad: %.4f, Errores corregidos: %d\n",
           resultado->exito ? "SI" : "NO",
           resultado->fidelidad_final,
           resultado->errores_corregidos);
}

// ============================================================
// Wrappers _syn_qec_* para enlace con std.quantum_err_corr
// ============================================================
int _syn_qec_inicializar_estado_logico(void* sistema, int valor) {
    return qec_inicializar_estado_logico((EstadoCuantico*)sistema, valor);
}

int _syn_qec_inyectar_bit_flip(void* sistema, int qubit) {
    return qec_inyectar_bit_flip((EstadoCuantico*)sistema, qubit);
}

int _syn_qec_inyectar_phase_flip(void* sistema, int qubit) {
    return qec_inyectar_phase_flip((EstadoCuantico*)sistema, qubit);
}

int _syn_qec_corregir_errores(void* sistema) {
    EstadoCuantico* s = (EstadoCuantico*)sistema;
    MedicionSindromes m = qec_medir_sindromes(s);
    ResultadoCorreccion r = qec_corregir_errores(s, &m);
    return r.exito;
}

int _syn_qec_verificar_estado_logico(void* sistema, int valor_esperado) {
    return qec_verificar_estado_logico((EstadoCuantico*)sistema, valor_esperado);
}
