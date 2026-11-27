// test_json.c — TDD spec Manual 3 §12 (std.json: JSON parser + serializador)
// Verifica: _json_parse (parser) + _json_a_texto (serializador) + getters
// Si alguna funcion no existe, el test NO compila -> falla TDD.

#include <stdio.h>
#include <string.h>
#include <assert.h>
#include <stdlib.h>
#include "../synapse_rt_types.h"
#include "../runtime/core/json.h"

static int _tests_total = 0;
static int _tests_passed = 0;

#define TEST(name) do { \
    _tests_total++; \
    printf("  TEST %d: %s ... ", _tests_total, name); \
    fflush(stdout); \
} while(0)

#define PASS() do { _tests_passed++; printf("PASS\n"); } while(0)
#define FAIL(msg) do { printf("FAIL: %s\n", msg); } while(0)

#define ASSERT(cond, msg) do { \
    if (!(cond)) { FAIL(msg); return; } \
} while(0)

// Helper: crea CadenaSegura con buffer mutable (el parser escribe \0 in-place)
static CadenaSegura cs_mutable(const char* s) {
    int len = (int)strlen(s);
    char* buf = (char*)malloc(len + 1);
    memcpy(buf, s, len + 1);
    return (CadenaSegura){ .longitud = len, .datos = buf };
}

// ============================================================
// §12.2 — Parser: desde_texto
// ============================================================

static void test_parse_null(void) {
    TEST("parse null");
    CadenaSegura s = cs_mutable("null");
    NodoJson n = _json_parse(s);
    ASSERT(n.tipo == 0, "null tipo != 0");
    PASS();
}

static void test_parse_bool_true(void) {
    TEST("parse boolean true");
    CadenaSegura s = cs_mutable("true");
    NodoJson n = _json_parse(s);
    ASSERT(n.tipo == 1, "bool tipo != 1");
    ASSERT(n.valor_bool == 1, "true valor_bool != 1");
    PASS();
}

static void test_parse_bool_false(void) {
    TEST("parse boolean false");
    CadenaSegura s = cs_mutable("false");
    NodoJson n = _json_parse(s);
    ASSERT(n.tipo == 1, "bool tipo != 1");
    ASSERT(n.valor_bool == 0, "false valor_bool != 0");
    PASS();
}

static void test_parse_number(void) {
    TEST("parse number 42");
    CadenaSegura s = cs_mutable("42");
    NodoJson n = _json_parse(s);
    ASSERT(n.tipo == 2, "number tipo != 2");
    ASSERT(n.valor_num == 42.0f, "42 != 42.0");
    PASS();
}

static void test_parse_number_negative(void) {
    TEST("parse number -3.14");
    CadenaSegura s = cs_mutable("-3.14");
    NodoJson n = _json_parse(s);
    ASSERT(n.tipo == 2, "neg number tipo != 2");
    ASSERT(n.valor_num > -3.15f && n.valor_num < -3.13f, "-3.14 fuera de rango");
    PASS();
}

static void test_parse_string(void) {
    TEST("parse string \"hello\"");
    CadenaSegura s = cs_mutable("\"hello\"");
    NodoJson n = _json_parse(s);
    ASSERT(n.tipo == 3, "string tipo != 3");
    ASSERT(n.valor_str.longitud == 5, "string longitud != 5");
    ASSERT(strncmp(n.valor_str.datos, "hello", 5) == 0, "string contenido != hello");
    PASS();
}

static void test_parse_empty_object(void) {
    TEST("parse empty object {}");
    CadenaSegura s = cs_mutable("{}");
    NodoJson n = _json_parse(s);
    ASSERT(n.tipo == 5, "obj tipo != 5");
    ASSERT(n.longitud == 0, "obj vacio longitud != 0");
    PASS();
}

static void test_parse_object_one_field(void) {
    TEST("parse object {\"name\":\"Buffy\"}");
    CadenaSegura s = cs_mutable("{\"name\":\"Buffy\"}");
    NodoJson n = _json_parse(s);
    ASSERT(n.tipo == 5, "obj tipo != 5");
    ASSERT(n.longitud == 1, "obj 1 campo");
    NodoJson val = _json_object_get(n, (CadenaSegura){4, "name"});
    ASSERT(val.tipo == 3, "campo tipo != 3");
    ASSERT(strncmp(val.valor_str.datos, "Buffy", 5) == 0, "campo valor != Buffy");
    PASS();
}

