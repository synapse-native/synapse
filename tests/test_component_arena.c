// FASE 23 — Test de Arenas de Componente (Manual 4 §6)
// TDD: este test ES la especificación. Si comp_arena_crear/comp_alloc/comp_destroy
// no existen, el test NO compila — eso es correcto. Se corrige el CÓDIGO, no el test.
//
// Manual 4 §6.3: ComponentArena struct (padre, hijos, num_hijos, ref_count,
//   marcado_para_liberar, destructor)
// Manual 4 §6.3: comp_arena_crear(Arena* padre, size_t tamano_inicial)
// Manual 4 §6.3: comp_alloc(ComponentArena* ca, size_t tamano)
// Manual 4 §6.3: comp_destroy(ComponentArena* ca) — libera componente y todos sus hijos
//
// Compila: gcc -O2 -I. -I.. -c tests/test_component_arena.c -o ...
//          gcc -O2 -I. -o test_component_arena.exe test_component_arena.o synapse_rt_memory.o -lm -lpthread -lws2_32

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

int main(void) {
    setbuf(stdout, NULL);

    // ================================================================
    // Manual 4 §6.3: comp_arena_crear — crear componente con arena propia
    // ================================================================
    printf("=== 1. comp_arena_crear ===\n");
    // Primer componente: sin padre (raíz)
    ComponentArena* comp = comp_arena_crear(NULL, 4096);
    CHECK(comp != NULL, "comp_arena_crear retorna no-NULL");
    CHECK(comp->arena != NULL, "comp->arena inicializada");
    CHECK(comp->padre == NULL, "comp->padre == NULL (raíz)");
    CHECK(comp->num_hijos == 0, "comp->num_hijos == 0");
    CHECK(comp->ref_count == 1, "comp->ref_count == 1");
    CHECK(comp->marcado_para_liberar == false, "marcado_para_liberar == false");

    // ================================================================
    // Manual 4 §6.3: comp_alloc — asignar en la arena del componente
    // ================================================================
    printf("=== 2. comp_alloc ===\n");
    void* widget1 = comp_alloc(comp, 128);
    CHECK(widget1 != NULL, "comp_alloc(128) retorna no-NULL");
    CHECK((uintptr_t)widget1 % 8 == 0, "widget1 alineado 8");
    memset(widget1, 0xAB, 128);
    CHECK(((unsigned char*)widget1)[0] == 0xAB, "widget1 escribe OK");

    void* widget2 = comp_alloc(comp, 256);
    CHECK(widget2 != NULL, "comp_alloc(256) retorna no-NULL");
    CHECK(widget2 > widget1, "widget2 > widget1 (bump order)");

    // ================================================================
    // Manual 4 §6.4: anidamiento — hijos heredan arena del padre
    // ================================================================
    printf("=== 3. Anidamiento de componentes ===\n");
    ComponentArena* child1 = comp_arena_crear(comp, 2048);
    CHECK(child1 != NULL, "child1 creado");
    CHECK(child1->padre == comp, "child1->padre == comp");
    CHECK(comp->num_hijos == 1, "comp->num_hijos == 1");

    ComponentArena* child2 = comp_arena_crear(comp, 2048);
    CHECK(child2 != NULL, "child2 creado");
    CHECK(comp->num_hijos == 2, "comp->num_hijos == 2");

    // Asignar en los hijos
    void* w_child1 = comp_alloc(child1, 64);
    void* w_child2 = comp_alloc(child2, 64);
    CHECK(w_child1 != NULL && w_child2 != NULL, "allocs en hijos OK");

    // ================================================================
    // Manual 4 §6.3: comp_destroy — liberación en masa de toda la jerarquía
    // ================================================================
    printf("=== 4. comp_destroy (liberación en masa) ===\n");
    comp_destroy(comp);
    // Si comp_destroy funciona correctamente:
    // - child1 y child2 se liberaron (cascada)
    // - sus arenas se liberaron
    // - comp->arena se liberó
    CHECK(1, "comp_destroy ejecutado sin crash");
    // Nota: no podemos verificar memoria liberada sin ASAN,
    // pero el test no debe crashear ni tener use-after-free.

    // ================================================================
    // Manual 4 §6.4: reglas — callbacks con ref débil
    // ================================================================
    printf("=== 5. NULL safety ===\n");
    comp_destroy(NULL);
    CHECK(1, "comp_destroy(NULL) no crashea");

    void* null_alloc = comp_alloc(NULL, 64);
    CHECK(null_alloc == NULL, "comp_alloc(NULL) retorna NULL");

    ComponentArena* null_child = comp_arena_crear(NULL, 2048);
    // Sin padre raíz, comp_arena_crear debe fallar o crear sin padre
    CHECK(1, "comp_arena_crear(NULL padre) no crashea");

    printf("\n=== RESULTADO: %d passed, %d failed ===\n", passed, failed);
    return failed > 0 ? 1 : 0;
}
