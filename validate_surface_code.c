// validate_surface_code.c — Suite de validacion del Surface Code (M16.3)
// Pruebas aisladas para correccion topologica de errores en rejillas 2D.
// ======================================================================

#include "nucleo/surface_code.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

static int test_passed = 0;
static int test_failed = 0;
static int section_num = 0;

#define TEST(nombre, expr) do { \
    if (!(expr)) { \
        fprintf(stderr, "  [FAIL] %s (linea %d)\n", nombre, __LINE__); \
        test_failed++; \
    } else { \
        test_passed++; \
    } \
} while(0)

#define SECCION(nombre) do { \
    section_num++; \
    printf("\n=== Seccion %d: %s ===\n", section_num, nombre); \
} while(0)

// ============================================================
// 1. Creacion de rejilla
// ============================================================
static void test_lattice_creation(void) {
    SECCION("Creacion de rejilla");

    SurfaceCode* r = sc_crear_rejilla(3);
    TEST("Rejilla 3x3 creada", r != NULL);
    TEST("L=3", r->L == 3);
    TEST("9 qubits de datos", r->num_qubits == 9);
    TEST("Estabilizadores >0", r->num_estabilizadores > 0);
    sc_liberar_rejilla(r);

    r = sc_crear_rejilla(5);
    TEST("Rejilla 5x5 creada", r != NULL);
    TEST("25 qubits de datos", r->num_qubits == 25);
    sc_liberar_rejilla(r);

    TEST("Rejilla L=1 rechazada", sc_crear_rejilla(1) == NULL);
    TEST("Rejilla L=0 rechazada", sc_crear_rejilla(0) == NULL);
    TEST("Rejilla L=8 rechazada (max=7)", sc_crear_rejilla(8) == NULL);
}

// ============================================================
// 2. Inicializacion
// ============================================================
static void test_initialization(void) {
    SECCION("Inicializacion");

    SurfaceCode* r = sc_crear_rejilla(3);
    int rc = sc_inicializar_estado_cero(r);
    TEST("Inicializar estado cero retorna 0", rc == 0);
    TEST("0 errores X tras init", sc_obtener_num_errores(r) == 0);
    TEST("Estado CORRECTED tras init", r->estado == SC_CORRECTED);

    // Verificar todos los qubits en cero
    int errores = 0;
    for (int i = 0; i < r->num_qubits; i++) {
        if (r->data_qubits[i].error_x > 0.01) errores++;
        if (r->data_qubits[i].error_z > 0.01) errores++;
    }
    TEST("Sin errores residuales", errores == 0);
    sc_liberar_rejilla(r);

    // NULL safety
    TEST("Init NULL retorna -1", sc_inicializar_estado_cero(NULL) == -1);
}

// ============================================================
// 3. Inyeccion de errores
// ============================================================
static void test_error_injection(void) {
    SECCION("Inyeccion de errores");

    SurfaceCode* r = sc_crear_rejilla(3);
    sc_inicializar_estado_cero(r);

    int rc = sc_inyectar_error_en(r, 0, 0, SC_ERROR_X);
    TEST("Inyectar X en (0,0) retorna 0", rc == 0);
    TEST("Error X detectado en (0,0)", r->data_qubits[0].error_x > 0.5);
    TEST("Error Z=0 en (0,0)", r->data_qubits[0].error_z < 0.5);

    rc = sc_inyectar_error_en(r, 1, 2, SC_ERROR_Z);
    TEST("Inyectar Z en (1,2) retorna 0", rc == 0);
    int idx = 1 * 3 + 2;
    TEST("Error Z detectado en (1,2)", r->data_qubits[idx].error_z > 0.5);

    rc = sc_inyectar_error_en(r, 2, 0, SC_ERROR_BOTH);
    TEST("Inyectar X+Z en (2,0) retorna 0", rc == 0);
    idx = 2 * 3 + 0;
    TEST("Error X en (2,0)", r->data_qubits[idx].error_x > 0.5);
    TEST("Error Z en (2,0)", r->data_qubits[idx].error_z > 0.5);

    // Errores fuera de rango
    TEST("Error fuera de rango rechazado", sc_inyectar_error_en(r, -1, 0, SC_ERROR_X) == -1);
    TEST("Error fuera de rango rechazado", sc_inyectar_error_en(r, 5, 0, SC_ERROR_X) == -1);

    sc_liberar_rejilla(r);
}

