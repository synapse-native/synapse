// cumple Manual 6 §3: JSON parsing
// runtime/core/json.h — std.json: Deterministic JSON Parser API
// D-9(d) corte 7: extraído de synapse_rt.c (lines 72-461, byte-identical)
// Manual 5 §7: std.json (Deserializador Determinista, arquitectura simdjson-style)
#ifndef JSON_H
#define JSON_H

#include "synapse_rt_types.h"

// Public API — same signatures as the original (defined in synapse_rt.c)
NodoJson _json_nodo_new(void);
void _json_nodo_liberar(NodoJson n);
NodoJson _json_parse(CadenaSegura entrada);
NodoJson _json_nodo_clonar(NodoJson src);
NodoJson _json_array_get(NodoJson nodo, int indice);
NodoJson _json_object_get(NodoJson nodo, CadenaSegura clave);

// Serializador: NodoJson → CadenaSegura (JSON texto)
// Manual 3 §12.2: a_texto — genera JSON determinista desde un árbol NodoJson
CadenaSegura _json_a_texto(NodoJson nodo);

#endif /* JSON_H */