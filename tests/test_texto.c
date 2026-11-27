// FASE 24 — Test de Texto (Manual 3 §12.1)
// TDD: este test ES la especificación. Si las funciones _syn_texto_*
// no existen, el test NO compila — eso es correcto.
//
// Manual 3 §12.1: lib/texto.syq — Manipulación avanzada de cadenas
// Comando: pytest tests/syquex/test_texto.py -v
// Criterio: todas las operaciones de cadena correctas

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include "synapse_rt_types.h"
#include "runtime/core/texto.h"

static int passed = 0;
static int failed = 0;

#define CHECK(cond, msg) do { \
    if (!(cond)) { printf("  [FAIL] %s\n", msg); failed++; } \
    else { printf("  [PASS] %s\n", msg); passed++; } \
} while(0)

#define CS(s) ((CadenaSegura){ .longitud = (int)strlen(s), .datos = (s) })

int main(void) {
    setbuf(stdout, NULL);

    // === 1. Longitud ===
    printf("=== 1. Longitud ===\n");
    CHECK(_syn_texto_longitud(CS("")) == 0, "longitud(\"\") == 0");
    CHECK(_syn_texto_longitud(CS("hola")) == 4, "longitud(\"hola\") == 4");
    CHECK(_syn_texto_longitud(CS("hello world")) == 11, "longitud(\"hello world\") == 11");
    CHECK(_syn_texto_longitud((CadenaSegura){0, NULL}) == 0, "longitud(NULL) == 0");

    // === 2. Subcadena ===
    printf("=== 2. Subcadena ===\n");
    CadenaSegura s2 = _syn_texto_subcadena(CS("hola mundo"), 0, 4);
    CHECK(s2.longitud == 4 && memcmp(s2.datos, "hola", 4) == 0, "subcadena(\"hola mundo\", 0, 4) == \"hola\"");
    CadenaSegura s2b = _syn_texto_subcadena(CS("hola mundo"), 5, 10);
    CHECK(s2b.longitud == 5 && memcmp(s2b.datos, "mundo", 5) == 0, "subcadena(\"hola mundo\", 5, 10) == \"mundo\"");
    CadenaSegura s2c = _syn_texto_subcadena(CS("abc"), 1, 1);
    CHECK(s2c.longitud == 0, "subcadena(\"abc\", 1, 1) == \"\"");

    // === 3. Contiene ===
    printf("=== 3. Contiene ===\n");
    CHECK(_syn_texto_contiene(CS("hola mundo"), CS("mundo")) == 1, "contiene(\"hola mundo\", \"mundo\") == true");
    CHECK(_syn_texto_contiene(CS("hola mundo"), CS("xyz")) == 0, "contiene(\"hola mundo\", \"xyz\") == false");
    CHECK(_syn_texto_contiene(CS("hola"), CS("")) == 1, "contiene(\"hola\", \"\") == true");
    CHECK(_syn_texto_contiene(CS(""), CS("a")) == 0, "contiene(\"\", \"a\") == false");

    // === 4. Reemplazar ===
    printf("=== 4. Reemplazar ===\n");
    CadenaSegura r4 = _syn_texto_reemplazar(CS("hola mundo"), CS("mundo"), CS("syquex"));
    CHECK(r4.longitud == 11 && memcmp(r4.datos, "hola syquex", 11) == 0, "reemplazar(\"hola mundo\", \"mundo\", \"syquex\")");
    CadenaSegura r4b = _syn_texto_reemplazar(CS("aaa"), CS("a"), CS("b"));
    CHECK(r4b.longitud == 3 && memcmp(r4b.datos, "bbb", 3) == 0, "reemplazar(\"aaa\", \"a\", \"b\") == \"bbb\"");
    CadenaSegura r4c = _syn_texto_reemplazar(CS("abc"), CS("x"), CS("y"));
    CHECK(r4c.longitud == 3 && memcmp(r4c.datos, "abc", 3) == 0, "reemplazar sin match retorna original");

    // === 5. Dividir (split) ===
    printf("=== 5. Dividir ===\n");
    int64_t sp = _syn_texto_dividir(CS("a,b,c"), CS(","));
    CHECK(_syn_texto_dividir_longitud(sp) == 3, "dividir(\"a,b,c\", \",\") tiene 3 partes");
    CadenaSegura sp0 = _syn_texto_dividir_obtener(sp, 0);
    CHECK(sp0.longitud == 1 && sp0.datos[0] == 'a', "parte[0] == \"a\"");
    CadenaSegura sp2 = _syn_texto_dividir_obtener(sp, 2);
    CHECK(sp2.longitud == 1 && sp2.datos[0] == 'c', "parte[2] == \"c\"");
    _syn_texto_dividir_liberar(sp);

    // === 6. Unir (join) ===
    printf("=== 6. Unir ===\n");
    int64_t jn = _syn_texto_dividir(CS("a,b,c"), CS(","));
    CadenaSegura j = _syn_texto_unir(jn, CS(" + "));
    CHECK(j.longitud == 9 && memcmp(j.datos, "a + b + c", 9) == 0, "unir([a,b,c], \" + \") == \"a + b + c\"");
    _syn_texto_dividir_liberar(jn);

    // === 7. Recortar (trim) ===
    printf("=== 7. Recortar ===\n");
    CadenaSegura tr = _syn_texto_recortar(CS("  hola  "));
    CHECK(tr.longitud == 4 && memcmp(tr.datos, "hola", 4) == 0, "recortar(\"  hola  \") == \"hola\"");
    CadenaSegura tr2 = _syn_texto_recortar(CS("sin_espacios"));
    CHECK(tr2.longitud == 12, "recortar(\"sin_espacios\") sin cambio");

    // === 8. Mayúsculas / Minúsculas ===
    printf("=== 8. Mayusculas / Minusculas ===\n");
    CadenaSegura mu = _syn_texto_mayusculas(CS("hola"));
    CHECK(mu.longitud == 4 && memcmp(mu.datos, "HOLA", 4) == 0, "mayusculas(\"hola\") == \"HOLA\"");
    CadenaSegura mi = _syn_texto_minusculas(CS("HOLA"));
    CHECK(mi.longitud == 4 && memcmp(mi.datos, "hola", 4) == 0, "minusculas(\"HOLA\") == \"hola\"");

    // === 9. Comienza con / Termina con ===
    printf("=== 9. Comienza con / Termina con ===\n");
    CHECK(_syn_texto_comienza_con(CS("hola mundo"), CS("hola")) == 1, "comienza_con(\"hola mundo\", \"hola\") == true");
    CHECK(_syn_texto_comienza_con(CS("hola mundo"), CS("mundo")) == 0, "comienza_con(\"hola mundo\", \"mundo\") == false");
    CHECK(_syn_texto_termina_con(CS("hola mundo"), CS("mundo")) == 1, "termina_con(\"hola mundo\", \"mundo\") == true");
    CHECK(_syn_texto_termina_con(CS("hola mundo"), CS("hola")) == 0, "termina_con(\"hola mundo\", \"hola\") == false");

    // === 10. Índice de ===
    printf("=== 10. Indice de ===\n");
    CHECK(_syn_texto_indice_de(CS("hola mundo"), CS("mundo")) == 5, "indice_de(\"hola mundo\", \"mundo\") == 5");
    CHECK(_syn_texto_indice_de(CS("hola mundo"), CS("xyz")) == -1, "indice_de(\"hola mundo\", \"xyz\") == -1");
    CHECK(_syn_texto_indice_de(CS("abc"), CS("")) == 0, "indice_de(\"abc\", \"\") == 0");

    // === 11. Repetir ===
    printf("=== 11. Repetir ===\n");
    CadenaSegura rep = _syn_texto_repetir(CS("ab"), 3);
    CHECK(rep.longitud == 6 && memcmp(rep.datos, "ababab", 6) == 0, "repetir(\"ab\", 3) == \"ababab\"");
    CadenaSegura rep0 = _syn_texto_repetir(CS("x"), 0);
    CHECK(rep0.longitud == 0, "repetir(\"x\", 0) == \"\"");

    // === 12. Invertir ===
    printf("=== 12. Invertir ===\n");
    CadenaSegura inv = _syn_texto_invertir(CS("abc"));
    CHECK(inv.longitud == 3 && memcmp(inv.datos, "cba", 3) == 0, "invertir(\"abc\") == \"cba\"");
    CadenaSegura inv1 = _syn_texto_invertir(CS("a"));
    CHECK(inv1.longitud == 1 && inv1.datos[0] == 'a', "invertir(\"a\") == \"a\"");

    printf("\n=== RESULTADO: %d passed, %d failed ===\n", passed, failed);
    return failed > 0 ? 1 : 0;
}
