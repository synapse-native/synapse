// FASE 23 — Test de FFI Marshaling Zero-Copy (Manual 4 §7)
// TDD: este test ES la especificación. Si texto_a_c_string no existe,
// el test NO compila — eso es correcto. Se corrige el CÓDIGO, no el test.
//
// Manual 4 §7.1: El desafío — Syquex texto (sin \0) vs C const char* (con \0)
// Manual 4 §7.2: Estrategia zero-copy — añadir byte \0 al final en la arena
// Manual 4 §7.3: texto_a_c_string(CadenaSegura* texto, Arena* arena) -> const char*
//
// Compila: gcc -O2 -I. -I.. -c tests/test_ffi_marshaling.c -o ...
//          gcc -O2 -I. -o test_ffi_marshaling.exe test_ffi_marshaling.o synapse_rt_memory.o -lm -lpthread -lws2_32

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
    // Manual 4 §7.2: texto_a_c_string — zero-copy conversion
    // ================================================================
    printf("=== 1. texto_a_c_string basico ===\n");
    Arena* arena = arena_crear(4096);

    // Simular un CadenaSegura de Syquex (sin byte nulo)
    const char* original = "Hola Mundo";
    CadenaSegura texto = { .longitud = (int)strlen(original), .datos = original };

    // La función zero-copy debe:
    // 1. Asignar longitud+1 bytes en la arena
    // 2. Copiar los datos
    // 3. Añadir '\0' al final
    // 4. Retornar un puntero al buffer en la arena
    const char* c_str = texto_a_c_string(&texto, arena);
    CHECK(c_str != NULL, "texto_a_c_string retorna no-NULL");
    CHECK(c_str != original, "c_str NO es el mismo puntero que original (copia en arena)");
    CHECK(strlen(c_str) == 10, "strlen(c_str) == 10 (Hola Mundo)");
    CHECK(c_str[10] == '\0', "c_str termina en \\0");
    CHECK(memcmp(c_str, "Hola Mundo", 10) == 0, "contenido coincide");

    // ================================================================
    // Manual 4 §7.2: Verificar zero-copy — el buffer está en la arena
    // ================================================================
    printf("=== 2. Zero-copy: buffer en arena ===\n");
    CHECK((uintptr_t)c_str >= (uintptr_t)arena->inicio,
          "c_str está dentro del bloque arena (no en heap separado)");
    CHECK((uintptr_t)c_str < (uintptr_t)arena->fin,
          "c_str antes del fin de la arena");

    // ================================================================
    // Manual 4 §7.2: Texto vacío
    // ================================================================
    printf("=== 3. Texto vacío ===\n");
    CadenaSegura vacio = { .longitud = 0, .datos = "" };
    const char* c_vacio = texto_a_c_string(&vacio, arena);
    CHECK(c_vacio != NULL, "texto_a_c_string(vacio) retorna no-NULL");
    CHECK(c_vacio[0] == '\0', "cadena vacía termina en \\0 inmediatamente");

    // ================================================================
    // Manual 4 §7.2: Texto largo
    // ================================================================
    printf("=== 4. Texto largo ===\n");
    const char* largo_texto = "Esto es una prueba de marshaling zero-copy para FFI con C";
    CadenaSegura largo = { .longitud = (int)strlen(largo_texto), .datos = largo_texto };
    const char* c_largo = texto_a_c_string(&largo, arena);
    CHECK(c_largo != NULL, "texto_largo retorna no-NULL");
    CHECK(strlen(c_largo) == 57, "strlen(texto_largo) == 57");
    CHECK(c_largo[57] == '\0', "texto_largo termina en \\0");

    // ================================================================
    // Manual 4 §7.2: NULL safety
    // ================================================================
    printf("=== 5. NULL safety ===\n");
    const char* c_null = texto_a_c_string(NULL, arena);
    CHECK(c_null == NULL, "texto_a_c_string(NULL) retorna NULL");

    const char* c_null_arena = texto_a_c_string(&texto, NULL);
    CHECK(c_null_arena == NULL, "texto_a_c_string(_, NULL arena) retorna NULL");

    // ================================================================
    // Manual 4 §7.2: Múltiples conversiones — todas en la arena
    // ================================================================
    printf("=== 6. Multiples conversiones en la arena ===\n");
    const char* s1 = texto_a_c_string(&(CadenaSegura){.longitud=3, .datos="abc"}, arena);
    const char* s2 = texto_a_c_string(&(CadenaSegura){.longitud=3, .datos="def"}, arena);
    CHECK(s1 != NULL && s2 != NULL, "múltiples conversiones OK");
    CHECK(s2 > s1, "s2 > s1 (asignación secuencial en arena)");
    CHECK(strcmp(s1, "abc") == 0, "s1 == \"abc\"");
    CHECK(strcmp(s2, "def") == 0, "s2 == \"def\"");

    arena_free(arena);

    printf("\n=== RESULTADO: %d passed, %d failed ===\n", passed, failed);
    return failed > 0 ? 1 : 0;
}
