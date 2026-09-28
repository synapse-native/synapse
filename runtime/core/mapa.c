// cumple Manual 6 3: mapa hash
// cumple Manual 6 §3.1: externo funcion mapa del runtime C
// runtime/core/mapa.c — Simple hash map for Syquex lib/mapa.syq
// Manual 3 §5.2: Mapa<K,V> — diccionario hash
// Implementación simple: array de pares con lineal probing

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include "synapse_rt_types.h"

#define MAPA_CAP_INICIAL 32
#define MAPA_VACIO 0
#define MAPA_OCUPADO 1
#define MAPA_BORRADO 2

typedef struct {
    char* clave;
    int64_t valor;
    int estado;  // VACIO/OCUPADO/BORRADO
} ParMapa;

typedef struct {
    ParMapa* pares;
    int capacidad;
    int longitud;
} MapaSyn;

// Hash simple djb2
static uint32_t _mapa_hash(const char* clave) {
    uint32_t hash = 5381;
    while (*clave) {
        hash = ((hash << 5) + hash) + (unsigned char)*clave;
        clave++;
    }
    return hash;
}

// --- Creación ---

void* _syn_mapa_crear(void) {
    MapaSyn* m = (MapaSyn*)malloc(sizeof(MapaSyn));
    if (!m) return NULL;
    m->pares = (ParMapa*)calloc(MAPA_CAP_INICIAL, sizeof(ParMapa));
    if (!m->pares) { free(m); return NULL; }
    m->capacidad = MAPA_CAP_INICIAL;
    m->longitud = 0;
    return m;
}

// --- Redimensionar ---

static void _mapa_redimensionar(MapaSyn* m) {
    int nueva_cap = m->capacidad * 2;
    ParMapa* nuevos = (ParMapa*)calloc(nueva_cap, sizeof(ParMapa));
    if (!nuevos) return;

    for (int i = 0; i < m->capacidad; i++) {
        if (m->pares[i].estado == MAPA_OCUPADO) {
            uint32_t h = _mapa_hash(m->pares[i].clave) % nueva_cap;
            while (nuevos[h].estado == MAPA_OCUPADO) {
                h = (h + 1) % nueva_cap;
            }
            nuevos[h].clave = m->pares[i].clave;
            nuevos[h].valor = m->pares[i].valor;
            nuevos[h].estado = MAPA_OCUPADO;
        }
    }
    free(m->pares);
    m->pares = nuevos;
    m->capacidad = nueva_cap;
}

// --- Búsqueda interna ---

static int _mapa_buscar(MapaSyn* m, const char* clave) {
    uint32_t h = _mapa_hash(clave) % m->capacidad;
    for (int i = 0; i < m->capacidad; i++) {
        int idx = (h + i) % m->capacidad;
        if (m->pares[idx].estado == MAPA_VACIO) return -1;
        if (m->pares[idx].estado == MAPA_OCUPADO &&
            strcmp(m->pares[idx].clave, clave) == 0) {
            return idx;
        }
    }
    return -1;
}

// --- Operaciones ---

int _syn_mapa_longitud(void* m) {
    if (!m) return 0;
    return ((MapaSyn*)m)->longitud;
}

void _syn_mapa_poner(void* m, const char* clave, int64_t valor) {
    if (!m || !clave) return;
    MapaSyn* mp = (MapaSyn*)m;

    // Redimensionar si >70% lleno
    if (mp->longitud > mp->capacidad * 70 / 100) {
        _mapa_redimensionar(mp);
    }

    uint32_t h = _mapa_hash(clave) % mp->capacidad;
    for (int i = 0; i < mp->capacidad; i++) {
        int idx = (h + i) % mp->capacidad;
        if (mp->pares[idx].estado == MAPA_VACIO ||
            mp->pares[idx].estado == MAPA_BORRADO) {
            mp->pares[idx].clave = strdup(clave);
            if (!mp->pares[idx].clave) return;  // OOM safety
            mp->pares[idx].valor = valor;
            mp->pares[idx].estado = MAPA_OCUPADO;
            mp->longitud++;
            return;
        }
        if (mp->pares[idx].estado == MAPA_OCUPADO &&
            strcmp(mp->pares[idx].clave, clave) == 0) {
            mp->pares[idx].valor = valor;
            return;
        }
    }
}

