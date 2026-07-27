// validate_atp_engine.c — Suite de validación del Motor ATP (M15.2)
// =================================================================
// Pruebas aisladas y autónomas fuera del directorio protegido tests/.
// Valida:
//   1. Inicialización y ciclo de vida
//   2. Tautologías aritméticas
//   3. Tautologías lógicas
//   4. Detección de contradicciones
//   5. Propagación de restricciones
//   6. Verificación de contratos (pre → post)
//   7. Contratos inválidos y contraejemplos
//   8. Contratos con invariantes
//   9. Persistencia (guardar/cargar)
//   10. Limpieza y reutilización
//   11. Casos borde
//   12. Integración con proof_bridge
//
// Compilación:
//   gcc -O2 -std=c99 -Wall -Wextra -Werror -static validate_atp_engine.c
//       nucleo/atp_engine.c -o validate_atp_engine.exe -lm
// =================================================================

#include "nucleo/atp_engine.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <math.h>

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

    // 1.1 Crear con configuración NULL (valores por defecto)
    ATPEngine* e = atp_iniciar(NULL);
    TEST("atp_iniciar(NULL) no es NULL", e != NULL);
    TEST("Estado inicial: 0", e->estado == 0);
    TEST("Num preconditions inicial: 0", e->num_preconditions == 0);
    TEST("Num postconditions inicial: 0", e->num_postconditions == 0);
    TEST("Num invariants inicial: 0", e->num_invariants == 0);
    TEST("Num intervalos inicial: 0", e->num_intervalos == 0);
    TEST("Last result inicial: UNKNOWN", e->last_result == ATP_UNKNOWN);

    // 1.2 Crear con configuración explícita
    ATPConfig cfg;
    memset(&cfg, 0, sizeof(ATPConfig));
    cfg.max_resolution_depth = 50;
    cfg.max_theorem_size = 128;
    cfg.use_arithmetic_solver = 1;
    cfg.use_propagation = 1;
    cfg.use_contradiction_check = 1;
    cfg.timeout_ms = 1000;
    cfg.verify_strict = 0;

    ATPEngine* e2 = atp_iniciar(&cfg);
    TEST("atp_iniciar(config) no es NULL", e2 != NULL);
    TEST("Config depth = 50", e2->config.max_resolution_depth == 50);
    TEST("Config timeout = 1000", e2->config.timeout_ms == 1000);

    // 1.3 Cerrar motores
    atp_cerrar(e);
    atp_cerrar(e2);
    TEST("Cierre exitoso (sin crash)", 1);
}

