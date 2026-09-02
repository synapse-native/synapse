// cumple Manual 6 3: TOML parsing
// runtime/core/toml.h — std.toml: Deterministic TOML Parser API
// D-9(d) corte 9: extraído de synapse_rt.c (texto byte-idéntico)
// Manual 5 §7: std.toml (deserializador TOML para configuracion Axon)
#ifndef TOML_H
#define TOML_H

#include "synapse_rt_types.h"

// Public API — same signatures as the original (defined in synapse_rt.c)
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

NodoToml _toml_nodo_new(void);
void _toml_nodo_liberar(NodoToml n);
NodoToml _toml_object_get(NodoToml nodo, CadenaSegura clave);
NodoToml _toml_parse(CadenaSegura entrada);

#endif /* TOML_H */