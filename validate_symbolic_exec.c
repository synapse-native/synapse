// validate_symbolic_exec.c — Suite de validación del Motor de Ejecución Simbólica (M15.3)
// =====================================================================================
// Pruebas aisladas y autónomas fuera del directorio protegido tests/.
//
// Valida:
//   1. Inicialización y ciclo de vida
//   2. Variables simbólicas y restricciones
//   3. Exploración de rutas (path exploration)
//   4. Bifurcaciones de control (if/else)
//   5. Detección de caminos imposibles
//   6. Detección de división por cero simbólica
//   7. Detección de desbordamiento
//   8. Detección de acceso fuera de límites
//   9. Detección de violaciones de contrato
//   10. Persistencia (guardar/cargar)
//   11. Limpieza y reutilización
//   12. Casos borde
//
// Compilación:
//   gcc -O2 -std=c99 -Wall -Wextra -Werror -static validate_symbolic_exec.c
//       nucleo/symbolic_exec.c -o validate_symbolic_exec.exe -lm
// =====================================================================

#include "nucleo/symbolic_exec.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

// ============================================================
// Métricas de prueba
// ============================================================
static int test_passed = 0;
static int test_failed = 0;
static int section_num = 0;

#define TEST(nombre, expr) do { \
    if (!(expr)) { \
        fprintf(stderr, "  [FAIL] %s (línea %d)\n", nombre, __LINE__); \
        test_failed++; \
    } else { \
        test_passed++; \
    } \
} while(0)

#define SECCION(nombre) do { \
    section_num++; \
    printf("\n=== Sección %d: %s ===\n", section_num, nombre); \
} while(0)

// ============================================================
// 1. Inicialización y ciclo de vida
// ============================================================
static void test_lifecycle(void) {
    SECCION("Inicialización y ciclo de vida");

    // 1.1 Crear con configuración NULL
    SEEngine* e = se_iniciar(NULL, NULL);
    TEST("se_iniciar(NULL) no es NULL", e != NULL);
    TEST("Estado inicial: 0", e->estado == 0);
    TEST("Num variables inicial: 0", e->num_variables == 0);
    TEST("Num paths inicial: 0", e->num_paths == 0);
    TEST("Active path: -1", e->active_path_idx == -1);

    // 1.2 Crear con configuración explícita
    SEConfig cfg;
    memset(&cfg, 0, sizeof(SEConfig));
    cfg.explore_mode = SE_EXPLORE_ALL;
    cfg.max_path_depth = 50;
    cfg.detect_div_by_zero = 1;
    cfg.detect_overflow = 1;
    cfg.detect_bounds = 0;
    cfg.detect_contract_violations = 1;
    cfg.timeout_ms = 1000;

    SEEngine* e2 = se_iniciar(&cfg, NULL);
    TEST("se_iniciar(config) no es NULL", e2 != NULL);
    TEST("Config max_path_depth = 50", e2->config.max_path_depth == 50);
    TEST("Config detect_bounds = 0", e2->config.detect_bounds == 0);

    // 1.3 Cerrar
    se_cerrar(e);
    se_cerrar(e2);
    TEST("Cierre exitoso (sin crash)", 1);
}

// ============================================================
// 2. Variables simbólicas y restricciones
// ============================================================
static void test_symbolic_variables(void) {
    SECCION("Variables simbólicas y restricciones");

    SEEngine* e = se_iniciar(NULL, NULL);
    TEST("Motor creado para variables", e != NULL);

    // 2.1 Crear variable simbólica
    int idx = se_agregar_variable(e, "x", 0.0, 100.0, 0);
    TEST("se_agregar_variable('x', 0, 100) retorna >= 0", idx >= 0);
    TEST("Variable 'x' tiene nombre correcto", strcmp(e->variables[0].nombre, "x") == 0);
    TEST("Variable 'x' cota_inf = 0", e->variables[0].cota_inf == 0.0);
    TEST("Variable 'x' cota_sup = 100", e->variables[0].cota_sup == 100.0);
    TEST("Variable 'x' es simbólica", e->variables[0].es_simbolica == 1);

    // 2.2 Crear segunda variable
    idx = se_agregar_variable(e, "y", -50.0, 50.0, 0);
    TEST("se_agregar_variable('y', -50, 50) retorna >= 0", idx >= 0);

    // 2.3 No duplicados
    idx = se_agregar_variable(e, "x", 0.0, 10.0, 0);
    TEST("Variable duplicada 'x' retorna -1", idx == -1);

    // 2.4 Agregar restricción
    int rc = se_agregar_restriccion(e, "x > 5", SE_CONSTRAINT_GT);
    TEST("se_agregar_restriccion('x > 5') retorna >= 0", rc >= 0);
    TEST("Variable 'x' cota_inf actualizada a 5 (de 0)", e->variables[0].cota_inf >= 4.999);

    // 2.5 Ruta se crea automáticamente
    TEST("Ruta creada automáticamente", e->num_paths >= 1);

    se_cerrar(e);
}