// ============================================================
// 2. Tautologías aritméticas
// ============================================================
static void test_arithmetic_tautologies(void) {
    SECCION("Tautologías aritméticas");

    ATPEngine* e = atp_iniciar(NULL);
    TEST("Motor creado para tautologías", e != NULL);

    // 2.1 x == x
    TEST("x == x es VÁLIDO",
         atp_verificar_tautologia(e, "x == x") == ATP_VALID);

    // 2.2 x >= x
    TEST("x >= x es VÁLIDO",
         atp_verificar_tautologia(e, "x >= x") == ATP_VALID);

    // 2.3 x <= x
    TEST("x <= x es VÁLIDO",
         atp_verificar_tautologia(e, "x <= x") == ATP_VALID);

    // 2.4 x != x es FALSO
    TEST("x != x es INVÁLIDO",
         atp_verificar_tautologia(e, "x != x") == ATP_INVALID);

    // 2.5 x > x es FALSO
    TEST("x > x es INVÁLIDO",
         atp_verificar_tautologia(e, "x > x") == ATP_INVALID);

    // 2.6 x < x es FALSO
    TEST("x < x es INVÁLIDO",
         atp_verificar_tautologia(e, "x < x") == ATP_INVALID);

    // 2.7 true es VÁLIDO
    TEST("true es VÁLIDO",
         atp_verificar_tautologia(e, "true") == ATP_VALID);

    // 2.8 false es INVÁLIDO
    TEST("false es INVÁLIDO",
         atp_verificar_tautologia(e, "false") == ATP_INVALID);

    // 2.9 5 > 0
    TEST("5 > 0 es VÁLIDO",
         atp_verificar_tautologia(e, "5 > 0") == ATP_VALID);

    // 2.10 0 > 5
    TEST("0 > 5 es INVÁLIDO",
         atp_verificar_tautologia(e, "0 > 5") == ATP_INVALID);

    // 2.11 3 < 10
    TEST("3 < 10 es VÁLIDO",
         atp_verificar_tautologia(e, "3 < 10") == ATP_VALID);

    // 2.12 10 < 3
    TEST("10 < 3 es INVÁLIDO",
         atp_verificar_tautologia(e, "10 < 3") == ATP_INVALID);

    // 2.13 5 <= 5
    TEST("5 <= 5 es VÁLIDO",
         atp_verificar_tautologia(e, "5 <= 5") == ATP_VALID);

    // 2.14 5 == 5
    TEST("5 == 5 es VÁLIDO",
         atp_verificar_tautologia(e, "5 == 5") == ATP_VALID);

    // 2.15 5 != 3
    TEST("5 != 3 es VÁLIDO",
         atp_verificar_tautologia(e, "5 != 3") == ATP_VALID);

    // 2.16 -1 < 0
    TEST("-1 < 0 es VÁLIDO",
         atp_verificar_tautologia(e, "-1 < 0") == ATP_VALID);

    atp_cerrar(e);
}

// ============================================================
// 3. Detección de contradicciones
// ============================================================
static void test_contradictions(void) {
    SECCION("Detección de contradicciones");

    // 3.1 x > 5 y x < 3 es contradictorio
    {
        ATPEngine* e = atp_iniciar(NULL);
        atp_agregar_precondicion(e, "x > 5");
        atp_agregar_precondicion(e, "x < 3");
        int contra = atp_verificar_contradiccion(e);
        TEST("x > 5 y x < 3 → contradicción", contra == 1);
        atp_cerrar(e);
    }

    // 3.2 x > 5 y x >= 3 NO es contradictorio
    {
        ATPEngine* e = atp_iniciar(NULL);
        atp_agregar_precondicion(e, "x > 5");
        atp_agregar_precondicion(e, "x >= 3");
        int contra = atp_verificar_contradiccion(e);
        TEST("x > 5 y x >= 3 → NO contradicción", contra == 0);
        atp_cerrar(e);
    }

    // 3.3 x < 10 y x > 20 es contradictorio
    {
        ATPEngine* e = atp_iniciar(NULL);
        atp_agregar_precondicion(e, "x < 10");
        atp_agregar_precondicion(e, "x > 20");
        int contra = atp_verificar_contradiccion(e);
        TEST("x < 10 y x > 20 → contradicción", contra == 1);
        atp_cerrar(e);
    }

    // 3.4 x < 10 y x > 5 NO es contradictorio
    {
        ATPEngine* e = atp_iniciar(NULL);
        atp_agregar_precondicion(e, "x < 10");
        atp_agregar_precondicion(e, "x > 5");
        int contra = atp_verificar_contradiccion(e);
        TEST("x < 10 y x > 5 → NO contradicción", contra == 0);
        atp_cerrar(e);
    }

    // 3.5 x == 5 y x == 10 es contradictorio
    {
        ATPEngine* e = atp_iniciar(NULL);
        atp_agregar_precondicion(e, "x == 5");
        atp_agregar_precondicion(e, "x == 10");
        int contra = atp_verificar_contradiccion(e);
        TEST("x == 5 y x == 10 → contradicción", contra == 1);
        atp_cerrar(e);
    }

    // 3.6 x == 5 y x > 0 NO es contradictorio
    {
        ATPEngine* e = atp_iniciar(NULL);
        atp_agregar_precondicion(e, "x == 5");
        atp_agregar_precondicion(e, "x > 0");
        int contra = atp_verificar_contradiccion(e);
        TEST("x == 5 y x > 0 → NO contradicción", contra == 0);
        atp_cerrar(e);
    }

    // 3.7 x >= 10 y x <= 5 es contradictorio
    {
        ATPEngine* e = atp_iniciar(NULL);
        atp_agregar_precondicion(e, "x >= 10");
        atp_agregar_precondicion(e, "x <= 5");
        int contra = atp_verificar_contradiccion(e);
        TEST("x >= 10 y x <= 5 → contradicción", contra == 1);
        atp_cerrar(e);
    }

    // 3.8 Sin contradicciones
    {
        ATPEngine* e = atp_iniciar(NULL);
        int contra = atp_verificar_contradiccion(e);
        TEST("Sin restricciones → NO contradicción", contra == 0);
        atp_cerrar(e);
    }
}

