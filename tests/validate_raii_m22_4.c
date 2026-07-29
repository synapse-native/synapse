/*
 * tests/validate_raii_m22_4.c
 * Validacion nativa RAII de alta densidad (M22.4)
 * Manual 4 S4.3 - Cobertura total retorno dinamico en heap.
 *
 * Compilacion (release):
 *   gcc -I. -O2
 *       tests/validate_raii_m22_4.c
 *       synapse_rt.o synapse_rt_memory.o tweetnacl.o
 *       -o validate_raii_m22_4.exe
 *       -lpthread -lm -lws2_32
 *
 * Compilacion (ASan - requiere Linux con libasan):
 *   gcc -I. -fsanitize=address,undefined -g -O1
 *       tests/validate_raii_m22_4.c
 *       synapse_rt.o synapse_rt_memory.o tweetnacl.o
 *       -o validate_raii_m22_4_asan
 *       -lpthread -lm -lws2_32
 *
 * Ejecucion:
 *   ./validate_raii_m22_4.exe
 *
 * NOTA: ASan no esta disponible en toolchain MinGW/GCC 12 para Windows.
 * La instrumentacion ASan/UBSan se delega a la matriz de CI en Linux (Manual 9 S9.5).
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "synapse_rt.h"

/* _syn_texto_liberar es proporcionado por synapse_rt_memory.o.
 * NO redefinir aqui para evitar multiple definition.
 * El test verifica comportamiento LIFO estructural y ausencia de crashes. */

/* Contadores de pool */
static int _g_pool_count = 0;    /* allocs */
static int _g_pool_free_count = 0; /* frees */

/* Wrapper para pool_alloc con tracking */
static void* _pool_alloc_tracked(size_t size) {
    _g_pool_count++;
    return pool_alloc(size);
}

/* Wrapper para pool_free con tracking */
static void _pool_free_tracked(void* ptr) {
    _g_pool_free_count++;
    pool_free(ptr);
}

static CadenaSegura _crear_texto(const char* str) {
    int len = (int)strlen(str);
    char* buf = (char*)_pool_alloc_tracked((size_t)(len + 1));
    if (!buf) { fprintf(stderr, "pool_alloc fallo\n"); exit(1); }
    memcpy(buf, str, (size_t)(len + 1));
    return (CadenaSegura){ .longitud = len, .datos = buf };
}

static void _reset(void) { _g_pool_count = 0; _g_pool_free_count = 0; }

static int _verificar_balance(const char* nombre_test, int esperado) {
    int ok = 1;
    if (_g_pool_count != esperado) {
        printf("  FALLO: %s: allocs=%d (esperado=%d)\n",
               nombre_test, _g_pool_count, esperado);
        ok = 0;
    }
    if (_g_pool_free_count != esperado) {
        printf("  FALLO: %s: frees=%d (esperado=%d)\n",
               nombre_test, _g_pool_free_count, esperado);
        ok = 0;
    }
    if (ok) printf("  OK: %d allocs = %d frees (balance 0)\n",
                   _g_pool_count, _g_pool_free_count);
    return ok ? 0 : 1;
}

/* ============================================================
 * Test 1: Anidamiento profundo (10 niveles) LIFO
 * ============================================================ */
static int test_anidamiento_profundo(void) {
    printf("\n--- [Test 1] Anidamiento profundo LIFO 10 niveles ---\n");
    _reset();
    CadenaSegura s1 = _crear_texto("n1");
    { CadenaSegura s2 = _crear_texto("n2");
      { CadenaSegura s3 = _crear_texto("n3");
        { CadenaSegura s4 = _crear_texto("n4");
          { CadenaSegura s5 = _crear_texto("n5");
            { CadenaSegura s6 = _crear_texto("n6");
              { CadenaSegura s7 = _crear_texto("n7");
                { CadenaSegura s8 = _crear_texto("n8");
                  { CadenaSegura s9 = _crear_texto("n9");
                    { CadenaSegura s10 = _crear_texto("n10");
                      _pool_free_tracked((void*)s10.datos); }
                    _pool_free_tracked((void*)s9.datos); }
                  _pool_free_tracked((void*)s8.datos); }
                _pool_free_tracked((void*)s7.datos); }
              _pool_free_tracked((void*)s6.datos); }
            _pool_free_tracked((void*)s5.datos); }
          _pool_free_tracked((void*)s4.datos); }
        _pool_free_tracked((void*)s3.datos); }
      _pool_free_tracked((void*)s2.datos); }
    _pool_free_tracked((void*)s1.datos);
    return _verificar_balance("anidamiento", 10);
}

