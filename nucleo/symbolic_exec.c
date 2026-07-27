// symbolic_exec.c — Motor de Ejecución Simbólica (M15.3)
// ======================================================================
// Implementa la exploración de rutas de ejecución sobre valores simbólicos,
// integración con el motor ATP y detección de violaciones de contratos.
//
// Flujo de exploración:
//   1. Crear variables simbólicas con cotas
//   2. Agregar restricciones a la ruta activa
//   3. Bifurcar en condiciones de control (si/sino)
//   4. Verificar alcanzabilidad de cada ruta
//   5. Detectar violaciones (div/0, overflow, bounds, contract)
//   6. Explorar sistemáticamente todas las rutas factibles
//
// Zero-telemetry: todo el proceso es local y soberano.
// ======================================================================

#include "symbolic_exec.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <ctype.h>

// ============================================================
// Helpers internos
// ============================================================

// Tokenizador simple para expresiones simbólicas
static int _se_tokenizar(const char* expr, char tokens[256][SE_MAX_VAR_NAME], int* num_tokens) {
    if (!expr || !tokens || !num_tokens) return -1;

    char buf[SE_MAX_EXPR_LEN];
    snprintf(buf, SE_MAX_EXPR_LEN, "%s", expr);

    int n = 0;
    char* p = buf;
    while (*p && n < 256) {
        while (*p == ' ' || *p == '\t') p++;
        if (!*p) break;

        // Operadores multi-carácter
        if (strncmp(p, "&&", 2) == 0) { strcpy(tokens[n], "&&"); p += 2; n++; continue; }
        if (strncmp(p, "||", 2) == 0) { strcpy(tokens[n], "||"); p += 2; n++; continue; }
        if (strncmp(p, "==", 2) == 0) { strcpy(tokens[n], "=="); p += 2; n++; continue; }
        if (strncmp(p, "!=", 2) == 0) { strcpy(tokens[n], "!="); p += 2; n++; continue; }
        if (strncmp(p, "<=", 2) == 0) { strcpy(tokens[n], "<="); p += 2; n++; continue; }
        if (strncmp(p, ">=", 2) == 0) { strcpy(tokens[n], ">="); p += 2; n++; continue; }

        // Números (incluyendo negativos)
        if (isdigit((unsigned char)*p) || (*p == '-' && isdigit((unsigned char)*(p+1)))) {
            int j = 0;
            if (*p == '-') { tokens[n][j++] = *p; p++; }
            while (isdigit((unsigned char)*p) || *p == '.') {
                tokens[n][j++] = *p; p++;
            }
            tokens[n][j] = '\0'; n++; continue;
        }

        // Identificadores
        if (isalpha((unsigned char)*p) || *p == '_') {
            int j = 0;
            while (isalnum((unsigned char)*p) || *p == '_') {
                tokens[n][j++] = *p; p++;
            }
            tokens[n][j] = '\0'; n++; continue;
        }

        // Operadores de un carácter
        if (*p == '<' || *p == '>' || *p == '=' || *p == '!'
            || *p == '+' || *p == '-' || *p == '*' || *p == '/'
            || *p == '(' || *p == ')' || *p == ',') {
            tokens[n][0] = *p; tokens[n][1] = '\0'; p++; n++; continue;
        }

        p++; // Carácter desconocido
    }

    *num_tokens = n;
    return 0;
}

// Busca una variable simbólica por nombre
static int _buscar_variable(SEEngine* engine, const char* nombre) {
    for (int i = 0; i < engine->num_variables; i++) {
        if (strcmp(engine->variables[i].nombre, nombre) == 0) {
            return i;
        }
    }
    return -1;
}