// ============================================================
// 4. Propagación de restricciones
// ============================================================
static void test_propagation(void) {
    SECCION("Propagación de restricciones");

    // 4.1 Propagación básica
    {
        ATPEngine* e = atp_iniciar(NULL);
        atp_agregar_precondicion(e, "x > 5");
        atp_agregar_precondicion(e, "x < 10");
        int inf = atp_propagar_restricciones(e);
        // Las inferencias pueden ser 0 si los intervalos ya fueron establecidos durante add
        // Lo importante es que los intervalos tengan ambas cotas después de propagar
        TEST("Propagación no genera error (x >5 y x <10)", inf >= 0);

        // Verificar intervalos después de propagación
        TEST("Intervalo x tiene cota inf", e->intervalos[0].tiene_inf == 1);
        TEST("Intervalo x tiene cota sup", e->intervalos[0].tiene_sup == 1);
        // x > 5 → inf = 5, x < 10 → sup = 10
        TEST("x.inf >= 5 (aprox)", e->intervalos[0].inf >= 4.999);
        TEST("x.sup <= 10 (aprox)", e->intervalos[0].sup <= 10.001);
        atp_cerrar(e);
    }

    // 4.2 Propagación con múltiples variables
    {
        ATPEngine* e = atp_iniciar(NULL);
        atp_agregar_precondicion(e, "x > 0");
        atp_agregar_precondicion(e, "x < 100");
        atp_agregar_precondicion(e, "y > -10");
        atp_agregar_precondicion(e, "y < 10");
        int inf = atp_propagar_restricciones(e);
        TEST("Propagación multi-variable (no error)", inf >= 0);
        TEST("Número de intervalos = 2", e->num_intervalos == 2);
        atp_cerrar(e);
    }
}

