// tests/unit/test_nodojson_abi.c — TDD: verifica ABI NodoJson == 64 bytes
// cumple Manual 2 §4.1: entero = int64_t (8B), decimal = double (8B)
#include <stdio.h>
#include <stdint.h>
#include <assert.h>
#include "../../synapse_rt_types.h"

// Manual 2 §4.1: CadenaSegura = { int longitud; const char* datos; } = 16 bytes
// Manual 2 §4.1: entero = int64_t (8B), decimal = double (8B)
// NodoJson layout esperado (64 bytes):
//   int64_t tipo       (8B)
//   int64_t valor_bool (8B)
//   double valor_num   (8B)
//   CadenaSegura valor_str (16B)
//   NodoJson* arreglo_hijos (8B)
//   ParJson* objeto_pares   (8B)
//   int64_t longitud   (8B)
// Total: 8+8+8+16+8+8+8 = 64 bytes

int main(void) {
    printf("sizeof(NodoJson) = %zu\n", sizeof(NodoJson));
    printf("sizeof(ParJson) = %zu\n", sizeof(ParJson));
    printf("sizeof(CadenaSegura) = %zu\n", sizeof(CadenaSegura));

    // Test 1: sizeof(NodoJson) debe ser 64 bytes (Manual 2 §4.1)
    assert(sizeof(NodoJson) == 64 && "NodoJson debe ser 64 bytes (int64_t tipo + int64_t valor_bool + double valor_num + CadenaSegura + 2 ptr + int64_t longitud)");

    // Test 2: sizeof(ParJson) debe ser 24 bytes (CadenaSegura 16B + ptr 8B)
    assert(sizeof(ParJson) == 24 && "ParJson debe ser 24 bytes (CadenaSegura 16B + NodoJson* 8B)");

    // Test 3: offsets correctos
    NodoJson n = {0};
    assert((char*)&n.tipo - (char*)&n == 0 && "tipo offset == 0");
    assert((char*)&n.valor_bool - (char*)&n == 8 && "valor_bool offset == 8");
    assert((char*)&n.valor_num - (char*)&n == 16 && "valor_num offset == 16");
    assert((char*)&n.valor_str - (char*)&n == 24 && "valor_str offset == 24");
    assert((char*)&n.arreglo_hijos - (char*)&n == 40 && "arreglo_hijos offset == 40");
    assert((char*)&n.objeto_pares - (char*)&n == 48 && "objeto_pares offset == 48");
    assert((char*)&n.longitud - (char*)&n == 56 && "longitud offset == 56");

    // Test 4: tipo es int64_t (no int)
    assert(sizeof(n.tipo) == 8 && "tipo debe ser int64_t (8 bytes)");
    assert(sizeof(n.valor_bool) == 8 && "valor_bool debe ser int64_t (8 bytes)");
    assert(sizeof(n.valor_num) == 8 && "valor_num debe ser double (8 bytes)");
    assert(sizeof(n.longitud) == 8 && "longitud debe ser int64_t (8 bytes)");

    printf("ALL TESTS PASSED\n");
    return 0;
}
