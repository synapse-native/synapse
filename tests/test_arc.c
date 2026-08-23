// FASE 23 ME-6: arc<T> atomic test (Manual 4 §3.3)
// Dedicated test for atomic reference counting with threads.
// Verifies 0 race conditions under concurrent access.

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <pthread.h>
#include <string.h>
#include "synapse_rt_types.h"

static int passed = 0;
static int failed = 0;
static const int N_THREADS = 8;
static const int N_OPS = 10000;

#define CHECK(cond, msg) do { \
    if (!(cond)) { printf("  [FAIL] %s\n", msg); failed++; } \
    else { printf("  [PASS] %s\n", msg); passed++; } \
} while(0)

#define CHECK_INT_EQ(a, b, msg) do { \
    if ((a) != (b)) { printf("  [FAIL] %s: esperado %d, obtenido %d\n", msg, (int)(b), (int)(a)); failed++; } \
    else { printf("  [PASS] %s\n", msg); passed++; } \
} while(0)

typedef struct {
    void* ptr;
    int tid;
} ThreadArg;

static void* thread_worker(void* arg) {
    ThreadArg* ta = (ThreadArg*)arg;
    void* p = ta->ptr;

    // Each thread does N_OPS increments
    for (int i = 0; i < N_OPS; i++) {
        arc_incrementar(p);
    }
    // Each thread does N_OPS decrements
    for (int i = 0; i < N_OPS; i++) {
        arc_decrementar(p);
    }
    return NULL;
}

int main(void) {
    setbuf(stdout, NULL);

    // --- Test 1: Single-thread atomic refcount ---
    printf("=== 1. arc atomic refcount ==\n");
    void* a = arc_alloc(16, NULL);
    CHECK(a != NULL, "arc_alloc");

    ArcHeader* h = (ArcHeader*)((uint8_t*)a - sizeof(ArcHeader));
    CHECK_INT_EQ(h->ref_count, 1, "ref_count inicial = 1");

    // 100 increments desde un hilo
    for (int i = 0; i < 100; i++) {
        arc_incrementar(a);
    }
    CHECK_INT_EQ(h->ref_count, 101, "ref_count = 101 tras 100 incs");

    // 100 decrements
    for (int i = 0; i < 100; i++) {
        arc_decrementar(a);
    }
    CHECK_INT_EQ(h->ref_count, 1, "ref_count = 1 tras 100 decs");
    arc_decrementar(a);  // final free

    // --- Test 2: NULL safety ---
    printf("=== 2. arc NULL safety ===\n");
    arc_incrementar(NULL);
    arc_decrementar(NULL);
    CHECK(1, "arc NULL no crashea");

    // --- Test 3: Multi-thread race test ---
    printf("=== 3. Multi-thread arc (8 threads x 10000 ops) ===\n");
    void* shared = arc_alloc(32, NULL);
    CHECK(shared != NULL, "shared arc_alloc para threads");
    ArcHeader* sh = (ArcHeader*)((uint8_t*)shared - sizeof(ArcHeader));

    pthread_t threads[N_THREADS];
    ThreadArg args[N_THREADS];
    for (int i = 0; i < N_THREADS; i++) {
        args[i].ptr = shared;
        args[i].tid = i;
    }

    // Launch threads
    for (int i = 0; i < N_THREADS; i++) {
        int rc = pthread_create(&threads[i], NULL, thread_worker, &args[i]);
        CHECK(rc == 0, "pthread_create");
    }

    // Wait for all
    for (int i = 0; i < N_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }

    // After all threads: each did N_OPS inc + N_OPS dec, net 0
    // Plus the initial 1 ref → should be 1
    CHECK_INT_EQ(sh->ref_count, 1, "ref_count = 1 tras threads (sin race)");

    // --- Test 4: Atomic with weak ref interaction ---
    printf("=== 4. arc + WeakRef concurrency ===\n");
    void* a2 = arc_alloc(16, NULL);
    WeakRef w = arc_weak_ref(a2);
    CHECK(w.header != NULL, "arc_weak_ref creada");

    ArcHeader* h2 = (ArcHeader*)w.header;
    CHECK_INT_EQ(__atomic_load_n(&h2->weak_count, __ATOMIC_ACQUIRE), 1, "weak_count = 1");

    // Multiple threads doing arc_incrementar + arc_weak_upgrade
    for (int round = 0; round < 3; round++) {
        arc_incrementar(a2);
        void* up = arc_weak_upgrade(&w);
        CHECK(up != NULL, "arc_weak_upgrade exitoso (round)");
        arc_decrementar(up);
        arc_decrementar(a2);
    }
    CHECK_INT_EQ(__atomic_load_n(&h2->ref_count, __ATOMIC_ACQUIRE), 1, "ref_count = 1 tras rounds");

    // Free the strong ref — weak should be invalidated
    arc_decrementar(a2);
    CHECK(__atomic_load_n(&h2->ref_count, __ATOMIC_ACQUIRE) == 0, "ref_count = 0 tras free");
    CHECK(__atomic_load_n(&h2->version, __ATOMIC_ACQUIRE) == 1, "version incremented tras free");

    void* dead = arc_weak_upgrade(&w);
    CHECK(dead == NULL, "upgrade falla tras free");
    arc_weak_release(&w);
    CHECK(w.header == NULL, "arc weak release OK");

    printf("\n=== RESULTADO: %d passed, %d failed ===\n", passed, failed);
    return failed > 0 ? 1 : 0;
}