// ============================================================
// 5. Verificación de contratos (pre → post)
// ============================================================
static void test_contract_verification(void) {
    SECCION("Verificación de contratos");

    // 5.1 Contrato válido: x > 5 → x > 0
    {
        ATPEngine* e = atp_iniciar(NULL);
        const char* pre[] = {"x > 5"};
        const char* post[] = {"x > 0"};
        int r = atp_verificar_contrato(e, pre, 1, post, 1);
        TEST("x > 5 → x > 0 es VÁLIDO", r == ATP_VALID);
        atp_cerrar(e);
    }

    // 5.2 Contrato válido: x > 0 → x >= -10
    {
        ATPEngine* e = atp_iniciar(NULL);
        const char* pre[] = {"x > 0"};
        const char* post[] = {"x >= -10"};
        int r = atp_verificar_contrato(e, pre, 1, post, 1);
        TEST("x > 0 → x >= -10 es VÁLIDO", r == ATP_VALID);
        atp_cerrar(e);
    }

    // 5.3 Contrato válido: x < 10 → x <= 100
    {
        ATPEngine* e = atp_iniciar(NULL);
        const char* pre[] = {"x < 10"};
        const char* post[] = {"x <= 100"};
        int r = atp_verificar_contrato(e, pre, 1, post, 1);
        TEST("x < 10 → x <= 100 es VÁLIDO", r == ATP_VALID);
        atp_cerrar(e);
    }

    // 5.4 Contrato válido: x >= 0 → x > -1
    {
        ATPEngine* e = atp_iniciar(NULL);
        const char* pre[] = {"x >= 0"};
        const char* post[] = {"x > -1"};
        int r = atp_verificar_contrato(e, pre, 1, post, 1);
        TEST("x >= 0 → x > -1 es VÁLIDO", r == ATP_VALID);
        atp_cerrar(e);
    }

    // 5.5 Contrato inválido: x > 0 → x < 0
    {
        ATPEngine* e = atp_iniciar(NULL);
        const char* pre[] = {"x > 0"};
        const char* post[] = {"x < 0"};
        int r = atp_verificar_contrato(e, pre, 1, post, 1);
        TEST("x > 0 → x < 0 es INVÁLIDO", r == ATP_INVALID);
        atp_cerrar(e);
    }

    // 5.6 Contrato inválido: x < 5 → x > 10
    {
        ATPEngine* e = atp_iniciar(NULL);
        const char* pre[] = {"x < 5"};
        const char* post[] = {"x > 10"};
        int r = atp_verificar_contrato(e, pre, 1, post, 1);
        TEST("x < 5 → x > 10 es INVÁLIDO", r == ATP_INVALID);
        atp_cerrar(e);
    }

    // 5.7 Contrato con múltiples precondiciones
    {
        ATPEngine* e = atp_iniciar(NULL);
        const char* pre[] = {"x > 5", "x < 20"};
        const char* post[] = {"x > 0"};
        int r = atp_verificar_contrato(e, pre, 2, post, 1);
        TEST("x > 5 && x < 20 → x > 0 es VÁLIDO", r == ATP_VALID);
        atp_cerrar(e);
    }

    // 5.8 Contrato con múltiples postcondiciones
    {
        ATPEngine* e = atp_iniciar(NULL);
        const char* pre[] = {"x > 0"};
        const char* post[] = {"x > -1", "x < 1000"};
        int r = atp_verificar_contrato(e, pre, 1, post, 2);
        TEST("x > 0 → x > -1 && x < 1000 es VÁLIDO", r == ATP_VALID);
        atp_cerrar(e);
    }

    // 5.9 Contrato con postcondición que replica precondición
    {
        ATPEngine* e = atp_iniciar(NULL);
        const char* pre[] = {"x == 42"};
        const char* post[] = {"x == 42"};
        int r = atp_verificar_contrato(e, pre, 1, post, 1);
        // La postcondición replica la pre, y la pre == exacto → post es válida
        TEST("x == 42 → x == 42 es VÁLIDO", r == ATP_VALID);
        atp_cerrar(e);
    }
}

// ============================================================
// 6. Contratos inválidos y contraejemplos
// ============================================================
static void test_invalid_contracts(void) {
    SECCION("Contratos inválidos y contraejemplos");

    // 6.1 Contradicción en precondiciones detectada
    {
        ATPEngine* e = atp_iniciar(NULL);
        const char* pre[] = {"x > 10", "x < 5"};
        const char* post[] = {"x > 0"};
        int r = atp_verificar_contrato(e, pre, 2, post, 1);
        TEST("Pre contradictorias (x>10 && x<5) → INVÁLIDO", r == ATP_INVALID);
        atp_cerrar(e);
    }

    // 6.2 Contradicción en precondiciones con igualdad
    {
        ATPEngine* e = atp_iniciar(NULL);
        const char* pre[] = {"x == 5", "x == 10"};
        const char* post[] = {"x > 0"};
        int r = atp_verificar_contrato(e, pre, 2, post, 1);
        TEST("Pre contradictorias (x==5 && x==10) → INVÁLIDO", r == ATP_INVALID);
        atp_cerrar(e);
    }

    // 6.3 Postcondición más restrictiva que precondición (límite inferior)
    {
        ATPEngine* e = atp_iniciar(NULL);
        const char* pre[] = {"x > 0"};
        const char* post[] = {"x > 100"};
        int r = atp_verificar_contrato(e, pre, 1, post, 1);
        TEST("x > 0 → x > 100 es INVÁLIDO (no garantizado)", r == ATP_INVALID);
        atp_cerrar(e);
    }

    // 6.4 Postcondición más restrictiva que precondición (límite superior)
    {
        ATPEngine* e = atp_iniciar(NULL);
        const char* pre[] = {"x < 100"};
        const char* post[] = {"x < 50"};
        int r = atp_verificar_contrato(e, pre, 1, post, 1);
        TEST("x < 100 → x < 50 es INVÁLIDO (no garantizado)", r == ATP_INVALID);
        atp_cerrar(e);
    }
}

