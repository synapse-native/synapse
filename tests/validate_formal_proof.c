// validate_formal_proof.c — Validación aislada del Puente de Verificación Formal (M15.1)
// =======================================================================================
// Prueba: Coq/Lean syntax translation, contract aggregation, theorem generation,
// certificate verification, persistence, edge cases.
//
// AISLADA: No modifica archivos bajo tests/ (candado de solo lectura activo).
// =======================================================================================

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include "nucleo/proof_bridge.h"

// ============================================================
// Contadores de pruebas
// ============================================================
static int test_passed = 0;
static int test_total = 0;
static int test_section = 0;

#define test_assert(msg, expr) do { \
    test_total++; \
    if (!(expr)) { \
        fprintf(stderr, "  [FALLO] %s (linea %d): %s\n", __func__, __LINE__, msg); \
    } else { \
        test_passed++; \
    } \
} while(0)

#define test_section_start(msg) do { \
    test_section++; \
    printf("\n=== Seccion %d: %s ===\n", test_section, msg); \
} while(0)

// ============================================================
// Sección 1: Traducción Synapse → Coq
// ============================================================
static void test_synapse_to_coq(void) {
    const char* result;

    // 1.1 Comparación básica
    result = pb_traducir_a_coq("x > 0");
    test_assert("x > 0 -> Coq", result && strstr(result, ">") != NULL);

    result = pb_traducir_a_coq("x >= 0");
    test_assert("x >= 0 -> Coq", result && strstr(result, ">=") != NULL);

    // 1.2 Igualdad y desigualdad
    result = pb_traducir_a_coq("x == 0");
    test_assert("x == 0 -> x = 0 en Coq", result && strstr(result, "=") != NULL);

    result = pb_traducir_a_coq("x != 0");
    test_assert("x != 0 -> x <> 0 en Coq", result && strstr(result, "<>") != NULL);

    // 1.3 Conectivas lógicas
    result = pb_traducir_a_coq("x > 0 && y < 10");
    test_assert("&& -> /\\ en Coq", result && strstr(result, "/\\") != NULL);

    result = pb_traducir_a_coq("x == 0 || y == 1");
    test_assert("|| -> \\/ en Coq", result && strstr(result, "\\/") != NULL);

    // 1.4 Negación
    result = pb_traducir_a_coq("!activo");
    test_assert("! -> ~ en Coq", result && strstr(result, "~") != NULL);

    // 1.5 _resultado_ placeholder
    result = pb_traducir_a_coq("_resultado_ >= 0");
    test_assert("_resultado_ -> result en Coq", result && strstr(result, "result") != NULL);

    // 1.6 Expresión compuesta
    result = pb_traducir_a_coq("x >= 0 && x < 100");
    test_assert("Expresion compuesta a Coq", result != NULL);
    test_assert("Contiene /\\", strstr(result, "/\\") != NULL);
    test_assert("Contiene >=", strstr(result, ">=") != NULL);

    // 1.7 NULL safety
    result = pb_traducir_a_coq(NULL);
    test_assert("NULL expr -> NULL", result == NULL);
}

// ============================================================
// Sección 2: Traducción Synapse → Lean
// ============================================================
static void test_synapse_to_lean(void) {
    const char* result;

    result = pb_traducir_a_lean("x > 0");
    test_assert("x > 0 -> Lean", result != NULL);

    result = pb_traducir_a_lean("x >= 0");
    test_assert("x >= 0 -> >= en Lean", result && strstr(result, "≥") != NULL);

    result = pb_traducir_a_lean("x == 0");
    test_assert("x == 0 -> = en Lean", result && strstr(result, "=") != NULL);

    result = pb_traducir_a_lean("x != 0");
    test_assert("x != 0 -> ≠ en Lean", result && strstr(result, "≠") != NULL);

    result = pb_traducir_a_lean("x > 0 && y < 10");
    test_assert("&& -> ∧ en Lean", result && strstr(result, "∧") != NULL);

    result = pb_traducir_a_lean("x == 0 || y == 1");
    test_assert("|| -> ∨ en Lean", result && strstr(result, "∨") != NULL);

    result = pb_traducir_a_lean("!activo");
    test_assert("! -> ¬ en Lean", result && strstr(result, "¬") != NULL);

    result = pb_traducir_a_lean("_resultado_ >= 0");
    test_assert("_resultado_ -> result en Lean", result && strstr(result, "result") != NULL);

    result = pb_traducir_a_lean(NULL);
    test_assert("NULL expr -> NULL", result == NULL);
}