// ============================================================
// 3. Exploración de rutas
// ============================================================
static void test_path_exploration(void) {
    SECCION("Exploración de rutas");

    SEEngine* e = se_iniciar(NULL, NULL);
    se_agregar_variable(e, "x", 0.0, 100.0, 0);

    // 3.1 Explorar sin bifurcaciones (ruta única)
    int n = se_explorar(e);
    TEST("Exploración sin bifurcaciones retorna >= 1", n >= 1);
    TEST("Ruta marcada como explorada",
         e->paths[0].estado == SE_PATH_EXPLORED);

    se_cerrar(e);
}

// ============================================================
// 4. Bifurcaciones de control
// ============================================================
static void test_branching(void) {
    SECCION("Bifurcaciones de control");

    // 4.1 Bifurcación simple: x > 5 (then/else)
    {
        SEEngine* e = se_iniciar(NULL, NULL);
        se_agregar_variable(e, "x", 0.0, 100.0, 0);
        se_agregar_restriccion(e, "x > 10", SE_CONSTRAINT_GT);

        int rc = se_bifurcar(e, "x > 50");
        TEST("Bifurcación retorna 0", rc == 0);
        TEST("Dos rutas después de bifurcar", e->num_paths == 2);
        TEST("Ruta 0 (then) factible",
             e->paths[0].estado == SE_PATH_FEASIBLE);
        se_cerrar(e);
    }

    // 4.2 Bifurcación con rama imposible
    {
        SEEngine* e = se_iniciar(NULL, NULL);
        se_agregar_variable(e, "x", 0.0, 10.0, 0);
        se_agregar_restriccion(e, "x > 5", SE_CONSTRAINT_GT);

        // Bifurcar: x > 15 — la negación (x <= 15) es factible, x > 15 debe ser imposible
        se_bifurcar(e, "x > 15");
        TEST("Bifurcación con rama posible sea factible",
             e->num_paths >= 1);
        se_cerrar(e);
    }

    // 4.3 Múltiples bifurcaciones
    {
        SEEngine* e = se_iniciar(NULL, NULL);
        se_agregar_variable(e, "x", -10.0, 10.0, 0);
        se_agregar_restriccion(e, "x > 0", SE_CONSTRAINT_GT);

        se_bifurcar(e, "x < 5");
        se_activar_ruta(e, 0);
        se_bifurcar(e, "x < 8");
        TEST("Múltiples bifurcaciones: 3+ rutas", e->num_paths >= 3);
        se_cerrar(e);
    }
}

// ============================================================
// 5. Detección de caminos imposibles
// ============================================================
static void test_infeasible_paths(void) {
    SECCION("Detección de caminos imposibles");

    // 5.1 Restricciones contradictorias
    {
        SEEngine* e = se_iniciar(NULL, NULL);
        se_agregar_variable(e, "x", 0.0, 10.0, 0);
        se_agregar_restriccion(e, "x > 5", SE_CONSTRAINT_GT);

        // x < 3 es contradictorio con x > 5
        int rc = se_agregar_restriccion(e, "x < 3", SE_CONSTRAINT_LT);
        TEST("x < 3 después de x > 5 retorna -1 (contradicción)", rc == -1);
        se_cerrar(e);
    }

    // 5.2 Alcanzabilidad después de contradicción
    {
        SEEngine* e = se_iniciar(NULL, NULL);
        se_agregar_variable(e, "x", 0.0, 100.0, 0);
        se_agregar_restriccion(e, "x > 50", SE_CONSTRAINT_GT);
        TEST("Ruta alcanzable sin contradicción",
             se_verificar_alcanzabilidad(e) == 1);

        // Esto debería marcar la ruta como infactible
        se_agregar_restriccion(e, "x < 30", SE_CONSTRAINT_LT);
        TEST("Ruta NO alcanzable después de contradicción",
             se_verificar_alcanzabilidad(e) == 0);
        se_cerrar(e);
    }
}

