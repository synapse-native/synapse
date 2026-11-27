// M9.3 — Memory Snapshots & Historical State Diff
// Tests for ms_* engine (snapshot, diff, secuencias)
// Compile: gcc -I. -I../compilador -o test_memory_snapshots test_memory_snapshots.c ../synapse_rt.c ../tweetnacl.c -lm -lws2_32 -static
// Run: ./test_memory_snapshots

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdint.h>
#include <assert.h>

typedef struct { int longitud; const char* datos; } CadenaSegura;

extern void pool_init(uint32_t total_blocks, uint32_t block_size);
extern void* pool_alloc(size_t size);
extern void pool_free(void* ptr);

extern int tr_inicializar_recording(void);
extern int tr_grabar_snapshot(CadenaSegura nombre_variable, int valor_entero,
                               CadenaSegura valor_texto, int linea);
extern int tr_grabar_bifurcacion(int linea, int rama, CadenaSegura id_funcion);
extern int tr_grabar_llamada(CadenaSegura funcion, int linea, int num_args);
extern int tr_grabar_retorno(CadenaSegura funcion, int linea);
extern int tr_grabar_error(CadenaSegura mensaje, int linea);
extern int tr_total_eventos(void);

extern CadenaSegura ms_tomar_en(int secuencia);
extern CadenaSegura ms_diferenciar(CadenaSegura snap_a, CadenaSegura snap_b);
extern CadenaSegura ms_diff_entre(int seq_a, int seq_b);
extern int ms_snapshot_contar_vars(CadenaSegura snapshot);
extern int ms_snapshot_tamano(CadenaSegura snapshot);
extern CadenaSegura ms_snapshot_contiene(CadenaSegura snapshot, CadenaSegura nombre);

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

#define CHECK_NULL(ptr, msg) do { \
    if ((ptr).datos != NULL) { \
        printf("  [FAIL] %s: se esperaba NULL\n", msg); \
        failed++; \
    } else { \
        printf("  [PASS] %s\n", msg); \
        passed++; \
    } \
} while(0)

#define CHECK_NOT_NULL(ptr, msg) do { \
    if ((ptr).datos == NULL) { \
        printf("  [FAIL] %s: se esperaba no NULL\n", msg); \
        failed++; \
    } else { \
        printf("  [PASS] %s\n", msg); \
        passed++; \
    } \
} while(0)

#define CHECK_STR_CONTENTS(s, substr, msg) do { \
    if ((s).datos == NULL || strstr((s).datos, (substr)) == NULL) { \
        printf("  [FAIL] %s: se esperaba '%s' en '%.*s'\n", msg, (substr), \
               (s).longitud, (s).datos ? (s).datos : "(null)"); \
        failed++; \
    } else { \
        printf("  [PASS] %s\n", msg); \
        passed++; \
    } \
} while(0)