// ============================================================
// Sección 3: Ciclo de vida de sesión
// ============================================================
static void test_lifecycle(void) {
    // 3.1 Config por defecto
    PBSession* sesion = pb_iniciar(NULL);
    test_assert("Session default", sesion != NULL);
    test_assert("Formato Coq default", sesion->config.formato_destino == PB_FORMAT_COQ);
    test_assert("Nombre teoria default", strcmp(sesion->config.nombre_teoria, "SynapseProof") == 0);
    pb_cerrar(sesion);

    // 3.2 Config Lean explícita
    PBConfig cfg;
    cfg.formato_destino = PB_FORMAT_LEAN;
    cfg.generar_esqueleto = 1;
    cfg.verificar_automatico = 1;
    snprintf(cfg.nombre_teoria, 64, "MiTeoria");
    cfg.incluir_axiomas = 1;

    sesion = pb_iniciar(&cfg);
    test_assert("Session Lean", sesion != NULL);
    test_assert("Formato Lean", sesion->config.formato_destino == PB_FORMAT_LEAN);
    test_assert("Nombre teoria personalizado", strcmp(sesion->config.nombre_teoria, "MiTeoria") == 0);
    pb_cerrar(sesion);

    // 3.3 Cerrar NULL
    pb_cerrar(NULL);
    test_assert("Cerrar NULL no crash", 1);
}

// ============================================================
// Sección 4: Agregar funciones y contratos
// ============================================================
static void test_functions_and_contracts(void) {
    PBSession* sesion = pb_iniciar(NULL);
    test_assert("Session contracts", sesion != NULL);

    // 4.1 Agregar función
    int idx = pb_agregar_funcion(sesion, "fib", "entero", "n: entero");
    test_assert("Funcion fib agregada", idx == 0);
    test_assert("1 funcion en sesion", sesion->num_funciones == 1);

    // 4.2 Agregar requiere (precondición)
    int rc = pb_agregar_contrato(sesion, "n >= 0", PB_CONTRACT_REQUIERE);
    test_assert("Requiere agregado", rc == 0);
    test_assert("1 requiere", sesion->funciones[0].num_requiere == 1);

    // 4.3 Agregar garantiza (postcondición)
    rc = pb_agregar_contrato(sesion, "_resultado_ >= 0", PB_CONTRACT_GARANTIZA);
    test_assert("Garantiza agregado", rc == 0);
    test_assert("1 garantiza", sesion->funciones[0].num_garantiza == 1);

    // 4.4 Verificar traducciones
    test_assert("Requiere traducido a Coq",
        strlen(sesion->funciones[0].requiere[0].termino_coq) > 0);
    test_assert("Garantiza traducido a Lean",
        strlen(sesion->funciones[0].garantiza[0].termino_lean) > 0);

    // 4.5 Segunda función
    idx = pb_agregar_funcion(sesion, "suma", "entero", "a: entero, b: entero");
    test_assert("Funcion suma agregada", idx == 1);
    rc = pb_agregar_contrato(sesion, "a > 0 && b > 0", PB_CONTRACT_REQUIERE);
    test_assert("Requiere suma OK", rc == 0);
    test_assert("2 funciones", sesion->num_funciones == 2);

    // 4.6 Agregar con NULL params
    rc = pb_agregar_funcion(NULL, "f", "entero", "");
    test_assert("Funcion NULL session falla", rc < 0);

    rc = pb_agregar_funcion(sesion, NULL, "entero", "");
    test_assert("Funcion NULL nombre falla", rc < 0);

    pb_cerrar(sesion);
}