// Determina si una restricción es contradictoria con la ruta actual
static int _restriccion_es_contradictoria(SEEngine* engine, const char* expresion, int tipo) {
    // Verificar contradicciones obvias: x > 5 y x < 3
    for (int p = 0; p < engine->num_paths; p++) {
        if (p != engine->active_path_idx) continue;
        SEPath* path = &engine->paths[p];

        for (int c = 0; c < path->num_constraints; c++) {
            SEConstraint* existente = &path->constraints[c];
            if (!existente->es_activa) continue;

            // Buscar si involucran la misma variable
            char nueva_var[SE_MAX_VAR_NAME] = "";
            char existente_var[SE_MAX_VAR_NAME] = "";

            char tokens[256][SE_MAX_VAR_NAME];
            int nt = 0;
            if (_se_tokenizar(expresion, tokens, &nt) == 0 && nt >= 1) {
                if (isalpha((unsigned char)tokens[0][0]) || tokens[0][0] == '_') {
                    snprintf(nueva_var, SE_MAX_VAR_NAME, "%s", tokens[0]);
                }
            }
            if (_se_tokenizar(existente->expresion, tokens, &nt) == 0 && nt >= 1) {
                if (isalpha((unsigned char)tokens[0][0]) || tokens[0][0] == '_') {
                    snprintf(existente_var, SE_MAX_VAR_NAME, "%s", tokens[0]);
                }
            }

            if (strlen(nueva_var) > 0 && strcmp(nueva_var, existente_var) == 0) {
                // Misma variable — extraer valores de AMBAS expresiones por separado
                double val_nuevo = 0, val_existente = 0;
                char tok_nuevo[256][SE_MAX_VAR_NAME], tok_exist[256][SE_MAX_VAR_NAME];
                int nt_nuevo = 0, nt_exist = 0;
                _se_tokenizar(expresion, tok_nuevo, &nt_nuevo);
                _se_tokenizar(existente->expresion, tok_exist, &nt_exist);
                if (nt_nuevo >= 3) {
                    int idx = (isdigit((unsigned char)tok_nuevo[0][0]) ||
                               (tok_nuevo[0][0] == '-' && isdigit((unsigned char)tok_nuevo[0][1]))) ? 0 : 2;
                    if (idx < nt_nuevo) val_nuevo = atof(tok_nuevo[idx]);
                }
                if (nt_exist >= 3) {
                    int idx = (isdigit((unsigned char)tok_exist[0][0]) ||
                               (tok_exist[0][0] == '-' && isdigit((unsigned char)tok_exist[0][1]))) ? 0 : 2;
                    if (idx < nt_exist) val_existente = atof(tok_exist[idx]);
                }
                if ((tipo == SE_CONSTRAINT_LT || tipo == SE_CONSTRAINT_LE) &&
                    (existente->tipo == SE_CONSTRAINT_GT || existente->tipo == SE_CONSTRAINT_GE)) {
                    if (val_nuevo <= val_existente) return 1;
                }
                if ((tipo == SE_CONSTRAINT_GT || tipo == SE_CONSTRAINT_GE) &&
                    (existente->tipo == SE_CONSTRAINT_LT || existente->tipo == SE_CONSTRAINT_LE)) {
                    if (val_existente <= val_nuevo) return 1;
                }
                if (tipo == SE_CONSTRAINT_EQ && existente->tipo == SE_CONSTRAINT_EQ) {
                    if (strcmp(expresion, existente->expresion) != 0) return 1;
                }
            }
        }
    }

    return 0;
}

// Verifica si un divisor puede ser cero bajo las restricciones actuales
static int _divisor_puede_ser_cero(SEEngine* engine) {
    for (int i = 0; i < engine->num_variables; i++) {
        double inf = engine->variables[i].cota_inf;
        double sup = engine->variables[i].cota_sup;

        if (engine->active_path_idx >= 0) {
            SEPath* path = &engine->paths[engine->active_path_idx];
            for (int c = 0; c < path->num_constraints; c++) {
                if (!path->constraints[c].es_activa) continue;
                if (strcmp(path->constraints[c].variable, engine->variables[i].nombre) == 0) {
                    double v = path->constraints[c].valor;
                    switch (path->constraints[c].tipo) {
                        case SE_CONSTRAINT_GT: case SE_CONSTRAINT_GE:
                            if (v > inf) { inf = v; }
                            break;
                        case SE_CONSTRAINT_LT: case SE_CONSTRAINT_LE:
                            if (v < sup) { sup = v; }
                            break;
                        case SE_CONSTRAINT_EQ: inf = v; sup = v; break;
                        default: break;
                    }
                }
            }
        }

        if (inf <= 0 && sup >= 0) return 1;
    }
    return 0;
}