// ============================================================
// 6. Detección de división por cero simbólica
// ============================================================
static void test_div_by_zero(void) {
    SECCION("Detección de división por cero");

    // 6.1 Divisor literal cero
    {
        SEEngine* e = se_iniciar(NULL, NULL);
        int v = se_detectar_division_por_cero(e, "0");
        TEST("Divisor literal '0' detectado como riesgo",
             v == SE_VIOLATION_DIV_BY_ZERO);
        se_cerrar(e);
    }

    // 6.2 Variable simbólica que puede ser cero
    {
        SEEngine* e = se_iniciar(NULL, NULL);
        se_agregar_variable(e, "x", -5.0, 5.0, 0);  // x puede ser 0
        int v = se_detectar_division_por_cero(e, "x");
        TEST("Variable 'x' en [-5,5] detectada como riesgo de div/0",
             v == SE_VIOLATION_DIV_BY_ZERO);
        se_cerrar(e);
    }

    // 6.3 Variable simbólica que NO puede ser cero
    {
        SEEngine* e = se_iniciar(NULL, NULL);
        se_agregar_variable(e, "x", 10.0, 100.0, 0);  // x > 0
        int v = se_detectar_division_por_cero(e, "x");
        TEST("Variable 'x' en [10,100] NO tiene riesgo de div/0",
             v == SE_VIOLATION_NONE);
        se_cerrar(e);
    }

    // 6.4 Variable restringida para evitar cero
    {
        SEEngine* e = se_iniciar(NULL, NULL);
        se_agregar_variable(e, "x", -10.0, 10.0, 0);
        se_agregar_restriccion(e, "x > 1", SE_CONSTRAINT_GT);
        int v = se_detectar_division_por_cero(e, "x");
        TEST("Variable 'x' > 1 NO tiene riesgo de div/0",
             v == SE_VIOLATION_NONE);
        se_cerrar(e);
    }
}

// ============================================================
// 7. Detección de desbordamiento
// ============================================================
static void test_overflow(void) {
    SECCION("Detección de desbordamiento");

    // 7.1 Variable dentro de límites seguros
    {
        SEEngine* e = se_iniciar(NULL, NULL);
        se_agregar_variable(e, "x", 0.0, 100.0, 0);
        int v = se_detectar_desbordamiento(e, "x + 1", 0.0, 1000.0);
        TEST("x en [0,100] dentro de [0,1000] NO es overflow",
             v == SE_VIOLATION_NONE);
        se_cerrar(e);
    }

    // 7.2 Variable fuera de límites seguros
    {
        SEEngine* e = se_iniciar(NULL, NULL);
        se_agregar_variable(e, "x", 0.0, 1000.0, 0);
        int v = se_detectar_desbordamiento(e, "x", 0.0, 100.0);
        TEST("x en [0,1000] puede exceder [0,100] → overflow",
             v == SE_VIOLATION_OVERFLOW);
        se_cerrar(e);
    }
}

// ============================================================
// 8. Detección de acceso fuera de límites
// ============================================================
static void test_bounds(void) {
    SECCION("Detección de acceso fuera de límites");

    // 8.1 Índice dentro de límites
    {
        SEEngine* e = se_iniciar(NULL, NULL);
        se_agregar_variable(e, "i", 0.0, 9.0, 0);
        int v = se_detectar_fuera_limites(e, "i", 10);
        TEST("i en [0,9] para array[10] NO es fuera de límites",
             v == SE_VIOLATION_NONE);
        se_cerrar(e);
    }

    // 8.2 Índice puede exceder límite superior
    {
        SEEngine* e = se_iniciar(NULL, NULL);
        se_agregar_variable(e, "i", 0.0, 20.0, 0);
        int v = se_detectar_fuera_limites(e, "i", 10);
        TEST("i en [0,20] para array[10] → posible BOUNDS",
             v == SE_VIOLATION_BOUNDS);
        se_cerrar(e);
    }

    // 8.3 Índice puede ser negativo
    {
        SEEngine* e = se_iniciar(NULL, NULL);
        se_agregar_variable(e, "i", -5.0, 5.0, 0);
        int v = se_detectar_fuera_limites(e, "i", 10);
        TEST("i en [-5,5] para array[10] → posible BOUNDS (negativo)",
             v == SE_VIOLATION_BOUNDS);
        se_cerrar(e);
    }
}