static void test_parse_empty_array(void) {
    TEST("parse empty array []");
    CadenaSegura s = cs_mutable("[]");
    NodoJson n = _json_parse(s);
    ASSERT(n.tipo == 4, "arr tipo != 4");
    ASSERT(n.longitud == 0, "arr vacio longitud != 0");
    PASS();
}

static void test_parse_array_numbers(void) {
    TEST("parse array [1,2,3]");
    CadenaSegura s = cs_mutable("[1,2,3]");
    NodoJson n = _json_parse(s);
    ASSERT(n.tipo == 4, "arr tipo != 4");
    ASSERT(n.longitud == 3, "arr 3 elementos");
    NodoJson e0 = _json_array_get(n, 0);
    ASSERT(e0.tipo == 2 && e0.valor_num == 1.0f, "arr[0] != 1");
    NodoJson e2 = _json_array_get(n, 2);
    ASSERT(e2.tipo == 2 && e2.valor_num == 3.0f, "arr[2] != 3");
    PASS();
}

static void test_parse_nested_object(void) {
    TEST("parse nested {\"a\":{\"b\":42}}");
    CadenaSegura s = cs_mutable("{\"a\":{\"b\":42}}");
    NodoJson n = _json_parse(s);
    ASSERT(n.tipo == 5, "outer tipo != 5");
    NodoJson inner = _json_object_get(n, (CadenaSegura){1, "a"});
    ASSERT(inner.tipo == 5, "inner tipo != 5");
    NodoJson val = _json_object_get(inner, (CadenaSegura){1, "b"});
    ASSERT(val.tipo == 2 && val.valor_num == 42.0f, "nested b != 42");
    PASS();
}

static void test_parse_invalid_json(void) {
    TEST("parse invalid JSON returns error");
    CadenaSegura s = cs_mutable("{invalid}");
    NodoJson n = _json_parse(s);
    ASSERT(n.tipo == -1, "invalido tipo != -1");
    PASS();
}

// ============================================================
// §12.2 — Serializador: a_texto
// ============================================================

static void test_a_texto_null(void) {
    TEST("a_texto null");
    NodoJson n = {0}; n.tipo = 0;
    CadenaSegura out = _json_a_texto(n);
    ASSERT(out.longitud == 4, "null longitud != 4");
    ASSERT(strncmp(out.datos, "null", 4) == 0, "null != \"null\"");
    PASS();
}

static void test_a_texto_bool_true(void) {
    TEST("a_texto true");
    NodoJson n = {0}; n.tipo = 1; n.valor_bool = 1;
    CadenaSegura out = _json_a_texto(n);
    ASSERT(out.longitud == 4, "true longitud != 4");
    ASSERT(strncmp(out.datos, "true", 4) == 0, "true != \"true\"");
    PASS();
}

static void test_a_texto_bool_false(void) {
    TEST("a_texto false");
    NodoJson n = {0}; n.tipo = 1; n.valor_bool = 0;
    CadenaSegura out = _json_a_texto(n);
    ASSERT(out.longitud == 5, "false longitud != 5");
    ASSERT(strncmp(out.datos, "false", 5) == 0, "false != \"false\"");
    PASS();
}

static void test_a_texto_number(void) {
    TEST("a_texto number 42");
    NodoJson n = {0}; n.tipo = 2; n.valor_num = 42.0f;
    CadenaSegura out = _json_a_texto(n);
    ASSERT(out.longitud > 0, "number vacio");
    ASSERT(strncmp(out.datos, "42", 2) == 0, "42 != \"42\"");
    PASS();
}

static void test_a_texto_string(void) {
    TEST("a_texto string \"hello\"");
    NodoJson n = {0}; n.tipo = 3;
    n.valor_str = (CadenaSegura){ .datos = "hello", .longitud = 5 };
    CadenaSegura out = _json_a_texto(n);
    ASSERT(out.longitud == 7, "string longitud != 7 (\"hello\")");
    ASSERT(strncmp(out.datos, "\"hello\"", 7) == 0, "hello != \"\\\"hello\\\"\"");
    PASS();
}

