// FASE 23 ME-5: Scope analyzer runtime C (Manual 4 §5.2-5.3)
// Tests _a_analizar_bloque / _a_get_rc_count / _a_reset_rc_vars
// with a mock SemNodo[] AST that simulates rc<T> variables.

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
    if ((a) != (b)) { printf("  [FAIL] %s: esperado %d, obtenido %d\n", msg, (int)(b), (int)(a)); failed++; } \
    else { printf("  [PASS] %s\n", msg); passed++; } \
} while(0)

int main(void) {
    setbuf(stdout, NULL);

    // Mock AST: 6 nodos. hijo_izq/hijo_der/hermano = -1 para "sin hijo"
    // (0 es un índice válido = NODO_PROGRAMA, no usar 0 como null)
    NodoAST nodos[7];
    memset(nodos, 0, sizeof(nodos));
    // Inicializar todos los punteros a -1 (null)
    for (int i = 0; i < 7; i++) {
        nodos[i].hijo_izq = -1;
        nodos[i].hijo_der = -1;
        nodos[i].hermano = -1;
        nodos[i].ptr_extra = -1;
    }

    nodos[0].tipo_nodo = 1;  // NODO_PROGRAMA
    nodos[0].hijo_izq = 1;   // → funcion

    nodos[1].tipo_nodo = 2;  // NODO_FUNCION
    nodos[1].hijo_izq = 2;   // → primer stmt

    // Lista de statements en hermano chain: 2→3→4→5
    nodos[2].tipo_nodo = 34;  // NODO_DECLARACION (rc)
    nodos[2].valor_int = 1;   // bit0: rc
    nodos[2].hermano = 3;

    nodos[3].tipo_nodo = 34;  // NODO_DECLARACION (arc)
    nodos[3].valor_int = 2;   // bit1: arc
    nodos[3].hermano = 4;

    nodos[4].tipo_nodo = 34;  // NODO_DECLARACION (plain, no ownership)
    nodos[4].valor_int = 0;   // sin flags
    nodos[4].hermano = 5;

    nodos[5].tipo_nodo = 48;  // NODO_LET (débil)
    nodos[5].valor_int = 4;   // bit2: débil
    nodos[5].hermano = -1;

    // --- Test 1: reset + analizar ---
    printf("=== 1. _a_analizar_bloque cuenta rc/arc vars ===\n");
    _a_set_nodos_base(nodos);
    _a_reset_rc_vars();
    // Empezar en NODO_FUNCION (índice 1) → hijo_izq → stmt chain
    _a_analizar_bloque(1);
    CHECK_INT_EQ(_a_get_rc_count(), 2, "2 rc/arC vars (rc + arc, no débil, no plain)");

    // --- Test 2: reset limpia el contador ---
    printf("=== 2. _a_reset_rc_vars limpia contador ===\n");
    _a_reset_rc_vars();
    CHECK_INT_EQ(_a_get_rc_count(), 0, "contador = 0 tras reset");

    // --- Test 3: NULL safety (base no set) ---
    printf("=== 3. NULL safety ===\n");
    _a_set_nodos_base(NULL);
    _a_analizar_bloque(0);  // no crashea con base NULL
    CHECK_INT_EQ(_a_get_rc_count(), 0, "0 vars con base NULL");
    _a_set_nodos_base(nodos);

    // --- Test 4: nodo 0 (NODO_PROGRAMA) → hijo_izq=1 → funcion → stmts ---
    printf("=== 4. Walk desde programa raíz ===\n");
    _a_reset_rc_vars();
    _a_analizar_bloque(0);  // NODO_PROGRAMA → hijo_izq → funcion → stmts
    CHECK(_a_get_rc_count() >= 2, "encuentra rc vars en subtree del programa");
    CHECK(_a_get_rc_count() == 2, "exactamente 2 rc vars en todo el subtree");

    // --- Test 5: débil no cuenta ---
    printf("=== 5. débiles<T> no incrementan rc_count ===\n");
    _a_reset_rc_vars();
    _a_analizar_bloque(5);  // NODO_LET con débil (valor_int=4)
    CHECK_INT_EQ(_a_get_rc_count(), 0, "débil no cuenta como ownership");

    // --- Test 6: nodo individual (el walker sigue sibling chain, asi que
    //     testeamos nodos aislados rompiendo el hermano) ---
    printf("=== 6. Nodos isolados verificado ===\n");
    _a_reset_rc_vars();
    _a_analizar_bloque(5);  // NODO_LET con débil (valor_int=4, hermano=-1)
    CHECK_INT_EQ(_a_get_rc_count(), 0, "débil no cuenta");
    // Test rc isolado: temporalmente romper hermano de nodo 2
    int orig_herm = (int)nodos[2].hermano;
    nodos[2].hermano = -1;
    _a_reset_rc_vars();
    _a_analizar_bloque(2);  // rc (hermano roto)
    CHECK_INT_EQ(_a_get_rc_count(), 1, "rc cuenta");
    nodos[2].hermano = orig_herm;
    // Test arc isolado
    int orig_herm3 = (int)nodos[3].hermano;
    nodos[3].hermano = -1;
    _a_reset_rc_vars();
    _a_analizar_bloque(3);  // arc (hermano roto)
    CHECK_INT_EQ(_a_get_rc_count(), 1, "arc cuenta");
    nodos[3].hermano = orig_herm3;
    // Test plain isolado
    int orig_herm4 = (int)nodos[4].hermano;
    nodos[4].hermano = -1;
    _a_reset_rc_vars();
    _a_analizar_bloque(4);  // plain (hermano roto)
    CHECK_INT_EQ(_a_get_rc_count(), 0, "plain no cuenta");
    nodos[4].hermano = orig_herm4;

    printf("\n=== RESULTADO: %d passed, %d failed ===\n", passed, failed);
    return failed > 0 ? 1 : 0;
}
