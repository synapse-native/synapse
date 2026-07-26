// M9.2 — Reversible Breakpoints & Historical Snapshot Inspection
// Tests for rp_* engine (replay inverso, breakpoints, inspeccion)
// Compile: gcc -I. -I../compilador -o test_reversible_debug test_reversible_debug.c ../synapse_rt.c -lm -lws2_32 -static
// Run: ./test_reversible_debug

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
extern int tr_grabar_bifurcacion(int linea, int rama, CadenaSegura id_funcion);
extern int tr_grabar_snapshot(CadenaSegura nombre_variable, long long valor_entero,
                               CadenaSegura valor_texto, int linea);
extern int tr_grabar_llamada(CadenaSegura funcion, int linea, int num_args);
extern int tr_grabar_retorno(CadenaSegura funcion, int linea);
extern int tr_grabar_error(CadenaSegura mensaje, int linea);
extern int tr_total_eventos(void);

extern int rp_inicializar(void);
extern int rp_establecer_breakpoint(int tipo, CadenaSegura patron, int valor_int);
extern int rp_eliminar_breakpoint(int id);
extern int rp_limpiar_breakpoints(void);
extern int rp_buscar_breakpoint(int id);
extern int rp_retroceder(int pasos, int desde_evento);
extern int rp_posicion_actual(void);
extern int rp_ir_a_pre_error(void);
extern CadenaSegura rp_inspeccionar_variable(int indice_evento, CadenaSegura nombre);
extern CadenaSegura rp_pila_llamadas(int indice_evento);
extern int rp_buscar_cambio_variable(CadenaSegura nombre, int valor);