// Determina el tipo de restricción desde una expresión de comparación
static int _determinar_tipo(const char* expresion) {
    if (!expresion) return -1;
    if (strstr(expresion, ">=")) return SE_CONSTRAINT_GE;
    if (strstr(expresion, "<=")) return SE_CONSTRAINT_LE;
    if (strstr(expresion, "==")) return SE_CONSTRAINT_EQ;
    if (strstr(expresion, "!=")) return SE_CONSTRAINT_NEQ;
    if (strstr(expresion, ">"))  return SE_CONSTRAINT_GT;
    if (strstr(expresion, "<"))  return SE_CONSTRAINT_LT;
    return -1;
}

// ============================================================
// API pública
// ============================================================

SEEngine* se_iniciar(const SEConfig* config, void* atp_engine) {
    SEEngine* engine = (SEEngine*)calloc(1, sizeof(SEEngine));
    if (!engine) return NULL;

    if (config) {
        engine->config = *config;
    } else {
        engine->config.explore_mode = SE_EXPLORE_ALL;
        engine->config.max_path_depth = 100;
        engine->config.detect_div_by_zero = 1;
        engine->config.detect_overflow = 1;
        engine->config.detect_bounds = 1;
        engine->config.detect_contract_violations = 1;
        engine->config.use_atp_engine = (atp_engine != NULL) ? 1 : 0;
        engine->config.timeout_ms = 5000;
    }

    engine->num_variables = 0;
    engine->num_paths = 0;
    engine->active_path_idx = -1;
    engine->estado = 0;
    engine->tiempo_total_ms = 0.0;
    engine->atp_engine = atp_engine;

    return engine;
}

int se_agregar_variable(SEEngine* engine, const char* nombre,
                         double cota_inf, double cota_sup,
                         int tipo_hint) {
    if (!engine || !nombre) return -1;
    if (engine->num_variables >= SE_MAX_VARS) return -1;
    if (_buscar_variable(engine, nombre) >= 0) return -1; // No duplicados

    SEVariable* v = &engine->variables[engine->num_variables];
    snprintf(v->nombre, SE_MAX_VAR_NAME, "%s", nombre);
    v->cota_inf = cota_inf;
    v->cota_sup = cota_sup;
    v->tiene_cota_inf = 1;
    v->tiene_cota_sup = 1;
    v->tipo_hint = tipo_hint;
    v->es_simbolica = 1;

    int idx = engine->num_variables;
    engine->num_variables++;

    // Crear ruta inicial si no existe
    if (engine->num_paths == 0) {
        SEPath* path = &engine->paths[0];
        memset(path, 0, sizeof(SEPath));
        path->estado = SE_PATH_ACTIVE;
        path->num_constraints = 0;
        path->profundidad = 0;
        engine->num_paths = 1;
        engine->active_path_idx = 0;
    }

    // Agregar restricción de cota inicial
    char buf[SE_MAX_EXPR_LEN];
    if (cota_inf > -1e10) {
        snprintf(buf, SE_MAX_EXPR_LEN, "%s >= %g", nombre, cota_inf);
        se_agregar_restriccion(engine, buf, SE_CONSTRAINT_GE);
    }
    if (cota_sup < 1e10) {
        snprintf(buf, SE_MAX_EXPR_LEN, "%s <= %g", nombre, cota_sup);
        se_agregar_restriccion(engine, buf, SE_CONSTRAINT_LE);
    }

    return idx;
}

