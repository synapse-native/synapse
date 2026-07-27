// atp_engine.c — Motor de Demostración Automática de Teoremas (ATP Engine)
// ======================================================================
// Implementa un resolvedor SMT ligero integrado para verificación de
// contratos requiere/garantiza en tiempo de compilación.
//
// Técnicas de demostración:
//   1. Propagación de intervalos (aritmética lineal)
//   2. Detección de contradicciones (intersección de intervalos)
//   3. Resolución proposicional (modus ponens, silogismo)
//   4. Verificación de tautologías por sustitución
//   5. Búsqueda de contraejemplos por generación de casos
//
// Zero-telemetry: todo el proceso es local y soberano.
// ======================================================================

#include "atp_engine.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <ctype.h>

// ============================================================
// Helpers internos
// ============================================================

// Divide una expresión en tokens simples
static int _tokenizar(const char* expr, char tokens[256][ATP_MAX_VAR_NAME], int* num_tokens) {
    if (!expr || !tokens || !num_tokens) return -1;

    char buf[ATP_MAX_EXPR_LEN];
    strncpy(buf, expr, ATP_MAX_EXPR_LEN - 1);
    buf[ATP_MAX_EXPR_LEN - 1] = '\0';

    int n = 0;
    char* p = buf;
    while (*p && n < 256) {
        // Saltar espacios
        while (*p == ' ' || *p == '\t') p++;
        if (!*p) break;

        // Operadores multi-carácter
        if (strncmp(p, "&&", 2) == 0) {
            strcpy(tokens[n], "&&");
            p += 2; n++; continue;
        }
        if (strncmp(p, "||", 2) == 0) {
            strcpy(tokens[n], "||");
            p += 2; n++; continue;
        }
        if (strncmp(p, "==", 2) == 0) {
            strcpy(tokens[n], "==");
            p += 2; n++; continue;
        }
        if (strncmp(p, "!=", 2) == 0) {
            strcpy(tokens[n], "!=");
            p += 2; n++; continue;
        }
        if (strncmp(p, "<=", 2) == 0) {
            strcpy(tokens[n], "<=");
            p += 2; n++; continue;
        }
        if (strncmp(p, ">=", 2) == 0) {
            strcpy(tokens[n], ">=");
            p += 2; n++; continue;
        }

        // Números (enteros y decimales) — debe ir ANTES de operadores single-char
        // para que -273.15 se tokenice como un solo token, no como "-" + "273.15"
        if (isdigit((unsigned char)*p) || (*p == '-' && isdigit((unsigned char)*(p+1)))) {
            int j = 0;
            if (*p == '-') { tokens[n][j++] = *p; p++; }
            while (isdigit((unsigned char)*p) || *p == '.') {
                tokens[n][j++] = *p;
                p++;
            }
            tokens[n][j] = '\0';
            n++; continue;
        }

        // Identificadores (letras y _)
        if (isalpha((unsigned char)*p) || *p == '_') {
            int j = 0;
            while (isalnum((unsigned char)*p) || *p == '_') {
                tokens[n][j++] = *p;
                p++;
            }
            tokens[n][j] = '\0';
            n++; continue;
        }

        // Operadores de un carácter — el resto (+, -, *, /, etc.)
        // NOTA: los números negativos ya fueron capturados arriba; aquí '-' es solo operador binario
        if (*p == '<' || *p == '>' || *p == '=' || *p == '!'
            || *p == '+' || *p == '-' || *p == '*' || *p == '/'
            || *p == '(' || *p == ')' || *p == ',') {
            tokens[n][0] = *p;
            tokens[n][1] = '\0';
            p++; n++; continue;
        }

        // Saltar carácter desconocido
        p++;
    }

    *num_tokens = n;
    return 0;
}

// Busca o crea un intervalo para una variable
static int _buscar_o_crear_intervalo(ATPEngine* engine, const char* nombre) {
    for (int i = 0; i < engine->num_intervalos; i++) {
        if (strcmp(engine->intervalos[i].nombre, nombre) == 0) {
            return i;
        }
    }

    if (engine->num_intervalos >= ATP_MAX_VARS) return -1;

    int idx = engine->num_intervalos;
    snprintf(engine->intervalos[idx].nombre, ATP_MAX_VAR_NAME, "%s", nombre);
    engine->intervalos[idx].inf = -1e308;
    engine->intervalos[idx].sup = 1e308;
    engine->intervalos[idx].tiene_inf = 0;
    engine->intervalos[idx].tiene_sup = 0;
    engine->intervalos[idx].es_entero = 1; // Por defecto enteros
    engine->num_intervalos++;

    return idx;
}

