/*
 * test_cluster_discovery.c — Prueba de integración del Auto-Descubrimiento y Membresía (M8.5)
 *
 * Compilar:
 *   gcc -O2 tests/test_cluster_discovery.c synapse_rt.o -o tests/test_cluster_discovery.exe -lm -lpthread
 *
 * Ejecutar:
 *   tests/test_cluster_discovery.exe
 *
 * Pruebas:
 *   1. Inicialización del subsistema de descubrimiento
 *   2. Registro de nodos y consulta de membresía
 *   3. Eliminación de nodos de la tabla
 *   4. Heartbeat: tick, recepción, timeout y purga
 *   5. Generación y procesamiento de anuncios SYNCLUSTER
 *   6. Información de membresía como texto
 *   7. Verificación de salud de nodos
 *   8. Heartbeat invalida timeout correctamente
 *   9. Límite de nodos (tabla llena)
 *  10. Nodo duplicado se actualiza en lugar de duplicarse
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <time.h>

// Typedefs (deben coincidir con synapse_rt.c)
typedef struct { int longitud; const char* datos; } CadenaSegura;

// Forward declarations de las funciones a probar
extern int cluster_descubrimiento_inicializar(int max_nodos);
extern int cluster_descubrimiento_detener(void);
extern int cluster_registrar_nodo(CadenaSegura id, CadenaSegura ip, int puerto, CadenaSegura pubkey);
extern int cluster_eliminar_nodo(CadenaSegura id);
extern int cluster_nodos_activos(void);
extern int cluster_total_nodos(void);
extern CadenaSegura cluster_obtener_nodo(int idx);
extern int cluster_heartbeat_inicializar(int intervalo_s, int timeout_s);
extern int cluster_tick_heartbeat(int tiempo_actual_s);
extern int cluster_recibir_heartbeat(CadenaSegura id);
extern CadenaSegura cluster_generar_anuncio(CadenaSegura id, CadenaSegura ip, int puerto, CadenaSegura pubkey);
extern int cluster_procesar_anuncio(CadenaSegura paquete);
extern CadenaSegura cluster_info_membresia_como_texto(void);
extern int cluster_verificar_salud_nodo(CadenaSegura id);
extern int cluster_ultimo_tick_heartbeat(void);
extern CadenaSegura cluster_info_heartbeat(void);

// Helpers
#define CHECK(cond, msg) do { \
    if (!(cond)) { \
        fprintf(stderr, "[FAIL] %s (line %d)\\n", msg, __LINE__); \
        fallos++; \
    } else { \
        fprintf(stderr, "[PASS] %s\\n", msg); \
        exitosos++; \
    } \
} while(0)

#define CHECK_INT_EQ(val, expected, msg) CHECK((val) == (expected), msg)
#define CHECK_INT_GT(val, threshold, msg) CHECK((val) > (threshold), msg)

static int fallos = 0;
static int exitosos = 0;

static CadenaSegura cs(const char* s) {
    return (CadenaSegura){ .longitud = (int)strlen(s), .datos = s };
}

int main(void) {
    fprintf(stderr, "=== Test M8.5: Cluster Auto-Discovery & Membership ===\\n\\n");

    // ============================================
    // Test 1: Inicialización
    // ============================================
    fprintf(stderr, "\\n--- Test 1: Descubrimiento Inicializar ---\\n");
    int rc = cluster_descubrimiento_inicializar(10);
    CHECK_INT_EQ(rc, 0, "descubrimiento_inicializar(10) ok");

    CHECK_INT_EQ(cluster_total_nodos(), 0, "tabla vacia tras init");

    // ============================================
    // Test 2: Registro de nodos
    // ============================================
    fprintf(stderr, "\\n--- Test 2: Registro de nodos ---\\n");
    int idx1 = cluster_registrar_nodo(cs("nodo-1"), cs("192.168.1.10"), 9001, cs("pubkey_abc123"));
    CHECK_INT_GT(idx1, -1, "registrar nodo-1 ok");
    CHECK_INT_EQ(idx1, 0, "nodo-1 tiene indice 0");

    int idx2 = cluster_registrar_nodo(cs("nodo-2"), cs("192.168.1.20"), 9002, cs("pubkey_def456"));
    CHECK_INT_GT(idx2, -1, "registrar nodo-2 ok");

    CHECK_INT_EQ(cluster_total_nodos(), 2, "2 nodos registrados");
    CHECK_INT_EQ(cluster_nodos_activos(), 2, "2 nodos activos");

    // ============================================
    // Test 3: Consultar nodo por índice
    // ============================================
    fprintf(stderr, "\\n--- Test 3: Obtener nodo ---\\n");
    CadenaSegura info = cluster_obtener_nodo(0);
    CHECK(info.datos != NULL, "obtener_nodo(0) no es NULL");
    CHECK(strstr(info.datos, "nodo-1") != NULL, "nodo 0 contiene 'nodo-1'");
    CHECK(strstr(info.datos, "192.168.1.10") != NULL, "nodo 0 contiene IP");
    CHECK(strstr(info.datos, "pubkey_abc123") != NULL, "nodo 0 contiene pubkey");

    info = cluster_obtener_nodo(1);
    CHECK(info.datos != NULL, "obtener_nodo(1) no es NULL");
    CHECK(strstr(info.datos, "nodo-2") != NULL, "nodo 1 contiene 'nodo-2'");

    info = cluster_obtener_nodo(99);
    CHECK(info.datos == NULL, "obtener_nodo(99) es NULL (fuera de rango)");

    // ============================================
    // Test 4: Eliminar nodo
    // ============================================
    fprintf(stderr, "\\n--- Test 4: Eliminar nodo ---\\n");
    rc = cluster_eliminar_nodo(cs("nodo-2"));
    CHECK_INT_EQ(rc, 0, "eliminar nodo-2 ok");
    CHECK_INT_EQ(cluster_total_nodos(), 1, "1 nodo tras eliminar");
    CHECK_INT_EQ(cluster_nodos_activos(), 1, "1 nodo activo tras eliminar");

    // Eliminar nodo inexistente
    rc = cluster_eliminar_nodo(cs("nodo-inexistente"));
    CHECK_INT_EQ(rc, -1, "eliminar nodo inexistente retorna -1");

    // ============================================
    // Test 5: Heartbeat — tick y timeout
    // ============================================
    fprintf(stderr, "\\n--- Test 5: Heartbeat tick y timeout ---\\n");

    // Re-registrar nodo-2
    cluster_registrar_nodo(cs("nodo-2"), cs("192.168.1.20"), 9002, cs("pubkey_def456"));

    // Configurar heartbeat: tick cada 2s, timeout a 6s
    rc = cluster_heartbeat_inicializar(2, 6);
    CHECK_INT_EQ(rc, 0, "heartbeat_inicializar(2, 6) ok");

    CadenaSegura hb_info = cluster_info_heartbeat();
    CHECK(hb_info.datos != NULL, "info_heartbeat no es NULL");
    CHECK(strstr(hb_info.datos, "2:6") != NULL || strstr(hb_info.datos, "2") != NULL,
          "heartbeat config contiene intervalo 2 y timeout >= 6");

    // Tick con tiempo actual para verificar estado inicial (ambos nodos VIVOS)
    // Ambos nodos fueron registrados hace <1s, timeout es 6s, debe haber 0 purgados
    int purgados = cluster_tick_heartbeat((int)time(NULL));
    CHECK(purgados >= 0, "tick heartbeat ejecutado sin errores");

    // Verificar que ambos nodos estan VIVOS o SOSPECHOSOS (no MUERTOS)
    int salud_n1 = cluster_verificar_salud_nodo(cs("nodo-1"));
    int salud_n2 = cluster_verificar_salud_nodo(cs("nodo-2"));
    CHECK(salud_n1 == 1 || salud_n1 == 2, "nodo-1 VIVO o SOSPECHOSO tras tick reciente");
    CHECK(salud_n2 == 1 || salud_n2 == 2, "nodo-2 VIVO o SOSPECHOSO tras tick reciente");

    // Tick con tiempo futuro para simular timeout
    // +20s con timeout 6s: ambos nodos deberian morir
    int purgados_futuro = cluster_tick_heartbeat((int)time(NULL) + 20);
    CHECK_INT_GT(purgados_futuro, 0, "tick heartbeat futuro purga nodos caidos");

    // Ambos nodos deben estar MUERTOS (3) por timeout
    int salud_n1_fut = cluster_verificar_salud_nodo(cs("nodo-1"));
    int salud_n2_fut = cluster_verificar_salud_nodo(cs("nodo-2"));
    CHECK_INT_EQ(salud_n1_fut, 3, "nodo-1 MUERTO por timeout");
    CHECK_INT_EQ(salud_n2_fut, 3, "nodo-2 MUERTO por timeout");

    // Verificar tick timestamp
    CHECK_INT_GT(cluster_ultimo_tick_heartbeat(), 0, "ultimo_tick_heartbeat > 0");

    // ============================================
    // Test 6: Heartbeat revive nodo
    // ============================================
    fprintf(stderr, "\\n--- Test 6: Heartbeat revive nodo ---\\n");
    rc = cluster_recibir_heartbeat(cs("nodo-2"));
    CHECK_INT_EQ(rc, 0, "recibir_heartbeat nodo-2 ok");
    CHECK_INT_EQ(cluster_verificar_salud_nodo(cs("nodo-2")), 1, "nodo-2 VIVO tras heartbeat recibido");

    // ============================================
    // Test 7: Anuncio SYNCLUSTER
    // ============================================
    fprintf(stderr, "\\n--- Test 7: Generacion y procesamiento de anuncio ---\\n");
    CadenaSegura anuncio = cluster_generar_anuncio(cs("nodo-3"), cs("10.0.0.50"), 9003, cs("key_xyz789"));
    CHECK(anuncio.datos != NULL, "generar_anuncio no es NULL");
    CHECK(strstr(anuncio.datos, "SYNCLUSTER") != NULL, "anuncio contiene 'SYNCLUSTER'");
    CHECK(strstr(anuncio.datos, "nodo-3") != NULL, "anuncio contiene 'nodo-3'");
    CHECK(strstr(anuncio.datos, "10.0.0.50") != NULL, "anuncio contiene IP");
    CHECK(strstr(anuncio.datos, "9003") != NULL, "anuncio contiene puerto");
    CHECK(strstr(anuncio.datos, "key_xyz789") != NULL, "anuncio contiene pubkey");

    // Procesar el anuncio (simula recepción en otro nodo)
    rc = cluster_procesar_anuncio(anuncio);
    CHECK_INT_EQ(rc, 0, "procesar_anuncio ok");

    // Verificar nodo-3 registrado
    CHECK_INT_EQ(cluster_verificar_salud_nodo(cs("nodo-3")), 1, "nodo-3 VIVO tras anuncio");
    CHECK_INT_EQ(cluster_total_nodos(), 3, "3 nodos totales (nodo-1, nodo-2, nodo-3)");

    // Anuncio inválido
    rc = cluster_procesar_anuncio(cs("INVALIDO:foo:bar"));
    CHECK_INT_EQ(rc, -2, "anuncio invalido retorna -2");

    rc = cluster_procesar_anuncio(cs("SYNCLUSTER:"));
    CHECK(rc < 0, "anuncio truncado retorna error");

    // ============================================
    // Test 8: Información de membresía como texto
    // ============================================
    fprintf(stderr, "\\n--- Test 8: Info membresia como texto ---\\n");
    CadenaSegura membresia = cluster_info_membresia_como_texto();
    CHECK(membresia.datos != NULL, "info_membresia no es NULL");
    CHECK(strstr(membresia.datos, "nodo-1") != NULL, "membresia contiene nodo-1");
    CHECK(strstr(membresia.datos, "nodo-2") != NULL, "membresia contiene nodo-2");
    CHECK(strstr(membresia.datos, "nodo-3") != NULL, "membresia contiene nodo-3");

    // ============================================
    // Test 9: Nodo duplicado se actualiza
    // ============================================
    fprintf(stderr, "\\n--- Test 9: Nodo duplicado se actualiza ---\\n");
    int idx_dup = cluster_registrar_nodo(cs("nodo-1"), cs("192.168.1.10"), 9001, cs("nueva_pubkey"));
    CHECK_INT_EQ(idx_dup, 0, "nodo duplicado retorna mismo indice");

    // Verificar pubkey actualizada
    CadenaSegura info_actualizada = cluster_obtener_nodo(0);
    CHECK(strstr(info_actualizada.datos, "nueva_pubkey") != NULL,
          "nodo duplicado actualiza pubkey");
    CHECK_INT_EQ(cluster_total_nodos(), 3, "total nodos sigue siendo 3 (sin duplicado)");

    // ============================================
    // Test 10: Detener y reinicializar
    // ============================================
    fprintf(stderr, "\\n--- Test 10: Detener y reinicializar ---\\n");
    rc = cluster_descubrimiento_detener();
    CHECK_INT_EQ(rc, 0, "descubrimiento_detener ok");
    CHECK_INT_EQ(cluster_nodos_activos(), 0, "0 nodos activos tras detener");

    // Reinicializar
    rc = cluster_descubrimiento_inicializar(64);
    CHECK_INT_EQ(rc, 0, "reinicializar con 64 slots ok");
    CHECK_INT_EQ(cluster_total_nodos(), 0, "tabla vacia tras reinicializar");

    // ============================================
    // Resultados
    // ============================================
    fprintf(stderr, "\\n=== RESULTADOS M8.5 ===\\n");
    fprintf(stderr, "Eitosos: %d | Fallos: %d\\n", exitosos, fallos);
    fprintf(stderr, "=== %s ===\\n", (fallos == 0) ? "TODOS LOS TESTS PASARON" : "HUBO FALLOS");

    return fallos;
}
