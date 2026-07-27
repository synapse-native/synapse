// surface_code.c — Surface Code / Topological Error Correction (M16.3)
// ======================================================================
// Implementa correccion topologica de errores sobre una rejilla 2D LxL.
// Estabilizadores tipo X (estrella) alrededor de vertices,
// tipo Z (plaqueta) alrededor de celdas.
// Decodificador: Union-Find con agrupacion de sindromes.
//
// Zero-telemetry: todo el proceso es local y soberano.
// ======================================================================

#include "surface_code.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

// ============================================================
// Helpers internos
// ============================================================

static int _idx(SurfaceCode* r, int fila, int col) {
    return fila * r->L + col;
}

static int _idx_const(const SurfaceCode* r, int fila, int col) {
    return fila * r->L + col;
}

static int _valido(SurfaceCode* r) {
    return r != NULL && r->data_qubits != NULL && r->estabilizadores != NULL
           && r->L >= 2 && r->L <= SC_MAX_L;
}

static int _pos_valida(SurfaceCode* r, int fila, int col) {
    return _valido(r) && fila >= 0 && fila < r->L && col >= 0 && col < r->L;
}

// ============================================================
// Creacion y liberacion de rejilla
// ============================================================

SurfaceCode* sc_crear_rejilla(int L) {
    if (L < 2 || L > SC_MAX_L) return NULL;

    SurfaceCode* r = (SurfaceCode*)calloc(1, sizeof(SurfaceCode));
    if (!r) return NULL;

    r->L = L;
    r->num_qubits = L * L;

    // Crear qubits de datos
    r->data_qubits = (SCDataQubit*)calloc(r->num_qubits, sizeof(SCDataQubit));
    if (!r->data_qubits) { free(r); return NULL; }

    // Crear estabilizadores
    // X-stabilizers (estrella): en cada vertice interior (L-1)*(L-1)
    // Z-stabilizers (plaqueta): en cada celda (L-1)*(L-1)
    int max_estab = 2 * (L - 1) * (L - 1) + 4 * (L - 1); // Interior + bordes
    if (max_estab > SC_MAX_STABILIZERS) max_estab = SC_MAX_STABILIZERS;

    r->estabilizadores = (SCStabilizer*)calloc(max_estab, sizeof(SCStabilizer));
    if (!r->estabilizadores) { free(r->data_qubits); free(r); return NULL; }

    // Configurar estabilizadores X (estrella): en cada vertice (i,j) con 0<=i,j<=L-2
    // Rodea 4 qubits: (i,j), (i,j+1), (i+1,j), (i+1,j+1)
    int n_estab = 0;

    for (int i = 0; i < L - 1; i++) {
        for (int j = 0; j < L - 1; j++) {
            SCStabilizer* s = &r->estabilizadores[n_estab];
            s->tipo = SC_STAB_X;
            s->fila = i;
            s->col = j;
            s->qubits[0] = _idx(r, i, j);
            s->qubits[1] = _idx(r, i, j + 1);
            s->qubits[2] = _idx(r, i + 1, j);
            s->qubits[3] = _idx(r, i + 1, j + 1);
            s->num_qubits = 4;
            n_estab++;
        }
    }

    // Configurar estabilizadores Z (plaqueta): en cada celda (i,j) con 0<=i,j<=L-2
    // Misma topologia pero operador Z
    for (int i = 0; i < L - 1; i++) {
        for (int j = 0; j < L - 1; j++) {
            SCStabilizer* s = &r->estabilizadores[n_estab];
            s->tipo = SC_STAB_Z;
            s->fila = i;
            s->col = j;
            s->qubits[0] = _idx(r, i, j);
            s->qubits[1] = _idx(r, i, j + 1);
            s->qubits[2] = _idx(r, i + 1, j);
            s->qubits[3] = _idx(r, i + 1, j + 1);
            s->num_qubits = 4;
            n_estab++;
        }
    }

    r->num_estabilizadores = n_estab;

    // Arreglos de sindromes
    r->sindrome_x = (int*)calloc(SC_MAX_SYNDROMES, sizeof(int));
    r->sindrome_z = (int*)calloc(SC_MAX_SYNDROMES, sizeof(int));
    if (!r->sindrome_x || !r->sindrome_z) {
        free(r->sindrome_z); free(r->sindrome_x);
        free(r->estabilizadores); free(r->data_qubits); free(r);
        return NULL;
    }

    r->tasa_error = 0.0;
    r->estado = SC_CORRECTED;

    return r;
}