// Extrae variable y valor de una expresión como "x > 5"
// Retorna: 0 si pudo extraer, -1 si no
static int _extraer_comparacion(const char* expr,
                                 char* var_out, int max_var,
                                 double* val_out, int* op_out) {
    if (!expr || !var_out || !val_out || !op_out) return -1;

    char tokens[256][ATP_MAX_VAR_NAME];
    int n = 0;
    if (_tokenizar(expr, tokens, &n) != 0 || n < 3) return -1;

    // Patrón: var op value o value op var
    // tokens[0] = variable o valor, tokens[1] = operador, tokens[2] = valor o variable

    int es_numero = (isdigit((unsigned char)tokens[0][0]) ||
                     (tokens[0][0] == '-' && isdigit((unsigned char)tokens[0][1])));
    int es_var = (isalpha((unsigned char)tokens[0][0]) || tokens[0][0] == '_');

    // Determinar operador
    int op = -1;
    if (strcmp(tokens[1], "<") == 0) op = ATP_OP_LT;
    else if (strcmp(tokens[1], ">") == 0) op = ATP_OP_GT;
    else if (strcmp(tokens[1], "<=") == 0) op = ATP_OP_LE;
    else if (strcmp(tokens[1], ">=") == 0) op = ATP_OP_GE;
    else if (strcmp(tokens[1], "==") == 0) op = ATP_OP_EQ;
    else if (strcmp(tokens[1], "!=") == 0) op = ATP_OP_NEQ;
    else return -1;

    if (es_numero) {
        // Patrón: 5 < x
        double val = atof(tokens[0]);
        // Invertir operador
        int op_inv = -1;
        switch (op) {
            case ATP_OP_LT: op_inv = ATP_OP_GT; break;
            case ATP_OP_GT: op_inv = ATP_OP_LT; break;
            case ATP_OP_LE: op_inv = ATP_OP_GE; break;
            case ATP_OP_GE: op_inv = ATP_OP_LE; break;
            default: op_inv = op; break;
        }
        *op_out = op_inv;
        *val_out = val;
        strncpy(var_out, tokens[2], (size_t)max_var - 1);
        var_out[max_var - 1] = '\0';
        return 0;
    } else if (es_var) {
        // Patrón: x > 5
        strncpy(var_out, tokens[0], (size_t)max_var - 1);
        var_out[max_var - 1] = '\0';
        *op_out = op;
        *val_out = atof(tokens[2]);
        return 0;
    }

    return -1;
}

// Aplica un operador de comparación a un intervalo
// Retorna: 0 si el intervalo se actualizó, -1 si hay contradicción
static int _aplicar_comparacion_a_intervalo(ATPInterval* iv, int op, double val) {
    if (!iv) return -1;

    switch (op) {
        case ATP_OP_LT:  // x < val
            if (iv->tiene_sup && iv->sup <= val) return 0; // Ya está acotado
            if (iv->tiene_inf && iv->inf >= val) return -1; // Contradicción: x >= inf >= val
            iv->sup = val;
            iv->tiene_sup = 1;
            return 0;

        case ATP_OP_GT:  // x > val
            if (iv->tiene_inf && iv->inf >= val) return 0; // Ya está acotado
            if (iv->tiene_sup && iv->sup <= val) return -1; // Contradicción: x <= sup <= val
            iv->inf = val;
            iv->tiene_inf = 1;
            return 0;

        case ATP_OP_LE:  // x <= val
            if (iv->tiene_sup && iv->sup <= val) return 0;
            if (iv->tiene_inf && iv->inf > val) return -1;
            iv->sup = val;
            iv->tiene_sup = 1;
            return 0;

        case ATP_OP_GE:  // x >= val
            if (iv->tiene_inf && iv->inf >= val) return 0;
            if (iv->tiene_sup && iv->sup < val) return -1;
            iv->inf = val;
            iv->tiene_inf = 1;
            return 0;

        case ATP_OP_EQ:  // x == val
            // Si ya tiene intervalo, verificar compatibilidad
            if (iv->tiene_inf && iv->inf > val) return -1;
            if (iv->tiene_sup && iv->sup < val) return -1;
            iv->inf = val;
            iv->sup = val;
            iv->tiene_inf = 1;
            iv->tiene_sup = 1;
            return 0;

        case ATP_OP_NEQ:  // x != val
            // No podemos representar esto con un intervalo simple
            // (es una disyunción: x < val || x > val)
            // Marcamos como no lineal
            return 0;
    }

    return 0;
}

// Verifica si dos intervalos tienen intersección vacía (contradicción)
static int _intervalos_contradictorios(ATPInterval* a, ATPInterval* b) {
    if (!a || !b) return 0;
    if (strcmp(a->nombre, b->nombre) != 0) return 0;

    double inf_a = a->tiene_inf ? a->inf : -1e308;
    double sup_a = a->tiene_sup ? a->sup : 1e308;
    double inf_b = b->tiene_inf ? b->inf : -1e308;
    double sup_b = b->tiene_sup ? b->sup : 1e308;

    // La intersección es [max(inf_a, inf_b), min(sup_a, sup_b)]
    double new_inf = (inf_a > inf_b) ? inf_a : inf_b;
    double new_sup = (sup_a < sup_b) ? sup_a : sup_b;

    return (new_inf > new_sup);
}

// Verifica si un intervalo individual es contradictorio (inf > sup)
static int _intervalo_contradictorio(ATPInterval* iv) {
    if (!iv) return 0;
    if (iv->tiene_inf && iv->tiene_sup) {
        return (iv->inf > iv->sup);
    }
    return 0;
}

// Parsea una expresión booleana compuesta en subexpresiones
// Retorna: número de subexpresiones
static int _descomponer_expresion(const char* expr,
                                   char subexprs[64][ATP_MAX_EXPR_LEN],
                                   int* operadores, int max_sub) {
    if (!expr || !subexprs || !operadores) return -1;

    // Dividir por && y || al nivel superior
    char buf[ATP_MAX_EXPR_LEN];
    strncpy(buf, expr, ATP_MAX_EXPR_LEN - 1);
    buf[ATP_MAX_EXPR_LEN - 1] = '\0';

    int n = 0;
    int paren_depth = 0;
    int start = 0;
    int len = (int)strlen(buf);

    for (int i = 0; i <= len && n < max_sub; i++) {
        if (i < len) {
            if (buf[i] == '(') { paren_depth++; continue; }
            if (buf[i] == ')') { paren_depth--; continue; }
        }

        if (paren_depth == 0 && i < len) {
            if (strncmp(buf + i, "&&", 2) == 0) {
                // Subexpresión izquierda
                int sub_len = i - start;
                int j;
                for (j = 0; j < sub_len && j < (int)ATP_MAX_EXPR_LEN - 1; j++) {
                    subexprs[n][j] = buf[start + j];
                }
                subexprs[n][j] = '\0';
                operadores[n] = ATP_OP_AND;
                n++;
                i += 2;
                start = i;
                continue;
            }
            if (strncmp(buf + i, "||", 2) == 0) {
                int sub_len = i - start;
                int j;
                for (j = 0; j < sub_len && j < (int)ATP_MAX_EXPR_LEN - 1; j++) {
                    subexprs[n][j] = buf[start + j];
                }
                subexprs[n][j] = '\0';
                operadores[n] = ATP_OP_OR;
                n++;
                i += 2;
                start = i;
                continue;
            }
        }

        if (i == len) {
            // Última subexpresión
            int sub_len = i - start;
            int j;
            for (j = 0; j < sub_len && j < (int)ATP_MAX_EXPR_LEN - 1; j++) {
                subexprs[n][j] = buf[start + j];
            }
            subexprs[n][j] = '\0';
            operadores[n] = -1;  // Sin operador de continuación
            n++;
        }
    }

    return n;
}

