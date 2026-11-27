// cumple Manual 9 §5.3: verificacion SHA-256 sin rehashear 873 MB en cada
// arranque. El digest se cachea por ruta + tamano + mtime; nunca se inventa un
// resultado: si la entrada no coincide con el archivo en disco, se rehashea.
// runtime/core/hash_cache.h — API de la cache de digests de archivo (r273).

#ifndef SYN_HASH_CACHE_H
#define SYN_HASH_CACHE_H

#include <stddef.h>

// 1 si la cache esta habilitada (por defecto si; `SYNAPSE_HASH_CACHE=0` la
// desactiva), 0 si no. Tambien devuelve 0 si no hay HOME donde escribir.
int _syn_hash_cache_habilitado(void);

// Busca el digest de `ruta`. Devuelve 1 y escribe 64 hex + NUL en `hash_salida`
// solo si existe una entrada cuyo tamano y mtime coinciden con el archivo en
// disco. Devuelve 0 si no hay entrada valida (hay que hashear).
int _syn_hash_cache_obtener(const char* ruta, char* hash_salida, size_t tam_salida);

// Tamano en bytes de `ruta`, o -1 si no se puede stat-ear. Uso INTERNO C
// (`const char*`): la version invocable desde Synapse es `_syn_tamano_archivo`
// (runtime/core/modelo.c), que recibe CadenaSegura por valor — ver R197.
long long _syn_tamano_archivo_c(const char* ruta);

// Guarda `hash` (64 hex) para `ruta` con el tamano y mtime actuales. No hace
// nada si la cache esta deshabilitada, si el archivo no se puede stat-ear o si
// su mtime es demasiado reciente (no se cachean archivos recien escritos).
void _syn_hash_cache_guardar(const char* ruta, const char* hash);

#endif // SYN_HASH_CACHE_H