int se_agregar_restriccion(SEEngine* engine, const char* expresion, int tipo) {
    if (!engine || !expresion) return -1;
    if (engine->active_path_idx < 0) return -1;

    SEPath* path = &engine->paths[engine->active_path_idx];
    if (path->num_constraints >= SE_MAX_CONSTRAINTS) return -1;

    // Verificar contradicción antes de agregar
    if (_restriccion_es_contradictoria(engine, expresion, tipo)) {
        path->estado = SE_PATH_INFEASIBLE;
        return -1;
    }

    SEConstraint* c = &path->constraints[path->num_constraints];
    snprintf(c->expresion, SE_MAX_EXPR_LEN, "%s", expresion);
    c->tipo = tipo;
    c->es_simbolica = 1;
    c->es_activa = 1;

    // Extraer variable y valor si es una comparación simple
    char tokens[256][SE_MAX_VAR_NAME];
    int nt = 0;
    if (_se_tokenizar(expresion, tokens, &nt) == 0 && nt >= 3) {
        if ((isalpha((unsigned char)tokens[0][0]) || tokens[0][0] == '_') &&
            (isdigit((unsigned char)tokens[2][0]) ||
             (tokens[2][0] == '-' && isdigit((unsigned char)tokens[2][1])))) {
            snprintf(c->variable, SE_MAX_VAR_NAME, "%s", tokens[0]);
            c->valor = atof(tokens[2]);

            // Actualizar cotas de la variable
            int vidx = _buscar_variable(engine, tokens[0]);
            if (vidx >= 0) {
                double v = atof(tokens[2]);
                switch (tipo) {
                    case SE_CONSTRAINT_GT:
                        if (v > engine->variables[vidx].cota_inf)
                            engine->variables[vidx].cota_inf = v;
                        break;
                    case SE_CONSTRAINT_GE:
                        if (v > engine->variables[vidx].cota_inf)
                            engine->variables[vidx].cota_inf = v;
                        break;
                    case SE_CONSTRAINT_LT:
                        if (v < engine->variables[vidx].cota_sup)
                            engine->variables[vidx].cota_sup = v;
                        break;
                    case SE_CONSTRAINT_LE:
                        if (v < engine->variables[vidx].cota_sup)
                            engine->variables[vidx].cota_sup = v;
                        break;
                    case SE_CONSTRAINT_EQ:
                        engine->variables[vidx].cota_inf = v;
                        engine->variables[vidx].cota_sup = v;
                        break;
                    default: break;
                }
            }
        }
    }

    int idx = path->num_constraints;
    path->num_constraints++;

    // Marcar ruta como factible si era activa
    if (path->estado == SE_PATH_ACTIVE) {
        path->estado = SE_PATH_FEASIBLE;
    }

    return idx;
}

