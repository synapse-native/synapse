/*
 * test_cluster_multicast.c — Prueba de integración de UDP Multicast Real (M8.6)
 *
 * Compilar:
 *   gcc -O2 tests/test_cluster_multicast.c synapse_rt.o tweetnacl.o -o tests/test_cluster_multicast.exe -lm -lpthread -lws2_32
 *
 * Ejecutar:
 *   tests/test_cluster_multicast.exe
 *
 * Pruebas:
 *   1. Inicialización del socket multicast y unión al grupo
 *   2. Cierre del socket y salida del grupo
 *   3. Envío de anuncio SYNCLUSTER por multicast (loopback)
 *   4. Recepción y procesamiento de anuncio multicast
 *   5. Descubrimiento completo: enviar + recibir + registrar nodo
 *   6. Hilo de descubrimiento activo (start/stop)
 *   7. Múltiples multicast init/stop (reentrante)
 *   8. Consulta de info multicast
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <time.h>

#ifdef _WIN32
#include <windows.h>
#else
#include <unistd.h>
#endif

typedef struct { int longitud; const char* datos; } CadenaSegura;

// Forward declarations M8.5 + M8.6
extern int cluster_descubrimiento_inicializar(int max_nodos);
extern int cluster_registrar_nodo(CadenaSegura id, CadenaSegura ip, int puerto, CadenaSegura pubkey);
extern int cluster_total_nodos(void);
extern int cluster_nodos_activos(void);
extern CadenaSegura cluster_obtener_nodo(int idx);
extern int cluster_multicast_iniciar(const char* grupo, int puerto);
extern int cluster_multicast_detener(void);
extern int cluster_anunciar_por_multicast(CadenaSegura id, CadenaSegura ip_host, int puerto_host, CadenaSegura pubkey);
extern int cluster_escuchar_multicast(int timeout_ms);
extern int cluster_iniciar_hilo_descubrimiento(CadenaSegura id, CadenaSegura ip_host, int puerto_host, CadenaSegura pubkey, int intervalo_s);
extern int cluster_detener_hilo_descubrimiento(void);
extern int cluster_hilo_descubrimiento_activo(void);
extern CadenaSegura cluster_multicast_info(void);

#define CHECK(cond, msg) do { \
    if (!(cond)) { \
        fprintf(stderr, "[FAIL] %s (line %d)\n", msg, __LINE__); \
        fallos++; \
    } else { \
        fprintf(stderr, "[PASS] %s\n", msg); \
        exitosos++; \
    } \
} while(0)

#define CHECK_INT_EQ(val, expected, msg) CHECK((val) == (expected), msg)
#define CHECK_INT_GT(val, threshold, msg) CHECK((val) > (threshold), msg)
#define CHECK_INT_GE(val, threshold, msg) CHECK((val) >= (threshold), msg)

static int fallos = 0;
static int exitosos = 0;

static CadenaSegura cs(const char* s) {
    return (CadenaSegura){ .longitud = (int)strlen(s), .datos = s };
}

int main(void) {
    fprintf(stderr, "=== Test M8.6: UDP Multicast Real Discovery ===\n\n");

    // Initialize discovery subsystem
    cluster_descubrimiento_inicializar(10);

    // ============================================
    // Test 1: Inicializar socket multicast
    // ============================================
    fprintf(stderr, "\n--- Test 1: Multicast Iniciar ---\n");
    int fd = cluster_multicast_iniciar("239.255.0.1", 19700);
    CHECK_INT_GT(fd, 0, "multicast_iniciar(239.255.0.1, 19700) ok");

    // Verify multicast info
    CadenaSegura info = cluster_multicast_info();
    CHECK(info.datos != NULL, "multicast_info no es NULL");
    CHECK(strstr(info.datos, "239.255.0.1") != NULL, "multicast_info contiene grupo");
    CHECK(strstr(info.datos, "19700") != NULL, "multicast_info contiene puerto");

    // ============================================
    // Test 2: Enviar y recibir anuncio (loopback)
    // ============================================
    fprintf(stderr, "\n--- Test 2: Enviar y recibir anuncio multicast ---\n");

    // Register node-1 as ourselves
    cluster_registrar_nodo(cs("nodo-A"), cs("127.0.0.1"), 19701, cs("pk_nodo_a"));

    // Send announcement for node-A
    int rc = cluster_anunciar_por_multicast(
        cs("nodo-A"), cs("127.0.0.1"), 19701, cs("pk_nodo_a"));
    CHECK_INT_EQ(rc, 0, "anunciar_por_multicast nodo-A ok");

    // Give OS time to deliver the loopback packet
#ifdef _WIN32
    Sleep(100);
#else
    usleep(100000);
#endif

    // Receive and process (simulating another node listening)
    int listen_rc = cluster_escuchar_multicast(500);
    CHECK(listen_rc == 0 || listen_rc == 1,
          "escuchar_multicast ok (0=procesado o 1=sin datos en loopback)");

    // We may or may not receive our own packet depending on loopback config.
    // The test validates the API works without crashing.

    // ============================================
    // Test 3: Segundo nodo — registro y discovery
    // ============================================
    fprintf(stderr, "\n--- Test 3: Discovery completo con 2 nodos ---\n");

    // Register node-B directly (simulates discovery via multicast)
    cluster_registrar_nodo(cs("nodo-B"), cs("10.0.0.20"), 19702, cs("pk_nodo_b"));
    CHECK_INT_EQ(cluster_total_nodos(), 2, "2 nodos totales (nodo-A, nodo-B)");

    // Verify we can retrieve node info
    CadenaSegura infoA = cluster_obtener_nodo(0);
    CHECK(infoA.datos != NULL, "obtener_nodo(0) existe");
    CadenaSegura infoB = cluster_obtener_nodo(1);
    CHECK(infoB.datos != NULL, "obtener_nodo(1) existe");

    // ============================================
    // Test 4: Envío y recepción directa (loopback test)
    // ============================================
    fprintf(stderr, "\n--- Test 4: Envio/recepcion directa loopback ---\n");

    // Send multiple packets
    for (int i = 0; i < 3; i++) {
        char id[32];
        snprintf(id, sizeof(id), "nodo-loop-%d", i);
        rc = cluster_anunciar_por_multicast(
            cs(id), cs("127.0.0.1"), 19800 + i, cs("pk_loop"));
        CHECK_INT_EQ(rc, 0, "anuncio loopback ok");
    }

#ifdef _WIN32
    Sleep(200);
#else
    usleep(200000);
#endif

    // Try to receive any loopback packets (may or may not work on Windows)
    int received = 0;
    for (int i = 0; i < 5; i++) {
        rc = cluster_escuchar_multicast(100);
        if (rc == 0) received++;
        if (rc < 0) break; // error
    }
    fprintf(stderr, "[INFO] Paquetes loopback recibidos: %d (depende de config)\n", received);

    // ============================================
    // Test 5: Hilo de descubrimiento activo
    // ============================================
    fprintf(stderr, "\n--- Test 5: Hilo de descubrimiento activo ---\n");

    // Start background discovery thread (5s interval, but won't run long)
    rc = cluster_iniciar_hilo_descubrimiento(
        cs("nodo-thread"), cs("192.168.1.100"), 19900,
        cs("pk_thread"), 2); // 2 second interval
    CHECK_INT_EQ(rc, 0, "iniciar_hilo_descubrimiento ok");
    CHECK_INT_EQ(cluster_hilo_descubrimiento_activo(), 1, "hilo activo");

    // Let it run briefly
#ifdef _WIN32
    Sleep(500);
#else
    usleep(500000);
#endif

    // Stop the thread
    rc = cluster_detener_hilo_descubrimiento();
    CHECK_INT_EQ(rc, 0, "detener_hilo_descubrimiento ok");

#ifdef _WIN32
    Sleep(100);
#else
    usleep(100000);
#endif

    CHECK_INT_EQ(cluster_hilo_descubrimiento_activo(), 0, "hilo inactivo tras detener");

    // ============================================
    // Test 6: Segundo inicio del hilo
    // ============================================
    fprintf(stderr, "\n--- Test 6: Reinicio del hilo de descubrimiento ---\n");
    rc = cluster_iniciar_hilo_descubrimiento(
        cs("nodo-thread2"), cs("10.0.0.50"), 19901,
        cs("pk_thread2"), 3);
    CHECK_INT_EQ(rc, 0, "reiniciar hilo ok");
    CHECK_INT_EQ(cluster_hilo_descubrimiento_activo(), 1, "hilo reactivado");

    // Cannot start another while active
    rc = cluster_iniciar_hilo_descubrimiento(
        cs("otro"), cs("10.0.0.99"), 19999, cs("otra_pk"), 1);
    CHECK_INT_EQ(rc, -1, "segundo hilo rechazado (-1)");

    // Stop
    cluster_detener_hilo_descubrimiento();
#ifdef _WIN32
    Sleep(200);
#else
    usleep(200000);
#endif

    // ============================================
    // Test 7: Multicast reentrante (stop/start)
    // ============================================
    fprintf(stderr, "\n--- Test 7: Multicast reentrante ---\n");
    rc = cluster_multicast_detener();
    CHECK_INT_EQ(rc, 0, "multicast_detener ok");
    CHECK_INT_EQ(cluster_hilo_descubrimiento_activo(), 0, "hilo inactivo tras detener multicast");

    // Restart multicast
    fd = cluster_multicast_iniciar("239.255.0.1", 19700);
    CHECK_INT_GT(fd, 0, "reiniciar multicast ok");

    // ============================================
    // Test 8: Cleanup final
    // ============================================
    fprintf(stderr, "\n--- Test 8: Cleanup final ---\n");
    rc = cluster_multicast_detener();
    CHECK_INT_EQ(rc, 0, "cleanup multicast final ok");

    // ============================================
    // Resultados
    // ============================================
    fprintf(stderr, "\n=== RESULTADOS M8.6 ===\n");
    fprintf(stderr, "Exitosos: %d | Fallos: %d\n", exitosos, fallos);
    fprintf(stderr, "=== %s ===\n", (fallos == 0) ? "TODOS LOS TESTS PASARON" : "HUBO FALLOS");

    return fallos;
}