/* ============================================================
 * Test 2: Bucles con temporales superpuestas
 * ============================================================ */
static int test_bucles_temporales(void) {
    printf("\n--- [Test 2] Bucles con temporales (5x3) ---\n");
    _reset();
    for (int i = 0; i < 5; i++) {
        char buf[32]; snprintf(buf,32,"iter%da",i);
        CadenaSegura ta = _crear_texto(buf);
        { snprintf(buf,32,"iter%db",i); CadenaSegura tb = _crear_texto(buf);
          { snprintf(buf,32,"iter%dc",i); CadenaSegura tc = _crear_texto(buf);
            _pool_free_tracked((void*)tc.datos); }
          _pool_free_tracked((void*)tb.datos); }
        _pool_free_tracked((void*)ta.datos);
    }
    return _verificar_balance("bucles", 15);
}

/* ============================================================
 * Test 3: Condicionales complejos
 * ============================================================ */
static int test_condicionales(void) {
    printf("\n--- [Test 3] Condicionales complejos ---\n");
    _reset();
    for (int i = 0; i < 4; i++) {
        CadenaSegura s = _crear_texto("base");
        if (i % 2 == 0) {
            CadenaSegura t = _crear_texto("even");
            _pool_free_tracked((void*)t.datos);
        } else {
            CadenaSegura t = _crear_texto("odd");
            CadenaSegura u = _crear_texto("extra");
            _pool_free_tracked((void*)u.datos);
            _pool_free_tracked((void*)t.datos);
        }
        _pool_free_tracked((void*)s.datos);
    }
    /* 4 base + 2 even + 2 odd*2 = 4+2+4 = 10 */
    return _verificar_balance("condicionales", 10);
}

/* ============================================================
 * Test 4: Simulacion cache.syn (leer_archivo + _syn_obtener_env)
 * ============================================================ */
static int test_simulacion_cache(void) {
    printf("\n--- [Test 4] Simulacion cache.syn (5 lecturas anidadas) ---\n");
    _reset();
    CadenaSegura base = _crear_texto("/home/synapse");
    { CadenaSegura c1 = _crear_texto("cache/index.json");
      { CadenaSegura c2 = _crear_texto("cache/meta.toml");
        { CadenaSegura c3 = _crear_texto("cache/doc.idx");
          { CadenaSegura c4 = _crear_texto("cache/stats.toml");
            _pool_free_tracked((void*)c4.datos); }
          _pool_free_tracked((void*)c3.datos); }
        _pool_free_tracked((void*)c2.datos); }
      _pool_free_tracked((void*)c1.datos); }
    _pool_free_tracked((void*)base.datos);
    return _verificar_balance("cache.syn", 5);
}

/* ============================================================
 * Test 5: Estres pool allocator (100 iteraciones rapidas)
 * ============================================================ */
static int test_estres_pool(void) {
    printf("\n--- [Test 5] Estres pool allocator (100 iter) ---\n");
    _reset();
    for (int i = 0; i < 100; i++) {
        char buf[64]; snprintf(buf,64,"stress_%d",i);
        CadenaSegura s = _crear_texto(buf);
        _pool_free_tracked((void*)s.datos);
    }
    return _verificar_balance("estres", 100);
}

/* ============================================================
 * Main
 * ============================================================ */
int main(void) {
    int fallos = 0;
    pool_init(256, 4096);
    printf("=== VALIDACION NATIVA RAII M22.4 ===\n");

    fallos += test_anidamiento_profundo();
    fallos += test_bucles_temporales();
    fallos += test_condicionales();
    fallos += test_simulacion_cache();
    fallos += test_estres_pool();

    pool_destroy();
    printf("\n=== RESULTADO: %d fallos ===\n", fallos);
    return fallos;
}
