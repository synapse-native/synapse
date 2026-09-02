// cumple Manual 6 §3: cache de compilación
// runtime/core/cache.h — nucleo/cache.syn backing: tipos de caché + helpers TOML
// D-9(d) corte 11: extraído de synapse_rt.c (modularización, patrón toml.c R64)
// Caché de Compilación Incremental (Manual 5 §11): tipos + externs de nucleo/cache.syn.
#ifndef SYNAPSE_CACHE_H
#define SYNAPSE_CACHE_H

#include "synapse_rt_types.h"
#include "runtime/core/toml.h"  // NodoToml

typedef struct CacheEntry {
    CadenaSegura clave;
    CadenaSegura archivo_fuente;
    CadenaSegura archivo_objeto;
    CadenaSegura hash_fuente;
    CadenaSegura hashes_deps;
    CadenaSegura flags_compilacion;
    CadenaSegura version_compilador;
    int64_t timestamp;
    int64_t tamano_bytes;
} CacheEntry;

typedef struct CacheStats {
    int64_t total_entradas;
    int64_t hits;
    int64_t misses;
    int64_t tamano_total_bytes;
    int64_t hits_ultima_ejecucion;
    int64_t misses_ultima_ejecucion;
} CacheStats;

typedef struct CampoToml {
    int64_t tipo;
    CadenaSegura valor_str;
    int64_t valor_ent;
} CampoToml;

struct NodoToml toml_desde_entrada(struct CacheEntry entry);
struct NodoToml toml_desde_stats(struct CacheStats entry);
CadenaSegura a_texto(struct NodoToml doc);
struct NodoToml actualizar_indice(struct NodoToml doc, struct CacheEntry entry);

#endif /* SYNAPSE_CACHE_H */
