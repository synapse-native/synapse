// cumple Manual 9 §5.3: "El modelo se descarga desde Hugging Face o Axon Hub, y
// se verifica su integridad mediante SHA‑256." Verificar 873 MB por arranque
// cuesta segundos; este modulo recuerda el digest ya calculado para el mismo
// contenido (ruta + tamanio + mtime) en ~/.synapse/cache/hash/.
//
// Reglas de honestidad (r273):
//  - Solo se reutiliza un digest que este runtime calculo antes y cuya entrada
//    coincide con el archivo actual (tamanio y mtime).
//  - Si algo no cuadra (falta la entrada, difiere el tamanio, diffiere el mtime,
//    archivo ilegible) se devuelve 0 y el llamador rehashea.
//  - Archivos modificados hace < 5 s no se cachean (evita entradas frescas).
//  - `SYNAPSE_HASH_CACHE=0` desactiva lectura y escritura.
//
// runtime/core/hash_cache.c — cache de digests de archivo (ME r273).
#include "runtime/core/hash_cache.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

#ifdef _WIN32
  #include <direct.h>
  #include <sys/stat.h>
  #define SYN_MKDIR(p) _mkdir(p)
  typedef struct _stat64 syn_stat_t;
  #define SYN_STAT(p, st) _stat64((p), (st))
#else
  #include <sys/stat.h>
  #include <sys/types.h>
  #include <unistd.h>
  #define SYN_MKDIR(p) mkdir((p), 0700)
  typedef struct stat syn_stat_t;
  #define SYN_STAT(p, st) stat((p), (st))
#endif

#define SYN_HASH_HEX 64
#define SYN_CACHE_VERSION "v1"
// Archivos escritos hace menos de esto no entran en la cache: su mtime puede
// cambiar despues de que el usuario lea el digest.
#define SYN_CACHE_EDAD_MINIMA_S 5

static int _hc_deshabilitada_por_entorno(void) {
    const char* v = getenv("SYNAPSE_HASH_CACHE");
    if (v == NULL || v[0] == '\0') return 0;
    if (strcmp(v, "0") == 0 || strcmp(v, "off") == 0 || strcmp(v, "false") == 0 ||
        strcmp(v, "no") == 0) {
        return 1;
    }
    return 0;
}

// Directorio base: $SYNAPSE_HASH_CACHE_DIR o <home>/.synapse/cache/hash.
// Devuelve 1 si dejo una ruta en `salida`.
static int _hc_directorio(char* salida, size_t tam) {
    const char* dir = getenv("SYNAPSE_HASH_CACHE_DIR");
    if (dir != NULL && dir[0] != '\0') {
        snprintf(salida, tam, "%s", dir);
        return 1;
    }
    const char* home = getenv("HOME");
#ifdef _WIN32
    if (home == NULL || home[0] == '\0') home = getenv("USERPROFILE");
#endif
    if (home == NULL || home[0] == '\0') return 0;
    snprintf(salida, tam, "%s/.synapse/cache/hash", home);
    return 1;
}

// Crea <dir> y sus dos padres inmediatos si faltan (best effort: si ya existen
// _mkdir devuelve error y se ignora).
static void _hc_asegurar_directorio(const char* dir) {
    char buf[1024];
    snprintf(buf, sizeof(buf), "%s", dir);
    for (char* p = buf + 1; *p != '\0'; p++) {
        if (*p == '/' || *p == '\\') {
            char sep = *p;
            *p = '\0';
            SYN_MKDIR(buf);
            *p = sep;
        }
    }
    SYN_MKDIR(buf);
}

// Nombre de entrada: FNV-1a de 64 bits de la ruta absoluta. La ruta completa se
// guarda dentro del archivo, asi que una colision solo pierde una entrada (la
// lectura compara la ruta y falla -> se rehashea); nunca devuelve un digest de
// otro archivo.
static void _hc_nombre_entrada(const char* dir, const char* ruta, char* salida, size_t tam) {
    uint64_t h = 1469598103934665603ULL;
    for (const unsigned char* p = (const unsigned char*)ruta; *p != '\0'; p++) {
        h ^= (uint64_t)(*p);
        h *= 1099511628211ULL;
    }
    snprintf(salida, tam, "%s/%016llx.entry", dir, (unsigned long long)h);
}

static int _hc_stat(const char* ruta, syn_stat_t* st) {
    return SYN_STAT(ruta, st) == 0 ? 1 : 0;
}

