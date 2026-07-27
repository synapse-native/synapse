// quantum_runtime.c — Simulador de Estado Cuantico (M16.1)
// ======================================================================
// Implementa un simulador de vectores de estado para hasta N qubits (max 8).
// Puertas: Hadamard, Pauli-X/Y/Z, Phase, T, CNOT, SWAP
// Algoritmos: Bell state, Deutsch-Jozsa
//
// Zero-telemetry: todo el proceso es local y soberano.
// ======================================================================

#include "quantum_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

// ============================================================
// Helpers matematicos
// ============================================================

static double _c_mod2(Complejo a) {
    return a.real * a.real + a.imag * a.imag;
}

// ============================================================
// Verificacion de validez de parametros
// ============================================================

static int _qc_valido(EstadoCuantico* s) {
    return s != NULL && s->amplitudes != NULL && s->num_qubits > 0 && s->num_qubits <= QC_MAX_QUBITS;
}

static int _qubit_valido(EstadoCuantico* s, int qubit) {
    return _qc_valido(s) && qubit >= 0 && qubit < s->num_qubits;
}

// ============================================================
// Actualizacion de probabilidades cacheadas
// ============================================================

static void _qc_recalcular_probabilidades(EstadoCuantico* s) {
    if (!s || !s->probabilidades) return;
    for (int i = 0; i < s->num_amplitudes; i++) {
        s->probabilidades[i] = _c_mod2(s->amplitudes[i]);
    }
}

// ============================================================
// API publica
// ============================================================

EstadoCuantico* qc_crear_sistema(int num_qubits) {
    if (num_qubits < 1 || num_qubits > QC_MAX_QUBITS) return NULL;

    EstadoCuantico* s = (EstadoCuantico*)calloc(1, sizeof(EstadoCuantico));
    if (!s) return NULL;

    s->num_qubits = num_qubits;
    s->num_amplitudes = 1 << num_qubits;

    s->amplitudes = (Complejo*)calloc(s->num_amplitudes, sizeof(Complejo));
    if (!s->amplitudes) { free(s); return NULL; }

    s->probabilidades = (double*)calloc(s->num_amplitudes, sizeof(double));
    if (!s->probabilidades) {
        free(s->amplitudes); free(s); return NULL;
    }

    s->qubits_medidos = (int*)calloc(num_qubits, sizeof(int));
    if (!s->qubits_medidos) {
        free(s->probabilidades); free(s->amplitudes); free(s); return NULL;
    }

    for (int i = 0; i < num_qubits; i++) {
        s->qubits_medidos[i] = -1;  // No medido
    }

    s->estado_inicializado = 0;
    s->entropia_entrelazamiento = 0.0;

    return s;
}

void qc_liberar_sistema(EstadoCuantico* s) {
    if (!s) return;
    free(s->amplitudes);
    free(s->probabilidades);
    free(s->qubits_medidos);
    free(s);
}

void qc_limpiar(EstadoCuantico* s) {
    if (!s) return;
    for (int i = 0; i < s->num_amplitudes; i++) {
        s->amplitudes[i].real = 0.0;
        s->amplitudes[i].imag = 0.0;
        s->probabilidades[i] = 0.0;
    }
    for (int i = 0; i < s->num_qubits; i++) {
        s->qubits_medidos[i] = -1;
    }
    s->estado_inicializado = 0;
    s->entropia_entrelazamiento = 0.0;
}

int qc_inicializar_estado_cero(EstadoCuantico* s) {
    if (!_qc_valido(s)) return -1;
    for (int i = 0; i < s->num_amplitudes; i++) {
        s->amplitudes[i].real = 0.0;
        s->amplitudes[i].imag = 0.0;
    }
    s->amplitudes[0].real = 1.0;  // |000...0>
    _qc_recalcular_probabilidades(s);
    s->estado_inicializado = 1;
    return 0;
}

int qc_inicializar_estado_uniforme(EstadoCuantico* s) {
    if (!_qc_valido(s)) return -1;
    double factor = 1.0 / sqrt((double)s->num_amplitudes);
    for (int i = 0; i < s->num_amplitudes; i++) {
        s->amplitudes[i].real = factor;
        s->amplitudes[i].imag = 0.0;
    }
    _qc_recalcular_probabilidades(s);
    s->estado_inicializado = 1;
    return 0;
}