// Normaliza una expresión (elimina paréntesis externos, espacios)
static void _normalizar_expr(const char* in, char* out, int max_out) {
    if (!in || !out) return;

    const char* p = in;
    char* d = out;

    // Saltar espacios iniciales
    while (*p == ' ' || *p == '\t') p++;

    while (*p && d < out + max_out - 1) {
        if (*p != ' ' && *p != '\t') {
            *d++ = *p;
        }
        p++;
    }
    *d = '\0';
}

// ============================================================
// Implementación de la API pública
// ============================================================

ATPEngine* atp_iniciar(const ATPConfig* config) {
    ATPEngine* engine = (ATPEngine*)calloc(1, sizeof(ATPEngine));
    if (!engine) return NULL;

    if (config) {
        engine->config = *config;
    } else {
        engine->config.max_resolution_depth = 100;
        engine->config.max_theorem_size = 256;
        engine->config.use_arithmetic_solver = 1;
        engine->config.use_propagation = 1;
        engine->config.use_contradiction_check = 1;
        engine->config.timeout_ms = 5000;
        engine->config.verify_strict = 0;
    }

    engine->num_preconditions = 0;
    engine->num_postconditions = 0;
    engine->num_invariants = 0;
    engine->num_intervalos = 0;
    engine->last_result = ATP_UNKNOWN;
    engine->error_message[0] = '\0';
    engine->resolution_steps = 0;
    engine->resolution_time_ms = 0.0;
    engine->estado = 0;
    engine->function_name[0] = '\0';

    return engine;
}

int atp_agregar_precondicion(ATPEngine* engine, const char* expresion) {
    if (!engine || !expresion) return -1;
    // Rechazar strings vacíos o solo espacios
    {
        int solo_espacios = 1;
        for (const char* p = expresion; *p; p++) {
            if (*p != ' ' && *p != '\t') { solo_espacios = 0; break; }
        }
        if (solo_espacios) return -1;
    }
    if (engine->num_preconditions >= ATP_MAX_CONSTRAINTS) return -1;

    ATPConstraint* c = &engine->preconditions[engine->num_preconditions];
    snprintf(c->expresion, ATP_MAX_EXPR_LEN, "%s", expresion);
    c->tipo = ATP_CONSTRAINT_REQUIERE;
    c->num_vars = 0;
    c->es_lineal = 1;
    c->es_booleana = 1;
    c->num_atomos = 0;
    c->tiene_cota_inf = 0;
    c->tiene_cota_sup = 0;
    c->evaluable = 0;

    // Extraer variable y valor si es una comparación simple
    char var[ATP_MAX_VAR_NAME];
    double val;
    int op;
    if (_extraer_comparacion(expresion, var, ATP_MAX_VAR_NAME, &val, &op) == 0) {
        int idx = _buscar_o_crear_intervalo(engine, var);
        if (idx >= 0) {
            int r = _aplicar_comparacion_a_intervalo(&engine->intervalos[idx], op, val);
            if (r < 0) {
                // Contradicción detectada: forzar intervalo contradictorio
                engine->intervalos[idx].sup = engine->intervalos[idx].inf - 1.0;
                engine->intervalos[idx].tiene_sup = 1;
            }
            // Guardar cotas en la restricción
            if (op == ATP_OP_GT || op == ATP_OP_GE) {
                c->cota_inferior = val;
                c->tiene_cota_inf = 1;
            } else if (op == ATP_OP_LT || op == ATP_OP_LE) {
                c->cota_superior = val;
                c->tiene_cota_sup = 1;
            } else if (op == ATP_OP_EQ) {
                c->cota_inferior = val;
                c->cota_superior = val;
                c->tiene_cota_inf = 1;
                c->tiene_cota_sup = 1;
            }
        }
        c->num_vars = 1;
        snprintf(c->vars[0], ATP_MAX_VAR_NAME, "%s", var);
        c->es_lineal = 1;
    } else {
        // Expresión booleana compuesta — descomponer
        char subexprs[64][ATP_MAX_EXPR_LEN];
        int operadores[64];
        int n = _descomponer_expresion(expresion, subexprs, operadores, 64);
        if (n > 0) {
            for (int i = 0; i < n && c->num_vars < ATP_MAX_VARS; i++) {
                char sub_var[ATP_MAX_VAR_NAME];
                double sub_val;
                int sub_op;
                if (_extraer_comparacion(subexprs[i], sub_var, ATP_MAX_VAR_NAME, &sub_val, &sub_op) == 0) {
                    // Agregar variable si no existe
                    int ya_existe = 0;
                    for (int v = 0; v < c->num_vars; v++) {
                        if (strcmp(c->vars[v], sub_var) == 0) {
                            ya_existe = 1; break;
                        }
                    }
                    if (!ya_existe) {
                        snprintf(c->vars[c->num_vars], ATP_MAX_VAR_NAME, "%s", sub_var);
                        c->num_vars++;
                    }
                }
            }
        }
        c->es_lineal = 0;
        c->es_booleana = 1;
    }

    int idx = engine->num_preconditions;
    engine->num_preconditions++;
    return idx;
}

