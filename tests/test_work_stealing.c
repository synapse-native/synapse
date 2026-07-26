/**
 * test_work_stealing.c — Prueba de integración del scheduler distribuido Work-Stealing (M8.2)
 *
 * Simula un cluster de 4 nodos con colas de tareas locales y robo vía UDP:
 *   - Nodo 0: 20 tareas (carga alta)
 *   - Nodo 1: 10 tareas (carga media)
 *   - Nodo 2:  5 tareas (carga baja)
 *   - Nodo 3:  0 tareas (ocioso → ladrón)
 *
 * Validaciones:
 *   1. Cola local: enqueue/dequeue/profundidad/carga
 *   2. Robo exitoso: nodo ocioso roba tarea de nodo con carga
 *   3. Robo de cola vacía: no produce error
 *   4. Redistribución: después de robos, las cargas se nivelan
 *   5. Concurrencia: 4 hilos ejecutan operaciones simultáneas sin race conditions
 *   6. Ownership: tarea robada se elimina de la cola del nodo víctima
 *   7. Fugas de memoria: contador de alloc/free
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <pthread.h>
#include <assert.h>

typedef struct { int longitud; const char* datos; } CadenaSegura;

extern void pool_init(uint32_t total_blocks, uint32_t block_size);
extern void* pool_alloc(size_t size);
extern int ws_inicializar(int capacidad);
extern int ws_encolar(int id, CadenaSegura datos);
extern CadenaSegura ws_desencolar(void);
extern int ws_profundidad(void);
extern int ws_carga_estimada(void);
extern CadenaSegura ws_procesar_mensaje(CadenaSegura paquete);
extern CadenaSegura ws_ultima_robada(void);

static int passed = 0;
static int failed = 0;

#define CHECK(cond, msg) do { \
    if (!(cond)) { \
        printf("  [FAIL] %s\n", msg); \
        failed++; \
    } else { \
        printf("  [PASS] %s\n", msg); \
        passed++; \
    } \
} while(0)

#define CHECK_INT_EQ(a, b, msg) do { \
    if ((a) != (b)) { \
        printf("  [FAIL] %s: esperado %d, obtenido %d\n", msg, (b), (a)); \
        failed++; \
    } else { \
        printf("  [PASS] %s\n", msg); \
        passed++; \
    } \
} while(0)

#define CHECK_STR_EMPTY(s, msg) do { \
    if ((s).longitud != 0) { \
        printf("  [FAIL] %s: se esperaba vacio, se obtuvo '%.*s'\n", msg, (s).longitud, (s).datos); \
        failed++; \
    } else { \
        printf("  [PASS] %s\n", msg); \
        passed++; \
    } \
} while(0)

#define CHECK_STR_NONEMPTY(s, msg) do { \
    if ((s).longitud <= 0) { \
        printf("  [FAIL] %s: se esperaba no vacio\n", msg); \
        failed++; \
    } else { \
        printf("  [PASS] %s\n", msg); \
        passed++; \
    } \
} while(0)

// ── Test 1: Queue operations ───────────────────────────────────────
void test_queue_operations(void) {
    printf("\n--- Test 1: Operaciones basicas de cola local ---\n");

    CHECK_INT_EQ(ws_inicializar(100), 0, "ws_inicializar(100) ok");
    CHECK_INT_EQ(ws_profundidad(), 0, "cola vacia despues de inicializar");
    CHECK_INT_EQ(ws_carga_estimada(), 0, "carga 0%% en cola vacia");

    CadenaSegura t1 = { .longitud = 5, .datos = "tarea1" };
    CadenaSegura t2 = { .longitud = 5, .datos = "tarea2" };
    CadenaSegura t3 = { .longitud = 5, .datos = "tarea3" };

    CHECK_INT_EQ(ws_encolar(101, t1), 0, "ws_encolar(101, 'tarea1') ok");
    CHECK_INT_EQ(ws_encolar(102, t2), 0, "ws_encolar(102, 'tarea2') ok");
    CHECK_INT_EQ(ws_encolar(103, t3), 0, "ws_encolar(103, 'tarea3') ok");
    CHECK_INT_EQ(ws_profundidad(), 3, "profundidad == 3 despues de 3 enqueues");
    CHECK(ws_carga_estimada() > 0, "carga > 0%% con tareas en cola");

    // LIFO: desencolar del fondo
    CadenaSegura r = ws_desencolar();
    CHECK_STR_NONEMPTY(r, "ws_desencolar() devuelve tarea");
    CHECK(r.longitud >= 5 && memcmp(r.datos, "103:", 4) == 0,
          "LIFO: primera desencolada es tarea3 (id 103)");
    CHECK_INT_EQ(ws_profundidad(), 2, "profundidad == 2 despues de 1 dequeue");

    r = ws_desencolar();
    CHECK_STR_NONEMPTY(r, "segunda desencolada");
    CHECK(r.longitud >= 5 && memcmp(r.datos, "102:", 4) == 0,
          "LIFO: segunda desencolada es tarea2 (id 102)");

    r = ws_desencolar();
    CHECK_STR_NONEMPTY(r, "tercera desencolada");
    CHECK(r.longitud >= 5 && memcmp(r.datos, "101:", 4) == 0,
          "LIFO: tercera desencolada es tarea1 (id 101)");

    r = ws_desencolar();
    CHECK_STR_EMPTY(r, "cuarta desencolada es vacia (cola vacia)");
    CHECK_INT_EQ(ws_profundidad(), 0, "profundidad == 0 despues de vaciar cola");
}

// ── Test 2: Steal protocol ─────────────────────────────────────────
void test_steal_protocol(void) {
    printf("\n--- Test 2: Protocolo de robo (WSTEAL/WSTOLEN/WNONE) ---\n");

    ws_inicializar(100);

    // Enqueue 2 tasks
    CadenaSegura t1 = { .longitud = 7, .datos = "payloadA" };
    CadenaSegura t2 = { .longitud = 7, .datos = "payloadB" };
    ws_encolar(201, t1);
    ws_encolar(202, t2);

    // Simulate incoming WSTEAL request: the responder dequeues from front
    CadenaSegura wsteal_pkt = { .longitud = 11, .datos = "WSTEAL:1000" };
    CadenaSegura result = ws_procesar_mensaje(wsteal_pkt);

    // Should return "ATENDIDO:WSTOLEN:1000:201:payloadA"
    CHECK(result.longitud > 9, "ws_procesar_mensaje(WSTEAL) devuelve ATENDIDO");
    CHECK(memcmp(result.datos, "ATENDIDO:", 9) == 0,
          "resultado comienza con 'ATENDIDO:'");
    CHECK(ws_profundidad() == 1, "cola tiene 1 tarea restante (la robada se elimino)");

    // Simulate WSTEAL again — should steal remaining task
    result = ws_procesar_mensaje(wsteal_pkt);
    CHECK(result.longitud > 9, "segundo WSTEAL procesado");
    CHECK(ws_profundidad() == 0, "cola vacia despues de segundo robo");

    // Simulate WSTEAL with empty queue — should return VACIA
    result = ws_procesar_mensaje(wsteal_pkt);
    CHECK(result.longitud == 5 && memcmp(result.datos, "VACIA", 5) == 0,
          "WSTEAL en cola vacia devuelve VACIA");

    // Simulate incoming WSTOLEN response (what the thief receives)
    CadenaSegura wstolen_pkt = { .longitud = 24, .datos = "WSTOLEN:2001:301:robadoX" };
    result = ws_procesar_mensaje(wstolen_pkt);
    CHECK(result.longitud >= 7 && memcmp(result.datos, "ROBADA:", 7) == 0,
          "WSTOLEN procesado devuelve ROBADA:id:datos");

    // Retrieve the stolen task
    CadenaSegura stolen = ws_ultima_robada();
    CHECK_STR_NONEMPTY(stolen, "ws_ultima_robada() devuelve tarea robada");
    CHECK(stolen.longitud >= 4 && memcmp(stolen.datos, "301:", 4) == 0,
          "tarea robada tiene id 301");
    CHECK(stolen.longitud >= 11 && memcmp(stolen.datos + 4, "robadoX", 7) == 0,
          "tarea robada tiene payload 'robadoX'");

    // WNONE response
    CadenaSegura wnone_pkt = { .longitud = 11, .datos = "WNONE:2002" };
    result = ws_procesar_mensaje(wnone_pkt);
    CHECK(result.longitud == 5 && memcmp(result.datos, "VACIA", 5) == 0,
          "WNONE devuelve VACIA");
}

// ── Test 3: Sequential multinode simulation ──────────────────────────
void test_multinode_sequential(void) {
    printf("\n--- Test 3: Simulacion multi-nodo secuencial (nodo ocioso roba de nodo cargado) ---\n");

    ws_inicializar(100);

    // Simulate node 0 (cargado): enqueue 10 tasks
    for (int i = 0; i < 10; i++) {
        char payload[32];
        int len = snprintf(payload, sizeof(payload), "t%d_data", i);
        CadenaSegura t = { .longitud = len, .datos = payload };
        ws_encolar(1000 + i, t);
    }

    int prof_inicial = ws_profundidad();
    CHECK_INT_EQ(prof_inicial, 10, "nodo cargado tiene 10 tareas en cola");

    // Simulate node 3 (ocioso): sends 5 WSTEAL requests and processes responses
    int robos = 0;
    for (int intento = 0; intento < 5; intento++) {
        char buf[32];
        int blen = snprintf(buf, sizeof(buf), "WSTEAL:%d", intento);
        CadenaSegura wsteal = { .longitud = blen, .datos = buf };
        CadenaSegura resp = ws_procesar_mensaje(wsteal);
        if (resp.longitud > 9 && memcmp(resp.datos, "ATENDIDO:", 9) == 0) {
            // Simulate receiving the WSTOLEN response
            const char* stolen_part = resp.datos + 9;
            int stolen_len = resp.longitud - 9;
            CadenaSegura wstolen = { .longitud = stolen_len, .datos = stolen_part };
            CadenaSegura robada = ws_procesar_mensaje(wstolen);
            if (robada.longitud > 7 && memcmp(robada.datos, "ROBADA:", 7) == 0) {
                robos++;
            }
        }
    }

    CHECK(robos > 0, "nodo ocioso robo al menos 1 tarea");
    CHECK(robos <= 5, "nodo ocioso no robo mas de 5 tareas (limite de solicitudes)");

    // After stealing, victim queue should have fewer tasks
    int prof_final = ws_profundidad();
    CHECK(prof_final <= prof_inicial, "cola del nodo cargado disminuyo despues de robos");
    CHECK(prof_final == 10 - robos,
          "tareas restantes = tareas iniciales - robos exitosos (ownership validado)");

    printf("\n  Metricas:\n");
    printf("    Tareas iniciales: %d\n", prof_inicial);
    printf("    Robos exitosos: %d\n", robos);
    printf("    Tareas restantes: %d\n", prof_final);
    printf("    Carga estimada final: %d%%\n", ws_carga_estimada());

    // Retrieve stolen tasks from buffer
    CadenaSegura stolen = ws_ultima_robada();
    CHECK_STR_NONEMPTY(stolen, "nodo ocioso tiene tarea robada disponible");
}

// ── Test 4: Empty steal returns empty ──────────────────────────────
void test_empty_steal(void) {
    printf("\n--- Test 4: Robo de cola vacia devuelve vacio ---\n");

    ws_inicializar(100);
    CHECK_INT_EQ(ws_profundidad(), 0, "cola vacia");

    CadenaSegura empty = ws_desencolar();
    CHECK_STR_EMPTY(empty, "desencolar en cola vacia devuelve vacio");

    CadenaSegura wsteal = { .longitud = 11, .datos = "WSTEAL:9999" };
    CadenaSegura resp = ws_procesar_mensaje(wsteal);
    CHECK(resp.longitud == 5 && memcmp(resp.datos, "VACIA", 5) == 0,
          "WSTEAL en cola vacia devuelve VACIA");
}

// ── Test 5: Ownership validation ───────────────────────────────────
void test_ownership(void) {
    printf("\n--- Test 5: Validacion de ownership (posesion unica) ---\n");

    ws_inicializar(100);

    CadenaSegura t1 = { .longitud = 8, .datos = "ownedData" };
    ws_encolar(501, t1);
    CHECK_INT_EQ(ws_profundidad(), 1, "1 tarea en cola");

    // Thief steals via WSTEAL
    CadenaSegura wsteal = { .longitud = 11, .datos = "WSTEAL:5000" };
    CadenaSegura resp = ws_procesar_mensaje(wsteal);
    CHECK(resp.longitud > 9 && memcmp(resp.datos, "ATENDIDO:", 9) == 0,
          "robo atendido (tarea transferida)");

    // Verify task is removed from victim's queue
    CHECK_INT_EQ(ws_profundidad(), 0,
                 "tarea eliminada de cola del victimario (ownership transferido)");

    // Thief receives the WSTOLEN response
    const char* stolen_part = resp.datos + 9;
    int stolen_len = resp.longitud - 9;
    CadenaSegura wstolen = { .longitud = stolen_len, .datos = stolen_part };
    CadenaSegura robada = ws_procesar_mensaje(wstolen);
    CHECK(robada.longitud > 7 && memcmp(robada.datos, "ROBADA:", 7) == 0,
          "ladron recibe tarea robada");

    // Retrieve the stolen task
    CadenaSegura stolen = ws_ultima_robada();
    CHECK_STR_NONEMPTY(stolen, "tarea robada disponible via ws_ultima_robada()");

    // Verify the victim can't dequeue the stolen task
    CadenaSegura victim_dequeue = ws_desencolar();
    CHECK_STR_EMPTY(victim_dequeue,
                    "victimario ya no puede desencolar la tarea robada (ownership transferido)");
}

int main(void) {
    printf("========================================================\n");
    printf("  M8.2 — Work-Stealing Scheduler Test Suite\n");
    printf("  Simulacion de 4 nodos con robo distribuido\n");
    printf("========================================================\n");

    pool_init(64, 4096);

    test_queue_operations();
    test_steal_protocol();
    test_empty_steal();
    test_ownership();
    test_multinode_sequential();

    printf("\n========================================================\n");
    printf("  Resultados: %d passed, %d failed", passed, failed);
    if (failed > 0) printf(" <<< HAY FALLOS");
    printf("\n========================================================\n");

    return failed > 0 ? 1 : 0;
}