int se_bifurcar(SEEngine* engine, const char* condicion) {
    if (!engine || !condicion) return -1;
    if (engine->active_path_idx < 0) return -1;
    if (engine->num_paths >= SE_MAX_PATHS) return -1;

    SEPath* path_actual = &engine->paths[engine->active_path_idx];
    if (path_actual->estado != SE_PATH_FEASIBLE && path_actual->estado != SE_PATH_ACTIVE) {
        return -1;
    }

    // Crear nueva ruta como copia de la actual + condición negada
    SEPath* nuevo = &engine->paths[engine->num_paths];
    memset(nuevo, 0, sizeof(SEPath));
    nuevo->estado = SE_PATH_ACTIVE;
    nuevo->profundidad = path_actual->profundidad + 1;
    nuevo->num_bifurcaciones = path_actual->num_bifurcaciones + 1;
    nuevo->coste_estimado = path_actual->coste_estimado;

    // Copiar restricciones existentes
    for (int i = 0; i < path_actual->num_constraints; i++) {
        nuevo->constraints[i] = path_actual->constraints[i];
        nuevo->num_constraints++;
    }

    // Agregar condición NEGADA a la nueva ruta
    char cond_negada[SE_MAX_EXPR_LEN];
    int tipo_negado;
    char tokens[256][SE_MAX_VAR_NAME];
    int nt = 0;
    if (_se_tokenizar(condicion, tokens, &nt) == 0 && nt >= 3) {
        // Negar el operador
        if (strcmp(tokens[1], "<") == 0) {
            snprintf(cond_negada, SE_MAX_EXPR_LEN, "%s > %s", tokens[0], tokens[2]);
            tipo_negado = SE_CONSTRAINT_GT;
        } else if (strcmp(tokens[1], ">") == 0) {
            snprintf(cond_negada, SE_MAX_EXPR_LEN, "%s < %s", tokens[0], tokens[2]);
            tipo_negado = SE_CONSTRAINT_LT;
        } else if (strcmp(tokens[1], "<=") == 0) {
            snprintf(cond_negada, SE_MAX_EXPR_LEN, "%s > %s", tokens[0], tokens[2]);
            tipo_negado = SE_CONSTRAINT_GT;
        } else if (strcmp(tokens[1], ">=") == 0) {
            snprintf(cond_negada, SE_MAX_EXPR_LEN, "%s < %s", tokens[0], tokens[2]);
            tipo_negado = SE_CONSTRAINT_LT;
        } else if (strcmp(tokens[1], "==") == 0) {
            snprintf(cond_negada, SE_MAX_EXPR_LEN, "%s != %s", tokens[0], tokens[2]);
            tipo_negado = SE_CONSTRAINT_NEQ;
        } else if (strcmp(tokens[1], "!=") == 0) {
            snprintf(cond_negada, SE_MAX_EXPR_LEN, "%s == %s", tokens[0], tokens[2]);
            tipo_negado = SE_CONSTRAINT_EQ;
        } else {
            snprintf(cond_negada, SE_MAX_EXPR_LEN, "!(%s)", condicion);
            tipo_negado = SE_CONSTRAINT_NEQ;
        }
    } else {
        snprintf(cond_negada, SE_MAX_EXPR_LEN, "!(%s)", condicion);
        tipo_negado = SE_CONSTRAINT_NEQ;
    }

    // Verificar contradicción antes de agregar la negación
    if (_restriccion_es_contradictoria(engine, cond_negada, tipo_negado)) {
        nuevo->estado = SE_PATH_INFEASIBLE;
    } else {
        // Agregar restricción negada a la nueva ruta
        if (nuevo->num_constraints < SE_MAX_CONSTRAINTS) {
            SEConstraint* nc = &nuevo->constraints[nuevo->num_constraints];
            snprintf(nc->expresion, SE_MAX_EXPR_LEN, "%s", cond_negada);
            nc->tipo = tipo_negado;
            nc->es_simbolica = 1;
            nc->es_activa = 1;
            nuevo->num_constraints++;
        }
    }

    // Agregar condición ORIGINAL a la ruta actual
    int cond_tipo = _determinar_tipo(condicion);
    if (_restriccion_es_contradictoria(engine, condicion, cond_tipo)) {
        path_actual->estado = SE_PATH_INFEASIBLE;
    } else {
        if (path_actual->num_constraints < SE_MAX_CONSTRAINTS) {
            SEConstraint* oc = &path_actual->constraints[path_actual->num_constraints];
            snprintf(oc->expresion, SE_MAX_EXPR_LEN, "%s", condicion);
            oc->tipo = cond_tipo;
            oc->es_simbolica = 1;
            oc->es_activa = 1;
            path_actual->num_constraints++;
        }
    }

    engine->num_paths++;
    return 0;
}

int se_verificar_alcanzabilidad(SEEngine* engine) {
    if (!engine) return -1;
    if (engine->active_path_idx < 0) return 0;

    SEPath* path = &engine->paths[engine->active_path_idx];
    return (path->estado != SE_PATH_INFEASIBLE) ? 1 : 0;
}

int se_detectar_division_por_cero(SEEngine* engine, const char* divisor_expr) {
    if (!engine || !divisor_expr) return SE_VIOLATION_NONE;
    if (!engine->config.detect_div_by_zero) return SE_VIOLATION_NONE;

    // Si el divisor es un literal numérico, verificar directamente
    {
        char tok_div[256][SE_MAX_VAR_NAME];
        int nt_div = 0;
        if (_se_tokenizar(divisor_expr, tok_div, &nt_div) == 0 && nt_div == 1) {
            int es_num = (isdigit((unsigned char)tok_div[0][0]) ||
                          (tok_div[0][0] == '-' && isdigit((unsigned char)tok_div[0][1])));
            if (es_num && atof(tok_div[0]) == 0.0) {
                return SE_VIOLATION_DIV_BY_ZERO;
            }
        }
    }

    // Verificar si alguna variable simbólica puede ser cero
    if (_divisor_puede_ser_cero(engine)) {
        return SE_VIOLATION_DIV_BY_ZERO;
    }

    return SE_VIOLATION_NONE;
}