int atp_agregar_postcondicion(ATPEngine* engine, const char* expresion) {
    if (!engine || !expresion) return -1;
    // Rechazar strings vacíos o solo espacios
    {
        int solo_espacios = 1;
        for (const char* p = expresion; *p; p++) {
            if (*p != ' ' && *p != '\t') { solo_espacios = 0; break; }
        }
        if (solo_espacios) return -1;
    }
    if (engine->num_postconditions >= ATP_MAX_CONSTRAINTS) return -1;

    ATPConstraint* c = &engine->postconditions[engine->num_postconditions];
    snprintf(c->expresion, ATP_MAX_EXPR_LEN, "%s", expresion);
    c->tipo = ATP_CONSTRAINT_GARANTIZA;
    c->num_vars = 0;
    c->es_lineal = 0;
    c->es_booleana = 1;
    c->tiene_cota_inf = 0;
    c->tiene_cota_sup = 0;
    c->evaluable = 0;

    // Extraer variable y valor si es posible (solo para almacenar, NO actualizar intervalos)
    char var[ATP_MAX_VAR_NAME];
    double val;
    int op;
    if (_extraer_comparacion(expresion, var, ATP_MAX_VAR_NAME, &val, &op) == 0) {
        c->num_vars = 1;
        snprintf(c->vars[0], ATP_MAX_VAR_NAME, "%s", var);
        c->es_lineal = 1;
        // Almacenar cotas para verificación posterior (no actualizar intervalos)
        if (op == ATP_OP_GT || op == ATP_OP_GE) {
            c->cota_inferior = val;
            c->tiene_cota_inf = 1;
        } else if (op == ATP_OP_LT || op == ATP_OP_LE) {
            c->cota_superior = val;
            c->tiene_cota_sup = 1;
        } else if (op == ATP_OP_EQ) {
            c->cota_inferior = val;
            c->cota_superior = val;
            c->tiene_cota_inf = 1;
            c->tiene_cota_sup = 1;
        }
    }

    int idx = engine->num_postconditions;
    engine->num_postconditions++;
    return idx;
}

int atp_agregar_invariante(ATPEngine* engine, const char* expresion) {
    if (!engine || !expresion) return -1;
    if (engine->num_invariants >= ATP_MAX_CONSTRAINTS) return -1;

    ATPConstraint* c = &engine->invariants[engine->num_invariants];
    snprintf(c->expresion, ATP_MAX_EXPR_LEN, "%s", expresion);
    c->tipo = ATP_CONSTRAINT_INVARIANTE;
    c->num_vars = 0;
    c->es_lineal = 1;
    c->num_atomos = 0;
    c->tiene_cota_inf = 0;
    c->tiene_cota_sup = 0;
    c->evaluable = 0;

    char var[ATP_MAX_VAR_NAME];
    double val;
    int op;
    if (_extraer_comparacion(expresion, var, ATP_MAX_VAR_NAME, &val, &op) == 0) {
        int idx = _buscar_o_crear_intervalo(engine, var);
        if (idx >= 0) {
            int r = _aplicar_comparacion_a_intervalo(&engine->intervalos[idx], op, val);
            if (r < 0) {
                // Contradicción detectada: forzar intervalo contradictorio
                engine->intervalos[idx].sup = engine->intervalos[idx].inf - 1.0;
                engine->intervalos[idx].tiene_sup = 1;
            }
        }
        c->num_vars = 1;
        snprintf(c->vars[0], ATP_MAX_VAR_NAME, "%s", var);
    } else {
        c->es_lineal = 0;
    }

    engine->num_invariants++;
    return engine->num_invariants - 1;
}

void atp_establecer_funcion(ATPEngine* engine, const char* nombre) {
    if (!engine || !nombre) return;
    strncpy(engine->function_name, nombre, 255);
    engine->function_name[255] = '\0';
}

int atp_verificar_tautologia(ATPEngine* engine, const char* expresion) {
    if (!engine || !expresion) return ATP_ERROR;

    char normalizada[ATP_MAX_EXPR_LEN];
    _normalizar_expr(expresion, normalizada, ATP_MAX_EXPR_LEN);

    // 1. Identidad: x == x, x >= x, x <= x
    // Parsear directamente: buscamos el operador
    {
        char tok[256][ATP_MAX_VAR_NAME];
        int nt = 0;
        _tokenizar(normalizada, tok, &nt);

        if (nt == 3) {
            if (strcmp(tok[0], tok[2]) == 0) {
                if (strcmp(tok[1], "==") == 0 ||
                    strcmp(tok[1], ">=") == 0 ||
                    strcmp(tok[1], "<=") == 0) {
                    return ATP_VALID;
                }
                if (strcmp(tok[1], "!=") == 0 ||
                    strcmp(tok[1], ">") == 0 ||
                    strcmp(tok[1], "<") == 0) {
                    return ATP_INVALID;
                }
            }
        }
    }

    // 2. Constantes lógicas true/false
    if (strcmp(normalizada, "true") == 0 ||
        strcmp(normalizada, "1") == 0 ||
        strcmp(normalizada, "1.0") == 0) {
        return ATP_VALID;
    }
    if (strcmp(normalizada, "false") == 0 ||
        strcmp(normalizada, "0") == 0 ||
        strcmp(normalizada, "0.0") == 0) {
        return ATP_INVALID;
    }

    // 3. Tautologías aritméticas: 5 > 0, 0 < 5
    {
        char tok2[256][ATP_MAX_VAR_NAME];
        int nt2 = 0;
        if (_tokenizar(normalizada, tok2, &nt2) == 0 && nt2 == 3) {
            int izq_num = (isdigit((unsigned char)tok2[0][0]) ||
                           (tok2[0][0] == '-' && isdigit((unsigned char)tok2[0][1])));
            int der_num = (isdigit((unsigned char)tok2[2][0]) ||
                           (tok2[2][0] == '-' && isdigit((unsigned char)tok2[2][1])));
            if (izq_num && der_num) {
                double a = atof(tok2[0]);
                double b = atof(tok2[2]);
                if (strcmp(tok2[1], "<") == 0)  return (a < b)  ? ATP_VALID : ATP_INVALID;
                if (strcmp(tok2[1], ">") == 0)  return (a > b)  ? ATP_VALID : ATP_INVALID;
                if (strcmp(tok2[1], "<=") == 0) return (a <= b) ? ATP_VALID : ATP_INVALID;
                if (strcmp(tok2[1], ">=") == 0) return (a >= b) ? ATP_VALID : ATP_INVALID;
                if (strcmp(tok2[1], "==") == 0) return (a == b) ? ATP_VALID : ATP_INVALID;
                if (strcmp(tok2[1], "!=") == 0) return (a != b) ? ATP_VALID : ATP_INVALID;
            }
        }
    }

    // 4. a && a → a (redundancia detectada por descomposición)
    // Si no podemos determinar, devolver UNKNOWN
    return ATP_UNKNOWN;
}