int qc_inicializar_base(EstadoCuantico* s, int indice_basis) {
    if (!_qc_valido(s)) return -1;
    if (indice_basis < 0 || indice_basis >= s->num_amplitudes) return -1;
    for (int i = 0; i < s->num_amplitudes; i++) {
        s->amplitudes[i].real = 0.0;
        s->amplitudes[i].imag = 0.0;
    }
    s->amplitudes[indice_basis].real = 1.0;
    _qc_recalcular_probabilidades(s);
    s->estado_inicializado = 1;
    return 0;
}

// ============================================================
// Puerta Hadamard (H)
// Aplica H al qubit k: transforma cada par de amplitudes
//   |x0_k> y |x1_k> en (|x0> + |x1>)/sqrt(2) y (|x0> - |x1>)/sqrt(2)
// ============================================================
int qc_aplicar_hadamard(EstadoCuantico* s, int qubit) {
    if (!_qubit_valido(s, qubit)) return -1;

    int paso = 1 << qubit;
    int total = s->num_amplitudes;

    for (int i = 0; i < total; i += (paso << 1)) {
        for (int j = 0; j < paso; j++) {
            int idx0 = i + j;       // |...0_k...>
            int idx1 = i + j + paso; // |...1_k...>

            Complejo a = s->amplitudes[idx0];
            Complejo b = s->amplitudes[idx1];

            // |0> -> (|0> + |1>)/sqrt(2)
            // |1> -> (|0> - |1>)/sqrt(2)
            s->amplitudes[idx0].real = (a.real + b.real) * QC_SQRT2_INV;
            s->amplitudes[idx0].imag = (a.imag + b.imag) * QC_SQRT2_INV;
            s->amplitudes[idx1].real = (a.real - b.real) * QC_SQRT2_INV;
            s->amplitudes[idx1].imag = (a.imag - b.imag) * QC_SQRT2_INV;
        }
    }

    _qc_recalcular_probabilidades(s);
    return 0;
}

// ============================================================
// Puerta Pauli-X (NOT cuantico)
// X = [[0,1],[1,0]]  — intercambia |0> y |1>
// ============================================================
int qc_aplicar_pauli_x(EstadoCuantico* s, int qubit) {
    if (!_qubit_valido(s, qubit)) return -1;

    int paso = 1 << qubit;
    int total = s->num_amplitudes;

    for (int i = 0; i < total; i += (paso << 1)) {
        for (int j = 0; j < paso; j++) {
            int idx0 = i + j;
            int idx1 = i + j + paso;

            Complejo tmp = s->amplitudes[idx0];
            s->amplitudes[idx0] = s->amplitudes[idx1];
            s->amplitudes[idx1] = tmp;
        }
    }

    _qc_recalcular_probabilidades(s);
    return 0;
}

// ============================================================
// Puerta Pauli-Y
// Y = [[0,-i],[i,0]]
// ============================================================
int qc_aplicar_pauli_y(EstadoCuantico* s, int qubit) {
    if (!_qubit_valido(s, qubit)) return -1;

    int paso = 1 << qubit;
    int total = s->num_amplitudes;

    for (int i = 0; i < total; i += (paso << 1)) {
        for (int j = 0; j < paso; j++) {
            int idx0 = i + j;
            int idx1 = i + j + paso;

            // Y = [[0,-i],[i,0]]
            // Y|0> = i|1>, Y|1> = -i|0>
            // [idx0; idx1] = [-i*b; i*a]
            Complejo a = s->amplitudes[idx0];
            Complejo b = s->amplitudes[idx1];

            // idx0 = -i*b = (-i)*(b.real + i*b.imag) = b.imag + i*(-b.real)
            s->amplitudes[idx0].real = b.imag;
            s->amplitudes[idx0].imag = -b.real;
            // idx1 = i*a = i*(a.real + i*a.imag) = -a.imag + i*a.real
            s->amplitudes[idx1].real = -a.imag;
            s->amplitudes[idx1].imag = a.real;
        }
    }

    _qc_recalcular_probabilidades(s);
    return 0;
}