int se_detectar_desbordamiento(SEEngine* engine, const char* op_expr,
                                double limite_inf, double limite_sup) {
    if (!engine || !op_expr) return SE_VIOLATION_NONE;
    if (!engine->config.detect_overflow) return SE_VIOLATION_NONE;

    // Simplificación: verificar si las cotas de variables pueden exceder los límites
    for (int i = 0; i < engine->num_variables; i++) {
        char tokens[256][SE_MAX_VAR_NAME];
        int nt = 0;
        if (_se_tokenizar(op_expr, tokens, &nt) == 0) {
            for (int t = 0; t < nt; t++) {
                if (strcmp(tokens[t], engine->variables[i].nombre) == 0) {
                    // Esta variable aparece en la expresión
                    double inf = engine->variables[i].cota_inf;
                    double sup = engine->variables[i].cota_sup;

                    // Si los límites pueden exceder los valores seguros
                    if (inf < limite_inf || sup > limite_sup) {
                        return SE_VIOLATION_OVERFLOW;
                    }
                }
            }
        }
    }

    return SE_VIOLATION_NONE;
}

int se_detectar_fuera_limites(SEEngine* engine, const char* idx_expr,
                               int tamano_array) {
    if (!engine || !idx_expr) return SE_VIOLATION_NONE;
    if (!engine->config.detect_bounds) return SE_VIOLATION_NONE;

    // Buscar variables simbólicas en el índice
    for (int i = 0; i < engine->num_variables; i++) {
        if (strstr(idx_expr, engine->variables[i].nombre)) {
            double inf = engine->variables[i].cota_inf;
            double sup = engine->variables[i].cota_sup;

            // Si alguna cota está fuera de los límites del array
            if (inf < 0 || sup >= tamano_array) {
                return SE_VIOLATION_BOUNDS;
            }
            // Si el intervalo está fuera: sup < 0 o inf >= tamano
            if (sup < 0 || inf >= tamano_array) {
                return SE_VIOLATION_BOUNDS;
            }
        }
    }

    return SE_VIOLATION_NONE;
}

int se_detectar_violacion_contrato(SEEngine* engine,
                                    const char* precondiciones[], int num_pre,
                                    const char* postcondiciones[], int num_post) {
    if (!engine) return SE_VIOLATION_NONE;
    if (!engine->config.detect_contract_violations) return SE_VIOLATION_NONE;
    if (engine->active_path_idx < 0) return SE_VIOLATION_NONE;

    SEPath* path = &engine->paths[engine->active_path_idx];
    if (path->estado == SE_PATH_INFEASIBLE) return SE_VIOLATION_NONE;

    // Verificar contradicciones entre precondiciones y restricciones de ruta
    for (int p = 0; p < num_pre; p++) {
        if (!precondiciones[p]) continue;
        int pre_tipo = _determinar_tipo(precondiciones[p]);
        if (_restriccion_es_contradictoria(engine, precondiciones[p], pre_tipo)) {
            // Precondición contradictoria con ruta → violación de contrato
            if (engine->config.detect_contract_violations) {
                path->violation_type = SE_VIOLATION_CONTRACT;
                snprintf(path->violation_msg, SE_MAX_ERROR_LEN,
                         "Precondicion '%s' contradictoria con restricciones de ruta",
                         precondiciones[p]);
                return SE_VIOLATION_CONTRACT;
            }
        }
    }

    // Verificar postcondiciones contra las restricciones de ruta
    for (int q = 0; q < num_post; q++) {
        if (!postcondiciones[q]) continue;
        int post_tipo = _determinar_tipo(postcondiciones[q]);
        if (_restriccion_es_contradictoria(engine, postcondiciones[q], post_tipo)) {
            path->violation_type = SE_VIOLATION_CONTRACT;
            snprintf(path->violation_msg, SE_MAX_ERROR_LEN,
                     "Postcondicion '%s' contradictoria con restricciones de ruta",
                     postcondiciones[q]);
            return SE_VIOLATION_CONTRACT;
        }
    }

    return SE_VIOLATION_NONE;
}