long long _syn_tamano_archivo_c(const char* ruta) {
    if (ruta == NULL) return -1;
    syn_stat_t st;
    if (!_hc_stat(ruta, &st)) return -1;
    return (long long)st.st_size;
}

int _syn_hash_cache_habilitado(void) {
    if (_hc_deshabilitada_por_entorno()) return 0;
    char dir[1024];
    return _hc_directorio(dir, sizeof(dir));
}

int _syn_hash_cache_obtener(const char* ruta, char* hash_salida, size_t tam_salida) {
    if (ruta == NULL || hash_salida == NULL || tam_salida < SYN_HASH_HEX + 1) return 0;
    if (!_syn_hash_cache_habilitado()) return 0;

    syn_stat_t st;
    if (!_hc_stat(ruta, &st)) return 0;
    if ((long long)st.st_mtime > (long long)time(NULL) - SYN_CACHE_EDAD_MINIMA_S) return 0;

    char dir[1024], entrada[1200];
    if (!_hc_directorio(dir, sizeof(dir))) return 0;
    _hc_nombre_entrada(dir, ruta, entrada, sizeof(entrada));

    FILE* f = fopen(entrada, "rb");
    if (!f) return 0;

    char version[16] = {0};
    long long tam_guardado = -1;
    long long mtime_guardado = -1;
    char hash[72] = {0};
    char ruta_guardada[1024] = {0};

    int ok = 0;
    if (fgets(version, sizeof(version), f) != NULL) {
        version[strcspn(version, "\r\n")] = '\0';
        char linea[1100];
        if (strcmp(version, SYN_CACHE_VERSION) == 0 &&
            fgets(linea, sizeof(linea), f) != NULL) {
            tam_guardado = atoll(linea);
            if (fgets(linea, sizeof(linea), f) != NULL) {
                mtime_guardado = atoll(linea);
                if (fgets(hash, sizeof(hash), f) != NULL &&
                    fgets(ruta_guardada, sizeof(ruta_guardada), f) != NULL) {
                    hash[strcspn(hash, "\r\n")] = '\0';
                    ruta_guardada[strcspn(ruta_guardada, "\r\n")] = '\0';
                    ok = 1;
                }
            }
        }
    }
    fclose(f);
    if (!ok) return 0;

    // La entrada vale solo para el mismo archivo con el mismo contenido
    // declarado (tamanio + mtime). Cualquier diferencia -> rehashear.
    if (strcmp(ruta_guardada, ruta) != 0) return 0;
    if (tam_guardado != (long long)st.st_size) return 0;
    if (mtime_guardado != (long long)st.st_mtime) return 0;
    if (strlen(hash) != SYN_HASH_HEX) return 0;

    memcpy(hash_salida, hash, SYN_HASH_HEX);
    hash_salida[SYN_HASH_HEX] = '\0';
    return 1;
}

void _syn_hash_cache_guardar(const char* ruta, const char* hash) {
    if (ruta == NULL || hash == NULL) return;
    if (strlen(hash) != SYN_HASH_HEX) return;               // digest vacio/parcial: no cachear
    if (!_syn_hash_cache_habilitado()) return;

    syn_stat_t st;
    if (!_hc_stat(ruta, &st)) return;
    if ((long long)st.st_mtime > (long long)time(NULL) - SYN_CACHE_EDAD_MINIMA_S) return;

    char dir[1024], entrada[1200], temporal[1300];
    if (!_hc_directorio(dir, sizeof(dir))) return;
    _hc_asegurar_directorio(dir);
    _hc_nombre_entrada(dir, ruta, entrada, sizeof(entrada));
#ifdef _WIN32
    snprintf(temporal, sizeof(temporal), "%s.tmp%lu", entrada, (unsigned long)clock());
#else
    snprintf(temporal, sizeof(temporal), "%s.tmp%ld", entrada, (long)getpid());
#endif

    // Escritura atomica: temporal + rename, para que un corte a mitad deje
    // intacta la entrada anterior en vez de una entrada truncada.
    FILE* f = fopen(temporal, "wb");
    if (!f) return;
    int escrito = fprintf(f, "%s\n%lld\n%lld\n%s\n%s\n",
                          SYN_CACHE_VERSION,
                          (long long)st.st_size,
                          (long long)st.st_mtime,
                          hash,
                          ruta) > 0;
    if (fclose(f) != 0 || !escrito) {
        remove(temporal);
        return;
    }
#ifdef _WIN32
    remove(entrada);  // Windows no reemplaza en rename()
#endif
    if (rename(temporal, entrada) != 0) {
        remove(temporal);
    }
}
