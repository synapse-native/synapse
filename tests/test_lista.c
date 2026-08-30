// FASE 24 — Test de Lista dinámica (Manual 3 §5.2)
// TDD: este test ES la especificación. Si las funciones _syn_lista_*
// no existen, el test NO compila — eso es correcto.
//
// Manual 3 §5.2: Lista<T> — lista dinámica (vector)
// Comando: pytest tests/syquex/test_lista.py -v
// Criterio: 0 fugas, operaciones correctas

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

    // === 1. Creación y básicos ===
    printf("=== 1. Creacion y operaciones basicas ===\n");
    void* l = _syn_lista_crear();
    CHECK(l != NULL, "lista_crear retorna no-NULL");
    CHECK(_syn_lista_longitud(l) == 0, "lista vacía tiene longitud 0");

    _syn_lista_agregar(l, 10);
    _syn_lista_agregar(l, 20);
    _syn_lista_agregar(l, 30);
    CHECK(_syn_lista_longitud(l) == 3, "longitud = 3 tras 3 agregar");

    CHECK(_syn_lista_obtener(l, 0) == 10, "obtener(0) == 10");
    CHECK(_syn_lista_obtener(l, 1) == 20, "obtener(1) == 20");
    CHECK(_syn_lista_obtener(l, 2) == 30, "obtener(2) == 30");

    // === 2. Establecer ===
    printf("=== 2. Establecer ===\n");
    _syn_lista_establecer(l, 1, 99);
    CHECK(_syn_lista_obtener(l, 1) == 99, "establecer(1, 99) → obtener(1) == 99");
    CHECK(_syn_lista_longitud(l) == 3, "longitud no cambia tras establecer");

    // === 3. Eliminar ===
    printf("=== 3. Eliminar ===\n");
    _syn_lista_eliminar(l, 0);  // eliminar 10
    CHECK(_syn_lista_longitud(l) == 2, "longitud = 2 tras eliminar(0)");
    CHECK(_syn_lista_obtener(l, 0) == 99, "obtener(0) == 99 (antes era índice 1)");
    CHECK(_syn_lista_obtener(l, 1) == 30, "obtener(1) == 30");

    // === 4. Limpiar ===
    printf("=== 4. Limpiar ===\n");
    _syn_lista_limpiar(l);
    CHECK(_syn_lista_longitud(l) == 0, "longitud = 0 tras limpiar");

    // === 5. Muchos elementos (expansión) ===
    printf("=== 5. Expansion (1000 elementos) ===\n");
    for (int i = 0; i < 1000; i++) {
        _syn_lista_agregar(l, i);
    }
    CHECK(_syn_lista_longitud(l) == 1000, "longitud = 1000");
    CHECK(_syn_lista_obtener(l, 0) == 0, "primer elemento == 0");
    CHECK(_syn_lista_obtener(l, 999) == 999, "último elemento == 999");
    CHECK(_syn_lista_obtener(l, 500) == 500, "medio == 500");

    // === 6. NULL safety ===
    printf("=== 6. NULL safety ===\n");
    CHECK(_syn_lista_longitud(NULL) == 0, "longitud(NULL) == 0");
    _syn_lista_agregar(NULL, 1);  // no crashea
    CHECK(1, "agregar(NULL) no crashea");
    CHECK(_syn_lista_obtener(NULL, 0) == 0, "obtener(NULL, 0) == 0");
    CHECK(_syn_lista_obtener(l, -1) == 0, "obtener(_, -1) == 0 (bounds)");
    CHECK(_syn_lista_obtener(l, 9999) == 0, "obtener(_, 9999) == 0 (bounds)");

    // === 7. Liberación ===
    printf("=== 7. Liberacion ===\n");
    _syn_lista_liberar(l);
    CHECK(1, "lista_liberar no crashea");

    printf("\n=== RESULTADO: %d passed, %d failed ===\n", passed, failed);
    return failed > 0 ? 1 : 0;
}