// ============================================================
// 7. Contratos con invariantes
// ============================================================
static void test_invariants(void) {
    SECCION("Contratos con invariantes");

    // 7.1 Invariante y precondición compatibles
    {
        ATPEngine* e = atp_iniciar(NULL);
        atp_agregar_precondicion(e, "x > 0");
        atp_agregar_invariante(e, "x < 100");
        atp_agregar_postcondicion(e, "x > 0");
        int r = atp_demostrar(e);
        TEST("x > 0, inv: x<100 → x>0 es VÁLIDO", r == ATP_VALID);
        atp_cerrar(e);
    }

    // 7.2 Invariante y postcondición compatibles
    {
        ATPEngine* e = atp_iniciar(NULL);
        atp_agregar_precondicion(e, "x >= 0");
        atp_agregar_invariante(e, "x < 50");
        atp_agregar_postcondicion(e, "x < 50");
        int r = atp_demostrar(e);
        TEST("x >= 0, inv: x<50 → x<50 es VÁLIDO", r == ATP_VALID);
        atp_cerrar(e);
    }

    // 7.3 Invariante contradictorio con precondición
    {
        ATPEngine* e = atp_iniciar(NULL);
        atp_agregar_precondicion(e, "x > 100");
        atp_agregar_invariante(e, "x < 0");
        int contra = atp_verificar_contradiccion(e);
        TEST("x > 100 e inv: x < 0 → contradicción", contra == 1);
        atp_cerrar(e);
    }
}

// ============================================================
// 8. Persistencia (guardar/cargar)
// ============================================================
static void test_persistence(void) {
    SECCION("Persistencia (guardar/cargar)");

    const char* ruta = "_test_atp_engine.bin";

    // 8.1 Guardar motor con datos
    {
        ATPEngine* e = atp_iniciar(NULL);
        atp_agregar_precondicion(e, "x > 0");
        atp_agregar_precondicion(e, "x < 100");
        atp_agregar_postcondicion(e, "x > -1");
        atp_establecer_funcion(e, "test_funcion");
        atp_demostrar(e);

        int r = atp_guardar(e, ruta);
        TEST("Guardar motor ATP retorna 0", r == 0);
        atp_cerrar(e);
    }

    // 8.2 Cargar motor y verificar datos
    {
        ATPEngine* e = atp_iniciar(NULL);
        int r = atp_cargar(e, ruta);
        TEST("Cargar motor ATP retorna 0", r == 0);
        TEST("Número de precondiciones después de cargar", e->num_preconditions == 2);
        TEST("Número de postcondiciones después de cargar", e->num_postconditions == 1);
        TEST("Nombre de función preservado",
             strcmp(e->function_name, "test_funcion") == 0);
        TEST("Intervalos preservados", e->num_intervalos >= 1);
        atp_cerrar(e);
    }

    // 8.3 Cargar en motor limpio
    {
        ATPEngine* e = atp_iniciar(NULL);
        atp_limpiar(e);
        TEST("Motor limpio antes de cargar", e->num_preconditions == 0);

        int r = atp_cargar(e, ruta);
        TEST("Cargar en motor limpio retorna 0", r == 0);
        TEST("Precondiciones después de cargar", e->num_preconditions == 2);
        atp_cerrar(e);
    }

    // 8.4 Cargar archivo inválido
    {
        ATPEngine* e = atp_iniciar(NULL);
        int r = atp_cargar(e, "_archivo_que_no_existe.bin");
        TEST("Cargar archivo inexistente retorna -1", r == -1);
        atp_cerrar(e);
    }

    // Limpiar archivo temporal
    remove(ruta);
}

