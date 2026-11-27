// tests/unit/test_modelo_strtol.c
// TDD test ME-SEC-3: strtol+endptr en modelo.c
// Manual 7 §3, Manual 2 §12, Manual 4 §2.1
// OBL-M7-01: metadatos GGUF parseados correctamente
//
// Este test prueba _syn_vocab_tamano (pública) que usa strtol internamente.
// Validación: InternalData real via modelo.h (autorización ARQ-2026-08-30).

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include "runtime/core/modelo.h"  // InternalData real — autorizado por Arquitecto

// Declarar función pública de modelo.c
extern int _syn_vocab_tamano(void* datos_internos);

static int tests_pasados = 0;
static int tests_fallidos = 0;

#define ASSERT_EQ(expr, esperado, msg) do { \
    int _v = (expr); \
    int _e = (esperado); \
    if (_v == _e) { \
        tests_pasados++; \
        printf("  PASS: %s = %d\n", msg, _v); \
    } else { \
        tests_fallidos++; \
        printf("  FAIL: %s = %d (esperado %d)\n", msg, _v, _e); \
    } \
} while(0)

int main(void) {
    printf("=== ME-SEC-3: strtol+endptr en modelo.c ===\n");

    // Helper: crear InternalData con 1 par metadato
    InternalData d;
    memset(&d, 0, sizeof(d));
    d.cantidad_metadatos = 1;

    // Caso 1: valor numérico válido → debe retornar el número
    d.metadatos[0].clave = "vocab_size";
    d.metadatos[0].valor = "32000";
    ASSERT_EQ(_syn_vocab_tamano(&d), 32000, "vocab_size=32000 → 32000");

    // Caso 2: valor con sufijo alfanumérico → strtol detecta error
    d.metadatos[0].valor = "32700abc";
    ASSERT_EQ(_syn_vocab_tamano(&d), 0, "vocab_size=32700abc → 0 (no 32700)");

    // Caso 3: valor no numérico
    d.metadatos[0].valor = "not_a_number";
    ASSERT_EQ(_syn_vocab_tamano(&d), 0, "vocab_size=not_a_number → 0");

    // Caso 4: valor vacío
    d.metadatos[0].valor = "";
    ASSERT_EQ(_syn_vocab_tamano(&d), 0, "vocab_size='' → 0");

    // Caso 5: valor NULL (requiere fix para no crashear)
    d.metadatos[0].valor = NULL;
    ASSERT_EQ(_syn_vocab_tamano(&d), 0, "vocab_size=NULL → 0 (sin crash)");

    // Caso 6: clave no encontrada
    d.metadatos[0].clave = "otra_clave";
    d.metadatos[0].valor = "12345";
    ASSERT_EQ(_syn_vocab_tamano(&d), 0, "clave inexistente → 0");

    // Caso 7: sin metadatos
    d.cantidad_metadatos = 0;
    ASSERT_EQ(_syn_vocab_tamano(&d), 0, "sin metadatos → 0");

    // Caso 8: NULL datos_internos
    ASSERT_EQ(_syn_vocab_tamano(NULL), 0, "NULL datos_internos → 0");

    printf("\n=== Resultado: %d pasados, %d fallidos ===\n",
           tests_pasados, tests_fallidos);

    return tests_fallidos > 0 ? 1 : 0;
}