void sc_liberar_rejilla(SurfaceCode* r) {
    if (!r) return;
    free(r->sindrome_z);
    free(r->sindrome_x);
    free(r->estabilizadores);
    free(r->data_qubits);
    free(r);
}

void sc_limpiar_rejilla(SurfaceCode* r) {
    if (!_valido(r)) return;
    for (int i = 0; i < r->num_qubits; i++) {
        r->data_qubits[i].error_x = 0.0;
        r->data_qubits[i].error_z = 0.0;
        r->data_qubits[i].corregido = 0;
        r->data_qubits[i].etiqueta_union = i;
    }
    for (int i = 0; i < r->num_estabilizadores; i++) {
        r->estabilizadores[i].activo = 0;
    }
    r->num_sindrome_x = 0;
    r->num_sindrome_z = 0;
    r->tasa_error = 0.0;
    r->estado = SC_CORRECTED;
}

// ============================================================
// Inicializacion
// ============================================================

int sc_inicializar_estado_cero(SurfaceCode* r) {
    if (!_valido(r)) return -1;
    sc_limpiar_rejilla(r);
    return 0;
}

// ============================================================
// Inyeccion de errores
// ============================================================

int sc_inyectar_error_en(SurfaceCode* r, int fila, int col, int tipo_error) {
    if (!_pos_valida(r, fila, col)) return -1;

    int idx = _idx(r, fila, col);
    if (tipo_error == SC_ERROR_X || tipo_error == SC_ERROR_BOTH) {
        r->data_qubits[idx].error_x = 1.0;
    }
    if (tipo_error == SC_ERROR_Z || tipo_error == SC_ERROR_BOTH) {
        r->data_qubits[idx].error_z = 1.0;
    }

    // Recalcular tasa de error
    int total_con_error = 0;
    for (int i = 0; i < r->num_qubits; i++) {
        if (r->data_qubits[i].error_x > 0.5 || r->data_qubits[i].error_z > 0.5) {
            total_con_error++;
        }
    }
    r->tasa_error = (double)total_con_error / (double)r->num_qubits;

    return 0;
}

int sc_inyectar_cadena_error(SurfaceCode* r, int tipo_error,
                              int f_inicio, int c_inicio,
                              int f_fin, int c_fin) {
    if (!_valido(r)) return -1;

    int f_min = (f_inicio < f_fin) ? f_inicio : f_fin;
    int f_max = (f_inicio > f_fin) ? f_inicio : f_fin;
    int c_min = (c_inicio < c_fin) ? c_inicio : c_fin;
    int c_max = (c_inicio > c_fin) ? c_inicio : c_fin;

    // Inyectar error a lo largo del camino Manhattan
    for (int f = f_min; f <= f_max; f++) {
        for (int c = c_min; c <= c_max; c++) {
            if (_pos_valida(r, f, c)) {
                int rc = sc_inyectar_error_en(r, f, c, tipo_error);
                if (rc != 0) return rc;
            }
        }
    }

    return 0;
}

// ============================================================
// Medicion de estabilizadores
// ============================================================