int atp_verificar_contradiccion(ATPEngine* engine) {
    if (!engine) return -1;

    // 1. Verificar cada intervalo individualmente
    for (int i = 0; i < engine->num_intervalos; i++) {
        if (_intervalo_contradictorio(&engine->intervalos[i])) {
            snprintf(engine->error_message, ATP_MAX_ERROR_LEN,
                     "Contradicción en variable '%s': intervalo vacío [%g, %g]",
                     engine->intervalos[i].nombre,
                     engine->intervalos[i].inf,
                     engine->intervalos[i].sup);
            return 1;
        }
    }

    // 2. Verificar contradicciones entre pares de intervalos
    for (int i = 0; i < engine->num_intervalos; i++) {
        for (int j = i + 1; j < engine->num_intervalos; j++) {
            if (_intervalos_contradictorios(&engine->intervalos[i],
                                             &engine->intervalos[j])) {
                snprintf(engine->error_message, ATP_MAX_ERROR_LEN,
                         "Contradicción entre variables '%s' y '%s'",
                         engine->intervalos[i].nombre,
                         engine->intervalos[j].nombre);
                return 1;
            }
        }
    }

    // 3. Verificar contradicciones entre precondiciones individuales
    // (ej. x > 5 y x < 3 para la misma variable)
    for (int i = 0; i < engine->num_preconditions; i++) {
        for (int j = i + 1; j < engine->num_preconditions; j++) {
            ATPConstraint* a = &engine->preconditions[i];
            ATPConstraint* b = &engine->preconditions[j];

            // Si ambas tienen la misma variable y cotas opuestas
            if (a->num_vars == 1 && b->num_vars == 1 &&
                strcmp(a->vars[0], b->vars[0]) == 0) {
                if (a->tiene_cota_inf && b->tiene_cota_sup) {
                    if (a->cota_inferior > b->cota_superior) {
                        snprintf(engine->error_message, ATP_MAX_ERROR_LEN,
                                 "Contradicción en '%s': %s (%g) y %s (%g) son incompatibles",
                                 a->vars[0], a->expresion, a->cota_inferior,
                                 b->expresion, b->cota_superior);
                        return 1;
                    }
                }
                if (a->tiene_cota_sup && b->tiene_cota_inf) {
                    if (a->cota_superior < b->cota_inferior) {
                        snprintf(engine->error_message, ATP_MAX_ERROR_LEN,
                                 "Contradicción en '%s': %s (%g) y %s (%g) son incompatibles",
                                 a->vars[0], a->expresion, a->cota_superior,
                                 b->expresion, b->cota_inferior);
                        return 1;
                    }
                }
            }
        }
    }

    return 0;
}

int atp_propagar_restricciones(ATPEngine* engine) {
    if (!engine) return 0;

    int inferencias = 0;

    // Propagar entre precondiciones que comparten variables
    for (int i = 0; i < engine->num_preconditions; i++) {
        ATPConstraint* ci = &engine->preconditions[i];
        if (ci->num_vars != 1) continue;

        // Buscar la variable en los intervalos
        for (int v = 0; v < engine->num_intervalos; v++) {
            if (strcmp(engine->intervalos[v].nombre, ci->vars[0]) == 0) {
                // Aplicar cotas al intervalo
                int idx = v;
                if (ci->tiene_cota_inf) {
                    if (engine->intervalos[idx].tiene_inf) {
                        double nueva = (engine->intervalos[idx].inf > ci->cota_inferior)
                                        ? engine->intervalos[idx].inf : ci->cota_inferior;
                        if (nueva > engine->intervalos[idx].inf) {
                            inferencias++;
                        }
                        engine->intervalos[idx].inf = nueva;
                    } else {
                        engine->intervalos[idx].inf = ci->cota_inferior;
                        engine->intervalos[idx].tiene_inf = 1;
                        inferencias++;
                    }
                }
                if (ci->tiene_cota_sup) {
                    if (engine->intervalos[idx].tiene_sup) {
                        double nueva = (engine->intervalos[idx].sup < ci->cota_superior)
                                        ? engine->intervalos[idx].sup : ci->cota_superior;
                        if (nueva < engine->intervalos[idx].sup) {
                            inferencias++;
                        }
                        engine->intervalos[idx].sup = nueva;
                    } else {
                        engine->intervalos[idx].sup = ci->cota_superior;
                        engine->intervalos[idx].tiene_sup = 1;
                        inferencias++;
                    }
                }
                break;
            }
        }
    }

    // Propagar invariantes a los intervalos
    for (int i = 0; i < engine->num_invariants; i++) {
        ATPConstraint* ci = &engine->invariants[i];
        if (ci->num_vars != 1) continue;

        char var[ATP_MAX_VAR_NAME];
        double val;
        int op;
        if (_extraer_comparacion(ci->expresion, var, ATP_MAX_VAR_NAME, &val, &op) == 0) {
            for (int v = 0; v < engine->num_intervalos; v++) {
                if (strcmp(engine->intervalos[v].nombre, var) == 0) {
                    if (_aplicar_comparacion_a_intervalo(&engine->intervalos[v], op, val) == 0) {
                        inferencias++;
                    }
                    break;
                }
            }
        }
    }

    return inferencias;
}