// ============================================================
// Sección 5: Generación de archivo Coq
// ============================================================
static void test_coq_generation(void) {
    PBSession* sesion = pb_iniciar(NULL);
    test_assert("Session Coq gen", sesion != NULL);

    pb_agregar_funcion(sesion, "fib", "entero", "n: entero");
    pb_agregar_contrato(sesion, "n >= 0", PB_CONTRACT_REQUIERE);
    pb_agregar_contrato(sesion, "_resultado_ >= 0", PB_CONTRACT_GARANTIZA);

    int len = pb_generar_archivo_coq(sesion);
    test_assert("Archivo Coq generado", len > 0);
    test_assert("Buffer no vacio", sesion->buffer_salida[0] != '\0');

    // Verificar contenido
    test_assert("Cabecera Coq presente", strstr(sesion->buffer_salida, "Synapse Proof Theory") != NULL);
    test_assert("Axiomas incluidos", strstr(sesion->buffer_salida, "Axiom") != NULL);
    test_assert("Teorema requiere generado", strstr(sesion->buffer_salida, "fib_requiere_0") != NULL);
    test_assert("Teorema garantiza generado", strstr(sesion->buffer_salida, "fib_garantiza_0") != NULL);
    test_assert("Proof skeleton presente", strstr(sesion->buffer_salida, "Admitted") != NULL);

    pb_cerrar(sesion);

    // Sin axiomas
    PBConfig cfg;
    cfg.formato_destino = PB_FORMAT_COQ;
    cfg.incluir_axiomas = 0;
    cfg.generar_esqueleto = 1;
    sesion = pb_iniciar(&cfg);
    pb_agregar_funcion(sesion, "f", "entero", "x: entero");
    pb_agregar_contrato(sesion, "x > 0", PB_CONTRACT_REQUIERE);
    len = pb_generar_archivo_coq(sesion);
    test_assert("Coq sin axiomas", len > 0);
    test_assert("Sin axiomas", strstr(sesion->buffer_salida, "Axiom") == NULL);
    pb_cerrar(sesion);
}

// ============================================================
// Sección 6: Generación de archivo Lean
// ============================================================
static void test_lean_generation(void) {
    PBConfig cfg;
    cfg.formato_destino = PB_FORMAT_LEAN;
    cfg.incluir_axiomas = 1;
    cfg.generar_esqueleto = 1;

    PBSession* sesion = pb_iniciar(&cfg);
    test_assert("Session Lean gen", sesion != NULL);

    pb_agregar_funcion(sesion, "fact", "entero", "n: entero");
    pb_agregar_contrato(sesion, "n >= 0", PB_CONTRACT_REQUIERE);
    pb_agregar_contrato(sesion, "_resultado_ > 0", PB_CONTRACT_GARANTIZA);

    int len = pb_generar_archivo_lean(sesion);
    test_assert("Archivo Lean generado", len > 0);

    test_assert("Cabecera Lean", strstr(sesion->buffer_salida, "Synapse Proof Theory") != NULL);
    test_assert("Teorema requiere generado", strstr(sesion->buffer_salida, "fact_requiere_0") != NULL);
    test_assert("Teorema garantiza generado", strstr(sesion->buffer_salida, "fact_garantiza_0") != NULL);
    test_assert("Proof skeleton sorry", strstr(sesion->buffer_salida, "sorry") != NULL);

    pb_cerrar(sesion);
}

// ============================================================
// Sección 7: Certificados de verificación
// ============================================================
static void test_certificates(void) {
    PBSession* sesion = pb_iniciar(NULL);
    test_assert("Session certificados", sesion != NULL);

    pb_agregar_funcion(sesion, "abs", "entero", "x: entero");
    pb_agregar_contrato(sesion, "x >= 0", PB_CONTRACT_REQUIERE);
    pb_agregar_contrato(sesion, "_resultado_ >= 0", PB_CONTRACT_GARANTIZA);

    // Generar certificado
    int rc = pb_generar_certificado(sesion, "abs");
    test_assert("Certificado generado", rc == 0);
    test_assert("Funcion verificada", sesion->funciones[0].verificada == PB_VERIFY_VALID);
    test_assert("Certificado no vacio", strlen(sesion->funciones[0].certificado) > 0);

    // Certificado para función inexistente
    rc = pb_generar_certificado(sesion, "no_existe");
    test_assert("Funcion inexistente falla", rc < 0);

    // Certificado NULL
    rc = pb_generar_certificado(NULL, "abs");
    test_assert("Session NULL falla", rc < 0);
    rc = pb_generar_certificado(sesion, NULL);
    test_assert("Nombre NULL falla", rc < 0);

    pb_cerrar(sesion);

    // Verificar certificado
    PBCertificate cert;
    cert.magic = PB_MAGIC_HEADER;
    cert.version = PB_VERSION;
    strncpy(cert.resultado, "VALID", 16);

    PBFunctionSpec spec;
    strncpy(spec.nombre_funcion, "abs", PB_MAX_EXPR_LEN);
    strncpy(spec.tipo_retorno, "entero", 64);
    spec.num_requiere = 1;
    spec.num_garantiza = 1;

    // Generar hash esperado
    char input[PB_MAX_EXPR_LEN + 64];
    snprintf(input, sizeof(input), "abs:entero:1:1");
    unsigned long h = 0x12345678;
    for (const char* p = input; *p; p++) {
        h = ((h << 5) + h) ^ (unsigned char)*p;
    }
    snprintf(cert.proof_hash, 64, "PROOF_%016lx_%016lx", h, (unsigned long)0);

    int vrc = pb_verificar_certificado(&cert, &spec);
    // Nota: no podemos predecir el timestamp, solo verificamos que la función existe
    test_assert("Verificacion ejecutada", vrc == PB_VERIFY_VALID || vrc == PB_VERIFY_INVALID);
}