static void test_a_texto_empty_array(void) {
    TEST("a_texto empty array []");
    NodoJson n = {0}; n.tipo = 4; n.longitud = 0;
    CadenaSegura out = _json_a_texto(n);
    ASSERT(out.longitud == 2, "[] longitud != 2");
    ASSERT(strncmp(out.datos, "[]", 2) == 0, "[] != \"[]\"");
    PASS();
}

static void test_a_texto_empty_object(void) {
    TEST("a_texto empty object {}");
    NodoJson n = {0}; n.tipo = 5; n.longitud = 0;
    CadenaSegura out = _json_a_texto(n);
    ASSERT(out.longitud == 2, "{} longitud != 2");
    ASSERT(strncmp(out.datos, "{}", 2) == 0, "{} != \"{}\"");
    PASS();
}

static void test_roundtrip_string(void) {
    TEST("roundtrip: parse -> a_texto preserves value");
    CadenaSegura input = cs_mutable("\"hello world\"");
    NodoJson n = _json_parse(input);
    ASSERT(n.tipo == 3, "parse tipo != 3");
    CadenaSegura out = _json_a_texto(n);
    ASSERT(out.longitud == 13, "roundtrip longitud != 13");
    ASSERT(strncmp(out.datos, "\"hello world\"", 13) == 0, "roundtrip valor diferente");
    PASS();
}

static void test_roundtrip_number(void) {
    TEST("roundtrip: parse -> a_texto preserves number");
    CadenaSegura input = cs_mutable("42");
    NodoJson n = _json_parse(input);
    ASSERT(n.tipo == 2, "parse tipo != 2");
    CadenaSegura out = _json_a_texto(n);
    ASSERT(out.longitud == 2, "roundtrip longitud != 2");
    ASSERT(strncmp(out.datos, "42", 2) == 0, "roundtrip valor diferente");
    PASS();
}

static void test_roundtrip_object(void) {
    TEST("roundtrip: parse -> a_texto preserves object");
    CadenaSegura input = cs_mutable("{\"key\":\"val\",\"n\":1}");
    NodoJson n = _json_parse(input);
    ASSERT(n.tipo == 5, "parse tipo != 5");
    CadenaSegura out = _json_a_texto(n);
    ASSERT(out.longitud == 19, "roundtrip obj longitud != 19");
    ASSERT(strncmp(out.datos, "{\"key\":\"val\",\"n\":1}", 19) == 0, "roundtrip obj diferente");
    PASS();
}

static void test_roundtrip_array(void) {
    TEST("roundtrip: parse -> a_texto preserves array");
    CadenaSegura input = cs_mutable("[1,2,3]");
    NodoJson n = _json_parse(input);
    ASSERT(n.tipo == 4, "parse tipo != 4");
    CadenaSegura out = _json_a_texto(n);
    ASSERT(out.longitud == 7, "roundtrip arr longitud != 7");
    ASSERT(strncmp(out.datos, "[1,2,3]", 7) == 0, "roundtrip arr diferente");
    PASS();
}

// ============================================================
// main
// ============================================================

int main(void) {
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    printf("=== test_json.c — Manual 3 §12 (std.json) ===\n\n");

    printf("[Parser: _json_parse]\n");
    test_parse_null();
    test_parse_bool_true();
    test_parse_bool_false();
    test_parse_number();
    test_parse_number_negative();
    test_parse_string();
    test_parse_empty_object();
    test_parse_object_one_field();
    test_parse_empty_array();
    test_parse_array_numbers();
    test_parse_nested_object();
    test_parse_invalid_json();

    printf("\n[Serializador: _json_a_texto]\n");
    test_a_texto_null();
    test_a_texto_bool_true();
    test_a_texto_bool_false();
    test_a_texto_number();
    test_a_texto_string();
    test_a_texto_empty_array();
    test_a_texto_empty_object();

    printf("\n[Roundtrip: parse -> a_texto]\n");
    test_roundtrip_string();
    test_roundtrip_number();
    test_roundtrip_object();
    test_roundtrip_array();

    printf("\n=== Results: %d/%d passed ===\n", _tests_passed, _tests_total);
    return (_tests_passed == _tests_total) ? 0 : 1;
}