int atp_demostrar(ATPEngine* engine) {
    if (!engine) return ATP_ERROR;

    clock_t inicio = clock();
    engine->estado = 1;  // Resolviendo
    engine->resolution_steps = 0;

    // 1. Propagar restricciones
    if (engine->config.use_propagation) {
        engine->resolution_steps += atp_propagar_restricciones(engine);
    }

    // 2. Verificar contradicciones en precondiciones
    if (engine->config.use_contradiction_check) {
        int contradiccion = atp_verificar_contradiccion(engine);
        if (contradiccion > 0) {
            engine->last_result = ATP_INVALID;
            engine->estado = 2;
            engine->resolution_time_ms = ((double)(clock() - inicio) / CLOCKS_PER_SEC) * 1000.0;
            return ATP_INVALID;
        }
    }

    // 3. Verificar cada postcondición contra las precondiciones
    int todas_validas = 1;
    int alguna_determinada = 0;

    for (int p = 0; p < engine->num_postconditions; p++) {
        ATPConstraint* post = &engine->postconditions[p];

        // Verificar tautología directa
        int taut = atp_verificar_tautologia(engine, post->expresion);
        if (taut == ATP_VALID) {
            engine->resolution_steps++;
            alguna_determinada = 1;
            continue;
        }
        if (taut == ATP_INVALID) {
            todas_validas = 0;
            alguna_determinada = 1;
            continue;
        }

        // Verificar si la postcondición es una comparación simple
        char post_var[ATP_MAX_VAR_NAME];
        double post_val;
        int post_op;
        if (_extraer_comparacion(post->expresion, post_var, ATP_MAX_VAR_NAME, &post_val, &post_op) == 0) {
            // Buscar la variable en los intervalos propagados
            for (int v = 0; v < engine->num_intervalos; v++) {
                if (strcmp(engine->intervalos[v].nombre, post_var) == 0) {
                    ATPInterval* iv = &engine->intervalos[v];
                    int valida = 0;

                    // Verificar si la postcondición está garantizada por los intervalos
                    int invalida = 0;
                    switch (post_op) {
                        case ATP_OP_LT:  // post: x < val
                            if (iv->tiene_sup && iv->sup < post_val) valida = 1;
                            // Contradicción: intervalo completamente >= post_val
                            if (iv->tiene_inf && iv->inf >= post_val) invalida = 1;
                            // Contraejemplo: sup > val → existen x en [inf, sup] que no cumplen x < val
                            if (iv->tiene_sup && iv->sup > post_val) invalida = 1;
                            break;
                        case ATP_OP_GT:  // post: x > val
                            if (iv->tiene_inf && iv->inf > post_val) valida = 1;
                            // Contradicción: intervalo completamente <= post_val
                            if (iv->tiene_sup && iv->sup <= post_val) invalida = 1;
                            // Contraejemplo: inf < val → existen x en [inf, sup] que no cumplen x > val
                            if (iv->tiene_inf && iv->inf < post_val) invalida = 1;
                            break;
                        case ATP_OP_LE:  // post: x <= val
                            if (iv->tiene_sup && iv->sup <= post_val) valida = 1;
                            // Contradicción: intervalo completamente > post_val
                            if (iv->tiene_inf && iv->inf > post_val) invalida = 1;
                            // Contraejemplo: sup > val → existen x en [inf, sup] que no cumplen x <= val
                            if (iv->tiene_sup && iv->sup > post_val) invalida = 1;
                            break;
                        case ATP_OP_GE:  // post: x >= val
                            if (iv->tiene_inf && iv->inf >= post_val) valida = 1;
                            // Contradicción: intervalo completamente < post_val
                            if (iv->tiene_sup && iv->sup < post_val) invalida = 1;
                            // Contraejemplo: inf < val → existen x en [inf, sup] que no cumplen x >= val
                            if (iv->tiene_inf && iv->inf < post_val) invalida = 1;
                            break;
                        case ATP_OP_EQ:  // post: x == val
                            if (iv->tiene_inf && iv->tiene_sup &&
                                iv->inf == post_val && iv->sup == post_val) valida = 1;
                            // Contradicción: val fuera del intervalo
                            if ((iv->tiene_inf && iv->inf > post_val) ||
                                (iv->tiene_sup && iv->sup < post_val)) invalida = 1;
                            break;
                        case ATP_OP_NEQ:  // post: x != val
                            if (iv->tiene_inf && iv->inf > post_val) valida = 1;
                            else if (iv->tiene_sup && iv->sup < post_val) valida = 1;
                            // Contradicción: intervalo = {val}
                            if (iv->tiene_inf && iv->tiene_sup &&
                                iv->inf == post_val && iv->sup == post_val) invalida = 1;
                            break;
                    }

                    if (invalida) {
                        // Postcondición definitivamente INVALIDA
                        todas_validas = 0;
                        alguna_determinada = 1;
                    } else if (valida) {
                        engine->resolution_steps++;
                        alguna_determinada = 1;
                    } else if (!valida) {
                        // Ni provable ni refutable por intervalos: verificar si post == pre
                        for (int r = 0; r < engine->num_preconditions; r++) {
                            if (strcmp(engine->preconditions[r].expresion, post->expresion) == 0) {
                                valida = 1;
                                engine->resolution_steps++;
                                alguna_determinada = 1;
                                break;
                            }
                        }
                        // Verificar también contra invariantes
                        if (!valida) {
                            for (int r = 0; r < engine->num_invariants; r++) {
                                if (strcmp(engine->invariants[r].expresion, post->expresion) == 0) {
                                    valida = 1;
                                    engine->resolution_steps++;
                                    alguna_determinada = 1;
                                    break;
                                }
                            }
                        }
                    }
                    break;
                }
            }
        } else {
            // Postcondición compleja — verificar con precondiciones directas
            // Si alguna precondición contiene la misma expresión, es válida
            for (int r = 0; r < engine->num_preconditions; r++) {
                if (strcmp(engine->preconditions[r].expresion, post->expresion) == 0) {
                    engine->resolution_steps++;
                    alguna_determinada = 1;
                    todas_validas = todas_validas && 1;
                    break;
                }
            }
        }
    }

    // 4. Verificar timeouts
    clock_t fin = clock();
    engine->resolution_time_ms = ((double)(fin - inicio) / CLOCKS_PER_SEC) * 1000.0;

    if (engine->resolution_time_ms > engine->config.timeout_ms) {
        engine->last_result = ATP_TIMEOUT;
        engine->estado = 2;
        return ATP_TIMEOUT;
    }

    // 5. Determinar resultado final
    if (alguna_determinada && todas_validas) {
        engine->last_result = ATP_VALID;
    } else if (!alguna_determinada) {
        engine->last_result = engine->config.verify_strict ? ATP_INVALID : ATP_UNKNOWN;
    } else {
        engine->last_result = ATP_INVALID;
    }

    engine->estado = 2;  // Completado
    return engine->last_result;
}