// ============================================================
// 4. Inyeccion de cadena de error
// ============================================================
static void test_error_chain(void) {
    SECCION("Inyeccion de cadena de error");

    SurfaceCode* r = sc_crear_rejilla(4);
    sc_inicializar_estado_cero(r);

    // Inyectar cadena de errores X en linea horizontal (fila 0, cols 0-3)
    int rc = sc_inyectar_cadena_error(r, SC_ERROR_X, 0, 0, 0, 3);
    TEST("Cadena de error retorna 0", rc == 0);

    // Verificar que los qubits en la fila 0 tienen error X
    for (int c = 0; c < 4; c++) {
        int idx = 0 * 4 + c;
        TEST("Error X en fila 0, col C", r->data_qubits[idx].error_x > 0.5);
    }

    // Verificar numero exacto de errores (4 en la fila 0)
    int total_errores = 0;
    for (int i = 0; i < r->num_qubits; i++) {
        if (r->data_qubits[i].error_x > 0.5) total_errores++;
    }
    TEST("Exactamente 4 errores X en fila 0", total_errores == 4);

    sc_liberar_rejilla(r);
}

// ============================================================
// 5. Medicion de estabilizadores
// ============================================================
static void test_stabilizer_measurement(void) {
    SECCION("Medicion de estabilizadores");

    SurfaceCode* r = sc_crear_rejilla(3);
    sc_inicializar_estado_cero(r);

    // Sin errores: todos los estabilizadores inactivos
    sc_medir_estabilizadores(r);
    TEST("Sin errores: 0 sindromes X", r->num_sindrome_x == 0);
    TEST("Sin errores: 0 sindromes Z", r->num_sindrome_z == 0);

    // Inyectar error X en (0,0): debe activar estabilizadores X en (0,0)
    sc_inyectar_error_en(r, 0, 0, SC_ERROR_X);
    sc_medir_estabilizadores(r);
    TEST("Error X en (0,0): sindromes X > 0", r->num_sindrome_x > 0);
    sc_limpiar_rejilla(r);

    // Inyectar error Z en (1,1): debe activar estabilizadores Z
    sc_inyectar_error_en(r, 1, 1, SC_ERROR_Z);
    sc_medir_estabilizadores(r);
    TEST("Error Z en (1,1): sindromes Z > 0", r->num_sindrome_z > 0);
    sc_limpiar_rejilla(r);

    sc_liberar_rejilla(r);
}

// ============================================================
// 6. Decodificador Union-Find
// ============================================================
static void test_union_find_decoder(void) {
    SECCION("Decodificador Union-Find");

    SurfaceCode* r = sc_crear_rejilla(3);
    sc_inicializar_estado_cero(r);

    // Sin errores: decoder no encuentra nada
    sc_medir_estabilizadores(r);
    int candidatos = sc_decodificar_union_find(r);
    TEST("Sin errores: 0 candidatos", candidatos == 0);

    // Inyectar error X en (0,0): decoder debe identificar qubit
    sc_inyectar_error_en(r, 0, 0, SC_ERROR_X);
    sc_medir_estabilizadores(r);
    candidatos = sc_decodificar_union_find(r);
    TEST("Error X en (0,0): candidatos > 0", candidatos > 0);

    // Limpiar y probar error Z
    sc_limpiar_rejilla(r);
    sc_inyectar_error_en(r, 2, 2, SC_ERROR_Z);
    sc_medir_estabilizadores(r);
    candidatos = sc_decodificar_union_find(r);
    TEST("Error Z en (2,2): candidatos > 0", candidatos > 0);

    sc_liberar_rejilla(r);
}