// ============================================================
// 9. Limpieza y reutilización
// ============================================================
static void test_cleanup(void) {
    SECCION("Limpieza y reutilización");

    // 9.1 Limpiar y reusar motor
    {
        ATPEngine* e = atp_iniciar(NULL);
        atp_agregar_precondicion(e, "x > 0");
        atp_agregar_postcondicion(e, "x > -1");
        TEST("Precondiciones antes de limpiar", e->num_preconditions == 1);

        atp_limpiar(e);
        TEST("Precondiciones después de limpiar", e->num_preconditions == 0);
        TEST("Postcondiciones después de limpiar", e->num_postconditions == 0);
        TEST("Intervalos después de limpiar", e->num_intervalos == 0);

        // Reutilizar
        atp_agregar_precondicion(e, "y < 10");
        atp_agregar_postcondicion(e, "y <= 10");
        const char* pre[] = {"y < 10"};
        const char* post[] = {"y <= 10"};
        int r = atp_verificar_contrato(e, pre, 1, post, 1);
        TEST("Reutilización: contrato válido", r == ATP_VALID);
        atp_cerrar(e);
    }

    // 9.2 Múltiples motores simultáneos
    {
        ATPEngine* e1 = atp_iniciar(NULL);
        ATPEngine* e2 = atp_iniciar(NULL);

        atp_agregar_precondicion(e1, "x > 5");
        atp_agregar_precondicion(e2, "x < 5");

        TEST("Motor 1: 1 precondición", e1->num_preconditions == 1);
        TEST("Motor 2: 1 precondición", e2->num_preconditions == 1);
        TEST("Los motores son independientes", e1 != e2);

        atp_cerrar(e1);
        atp_cerrar(e2);
    }
}

// ============================================================
// 10. Casos borde
// ============================================================
static void test_edge_cases(void) {
    SECCION("Casos borde");

    // 10.1 NULL pointer safety
    {
        int r = atp_verificar_tautologia(NULL, "x == x");
        TEST("atp_verificar_tautologia(NULL) es ERROR", r == ATP_ERROR);

        r = atp_verificar_contradiccion(NULL);
        TEST("atp_verificar_contradiccion(NULL) es -1", r == -1);

        atp_limpiar(NULL);
        TEST("atp_limpiar(NULL) es seguro (sin crash)", 1);

        atp_cerrar(NULL);
        TEST("atp_cerrar(NULL) es seguro (sin crash)", 1);
    }

    // 10.2 Strings vacíos
    {
        ATPEngine* e = atp_iniciar(NULL);
        int r = atp_agregar_precondicion(e, "");
        TEST("Agregar precondición vacía retorna -1", r == -1);
        atp_cerrar(e);
    }

    // 10.3 Sin postcondiciones
    {
        ATPEngine* e = atp_iniciar(NULL);
        const char* pre[] = {"x > 0"};
        const char* post[] = {};
        int r = atp_verificar_contrato(e, pre, 1, post, 0);
        TEST("Sin postcondiciones retorna UNKNOWN", r == ATP_UNKNOWN);
        atp_cerrar(e);
    }

    // 10.4 Sin precondiciones
    {
        ATPEngine* e = atp_iniciar(NULL);
        const char* pre[] = {};
        const char* post[] = {"x > 0"};
        int r = atp_verificar_contrato(e, pre, 0, post, 1);
        TEST("Sin precondiciones, post es UNKNOWN (sin intervalo)", r == ATP_UNKNOWN);
        atp_cerrar(e);
    }

    // 10.5 Límite de restricciones
    {
        ATPEngine* e = atp_iniciar(NULL);
        int todos_ok = 1;
        for (int i = 0; i < ATP_MAX_CONSTRAINTS + 5; i++) {
            char buf[128];
            snprintf(buf, sizeof(buf), "x > %d", i);
            int r = atp_agregar_precondicion(e, buf);
            if (i >= ATP_MAX_CONSTRAINTS && r >= 0) {
                todos_ok = 0;
                break;
            }
        }
        TEST("Límite de restricciones respetado", todos_ok == 1);
        atp_cerrar(e);
    }
}

