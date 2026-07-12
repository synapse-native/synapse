// smoke_toml.c — Smoke test para std.toml con RAII
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

typedef struct { int longitud; const char* datos; } CadenaSegura;

// Forward declarations (matched to synapse_rt.c)
typedef struct ParToml ParToml;
typedef struct NodoToml NodoToml;

struct ParToml {
    CadenaSegura clave;
    NodoToml* valor;
};

struct NodoToml {
    int tipo;           // -1=Error, 0=Nulo, 1=Tabla, 2=Cadena, 3=TablaEnLinea
    CadenaSegura valor_str;
    ParToml* pares;
    int longitud;
};

// Pool stubs
#define POOL_BLOQUES 64
#define TAMANO_BLOQUE 4096

extern NodoToml _toml_parse(CadenaSegura entrada);
extern NodoToml _toml_object_get(NodoToml nodo, CadenaSegura clave);
extern void _toml_nodo_liberar(NodoToml n);

int main(int argc, char** argv) {
    (void)argc; (void)argv;

    const char* toml_data =
        "[proyecto]\n"
        "nombre = \"Synapse\"\n"
        "version = \"1.5.0\"\n"
        "punto_entrada = \"src/main.syn\"\n"
        "\n"
        "[dependencias]\n"
        "mathlib = { git = \"https://github.com/ejemplo/mathlib.git\", rev = \"main\" }\n";

    CadenaSegura entrada = {
        .longitud = (int)strlen(toml_data),
        .datos = toml_data
    };

    printf("=== Test TOML Parser ===\n");

    NodoToml doc = _toml_parse(entrada);
    if (doc.tipo < 0) {
        printf("FALLO: Error de parseo TOML: %s\n",
               doc.valor_str.datos ? doc.valor_str.datos : "desconocido");
        _toml_nodo_liberar(doc);
        return 1;
    }
    printf("Parseo TOML OK (tipo=%d, pares=%d)\n", doc.tipo, doc.longitud);

    NodoToml seccion_proy = _toml_object_get(doc,
        (CadenaSegura){ .longitud = 8, .datos = "proyecto" });
    if (seccion_proy.tipo != 1) {
        printf("FALLO: No se encontro seccion 'proyecto' (tipo=%d)\n", seccion_proy.tipo);
        _toml_nodo_liberar(seccion_proy); _toml_nodo_liberar(doc);
        return 1;
    }
    printf("Seccion [proyecto] OK (pares=%d)\n", seccion_proy.longitud);

    NodoToml campo_nombre = _toml_object_get(seccion_proy,
        (CadenaSegura){ .longitud = 6, .datos = "nombre" });
    if (campo_nombre.tipo != 2) {
        printf("FALLO: campo 'nombre' no es string (tipo=%d)\n", campo_nombre.tipo);
        _toml_nodo_liberar(campo_nombre); _toml_nodo_liberar(seccion_proy); _toml_nodo_liberar(doc);
        return 1;
    }
    printf("campo nombre = \"%.*s\" OK\n",
           campo_nombre.valor_str.longitud, campo_nombre.valor_str.datos);

    NodoToml campo_pe = _toml_object_get(seccion_proy,
        (CadenaSegura){ .longitud = 13, .datos = "punto_entrada" });
    if (campo_pe.tipo != 2) {
        printf("FALLO: campo 'punto_entrada' no es string (tipo=%d)\n", campo_pe.tipo);
        _toml_nodo_liberar(campo_pe); _toml_nodo_liberar(campo_nombre);
        _toml_nodo_liberar(seccion_proy); _toml_nodo_liberar(doc);
        return 1;
    }
    printf("campo punto_entrada = \"%.*s\" OK\n",
           campo_pe.valor_str.longitud, campo_pe.valor_str.datos);

    NodoToml campo_faltante = _toml_object_get(seccion_proy,
        (CadenaSegura){ .longitud = 20, .datos = "no_existe" });
    if (campo_faltante.tipo != 0) {
        printf("FALLO: campo faltante debio ser Nulo (tipo=%d)\n", campo_faltante.tipo);
        _toml_nodo_liberar(campo_faltante); _toml_nodo_liberar(campo_pe);
        _toml_nodo_liberar(campo_nombre); _toml_nodo_liberar(seccion_proy);
        _toml_nodo_liberar(doc);
        return 1;
    }
    printf("campo faltante devuelve Nulo OK\n");

    // Liberar independientes (simula RAII por scope)
    _toml_nodo_liberar(campo_faltante);
    _toml_nodo_liberar(campo_pe);
    _toml_nodo_liberar(campo_nombre);
    _toml_nodo_liberar(seccion_proy);

    NodoToml seccion_deps = _toml_object_get(doc,
        (CadenaSegura){ .longitud = 12, .datos = "dependencias" });
    if (seccion_deps.tipo != 1) {
        printf("FALLO: No se encontro seccion 'dependencias' (tipo=%d)\n", seccion_deps.tipo);
        _toml_nodo_liberar(seccion_deps); _toml_nodo_liberar(doc);
        return 1;
    }
    printf("Seccion [dependencias] OK (pares=%d)\n", seccion_deps.longitud);

    NodoToml campo_mathlib = _toml_object_get(seccion_deps,
        (CadenaSegura){ .longitud = 7, .datos = "mathlib" });
    if (campo_mathlib.tipo != 3) {
        printf("FALLO: campo 'mathlib' no es inline table (tipo=%d)\n", campo_mathlib.tipo);
        _toml_nodo_liberar(campo_mathlib); _toml_nodo_liberar(seccion_deps);
        _toml_nodo_liberar(doc);
        return 1;
    }
    printf("campo mathlib es inline table OK (pares=%d)\n", campo_mathlib.longitud);

    NodoToml mathlib_git = _toml_object_get(campo_mathlib,
        (CadenaSegura){ .longitud = 3, .datos = "git" });
    if (mathlib_git.tipo != 2) {
        printf("FALLO: mathlib.git no es string (tipo=%d)\n", mathlib_git.tipo);
        _toml_nodo_liberar(mathlib_git); _toml_nodo_liberar(campo_mathlib);
        _toml_nodo_liberar(seccion_deps); _toml_nodo_liberar(doc);
        return 1;
    }
    printf("mathlib.git = \"%.*s\" OK\n",
           mathlib_git.valor_str.longitud, mathlib_git.valor_str.datos);

    // Liberar todo en orden inverso (simula RAII)
    _toml_nodo_liberar(mathlib_git);
    _toml_nodo_liberar(campo_mathlib);
    _toml_nodo_liberar(seccion_deps);
    _toml_nodo_liberar(doc);

    printf("=== FIN: TODOS LOS TESTS PASARON ===\n");
    return 0;
}