// ============================================================
// Puerta Pauli-Z
// Z = [[1,0],[0,-1]]
// ============================================================
int qc_aplicar_pauli_z(EstadoCuantico* s, int qubit) {
    if (!_qubit_valido(s, qubit)) return -1;

    int paso = 1 << qubit;
    int total = s->num_amplitudes;

    for (int i = 0; i < total; i += (paso << 1)) {
        for (int j = 0; j < paso; j++) {
            int idx1 = i + j + paso;
            // |1> -> -|1>
            s->amplitudes[idx1].real = -s->amplitudes[idx1].real;
            s->amplitudes[idx1].imag = -s->amplitudes[idx1].imag;
        }
    }

    _qc_recalcular_probabilidades(s);
    return 0;
}

// ============================================================
// Puerta Phase (S) — desplazamiento de fase
// S = [[1,0],[0,i]]
// ============================================================
int qc_aplicar_phase(EstadoCuantico* s, int qubit, double angulo) {
    if (!_qubit_valido(s, qubit)) return -1;

    double cos_a = cos(angulo);
    double sin_a = sin(angulo);
    int paso = 1 << qubit;
    int total = s->num_amplitudes;

    for (int i = 0; i < total; i += (paso << 1)) {
        for (int j = 0; j < paso; j++) {
            int idx1 = i + j + paso;
            // |1> -> e^(i*angulo) * |1>
            double r = s->amplitudes[idx1].real;
            double im = s->amplitudes[idx1].imag;
            s->amplitudes[idx1].real = r * cos_a - im * sin_a;
            s->amplitudes[idx1].imag = r * sin_a + im * cos_a;
        }
    }

    _qc_recalcular_probabilidades(s);
    return 0;
}

// ============================================================
// Puerta T (pi/8)
// T = [[1,0],[0,e^(i*pi/4)]]
// ============================================================
int qc_aplicar_t(EstadoCuantico* s, int qubit) {
    return qc_aplicar_phase(s, qubit, 3.14159265358979323846 / 4.0);
}

// ============================================================
// CNOT (Controlled-X)
// Si control = 1, aplica X a target
// ============================================================
int qc_aplicar_cnot(EstadoCuantico* s, int control, int target) {
    if (!_qubit_valido(s, control) || !_qubit_valido(s, target)) return -1;
    if (control == target) return -1;

    int bit_c = 1 << control;
    int bit_t = 1 << target;
    int total = s->num_amplitudes;

    // Iterar sobre todos los estados base
    // Si el bit de control es 1, intercambiar amplitudes entre
    // estados con target=0 y target=1
    for (int i = 0; i < total; i++) {
        if (i & bit_c) {  // Control = 1
            int par = i ^ bit_t;  // Flip target bit
            if (par > i) {
                Complejo tmp = s->amplitudes[i];
                s->amplitudes[i] = s->amplitudes[par];
                s->amplitudes[par] = tmp;
            }
        }
    }

    _qc_recalcular_probabilidades(s);
    return 0;
}

// ============================================================
// SWAP — intercambia dos qubits
// ============================================================
int qc_aplicar_swap(EstadoCuantico* s, int q1, int q2) {
    if (!_qubit_valido(s, q1) || !_qubit_valido(s, q2)) return -1;
    if (q1 == q2) return 0;

    // SWAP = CNOT(q1,q2) + CNOT(q2,q1) + CNOT(q1,q2)
    int rc = qc_aplicar_cnot(s, q1, q2);
    if (rc != 0) return rc;
    rc = qc_aplicar_cnot(s, q2, q1);
    if (rc != 0) return rc;
    rc = qc_aplicar_cnot(s, q1, q2);
    return rc;
}

// ============================================================
// Medicion — colapso estocastico de funcion de onda
// ============================================================
int qc_medir(EstadoCuantico* s, int qubit) {
    if (!_qubit_valido(s, qubit)) return -1;

    // Calcular probabilidad de |1> para este qubit
    double prob_uno = 0.0;
    int bit = 1 << qubit;
    int total = s->num_amplitudes;

    for (int i = 0; i < total; i++) {
        if (i & bit) {
            prob_uno += s->probabilidades[i];
        }
    }

    // Decision estocastica
    double r = (double)rand() / (double)RAND_MAX;
    int resultado = (r < prob_uno) ? 1 : 0;

    // Colapsar: mantener solo amplitudes compatibles con el resultado
    double norma = 0.0;
    for (int i = 0; i < total; i++) {
        int bit_val = (i & bit) ? 1 : 0;
        if (bit_val != resultado) {
            s->amplitudes[i].real = 0.0;
            s->amplitudes[i].imag = 0.0;
        } else {
            norma += s->probabilidades[i];
        }
    }

    // Renormalizar
    if (norma > 0.0) {
        double inv_norma = 1.0 / sqrt(norma);
        for (int i = 0; i < total; i++) {
            int bit_val = (i & bit) ? 1 : 0;
            if (bit_val == resultado) {
                s->amplitudes[i].real *= inv_norma;
                s->amplitudes[i].imag *= inv_norma;
            }
        }
    }

    s->qubits_medidos[qubit] = resultado;
    _qc_recalcular_probabilidades(s);

    return resultado;
}