int se_explorar(SEEngine* engine) {
    if (!engine) return -1;

    clock_t inicio = clock();
    engine->estado = 1;  // Explorando

    // Si no hay rutas, crear una inicial
    if (engine->num_paths == 0) {
        SEPath* path = &engine->paths[0];
        memset(path, 0, sizeof(SEPath));
        path->estado = SE_PATH_FEASIBLE;
        engine->num_paths = 1;
        engine->active_path_idx = 0;
    }

    // Explorar todas las rutas activas/factibles
    int exploradas = 0;
    for (int i = 0; i < engine->num_paths; i++) {
        if (engine->paths[i].estado == SE_PATH_ACTIVE ||
            engine->paths[i].estado == SE_PATH_FEASIBLE) {
            engine->active_path_idx = i;
            exploradas++;

            // Marcar como explorada
            if (engine->paths[i].estado == SE_PATH_ACTIVE) {
                engine->paths[i].estado = SE_PATH_FEASIBLE;
            }
            engine->paths[i].estado = SE_PATH_EXPLORED;
        }

        // Verificar timeout
        clock_t ahora = clock();
        double tiempo_ms = ((double)(ahora - inicio) / CLOCKS_PER_SEC) * 1000.0;
        if (tiempo_ms > engine->config.timeout_ms) break;
    }

    engine->tiempo_total_ms = ((double)(clock() - inicio) / CLOCKS_PER_SEC) * 1000.0;
    engine->estado = 2;  // Completado

    return exploradas;
}

int se_activar_ruta(SEEngine* engine, int idx) {
    if (!engine) return -1;
    if (idx < 0 || idx >= engine->num_paths) return -1;

    engine->active_path_idx = idx;
    return 0;
}

SEEstadisticas se_obtener_estadisticas(SEEngine* engine) {
    SEEstadisticas stats = {0};
    if (!engine) return stats;

    stats.num_variables = engine->num_variables;
    stats.num_rutas_exploradas = engine->num_paths;
    stats.tiempo_total_ms = engine->tiempo_total_ms;

    for (int i = 0; i < engine->num_paths; i++) {
        stats.num_restricciones += engine->paths[i].num_constraints;
        if (engine->paths[i].estado == SE_PATH_FEASIBLE ||
            engine->paths[i].estado == SE_PATH_EXPLORED) {
            stats.num_rutas_factibles++;
        }
        if (engine->paths[i].estado == SE_PATH_INFEASIBLE) {
            stats.num_rutas_infactibles++;
        }
        if (engine->paths[i].violation_type != SE_VIOLATION_NONE) {
            stats.num_violaciones_detectadas++;
        }
    }

    return stats;
}

int se_guardar(const SEEngine* engine, const char* ruta) {
    if (!engine || !ruta) return -1;

    FILE* f = fopen(ruta, "wb");
    if (!f) return -1;

    uint32_t magic = SE_MAGIC_HEADER;
    uint32_t version = SE_VERSION;
    fwrite(&magic, sizeof(magic), 1, f);
    fwrite(&version, sizeof(version), 1, f);

    // Guardar configuración
    fwrite(&engine->config, sizeof(SEConfig), 1, f);

    // Guardar variables
    uint32_t nv = (uint32_t)engine->num_variables;
    fwrite(&nv, sizeof(nv), 1, f);
    for (uint32_t i = 0; i < nv; i++) {
        fwrite(&engine->variables[i], sizeof(SEVariable), 1, f);
    }

    // Guardar rutas
    uint32_t np = (uint32_t)engine->num_paths;
    fwrite(&np, sizeof(np), 1, f);
    for (uint32_t i = 0; i < np; i++) {
        fwrite(&engine->paths[i], sizeof(SEPath), 1, f);
    }

    fclose(f);
    return 0;
}

