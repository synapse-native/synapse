// FASE 24 — Test de Mapa hash (Manual 3 §5.2)
// TDD: este test ES la especificación. Si las funciones _syn_mapa_*
// no existen, el test NO compila — eso es correcto.
//
// Manual 3 §5.2: Mapa<K,V> — diccionario hash
// Comando: pytest tests/syquex/test_mapa.py -v
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
    void* m = _syn_mapa_crear();
    CHECK(m != NULL, "mapa_crear retorna no-NULL");
    CHECK(_syn_mapa_longitud(m) == 0, "mapa vacío tiene longitud 0");

    // === 2. Poner y obtener ===
    printf("=== 2. Poner y obtener ===\n");
    _syn_mapa_poner(m, "nombre", 42);
    _syn_mapa_poner(m, "edad", 28);
    _syn_mapa_poner(m, "activo", 1);
    CHECK(_syn_mapa_longitud(m) == 3, "longitud = 3 tras 3 poner");

    CHECK(_syn_mapa_obtener(m, "nombre") == 42, "obtener(\"nombre\") == 42");
    CHECK(_syn_mapa_obtener(m, "edad") == 28, "obtener(\"edad\") == 28");
    CHECK(_syn_mapa_obtener(m, "activo") == 1, "obtener(\"activo\") == 1");

    // === 3. Contiene ===
    printf("=== 3. Contiene ===\n");
    CHECK(_syn_mapa_contiene(m, "nombre") == 1, "contiene(\"nombre\") == true");
    CHECK(_syn_mapa_contiene(m, "inexistente") == 0, "contiene(\"inexistente\") == false");

    // === 4. Actualizar valor ===
    printf("=== 4. Actualizar valor ===\n");
    _syn_mapa_poner(m, "nombre", 99);
    CHECK(_syn_mapa_obtener(m, "nombre") == 99, "actualizar \"nombre\" a 99");
    CHECK(_syn_mapa_longitud(m) == 3, "longitud sigue en 3 tras actualizar");

    // === 5. Eliminar ===
    printf("=== 5. Eliminar ===\n");
    _syn_mapa_eliminar(m, "edad");
    CHECK(_syn_mapa_longitud(m) == 2, "longitud = 2 tras eliminar \"edad\"");
    CHECK(_syn_mapa_contiene(m, "edad") == 0, "contiene(\"edad\") == false tras eliminar");
    CHECK(_syn_mapa_obtener(m, "edad") == 0, "obtener(\"edad\") == 0 tras eliminar");

    // === 6. Limpiar ===
    printf("=== 6. Limpiar ===\n");
    _syn_mapa_limpiar(m);
    CHECK(_syn_mapa_longitud(m) == 0, "longitud = 0 tras limpiar");
    CHECK(_syn_mapa_contiene(m, "nombre") == 0, "contiene(\"nombre\") == false tras limpiar");

    // === 7. Muchas claves (expansión) ===
    printf("=== 7. Expansion (500 claves) ===\n");
    char clave[32];
    for (int i = 0; i < 500; i++) {
        snprintf(clave, sizeof(clave), "key_%d", i);
        _syn_mapa_poner(m, clave, i);
    }
    CHECK(_syn_mapa_longitud(m) == 500, "longitud = 500");
    CHECK(_syn_mapa_obtener(m, "key_0") == 0, "key_0 == 0");
    CHECK(_syn_mapa_obtener(m, "key_250") == 250, "key_250 == 250");
    CHECK(_syn_mapa_obtener(m, "key_499") == 499, "key_499 == 499");
    CHECK(_syn_mapa_contiene(m, "key_100") == 1, "contiene key_100");

    // === 8. Claves y valores ===
    printf("=== 8. Claves y valores ===\n");
    _syn_mapa_limpiar(m);
    _syn_mapa_poner(m, "a", 1);
    _syn_mapa_poner(m, "b", 2);
    _syn_mapa_poner(m, "c", 3);
    void* claves = _syn_mapa_claves(m);
    void* valores = _syn_mapa_valores(m);
    CHECK(claves != NULL, "claves() retorna no-NULL");
    CHECK(valores != NULL, "valores() retorna no-NULL");
    CHECK(_syn_lista_longitud(claves) == 3, "claves tiene 3 elementos");
    CHECK(_syn_lista_longitud(valores) == 3, "valores tiene 3 elementos");

    // Verificar que los valores están (el orden puede variar por hash)
    int64_t v0 = _syn_lista_obtener(valores, 0);
    int64_t v1 = _syn_lista_obtener(valores, 1);
    int64_t v2 = _syn_lista_obtener(valores, 2);
    CHECK((v0 == 1 || v0 == 2 || v0 == 3), "valor[0] es 1, 2 o 3");
    CHECK((v1 == 1 || v1 == 2 || v1 == 3), "valor[1] es 1, 2 o 3");
    CHECK((v2 == 1 || v2 == 2 || v2 == 3), "valor[2] es 1, 2 o 3");

    _syn_lista_liberar(claves);
    _syn_lista_liberar(valores);

    // === 9. NULL safety ===
    printf("=== 9. NULL safety ===\n");
    CHECK(_syn_mapa_longitud(NULL) == 0, "longitud(NULL) == 0");
    _syn_mapa_poner(NULL, "x", 1);  // no crashea
    CHECK(1, "poner(NULL) no crashea");
    CHECK(_syn_mapa_obtener(NULL, "x") == 0, "obtener(NULL, \"x\") == 0");
    CHECK(_syn_mapa_contiene(NULL, "x") == 0, "contiene(NULL, \"x\") == 0");

    // === 10. Liberación ===
    printf("=== 10. Liberacion ===\n");
    _syn_mapa_liberar(m);
    CHECK(1, "mapa_liberar no crashea");

    printf("\n=== RESULTADO: %d passed, %d failed ===\n", passed, failed);
    return failed > 0 ? 1 : 0;
}