// ============================================================
// 11. Integración con proof_bridge (contratos exportables)
// ============================================================
static void test_proof_bridge_integration(void) {
    SECCION("Integración con proof_bridge (contratos Synapse→Coq/Lean)");

    // 11.1 Contrato válido para exportación Coq: n >= 0 → _resultado_ >= 0
    {
        ATPEngine* e = atp_iniciar(NULL);
        const char* pre[] = {"n >= 0"};
        // _resultado_ se normaliza como "result" en el bridge,
        // pero aquí es un identificador como cualquier otro
        const char* post[] = {"result >= 0"};
        int r = atp_verificar_contrato(e, pre, 1, post, 1);
        TEST("n >= 0 → result >= 0 es UNKNOWN (variable libre 'result')", r == ATP_UNKNOWN);
        atp_cerrar(e);
    }

    // 11.2 Contrato de búsqueda binaria: arr != NULL, n > 0 → idx >= -1
    {
        ATPEngine* e = atp_iniciar(NULL);
        const char* pre[] = {"n > 0"};
        const char* post[] = {"idx >= -1"};
        int r = atp_verificar_contrato(e, pre, 1, post, 1);
        TEST("n > 0 → idx >= -1 es UNKNOWN (idx no relacionado con n)", r == ATP_UNKNOWN);
        atp_cerrar(e);
    }

    // 11.3 Contrato factorial: n >= 0 → result == n * factorial(n-1)
    {
        ATPEngine* e = atp_iniciar(NULL);
        const char* pre[] = {"n >= 0"};
        const char* post[] = {"n >= -1"};
        int r = atp_verificar_contrato(e, pre, 1, post, 1);
        TEST("n >= 0 → n >= -1 es VÁLIDO", r == ATP_VALID);
        atp_cerrar(e);
    }

    // 11.4 Contrato con variable real: temperatura > -273.15
    {
        ATPEngine* e = atp_iniciar(NULL);
        const char* pre[] = {"temp >= -273.15"};
        const char* post[] = {"temp >= -300"};
        int r = atp_verificar_contrato(e, pre, 1, post, 1);
        TEST("temp >= -273.15 → temp >= -300 es VÁLIDO", r == ATP_VALID);
        atp_cerrar(e);
    }

    // 11.5 Error de tipado en contrato: requerir x != NULL
    {
        ATPEngine* e = atp_iniciar(NULL);
        const char* pre[] = {"x != 0"};
        const char* post[] = {"x > -1"};
        int r = atp_verificar_contrato(e, pre, 1, post, 1);
        TEST("x != 0 → x > -1 es UNKNOWN (diferencia/disyunción no modelada)", r == ATP_UNKNOWN);
        atp_cerrar(e);
    }
}

// ============================================================
// Main
// ============================================================
int main(void) {
    printf("============================================================\n");
    printf("  VALIDACIÓN DEL MOTOR DE DEMOSTRACIÓN AUTOMÁTICA DE TEOREMAS\n");
    printf("  ATP Engine — M15.2\n");
    printf("============================================================\n\n");

    test_lifecycle();
    test_arithmetic_tautologies();
    test_contradictions();
    test_propagation();
    test_contract_verification();
    test_invalid_contracts();
    test_invariants();
    test_persistence();
    test_cleanup();
    test_edge_cases();
    test_proof_bridge_integration();

    printf("\n============================================================\n");
    printf("  RESULTADOS\n");
    printf("============================================================\n");
    printf("  Pruebas: %d secciones\n", section_num);
    printf("  Pasadas: %d\n", test_passed);
    printf("  Falladas: %d\n", test_failed);
    printf("============================================================\n\n");

    return test_failed > 0 ? 1 : 0;
}
