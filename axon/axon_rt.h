// cumple Manual 6 §5: axon runtime + aislamiento de workspaces (Fase 31.1)
// axón/axon_rt.h — Axon workspace isolation: declarations
// D-9(d) corte 11: extraído de synapse_rt.c (modularización)
// Fase 31.1: Workspace isolation — cache por proyecto en .axon/cache/
// (Manual 31 §2.2). Reemplaza el cache global ~/.axon/cache/ con cache
// local por workspace, evitando colisiones de versiones (Manual 31 §2.1).

#ifndef AXON_RT_H
#define AXON_RT_H

#include "synapse_rt_types.h"

// --- Workspace Isolation (Manual 31 §2.3) ---
// Estas funciones implementan el aislamiento de workspaces: cada proyecto
// tiene su propio .axon/cache/ y axon.lock, resolviendo dependencias de
// forma local y determinista (offline-first con lockfile existente).

// axon_workspace_cache_path: retorna la ruta del directorio de cache
// para un proyecto dado. Formato: <ruta_proyecto>/.axon/cache/
// Retorna: puntero a buffer estático (válido hasta la siguiente llamada),
// o NULL en error.
const char* _syn_axon_workspace_cache_path(const char* ruta_proyecto);

// axon_workspace_crear: crea la estructura de directorios para un
// workspace aislado: <ruta_proyecto>/.axon/cache/
// Retorna: 0 OK, -1 error.
int _syn_axon_workspace_crear(const char* ruta_proyecto);

// axon_workspace_resolver: resuelve dependencias de un proyecto usando
// su lockfile local (<ruta_proyecto>/axón.lock) y cache aislado.
// Flujo (Manual 31 §2.2):
//   1. Leer axon.lock del proyecto
//   2. Para cada paquete: verificar hash en .axon/cache/
//   3. Si no está en cache, descargar y guardar en .axon/cache/
// Retorna: número de paquetes resueltos, -1 error.
int _syn_axon_workspace_resolver(const char* ruta_proyecto, const char* lock_path);

#endif /* AXON_RT_H */