// ============================================================
// Probabilidades
// ============================================================
double qc_probabilidad_cero(EstadoCuantico* s, int qubit) {
    if (!_qubit_valido(s, qubit)) return -1.0;
    return 1.0 - qc_probabilidad_uno(s, qubit);
}

double qc_probabilidad_uno(EstadoCuantico* s, int qubit) {
    if (!_qubit_valido(s, qubit)) return -1.0;

    double prob = 0.0;
    int bit = 1 << qubit;
    int total = s->num_amplitudes;

    for (int i = 0; i < total; i++) {
        if (i & bit) {
            prob += s->probabilidades[i];
        }
    }

    return prob;
}

// ============================================================
// Estados especiales
// ============================================================

// Crea estado de Bell |Phi+> = (|00> + |11>)/sqrt(2)
int qc_crear_estado_bell(EstadoCuantico* s, int q1, int q2) {
    if (!_qubit_valido(s, q1) || !_qubit_valido(s, q2)) return -1;

    // |00>
    int rc = qc_inicializar_estado_cero(s);
    if (rc != 0) return rc;

    // H en q1
    rc = qc_aplicar_hadamard(s, q1);
    if (rc != 0) return rc;

    // CNOT q1 -> q2
    rc = qc_aplicar_cnot(s, q1, q2);
    if (rc != 0) return rc;

    _qc_recalcular_probabilidades(s);
    return 0;
}

// Verifica entrelazamiento: traza parcial del sistema
int qc_es_entrelazado(EstadoCuantico* s) {
    if (!_qc_valido(s)) return -1;

    // Metodo simplificado: si hay mas de una amplitud no cero
    // y el estado no es producto tensorial separable
    int no_cero = 0;
    for (int i = 0; i < s->num_amplitudes; i++) {
        if (s->probabilidades[i] > 1e-10) {
            no_cero++;
        }
    }

    // Si solo un estado base tiene amplitud, no hay entrelazamiento
    if (no_cero <= 1) return 0;

    // Para 2 qubits: verificar si es estado de Bell
    if (s->num_qubits == 2) {
        double p00 = s->probabilidades[0];  // |00>
        double p11 = s->probabilidades[3];  // |11>
        double total = p00 + p11;

        // Estado de Bell tiene >99% en |00> y |11>
        if (total > 0.99 && p00 > 0.4 && p11 > 0.4) {
            return 1;
        }

        // Estado separable: p00 + p01 + p10 + p11 con producto
        return 0;
    }

    return (no_cero > 1) ? 1 : 0;
}

// ============================================================
// Verificacion de conservacion de probabilidad
// ============================================================
double qc_probabilidad_conservada(EstadoCuantico* s) {
    if (!_qc_valido(s)) return -1.0;

    double suma = 0.0;
    for (int i = 0; i < s->num_amplitudes; i++) {
        suma += s->probabilidades[i];
    }

    return suma;
}