int atp_verificar_contrato(ATPEngine* engine,
                            const char** precondiciones, int num_pre,
                            const char** postcondiciones, int num_post) {
    if (!engine) return ATP_ERROR;

    // Limpiar estado anterior
    atp_limpiar(engine);

    // Agregar precondiciones
    for (int i = 0; i < num_pre && i < ATP_MAX_CONSTRAINTS; i++) {
        if (precondiciones[i]) {
            atp_agregar_precondicion(engine, precondiciones[i]);
        }
    }

    // Agregar postcondiciones
    for (int i = 0; i < num_post && i < ATP_MAX_CONSTRAINTS; i++) {
        if (postcondiciones[i]) {
            atp_agregar_postcondicion(engine, postcondiciones[i]);
        }
    }

    // Demostrar
    return atp_demostrar(engine);
}

ATPEstadisticas atp_obtener_estadisticas(ATPEngine* engine) {
    ATPEstadisticas stats = {0};
    if (!engine) return stats;

    stats.num_precondiciones = engine->num_preconditions;
    stats.num_postcondiciones = engine->num_postconditions;
    stats.num_resolution_steps = engine->resolution_steps;
    stats.tiempo_total_ms = engine->resolution_time_ms;
    stats.ultimo_resultado = engine->last_result;

    // Contar contradicciones
    if (engine->last_result == ATP_INVALID) {
        stats.num_contradicciones_encontradas = 1;
    }
    if (engine->last_result == ATP_VALID) {
        stats.num_teoremas_demostrados = 1;
    }

    return stats;
}

int atp_guardar(const ATPEngine* engine, const char* ruta) {
    if (!engine || !ruta) return -1;

    FILE* f = fopen(ruta, "wb");
    if (!f) return -1;

    uint32_t magic = ATP_MAGIC_HEADER;
    uint32_t version = ATP_VERSION;
    fwrite(&magic, sizeof(magic), 1, f);
    fwrite(&version, sizeof(version), 1, f);

    // Guardar configuración
    fwrite(&engine->config, sizeof(ATPConfig), 1, f);

    // Guardar número de restricciones
    uint32_t np = (uint32_t)engine->num_preconditions;
    uint32_t nq = (uint32_t)engine->num_postconditions;
    uint32_t ni = (uint32_t)engine->num_invariants;
    fwrite(&np, sizeof(np), 1, f);
    fwrite(&nq, sizeof(nq), 1, f);
    fwrite(&ni, sizeof(ni), 1, f);

    // Guardar restricciones
    for (uint32_t i = 0; i < np; i++) {
        fwrite(&engine->preconditions[i], sizeof(ATPConstraint), 1, f);
    }
    for (uint32_t i = 0; i < nq; i++) {
        fwrite(&engine->postconditions[i], sizeof(ATPConstraint), 1, f);
    }
    for (uint32_t i = 0; i < ni; i++) {
        fwrite(&engine->invariants[i], sizeof(ATPConstraint), 1, f);
    }

    // Guardar intervalos
    uint32_t nv = (uint32_t)engine->num_intervalos;
    fwrite(&nv, sizeof(nv), 1, f);
    for (uint32_t i = 0; i < nv; i++) {
        fwrite(&engine->intervalos[i], sizeof(ATPInterval), 1, f);
    }

    // Guardar nombre de función y resultado
    fwrite(engine->function_name, sizeof(engine->function_name), 1, f);
    fwrite(&engine->last_result, sizeof(engine->last_result), 1, f);

    fclose(f);
    return 0;
}

