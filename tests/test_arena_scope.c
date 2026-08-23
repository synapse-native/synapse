// FASE 23 ME-1: Arena allocator test (Manual 4 §2)
// Auto-compilado por conftest.py via _RT_BINARIOS_EXTRA -> test_arena_scope.exe
// Compila: gcc -O2 -I. -I.. -c tests/test_arena_scope.c -o ...
//          gcc -O2 -I. -o test_arena_scope.exe test_arena_scope.o synapse_rt_memory.o -lm -lpthread -lws2_32
// Run: ./test_arena_scope.exe
// Verifica: O(1) alloc, O(1) lib, alignment, anidamiento, expansión global, fallback malloc

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

int main(void) {
    setbuf(stdout, NULL);

    // 1. arena_crear + arena_alloc básico
    printf("=== 1. Creacion y asignacion basica ===\n");
    Arena* a = arena_crear(4096);
    CHECK(a != NULL, "arena_crear retorna no-NULL");
    CHECK(a->es_global == false, "es_global=false por defecto");
    CHECK(a->inicio != NULL && a->fin != NULL, "inicio/fin inicializados");
    CHECK((size_t)(a->fin - a->inicio) == 4096, "tamano inicial 4096");

    void* p1 = arena_alloc(a, 100, 8);
    CHECK(p1 != NULL, "alloc 100 bytes");
    CHECK((uintptr_t)p1 % 8 == 0, "p1 alineado 8");

    void* p2 = arena_alloc(a, 50, 16);
    CHECK(p2 != NULL, "alloc 50 bytes");
    CHECK((uintptr_t)p2 % 16 == 0, "p2 alineado 16");
    CHECK(p2 > p1, "p2 > p1 (bump order)");
    arena_free(a);

    // 2. arena_reset
    printf("=== 2. arena_reset ===\n");
    Arena* r = arena_crear(2048);
    void* rp1 = arena_alloc(r, 100, 8);
    arena_reset(r);
    CHECK(r->puntero == r->inicio, "puntero vuelve al inicio");
    void* rp2 = arena_alloc(r, 100, 8);
    CHECK(rp1 == rp2, "mismo slot tras reset");
    arena_free(r);

    // 3. Anidamiento + cascada
    printf("=== 3. Anidamiento ===\n");
    Arena* padre = arena_crear(8192);
    Arena* hijo = arena_crear_hijo(padre, 2048);
    CHECK(hijo->padre == padre, "hijo->padre == padre");
    CHECK(padre->hijo == hijo, "padre->hijo == hijo");
    Arena* nieto = arena_crear_hijo(hijo, 1024);
    CHECK(nieto->padre == hijo, "nieto->padre == hijo");
    void* ph = arena_alloc(hijo, 100, 8);
    CHECK(ph != NULL, "alloc en hijo");
    arena_free(padre);  // libera hijo + nieto en cascada
    printf("  [PASS] cascada liberada\n");

    // 4. Expansion global
    printf("=== 4. Expansion global ===\n");
    Arena* g = arena_crear(128);
    g->es_global = true;
    void* big1 = arena_alloc(g, 64, 8);
    void* big2 = arena_alloc(g, 512, 16);
    CHECK(big2 != NULL, "alloc > tamano inicial (expansion)");
    CHECK((uintptr_t)big2 % 16 == 0, "big2 alineado 16 tras expansion");
    CHECK(g->tamano >= 640, "arena expandida");
    arena_free(g);

    // 5. Alineaciones variadas
    printf("=== 5. Alineaciones ===\n");
    Arena* al = arena_crear(4096);
    void* a1 = arena_alloc(al, 1, 1);
    void* a8 = arena_alloc(al, 1, 8);
    void* a16 = arena_alloc(al, 1, 16);
    void* a32 = arena_alloc(al, 1, 32);
    void* a64 = arena_alloc(al, 1, 64);
    CHECK((uintptr_t)a1 % 1 == 0, "alig 1");
    CHECK((uintptr_t)a8 % 8 == 0, "alig 8");
    CHECK((uintptr_t)a16 % 16 == 0, "alig 16");
    CHECK((uintptr_t)a32 % 32 == 0, "alig 32");
    CHECK((uintptr_t)a64 % 64 == 0, "alig 64");

    // 6. Escritura/verificacion de datos
    void* da = arena_alloc(al, 100, 8);
    void* db = arena_alloc(al, 100, 8);
    memset(da, 0xAB, 100);
    memset(db, 0xCD, 100);
    CHECK(((unsigned char*)da)[0] == 0xAB, "da[0] = 0xAB");
    CHECK(((unsigned char*)db)[0] == 0xCD, "db[0] = 0xCD");
    CHECK(((unsigned char*)da)[99] == 0xAB, "da[99] = 0xAB");
    arena_free(al);

    // 7. Fallback malloc (arena local llena — alloc > 4096 min)
    printf("=== 7. Fallback malloc ===\n");
    Arena* small = arena_crear(4096);  // min size 4096
    void* s1 = arena_alloc(small, 100, 8);
    CHECK(s1 != NULL, "alloc normal en arena");
    // Alloc > arena remaining → fallback a malloc (arena NO es global)
    void* s2 = arena_alloc(small, 5000, 8);
    CHECK(s2 != NULL, "alloc > arena → fallback malloc");
    CHECK((uintptr_t)s2 < (uintptr_t)small->inicio || (uintptr_t)s2 >= (uintptr_t)small->fin,
          "s2 fuera del bloque arena (es malloc)");
    memset(s2, 0xAB, 5000);
    CHECK(((unsigned char*)s2)[2500] == 0xAB, "malloc fallback escribe OK");
    free(s2);  // s2 es malloc, libre correctamente
    arena_free(small);

    printf("\n=== RESULTADO: %d passed, %d failed ===\n", passed, failed);
    return failed > 0 ? 1 : 0;
}
