/**
 * test_time_travel.c — Deterministic Execution Recording and Replay (M9.1)
 *
 * Validates rr-style time-travel debugging primitives:
 *   1. Recording initialization with sequence numbering
 *   2. Branch decision recording (true/false paths)
 *   3. Variable snapshot capture
 *   4. Function call/return recording
 *   5. Error event recording with fault induction
 *   6. Backward event search by tag
 *   7. Event retrieval by index
 *   8. Simulated replay up to target sequence
 *   9. Replay finds the fault point from trace
 *  10. Total event count and error index
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <assert.h>

typedef struct { int longitud; const char* datos; } CadenaSegura;

extern void pool_init(uint32_t total_blocks, uint32_t block_size);
extern void* pool_alloc(size_t size);
extern void pool_free(void* ptr);

extern int tr_inicializar_recording(void);
extern int tr_grabar_bifurcacion(int linea, int rama, CadenaSegura id_funcion);
extern int tr_grabar_snapshot(CadenaSegura nombre_variable, long long valor_entero,
                               CadenaSegura valor_texto, int linea);
extern int tr_grabar_llamada(CadenaSegura funcion, int linea, int num_args);
extern int tr_grabar_retorno(CadenaSegura funcion, int linea);
extern int tr_grabar_error(CadenaSegura mensaje, int linea);
extern int tr_buscar_evento(int tag, int desde_secuencia);
extern CadenaSegura tr_obtener_evento(int indice);
extern int tr_reproducir_hasta(int secuencia_objetivo);
extern int tr_indice_ultimo_error(void);
extern int tr_total_eventos(void);

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

// ── Test 1: Recording initialization ─────────────────────────────
void test_recording_init(void) {
    printf("\n--- Test 1: Inicializacion de grabacion ---\n");

    int rc = tr_inicializar_recording();
    CHECK_INT_EQ(rc, 0, "tr_inicializar_recording() ok");

    CHECK_INT_EQ(tr_total_eventos(), 0, "0 eventos grabados al inicio");

    // Verify re-initialization is safe
    rc = tr_inicializar_recording();
    CHECK_INT_EQ(rc, 0, "re-inicializacion ok");
}

// ── Test 2: Branch recording ─────────────────────────────────────
void test_branch_recording(void) {
    printf("\n--- Test 2: Grabacion de bifurcaciones ---\n");

    tr_inicializar_recording();

    CadenaSegura fn = { .longitud = 10, .datos = "calcular" };

    int seq1 = tr_grabar_bifurcacion(42, 1, fn);
    CHECK(seq1 >= 0, "bifurcacion true grabada (secuencia >= 0)");

    int seq2 = tr_grabar_bifurcacion(45, 0, fn);
    CHECK(seq2 > seq1, "bifurcacion false tiene secuencia > true");
    CHECK_INT_EQ(tr_total_eventos(), 2, "2 eventos grabados tras 2 bifurcaciones");

    // Search backwards for the first branch (tag EVENT_BRANCH_TAKEN = 4)
    int found = tr_buscar_evento(4, -1);
    CHECK(found >= 0, "busqueda inversa encuentra bifurcacion");
    CHECK_INT_EQ(found, seq2, "busqueda inversa encuentra la mas reciente");
}

// ── Test 3: Variable snapshots ───────────────────────────────────
void test_variable_snapshots(void) {
    printf("\n--- Test 3: Snapshots de variables ---\n");

    tr_inicializar_recording();

    CadenaSegura var_x = { .longitud = 1, .datos = "x" };
    CadenaSegura var_y = { .longitud = 1, .datos = "y" };
    CadenaSegura var_z = { .longitud = 1, .datos = "z" };
    CadenaSegura empty = { .longitud = 0, .datos = NULL };

    int s1 = tr_grabar_snapshot(var_x, 42, empty, 10);
    CHECK(s1 >= 0, "snapshot x=42 ok");

    int s2 = tr_grabar_snapshot(var_y, -1, empty, 15);
    CHECK(s2 > s1, "snapshot y=-1 tiene secuencia mayor");

    CadenaSegura text_val = { .longitud = 5, .datos = "Hola!" };
    int s3 = tr_grabar_snapshot(var_z, 0, text_val, 20);
    CHECK(s3 > s2, "snapshot z='Hola!' tiene secuencia mayor");

    CHECK_INT_EQ(tr_total_eventos(), 3, "3 snapshots grabados");

    // Retrieve event at index 0 and verify it's the first snapshot
    CadenaSegura ev0 = tr_obtener_evento(0);
    CHECK_STR_NONEMPTY(ev0, "evento[0] obtenido");
    CHECK(ev0.longitud >= 4 && memcmp(ev0.datos, "6|0|", 4) == 0,
          "evento[0] es tag=6 (EVENT_VARIABLE_CHANGE) con seq=0");
    if (ev0.datos) pool_free((void*)ev0.datos);

    // Out of bounds
    CadenaSegura evBad = tr_obtener_evento(999);
    CHECK_STR_EMPTY(evBad, "indice fuera de rango devuelve vacio");
}

// ── Test 4: Function call/return recording ───────────────────────
void test_function_call_recording(void) {
    printf("\n--- Test 4: Grabacion de llamadas y retornos ---\n");

    tr_inicializar_recording();

    CadenaSegura fn_main = { .longitud = 9, .datos = "principal" };
    CadenaSegura fn_foo = { .longitud = 3, .datos = "foo" };

    int call1 = tr_grabar_llamada(fn_main, 5, 0);
    CHECK(call1 >= 0, "llamada a principal() ok");

    int call2 = tr_grabar_llamada(fn_foo, 30, 2);
    CHECK(call2 > call1, "llamada anidada a foo(2) tiene secuencia mayor");

    int ret2 = tr_grabar_retorno(fn_foo, 35);
    CHECK(ret2 > call2, "retorno de foo tiene secuencia > llamada");

    int ret1 = tr_grabar_retorno(fn_main, 40);
    CHECK(ret1 > ret2, "retorno de principal tiene secuencia > retorno foo");

    CHECK_INT_EQ(tr_total_eventos(), 4, "4 eventos de llamada/retorno");

    // Search for first function call (EVENT_FN_CALL = 1)
    int found = tr_buscar_evento(1, call2);
    CHECK(found >= 0, "busqueda inversa encuentra llamada");
    CHECK(found <= call2, "busqueda respeta limite de secuencia");
}

// ── Test 5: Error recording and fault induction ───────────────────
void test_error_recording(void) {
    printf("\n--- Test 5: Grabacion de errores e induccion de fallos ---\n");

    tr_inicializar_recording();

    CadenaSegura fn = { .longitud = 8, .datos = "procesar" };
    CadenaSegura err = { .longitud = 17, .datos = "division_por_cero" };

    // Simulate normal execution
    tr_grabar_llamada(fn, 50, 1);
    tr_grabar_bifurcacion(55, 1, fn);
    CadenaSegura var_n = { .longitud = 1, .datos = "n" };
    tr_grabar_snapshot(var_n, 0, (CadenaSegura){ .longitud = 0, .datos = NULL }, 58);

    // Induce fault: division by zero
    int err_seq = tr_grabar_error(err, 60);
    CHECK(err_seq >= 0, "error grabado");

    // Verify error index
    int err_idx = tr_indice_ultimo_error();
    CHECK(err_idx >= 0, "tr_indice_ultimo_error() >= 0");

    // Search backwards for error (EVENT_ERROR = 3)
    int found = tr_buscar_evento(3, -1);
    CHECK(found >= 0, "busqueda inversa encuentra el error");
    CHECK_INT_EQ(found, err_seq, "secuencia del error coincide");

    CHECK_INT_EQ(tr_total_eventos(), 4, "4 eventos totales (incluyendo error)");
}

// ── Test 6: Replay simulation ────────────────────────────────────
void test_replay_simulation(void) {
    printf("\n--- Test 6: Simulacion de replay determinista ---\n");

    tr_inicializar_recording();

    CadenaSegura fn = { .longitud = 8, .datos = "simular" };
    CadenaSegura var_a = { .longitud = 1, .datos = "a" };
    CadenaSegura empty = { .longitud = 0, .datos = NULL };

    // Record a sequence of events
    tr_grabar_llamada(fn, 1, 0);
    tr_grabar_snapshot(var_a, 10, empty, 2);
    tr_grabar_bifurcacion(3, 1, fn);
    tr_grabar_snapshot(var_a, 20, empty, 4);
    tr_grabar_bifurcacion(5, 0, fn);
    tr_grabar_retorno(fn, 6);

    int total = tr_total_eventos();
    CHECK_INT_EQ(total, 6, "6 eventos grabados para replay");

    // Replay up to sequence 2 (should replay 3 events: seq 0, 1, 2)
    int replayed = tr_reproducir_hasta(2);
    CHECK(replayed >= 3, "replay hasta seq=2 reproduce >=3 eventos");

    // Replay up to sequence 5 (all events)
    replayed = tr_reproducir_hasta(5);
    CHECK_INT_EQ(replayed, total, "replay hasta seq=5 reproduce todos los eventos");

    // Replay with invalid target returns -1
    CHECK_INT_EQ(tr_reproducir_hasta(-1), -1, "replay con secuencia negativa devuelve -1");
}

// ── Test 7: Search edge cases ────────────────────────────────────
void test_search_edge_cases(void) {
    printf("\n--- Test 7: Casos borde de busqueda inversa ---\n");

    tr_inicializar_recording();

    // No events: search should return -1
    CHECK_INT_EQ(tr_buscar_evento(4, -1), -1, "buscar en buffer vacio devuelve -1");
    CHECK_INT_EQ(tr_indice_ultimo_error(), -1, "sin errores, indice_ultimo_error = -1");

    CadenaSegura fn = { .longitud = 4, .datos = "test" };
    CadenaSegura var_x = { .longitud = 1, .datos = "x" };
    CadenaSegura empty = { .longitud = 0, .datos = NULL };

    // Record multiple branches
    tr_grabar_bifurcacion(10, 1, fn);  // seq 0
    tr_grabar_snapshot(var_x, 1, empty, 11);  // seq 1 (tag=6)
    tr_grabar_bifurcacion(12, 0, fn);  // seq 2

    // Search for first branch (tag=4) limited to seq 0
    int found = tr_buscar_evento(4, 0);
    CHECK_INT_EQ(found, 0, "busqueda limitada a seq=0 encuentra la primera bifurcacion");

    // Search for first branch without limit (should find the latest = seq 2)
    found = tr_buscar_evento(4, -1);
    CHECK_INT_EQ(found, 2, "busqueda sin limite encuentra la bifurcacion mas reciente (seq=2)");

    // Search for non-existent tag
    found = tr_buscar_evento(7, -1);
    CHECK_INT_EQ(found, -1, "buscar tag=7 (sin eventos) devuelve -1");
}

// ── Test 8: Sequence monotonicity ─────────────────────────────────
void test_sequence_monotonicity(void) {
    printf("\n--- Test 8: Monotonicidad de secuencia ---\n");

    tr_inicializar_recording();

    CadenaSegura fn = { .longitud = 4, .datos = "test" };
    CadenaSegura empty = { .longitud = 0, .datos = NULL };
    CadenaSegura var_v = { .longitud = 1, .datos = "v" };

    int prev = -1;
    for (int i = 0; i < 20; i++) {
        int seq = -1;
        switch (i % 4) {
            case 0: seq = tr_grabar_bifurcacion(i, i % 2, fn); break;
            case 1: seq = tr_grabar_snapshot(var_v, (long long)i, empty, i); break;
            case 2: seq = tr_grabar_llamada(fn, i, 0); break;
            case 3: seq = tr_grabar_retorno(fn, i); break;
        }
        CHECK(seq > prev, "secuencias monotonicas");
        prev = seq;
    }
    CHECK_INT_EQ(tr_total_eventos(), 20, "20 eventos con secuencias unicas y monotonicas");
}

int main(void) {
    setbuf(stdout, NULL);
    printf("========================================================\n");
    printf("  M9.1 — Deterministic Execution Recording (rr-style)\n");
    printf("  Time-Travel Debug: Branch/Snapshot/Call/Replay\n");
    printf("========================================================\n");

    pool_init(128, 4096);

    test_recording_init();
    test_branch_recording();
    test_variable_snapshots();
    test_function_call_recording();
    test_error_recording();
    test_replay_simulation();
    test_search_edge_cases();
    test_sequence_monotonicity();

    printf("\n========================================================\n");
    printf("  Resultados: %d passed, %d failed", passed, failed);
    if (failed > 0) printf(" <<< HAY FALLOS");
    printf("\n========================================================\n");

    return failed > 0 ? 1 : 0;
}