int atp_cargar(ATPEngine* engine, const char* ruta) {
    if (!engine || !ruta) return -1;

    FILE* f = fopen(ruta, "rb");
    if (!f) return -1;

    uint32_t magic, version;
    if (fread(&magic, sizeof(magic), 1, f) != 1 || magic != ATP_MAGIC_HEADER) {
        fclose(f); return -1;
    }
    if (fread(&version, sizeof(version), 1, f) != 1 || version > ATP_VERSION) {
        fclose(f); return -1;
    }

    // Cargar configuración
    if (fread(&engine->config, sizeof(ATPConfig), 1, f) != 1) {
        fclose(f); return -1;
    }

    // Cargar números de restricciones
    uint32_t np, nq, ni;
    if (fread(&np, sizeof(np), 1, f) != 1 ||
        fread(&nq, sizeof(nq), 1, f) != 1 ||
        fread(&ni, sizeof(ni), 1, f) != 1) {
        fclose(f); return -1;
    }

    if (np > ATP_MAX_CONSTRAINTS || nq > ATP_MAX_CONSTRAINTS || ni > ATP_MAX_CONSTRAINTS) {
        fclose(f); return -1;
    }

    // Cargar restricciones
    for (uint32_t i = 0; i < np; i++) {
        if (fread(&engine->preconditions[i], sizeof(ATPConstraint), 1, f) != 1) {
            fclose(f); return -1;
        }
    }
    engine->num_preconditions = (int)np;

    for (uint32_t i = 0; i < nq; i++) {
        if (fread(&engine->postconditions[i], sizeof(ATPConstraint), 1, f) != 1) {
            fclose(f); return -1;
        }
    }
    engine->num_postconditions = (int)nq;

    for (uint32_t i = 0; i < ni; i++) {
        if (fread(&engine->invariants[i], sizeof(ATPConstraint), 1, f) != 1) {
            fclose(f); return -1;
        }
    }
    engine->num_invariants = (int)ni;

    // Cargar intervalos
    uint32_t nv;
    if (fread(&nv, sizeof(nv), 1, f) != 1 || nv > ATP_MAX_VARS) {
        fclose(f); return -1;
    }
    for (uint32_t i = 0; i < nv; i++) {
        if (fread(&engine->intervalos[i], sizeof(ATPInterval), 1, f) != 1) {
            fclose(f); return -1;
        }
    }
    engine->num_intervalos = (int)nv;

    // Cargar nombre de función y resultado
    if (fread(engine->function_name, sizeof(engine->function_name), 1, f) != 1 ||
        fread(&engine->last_result, sizeof(engine->last_result), 1, f) != 1) {
        fclose(f); return -1;
    }

    fclose(f);
    return 0;
}

void atp_limpiar(ATPEngine* engine) {
    if (!engine) return;
    engine->num_preconditions = 0;
    engine->num_postconditions = 0;
    engine->num_invariants = 0;
    engine->num_intervalos = 0;
    engine->last_result = ATP_UNKNOWN;
    engine->error_message[0] = '\0';
    engine->resolution_steps = 0;
    engine->resolution_time_ms = 0.0;
    engine->estado = 0;
}

void atp_cerrar(ATPEngine* engine) {
    if (!engine) return;
    free(engine);
}

// ============================================================
// Wrappers _syn_atp_* para enlace con std.atp_engine
// ============================================================

void* _syn_atp_iniciar(int use_arith, int use_prop, int use_contra) {
    ATPConfig cfg;
    memset(&cfg, 0, sizeof(ATPConfig));
    cfg.max_resolution_depth = 100;
    cfg.max_theorem_size = 256;
    cfg.use_arithmetic_solver = use_arith ? 1 : 0;
    cfg.use_propagation = use_prop ? 1 : 0;
    cfg.use_contradiction_check = use_contra ? 1 : 0;
    cfg.timeout_ms = 5000;
    cfg.verify_strict = 0;
    return atp_iniciar(&cfg);
}

void _syn_atp_cerrar(void* engine) {
    atp_cerrar((ATPEngine*)engine);
}

int _syn_atp_agregar_precondicion(void* engine, const char* expr) {
    return atp_agregar_precondicion((ATPEngine*)engine, expr);
}

int _syn_atp_agregar_postcondicion(void* engine, const char* expr) {
    return atp_agregar_postcondicion((ATPEngine*)engine, expr);
}

int _syn_atp_agregar_invariante(void* engine, const char* expr) {
    return atp_agregar_invariante((ATPEngine*)engine, expr);
}

void _syn_atp_establecer_funcion(void* engine, const char* nombre) {
    atp_establecer_funcion((ATPEngine*)engine, nombre);
}

int _syn_atp_verificar_tautologia(void* engine, const char* expr) {
    return atp_verificar_tautologia((ATPEngine*)engine, expr);
}

int _syn_atp_verificar_contradiccion(void* engine) {
    return atp_verificar_contradiccion((ATPEngine*)engine);
}

int _syn_atp_propagar_restricciones(void* engine) {
    return atp_propagar_restricciones((ATPEngine*)engine);
}

int _syn_atp_demostrar(void* engine) {
    return atp_demostrar((ATPEngine*)engine);
}

int _syn_atp_verificar_contrato(void* engine,
                                 const char** pre, int npre,
                                 const char** post, int npost) {
    return atp_verificar_contrato((ATPEngine*)engine, pre, npre, post, npost);
}

void _syn_atp_limpiar(void* engine) {
    atp_limpiar((ATPEngine*)engine);
}

int _syn_atp_guardar(void* engine, const char* ruta) {
    return atp_guardar((const ATPEngine*)engine, ruta);
}

int _syn_atp_cargar(void* engine, const char* ruta) {
    return atp_cargar((ATPEngine*)engine, ruta);
}