int64_t _syn_mapa_obtener(void* m, const char* clave) {
    if (!m || !clave) return 0;
    int idx = _mapa_buscar((MapaSyn*)m, clave);
    if (idx < 0) return 0;
    return ((MapaSyn*)m)->pares[idx].valor;
}

int _syn_mapa_contiene(void* m, const char* clave) {
    if (!m || !clave) return 0;
    return _mapa_buscar((MapaSyn*)m, clave) >= 0 ? 1 : 0;
}

void _syn_mapa_eliminar(void* m, const char* clave) {
    if (!m || !clave) return;
    MapaSyn* mp = (MapaSyn*)m;
    int idx = _mapa_buscar(mp, clave);
    if (idx >= 0) {
        free(mp->pares[idx].clave);
        mp->pares[idx].clave = NULL;
        mp->pares[idx].estado = MAPA_BORRADO;
        mp->longitud--;
    }
}

void _syn_mapa_limpiar(void* m) {
    if (!m) return;
    MapaSyn* mp = (MapaSyn*)m;
    for (int i = 0; i < mp->capacidad; i++) {
        if (mp->pares[i].estado == MAPA_OCUPADO) {
            free(mp->pares[i].clave);
            mp->pares[i].clave = NULL;
            mp->pares[i].estado = MAPA_VACIO;
        }
    }
    mp->longitud = 0;
}

// --- Claves/Valores (retornan listas simples de punteros) ---

void* _syn_mapa_claves(void* m) {
    // cumple Manual 2 §4.3 (33.4b): lista con las CLAVES reales del mapa.
    // Los slots viajan ENCAJONADOS como CadenaSegura* (heap, paridad
    // _encajonar_slot del emisor: los slots int64 viajan por VALOR para
    // escalares y por DIRECCIÓN para structs/texto — H-R153-2/H-R153-4).
    // Así el desencajonado de Lista<texto> (deref de la dirección) es
    // uniforme en S1 y nativo, y `para k en mapa` (M3 §5.2 keys()/iter())
    // entrega la clave como texto.
    if (!m) return NULL;
    MapaSyn* mp = (MapaSyn*)m;

    extern void* _syn_lista_crear(void);
    extern void _syn_lista_agregar(void*, int64_t);

    void* lista = _syn_lista_crear();
    if (!lista) return NULL;

    for (int i = 0; i < mp->capacidad; i++) {
        if (mp->pares[i].estado == MAPA_OCUPADO) {
            CadenaSegura* caja = (CadenaSegura*)malloc(sizeof(CadenaSegura));
            if (!caja) continue;  // OOM safety
            size_t n = strlen(mp->pares[i].clave);
            char* dup = (char*)malloc(n + 1);
            if (!dup) { free(caja); continue; }  // OOM safety
            memcpy(dup, mp->pares[i].clave, n + 1);
            caja->longitud = (int)n;
            caja->datos = dup;
            _syn_lista_agregar(lista, (int64_t)(intptr_t)caja);
        }
    }
    return lista;
}

void* _syn_mapa_valores(void* m) {
    if (!m) return NULL;
    MapaSyn* mp = (MapaSyn*)m;

    extern void* _syn_lista_crear(void);
    extern void _syn_lista_agregar(void*, int64_t);

    void* lista = _syn_lista_crear();
    if (!lista) return NULL;

    for (int i = 0; i < mp->capacidad; i++) {
        if (mp->pares[i].estado == MAPA_OCUPADO) {
            _syn_lista_agregar(lista, mp->pares[i].valor);
        }
    }
    return lista;
}

// --- Liberación ---

void _syn_mapa_liberar(void* m) {
    if (!m) return;
    MapaSyn* mp = (MapaSyn*)m;
    for (int i = 0; i < mp->capacidad; i++) {
        if (mp->pares[i].estado == MAPA_OCUPADO && mp->pares[i].clave) {
            free(mp->pares[i].clave);
        }
    }
    free(mp->pares);
    free(mp);
}