// ============================================================
// 9. Detección de violaciones de contrato
// ============================================================
static void test_contract_violations(void) {
    SECCION("Detección de violaciones de contrato");

    // 9.1 Contrato válido (sin violación)
    {
        SEEngine* e = se_iniciar(NULL, NULL);
        se_agregar_variable(e, "x", 0.0, 100.0, 0);
        se_agregar_restriccion(e, "x > 5", SE_CONSTRAINT_GT);

        const char* pre[] = {"x > 0"};
        int v = se_detectar_violacion_contrato(e, pre, 1, NULL, 0);
        TEST("x > 5 cumple pre 'x > 0' → SIN violación",
             v == SE_VIOLATION_NONE);
        se_cerrar(e);
    }

    // 9.2 Precondición contradictoria
    {
        SEEngine* e = se_iniciar(NULL, NULL);
        se_agregar_variable(e, "x", 0.0, 10.0, 0);
        se_agregar_restriccion(e, "x < 5", SE_CONSTRAINT_LT);

        const char* pre[] = {"x > 10"};
        int v = se_detectar_violacion_contrato(e, pre, 1, NULL, 0);
        TEST("x < 5 contradice pre 'x > 10' → VIOLACIÓN",
             v == SE_VIOLATION_CONTRACT);
        se_cerrar(e);
    }
}

// ============================================================
// 10. Persistencia (guardar/cargar)
// ============================================================
static void test_persistence(void) {
    SECCION("Persistencia (guardar/cargar)");

    const char* ruta = "_test_seng.bin";

    // 10.1 Guardar motor con datos
    {
        SEEngine* e = se_iniciar(NULL, NULL);
        se_agregar_variable(e, "x", 0.0, 100.0, 0);
        se_agregar_variable(e, "y", -10.0, 10.0, 0);
        se_agregar_restriccion(e, "x > 5", SE_CONSTRAINT_GT);

        int r = se_guardar(e, ruta);
        TEST("Guardar motor SE retorna 0", r == 0);
        se_cerrar(e);
    }

    // 10.2 Cargar y verificar
    {
        SEEngine* e = se_iniciar(NULL, NULL);
        int r = se_cargar(e, ruta);
        TEST("Cargar motor SE retorna 0", r == 0);
        TEST("Número de variables después de cargar", e->num_variables == 2);
        TEST("Variable 'x' preservada",
             strcmp(e->variables[0].nombre, "x") == 0);
        TEST("Variable 'x' cota_inf preservada (>=5 por x>5)", e->variables[0].cota_inf >= 5.0);
        TEST("Variable 'y' preservada",
             strcmp(e->variables[1].nombre, "y") == 0);
        se_cerrar(e);
    }

    // 10.3 Archivo inexistente
    {
        SEEngine* e = se_iniciar(NULL, NULL);
        int r = se_cargar(e, "_no_existe.bin");
        TEST("Cargar archivo inexistente retorna -1", r == -1);
        se_cerrar(e);
    }

    remove(ruta);
}

