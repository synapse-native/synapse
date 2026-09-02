// FASE 23 ME-2: rc<T> + arc<T> reference counting test (Manual 4 §3.2-3.3)
// Auto-compilado por conftest.py via _RT_BINARIOS_EXTRA -> test_rc_arc.exe
// Compila: gcc -O2 -I. -I.. -c tests/test_rc_arc.c -o ...
//          gcc -O2 -I. -o test_rc_arc.exe test_rc_arc.o synapse_rt_memory.o -lm -lpthread -lws2_32
// Verifica: rc_alloc/inc/dec, arc_alloc/inc/dec, move semantics, NULL safety

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdint.h>
#include "synapse_rt_types.h"

static int passed = 0;
static int failed = 0;

#define CHECK(cond, msg) do { \
    if (!(cond)) { printf("  [FAIL] %s\n", msg); failed++; } \
    else { printf("  [PASS] %s\n", msg); passed++; } \
} while(0)

#define CHECK_INT_EQ(a, b, msg) do { \
    if ((a) != (b)) { printf("  [FAIL] %s: esperado %ld, obtenido %ld\n", msg, (long)(b), (long)(a)); failed++; } \
    else { printf("  [PASS] %s\n", msg); passed++; } \
} while(0)

// Destructor de prueba: marca que fue llamado
static int destructor_called = 0;
static void test_destructor(void* ptr) {
    (void)ptr;
    destructor_called++;
}

int main(void) {
    setbuf(stdout, NULL);

    // ===== 1. rc_alloc básico =====
    printf("=== 1. rc_alloc basico ===\n");
    destructor_called = 0;
    void* r = rc_alloc(100, test_destructor);
    CHECK(r != NULL, "rc_alloc retorna no-NULL");
    RcHeader* rh = (RcHeader*)((uint8_t*)r - sizeof(RcHeader));
    CHECK_INT_EQ(rh->ref_count, 1, "ref_count inicial = 1");
    CHECK_INT_EQ(rh->weak_count, 0, "weak_count inicial = 0");
    CHECK_INT_EQ(rh->destructor == test_destructor, 1, "destructor registrado");

    // Escribir datos
    memset(r, 0xAB, 100);
    CHECK(((unsigned char*)r)[0] == 0xAB, "datos escribibles");
    CHECK(((unsigned char*)r)[99] == 0xAB, "datos en offset 99");

    // ===== 2. rc_incrementar / rc_decrementar =====
    printf("=== 2. rc_incrementar/decrementar ===\n");
    rc_incrementar(r);
    CHECK_INT_EQ(rh->ref_count, 2, "ref_count = 2 tras inc");
    rc_incrementar(r);
    CHECK_INT_EQ(rh->ref_count, 3, "ref_count = 3 tras segundo inc");

    rc_decrementar(r);
    CHECK_INT_EQ(rh->ref_count, 2, "ref_count = 2 tras dec");
    rc_decrementar(r);
    CHECK_INT_EQ(rh->ref_count, 1, "ref_count = 1 tras segundo dec");
    CHECK_INT_EQ(destructor_called, 0, "destructor no llamado (ref_count > 0)");

    rc_decrementar(r);
    CHECK_INT_EQ(destructor_called, 1, "destructor llamado al llegar a 0");

    // ===== 3. rc_decrementar con NULL (seguridad) =====
    printf("=== 3. NULL safety ===\n");
    rc_incrementar(NULL);  // no debe crashar
    rc_decrementar(NULL);  // no debe crashar
    printf("  [PASS] rc_incrementar(NULL) y rc_decrementar(NULL) no crashean\n");
    passed++;

    // ===== 4. arc_alloc básico (atómico) =====
    printf("=== 4. arc_alloc basico ===\n");
    void* a = arc_alloc(64, NULL);
    CHECK(a != NULL, "arc_alloc retorna no-NULL");
    ArcHeader* ah = (ArcHeader*)((uint8_t*)a - sizeof(ArcHeader));
    CHECK_INT_EQ(ah->ref_count, 1, "arc ref_count inicial = 1");
    CHECK_INT_EQ(ah->destructor == NULL, 1, "arc destructor = NULL");
    memset(a, 0xCD, 64);
    CHECK(((unsigned char*)a)[0] == 0xCD, "arc datos escribibles");

    // ===== 5. arc_incrementar / arc_decrementar (atomic) =====
    printf("=== 5. arc_incrementar/decrementar ===\n");
    for (int i = 0; i < 100; i++) {
        arc_incrementar(a);
    }
    CHECK_INT_EQ(ah->ref_count, 101, "arc ref_count = 101 tras 100 incs");

    for (int i = 0; i < 100; i++) {
        arc_decrementar(a);
    }
    CHECK_INT_EQ(ah->ref_count, 1, "arc ref_count = 1 tras 100 decs");
    CHECK_INT_EQ(ah->ref_count == 1, 1, "arc no liberado (ref_count > 0)");

    arc_decrementar(a);  // último dec → free
    printf("  [PASS] arc liberado al final\n");
    passed++;

    // ===== 6. NULL safety para arc =====
    printf("=== 6. arc NULL safety ===\n");
    arc_incrementar(NULL);
    arc_decrementar(NULL);
    printf("  [PASS] arc_incrementar(NULL) y arc_decrementar(NULL) no crashean\n");
    passed++;

    // ===== 7. Move semantics (transferir ownership) =====
    printf("=== 7. Move semantics ===\n");
    destructor_called = 0;
    void* src = rc_alloc(32, test_destructor);
    void* dst = src;  // move: NO incrementar
    src = NULL;       // fuente invalidada (no decrementar)
    CHECK_INT_EQ(destructor_called, 0, "destructor no llamado tras move (dst owns)");
    rc_decrementar(dst);
    CHECK_INT_EQ(destructor_called, 1, "destructor llamado al final del move");

    // ===== 8. Shared ownership (multiple incs) =====
    printf("=== 8. Shared ownership ===\n");
    destructor_called = 0;
    void* s1 = rc_alloc(16, test_destructor);
    void* s2 = s1;
    void* s3 = s1;
    rc_incrementar(s2);  // compartir
    rc_incrementar(s3);  // compartir
    rc_decrementar(s1);
    CHECK_INT_EQ(destructor_called, 0, "no liberado (3 refs)");
    rc_decrementar(s2);
    CHECK_INT_EQ(destructor_called, 0, "no liberado (1 ref restante)");
    rc_decrementar(s3);
    CHECK_INT_EQ(destructor_called, 1, "liberado al ultimo decremento");

    printf("\n=== RESULTADO: %d passed, %d failed ===\n", passed, failed);
    return failed > 0 ? 1 : 0;
}
