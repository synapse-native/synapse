// runtime/core/coverage.c — Instrumentación de aristas (ME coverage_aristas, Fase 33.2)
// cumple Manual 9 §6.1: synapse test --coverage genera informes de cobertura.
// cumple Manual 9 §6.2: el volcado JSON alimenta el informe HTML de cobertura
// (nucleo/coverage.syn, validación cruzada CI/CD Fase 31).
// cumple Manual 5 §2.6: memoria del runtime sin GC — buffer estático sin gestión
// propia (patrón trazas del debugger); sin fugas ni punteros colgantes.
// Diseño (ROADMAP §33.2): buffer de aristas en memoria + volcado JSON al salir
// (atexit). La bandera es OFF por defecto (SYNAPSE_COVERAGE=1 la activa): sin
// ella ni este módulo ni las sondas del emisor alteran el programa (bootstrap
// determinista — cumple Manual 1 §6).
// Modelo: el EMISOR conoce la anidación léxica de ramas, así que cada sonda
// SYN_COV(l, d) reporta la clave de rama l y su rama PADRE estática d (0 si
// no tiene). Llegar a l implica recorrer la arista (d -> l): las aristas
// cubiertas son las ramas ejecutadas; las NO ejecutadas salen del catálogo
// estático (mismo emisor, _syn_cov_ramas_estaticas). Sin gestión de memoria
// propia: el buffer es estático (patrón trazas del debugger, D-9(d) corte 5).
#include "synapse_rt_types.h"
#include "runtime/core/coverage.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define SYN_COV_MAX_RAMAS 1024

typedef struct {
    int64_t l;  // clave de rama (linea<<8 | ordinal del emisor)
    int64_t d;  // clave de la rama padre estática (0 = sin padre)
    int cubierta;
} SynCovRama;

static SynCovRama _syn_cov_ramas[SYN_COV_MAX_RAMAS];
static int _syn_cov_ramas_n = 0;
static int _syn_cov_estimado = 0;
static int _syn_cov_on = 0;
static char _syn_cov_ruta[640] = {0};   // ruta completa del JSON de salida
static char _syn_cov_fuente[260] = {0}; // nombre del fuente (para el informe)
static int _syn_cov_volcado = 0;
static int _syn_cov_atexit_reg = 0;

static void _syn_cov_atexit(void);  // fwd: habilitar() registra el volcado

void _syn_cov_habilitar(void) {
    _syn_cov_on = 1;
    // Exe instrumentado por el emisor: la config ya está horneada (el main
    // llamó a _syn_cov_configurar ANTES) — registrar el volcado aquí, sin
    // depender de entorno. Idempotente.
    if (!_syn_cov_atexit_reg && _syn_cov_ruta[0]) {
        atexit(_syn_cov_atexit);
        _syn_cov_atexit_reg = 1;
    }
}

void _syn_cov_total(int total) {
    _syn_cov_estimado = total;
}

void _syn_cov_configurar(const char* archivo_fuente, const char* ruta_base) {
    if (archivo_fuente && archivo_fuente[0]) {
        snprintf(_syn_cov_fuente, sizeof(_syn_cov_fuente), "%s", archivo_fuente);
    }
    if (ruta_base && ruta_base[0]) {
        snprintf(_syn_cov_ruta, sizeof(_syn_cov_ruta), "%s.coverage.json", ruta_base);
    }
}

// Catálogo estático del emisor: "l:d,l:d,..." (clave:padre). Idempotente.
void _syn_cov_ramas_estaticas(const char* pares) {
    if (!pares) {
        return;
    }
    const char* p = pares;
    while (*p && _syn_cov_ramas_n < SYN_COV_MAX_RAMAS) {
        char* fin = NULL;
        long long l = strtoll(p, &fin, 10);
        if (fin == p) {
            break;
        }
        long long d = 0;
        if (*fin == ':') {
            p = fin + 1;
            d = strtoll(p, &fin, 10);
        }
        int ya = 0;
        for (int i = 0; i < _syn_cov_ramas_n; i++) {
            if (_syn_cov_ramas[i].l == (int64_t)l) { ya = 1; break; }
        }
        if (!ya) {
            _syn_cov_ramas[_syn_cov_ramas_n].l = (int64_t)l;
            _syn_cov_ramas[_syn_cov_ramas_n].d = (int64_t)d;
            _syn_cov_ramas[_syn_cov_ramas_n].cubierta = 0;
            _syn_cov_ramas_n++;
        }
        p = fin;
        if (*p == ',') {
            p++;
        } else {
            break;
        }
    }
}