int sc_medir_estabilizadores(SurfaceCode* r) {
    if (!_valido(r)) return -1;

    // Resetear sindromes
    for (int i = 0; i < r->num_estabilizadores; i++) {
        r->estabilizadores[i].activo = 0;
    }
    r->num_sindrome_x = 0;
    r->num_sindrome_z = 0;

    // Medir cada estabilizador
    for (int i = 0; i < r->num_estabilizadores; i++) {
        SCStabilizer* s = &r->estabilizadores[i];
        int paridad = 0;

        // Calcular paridad del error en los qubits asociados
        for (int q = 0; q < s->num_qubits; q++) {
            int idx = s->qubits[q];
            if (idx < 0 || idx >= r->num_qubits) continue;

            if (s->tipo == SC_STAB_X) {
                // X-stabilizer: detecta errores X en data qubits
                if (r->data_qubits[idx].error_x > 0.5) {
                    paridad ^= 1;
                }
            } else {
                // Z-stabilizer: detecta errores Z en data qubits
                if (r->data_qubits[idx].error_z > 0.5) {
                    paridad ^= 1;
                }
            }
        }

        s->activo = paridad;

        // Registrar sindrome
        if (paridad) {
            if (s->tipo == SC_STAB_X && r->num_sindrome_x < SC_MAX_SYNDROMES - 1) {
                r->sindrome_x[r->num_sindrome_x++] = i;
            } else if (s->tipo == SC_STAB_Z && r->num_sindrome_z < SC_MAX_SYNDROMES - 1) {
                r->sindrome_z[r->num_sindrome_z++] = i;
            }
        }
    }

    // Actualizar estado de la rejilla
    if (r->num_sindrome_x > 0 || r->num_sindrome_z > 0) {
        r->estado = SC_UNCORRECTED;
    } else {
        r->estado = SC_CORRECTED;
    }

    return 0;
}

// ============================================================
// Decodificador Union-Find
// ============================================================

// Encontrar raiz de un cluster (Union-Find con compression de ruta)
static int _uf_encontrar(SurfaceCode* r, int idx) {
    if (idx < 0 || idx >= r->num_qubits) return idx;
    SCDataQubit* q = &r->data_qubits[idx];
    if (q->etiqueta_union != idx) {
        q->etiqueta_union = _uf_encontrar(r, q->etiqueta_union);
    }
    return q->etiqueta_union;
}

// Unir dos clusters
static void _uf_unir(SurfaceCode* r, int a, int b) {
    int ra = _uf_encontrar(r, a);
    int rb = _uf_encontrar(r, b);
    if (ra != rb) {
        r->data_qubits[rb].etiqueta_union = ra;
    }
}

int sc_decodificar_union_find(SurfaceCode* r) {
    if (!_valido(r)) return -1;

    // Inicializar Union-Find: cada qubit es su propio cluster
    for (int i = 0; i < r->num_qubits; i++) {
        r->data_qubits[i].etiqueta_union = i;
    }

    // Si no hay sindromes, no hay nada que decodificar
    if (r->num_sindrome_x == 0 && r->num_sindrome_z == 0) {
        return 0;
    }

    // Fase 1: Agrupar sindromes adyacentes en clusters
    // Para cada estabilizador activo, unir sus qubits asociados
    for (int i = 0; i < r->num_estabilizadores; i++) {
        SCStabilizer* s = &r->estabilizadores[i];
        if (!s->activo) continue;

        // Unir todos los qubits de este estabilizador
        for (int q = 1; q < s->num_qubits; q++) {
            _uf_unir(r, s->qubits[0], s->qubits[q]);
        }
    }

    // Fase 2: Encontrar qubits con error dentro de cada cluster
    // Un cluster con sindrome necesita al menos un error dentro
    // Identificar los qubits candidatos para correccion
    // Para simplificar: corregir todos los qubits en clusters con sindromes
    int corregidos = 0;

    // Recorrer clusters via los sindromes
    for (int i = 0; i < r->num_sindrome_x; i++) {
        int si = r->sindrome_x[i];
        if (si < 0 || si >= r->num_estabilizadores) continue;
        SCStabilizer* s = &r->estabilizadores[si];
        if (s->tipo != SC_STAB_X) continue;

        // Este cluster necesita correccion X
        int raiz = _uf_encontrar(r, s->qubits[0]);
        for (int q = 0; q < s->num_qubits; q++) {
            int idx = s->qubits[q];
            if (idx < 0 || idx >= r->num_qubits) continue;
            if (_uf_encontrar(r, idx) == raiz) {
                // Marcar qubit para correccion X
                r->data_qubits[idx].corregido = 1;
                corregidos++;
            }
        }
    }

    for (int i = 0; i < r->num_sindrome_z; i++) {
        int si = r->sindrome_z[i];
        if (si < 0 || si >= r->num_estabilizadores) continue;
        SCStabilizer* s = &r->estabilizadores[si];
        if (s->tipo != SC_STAB_Z) continue;

        int raiz = _uf_encontrar(r, s->qubits[0]);
        for (int q = 0; q < s->num_qubits; q++) {
            int idx = s->qubits[q];
            if (idx < 0 || idx >= r->num_qubits) continue;
            if (_uf_encontrar(r, idx) == raiz) {
                r->data_qubits[idx].corregido = 1;
                corregidos++;
            }
        }
    }

    return corregidos;
}