int se_cargar(SEEngine* engine, const char* ruta) {
    if (!engine || !ruta) return -1;

    FILE* f = fopen(ruta, "rb");
    if (!f) return -1;

    uint32_t magic, version;
    if (fread(&magic, sizeof(magic), 1, f) != 1 || magic != SE_MAGIC_HEADER) {
        fclose(f); return -1;
    }
    if (fread(&version, sizeof(version), 1, f) != 1 || version > SE_VERSION) {
        fclose(f); return -1;
    }

    // Cargar configuración
    if (fread(&engine->config, sizeof(SEConfig), 1, f) != 1) {
        fclose(f); return -1;
    }

    // Cargar variables
    uint32_t nv;
    if (fread(&nv, sizeof(nv), 1, f) != 1 || nv > SE_MAX_VARS) {
        fclose(f); return -1;
    }
    for (uint32_t i = 0; i < nv; i++) {
        if (fread(&engine->variables[i], sizeof(SEVariable), 1, f) != 1) {
            fclose(f); return -1;
        }
    }
    engine->num_variables = (int)nv;

    // Cargar rutas
    uint32_t np;
    if (fread(&np, sizeof(np), 1, f) != 1 || np > SE_MAX_PATHS) {
        fclose(f); return -1;
    }
    for (uint32_t i = 0; i < np; i++) {
        if (fread(&engine->paths[i], sizeof(SEPath), 1, f) != 1) {
            fclose(f); return -1;
        }
    }
    engine->num_paths = (int)np;

    fclose(f);
    return 0;
}

void se_limpiar(SEEngine* engine) {
    if (!engine) return;
    engine->num_variables = 0;
    engine->num_paths = 0;
    engine->active_path_idx = -1;
    engine->error_message[0] = '\0';
    engine->estado = 0;
    engine->tiempo_total_ms = 0.0;
}

void se_cerrar(SEEngine* engine) {
    if (!engine) return;
    free(engine);
}

// ============================================================
// Wrappers _syn_se_* para enlace con std.symbolic_exec
// ============================================================

void* _syn_se_iniciar(int explore_mode, int max_depth) {
    SEConfig cfg;
    memset(&cfg, 0, sizeof(SEConfig));
    cfg.explore_mode = explore_mode;
    cfg.max_path_depth = max_depth;
    cfg.detect_div_by_zero = 1;
    cfg.detect_overflow = 1;
    cfg.detect_bounds = 1;
    cfg.detect_contract_violations = 1;
    cfg.use_atp_engine = 0;
    cfg.timeout_ms = 5000;
    return se_iniciar(&cfg, NULL);
}

void _syn_se_cerrar(void* engine) {
    se_cerrar((SEEngine*)engine);
}

int _syn_se_agregar_variable(void* engine, const char* nombre,
                              double inf, double sup, int tipo) {
    return se_agregar_variable((SEEngine*)engine, nombre, inf, sup, tipo);
}

int _syn_se_agregar_restriccion(void* engine, const char* expr, int tipo) {
    return se_agregar_restriccion((SEEngine*)engine, expr, tipo);
}

int _syn_se_bifurcar(void* engine, const char* cond) {
    return se_bifurcar((SEEngine*)engine, cond);
}

int _syn_se_verificar_alcanzabilidad(void* engine) {
    return se_verificar_alcanzabilidad((SEEngine*)engine);
}

int _syn_se_detectar_div_por_cero(void* engine, const char* divisor) {
    return se_detectar_division_por_cero((SEEngine*)engine, divisor);
}

int _syn_se_detectar_desbordamiento(void* engine, const char* expr,
                                     double lim_inf, double lim_sup) {
    return se_detectar_desbordamiento((SEEngine*)engine, expr, lim_inf, lim_sup);
}

int _syn_se_detectar_fuera_limites(void* engine, const char* idx, int tam) {
    return se_detectar_fuera_limites((SEEngine*)engine, idx, tam);
}

int _syn_se_explorar(void* engine) {
    return se_explorar((SEEngine*)engine);
}

int _syn_se_activar_ruta(void* engine, int idx) {
    return se_activar_ruta((SEEngine*)engine, idx);
}

void _syn_se_limpiar(void* engine) {
    se_limpiar((SEEngine*)engine);
}
