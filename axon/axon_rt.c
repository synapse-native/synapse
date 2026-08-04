// axon_rt.c — Axon package manager runtime (unique functions only)
//
// This file contains ONLY the Axon-specific functions that are NOT
// provided by the modular runtime (synapse_rt.c, synapse_rt_memory.c,
// synapse_rt_concurrency.c). All shared runtime functions come from
// those modules via extern declarations.
//
// Compilar: gcc -c axon_rt.c -o axon_rt.o
// Linkear: gcc programa.c synapse_rt.o synapse_rt_memory.o synapse_rt_concurrency.o axon_rt.o tweetnacl.o -o programa -lpthread

#include "synapse_rt_types.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

// ============================================================
// TOML types (local definition, same layout as synapse_rt.c)
// ============================================================
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

// ============================================================
// Extern: functions provided by modular runtime (synapse_rt.c)
// ============================================================
extern NodoToml _toml_parse(CadenaSegura entrada);
extern void _toml_nodo_liberar(NodoToml n);
extern NodoToml _toml_object_get(NodoToml nodo, CadenaSegura clave);

// ============================================================
// SemVer helpers (static — local to this TU)
// ============================================================

/* _syn_parse_ver: parse "x.y.z" version string into components */
static int _syn_parse_ver(const char* v, int* maj, int* min, int* pat) {
    *maj = 0; *min = 0; *pat = 0;  // init before sscanf (partial match = 0 for rest)
    if (!v || !*v) return 0;
    return sscanf(v, "%d.%d.%d", maj, min, pat) >= 1;
}

/* _syn_semver_match: SemVer constraint matching.
 * Supports: exact, ^caret, ~tilde constraints.
 * Retorna: 1 si la version cumple la constraint, 0 en caso contrario.
 */
int _syn_semver_match(const char* constraint, const char* version) {
    if (!constraint || !*constraint || !version || !*version) return 0;

    int cmaj = 0, cmin = 0, cpat = 0;
    int vmaj = 0, vmin = 0, vpat = 0;

    char prefix = constraint[0];
    const char* cver = constraint;
    if (prefix == '^' || prefix == '~') {
        cver = constraint + 1;
    } else {
        prefix = 0;  // exact match
    }

    if (!_syn_parse_ver(cver, &cmaj, &cmin, &cpat)) return 0;
    if (!_syn_parse_ver(version, &vmaj, &vmin, &vpat)) return 0;

    if (prefix == '^') {
        // Caret: compatible releases.
        int upper_maj = cmaj, upper_min = cmin, upper_pat = cpat;
        if (cmaj > 0) {
            upper_maj = cmaj + 1; upper_min = 0; upper_pat = 0;
        } else if (cmin > 0) {
            upper_min = cmin + 1; upper_pat = 0;
        } else {
            upper_pat = cpat + 1;
        }
        long long lower = (long long)cmaj * 1000000 + cmin * 1000 + cpat;
        long long upper = (long long)upper_maj * 1000000 + upper_min * 1000 + upper_pat;
        long long actual = (long long)vmaj * 1000000 + vmin * 1000 + vpat;
        return (actual >= lower && actual < upper) ? 1 : 0;
    }

    if (prefix == '~') {
        // Tilde: patch-level. ~1.2.3 means >=1.2.3 and <1.3.0
        if (vmaj != cmaj) return 0;
        if (vmin != cmin) return 0;
        return (vpat >= cpat) ? 1 : 0;
    }

    // Exact version
    return (cmaj == vmaj && cmin == vmin && cpat == vpat) ? 1 : 0;
}

// ============================================================
// Axon: manifest validation
// ============================================================

/* _syn_axon_validar_manifiesto: valida que un archivo TOML contenga
 * la estructura minima de manifiesto Axon ([paquete] con nombre, version,
 * autor, tipo, punto_entrada).
 * Retorna: 0 si es valido, -1 si hay error.
 */
int _syn_axon_validar_manifiesto(const char* toml_path) {
    FILE* f = fopen(toml_path, "rb");
    if (!f) {
        fprintf(stderr, "[Axon] ERR_MANIFEST: no se pudo abrir %s\n", toml_path);
        return -1;
    }
    fseek(f, 0, SEEK_END);
    long fsz = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (fsz <= 0) { fclose(f); return -1; }
    char* buf = (char*)malloc((size_t)fsz + 1);
    if (!buf) { fclose(f); return -1; }
    size_t nread = fread(buf, 1, (size_t)fsz, f);
    fclose(f);
    if ((long)nread != fsz) { free(buf); return -1; }
    buf[fsz] = 0;

    CadenaSegura input = { .longitud = (int)fsz, .datos = buf };
    NodoToml root = _toml_parse(input);
    free(buf);

    if (root.tipo < 0) {
        fprintf(stderr, "[Axon] ERR_MANIFEST: error de parseo en %s\n", toml_path);
        if (root.valor_str.datos) free((void*)root.valor_str.datos);
        return -1;
    }

    int has_paquete = 0, has_nombre = 0, has_version = 0, has_autor = 0;
    int has_tipo = 0, has_punto_entrada = 0;
    int valid = 1;

    for (int i = 0; i < root.longitud; i++) {
        ParToml* sec = &root.pares[i];
        int slen = sec->clave.longitud;
        const char* sname = sec->clave.datos;

        if (slen == 7 && memcmp(sname, "paquete", 7) == 0) {
            has_paquete = 1;
            NodoToml* paq = sec->valor;
            if (paq->tipo == 1 || paq->tipo == 3) {
                for (int j = 0; j < paq->longitud; j++) {
                    ParToml* fld = &paq->pares[j];
                    int flen = fld->clave.longitud;
                    const char* fname = fld->clave.datos;
                    if (flen == 6 && memcmp(fname, "nombre", 6) == 0) {
                        has_nombre = 1;
                    } else if (flen == 7 && memcmp(fname, "version", 7) == 0) {
                        has_version = 1;
                    } else if (flen == 5 && memcmp(fname, "autor", 5) == 0) {
                        has_autor = 1;
                    } else if (flen == 5 && memcmp(fname, "tipo", 5) == 0) {
                        has_tipo = 1;
                    } else if (flen == 13 && memcmp(fname, "punto_entrada", 13) == 0) {
                        has_punto_entrada = 1;
                    }
                }
            }
        }

        // Optional: [dependencias] section — no validation required
        // Optional: [parametros] section — no validation required
    }

    if (!has_paquete) { fprintf(stderr, "[Axon] ERR_MANIFEST: falta seccion [paquete]\n"); valid = 0; }
    if (!has_nombre) { fprintf(stderr, "[Axon] ERR_MANIFEST: falta 'nombre' en [paquete]\n"); valid = 0; }
    if (!has_version) { fprintf(stderr, "[Axon] ERR_MANIFEST: falta 'version' en [paquete]\n"); valid = 0; }
    if (!has_autor) { fprintf(stderr, "[Axon] ERR_MANIFEST: falta 'autor' en [paquete]\n"); valid = 0; }
    if (!has_tipo) { fprintf(stderr, "[Axon] ERR_MANIFEST: falta 'tipo' en [paquete]\n"); valid = 0; }
    if (!has_punto_entrada) { fprintf(stderr, "[Axon] ERR_MANIFEST: falta 'punto_entrada' en [paquete]\n"); valid = 0; }

    _toml_nodo_liberar(root);
    return valid ? 0 : -1;
}
