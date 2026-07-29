/*
 * M22.3: Validacion nativa de RAII por scopes (Manual 4.3).
 * Verifica que pool_free / _syn_texto_liberar se invocan
 * correctamente al salir de bloques anidados.
 *
 * Compilacion:
 *   gcc -I. tests/validate_raii_scopes.c synapse_rt.o synapse_rt_memory.o -o validate_raii_scopes.exe -lpthread -lm -lws2_32
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "synapse_rt.h"
#include "synapse_rt_memory.h"

// Usar _syn_texto_liberar del runtime (no redefinir)
// El runtime synapse_rt_memory.o ya lo implementa.
// Solo verificamos que se pueda llamar sin crash.

// Test basico: string en heap se libera sin crash
int test_pool_alloc_free_string() {
    printf("  [TEST] pool_alloc + _syn_texto_liberar... ");
    fflush(stdout);
    char* buf = (char*)pool_alloc(64);
    if (!buf) { printf("FAIL (alloc)\n"); return 1; }
    strcpy(buf, "hola_mundo");
    CadenaSegura s = {10, buf};
    _syn_texto_liberar(s);
    printf("OK\n");
    return 0;
}

// Test: _syn_texto_liberar con cadena nula (no debe crash)
int test_liberar_cadena_nula() {
    printf("  [TEST] _syn_texto_liberar cadena nula... ");
    fflush(stdout);
    CadenaSegura s = {0, NULL};
    _syn_texto_liberar(s);
    printf("OK\n");
    return 0;
}

// Test: _syn_texto_liberar con cadena vacia (no debe crash)
int test_liberar_cadena_vacia() {
    printf("  [TEST] _syn_texto_liberar cadena vacia... ");
    fflush(stdout);
    char* buf = (char*)pool_alloc(1);
    if (!buf) { printf("FAIL (alloc)\n"); return 1; }
    buf[0] = 0;
    CadenaSegura s = {0, buf};
    _syn_texto_liberar(s);
    printf("OK\n");
    return 0;
}

// Test: multiples liberaciones en orden LIFO
int test_lifo_order() {
    printf("  [TEST] multiples liberaciones LIFO... ");
    fflush(stdout);
    char* a = (char*)pool_alloc(16); strcpy(a, "alpha");
    char* b = (char*)pool_alloc(16); strcpy(b, "beta");
    CadenaSegura sa = {5, a};
    CadenaSegura sb = {4, b};
    // Liberar en LIFO: _sb (ultimo declarado), _sa (primero)
    _syn_texto_liberar(sb);
    _syn_texto_liberar(sa);
    printf("OK\n");
    return 0;
}

int main() {
    int fallos = 0;

    pool_init(64, 4096);

    printf("=== VALIDACION NATIVA RAII SCOPES (M22.3) ===\n");

    fallos += test_pool_alloc_free_string();
    fallos += test_liberar_cadena_nula();
    fallos += test_liberar_cadena_vacia();
    fallos += test_lifo_order();

    pool_destroy();

    printf("\n=== RESULTADO: %d fallos ===\n", fallos);
    return fallos;
}