// ============================================================
// 11. Limpieza y reutilización
// ============================================================
static void test_cleanup(void) {
    SECCION("Limpieza y reutilización");

    // 11.1 Limpiar y reusar
    {
        SEEngine* e = se_iniciar(NULL, NULL);
        se_agregar_variable(e, "x", 0.0, 100.0, 0);
        se_agregar_restriccion(e, "x > 5", SE_CONSTRAINT_GT);
        TEST("Variables antes de limpiar", e->num_variables == 1);
        TEST("Rutas antes de limpiar", e->num_paths >= 1);

        se_limpiar(e);
        TEST("Variables después de limpiar", e->num_variables == 0);
        TEST("Rutas después de limpiar", e->num_paths == 0);
        TEST("Active path después de limpiar", e->active_path_idx == -1);

        // Reutilizar
        se_agregar_variable(e, "y", -50.0, 50.0, 0);
        TEST("Variable después de reutilizar", e->num_variables == 1);
        se_cerrar(e);
    }

    // 11.2 Múltiples motores simultáneos
    {
        SEEngine* e1 = se_iniciar(NULL, NULL);
        SEEngine* e2 = se_iniciar(NULL, NULL);

        se_agregar_variable(e1, "x", 0.0, 10.0, 0);
        se_agregar_variable(e2, "y", 100.0, 200.0, 0);

        TEST("Motor 1: 1 variable", e1->num_variables == 1);
        TEST("Motor 2: 1 variable", e2->num_variables == 1);
        TEST("Motores independientes", e1 != e2);

        se_cerrar(e1);
        se_cerrar(e2);
    }
}

// ============================================================
// 12. Casos borde
// ============================================================
static void test_edge_cases(void) {
    SECCION("Casos borde");

    // 12.1 NULL pointer safety
    {
        se_limpiar(NULL);
        TEST("se_limpiar(NULL) es seguro", 1);

        se_cerrar(NULL);
        TEST("se_cerrar(NULL) es seguro", 1);

        int v = se_verificar_alcanzabilidad(NULL);
        TEST("se_verificar_alcanzabilidad(NULL) = -1", v == -1);
    }

    // 12.2 Sin variables simbólicas
    {
        SEEngine* e = se_iniciar(NULL, NULL);
        int v = se_detectar_division_por_cero(e, "x");
        TEST("Div/0 sin variables retorna NONE", v == SE_VIOLATION_NONE);
        se_cerrar(e);
    }

    // 12.3 Exploración sin datos
    {
        SEEngine* e = se_iniciar(NULL, NULL);
        int n = se_explorar(e);
        TEST("Exploración sin datos retorna >= 0", n >= 0);
        se_cerrar(e);
    }

    // 12.4 Activar ruta inválida
    {
        SEEngine* e = se_iniciar(NULL, NULL);
        int rc = se_activar_ruta(e, 999);
        TEST("Activar ruta inválida retorna -1", rc == -1);
        se_cerrar(e);
    }

    // 12.5 Variable con nombre muy largo
    {
        SEEngine* e = se_iniciar(NULL, NULL);
        char nombre_largo[200];
        memset(nombre_largo, 'a', 190);
        nombre_largo[190] = '\0';
        int idx = se_agregar_variable(e, nombre_largo, 0.0, 1.0, 0);
        TEST("Variable con nombre largo se trunca correctamente", idx >= 0);
        TEST("Nombre truncado a max_var_name",
             strlen(e->variables[0].nombre) <= SE_MAX_VAR_NAME);
        se_cerrar(e);
    }

    // 12.6 Límite de variables
    {
        SEEngine* e = se_iniciar(NULL, NULL);
        int ok = 1;
        for (int i = 0; i < SE_MAX_VARS + 5; i++) {
            char buf[32];
            snprintf(buf, 32, "v_%d", i);
            int r = se_agregar_variable(e, buf, 0.0, 1.0, 0);
            if (i >= SE_MAX_VARS && r >= 0) { ok = 0; break; }
        }
        TEST("Límite de variables respetado", ok == 1);
        se_cerrar(e);
    }
}

// ============================================================
// Main
// ============================================================
int main(void) {
    printf("============================================================\n");
    printf("  VALIDACIÓN DEL MOTOR DE EJECUCIÓN SIMBÓLICA\n");
    printf("  Symbolic Execution Engine — M15.3\n");
    printf("============================================================\n\n");

    test_lifecycle();
    test_symbolic_variables();
    test_path_exploration();
    test_branching();
    test_infeasible_paths();
    test_div_by_zero();
    test_overflow();
    test_bounds();
    test_contract_violations();
    test_persistence();
    test_cleanup();
    test_edge_cases();

    printf("\n============================================================\n");
    printf("  RESULTADOS\n");
    printf("============================================================\n");
    printf("  Pruebas: %d secciones\n", section_num);
    printf("  Pasadas: %d\n", test_passed);
    printf("  Falladas: %d\n", test_failed);
    printf("============================================================\n\n");

    return test_failed > 0 ? 1 : 0;
}