// Sonda del emisor: la rama l (padre estático d) fue ALCANZADA en ejecución.
// Dedup por clave de rama (el registro es un CONJUNTO, edge coverage).
void _syn_cov(int64_t l, int64_t d) {
    if (!_syn_cov_on) {
        return;
    }
    for (int i = 0; i < _syn_cov_ramas_n; i++) {
        if (_syn_cov_ramas[i].l == l) {
            _syn_cov_ramas[i].cubierta = 1;
            return;
        }
    }
    if (_syn_cov_ramas_n >= SYN_COV_MAX_RAMAS) {
        return;
    }
    _syn_cov_ramas[_syn_cov_ramas_n].l = l;
    _syn_cov_ramas[_syn_cov_ramas_n].d = d;
    _syn_cov_ramas[_syn_cov_ramas_n].cubierta = 1;
    _syn_cov_ramas_n++;
}

static void _syn_cov_atexit(void) {
    _syn_cov_volcar();
}

__attribute__((constructor))
static void _syn_cov_init(void) {
    const char* env = getenv("SYNAPSE_COVERAGE");
    if (!env || env[0] != '1') {
        return;  // OFF por defecto: el proceso no se altera (bootstrap diff 0)
    }
    _syn_cov_on = 1;
    _syn_cov_atexit_reg = 1;  // el constructor ya registró su propio atexit
    const char* out = getenv("SYNAPSE_COVERAGE_OUT");
    const char* fuente = getenv("SYNAPSE_COVERAGE_FUENTE");
    if (fuente && fuente[0]) {
        snprintf(_syn_cov_fuente, sizeof(_syn_cov_fuente), "%s", fuente);
    }
    if (out && out[0]) {
        // Ruta completa explícita (el emisor ya añadió .coverage.json o el
        // oráculo configuró otra); sin concatener nada.
        snprintf(_syn_cov_ruta, sizeof(_syn_cov_ruta), "%s", out);
    }
    atexit(_syn_cov_atexit);
}

void _syn_cov_volcar(void) {
    if (!_syn_cov_on || _syn_cov_volcado || !_syn_cov_ruta[0]) {
        return;
    }
    _syn_cov_volcado = 1;
    FILE* f = fopen(_syn_cov_ruta, "wb");
    if (!f) {
        return;  // sin ruta/permiso: silencioso (el informe quedará sin JSON)
    }
    int cubiertas = 0;
    for (int i = 0; i < _syn_cov_ramas_n; i++) {
        if (_syn_cov_ramas[i].cubierta) {
            cubiertas++;
        }
    }
    int estimado = (_syn_cov_estimado > _syn_cov_ramas_n)
                       ? _syn_cov_estimado : _syn_cov_ramas_n;
    fprintf(f, "{\"archivo\":\"%s\",\"total_estimado\":%d,"
               "\"aristas_cubiertas\":%d,\"ramas\":[",
            _syn_cov_fuente, estimado, cubiertas);
    for (int i = 0; i < _syn_cov_ramas_n; i++) {
        fprintf(f, "%s{\"l\":%lld,\"d\":%lld,\"cubierta\":%s}",
                (i > 0) ? "," : "",
                (long long)_syn_cov_ramas[i].l,
                (long long)_syn_cov_ramas[i].d,
                _syn_cov_ramas[i].cubierta ? "true" : "false");
    }
    fprintf(f, "]}\n");
    fclose(f);
}
