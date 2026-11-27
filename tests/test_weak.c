// FASE 23 ME-3: débil<T> WeakRef test (Manual 4 §4.2)
// Auto-compilado por conftest.py via _RT_BINARIOS_EXTRA -> test_weak.exe
// Verifica: creación weak, upgrade exitoso, upgrade tras free (invalidation),
// cascade: header sobrevive a weak refs, freed al último release

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdint.h>
#include "synapse_rt_types.h"

static int passed = 0;
static int failed = 0;
static int destructor_calls = 0;

#define CHECK(cond, msg) do { \
    if (!(cond)) { printf("  [FAIL] %s\n", msg); failed++; } \
    else { printf("  [PASS] %s\n", msg); passed++; } \
} while(0)

#define CHECK_INT_EQ(a, b, msg) do { \
    if ((a) != (b)) { printf("  [FAIL] %s: esperado %d, obtenido %d\n", msg, (int)(b), (int)(a)); failed++; } \
    else { printf("  [PASS] %s\n", msg); passed++; } \
} while(0)

static void test_destructor(void* ptr) {
    (void)ptr;
    destructor_calls++;
}

int main(void) {
    setbuf(stdout, NULL);

    // 1. Creación de weak ref y upgrade exitoso
    printf("=== 1. WeakRef creacion + upgrade ===\n");
    destructor_calls = 0;
    void* rc = rc_alloc(64, test_destructor);
    WeakRef w = rc_weak_ref(rc);
    CHECK(w.header != NULL, "weak ref creada (header != NULL)");
    CHECK(w.version == 0, "version inicial = 0");

    RcHeader* h = (RcHeader*)((uint8_t*)rc - sizeof(RcHeader));
    CHECK_INT_EQ(h->weak_count, 1, "weak_count = 1 tras rc_weak_ref");

    void* upgraded = rc_weak_upgrade(&w);
    CHECK(upgraded != NULL, "upgrade exitoso (objeto vivo)");
    CHECK(upgraded == rc, "upgrade retorna mismo data pointer");
    CHECK_INT_EQ(h->ref_count, 2, "ref_count = 2 tras upgrade");
    rc_decrementar(upgraded);  // release upgrade
    CHECK_INT_EQ(h->ref_count, 1, "ref_count = 1 tras release upgrade");
    rc_decrementar(rc);        // release original
    // ref_count = 0, pero weak_count > 0 → header sobrevive

    // 2. Upgrade tras free (invalidation)
    printf("=== 2. WeakRef invalidation tras free ===\n");
    // El header sobrevive con version=1, ref_count=0
    CHECK(h->version == 1, "version incremented tras ref_count→0");
    CHECK_INT_EQ(h->ref_count, 0, "ref_count = 0 tras free fuerte");
    CHECK_INT_EQ(h->weak_count, 1, "weak_count = 1 (header sobrevive)");

    void* dead = rc_weak_upgrade(&w);
    CHECK(dead == NULL, "upgrade falla (objeto destruido)");

    // 3. Liberación de weak → header freed
    printf("=== 3. WeakRef release libera header ===\n");
    CHECK_INT_EQ(destructor_calls, 1, "destructor llamado al free fuerte");
    rc_weak_release(&w);
    CHECK(w.header == NULL, "weak ref invalidada tras release");
    printf("  [PASS] header liberado tras release de weak (no acceso a memoria libre)\n");
    passed++;

    // 4. WeakRef NULL safety
    printf("=== 4. WeakRef NULL safety ===\n");
    {
        WeakRef nula = { .header = NULL, .version = 0 };
        void* r = rc_weak_upgrade(&nula);
        CHECK(r == NULL, "upgrade de weak NULL retorna NULL");
        rc_weak_release(&nula);  // no crashea
        CHECK(nula.header == NULL, "weak NULL sigue NULL tras release");
        printf("  [PASS] NULL safety OK\n");
        passed++;
    }

    // 5. Arc weak ref
    printf("=== 5. ArcWeakRef ===\n");
    destructor_calls = 0;
    void* a = arc_alloc(32, test_destructor);
    WeakRef aw = arc_weak_ref(a);
    CHECK(aw.header != NULL, "arc_weak_ref creada");
    CHECK(aw.version == 0, "arc version = 0");
    ArcHeader* ah = (ArcHeader*)aw.header;
    CHECK_INT_EQ(__atomic_load_n(&ah->weak_count, __ATOMIC_ACQUIRE), 1, "arc weak_count = 1");

    void* au = arc_weak_upgrade(&aw);
    CHECK(au != NULL && au == a, "arc upgrade exitoso");
    arc_decrementar(au);
    arc_decrementar(a);
    CHECK_INT_EQ(__atomic_load_n(&ah->ref_count, __ATOMIC_ACQUIRE), 0, "arc ref_count=0 tras free");
    CHECK(__atomic_load_n(&ah->version, __ATOMIC_ACQUIRE) == 1, "arc header version incremented tras free");

    void* dead_a = arc_weak_upgrade(&aw);
    CHECK(dead_a == NULL, "arc upgrade falla (destruido)");
    arc_weak_release(&aw);
    CHECK(aw.header == NULL, "arc weak release OK");

    // 6. WeakRef sin crear (directamente NULL)
    printf("=== 6. WeakRef default ===\n");
    {
        WeakRef vacia = rc_weak_ref(NULL);
        CHECK(vacia.header == NULL, "weak_ref(NULL) retorna header=NULL");
        rc_weak_release(&vacia);  // no crashea
        printf("  [PASS] weak_ref(NULL) OK\n");
        passed++;
    }

    printf("\n=== RESULTADO: %d passed, %d failed ===\n", passed, failed);
    return failed > 0 ? 1 : 0;
}