#define RP_MAX_BREAKPOINTS 16

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
        printf("  [FAIL] %s: se esperaba NULL (datos=%p)\n", msg, (ptr).datos); \
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
    CadenaSegura s_foo = { .longitud = 3, .datos = "foo" };
    CadenaSegura s_bar = { .longitud = 3, .datos = "bar" };
    CadenaSegura s_loop = { .longitud = 4, .datos = "loop" };
    CadenaSegura s_x = { .longitud = 1, .datos = "x" };
    CadenaSegura s_y = { .longitud = 1, .datos = "y" };
    CadenaSegura s_z = { .longitud = 1, .datos = "z" };
    CadenaSegura s_a = { .longitud = 1, .datos = "a" };
    CadenaSegura s_b = { .longitud = 1, .datos = "b" };
    CadenaSegura s_w = { .longitud = 1, .datos = "w" };
    CadenaSegura s_i = { .longitud = 1, .datos = "i" };
    CadenaSegura s_acc = { .longitud = 3, .datos = "acc" };
    CadenaSegura s_v = { .longitud = 1, .datos = "v" };
    CadenaSegura s_ignored = { .longitud = 7, .datos = "ignored" };
    CadenaSegura s_empty_str = { .longitud = 0, .datos = "" };
    CadenaSegura s_hello = { .longitud = 5, .datos = "hello" };
    CadenaSegura s_error = { .longitud = 7, .datos = "error!" };

    printf("=== Escenario 1: Inicializacion y breakpoints por linea ===\n");
    {
        tr_inicializar_recording();
        CHECK_INT_EQ(rp_inicializar(), 0, "rp_inicializar ok");

        tr_grabar_bifurcacion(100, 1, s_main);
        tr_grabar_bifurcacion(200, 0, s_main);
        tr_grabar_snapshot(s_x, 42, empty, 300);
        tr_grabar_llamada(s_foo, 400, 2);
        tr_grabar_retorno(s_foo, 500);

        int bp1 = rp_establecer_breakpoint(0, s_ignored, 300);
        CHECK_INT_EQ(bp1, 0, "breakpoint por linea id=0");
        CHECK(rp_buscar_breakpoint(bp1) >= 0, "buscar_breakpoint por linea encontrado");
        CHECK(tr_total_eventos() >= 3, "total eventos >= 3");
        CHECK_INT_EQ(rp_limpiar_breakpoints(), 0, "limpiar_breakpoints ok");
    }

    printf("=== Escenario 2: Breakpoints por variable ===\n");
    {
        tr_inicializar_recording();
        rp_inicializar();

        tr_grabar_snapshot(s_x, 42, empty, 10);
        tr_grabar_snapshot(s_y, 99, empty, 20);
        tr_grabar_snapshot(s_x, 7, empty, 30);
        tr_grabar_snapshot(s_z, -1, empty, 40);
        tr_grabar_bifurcacion(50, 1, s_main);

        int bp_x = rp_establecer_breakpoint(1, s_x, 0);
        CHECK_INT_EQ(bp_x, 0, "breakpoint variable 'x' id=0");
        CHECK(rp_buscar_breakpoint(bp_x) >= 0, "buscar_breakpoint variable 'x' encontrado");

        int pos = rp_retroceder(1, -1);
        CHECK(pos >= 0, "retroceder 1 paso desde el final");
        CHECK_INT_EQ(pos, tr_total_eventos() - 2, "posicion = anteultimo evento");

        CHECK_INT_EQ(rp_limpiar_breakpoints(), 0, "limpiar_breakpoints ok");
    }

    printf("=== Escenario 3: Breakpoints por tag ===\n");
    {
        tr_inicializar_recording();
        rp_inicializar();

        tr_grabar_bifurcacion(10, 0, s_main);
        tr_grabar_snapshot(s_a, 1, empty, 20);
        tr_grabar_bifurcacion(30, 1, s_foo);
        tr_grabar_snapshot(s_b, 2, empty, 40);
        tr_grabar_error(s_error, 50);

        int bp_error = rp_establecer_breakpoint(2, empty, 3);
        CHECK_INT_EQ(bp_error, 0, "breakpoint tag EVENT_ERROR id=0");
        CHECK(rp_buscar_breakpoint(bp_error) >= 0, "buscar_breakpoint tag error encontrado");

        int bp_branch = rp_establecer_breakpoint(2, empty, 4);
        CHECK_INT_EQ(bp_branch, 1, "breakpoint tag EVENT_BRANCH id=1");
        CHECK(rp_buscar_breakpoint(bp_branch) >= 0, "buscar_breakpoint tag branch encontrado");

        CHECK_INT_EQ(rp_eliminar_breakpoint(0), 0, "eliminar_breakpoint(0) ok");
        CHECK(rp_buscar_breakpoint(0) >= 0, "buscar_breakpoint tras eliminacion (compactado)");
        CHECK_INT_EQ(rp_limpiar_breakpoints(), 0, "limpiar_breakpoints ok");
    }

    printf("=== Escenario 4: rp_retroceder ===\n");
    {
        tr_inicializar_recording();
        rp_inicializar();

        int n_events = 10;
        for (int i = 0; i < n_events; i++)
            tr_grabar_bifurcacion(i * 10, i % 2, s_loop);
        CHECK_INT_EQ(tr_total_eventos(), n_events, "10 eventos grabados");

        int pos = rp_retroceder(3, -1);
        CHECK_INT_EQ(pos, n_events - 1 - 3, "retroceder 3 desde el final");

        pos = rp_retroceder(0, pos);
        CHECK_INT_EQ(pos, n_events - 1 - 3, "retroceder 0 mantiene posicion");

        pos = rp_retroceder(999, -1);
        CHECK_INT_EQ(pos, -1, "retroceder 999 llega al inicio (-1)");

        pos = rp_retroceder(2, 5);
        CHECK_INT_EQ(pos, 3, "retroceder 2 desde pos=5 da pos=3");

        pos = rp_retroceder(0, -1);
        CHECK_INT_EQ(pos, n_events - 1, "retroceder 0 desde -1 da ultimo evento");

        CHECK_INT_EQ(rp_posicion_actual(), n_events - 1, "posicion_actual = ultimo evento");
    }

    printf("=== Escenario 5: rp_ir_a_pre_error ===\n");
    {
        tr_inicializar_recording();
        rp_inicializar();

        tr_grabar_bifurcacion(10, 1, s_main);
        tr_grabar_snapshot(s_x, 42, empty, 20);
        tr_grabar_llamada(s_foo, 30, 1);
        tr_grabar_error(s_error, 40);
        tr_grabar_bifurcacion(50, 0, s_main);

        int pre = rp_ir_a_pre_error();
        CHECK(pre >= 0, "ir_a_pre_error >= 0");
        CHECK_INT_EQ(pre, 2, "pre-error es el indice 2 (llamada a foo)");
        CHECK_INT_EQ(rp_posicion_actual(), pre, "posicion_actual = pre-error");

        tr_inicializar_recording();
        rp_inicializar();
        tr_grabar_bifurcacion(10, 1, s_main);
        CHECK_INT_EQ(rp_ir_a_pre_error(), -1, "sin error: ir_a_pre_error = -1");
    }

    printf("=== Escenario 6: rp_inspeccionar_variable ===\n");
    {
        tr_inicializar_recording();
        rp_inicializar();

        tr_grabar_snapshot(s_x, 42, empty, 10);
        tr_grabar_snapshot(s_y, 99, empty, 20);
        tr_grabar_snapshot(s_x, 7, s_hello, 30);
        tr_grabar_bifurcacion(40, 1, s_main);

        CadenaSegura val_x0 = rp_inspeccionar_variable(0, s_x);
        CHECK_NOT_NULL(val_x0, "x en evento 0 no es NULL");
        CHECK_STR_CONTENTS(val_x0, "42", "x en evento 0 contiene '42'");

        CadenaSegura val_x2 = rp_inspeccionar_variable(2, s_x);
        CHECK_NOT_NULL(val_x2, "x en evento 2 no es NULL");
        CHECK_STR_CONTENTS(val_x2, "hello", "x en evento 2 contiene 'hello'");

        CadenaSegura val_y1 = rp_inspeccionar_variable(1, s_y);
        CHECK_NOT_NULL(val_y1, "y en evento 1 no es NULL");
        CHECK_STR_CONTENTS(val_y1, "99", "y en evento 1 contiene '99'");

        CHECK_NULL(rp_inspeccionar_variable(0, s_w), "variable 'w' no existe -> NULL");
        CHECK_NOT_NULL(rp_inspeccionar_variable(3, s_x), "evento bifurcacion busca x hacia atras");
        CHECK_NULL(rp_inspeccionar_variable(0, empty), "nombre vacio -> NULL");
    }

    printf("=== Escenario 7: rp_pila_llamadas ===\n");
    {
        tr_inicializar_recording();
        rp_inicializar();

        tr_grabar_llamada(s_main, 10, 0);
        tr_grabar_bifurcacion(20, 1, s_main);
        tr_grabar_llamada(s_foo, 30, 2);
        tr_grabar_snapshot(s_x, 10, empty, 40);
        tr_grabar_llamada(s_bar, 50, 1);
        tr_grabar_bifurcacion(60, 0, s_bar);
        tr_grabar_retorno(s_bar, 70);
        tr_grabar_retorno(s_foo, 80);

        CadenaSegura stack5 = rp_pila_llamadas(5);
        CHECK_NOT_NULL(stack5, "pila_llamadas(5) no es NULL");
        CHECK(strlen(stack5.datos) > 0, "pila_llamadas(5) no vacia");
        CHECK_STR_CONTENTS(stack5, "bar", "pila(5) contiene 'bar'");
        CHECK_STR_CONTENTS(stack5, "foo", "pila(5) contiene 'foo'");

        CadenaSegura stack0 = rp_pila_llamadas(0);
        CHECK_NOT_NULL(stack0, "pila_llamadas(0) no es NULL");
        CHECK_STR_CONTENTS(stack0, "main", "pila(0) contiene 'main'");

        CadenaSegura stack2 = rp_pila_llamadas(2);
        CHECK_NOT_NULL(stack2, "pila_llamadas(2) no es NULL");
        CHECK_STR_CONTENTS(stack2, "foo", "pila(2) contiene 'foo'");

        CHECK_NULL(rp_pila_llamadas(-1), "pila_llamadas(-1) -> NULL");
        CHECK_NULL(rp_pila_llamadas(9999), "pila_llamadas(9999) -> NULL");
    }

    printf("=== Escenario 8: rp_buscar_cambio_variable ===\n");
    {
        tr_inicializar_recording();
        rp_inicializar();

        tr_grabar_snapshot(s_x, 1, empty, 10);
        tr_grabar_snapshot(s_y, 2, empty, 20);
        tr_grabar_snapshot(s_x, 42, empty, 30);
        tr_grabar_snapshot(s_z, 3, empty, 40);
        tr_grabar_snapshot(s_x, 99, empty, 50);

        CHECK_INT_EQ(rp_buscar_cambio_variable(s_x, 42), 2, "x=42 en indice 2");
        CHECK_INT_EQ(rp_buscar_cambio_variable(s_x, 99), 4, "x=99 en indice 4");
        CHECK_INT_EQ(rp_buscar_cambio_variable(s_x, 999), -1, "x=999 no existe");
        CHECK_INT_EQ(rp_buscar_cambio_variable(s_w, 0), -1, "variable 'w' no existe");
        CHECK_INT_EQ(rp_buscar_cambio_variable(empty, 0), -1, "nombre vacio -> -1");
    }

    printf("=== Escenario 9: Edge cases — limites ===\n");
    {
        tr_inicializar_recording();
        rp_inicializar();

        int ids[RP_MAX_BREAKPOINTS];
        int count = 0;
        for (int i = 0; i < RP_MAX_BREAKPOINTS + 5; i++) {
            int id = rp_establecer_breakpoint(0, empty, i);
            if (id >= 0) ids[count++] = id;
            else break;
        }
        CHECK_INT_EQ(count, RP_MAX_BREAKPOINTS, "max breakpoints = RP_MAX_BREAKPOINTS");

        CHECK_INT_EQ(rp_limpiar_breakpoints(), 0, "limpiar_breakpoints ok");
        CHECK_INT_EQ(rp_establecer_breakpoint(1, s_x, 0), 0, "breakpoint tras limpiar");
        CHECK_INT_EQ(rp_establecer_breakpoint(99, empty, 0), -1, "tipo invalido -> -1");
        CHECK_INT_EQ(rp_eliminar_breakpoint(99), -1, "eliminar id=99 -> -1");
        CHECK_INT_EQ(rp_limpiar_breakpoints(), 0, "limpiar_breakpoints ok");
    }

    printf("=== Escenario 10: Workflow completo — error, retroceso, inspeccion ===\n");
    {
        tr_inicializar_recording();
        rp_inicializar();

        tr_grabar_llamada(s_main, 1, 0);
        tr_grabar_snapshot(s_i, 0, empty, 2);
        tr_grabar_snapshot(s_i, 1, empty, 3);
        tr_grabar_bifurcacion(4, 1, s_main);
        tr_grabar_snapshot(s_i, 2, empty, 5);
        tr_grabar_snapshot(s_acc, 100, empty, 6);
        tr_grabar_error(s_error, 7);

        int pre = rp_ir_a_pre_error();
        CHECK(pre >= 0, "pre-error encontrado");
        CHECK_INT_EQ(pre, 5, "pre-error = indice 5 (acc=100)");

        CadenaSegura acc_val = rp_inspeccionar_variable(pre, s_acc);
        CHECK_NOT_NULL(acc_val, "acc en pre-error no es NULL");
        CHECK_STR_CONTENTS(acc_val, "100", "acc = 100 en pre-error");

        CadenaSegura i_val = rp_inspeccionar_variable(pre, s_i);
        CHECK_NOT_NULL(i_val, "i en pre-error no es NULL");

        CadenaSegura pre_stack = rp_pila_llamadas(pre);
        CHECK_NOT_NULL(pre_stack, "pila en pre-error no es NULL");
        CHECK_STR_CONTENTS(pre_stack, "main", "pila contiene 'main'");

        int step_back = rp_retroceder(1, pre);
        CHECK_INT_EQ(step_back, 4, "retroceder 1 desde pre-error = 4");

        CadenaSegura i_before = rp_inspeccionar_variable(step_back, s_i);
        CHECK_NOT_NULL(i_before, "i en step_back no es NULL");
        CHECK_STR_CONTENTS(i_before, "2", "i = 2 en step_back");

        CHECK_INT_EQ(rp_buscar_cambio_variable(s_i, 1), 2, "i=1 en indice 2");
        CHECK_INT_EQ(rp_buscar_cambio_variable(s_acc, 100), 5, "acc=100 en indice 5");
    }

    int total = passed + failed;
    printf("\nResultados: %d/%d PASS\n", passed, total);
    if (failed > 0) {
        printf("ERROR: %d tests FALLARON\n", failed);
        return 1;
    }
    return 0;
}