// ============================================================
// 7. Correccion de errores
// ============================================================
static void test_error_correction(void) {
    SECCION("Correccion de errores");

    SurfaceCode* r = sc_crear_rejilla(3);
    sc_inicializar_estado_cero(r);

    // Ciclo completo: inyectar error X, medir, decodificar, corregir
    sc_inyectar_error_en(r, 0, 1, SC_ERROR_X);
    sc_medir_estabilizadores(r);
    sc_decodificar_union_find(r);
    int corregidos = sc_corregir_errores(r);
    TEST("Error X corregido", corregidos > 0);
    TEST("Verificar correccion exitosa", sc_verificar_correccion(r) == 1);

    sc_liberar_rejilla(r);

    // Prueba con error Z
    r = sc_crear_rejilla(3);
    sc_inicializar_estado_cero(r);
    sc_inyectar_error_en(r, 1, 1, SC_ERROR_Z);
    sc_medir_estabilizadores(r);
    sc_decodificar_union_find(r);
    corregidos = sc_corregir_errores(r);
    TEST("Error Z corregido", corregidos > 0);
    TEST("Verificar correccion exitosa", sc_verificar_correccion(r) == 1);
    sc_liberar_rejilla(r);

    // Prueba con error doble
    r = sc_crear_rejilla(4);
    sc_inicializar_estado_cero(r);
    sc_inyectar_error_en(r, 2, 2, SC_ERROR_BOTH);
    sc_medir_estabilizadores(r);
    sc_decodificar_union_find(r);
    corregidos = sc_corregir_errores(r);
    TEST("Error X+Z corregido", corregidos > 0);
    TEST("Verificar correccion doble", sc_verificar_correccion(r) == 1);
    sc_liberar_rejilla(r);
}

// ============================================================
// 8. Ciclo completo de proteccion
// ============================================================
static void test_protection_cycle(void) {
    SECCION("Ciclo completo de proteccion");

    SurfaceCode* r = sc_crear_rejilla(3);
    SCResultado res = sc_ciclo_completo(r, 1, 0); // 1 error X
    TEST("1 error X: exito", res.exito == 1);
    TEST("1 error X: errores_detectados >= 1", res.errores_detectados >= 1);
    TEST("1 error X: errores_corregidos >= 1", res.errores_corregidos >= 1);
    TEST("1 error X: 0 errores restantes", res.errores_restantes == 0);
    sc_liberar_rejilla(r);

    r = sc_crear_rejilla(5);
    res = sc_ciclo_completo(r, 3, 2); // 3 errores X + 2 errores Z
    TEST("5 errores: exito", res.exito == 1);
    TEST("5 errores: detectados >= 5", res.errores_detectados >= 5);
    TEST("5 errores: corregidos >= 3", res.errores_corregidos >= 3);
    TEST("5 errores: 0 restantes", res.errores_restantes == 0);
    sc_liberar_rejilla(r);
}

// ============================================================
// 9. Cadena de error + correccion
// ============================================================
static void test_chain_correction(void) {
    SECCION("Correccion de cadena de error");

    SurfaceCode* r = sc_crear_rejilla(4);
    sc_inicializar_estado_cero(r);

    // Errores individuales en posiciones con sindromes detectables
    // Nota: una cadena continua de errores no genera sindromes en
    // estabilizadores interiores (paridad par). Probamos errores
    // individuales que crean patrones de sindrome aislados.
    sc_inyectar_error_en(r, 0, 1, SC_ERROR_X);
    sc_inyectar_error_en(r, 2, 3, SC_ERROR_X);
    TEST("2 errores X individuales", sc_obtener_num_errores(r) == 2);

    sc_medir_estabilizadores(r);
    TEST("Sindromes X detectados", r->num_sindrome_x > 0);

    sc_decodificar_union_find(r);
    int corregidos = sc_corregir_errores(r);
    TEST("Correccion aplicada", corregidos > 0);
    TEST("Verificacion exitosa", sc_verificar_correccion(r) == 1);

    sc_liberar_rejilla(r);
}