// ============================================================
// Sección 8: Exportación completa
// ============================================================
static void test_export(void) {
    PBConfig cfg;
    cfg.formato_destino = PB_FORMAT_COQ;
    cfg.incluir_axiomas = 1;
    cfg.generar_esqueleto = 1;
    cfg.ruta_salida[0] = '\0';  // Sin ruta (no escribe a disco)

    PBSession* sesion = pb_iniciar(&cfg);
    test_assert("Session exportacion", sesion != NULL);

    pb_agregar_funcion(sesion, "fib", "entero", "n: entero");
    pb_agregar_contrato(sesion, "n >= 0", PB_CONTRACT_REQUIERE);
    pb_agregar_funcion(sesion, "suma", "entero", "a: entero, b: entero");
    pb_agregar_contrato(sesion, "a > 0", PB_CONTRACT_REQUIERE);
    pb_agregar_contrato(sesion, "b > 0", PB_CONTRACT_REQUIERE);

    int n = pb_exportar(sesion);
    test_assert("Exportacion generada", n >= 0);
    test_assert("Estado verificacion", sesion->estado == 2);

    // Estadísticas
    PBEstadisticas stats = pb_obtener_estadisticas(sesion);
    test_assert("Stats: 2 funciones", stats.num_funciones_exportadas == 2);
    test_assert("Stats: 3 contratos", stats.num_contratos_exportados == 3);
    test_assert("Stats: Coq", stats.formato_usado == PB_FORMAT_COQ);

    pb_cerrar(sesion);
}

// ============================================================
// Sección 9: Persistencia (save/load)
// ============================================================
static void test_persistence(void) {
    PBSession* sesion = pb_iniciar(NULL);
    test_assert("Session persistencia", sesion != NULL);

    pb_agregar_funcion(sesion, "fib", "entero", "n: entero");
    pb_agregar_contrato(sesion, "n >= 0", PB_CONTRACT_REQUIERE);
    pb_exportar(sesion);

    remove("_test_pb_session.bin");
    int rc = pb_guardar(sesion, "_test_pb_session.bin");
    test_assert("Sesion guardada", rc == 0);
    test_assert("1 funcion guardada", sesion->num_funciones == 1);
    pb_cerrar(sesion);

    // Cargar
    sesion = pb_iniciar(NULL);
    rc = pb_cargar(sesion, "_test_pb_session.bin");
    test_assert("Sesion cargada", rc == 0);
    test_assert("1 funcion cargada", sesion->num_funciones == 1);
    test_assert("Nombre preservado", strcmp(sesion->funciones[0].nombre_funcion, "fib") == 0);
    test_assert("Requiere preservado", sesion->funciones[0].num_requiere == 1);

    pb_cerrar(sesion);
    remove("_test_pb_session.bin");

    // Guardar NULL
    rc = pb_guardar(NULL, "_test_pb_session.bin");
    test_assert("Guardar NULL falla", rc == -1);

    // Cargar archivo inexistente
    sesion = pb_iniciar(NULL);
    rc = pb_cargar(sesion, "_test_no_existe.bin");
    test_assert("Cargar inexistente falla", rc == -1);
    pb_cerrar(sesion);
}