// ============================================================
// Correccion de errores
// ============================================================

int sc_corregir_errores(SurfaceCode* r) {
    if (!_valido(r)) return -1;

    // Aplicar correccion: limpiar errores en qubits marcados como corregidos
    int corregidos = 0;

    for (int i = 0; i < r->num_qubits; i++) {
        SCDataQubit* q = &r->data_qubits[i];
        if (q->corregido) {
            if (q->error_x > 0.5) {
                q->error_x = 0.0;
                corregidos++;
            }
            if (q->error_z > 0.5) {
                q->error_z = 0.0;
                corregidos++;
            }
            q->corregido = 0;
        }
    }

    // Verificar si quedan errores
    int restantes = sc_obtener_num_errores(r);
    if (restantes == 0) {
        r->estado = SC_CORRECTED;
    }

    return corregidos;
}

// ============================================================
// Ciclo completo: inyectar errores -> medir -> decodificar -> corregir
// ============================================================

SCResultado sc_ciclo_completo(SurfaceCode* r, int num_errores_x, int num_errores_z) {
    SCResultado res;
    memset(&res, 0, sizeof(SCResultado));

    if (!_valido(r)) {
        snprintf(res.descripcion, sizeof(res.descripcion), "Error: rejilla invalida");
        return res;
    }

    // Inicializar
    sc_inicializar_estado_cero(r);

    // Inyectar errores X aleatorios
    int inyectados = 0;
    for (int i = 0; i < num_errores_x && i < r->num_qubits; i++) {
        int idx = (i * 7 + 3) % r->num_qubits; // Deterministico
        int f = idx / r->L;
        int c = idx % r->L;
        sc_inyectar_error_en(r, f, c, SC_ERROR_X);
        inyectados++;
    }
    for (int i = 0; i < num_errores_z && i < r->num_qubits; i++) {
        int idx = (i * 11 + 5) % r->num_qubits;
        int f = idx / r->L;
        int c = idx % r->L;
        sc_inyectar_error_en(r, f, c, SC_ERROR_Z);
        inyectados++;
    }

    res.errores_detectados = inyectados;

    // Medir estabilizadores
    sc_medir_estabilizadores(r);

    // Decodificar
    int candidatos = sc_decodificar_union_find(r);
    if (candidatos < 0) {
        snprintf(res.descripcion, sizeof(res.descripcion),
                 "Error en decodificacion");
        return res;
    }

    // Corregir
    int corregidos = sc_corregir_errores(r);
    res.errores_corregidos = corregidos;

    // Verificar
    if (sc_verificar_correccion(r)) {
        res.exito = 1;
        res.fidelidad = 1.0;
        res.errores_restantes = 0;
        snprintf(res.descripcion, sizeof(res.descripcion),
                 "Correccion topologica exitosa: %d errores corregidos en rejilla %dx%d",
                 corregidos, r->L, r->L);
    } else {
        res.exito = 0;
        res.errores_restantes = sc_obtener_num_errores(r);
        res.fidelidad = 1.0 - (double)res.errores_restantes / (double)r->num_qubits;
        snprintf(res.descripcion, sizeof(res.descripcion),
                 "Correccion parcial: %d/%d errores corregidos, %d restantes",
                 corregidos, inyectados, res.errores_restantes);
    }

    return res;
}

