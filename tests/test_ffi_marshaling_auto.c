// FASE 24.B — Test de FFI Marshaling Automático (Manual 4 §7)
// TDD: este test ES la especificación. Si ffi_marshaling no existe,
// el test NO compila — eso es correcto.
//
// Manual 4 §7.1: El desafío — Syquex texto (sin \0) vs C const char* (con \0)
// Manual 4 §7.2: Estrategia zero-copy — añadir byte \0 al final en la arena
// Manual 4 §7.3: Lifecycle management — callbacks con weak refs
//
// Compila: gcc -O2 -I. -I.. -c tests/test_ffi_marshaling_auto.c -o test_ffi_marshaling_auto.o
//          gcc -O2 -I. -o test_ffi_marshaling_auto.exe test_ffi_marshaling_auto.o ffi_marshaling.o synapse_rt_memory.o -lm -lpthread -lws2_32

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include "ffi_marshaling.h"
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
    // §7.2.1: ffi_texto_a_c_string — zero-copy conversion
    // ================================================================
    printf("=== 1. ffi_texto_a_c_string basico ===\n");
    Arena* arena = arena_crear(4096);

    // Simular un CadenaSegura de Syquex (sin byte nulo)
    const char* original = "Hola Mundo";
    CadenaSegura texto = { .longitud = (int)strlen(original), .datos = original };

    // La función zero-copy debe:
    // 1. Asignar longitud+1 bytes en la arena
    // 2. Copiar los datos
    // 3. Añadir '\0' al final
    // 4. Retornar un puntero al buffer en la arena
    const char* c_str = ffi_texto_a_c_string(&texto, arena);
    CHECK(c_str != NULL, "ffi_texto_a_c_string retorna no-NULL");
    CHECK(c_str != original, "c_str NO es el mismo puntero que original (copia en arena)");
    CHECK(strlen(c_str) == 10, "strlen(c_str) == 10 (Hola Mundo)");
    CHECK(c_str[10] == '\0', "c_str termina en \\0");
    CHECK(memcmp(c_str, "Hola Mundo", 10) == 0, "contenido coincide");

    // ================================================================
    // §7.2.1: Verificar zero-copy — el buffer está en la arena
    // ================================================================
    printf("=== 2. Zero-copy: buffer en arena ===\n");
    CHECK((uintptr_t)c_str >= (uintptr_t)arena->inicio,
          "c_str está dentro del bloque arena (no en heap separado)");
    CHECK((uintptr_t)c_str < (uintptr_t)arena->fin,
          "c_str antes del fin de la arena");

    // ================================================================
    // §7.2.1: Texto vacío
    // ================================================================
    printf("=== 3. Texto vacío ===\n");
    CadenaSegura vacio = { .longitud = 0, .datos = "" };
    const char* c_vacio = ffi_texto_a_c_string(&vacio, arena);
    CHECK(c_vacio != NULL, "ffi_texto_a_c_string(vacio) retorna no-NULL");
    CHECK(c_vacio[0] == '\0', "cadena vacía termina en \\0 inmediatamente");

    // ================================================================
    // §7.2.1: Texto largo
    // ================================================================
    printf("=== 4. Texto largo ===\n");
    const char* largo_texto = "Esto es una prueba de marshaling zero-copy para FFI con C";
    CadenaSegura largo = { .longitud = (int)strlen(largo_texto), .datos = largo_texto };
    const char* c_largo = ffi_texto_a_c_string(&largo, arena);
    CHECK(c_largo != NULL, "texto_largo retorna no-NULL");
    CHECK(strlen(c_largo) == 57, "strlen(texto_largo) == 57");
    CHECK(c_largo[57] == '\0', "texto_largo termina en \\0");

    // ================================================================
    // §7.2.1: NULL safety
    // ================================================================
    printf("=== 5. NULL safety ===\n");
    const char* c_null = ffi_texto_a_c_string(NULL, arena);
    CHECK(c_null == NULL, "ffi_texto_a_c_string(NULL) retorna NULL");

    const char* c_null_arena = ffi_texto_a_c_string(&texto, NULL);
    CHECK(c_null_arena == NULL, "ffi_texto_a_c_string(_, NULL arena) retorna NULL");

    // ================================================================
    // §7.2.1: Múltiples conversiones — todas en la arena
    // ================================================================
    printf("=== 6. Multiples conversiones en la arena ===\n");
    const char* s1 = ffi_texto_a_c_string(&(CadenaSegura){.longitud=3, .datos="abc"}, arena);
    const char* s2 = ffi_texto_a_c_string(&(CadenaSegura){.longitud=3, .datos="def"}, arena);
    CHECK(s1 != NULL && s2 != NULL, "múltiples conversiones OK");
    CHECK(s2 > s1, "s2 > s1 (asignación secuencial en arena)");
    CHECK(strcmp(s1, "abc") == 0, "s1 == \"abc\"");
    CHECK(strcmp(s2, "def") == 0, "s2 == \"def\"");

    arena_free(arena);

    // ================================================================
    // §7.2.2: Conversión de tipos primitivos
    // ================================================================
    printf("=== 7. Tipos primitivos ===\n");
    CHECK(ffi_entero_a_i64(42) == 42, "ffi_entero_a_i64(42) == 42");
    CHECK(ffi_entero_a_i64(-1) == -1, "ffi_entero_a_i64(-1) == -1");
    CHECK(ffi_entero_a_i64(0) == 0, "ffi_entero_a_i64(0) == 0");
    CHECK(ffi_decimal_a_f64(3.14) == 3.14, "ffi_decimal_a_f64(3.14) == 3.14");
    CHECK(ffi_booleano_a_int(1) == 1, "ffi_booleano_a_int(1) == 1");
    CHECK(ffi_booleano_a_int(0) == 0, "ffi_booleano_a_int(0) == 0");

    // ================================================================
    // §7.3: Callback registry
    // ================================================================
    printf("=== 8. Callback registry ===\n");
    int callback_invocado = 0;
    void test_callback(void* data) {
        callback_invocado = 1;
    }
    int id1 = ffi_registrar_callback(test_callback, NULL, 0);
    CHECK(id1 >= 0, "ffi_registrar_callback retorna ID válido");
    CHECK(id1 == 0, "primer callback tiene ID 0");

    ffi_invocar_callback(id1);
    CHECK(callback_invocado == 1, "callback fue invocado");

    ffi_desregistrar_callback(id1);
    callback_invocado = 0;
    ffi_invocar_callback(id1);
    CHECK(callback_invocado == 0, "callback des-registrado no se invoca");

    // ================================================================
    // §7.3: Weak reference callback
    // ================================================================
    printf("=== 9. Weak reference callback ===\n");
    int weak_invocado = 0;
    void weak_callback(void* data) {
        weak_invocado = 1;
    }
    int id2 = ffi_registrar_callback(weak_callback, NULL, 1);
    CHECK(id2 >= 0, "callback débil registrado");

    // Con dato NULL en weak, no debe invocarse
    ffi_invocar_callback(id2);
    CHECK(weak_invocado == 0, "callback débil NO se invoca con dato NULL");

    ffi_desregistrar_callback(id2);

    // ================================================================
    // §7.3: Límite de callbacks
    // ================================================================
    printf("=== 10. Límite de callbacks ===\n");
    int ids[FFI_MAX_CALLBACKS];
    int count = 0;
    for (int i = 0; i < FFI_MAX_CALLBACKS + 5; i++) {
        int id = ffi_registrar_callback(test_callback, NULL, 0);
        if (id >= 0) {
            ids[count++] = id;
        }
    }
    CHECK(count == FFI_MAX_CALLBACKS, "se pueden registrar FFI_MAX_CALLBACKS callbacks");
    int id_overflow = ffi_registrar_callback(test_callback, NULL, 0);
    CHECK(id_overflow == -1, "exceso retorna -1");

    // Limpiar
    for (int i = 0; i < count; i++) {
        ffi_desregistrar_callback(ids[i]);
    }

    printf("\n=== RESULTADO: %d passed, %d failed ===\n", passed, failed);
    return failed > 0 ? 1 : 0;
}