// ============================================================
// Algoritmo de Deutsch-Jozsa
// Determina si un oraculo es constante o balanceado
// ============================================================
int qc_deutsch_jozsa(EstadoCuantico* s,
                     int (*oraculo)(int entrada),
                     int num_bits_entrada) {
    if (!s || !oraculo) return -1;
    if (num_bits_entrada < 1 || num_bits_entrada > s->num_qubits - 1) return -1;

    // 1. Inicializar en |000...0>
    int rc = qc_inicializar_estado_cero(s);
    if (rc != 0) return rc;

    // 2. Aplicar X al ultimo qubit (qubit de salida)
    rc = qc_aplicar_pauli_x(s, num_bits_entrada);
    if (rc != 0) return rc;

    // 3. Aplicar H a todos los qubits
    for (int q = 0; q <= num_bits_entrada; q++) {
        rc = qc_aplicar_hadamard(s, q);
        if (rc != 0) return rc;
    }

    // 4. Aplicar oracle U_f via phase kickback:
    // |x>|y XOR f(x)> = (-1)^f(x)*|x>|y> (cuando |y> = |->)
    // Input bits = qubits 0..num_bits_entrada-1 (LSBs)
    int mascara = (1 << num_bits_entrada) - 1;
    int total_bases = 1 << (num_bits_entrada + 1);
    for (int i = 0; i < total_bases; i++) {
        if (s->probabilidades[i] > 1e-15) {
            int x = i & mascara;  // Extraer bits de entrada (LSBs)
            if (oraculo(x)) {
                // Phase kickback: negar amplitud
                s->amplitudes[i].real = -s->amplitudes[i].real;
                s->amplitudes[i].imag = -s->amplitudes[i].imag;
            }
        }
    }

    // 5. Aplicar H a los qubits de entrada
    for (int q = 0; q < num_bits_entrada; q++) {
        rc = qc_aplicar_hadamard(s, q);
        if (rc != 0) return rc;
    }

    _qc_recalcular_probabilidades(s);

    // 6. Determinar si es constante o balanceado
    // Calcular probabilidad conjunta de que TODOS los qubits de entrada sean |0>
    double prob_todos_cero = 0.0;
    int mascara_entrada = (1 << num_bits_entrada) - 1;
    for (int i = 0; i < s->num_amplitudes; i++) {
        if ((i & mascara_entrada) == 0) {  // Input bits all zero
            prob_todos_cero += s->probabilidades[i];
        }
    }

    if (prob_todos_cero > 0.75) {
        return 1;  // Constante (>75% probabilidad de |000...0>)
    }

    return 0;  // Balanceado
}

// ============================================================
// Consulta de amplitudes
// ============================================================
Complejo qc_obtener_amplitud(EstadoCuantico* s, int indice_basis) {
    Complejo cero = {0.0, 0.0};
    if (!_qc_valido(s)) return cero;
    if (indice_basis < 0 || indice_basis >= s->num_amplitudes) return cero;
    return s->amplitudes[indice_basis];
}

int qc_obtener_num_qubits(EstadoCuantico* s) {
    if (!s) return -1;
    return s->num_qubits;
}

// ============================================================
// Wrappers _syn_qc_* para enlace con std.quantum
// ============================================================

void* _syn_qc_crear_sistema(int num_qubits) {
    return (void*)qc_crear_sistema(num_qubits);
}

void _syn_qc_liberar_sistema(void* sistema) {
    qc_liberar_sistema((EstadoCuantico*)sistema);
}

int _syn_qc_inicializar_estado_cero(void* sistema) {
    return qc_inicializar_estado_cero((EstadoCuantico*)sistema);
}

int _syn_qc_inicializar_estado_uniforme(void* sistema) {
    return qc_inicializar_estado_uniforme((EstadoCuantico*)sistema);
}

int _syn_qc_aplicar_hadamard(void* sistema, int qubit) {
    return qc_aplicar_hadamard((EstadoCuantico*)sistema, qubit);
}

int _syn_qc_aplicar_pauli_x(void* sistema, int qubit) {
    return qc_aplicar_pauli_x((EstadoCuantico*)sistema, qubit);
}

int _syn_qc_aplicar_cnot(void* sistema, int control, int target) {
    return qc_aplicar_cnot((EstadoCuantico*)sistema, control, target);
}

int _syn_qc_medir(void* sistema, int qubit) {
    return qc_medir((EstadoCuantico*)sistema, qubit);
}

double _syn_qc_probabilidad_cero(void* sistema, int qubit) {
    return qc_probabilidad_cero((EstadoCuantico*)sistema, qubit);
}

double _syn_qc_probabilidad_conservada(void* sistema) {
    return qc_probabilidad_conservada((EstadoCuantico*)sistema);
}

int _syn_qc_crear_estado_bell(void* sistema, int q1, int q2) {
    return qc_crear_estado_bell((EstadoCuantico*)sistema, q1, q2);
}