// ============================================================
// Verificacion
// ============================================================

int sc_verificar_correccion(SurfaceCode* r) {
    if (!_valido(r)) return -1;

    for (int i = 0; i < r->num_qubits; i++) {
        if (r->data_qubits[i].error_x > 0.5 || r->data_qubits[i].error_z > 0.5) {
            return 0; // Aun hay errores
        }
    }

    return 1; // Sin errores
}

double sc_calcular_fidelidad(SurfaceCode* r) {
    if (!_valido(r)) return -1.0;

    int errores = sc_obtener_num_errores(r);
    return 1.0 - (double)errores / (double)(r->num_qubits * 2);
}

// ============================================================
// Utilidades
// ============================================================

int sc_obtener_num_errores(SurfaceCode* r) {
    if (!_valido(r)) return -1;

    int total = 0;
    for (int i = 0; i < r->num_qubits; i++) {
        if (r->data_qubits[i].error_x > 0.5) total++;
        if (r->data_qubits[i].error_z > 0.5) total++;
    }
    return total;
}

void sc_imprimir_rejilla(const SurfaceCode* r) {
    if (!r || !r->data_qubits) return;

    printf("Rejilla Surface Code %dx%d\n", r->L, r->L);
    printf("Qubits de datos: %d, Estabilizadores: %d (X:%d Z:%d)\n",
           r->num_qubits, r->num_estabilizadores,
           r->num_estabilizadores / 2, r->num_estabilizadores / 2);
    printf("Sindromes activos: X:%d Z:%d\n", r->num_sindrome_x, r->num_sindrome_z);
    printf("Tasa de error: %.2f\n", r->tasa_error);

    printf("\nMapa de errores X:\n");
    for (int f = 0; f < r->L; f++) {
        for (int c = 0; c < r->L; c++) {
            int idx = _idx_const(r, f, c);
            printf("%c ", r->data_qubits[idx].error_x > 0.5 ? 'X' : '.');
        }
        printf("\n");
    }

    printf("Mapa de errores Z:\n");
    for (int f = 0; f < r->L; f++) {
        for (int c = 0; c < r->L; c++) {
            int idx = _idx_const(r, f, c);
            printf("%c ", r->data_qubits[idx].error_z > 0.5 ? 'Z' : '.');
        }
        printf("\n");
    }
}

// ============================================================
// Wrappers _syn_sc_* para enlace con std.surface_code
// ============================================================

void* _syn_sc_crear_rejilla(int L) {
    return (void*)sc_crear_rejilla(L);
}

void _syn_sc_liberar_rejilla(void* r) {
    sc_liberar_rejilla((SurfaceCode*)r);
}

int _syn_sc_inicializar_estado_cero(void* r) {
    return sc_inicializar_estado_cero((SurfaceCode*)r);
}

int _syn_sc_inyectar_error(void* r, int fila, int col, int tipo) {
    return sc_inyectar_error_en((SurfaceCode*)r, fila, col, tipo);
}

int _syn_sc_medir_estabilizadores(void* r) {
    return sc_medir_estabilizadores((SurfaceCode*)r);
}

int _syn_sc_corregir_errores(void* r) {
    SurfaceCode* rejilla = (SurfaceCode*)r;
    sc_medir_estabilizadores(rejilla);
    sc_decodificar_union_find(rejilla);
    return sc_corregir_errores(rejilla);
}

int _syn_sc_verificar_correccion(void* r) {
    return sc_verificar_correccion((SurfaceCode*)r);
}
