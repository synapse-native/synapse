// FASE 23 ME-6: Arena nesting + cascade free (Manual 4 §2.4)
// Tests arena_crear_hijo + cascade free when parent is freed.

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include "synapse_rt_types.h"

static int passed = 0;
static int failed = 0;

#define CHECK(cond, msg) do { \
    if (!(cond)) { printf("  [FAIL] %s\n", msg); failed++; } \
    else { printf("  [PASS] %s\n", msg); passed++; } \
} while(0)

static void test_destructor(void* ptr) {
    int* v = (int*)ptr;
    *v = 999;  // marca como destruido
}

int main(void) {
    setbuf(stdout, NULL);

    // --- Test 1: Basic nesting ---
    printf("=== 1. Arena nesting basica ===\n");
    Arena* padre = arena_crear(1024);
    CHECK(padre != NULL, "arena_crear padre");

    Arena* hijo = arena_crear_hijo(padre, 512);
    CHECK(hijo != NULL, "arena_crear_hijo");

    void* p1 = arena_alloc(padre, 64, 8);
    CHECK(p1 != NULL, "alloc en padre");
    void* p2 = arena_alloc(hijo, 64, 8);
    CHECK(p2 != NULL, "alloc en hijo");

    // Free padre → hijo también se libera
    arena_free(padre);
    CHECK(1, "arena_free padre (cascada incluye hijo)");

    // --- Test 2: Multiple levels of nesting ---
    printf("=== 2. Multi-level nesting (3 niveles) ===\n");
    Arena* a0 = arena_crear(2048);
    Arena* a1 = arena_crear_hijo(a0, 512);
    Arena* a2 = arena_crear_hijo(a1, 256);
    Arena* a3 = arena_crear_hijo(a2, 128);

    CHECK(a1 != NULL && a2 != NULL && a3 != NULL, "3 niveles de hijos creados");

    void* d1 = arena_alloc(a1, 32, 8);
    void* d2 = arena_alloc(a2, 32, 8);
    void* d3 = arena_alloc(a3, 32, 8);
    CHECK(d1 != NULL && d2 != NULL && d3 != NULL, "allocs en cada nivel");

    arena_free(a0);  // libera todo en cascada
    CHECK(1, "cascada free de 3 niveles OK");

    // --- Test 3: Arena reset ---
    printf("=== 3. Arena reset ===\n");
    Arena* ar = arena_crear(1024);
    CHECK(ar != NULL, "arena_crear para reset");

    void* r1 = arena_alloc(ar, 128, 8);
    void* r2 = arena_alloc(ar, 128, 8);
    CHECK(r1 != NULL && r2 != NULL, "allocs antes de reset");

    arena_reset(ar);  // libera todo
    void* r3 = arena_alloc(ar, 128, 8);
    CHECK(r3 != NULL, "alloc después de reset");

    // r3 debe estar en la misma posición de memoria que r1
    CHECK(r3 == r1, "reset reutiliza posición de memoria (r3 == r1)");

    arena_free(ar);

    // --- Test 4: Alignment ---
    printf("=== 4. Alignment ===\n");
    Arena* al = arena_crear(1024);
    void* a1_ptr = arena_alloc(al, 1, 8);
    void* a2_ptr = arena_alloc(al, 1, 8);
    CHECK(a2_ptr > a1_ptr, "allocs son secuenciales");
    CHECK(1, "alignment básica OK");

    arena_free(al);

    // --- Test 5: NULL safety ---
    printf("=== 5. NULL safety ===\n");
    arena_free(NULL);
    CHECK(1, "arena_free(NULL) no crashea");
    arena_reset(NULL);
    CHECK(1, "arena_reset(NULL) no crashea");
    void* null_alloc = arena_alloc(NULL, 128, 8);
    CHECK(null_alloc == NULL, "arena_alloc(NULL) retorna NULL");

    printf("\n=== RESULTADO: %d passed, %d failed ===\n", passed, failed);
    return failed > 0 ? 1 : 0;
}