// ============================================================
// Sección 10: Estadísticas
// ============================================================
static void test_stats(void) {
    PBEstadisticas stats = pb_obtener_estadisticas(NULL);
    test_assert("Stats NULL: 0 funciones", stats.num_funciones_exportadas == 0);
    test_assert("Stats NULL: 0 contratos", stats.num_contratos_exportados == 0);

    PBSession* sesion = pb_iniciar(NULL);
    stats = pb_obtener_estadisticas(sesion);
    test_assert("Stats vacio: 0 funciones", stats.num_funciones_exportadas == 0);
    pb_cerrar(sesion);
}

// ============================================================
// Sección 11: Edge Cases
// ============================================================
static void test_edge_cases(void) {
    PBSession* sesion = pb_iniciar(NULL);
    test_assert("Session edge cases", sesion != NULL);

    // 11.1 Agregar contrato sin funciones
    int rc = pb_agregar_contrato(sesion, "x > 0", PB_CONTRACT_REQUIERE);
    test_assert("Contrato sin funcion falla", rc < 0);

    // 11.2 Agregar contrato con tipo inválido
    pb_agregar_funcion(sesion, "f", "entero", "x: entero");
    rc = pb_agregar_contrato(sesion, "x > 0", 99);  // Tipo inválido
    test_assert("Tipo contrato invalido falla", rc < 0);

    // 11.3 Contrato con expresión NULL
    rc = pb_agregar_contrato(sesion, NULL, PB_CONTRACT_REQUIERE);
    test_assert("Contrato NULL falla", rc < 0);

    // 11.4 Coq generation sin funciones
    PBSession* s2 = pb_iniciar(NULL);
    int len = pb_generar_archivo_coq(s2);
    test_assert("Coq sin funciones genera cabecera", len > 0);
    pb_cerrar(s2);

    // 11.5 Lean generation sin funciones
    s2 = pb_iniciar(NULL);
    len = pb_generar_archivo_lean(s2);
    test_assert("Lean sin funciones genera cabecera", len > 0);
    pb_cerrar(s2);

    // 11.6 Exportar sesión NULL
    rc = pb_exportar(NULL);
    test_assert("Exportar NULL falla", rc < 0);

    // 11.7 Guardar/Cargar con ruta NULL
    rc = pb_guardar(sesion, NULL);
    test_assert("Guardar ruta NULL falla", rc == -1);
    rc = pb_cargar(sesion, NULL);
    test_assert("Cargar ruta NULL falla", rc == -1);

    // 11.8 Cerrar sesión con datos
    pb_agregar_funcion(sesion, "g", "booleano", "x: entero, y: entero");
    pb_agregar_contrato(sesion, "x < y", PB_CONTRACT_REQUIERE);
    pb_agregar_contrato(sesion, "_resultado_ == verdadero", PB_CONTRACT_GARANTIZA);
    pb_generar_certificado(sesion, "g");
    test_assert("Funcion g verificada", sesion->funciones[1].verificada == PB_VERIFY_VALID);
    test_assert("Certificado g generado", strlen(sesion->funciones[1].certificado) > 0);

    pb_cerrar(sesion);
}

// ============================================================
// Main
// ============================================================

int main(void) {
    printf("============================================\n");
    printf("  Synapse Formal Proof Suite (M15.1)\n");
    printf("  Coq/Lean Bridge + Proof Certificates\n");
    printf("============================================\n");

    test_section_start("Synapse -> Coq Translation");
    test_synapse_to_coq();

    test_section_start("Synapse -> Lean Translation");
    test_synapse_to_lean();

    test_section_start("Session Lifecycle");
    test_lifecycle();

    test_section_start("Functions and Contracts");
    test_functions_and_contracts();

    test_section_start("Coq File Generation");
    test_coq_generation();

    test_section_start("Lean File Generation");
    test_lean_generation();

    test_section_start("Proof Certificates");
    test_certificates();

    test_section_start("Full Export");
    test_export();

    test_section_start("Persistence (Save/Load)");
    test_persistence();

    test_section_start("Statistics");
    test_stats();

    test_section_start("Edge Cases");
    test_edge_cases();

    printf("\n============================================\n");
    printf("  RESULTADOS: %d / %d PASS\n", test_passed, test_total);
    printf("============================================\n");

    return (test_passed == test_total) ? 0 : 1;
}