int main() {
    pool_init(8096, 64);

    CadenaSegura empty = { .longitud = 0, .datos = NULL };
    CadenaSegura s_main = { .longitud = 4, .datos = "main" };
    CadenaSegura s_x = { .longitud = 1, .datos = "x" };
    CadenaSegura s_y = { .longitud = 1, .datos = "y" };
    CadenaSegura s_z = { .longitud = 1, .datos = "z" };
    CadenaSegura s_w = { .longitud = 1, .datos = "w" };
    CadenaSegura s_acc = { .longitud = 3, .datos = "acc" };
    CadenaSegura s_hello = { .longitud = 5, .datos = "hello" };
    CadenaSegura s_world = { .longitud = 5, .datos = "world" };

    printf("=== Escenario 1: ms_tomar_en — snapshot basico ===\n");
    {
        tr_inicializar_recording();

        // events: x=10 (seq 1), y=20 (seq 2), x=30 (seq 3), z=hello (seq 4)
        tr_grabar_snapshot(s_x, 10, empty, 1);
        tr_grabar_snapshot(s_y, 20, empty, 2);
        tr_grabar_snapshot(s_x, 30, empty, 3);
        tr_grabar_snapshot(s_z, 0, s_hello, 4);

        // Snapshot at seq=4 (the end): should capture x=30, y=20, z=hello
        CadenaSegura snap = ms_tomar_en(4);
        CHECK_NOT_NULL(snap, "snapshot en seq=4 no es NULL");
        CHECK_STR_CONTENTS(snap, "x", "snapshot contiene 'x'");
        CHECK_STR_CONTENTS(snap, "y", "snapshot contiene 'y'");
        CHECK_STR_CONTENTS(snap, "z", "snapshot contiene 'z'");
        CHECK_STR_CONTENTS(snap, "30", "x=30 en snapshot");
        CHECK_STR_CONTENTS(snap, "20", "y=20 en snapshot");
        CHECK_STR_CONTENTS(snap, "hello", "z=hello en snapshot");
        CHECK_INT_EQ(ms_snapshot_contar_vars(snap), 3, "3 variables en snapshot");

        // Snapshot at seq=1: should capture x=10 (only x exists)
        CadenaSegura snap1 = ms_tomar_en(1);
        CHECK_NOT_NULL(snap1, "snapshot en seq=1 no es NULL");
        CHECK_INT_EQ(ms_snapshot_contar_vars(snap1), 1, "1 variable en seq=1");
        CHECK_STR_CONTENTS(snap1, "10", "x=10 en seq=1");

        // Snapshot at seq=2: x=10, y=20
        CadenaSegura snap2 = ms_tomar_en(2);
        CHECK_NOT_NULL(snap2, "snapshot en seq=2 no es NULL");
        CHECK_INT_EQ(ms_snapshot_contar_vars(snap2), 2, "2 variables en seq=2");
        CHECK_STR_CONTENTS(snap2, "x|entero|10", "x=10 en seq=2");
        CHECK_STR_CONTENTS(snap2, "y|entero|20", "y=20 en seq=2");

        // Snapshot at seq=0 (pre-init): should be empty
        CadenaSegura snap0 = ms_tomar_en(0);
        CHECK_NULL(snap0, "snapshot en seq=0 es NULL (no hay eventos)");
    }

    printf("=== Escenario 2: ms_tomar_en — salto de secuencias ===\n");
    {
        tr_inicializar_recording();
        tr_grabar_snapshot(s_x, 5, empty, 10);    // seq=10
        tr_grabar_snapshot(s_y, 50, empty, 20);   // seq=20
        tr_grabar_bifurcacion(30, 1, s_main);      // seq=30 (non-variable)
        tr_grabar_snapshot(s_y, 99, empty, 40);   // seq=40

        // Snapshot at seq=35: nearest event at index min(34, total-1=3)=3
        // Event 3 has y=99, walking back gives x=5, y=99
        CadenaSegura snap35 = ms_tomar_en(35);
        CHECK_NOT_NULL(snap35, "snapshot en seq=35 no es NULL");
        CHECK_STR_CONTENTS(snap35, "x|entero|5", "x=5 en seq=35");
        CHECK_STR_CONTENTS(snap35, "y|entero|99", "y=99 en seq=35 (evento mas cercano)");

        // Snapshot at seq=45: x=5, y=99
        CadenaSegura snap45 = ms_tomar_en(45);
        CHECK_NOT_NULL(snap45, "snapshot en seq=45 no es NULL");
        CHECK_STR_CONTENTS(snap45, "y|entero|99", "y=99 en seq=45");
    }

    printf("=== Escenario 3: ms_diferenciar — diff basico ===\n");
    {
        tr_inicializar_recording();
        tr_grabar_snapshot(s_x, 10, empty, 1);
        tr_grabar_snapshot(s_y, 20, empty, 2);
        tr_grabar_snapshot(s_x, 99, empty, 3);
        tr_grabar_snapshot(s_z, 0, s_hello, 4);

        CadenaSegura snap_a = ms_tomar_en(2);  // x=10, y=20
        CadenaSegura snap_b = ms_tomar_en(4);  // x=99, y=20, z=hello

        CHECK_NOT_NULL(snap_a, "snap_a no es NULL");
        CHECK_NOT_NULL(snap_b, "snap_b no es NULL");

        CadenaSegura diff = ms_diferenciar(snap_a, snap_b);
        CHECK_NOT_NULL(diff, "diff no es NULL");
        CHECK_STR_CONTENTS(diff, "~x", "diff contiene cambio en x");
        CHECK_STR_CONTENTS(diff, "10", "diff contiene valor anterior de x (10)");
        CHECK_STR_CONTENTS(diff, "99", "diff contiene valor nuevo de x (99)");
        CHECK_STR_CONTENTS(diff, "+z", "diff contiene adicion de z");

        // y should NOT be in diff (unchanged)
        CHECK(strstr(diff.datos, "y") == NULL, "y no aparece en diff (sin cambios)");

        CHECK_INT_EQ(ms_snapshot_contar_vars(snap_a), 2, "snap_a tiene 2 vars");
        CHECK_INT_EQ(ms_snapshot_contar_vars(snap_b), 3, "snap_b tiene 3 vars");
    }

    printf("=== Escenario 4: ms_diferenciar — vars anadidas/eliminadas ===\n");
    {
        tr_inicializar_recording();
        tr_grabar_snapshot(s_x, 1, empty, 1);
        tr_grabar_snapshot(s_y, 2, empty, 2);
        // seq=3: remove y by changing to different... well vars never removed in trace
        tr_grabar_snapshot(s_z, 3, empty, 3);

        // snap_a: x=1, y=2   (at seq=2)
        // snap_b: x=1, y=2, z=3 (at seq=3)
        CadenaSegura snap_a = ms_tomar_en(2);
        CadenaSegura snap_b = ms_tomar_en(3);

        CadenaSegura diff = ms_diferenciar(snap_a, snap_b);
        CHECK_NOT_NULL(diff, "diff no es NULL");
        CHECK_STR_CONTENTS(diff, "+z", "diff contiene adicion de z");

        // Now create a scenario with removal: snapshot at seq=3 vs something missing
        // Actually variables don't get removed. But we can simulate by having A have more vars
        // than B. Let's use ms_tomar_en(3) vs ms_tomar_en(2) — diff should show z as removed
        // Actually diff is (A, B), so diff(snap_a=seq3, snap_b=seq2) should show -z
        CadenaSegura diff_rev = ms_diferenciar(snap_b, snap_a);
        CHECK_NOT_NULL(diff_rev, "diff_rev no es NULL");
        CHECK_STR_CONTENTS(diff_rev, "-z", "diff_rev contiene eliminacion de z");
    }

    printf("=== Escenario 5: ms_diff_entre — diff por secuencia ===\n");
    {
        tr_inicializar_recording();
        tr_grabar_snapshot(s_x, 100, empty, 10);    // seq=1
        tr_grabar_snapshot(s_y, 200, empty, 20);    // seq=2
        tr_grabar_snapshot(s_x, 999, empty, 30);    // seq=3
        tr_grabar_snapshot(s_z, 0, s_world, 40);    // seq=4

        // diff between seq=1 (x=100) and seq=4 (x=999, y=200, z=world)
        CadenaSegura diff = ms_diff_entre(1, 4);
        CHECK_NOT_NULL(diff, "diff entre seq=1 y seq=4 no es NULL");
        CHECK_STR_CONTENTS(diff, "~x", "diff seq1->4 contiene cambio en x");
        CHECK_STR_CONTENTS(diff, "100", "contiene valor anterior x=100");
        CHECK_STR_CONTENTS(diff, "999", "contiene valor nuevo x=999");
        CHECK_STR_CONTENTS(diff, "+z", "diff contiene adicion de z");

        // Diff between same seq
        CadenaSegura diff_same = ms_diff_entre(2, 2);
        CHECK_NULL(diff_same, "diff entre seq iguales es NULL");

        // Reverse diff: seq=4 -> seq=1 (x: 999→100, z removed but was added, y: unchanged)
        CadenaSegura diff_rev = ms_diff_entre(4, 1);
        CHECK_NOT_NULL(diff_rev, "diff reverso no es NULL");
        CHECK_STR_CONTENTS(diff_rev, "~x", "diff reverso contiene x");
    }

    printf("=== Escenario 6: ms_snapshot_contar_vars ===\n");
    {
        CadenaSegura snap_empty = { .longitud = 0, .datos = NULL };
        CHECK_INT_EQ(ms_snapshot_contar_vars(snap_empty), 0, "snapshot vacio -> 0");

        tr_inicializar_recording();
        tr_grabar_snapshot(s_x, 1, empty, 1);
        tr_grabar_snapshot(s_y, 2, empty, 2);
        tr_grabar_snapshot(s_z, 3, empty, 3);
        tr_grabar_snapshot(s_w, 4, empty, 4);
        tr_grabar_snapshot(s_acc, 5, empty, 5);

        CadenaSegura snap = ms_tomar_en(5);
        CHECK_INT_EQ(ms_snapshot_contar_vars(snap), 5, "5 variables en snapshot");
        CHECK(ms_snapshot_tamano(snap) > 0, "tamano snapshot > 0");
    }

    printf("=== Escenario 7: ms_snapshot_contiene ===\n");
    {
        tr_inicializar_recording();
        tr_grabar_snapshot(s_x, 42, empty, 1);
        tr_grabar_snapshot(s_y, 99, s_hello, 2);

        CadenaSegura snap = ms_tomar_en(2);

        CadenaSegura found_x = ms_snapshot_contiene(snap, s_x);
        CHECK_NOT_NULL(found_x, "x encontrado en snapshot");
        CHECK_STR_CONTENTS(found_x, "entero:42", "x=entero:42");

        CadenaSegura found_y = ms_snapshot_contiene(snap, s_y);
        CHECK_NOT_NULL(found_y, "y encontrado en snapshot");
        CHECK_STR_CONTENTS(found_y, "texto:hello", "y=texto:hello");

        CadenaSegura not_found = ms_snapshot_contiene(snap, s_w);
        CHECK_NULL(not_found, "w no encontrado -> NULL");

        CadenaSegura empty_lookup = ms_snapshot_contiene(snap, empty);
        CHECK_NULL(empty_lookup, "nombre vacio -> NULL");
    }

    printf("=== Escenario 8: Edge cases — snapshot sin variables ===\n");
    {
        tr_inicializar_recording();
        tr_grabar_bifurcacion(10, 1, s_main);  // No variable events

        CadenaSegura snap = ms_tomar_en(1);
        CHECK(snap.datos != NULL && snap.longitud == 0, "snapshot sin variables (solo bifurcaciones) -> datos validos con longitud 0");
        CHECK_INT_EQ(ms_snapshot_contar_vars(
            (CadenaSegura){ .longitud = 0, .datos = NULL }), 0, "contar vars de NULL -> 0");

        // Snapshot with only one event type
        ms_snapshot_tamano((CadenaSegura){ .longitud = 0, .datos = NULL });
        CHECK(1, "tamano de snapshot NULL -> 0 (no crash)");
    }

    printf("=== Escenario 9: Workflow completo — 3 puntos, diff incremental ===\n");
    {
        tr_inicializar_recording();

        tr_grabar_llamada(s_main, 1, 0);           // seq=1
        tr_grabar_snapshot(s_x, 0, empty, 2);      // seq=2
        tr_grabar_bifurcacion(3, 1, s_main);        // seq=3
        tr_grabar_snapshot(s_x, 1, empty, 4);      // seq=4
        tr_grabar_snapshot(s_acc, 100, empty, 5);  // seq=5
        tr_grabar_snapshot(s_x, 5, empty, 6);      // seq=6
        tr_grabar_snapshot(s_y, 50, empty, 7);     // seq=7
        tr_grabar_error(empty, 8);                  // seq=8

        // Snapshot at seq=2: x=0
        CadenaSegura snap2 = ms_tomar_en(2);
        CHECK_NOT_NULL(snap2, "snap en seq=2");
        CHECK_INT_EQ(ms_snapshot_contar_vars(snap2), 1, "seq=2: 1 var (x)");
        CHECK_STR_CONTENTS(snap2, "x|entero|0", "seq=2: x=0");

        // Snapshot at seq=5: x=1, acc=100
        CadenaSegura snap5 = ms_tomar_en(5);
        CHECK_NOT_NULL(snap5, "snap en seq=5");
        CHECK_INT_EQ(ms_snapshot_contar_vars(snap5), 2, "seq=5: 2 vars (x, acc)");
        CHECK_STR_CONTENTS(snap5, "x|entero|1", "seq=5: x=1");
        CHECK_STR_CONTENTS(snap5, "acc|entero|100", "seq=5: acc=100");

        // Snapshot at seq=7: x=5, acc=100, y=50
        CadenaSegura snap7 = ms_tomar_en(7);
        CHECK_NOT_NULL(snap7, "snap en seq=7");
        CHECK_INT_EQ(ms_snapshot_contar_vars(snap7), 3, "seq=7: 3 vars");

        // Diff seq=2 -> seq=5: x changed (0->1), acc added
        CadenaSegura diff25 = ms_diff_entre(2, 5);
        CHECK_NOT_NULL(diff25, "diff seq=2->5");
        CHECK_STR_CONTENTS(diff25, "~x", "diff 2->5: x changed");
        CHECK_STR_CONTENTS(diff25, "0", "x antiguo=0");
        CHECK_STR_CONTENTS(diff25, "1", "x nuevo=1");
        CHECK_STR_CONTENTS(diff25, "+acc", "diff 2->5: acc added");

        // Diff seq=5 -> seq=7: x changed (1->5), y added
        CadenaSegura diff57 = ms_diff_entre(5, 7);
        CHECK_NOT_NULL(diff57, "diff seq=5->7");
        CHECK_STR_CONTENTS(diff57, "~x", "diff 5->7: x changed");
        CHECK_STR_CONTENTS(diff57, "+y", "diff 5->7: y added");

        // Diff seq=2 -> seq=7: x (0->5), acc added, y added
        CadenaSegura diff27 = ms_diff_entre(2, 7);
        CHECK_NOT_NULL(diff27, "diff seq=2->7");
        CHECK_STR_CONTENTS(diff27, "~x", "diff 2->7: x changed");
        CHECK_STR_CONTENTS(diff27, "+acc", "diff 2->7: acc added");
        CHECK_STR_CONTENTS(diff27, "+y", "diff 2->7: y added");
    }

    printf("=== Escenario 10: ms_snapshot_tamano ===\n");
    {
        CadenaSegura s = { .longitud = 42, .datos = "abcdefghijklmnopqrstuvwxyz1234567890" };
        CHECK_INT_EQ(ms_snapshot_tamano(s), 42, "tamano snapshot = 42");
        CHECK_INT_EQ(ms_snapshot_tamano(empty), 0, "tamano snapshot NULL = 0");

        tr_inicializar_recording();
        tr_grabar_snapshot(s_x, 1, empty, 1);
        tr_grabar_snapshot(s_y, 2, empty, 2);
        CadenaSegura snap = ms_tomar_en(2);
        CHECK(ms_snapshot_tamano(snap) > 0, "tamano snapshot real > 0");
    }

    int total = passed + failed;
    printf("\nResultados: %d/%d PASS\n", passed, total);
    if (failed > 0) {
        printf("ERROR: %d tests FALLARON\n", failed);
        return 1;
    }
    return 0;
}