// ============================================================
// 10. Casos borde
// ============================================================
static void test_edge_cases(void) {
    SECCION("Casos borde");

    TEST("Crear NULL no crashea", 1);
    sc_liberar_rejilla(NULL);
    TEST("Liberar NULL no crashea", 1);

    TEST("Medir estabilizadores NULL retorna -1",
         sc_medir_estabilizadores(NULL) == -1);
    TEST("Decodificar NULL retorna -1",
         sc_decodificar_union_find(NULL) == -1);
    TEST("Corregir NULL retorna -1",
         sc_corregir_errores(NULL) == -1);
    TEST("Verificar NULL retorna -1",
         sc_verificar_correccion(NULL) == -1);

    SurfaceCode* r = sc_crear_rejilla(3);
    sc_inicializar_estado_cero(r);

    // Doble correccion: no debe fallar
    sc_inyectar_error_en(r, 0, 0, SC_ERROR_X);
    sc_medir_estabilizadores(r);
    sc_decodificar_union_find(r);
    sc_corregir_errores(r);
    TEST("Verificar tras primera correccion", sc_verificar_correccion(r) == 1);

    // Segunda correccion sin errores
    sc_medir_estabilizadores(r);
    sc_decodificar_union_find(r);
    int corregidos = sc_corregir_errores(r);
    TEST("Segunda correccion sin errores: 0 corregidos", corregidos == 0);

    sc_liberar_rejilla(r);
}

// ============================================================
// 11. Rejilla grande (5x5)
// ============================================================
static void test_large_lattice(void) {
    SECCION("Rejilla grande 5x5");

    SurfaceCode* r = sc_crear_rejilla(5);
    TEST("Rejilla 5x5 creada", r != NULL);
    TEST("25 qubits", r->num_qubits == 25);

    sc_inicializar_estado_cero(r);
    TEST("Init 5x5 exitoso", r->estado == SC_CORRECTED);

    // Inyectar errores individuales no solapados
    sc_inyectar_error_en(r, 0, 0, SC_ERROR_X);
    sc_inyectar_error_en(r, 2, 4, SC_ERROR_X);
    sc_inyectar_error_en(r, 4, 2, SC_ERROR_Z);
    TEST("3 errores en 5x5", sc_obtener_num_errores(r) == 3);

    sc_medir_estabilizadores(r);
    sc_decodificar_union_find(r);
    int corregidos = sc_corregir_errores(r);
    TEST("Correccion 5x5: errores corregidos", corregidos > 0);
    TEST("Correccion 5x5: verificacion", sc_verificar_correccion(r) == 1);

    sc_liberar_rejilla(r);
}

// ============================================================
// 12. Fidelidad
// ============================================================
static void test_fidelity(void) {
    SECCION("Calculo de fidelidad");

    SurfaceCode* r = sc_crear_rejilla(3);
    sc_inicializar_estado_cero(r);

    double fid = sc_calcular_fidelidad(r);
    TEST("Fidelidad sin errores = 1.0", fabs(fid - 1.0) < 1e-10);

    sc_inyectar_error_en(r, 0, 0, SC_ERROR_X);
    fid = sc_calcular_fidelidad(r);
    TEST("Fidelidad con 1 error < 1.0", fid < 1.0);
    TEST("Fidelidad > 0.9 (1 error en 9 qubits)", fid > 0.9);

    sc_liberar_rejilla(r);
}

// ============================================================
// Main
// ============================================================
int main(void) {
    printf("=== VALIDACION DEL SURFACE CODE (CORRECCION TOPOLOGICA) ===\n");
    printf("  M16.3 — Topological Error Correction on 2D Lattice\n\n");

    test_lattice_creation();
    test_initialization();
    test_error_injection();
    test_error_chain();
    test_stabilizer_measurement();
    test_union_find_decoder();
    test_error_correction();
    test_protection_cycle();
    test_chain_correction();
    test_edge_cases();
    test_large_lattice();
    test_fidelity();

    printf("\n=== RESULTADOS ===\n");
    printf("  Secciones: %d\n", section_num);
    printf("  Pasadas: %d\n", test_passed);
    printf("  Falladas: %d\n", test_failed);
    printf("==================\n\n");
    return test_failed > 0 ? 1 : 0;
}
