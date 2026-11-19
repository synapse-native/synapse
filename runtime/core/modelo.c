// runtime/core/modelo.c — std.ai module (GGUF Reader / BPE Tokenizer /
// ModeloContexto inference / Sampling / Oraculos).
// Extracted from synapse_rt.c (D-9(d) corte 3, patron tensor.c R35).
// Texto de las funciones BYTE-IDENTICO al original (CRLF preservado).
// Consumido por std.modelo / std.oraculo / std.ai (externs Synapse, link-time).

#include "synapse_rt_types.h"
#include "runtime/core/tensor.h"  // D-9(d) corte 2: std.math/std.tensor/std.simd
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include "runtime/core/modelo.h"  // ME-SEC-3: tipos públicos para testing
#include "runtime/core/axon.h"  // cumple Manual 7 2.5/9 §5.3: _syn_http_get_archivo, _syn_sha256_archivo
#include "runtime/core/hash_cache.h"  // cumple Manual 9 §5.3: cache de digests por ruta+tamano+mtime (r273)
#ifdef _WIN32
  #include <windows.h>
  #include <direct.h>
  #include <io.h>
  #include <fcntl.h>
#else
  #include <sys/mman.h>
  #include <sys/stat.h>
  #include <fcntl.h>
  #include <unistd.h>
#endif

// --- std.ai (GGUF Reader / Memory Mapping) ---
#define MEM_ALIGN 32
// HASH_TAM y MAX_METADATOS ahora en runtime/core/modelo.h

// GGML tensor types
#define GGML_TYPE_F32  0
#define GGML_TYPE_F16  1
#define GGML_TYPE_Q4_0 2
#define GGML_TYPE_Q4_1 3
#define GGML_TYPE_Q5_0 6
#define GGML_TYPE_Q5_1 7
#define GGML_TYPE_Q8_0 8

// TensorInfo, EntradaHash, ParMetadato, ArrayMetaEntry, InternalData
// are defined in runtime/core/modelo.h (ME-SEC-3: testable interface)

typedef struct GGUF_Contexto {
    int es_valido;
    int version;
    int cantidad_tensores;
    void* datos_mmap;
    int tamano_total;
    int tamano_mmap;
    void* handle_plataforma;
    void* handle_archivo;
    void* datos_internos;
} GGUF_Contexto;

static uint32_t fnv1a_hash(const char* str) {
    uint32_t h = 2166136261u;
    while (*str) {
        h ^= (unsigned char)*str++;
        h *= 16777619u;
    }
    return h;
}

static char* gguf_read_string(const unsigned char* base, int64_t size, uint64_t* pos) {
    if ((int64_t)(*pos + 8) > size) return NULL;
    uint64_t len = *(const uint64_t*)(base + *pos);
    *pos += 8;
    if ((int64_t)(*pos + len) > size) return NULL;
    char* s = (char*)malloc((size_t)(len + 1));
    if (!s) return NULL;
    memcpy(s, base + *pos, (size_t)len);
    s[len] = '\0';
    *pos += len;
    return s;
}

// Read a GGUF value and return its string representation (malloc'd).
// Returns NULL if unsupported; caller must free.
static char* gguf_value_as_string(const unsigned char* base, int64_t size, uint64_t* pos, uint32_t val_type) {
    char buf[128];
    switch (val_type) {
        case 0: case 1: { // UINT8, INT8
            if ((int64_t)(*pos + 1) > size) return NULL;
            int v = (int)base[*pos];
            *pos += 1;
            snprintf(buf, sizeof(buf), "%d", v);
            return strdup(buf);
        }
        case 2: case 3: { // UINT16, INT16
            if ((int64_t)(*pos + 2) > size) return NULL;
            int v = (int)(*(const uint16_t*)(base + *pos));
            *pos += 2;
            snprintf(buf, sizeof(buf), "%d", v);
            return strdup(buf);
        }
        case 4: case 5: { // UINT32, INT32
            if ((int64_t)(*pos + 4) > size) return NULL;
            int v = (int)(*(const uint32_t*)(base + *pos));
            *pos += 4;
            snprintf(buf, sizeof(buf), "%d", v);
            return strdup(buf);
        }
        case 6: { // FLOAT32
            if ((int64_t)(*pos + 4) > size) return NULL;
            float v = *(const float*)(base + *pos);
            *pos += 4;
            snprintf(buf, sizeof(buf), "%g", v);
            return strdup(buf);
        }
        case 7: { // BOOL
            if ((int64_t)(*pos + 1) > size) return NULL;
            int v = base[*pos] ? 1 : 0;
            *pos += 1;
            return strdup(v ? "true" : "false");
        }
        case 8: { // STRING
            return gguf_read_string(base, size, pos);
        }
        case 10: case 11: { // UINT64, INT64
            if ((int64_t)(*pos + 8) > size) return NULL;
            long long v = (long long)(*(const uint64_t*)(base + *pos));
            *pos += 8;
            snprintf(buf, sizeof(buf), "%lld", v);
            return strdup(buf);
        }
        case 12: { // FLOAT64
            if ((int64_t)(*pos + 8) > size) return NULL;
            double v = *(const double*)(base + *pos);
            *pos += 8;
            snprintf(buf, sizeof(buf), "%g", v);
            return strdup(buf);
        }
        default:
            // ARRAY (9) and unknown types: return NULL (caller handles skip)
            return NULL;
    }
}

#ifdef _WIN32
static void* _syn_mmap_archivo(const char* ruta, int64_t* out_tamano,
                                void** out_handle_plat, void** out_handle_arch) {
    HANDLE hFile = CreateFileA(ruta, GENERIC_READ, FILE_SHARE_READ, NULL,
                                OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (hFile == INVALID_HANDLE_VALUE) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: CreateFileA fallo\n");
        return NULL;
    }
    LARGE_INTEGER li;
    GetFileSizeEx(hFile, &li);
    *out_tamano = li.QuadPart;

    HANDLE hMapping = CreateFileMappingA(hFile, NULL, PAGE_READONLY, 0, 0, NULL);
    if (!hMapping) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: CreateFileMappingA fallo\n");
        CloseHandle(hFile);
        return NULL;
    }
    void* ptr = MapViewOfFile(hMapping, FILE_MAP_READ, 0, 0, 0);
    if (!ptr) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: MapViewOfFile fallo\n");
        CloseHandle(hMapping);
        CloseHandle(hFile);
        return NULL;
    }
    *out_handle_plat = hMapping;
    *out_handle_arch = hFile;
    return ptr;
}

static void _syn_munmap_archivo(void* ptr, int64_t tamano,
                                 void* handle_plat, void* handle_arch) {
    (void)tamano;
    if (ptr) UnmapViewOfFile(ptr);
    if (handle_plat) CloseHandle(handle_plat);
    if (handle_arch) CloseHandle(handle_arch);
}
#else
static void* _syn_mmap_archivo(const char* ruta, int64_t* out_tamano,
                                void** out_handle_plat, void** out_handle_arch) {
    int fd = open(ruta, O_RDONLY);
    if (fd < 0) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: open fallo\n");
        return NULL;
    }
    struct stat st;
    if (fstat(fd, &st) < 0) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: fstat fallo\n");
        close(fd);
        return NULL;
    }
    *out_tamano = (int64_t)st.st_size;

    void* ptr = mmap(NULL, (size_t)st.st_size, PROT_READ, MAP_PRIVATE, fd, 0);
    close(fd);
    if (ptr == MAP_FAILED) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: mmap fallo\n");
        *out_tamano = 0;
        return NULL;
    }
    *out_handle_plat = NULL;
    *out_handle_arch = NULL;
    return ptr;
}

static void _syn_munmap_archivo(void* ptr, int64_t tamano,
                                 void* handle_plat, void* handle_arch) {
    (void)handle_plat;
    (void)handle_arch;
    if (ptr && tamano > 0) munmap(ptr, (size_t)tamano);
}
#endif

GGUF_Contexto _syn_gguf_abrir(CadenaSegura ruta) {
    GGUF_Contexto ctx;
    memset(&ctx, 0, sizeof(ctx));

    if (ruta.datos == NULL || ruta.longitud <= 0) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: Ruta de archivo invalida\n");
        return ctx;
    }

    char* fname = (char*)malloc((size_t)(ruta.longitud + 1));
    if (!fname) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: Error de memoria al abrir archivo\n");
        return ctx;
    }
    memcpy(fname, ruta.datos, (size_t)ruta.longitud);
    fname[ruta.longitud] = '\0';

    int64_t tamano_mmap = 0;
    void* h_plat = NULL;
    void* h_arch = NULL;
    void* mmap_ptr = _syn_mmap_archivo(fname, &tamano_mmap, &h_plat, &h_arch);
    free(fname);

    if (!mmap_ptr) {
        return ctx;
    }

    if (tamano_mmap < 24) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: Archivo demasiado pequeno\n");
        _syn_munmap_archivo(mmap_ptr, tamano_mmap, h_plat, h_arch);
        return ctx;
    }

    const unsigned char* base = (const unsigned char*)mmap_ptr;
    uint64_t pos = 0;

    // Magic: "GGUF"
    if (base[0] != 'G' || base[1] != 'G' || base[2] != 'U' || base[3] != 'F') {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: Magic GGUF invalido\n");
        _syn_munmap_archivo(mmap_ptr, tamano_mmap, h_plat, h_arch);
        return ctx;
    }
    pos += 4;

    // Version (uint32_t LE)
    uint32_t version_le = *(const uint32_t*)(base + pos);
    pos += 4;

    // Tensor count (uint64_t LE)
    uint64_t tensor_count = *(const uint64_t*)(base + pos);
    pos += 8;

    // Metadata KV count (uint64_t LE)
    uint64_t kv_count = *(const uint64_t*)(base + pos);
    pos += 8;

    // Allocate internal data
    InternalData* idata = (InternalData*)malloc(sizeof(InternalData));
    memset(idata, 0, sizeof(InternalData));
    idata->mmap_ptr = mmap_ptr;
    idata->tamano_mmap = tamano_mmap;
    idata->cantidad_tensores = (int)tensor_count;
    idata->tensores = (TensorInfo*)calloc((size_t)(tensor_count > 0 ? tensor_count : 1), sizeof(TensorInfo));

    // Parse & store metadata KV pairs
    int meta_idx = 0;
    for (uint64_t i = 0; i < kv_count && meta_idx < MAX_METADATOS; i++) {
        if ((int64_t)(pos + 8) > tamano_mmap) goto error;
        uint64_t key_len = *(const uint64_t*)(base + pos);
        pos += 8;
        if ((int64_t)(pos + key_len) > tamano_mmap) goto error;
        // Read key as C string
        char* clave = (char*)malloc((size_t)(key_len + 1));
        memcpy(clave, base + pos, (size_t)key_len);
        clave[key_len] = '\0';
        pos += key_len;
        if ((int64_t)(pos + 4) > tamano_mmap) goto error;
        uint32_t val_type = *(const uint32_t*)(base + pos);
        pos += 4;
        // Read value as string
        uint64_t save_pos = pos;
        char* valor = gguf_value_as_string(base, tamano_mmap, &pos, val_type);
        // If we couldn't convert, restore pos and skip
        if (!valor) {
            pos = save_pos;
            switch (val_type) {
                case 9: { // ARRAY
                    if ((int64_t)(pos + 4) > tamano_mmap) { free(clave); goto error; }
                    uint32_t elem_type = *(const uint32_t*)(base + pos);
                    pos += 4;
                    if ((int64_t)(pos + 8) > tamano_mmap) { free(clave); goto error; }
                    uint64_t arr_len = *(const uint64_t*)(base + pos);
                    pos += 8;
                    // Store array metadata for later access (tokens, scores, merges)
                    if (idata->cantidad_arrays < MAX_ARRAY_METADATOS) {
                        idata->arrays[idata->cantidad_arrays].clave = strdup(clave);
                        idata->arrays[idata->cantidad_arrays].tipo_elemento = (int)elem_type;
                        idata->arrays[idata->cantidad_arrays].cantidad = (int)arr_len;
                        idata->arrays[idata->cantidad_arrays].data_pos = pos;
                        idata->arrays[idata->cantidad_arrays].cache_indice = -1;
                        idata->arrays[idata->cantidad_arrays].cache_pos = pos;
                        idata->cantidad_arrays++;
                    }
                    for (uint64_t j = 0; j < arr_len; j++) {
                        if ((int64_t)(pos + 1) > tamano_mmap) { free(clave); goto error; }
                        uint64_t e_size = 0;
                        switch (elem_type) {
                            case 0: case 1: case 7: e_size = 1; break;
                            case 2: case 3: e_size = 2; break;
                            case 4: case 5: case 6: e_size = 4; break;
                            case 10: case 11: case 12: e_size = 8; break;
                            case 8:
                                if ((int64_t)(pos + 8) > tamano_mmap) { free(clave); goto error; }
                                e_size = 8 + *(const uint64_t*)(base + pos);
                                break;
                            default: { free(clave); goto error; }
                        }
                        if ((int64_t)(pos + e_size) > tamano_mmap) { free(clave); goto error; }
                        pos += e_size;
                    }
                    valor = strdup("<ARRAY>");
                    break;
                }
                default:
                    free(clave);
                    goto error;
            }
        }
        // Store metadata
        idata->metadatos[meta_idx].clave = clave;
        idata->metadatos[meta_idx].valor = valor;
        // Check if this is the architecture key
        if (clave && strcmp(clave, "general.architecture") == 0 && valor) {
            free(idata->architecture);
            idata->architecture = strdup(valor);
        }
        meta_idx++;
    }
    idata->cantidad_metadatos = meta_idx;

    // Read tensor infos
    for (uint64_t i = 0; i < tensor_count; i++) {
        TensorInfo* ti = &idata->tensores[i];

        if ((int64_t)(pos + 8) > tamano_mmap) goto error;
        uint64_t name_len = *(const uint64_t*)(base + pos);
        pos += 8;

        if ((int64_t)(pos + name_len) > tamano_mmap) goto error;
        ti->nombre = (char*)malloc((size_t)(name_len + 1));
        memcpy(ti->nombre, base + pos, (size_t)name_len);
        ti->nombre[name_len] = '\0';
        pos += name_len;

        if ((int64_t)(pos + 4) > tamano_mmap) goto error;
        ti->n_dimensiones = (int)(*(const uint32_t*)(base + pos));
        pos += 4;

        int ndims = ti->n_dimensiones < 4 ? ti->n_dimensiones : 4;
        for (int d = 0; d < ndims; d++) {
            if ((int64_t)(pos + 8) > tamano_mmap) goto error;
            ti->dimensiones[d] = *(const uint64_t*)(base + pos);
            pos += 8;
        }
        for (int d = ndims; d < ti->n_dimensiones; d++) {
            if ((int64_t)(pos + 8) > tamano_mmap) goto error;
            pos += 8;
        }

        if ((int64_t)(pos + 4) > tamano_mmap) goto error;
        ti->tipo = (int)(*(const uint32_t*)(base + pos));
        pos += 4;

        if ((int64_t)(pos + 8) > tamano_mmap) goto error;
        ti->offset = *(const uint64_t*)(base + pos);
        pos += 8;
    }

    // Build hash table from tensor names
    for (int i = 0; i < (int)tensor_count; i++) {
        uint32_t h = fnv1a_hash(idata->tensores[i].nombre) & (HASH_TAM - 1);
        EntradaHash* entry = (EntradaHash*)malloc(sizeof(EntradaHash));
        if (!entry) goto error;
        entry->indice_tensor = (uint32_t)i;
        entry->siguiente = idata->tabla_hash[h];
        idata->tabla_hash[h] = entry;
    }

    // Calculate aligned tensor data base offset
    uint64_t data_base = (pos + MEM_ALIGN - 1) & ~(uint64_t)(MEM_ALIGN - 1);
    idata->tensor_data_base_offset = data_base;

    // Fill context
    ctx.es_valido = 1;
    ctx.version = (int)version_le;
    ctx.cantidad_tensores = (int)tensor_count;
    ctx.datos_mmap = mmap_ptr;
    ctx.tamano_total = (int)tamano_mmap;
    ctx.tamano_mmap = (int)tamano_mmap;
    ctx.handle_plataforma = h_plat;
    ctx.handle_archivo = h_arch;
    ctx.datos_internos = idata;

    return ctx;

error:
    fprintf(stderr, "ESCAPA_DEL_ALCANCE: Error de parseo GGUF\n");
    if (idata) {
        if (idata->tensores) {
            for (int i = 0; i < idata->cantidad_tensores; i++) {
                free(idata->tensores[i].nombre);
                free(idata->tensores[i].cache_f32);  // ME_opensyn_ia: cache des-cuantizada
            }
            free(idata->tensores);
        }
        for (int i = 0; i < HASH_TAM; i++) {
            EntradaHash* e = idata->tabla_hash[i];
            while (e) {
                EntradaHash* next = e->siguiente;
                free(e);
                e = next;
            }
        }
        for (int i = 0; i < idata->cantidad_metadatos; i++) {
            free(idata->metadatos[i].clave);
            free(idata->metadatos[i].valor);
        }
        free(idata->architecture);
        free(idata);
    }
    _syn_munmap_archivo(mmap_ptr, tamano_mmap, h_plat, h_arch);
    return ctx;
}

void _syn_gguf_cerrar(void* datos_mmap, int tamano_mmap,
                       void* handle_plataforma, void* handle_archivo) {
    _syn_munmap_archivo(datos_mmap, (int64_t)tamano_mmap,
                         handle_plataforma, handle_archivo);
}

void _syn_gguf_cerrar_contex(GGUF_Contexto ctx) {
    if (ctx.datos_internos) {
        InternalData* idata = (InternalData*)ctx.datos_internos;
        if (idata->tensores) {
            for (int i = 0; i < idata->cantidad_tensores; i++) {
                free(idata->tensores[i].nombre);
                free(idata->tensores[i].cache_f32);  // ME_opensyn_ia: cache des-cuantizada
            }
            free(idata->tensores);
        }
        for (int i = 0; i < HASH_TAM; i++) {
            EntradaHash* e = idata->tabla_hash[i];
            while (e) {
                EntradaHash* next = e->siguiente;
                free(e);
                e = next;
            }
        }
        for (int i = 0; i < idata->cantidad_metadatos; i++) {
            free(idata->metadatos[i].clave);
            free(idata->metadatos[i].valor);
        }
        for (int i = 0; i < idata->cantidad_arrays; i++) {
            free(idata->arrays[i].clave);
        }
        free(idata->architecture);
        free(idata);
    }
    _syn_munmap_archivo(ctx.datos_mmap, (int64_t)ctx.tamano_mmap,
                         ctx.handle_plataforma, ctx.handle_archivo);
}

static ArrayMetaEntry* _gguf_buscar_arreglo(void* datos_internos, const char* clave) {
    if (!datos_internos || !clave) return NULL;
    InternalData* idata = (InternalData*)datos_internos;
    for (int i = 0; i < idata->cantidad_arrays; i++) {
        if (strcmp(idata->arrays[i].clave, clave) == 0) {
            return &idata->arrays[i];
        }
    }
    return NULL;
}

// --- ME_opensyn_ia: acceso secuencial O(n) a los arrays del GGUF ---
// Los arrays de metadatos (vocab, merges) tienen miles de elementos; cada
// acceso re-caminaba desde data_pos -> O(n^2). cache_indice/cache_pos
// recuerdan la posicion del ultimo elemento leido (avance O(1) amortizado).

static int _gguf_arr_tamano_elemento(int tipo_elemento) {
    switch (tipo_elemento) {
        case 0: case 1: case 7: return 1;
        case 2: case 3: return 2;
        case 4: case 5: case 6: return 4;
        case 10: case 11: case 12: return 8;
        case 8: return -1; // string: tamano variable
        default: return -2;
    }
}

// Salta n elementos desde *pos. Devuelve 0 OK, -1 fuera de rango.
static int _gguf_arr_saltar(const InternalData* idata, const ArrayMetaEntry* arr, uint64_t* pos, int n) {
    const unsigned char* base = (const unsigned char*)idata->mmap_ptr;
    for (int k = 0; k < n; k++) {
        if ((int64_t)(*pos + 8) > idata->tamano_mmap) return -1;
        if (arr->tipo_elemento == 8) {
            uint64_t l = *(const uint64_t*)(base + *pos);
            if ((int64_t)(*pos + 8 + l) > idata->tamano_mmap) return -1;
            *pos += 8 + l;
        } else {
            int sz = _gguf_arr_tamano_elemento(arr->tipo_elemento);
            if (sz <= 0) return -1;
            *pos += (uint64_t)sz;
        }
    }
    return 0;
}

// Devuelve la posicion del inicio del elemento `indice`, o (uint64_t)-1 si error.
static uint64_t _gguf_arr_posicion(InternalData* idata, ArrayMetaEntry* arr, int indice) {
    uint64_t pos;
    if (arr->cache_indice >= 0 && indice >= arr->cache_indice) {
        pos = arr->cache_pos;
        if (_gguf_arr_saltar(idata, arr, &pos, indice - arr->cache_indice) != 0) return (uint64_t)-1;
    } else {
        pos = arr->data_pos;
        if (_gguf_arr_saltar(idata, arr, &pos, indice) != 0) return (uint64_t)-1;
    }
    arr->cache_indice = indice;
    arr->cache_pos = pos;
    return pos;
}

static int _gguf_leer_elemento_string(const unsigned char* base, int64_t size, uint64_t* pos, char** out, int max_len) {
    if ((int64_t)(*pos + 8) > size) return -1;
    uint64_t slen = *(const uint64_t*)(base + *pos);
    *pos += 8;
    if ((int64_t)(*pos + slen) > size) return -1;
    int len = (int)slen;
    if (max_len > 0 && len > max_len) len = max_len;
    *out = (char*)malloc((size_t)(len + 1));
    if (!*out) return -1;
    memcpy(*out, base + *pos, (size_t)len);
    (*out)[len] = '\0';
    *pos += slen;
    return len;
}

// --- GGUF Array accessor functions (used by model loader) ---

int _syn_gguf_arreglo_cantidad(void* datos_internos, const char* clave) {
    ArrayMetaEntry* arr = _gguf_buscar_arreglo(datos_internos, clave);
    return arr ? arr->cantidad : -1;
}

int _syn_gguf_arreglo_tipo(void* datos_internos, const char* clave) {
    ArrayMetaEntry* arr = _gguf_buscar_arreglo(datos_internos, clave);
    return arr ? arr->tipo_elemento : -1;
}

CadenaSegura _syn_gguf_arreglo_string(void* datos_internos, const char* clave, int indice) {
    CadenaSegura result = {0, NULL};
    ArrayMetaEntry* arr = _gguf_buscar_arreglo(datos_internos, clave);
    if (!arr || arr->tipo_elemento != 8 || indice < 0 || indice >= arr->cantidad) return result;
    InternalData* idata = (InternalData*)datos_internos;
    const unsigned char* base = (const unsigned char*)idata->mmap_ptr;
    uint64_t pos = _gguf_arr_posicion(idata, arr, indice);
    if (pos == (uint64_t)-1) return result;
    char* out = NULL;
    int len = _gguf_leer_elemento_string(base, idata->tamano_mmap, &pos, &out, 0);
    if (len < 0) return result;
    result.longitud = len;
    result.datos = out;
    return result;
}

float _syn_gguf_arreglo_float(void* datos_internos, const char* clave, int indice) {
    ArrayMetaEntry* arr = _gguf_buscar_arreglo(datos_internos, clave);
    if (!arr || indice < 0 || indice >= arr->cantidad) return 0.0f;
    if (arr->tipo_elemento != 6) return 0.0f; // FLOAT32
    InternalData* idata = (InternalData*)datos_internos;
    const unsigned char* base = (const unsigned char*)idata->mmap_ptr;
    uint64_t pos = _gguf_arr_posicion(idata, arr, indice);
    if (pos == (uint64_t)-1) return 0.0f;
    if ((int64_t)(pos + 4) > idata->tamano_mmap) return 0.0f;
    return *(const float*)(base + pos);
}

int _syn_gguf_arreglo_int(void* datos_internos, const char* clave, int indice) {
    ArrayMetaEntry* arr = _gguf_buscar_arreglo(datos_internos, clave);
    if (!arr || indice < 0 || indice >= arr->cantidad) return 0;
    InternalData* idata = (InternalData*)datos_internos;
    const unsigned char* base = (const unsigned char*)idata->mmap_ptr;
    uint64_t pos = _gguf_arr_posicion(idata, arr, indice);
    if (pos == (uint64_t)-1) return 0;
    int elem_size = _gguf_arr_tamano_elemento(arr->tipo_elemento);
    if (elem_size <= 0) return 0;
    if ((int64_t)(pos + elem_size) > idata->tamano_mmap) return 0;
    switch (arr->tipo_elemento) {
        case 0: case 7: return (int)base[pos];
        case 1: return (int)(*(const int8_t*)(base + pos));
        case 2: return (int)(*(const uint16_t*)(base + pos));
        case 3: return (int)(*(const int16_t*)(base + pos));
        case 4: return (int)(*(const uint32_t*)(base + pos));
        case 5: return (int)(*(const int32_t*)(base + pos));
        case 6: return 0; // floats not representable as int
        case 10: return (int)(*(const uint64_t*)(base + pos));
        case 11: return (int)(*(const int64_t*)(base + pos));
        case 12: return (int)(*(const float*)(base + pos)); // float16 treated as 32 in GGUF
        default: return 0;
    }
}

// --- ME_opensyn_ia (opcion A): des-cuantizacion GGUF estandar a F32 ---
// El motor infiere sobre float* (F32). Los GGUFs reales vienen cuantizados en
// bloques de 32 (ggml): estos conversores exactos materializan el tensor a F32
// la primera vez que se solicita y se cachean en TensorInfo.cache_f32.
// Formatos soportados: F16, Q4_0, Q4_1, Q5_0, Q5_1, Q8_0 (bloque 32, exactos).
// cumple Manual 7 §3.3: cuantización para reducir tamaño y acelerar inferencia.
// cumple Manual 7 §8: verificación de límites contra tamano_mmap.

static float _fp16_a_f32(uint16_t h) {
    uint32_t sign = ((uint32_t)h & 0x8000u) << 16;
    uint32_t expo = ((uint32_t)h & 0x7C00u) >> 10;
    uint32_t mant = (uint32_t)h & 0x03FFu;
    uint32_t f32;
    if (expo == 0) {
        if (mant == 0) { f32 = sign; }
        else {
            expo = 127 - 15 + 1;
            while ((mant & 0x0400u) == 0) { mant <<= 1; expo--; }
            mant &= 0x03FFu;
            f32 = sign | (expo << 23) | (mant << 13);
        }
    } else if (expo == 0x1F) {
        f32 = sign | 0x7F800000u | (mant << 13);
    } else {
        f32 = sign | ((expo - 15 + 127) << 23) | (mant << 13);
    }
    float out;
    memcpy(&out, &f32, sizeof(out));
    return out;
}

static int64_t _gguf_nelem(const TensorInfo* ti) {
    int64_t n = 1;
    for (int d = 0; d < ti->n_dimensiones && d < 4; d++) n *= (int64_t)ti->dimensiones[d];
    return n;
}

static const unsigned char* _gguf_src_tensor(const InternalData* idata, const TensorInfo* ti) {
    return (const unsigned char*)idata->mmap_ptr + idata->tensor_data_base_offset + ti->offset;
}

static int _gguf_fuera_de_rango(const InternalData* idata, const TensorInfo* ti, uint64_t bytes) {
    uint64_t fin = idata->tensor_data_base_offset + ti->offset + bytes;
    return fin > (uint64_t)idata->tamano_mmap;
}

// Devuelve un buffer F32 (malloc) con el tensor des-cuantizado, o NULL.
static float* _gguf_decuantizar_f32(const InternalData* idata, const TensorInfo* ti) {
    int64_t nelem = _gguf_nelem(ti);
    if (nelem <= 0 || nelem > (int64_t)INT32_MAX) return NULL;
    const unsigned char* src = _gguf_src_tensor(idata, ti);
    float* out = (float*)malloc((size_t)nelem * sizeof(float));
    if (!out) return NULL;
    if (nelem % 32 != 0 && ti->tipo != GGML_TYPE_F16) { free(out); return NULL; }
    int nb = (int)(nelem / 32);
    switch (ti->tipo) {
        case GGML_TYPE_F16: {
            if (_gguf_fuera_de_rango(idata, ti, (uint64_t)nelem * 2)) { free(out); return NULL; }
            for (int64_t i = 0; i < nelem; i++) out[i] = _fp16_a_f32(((const uint16_t*)src)[i]);
            return out;
        }
        case GGML_TYPE_Q8_0: {  // bloque 32: [fp16 d][32 x int8] = 34 B
            if (_gguf_fuera_de_rango(idata, ti, (uint64_t)nb * 34)) { free(out); return NULL; }
            for (int b = 0; b < nb; b++) {
                const unsigned char* q = src + (size_t)b * 34;
                float d = _fp16_a_f32(*(const uint16_t*)q);
                const int8_t* vals = (const int8_t*)(q + 2);
                float* o = out + (size_t)b * 32;
                for (int i = 0; i < 32; i++) o[i] = (float)vals[i] * d;
            }
            return out;
        }
        case GGML_TYPE_Q4_0: {  // bloque 32: [fp16 d][16 x nibble(int4) c/ sesgo -8] = 18 B
            if (_gguf_fuera_de_rango(idata, ti, (uint64_t)nb * 18)) { free(out); return NULL; }
            for (int b = 0; b < nb; b++) {
                const unsigned char* q = src + (size_t)b * 18;
                float d = _fp16_a_f32(*(const uint16_t*)q);
                const unsigned char* qs = q + 2;
                float* o = out + (size_t)b * 32;
                for (int i = 0; i < 16; i++) {
                    int lo = qs[i] & 0x0F, hi = (qs[i] >> 4) & 0x0F;
                    o[2 * i]     = (float)((lo >= 8) ? lo - 16 : lo) * d;
                    o[2 * i + 1] = (float)((hi >= 8) ? hi - 16 : hi) * d;
                }
            }
            return out;
        }
        case GGML_TYPE_Q4_1: {  // bloque 32: [fp16 d][fp16 m][16 x nibble(int4) unsigned] = 20 B
            if (_gguf_fuera_de_rango(idata, ti, (uint64_t)nb * 20)) { free(out); return NULL; }
            for (int b = 0; b < nb; b++) {
                const unsigned char* q = src + (size_t)b * 20;
                float d = _fp16_a_f32(*(const uint16_t*)q);
                float m = _fp16_a_f32(*(const uint16_t*)(q + 2));
                const unsigned char* qs = q + 4;
                float* o = out + (size_t)b * 32;
                for (int i = 0; i < 16; i++) {
                    int lo = qs[i] & 0x0F, hi = (qs[i] >> 4) & 0x0F;
                    o[2 * i]     = m + (float)lo * d;
                    o[2 * i + 1] = m + (float)hi * d;
                }
            }
            return out;
        }
        case GGML_TYPE_Q5_0: {  // bloque 32: [fp16 d][4 x qh(bit e <- elem e)][16 x nibble] = 22 B
            if (_gguf_fuera_de_rango(idata, ti, (uint64_t)nb * 22)) { free(out); return NULL; }
            for (int b = 0; b < nb; b++) {
                const unsigned char* q = src + (size_t)b * 22;
                float d = _fp16_a_f32(*(const uint16_t*)q);
                const unsigned char* qh = q + 2;
                const unsigned char* qs = q + 6;
                float* o = out + (size_t)b * 32;
                for (int e = 0; e < 32; e++) {
                    int low = (qs[e / 2] >> (4 * (e & 1))) & 0x0F;
                    int high = (qh[e / 8] >> (e & 7)) & 1;
                    o[e] = (float)((low | (high << 4)) - 16) * d;
                }
            }
            return out;
        }
        case GGML_TYPE_Q5_1: {  // bloque 32: [fp16 d][fp16 m][4 x qh][16 x nibble] = 24 B
            if (_gguf_fuera_de_rango(idata, ti, (uint64_t)nb * 24)) { free(out); return NULL; }
            for (int b = 0; b < nb; b++) {
                const unsigned char* q = src + (size_t)b * 24;
                float d = _fp16_a_f32(*(const uint16_t*)q);
                float m = _fp16_a_f32(*(const uint16_t*)(q + 2));
                const unsigned char* qh = q + 4;
                const unsigned char* qs = q + 8;
                float* o = out + (size_t)b * 32;
                for (int e = 0; e < 32; e++) {
                    int low = (qs[e / 2] >> (4 * (e & 1))) & 0x0F;
                    int high = (qh[e / 8] >> (e & 7)) & 1;
                    o[e] = m + (float)(low | (high << 4)) * d;
                }
            }
            return out;
        }
        default:
            free(out);
            return NULL;
    }
}

Tensor _syn_gguf_obtener_tensor(void* datos_internos, CadenaSegura nombre) {
    Tensor t;
    memset(&t, 0, sizeof(t));

    if (!datos_internos || nombre.datos == NULL || nombre.longitud <= 0) {
        return t;
    }

    InternalData* idata = (InternalData*)datos_internos;

    char* name_str = (char*)malloc((size_t)(nombre.longitud + 1));
    memcpy(name_str, nombre.datos, (size_t)nombre.longitud);
    name_str[nombre.longitud] = '\0';

    // O(1) hash table lookup
    uint32_t h = fnv1a_hash(name_str) & (HASH_TAM - 1);
    EntradaHash* entry = idata->tabla_hash[h];
    while (entry) {
        TensorInfo* ti = &idata->tensores[entry->indice_tensor];
        if (strcmp(name_str, ti->nombre) == 0) {
            free(name_str);
            // ME_opensyn_ia: orden de dimensiones GGUF/llama.cpp. El archivo
            // guarda ne[] con ne[0] = dimension contigua (columnas) y la
            // externa al final (filas). Antes se leian invertidas: w_k daba
            // columnas=128 (kv_heads*head_dim) en vez de 896 -> matmul OOB.
            if (ti->n_dimensiones >= 2) {
                t.filas = (int)ti->dimensiones[ti->n_dimensiones - 1];
                t.columnas = (int)ti->dimensiones[0];
            } else if (ti->n_dimensiones == 1) {
                t.filas = 1;
                t.columnas = (int)ti->dimensiones[0];
            }
            if (ti->tipo != GGML_TYPE_F32) {
                // ME_opensyn_ia (opcion A): des-cuantizacion perezosa con cache.
                // La primera lectura materializa el tensor a F32 (heap) y lo
                // reutiliza; se libera al cerrar el contexto. es_mapeado=1
                // mantiene el contrato de los tensores mmap (el motor nunca los
                // libera; las ops con ownership solo liberan si es_mapeado==0).
                if (!ti->cache_f32) {
                    ti->cache_f32 = _gguf_decuantizar_f32(idata, ti);
                    if (!ti->cache_f32) {
                        fprintf(stderr, "ESCAPA_DEL_ALCANCE: Tipo de tensor no soportado "
                                "(tipo=%d)\n", ti->tipo);
                        return t;
                    }
                }
                t.datos = ti->cache_f32;
                t.es_mapeado = 1;
                return t;
            }
            t.datos = (float*)((unsigned char*)idata->mmap_ptr + idata->tensor_data_base_offset + ti->offset);
            t.es_mapeado = 1;
            return t;
        }
        entry = entry->siguiente;
    }

    free(name_str);
    return t;
}

// Devuelve el valor del metadato como texto, o texto vacio si no existe.
// El puntero apunta a memoria interna (no liberar).
CadenaSegura _syn_gguf_obtener_metadato(void* datos_internos, CadenaSegura clave) {
    if (!datos_internos || clave.datos == NULL || clave.longitud <= 0) {
        return (CadenaSegura){0, ""};
    }
    InternalData* idata = (InternalData*)datos_internos;
    char* key_str = (char*)malloc((size_t)(clave.longitud + 1));
    if (!key_str) return (CadenaSegura){0, ""};
    memcpy(key_str, clave.datos, (size_t)clave.longitud);
    key_str[clave.longitud] = '\0';
    CadenaSegura result = (CadenaSegura){0, ""};
    for (int i = 0; i < idata->cantidad_metadatos; i++) {
        if (strcmp(idata->metadatos[i].clave, key_str) == 0 && idata->metadatos[i].valor) {
            result = (CadenaSegura){.longitud = (int)strlen(idata->metadatos[i].valor), .datos = strdup(idata->metadatos[i].valor)};
            break;
        }
    }
    free(key_str);
    return result;
}

CadenaSegura _syn_gguf_obtener_arquitectura(void* datos_internos) {
    if (!datos_internos) return (CadenaSegura){0, ""};
    InternalData* idata = (InternalData*)datos_internos;
    if (idata->architecture) {
        return (CadenaSegura){.longitud = (int)strlen(idata->architecture), .datos = strdup(idata->architecture)};
    }
    return (CadenaSegura){0, ""};
}

int _syn_leer_byte_desde(void* base, int desplazamiento) {
    return (int)((unsigned char*)base)[desplazamiento];
}

float _syn_sumar_elementos(Tensor t) {
    float suma = 0.0f;
    for (int i = 0; i < (int)(t.filas * t.columnas); i++) {
        suma += t.datos[i];
    }
    return suma;
}

void _syn_fijar_elemento(Tensor t, int indice, float valor) {
    if (t.datos && indice >= 0 && indice < (int)(t.filas * t.columnas)) {
        t.datos[indice] = valor;
    }
}

int _syn_argmax(Tensor t) {
    if (t.datos == NULL || (t.filas * t.columnas) <= 0) return -1;
    int mejor = 0;
    float max_val = t.datos[0];
    int total = t.filas * t.columnas;
    for (int i = 1; i < total; i++) {
        if (t.datos[i] > max_val) {
            max_val = t.datos[i];
            mejor = i;
        }
    }
    return mejor;
}

int _syn_vocab_tamano(void* datos_internos) {
    if (!datos_internos) return 0;
    InternalData* idata = (InternalData*)datos_internos;
    for (int i = 0; i < idata->cantidad_metadatos; i++) {
        if (strcmp(idata->metadatos[i].clave, "vocab_size") == 0 && idata->metadatos[i].valor) {
            char* end = NULL;
            long v = strtol(idata->metadatos[i].valor, &end, 10);
            return (end && *end == '\0') ? (int)v : 0;
            // cumple Manual 7 3: metadatos GGUF parseados con strtol+endptr
        }
    }
    return 0;
}

CadenaSegura _syn_decodificar_token(void* datos_internos, int token_id) {
    if (!datos_internos || token_id < 0) return (CadenaSegura){0, ""};
    InternalData* idata = (InternalData*)datos_internos;
    char clave[64];
    snprintf(clave, sizeof(clave), "vocab.%d", token_id);
    for (int i = 0; i < idata->cantidad_metadatos; i++) {
        if (strcmp(idata->metadatos[i].clave, clave) == 0 && idata->metadatos[i].valor) {
            return (CadenaSegura){.longitud = (int)strlen(idata->metadatos[i].valor), .datos = strdup(idata->metadatos[i].valor)};
        }
    }
    return (CadenaSegura){0, ""};
}

int _syn_ejecutar_comando(CadenaSegura cmd) {
    if (cmd.datos == NULL || cmd.longitud <= 0) return -1;
    char* cstr = (char*)malloc((size_t)(cmd.longitud + 1));
    if (!cstr) return -1;
    memcpy(cstr, cmd.datos, (size_t)cmd.longitud);
    cstr[cmd.longitud] = '\0';
    int r = system(cstr);
    free(cstr);
    return r;
}

// (I/O de archivos movido a runtime/core/io.c en F3-1: _syn_leer_archivo,
// _syn_escribir_archivo, _syn_leer_archivo_como_texto)

CadenaSegura _syn_obtener_env(CadenaSegura nombre) {
    if (nombre.datos == NULL || nombre.longitud <= 0) return (CadenaSegura){0, ""};
    char* cstr = (char*)malloc((size_t)(nombre.longitud + 1));
    if (!cstr) return (CadenaSegura){0, ""};
    memcpy(cstr, nombre.datos, (size_t)nombre.longitud);
    cstr[nombre.longitud] = '\0';
    char* val = getenv(cstr);
    free(cstr);
    if (!val) return (CadenaSegura){0, ""};
    return (CadenaSegura){.longitud = (int)strlen(val), .datos = strdup(val)};
}

int _syn_existe_archivo(CadenaSegura ruta) {
    if (ruta.datos == NULL || ruta.longitud <= 0) return 0;
    char* cstr = (char*)malloc((size_t)(ruta.longitud + 1));
    if (!cstr) return 0;
    memcpy(cstr, ruta.datos, (size_t)ruta.longitud);
    cstr[ruta.longitud] = '\0';
    FILE* f = fopen(cstr, "rb");
    free(cstr);
    if (f) { fclose(f); return 1; }
    return 0;
}

int _syn_eliminar_archivo(CadenaSegura ruta) {
    if (ruta.datos == NULL || ruta.longitud <= 0) return -1;
    char* cstr = (char*)malloc((size_t)(ruta.longitud + 1));
    if (!cstr) return -1;
    memcpy(cstr, ruta.datos, (size_t)ruta.longitud);
    cstr[ruta.longitud] = '\0';
    int r = remove(cstr);
    free(cstr);
    return r;
}

/*
 * cumple Manual 9 §5.3: hash SHA-256 de archivo con ABI CadenaSegura.
 * R269 fallo EJECUTANDO como usuario 2026-10-25: el binding externo del
 * compilador pasa CadenaSegura (struct por valor) y la implementación nativa
 * _syn_sha256_archivo (runtime/core/axon.c) recibe const char* — el callee
 * leía `longitud` como puntero, fopen fallaba y el hash salía VACÍO: el
 * instalador OpenSyn reportaba "Error: checksum incorrecto" con el archivo
 * CORRECTO (vs X-Linked-ETag de HuggingFace, verificado con curl).
 * Wrapper con el patrón de _syn_existe_archivo/_syn_eliminar_archivo de
 * este archivo; los llamadores nativos C de axon.c/axon_rt.c no cambian.
 */
CadenaSegura _syn_hash_archivo(CadenaSegura ruta) {
    if (ruta.datos == NULL || ruta.longitud <= 0) return (CadenaSegura){0, ""};
    char* cstr = (char*)malloc((size_t)(ruta.longitud + 1));
    if (!cstr) return (CadenaSegura){0, ""};
    memcpy(cstr, ruta.datos, (size_t)ruta.longitud);
    cstr[ruta.longitud] = '\0';

    /*
     * cumple Manual 9 §5.3: verificar 873 MB por arranque costaba ~9 s (medido
     * con _syn_ahora_ms, r273) y hacia fallar por timeout la verificacion del
     * modelo. Si este runtime ya calculo el digest del MISMO contenido
     * (ruta + tamano + mtime) se reutiliza; no es un atajo de la verificacion:
     * la entrada solo vale para ese archivo exacto y, si algo no cuadra, se
     * rehashea (_syn_sha256_archivo, streaming con buffer de 8 KB).
     */
    char cacheado[65];
    if (_syn_hash_cache_obtener(cstr, cacheado, sizeof(cacheado))) {
        char* datos = (char*)pool_alloc(65);
        if (datos != NULL) {
            memcpy(datos, cacheado, 65);
            free(cstr);
            return (CadenaSegura){ .longitud = 64, .datos = datos };
        }
        /* Sin memoria para el digest cacheado: se hashea igual, sin falsear. */
    }

    /* Aviso honesto antes de un hasheo largo: el usuario ve que hay actividad
     * (y el instalador no parece colgado) en vez de esperar en silencio. Va a
     * stderr para no contaminar la salida de contrato del programa. */
    long long tam = _syn_tamano_archivo_c(cstr);
    if (tam > 64LL * 1024 * 1024) {
        fprintf(stderr, "[hash] verificando %lld MB (SHA-256)...\n", tam / (1024 * 1024));
        fflush(stdout);
        fflush(stderr);
    }

    CadenaSegura hash = _syn_sha256_archivo((const char*)cstr);
    if (hash.datos != NULL && hash.longitud == 64) {
        _syn_hash_cache_guardar(cstr, hash.datos);
    }
    free(cstr);
    return hash;
}

/*
 * cumple Manual 9 §5.3: tamano de archivo con ABI CadenaSegura.
 * El binding externo del compilador pasa CadenaSegura por valor; la version
 * nativa _syn_tamano_archivo_c (runtime/core/hash_cache.c) recibe const char*
 * y llamarla directamente desde Synapse repetiria el ABI mismatch de R197
 * (devolvia -1 y el instalador perdia el aviso de tamano/tiempo).
 */
int64_t _syn_tamano_archivo(CadenaSegura ruta) {
    if (ruta.datos == NULL || ruta.longitud <= 0) return -1;
    char* cstr = (char*)malloc((size_t)(ruta.longitud + 1));
    if (!cstr) return -1;
    memcpy(cstr, ruta.datos, (size_t)ruta.longitud);
    cstr[ruta.longitud] = '\0';
    int64_t tam = (int64_t)_syn_tamano_archivo_c(cstr);
    free(cstr);
    return tam;
}



/*
 * cumple Manual 7 2.5 / Manual 9 §5.3: funciones para modelo de descarga.
 * _syn_home retorna el directorio home del usuario (~/.
 * _syn_sha256_archivo delegado a axon.c (existe ya).
 * _syn_descargar: descarga URL a destino, verifica hash SHA-256.
 */
CadenaSegura _syn_home(void) {
    const char* h = getenv("HOME");
#ifdef _WIN32
    if (h == NULL || h[0] == '\0') h = getenv("USERPROFILE");
#endif
    const char* result = (h != NULL && h[0] != '\0') ? h : ".";
    int len = (int)strlen(result);
    char* buf = (char*)pool_alloc((size_t)(len + 1));
    if (!buf) return (CadenaSegura){ .longitud = 0, .datos = "" };
    memcpy(buf, result, (size_t)len);
    buf[len] = '\0';
    return (CadenaSegura){ .longitud = len, .datos = buf };
}

int _syn_descargar(CadenaSegura url, CadenaSegura destino) {
    /*
     * Descarga un archivo desde una URL (HTTP/HTTPS) a un path local.
     * Usa la funcion _syn_http_get_archivo del modulo axon.c.
     * Retorna 0 en exito, -1 en fallo.
     */
    char url_str[1024];
    char path_str[1024];
    if (url.longitud > 0 && url.longitud < 1023) {
        memcpy(url_str, url.datos, url.longitud);
        url_str[url.longitud] = '\0';
    } else {
        return -1;
    }
    if (destino.longitud > 0 && destino.longitud < 1023) {
        memcpy(path_str, destino.datos, destino.longitud);
        path_str[destino.longitud] = '\0';
    } else {
        return -1;
    }

    /* Parsear URL: scheme://host[:port]/path */
    char* scheme_sep = strstr(url_str, "://");
    if (!scheme_sep) return -1;
    char* host_start = scheme_sep + 3;
    char* path_start = strchr(host_start, '/');
    if (!path_start) return -1;

    char host[256];
    int host_len = (int)(path_start - host_start);
    if (host_len > 255) return -1;
    memcpy(host, host_start, host_len);
    host[host_len] = '\0';

    int puerto = 80;
    char* port_sep = strchr(host, ':');
    if (port_sep) {
        *port_sep = '\0';
        puerto = atoi(port_sep + 1);
        if (puerto <= 0) puerto = 80;
    }

    return _syn_http_get_archivo(
        (CadenaSegura){ .longitud = (int)strlen(host), .datos = host },
        puerto,
        (CadenaSegura){ .longitud = (int)strlen(path_start), .datos = path_start },
        path_str
    );
}

// ============================================================================
// Phase 8: Model Inference Engine (ModeloContexto)
// ============================================================================

// --- Helper: read metadata value as int ---
static int _meta_entero(void* datos_internos, const char* clave) {
    if (!datos_internos || !clave) return 0;
    InternalData* idata = (InternalData*)datos_internos;
    for (int i = 0; i < idata->cantidad_metadatos; i++) {
        if (idata->metadatos[i].clave && idata->metadatos[i].valor &&
            strcmp(idata->metadatos[i].clave, clave) == 0) {
            char* end = NULL;
            long v = strtol(idata->metadatos[i].valor, &end, 10);
            return (end && *end == '\0') ? (int)v : 0;
            // cumple Manual 7 3: metadatos GGUF parseados con strtol+endptr
        }
    }
    return 0;
}

static float _meta_decimal(void* datos_internos, const char* clave, float por_defecto) {
    if (!datos_internos || !clave) return por_defecto;
    InternalData* idata = (InternalData*)datos_internos;
    for (int i = 0; i < idata->cantidad_metadatos; i++) {
        if (idata->metadatos[i].clave && idata->metadatos[i].valor &&
            strcmp(idata->metadatos[i].clave, clave) == 0) {
            char* end = NULL;
            double v = strtod(idata->metadatos[i].valor, &end);
            return (end && *end == '\0') ? (float)v : por_defecto;
            // cumple Manual 7 3: metadatos GGUF parseados con strtod+endptr
        }
    }
    return por_defecto;
}

// Convenience macro for building CadenaSegura from a string literal
#define CS(s) ((CadenaSegura){ .longitud = (int)(sizeof(s) - 1), .datos = (s) })

// --- BPE Tokenizer ---

typedef struct {
    int first;
    int second;
    int result;
} BpeMerge;

typedef struct BpeContext {
    int vocab_size;
    char** tokens;          // [vocab_size] token strings
    int num_merges;
    BpeMerge* merges;       // merge rules (rank = indice de la lista)
    int bos_id;
    int eos_id;
    // ME_opensyn_ia: mapa byte->token (fallback GPT-2) y tabla hash par->rank
    int byte_a_token[256];
    int* tabla_pares;
    int tabla_pares_tam;
} BpeContext;

// --- ME_opensyn_ia: mapeo GPT-2 byte-level BPE (paridad llama.cpp/HF) ---
// El vocab guarda cada byte como 1 char unicode: identidad para 33..126,
// 161..172 y 174..255; el resto (0..32, 127..160, 173) -> U+0100+n en orden
// de byte. Sin estas tablas el encode de espacios/UTF-8 y el decode producen
// basura (la pieza del espacio es U+0120 y sin el mapeo inverso saldria como
// dos bytes ilegibles en vez de un espacio).
static uint8_t _gpt2_u2b[0x180];   // codepoint -> byte (0xFF = no es fallback)
static uint32_t _gpt2_b2u[256];    // byte -> codepoint
static int _gpt2_listo = 0;

static void _gpt2_construir_tablas(void) {
    if (_gpt2_listo) return;
    memset(_gpt2_u2b, 0xFF, sizeof(_gpt2_u2b));
    int n = 0;
    for (int b = 0; b < 256; b++) {
        int ident = (b >= 33 && b <= 126) || (b >= 161 && b <= 172) || (b >= 174);
        if (ident) {
            _gpt2_u2b[b] = (uint8_t)b;
            _gpt2_b2u[b] = (uint32_t)b;
        } else {
            _gpt2_u2b[0x100 + n] = (uint8_t)b;
            _gpt2_b2u[b] = 0x100u + (uint32_t)n;
            n++;
        }
    }
    _gpt2_listo = 1;
}

// Byte de un codepoint de pieza, o -1 si no es fallback GPT-2.
static int _gpt2_char_a_byte(uint32_t cp) {
    if (!_gpt2_listo) _gpt2_construir_tablas();
    if (cp >= 0x180) return -1;
    if (cp < 0x100) return (_gpt2_u2b[cp] == (uint8_t)cp) ? (int)cp : -1;
    return (_gpt2_u2b[cp] != 0xFF) ? (int)_gpt2_u2b[cp] : -1;
}

// Decodifica 1 UTF-8; devuelve el codepoint y bytes avanzados (o -1).
static int32_t _utf8_cp(const unsigned char* s, int len, int* adv) {
    if (len <= 0) return -1;
    unsigned char c0 = s[0];
    if (c0 < 0x80) { *adv = 1; return (int32_t)c0; }
    if ((c0 & 0xE0) == 0xC0 && len >= 2) { *adv = 2; return ((c0 & 0x1Fu) << 6) | (s[1] & 0x3Fu); }
    if ((c0 & 0xF0) == 0xE0 && len >= 3) { *adv = 3; return ((c0 & 0x0Fu) << 12) | ((s[1] & 0x3Fu) << 6) | (s[2] & 0x3Fu); }
    if ((c0 & 0xF8) == 0xF0 && len >= 4) { *adv = 4; return ((c0 & 0x07u) << 18) | ((s[1] & 0x3Fu) << 12) | ((s[2] & 0x3Fu) << 6) | (s[3] & 0x3Fu); }
    *adv = 1;
    return -1;
}

static int _utf8_emitir(uint32_t cp, char* out) {
    if (cp < 0x80) { out[0] = (char)cp; return 1; }
    if (cp < 0x800) { out[0] = (char)(0xC0 | (cp >> 6)); out[1] = (char)(0x80 | (cp & 0x3F)); return 2; }
    if (cp < 0x10000) { out[0] = (char)(0xE0 | (cp >> 12)); out[1] = (char)(0x80 | ((cp >> 6) & 0x3F)); out[2] = (char)(0x80 | (cp & 0x3F)); return 3; }
    out[0] = (char)(0xF0 | (cp >> 18)); out[1] = (char)(0x80 | ((cp >> 12) & 0x3F)); out[2] = (char)(0x80 | ((cp >> 6) & 0x3F)); out[3] = (char)(0x80 | (cp & 0x3F)); return 4;
}

// Decode: pieza (chars mapeados) -> bytes reales (malloc, NUL-terminado).
static char* _pieza_a_bytes(const char* pieza, int len, int* out_len) {
    char* out = (char*)malloc((size_t)(len * 2 + 8));
    if (!out) return NULL;
    int n = 0;
    const unsigned char* p = (const unsigned char*)pieza;
    int i = 0;
    while (i < len) {
        int adv = 0;
        int32_t cp = _utf8_cp(p + i, len - i, &adv);
        if (cp < 0) { out[n++] = (char)p[i]; i++; continue; }
        int b = _gpt2_char_a_byte((uint32_t)cp);
        if (b >= 0) { out[n++] = (char)b; }
        else { n += _utf8_emitir((uint32_t)cp, out + n); }
        i += adv;
    }
    out[n] = '\0';
    *out_len = n;
    return out;
}

// Indice ordenado (texto, id) para resolver merges por texto exacto.
typedef struct { const char* s; int id; } TokIdx;
static int _tokidx_cmp(const void* a, const void* b) {
    const TokIdx* ta = (const TokIdx*)a;
    const TokIdx* tb = (const TokIdx*)b;
    return strcmp(ta->s, tb->s);
}
// Devuelve el id del token cuyo texto == clave, o -1.
static int _tokidx_buscar(const TokIdx* idx, int nidx, const char* clave) {
    TokIdx key = { clave, 0 };
    const TokIdx* r = (const TokIdx*)bsearch(&key, idx, (size_t)nidx, sizeof(TokIdx), _tokidx_cmp);
    return r ? r->id : -1;
}

// Load tokenizer data from GGUF arrays into a BpeContext
// Caller must free with _bpe_liberar
static BpeContext* _bpe_crear_desde_gguf(void* datos_internos) {
    BpeContext* bpe = (BpeContext*)calloc(1, sizeof(BpeContext));
    if (!bpe) return NULL;

    InternalData* id = (InternalData*)datos_internos;

    // Read vocab size
    int vs = _syn_gguf_arreglo_cantidad(datos_internos, "tokenizer.ggml.tokens");
    if (vs <= 0) {
        // Fallback: try metadata vocab_size
        vs = _syn_vocab_tamano(datos_internos);
        if (vs <= 0) { free(bpe); return NULL; }
        // Create minimal token list from metadata
        bpe->vocab_size = vs;
        bpe->tokens = (char**)calloc((size_t)vs, sizeof(char*));
        for (int i = 0; i < vs; i++) {
            char k[64]; snprintf(k, sizeof(k), "vocab.%d", i);
            for (int j = 0; j < id->cantidad_metadatos; j++) {
                if (id->metadatos[j].clave && id->metadatos[j].valor && strcmp(id->metadatos[j].clave, k) == 0) {
                    bpe->tokens[i] = strdup(id->metadatos[j].valor);
                    break;
                }
            }
            if (!bpe->tokens[i]) {
                char fallback[16]; snprintf(fallback, sizeof(fallback), "[%d]", i);
                bpe->tokens[i] = strdup(fallback);
            }
        }
    } else {
        bpe->vocab_size = vs;
        bpe->tokens = (char**)calloc((size_t)vs, sizeof(char*));
        for (int i = 0; i < vs; i++) {
            CadenaSegura cs = _syn_gguf_arreglo_string(datos_internos, "tokenizer.ggml.tokens", i);
            if (cs.datos) {
                bpe->tokens[i] = (char*)cs.datos; // transfer ownership
            } else {
                char fallback[16]; snprintf(fallback, sizeof(fallback), "[%d]", i);
                bpe->tokens[i] = strdup(fallback);
            }
        }
    }

    // Mapa byte -> token id (piezas de 1 char del fallback GPT-2). Requerido
    // por el encoder byte-level (espacios y UTF-8). Los 256 bytes deberian
    // estar cubiertos en un vocab GPT-2 completo.
    if (!_gpt2_listo) _gpt2_construir_tablas();
    memset(bpe->byte_a_token, 0xFF, sizeof(bpe->byte_a_token));
    int cubiertos = 0;
    for (int j = 0; j < vs; j++) {
        if (!bpe->tokens[j]) continue;
        int tlen = (int)strlen(bpe->tokens[j]);
        if (tlen > 0 && tlen <= 4) {
            int adv = 0;
            int32_t cp = _utf8_cp((const unsigned char*)bpe->tokens[j], tlen, &adv);
            if (cp >= 0 && adv == tlen) {
                int b = _gpt2_char_a_byte((uint32_t)cp);
                if (b >= 0 && bpe->byte_a_token[b] < 0) { bpe->byte_a_token[b] = j; cubiertos++; }
            }
        }
    }
    if (cubiertos < 256) {
        fprintf(stderr, "AVISO: el vocab cubre %d/256 bytes como piezas de 1 char\n", cubiertos);
    }

    // Read merges
    int n_merges = _syn_gguf_arreglo_cantidad(datos_internos, "tokenizer.ggml.merges");
    if (n_merges > 0) {
        bpe->num_merges = n_merges;
        bpe->merges = (BpeMerge*)calloc((size_t)n_merges, sizeof(BpeMerge));
        for (int i = 0; i < n_merges; i++) {
            bpe->merges[i].first = -1;
            bpe->merges[i].second = -1;
            bpe->merges[i].result = -1;
        }

        // Resolucion por TEXTO EXACTO: la pieza resultado de un merge (la
        // concatenacion first+second) existe en el vocab; su id NO se puede
        // inferir por posicion (la version anterior adivinaba vs-n_merges+i,
        // produciendo ids rotos y tokenizacion inconsistente).
        TokIdx* idx = (TokIdx*)malloc((size_t)vs * sizeof(TokIdx));
        int nidx = 0;
        if (idx) {
            for (int j = 0; j < vs; j++) {
                if (bpe->tokens[j]) { idx[nidx].s = bpe->tokens[j]; idx[nidx].id = j; nidx++; }
            }
            qsort(idx, (size_t)nidx, sizeof(TokIdx), _tokidx_cmp);
        }

        int resueltos = 0;
        for (int i = 0; i < n_merges; i++) {
            CadenaSegura ms = _syn_gguf_arreglo_string(datos_internos, "tokenizer.ggml.merges", i);
            if (!ms.datos) continue;

            char* merge_str = (char*)ms.datos;
            char* space = strchr(merge_str, ' ');
            if (!space || !idx) { free(merge_str); continue; }
            *space = '\0';
            const char* first = merge_str;
            const char* second = space + 1;
            int first_len = (int)(space - merge_str);
            int second_len = ms.longitud - first_len - 1;

            int f_id = _tokidx_buscar(idx, nidx, first);
            int s_id = _tokidx_buscar(idx, nidx, second);
            if (f_id >= 0 && s_id >= 0) {
                bpe->merges[i].first = f_id;
                bpe->merges[i].second = s_id;
                char* concat = (char*)malloc((size_t)(first_len + second_len + 1));
                if (concat) {
                    memcpy(concat, first, (size_t)first_len);
                    memcpy(concat + first_len, second, (size_t)second_len);
                    concat[first_len + second_len] = '\0';
                    bpe->merges[i].result = _tokidx_buscar(idx, nidx, concat);
                    free(concat);
                }
                if (bpe->merges[i].result >= 0) resueltos++;
            }
            free(merge_str);
        }
        free(idx);
        if (resueltos < n_merges) {
            fprintf(stderr, "AVISO: %d/%d merges resueltos por texto\n", resueltos, n_merges);
        }

        // Tabla hash par->rank para fusion O(1) durante el encode (el rank de
        // cada regla es su indice en la lista, orden BPE estandar).
        int tam = 16;
        while (tam < n_merges * 2) tam <<= 1;
        bpe->tabla_pares = (int*)malloc((size_t)tam * sizeof(int));
        if (bpe->tabla_pares) {
            for (int k = 0; k < tam; k++) bpe->tabla_pares[k] = -1;
            bpe->tabla_pares_tam = tam;
            for (int i = 0; i < n_merges; i++) {
                if (bpe->merges[i].first < 0 || bpe->merges[i].second < 0 || bpe->merges[i].result < 0) continue;
                uint32_t h = (uint32_t)((bpe->merges[i].first * 2654435761u) ^ (uint32_t)(bpe->merges[i].second * 40503u));
                int pos = (int)(h & (uint32_t)(tam - 1));
                while (bpe->tabla_pares[pos] >= 0) {
                    int oc = bpe->tabla_pares[pos];
                    if (bpe->merges[oc].first == bpe->merges[i].first &&
                        bpe->merges[oc].second == bpe->merges[i].second) break; // duplicado: ya el de menor rank
                    pos = (pos + 1) & (tam - 1);
                }
                if (bpe->tabla_pares[pos] < 0) bpe->tabla_pares[pos] = i;
            }
        }
    }

    // Read BOS/EOS from metadata
    bpe->bos_id = 1;  // default
    bpe->eos_id = 2;  // default
    for (int i = 0; i < id->cantidad_metadatos; i++) {
        if (id->metadatos[i].clave && id->metadatos[i].valor) {
            if (strcmp(id->metadatos[i].clave, "tokenizer.ggml.bos_id") == 0)
                { char* _e = NULL; long _v = strtol(id->metadatos[i].valor, &_e, 10); bpe->bos_id = (_e && *_e == '\0') ? (int)_v : 1; }
                // cumple Manual 7 3: metadatos GGUF parseados con strtol+endptr
            else if (strcmp(id->metadatos[i].clave, "tokenizer.ggml.eos_id") == 0)
                { char* _e = NULL; long _v = strtol(id->metadatos[i].valor, &_e, 10); bpe->eos_id = (_e && *_e == '\0') ? (int)_v : 2; }
                // cumple Manual 7 3: metadatos GGUF parseados con strtol+endptr
        }
    }

    return bpe;
}

static void _bpe_liberar(BpeContext* bpe) {
    if (!bpe) return;
    if (bpe->tokens) {
        for (int i = 0; i < bpe->vocab_size; i++) free(bpe->tokens[i]);
        free(bpe->tokens);
    }
    free(bpe->merges);
    free(bpe->tabla_pares);
    free(bpe);
}

// --- BPE encoding helpers ---

// Maximum symbols in a single word being encoded
#define BPE_MAX_SYMBOLS 256

// Linear scan: find merge with smallest rank for a pair
// Returns result token ID or -1 if not mergeable
// Sets *out_rank to the merge rank (index in merge list)
// Fusion O(1): busca el par en la tabla hash (rank = indice en la lista).
static int _bpe_mejor_fusion(BpeContext* bpe, int first, int second, int* out_rank) {
    if (out_rank) *out_rank = -1;
    if (!bpe->tabla_pares || bpe->tabla_pares_tam <= 0) return -1;
    uint32_t h = (uint32_t)((first * 2654435761u) ^ (uint32_t)(second * 40503u));
    int pos = (int)(h & (uint32_t)(bpe->tabla_pares_tam - 1));
    int sondas = 0;
    while (bpe->tabla_pares[pos] >= 0) {
        int i = bpe->tabla_pares[pos];
        if (bpe->merges[i].first == first && bpe->merges[i].second == second) {
            if (out_rank) *out_rank = i;
            return bpe->merges[i].result;
        }
        if (++sondas > bpe->tabla_pares_tam) break;
        pos = (pos + 1) & (bpe->tabla_pares_tam - 1);
    }
    return -1;
}

// BPE-encode a single word (text with length len)
// Returns malloc'd array of token IDs; *out_len set to number of tokens
// ME_opensyn_ia: encode BPE byte-level sobre un flujo de bytes completo.
// Reemplaza a _bpe_codificar_palabra: el mapeo fase 1 es byte -> token
// (fallback GPT-2), sin pre-tokenizacion por clases ASCII (que dividia el
// UTF-8 y rompia el espaciado GPT-2), y la fusion aplica a TODO el texto.
static int* _bpe_codificar_bytes_global(BpeContext* bpe, const char* text, int len, int* out_len) {
    *out_len = 0;
    if (!bpe || !text || len <= 0) return NULL;

    // Phase 1: simbolos = token de cada byte (fallback GPT-2).
    int cap = len + 32;
    int* syms = (int*)malloc((size_t)cap * sizeof(int));
    if (!syms) return NULL;
    int n = 0;
    for (int i = 0; i < len; i++) {
        unsigned char b = (unsigned char)text[i];
        int t = bpe->byte_a_token[b];
        if (t < 0) {
            // Sin pieza de 1 char para el byte: busqueda legacy por texto.
            char ch[2] = { (char)b, '\0' };
            for (int j = 0; j < bpe->vocab_size && t < 0; j++) {
                if (bpe->tokens[j] && strcmp(bpe->tokens[j], ch) == 0) t = j;
            }
            if (t < 0) t = 0;  // UNK
        }
        if (n >= cap) {
            cap *= 2;
            int* tmp = (int*)realloc(syms, (size_t)cap * sizeof(int));
            if (!tmp) { free(syms); return NULL; }
            syms = tmp;
        }
        syms[n++] = t;
    }
    if (n == 0) { free(syms); return NULL; }

    // Phase 2: fusionar TODAS las ocurrencias del par con menor rank
    // (algoritmo BPE estandar, paridad llama.cpp), hasta no poder fusionar.
    while (n > 1) {
        int mejor_first = -1, mejor_second = -1;
        int best_rank = bpe->num_merges;
        int best_result = -1;
        for (int i = 0; i < n - 1; i++) {
            int rank = -1;
            int r = _bpe_mejor_fusion(bpe, syms[i], syms[i + 1], &rank);
            if (r >= 0 && rank >= 0 && rank < best_rank) {
                best_rank = rank;
                best_result = r;
                mejor_first = syms[i];
                mejor_second = syms[i + 1];
            }
        }
        if (best_result < 0) break;
        int w = 0;
        for (int i = 0; i < n; ) {
            if (i + 1 < n && syms[i] == mejor_first && syms[i + 1] == mejor_second) {
                syms[w++] = best_result;
                i += 2;
            } else {
                syms[w++] = syms[i];
                i++;
            }
        }
        n = w;
        if (n <= 0) break;
    }

    int* result = (int*)malloc((size_t)n * sizeof(int));
    if (!result) { free(syms); return NULL; }
    memcpy(result, syms, (size_t)n * sizeof(int));
    free(syms);
    *out_len = n;
    return result;
}

// ME_opensyn_ia: el texto completo se codifica como un flujo de bytes.
// Los merges con prefijo de espacio (piezas U+0120..) aplican por ranking
// global; los saltos de linea/puntuacion quedan como bytes.
static int* _bpe_codificar_texto(BpeContext* bpe, const char* text, int len, int* out_len) {
    return _bpe_codificar_bytes_global(bpe, text, len, out_len);
}

// --- ModeloContexto (inference state) ---

#define MODELO_MAX_LAYERS 256
#define MODELO_MAX_SEQ_LEN 4096
#define MODELO_MAX_EMBD 8192
#define MODELO_MAX_FF 32768
#define MODELO_MAX_HEADS 128

typedef struct ModeloContexto {
    void* datos_internos;          // GGUF InternalData*
    void* datos_mmap;
    int tamano_mmap;
    void* handle_plataforma;
    void* handle_archivo;

    int n_layers;
    int n_heads;
    int n_kv_heads;
    int n_embd;
    int n_ff;
    int head_dim;
    float rope_theta;
    int max_seq_len;
    int vocab_size;
    char arch_name[64];

    int n_past;

    float* w_hidden;
    float* w_attn_norm;
    float* w_ffn_norm;
    float* w_q;
    float* w_k;
    float* w_v;
    float* w_attn_out;
    float* w_gate;
    float* w_up;
    float* w_down;
    float* w_scores;

    float* k_cache;
    float* v_cache;
    int kvc_capa_stride;
    int kvc_cabeza_stride;
    int kvc_pos_stride;

    BpeContext* bpe;
    int* ultima_codificacion;
    int ultima_codificacion_len;
} ModeloContexto;

static ModeloContexto* _mc_crear(void) {
    ModeloContexto* mc = (ModeloContexto*)calloc(1, sizeof(ModeloContexto));
    if (!mc) return NULL;
    mc->rope_theta = 10000.0f;
    mc->max_seq_len = MODELO_MAX_SEQ_LEN;

    mc->w_hidden    = (float*)malloc(MODELO_MAX_EMBD * sizeof(float));
    mc->w_attn_norm = (float*)malloc(MODELO_MAX_EMBD * sizeof(float));
    mc->w_ffn_norm  = (float*)malloc(MODELO_MAX_EMBD * sizeof(float));
    mc->w_q         = (float*)malloc(MODELO_MAX_HEADS * 128 * sizeof(float));
    mc->w_k         = (float*)malloc(MODELO_MAX_HEADS * 128 * sizeof(float));
    mc->w_v         = (float*)malloc(MODELO_MAX_HEADS * 128 * sizeof(float));
    mc->w_attn_out  = (float*)malloc(MODELO_MAX_EMBD * sizeof(float));
    mc->w_gate      = (float*)malloc(MODELO_MAX_FF * sizeof(float));
    mc->w_up        = (float*)malloc(MODELO_MAX_FF * sizeof(float));
    mc->w_down      = (float*)malloc(MODELO_MAX_EMBD * sizeof(float));
    mc->w_scores    = (float*)malloc(MODELO_MAX_HEADS * MODELO_MAX_SEQ_LEN * sizeof(float));

    if (!mc->w_hidden || !mc->w_attn_norm || !mc->w_ffn_norm ||
        !mc->w_q || !mc->w_k || !mc->w_v || !mc->w_attn_out ||
        !mc->w_gate || !mc->w_up || !mc->w_down || !mc->w_scores) {
        free(mc->w_hidden); free(mc->w_attn_norm); free(mc->w_ffn_norm);
        free(mc->w_q); free(mc->w_k); free(mc->w_v); free(mc->w_attn_out);
        free(mc->w_gate); free(mc->w_up); free(mc->w_down); free(mc->w_scores);
        free(mc); return NULL;
    }
    return mc;
}

static void _mc_destruir(ModeloContexto* mc) {
    if (!mc) return;
    free(mc->w_hidden); free(mc->w_attn_norm); free(mc->w_ffn_norm);
    free(mc->w_q); free(mc->w_k); free(mc->w_v); free(mc->w_attn_out);
    free(mc->w_gate); free(mc->w_up); free(mc->w_down); free(mc->w_scores);
    free(mc->k_cache); free(mc->v_cache);
    free(mc->ultima_codificacion);
    _bpe_liberar(mc->bpe);
    mc->bpe = NULL;
    if (mc->datos_internos) {
        InternalData* id = (InternalData*)mc->datos_internos;
        if (id->tensores) {
            for (int i = 0; i < id->cantidad_tensores; i++) {
                free(id->tensores[i].nombre);
                free(id->tensores[i].cache_f32);  // ME_opensyn_ia: cache des-cuantizada
            }
            free(id->tensores);
        }
        for (int i = 0; i < HASH_TAM; i++) {
            EntradaHash* e = id->tabla_hash[i];
            while (e) { EntradaHash* n = e->siguiente; free(e); e = n; }
        }
        for (int i = 0; i < id->cantidad_metadatos; i++) {
            free(id->metadatos[i].clave);
            free(id->metadatos[i].valor);
        }
        free(id->architecture);
        free(id);
    }
    _syn_munmap_archivo(mc->datos_mmap, (int64_t)mc->tamano_mmap,
                         mc->handle_plataforma, mc->handle_archivo);
    free(mc);
}

static Tensor _vista_tensor(float* datos, int filas, int columnas) {
    Tensor t = { .filas = (uint32_t)filas, .columnas = (uint32_t)columnas, .datos = datos, .es_mapeado = 1 };
    return t;
}

static int _kvc_inicializar(ModeloContexto* mc) {
    if (mc->n_layers <= 0 || mc->n_kv_heads <= 0 || mc->head_dim <= 0 || mc->max_seq_len <= 0) return -1;
    mc->kvc_capa_stride = mc->n_kv_heads * mc->max_seq_len * mc->head_dim;
    mc->kvc_cabeza_stride = mc->max_seq_len * mc->head_dim;
    mc->kvc_pos_stride = mc->head_dim;
    int total = mc->n_layers * mc->kvc_capa_stride;
    mc->k_cache = (float*)calloc((size_t)total, sizeof(float));
    mc->v_cache = (float*)calloc((size_t)total, sizeof(float));
    return (!mc->k_cache || !mc->v_cache) ? -1 : 0;
}

static void _kvc_guardar(ModeloContexto* mc, int capa, const float* k, const float* v) {
    int lo = capa * mc->kvc_capa_stride;
    int po = mc->n_past * mc->kvc_pos_stride;
    for (int h = 0; h < mc->n_kv_heads; h++) {
        int ho = h * mc->kvc_cabeza_stride;
        memcpy(mc->k_cache + lo + ho + po, k + h * mc->head_dim, (size_t)mc->head_dim * sizeof(float));
        memcpy(mc->v_cache + lo + ho + po, v + h * mc->head_dim, (size_t)mc->head_dim * sizeof(float));
    }
}

static Tensor _kvc_vista(ModeloContexto* mc, float* cache, int capa, int head) {
    return _vista_tensor(cache + capa * mc->kvc_capa_stride + head * mc->kvc_cabeza_stride,
                         mc->n_past, mc->head_dim);
}

static void _rope_mh(float* data, int n_heads, int hd, int pos, float theta) {
    for (int h = 0; h < n_heads; h++) {
        int off = h * hd;
        for (int i = 0; i < hd; i += 2) {
            float f = 1.0f / powf(theta, (float)i / (float)hd);
            float c = cosf((float)pos * f), s = sinf((float)pos * f);
            float x0 = data[off + i], x1 = data[off + i + 1];
            data[off + i] = x0 * c - x1 * s;
            data[off + i + 1] = x0 * s + x1 * c;
        }
    }
}

#define TENSOR(n) _syn_gguf_obtener_tensor(mc->datos_internos, CS(n))
static Tensor _modelo_evaluar_token(ModeloContexto* mc, int token_id) {
    Tensor logits = { .filas = 1, .columnas = (uint32_t)mc->vocab_size, .datos = NULL, .es_mapeado = 0 };
    int E = mc->n_embd, H = mc->n_heads, KH = mc->n_kv_heads, HD = mc->head_dim;
    int FF = mc->n_ff, NP = mc->n_past, NL = mc->n_layers;

    Tensor w_emb = TENSOR("token_embd.weight");
    Tensor w_out = TENSOR("output.weight");
    Tensor w_out_norm = TENSOR("output_norm.weight");
    if (!w_emb.datos) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: token_embd.weight NO ENCONTRADO\n"); return logits; }
    if (!w_out.datos) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: output.weight NO ENCONTRADO\n"); return logits; }

    Tensor hid = _vista_tensor(mc->w_hidden, 1, E);
    _syn_extraer_fila(hid, w_emb, token_id);

    char name[128];
    for (int l = 0; l < NL; l++) {
        snprintf(name, sizeof(name), "blk.%d.attn_norm.weight", l);
        Tensor w_an = TENSOR(name);
        snprintf(name, sizeof(name), "blk.%d.attn_q.weight", l);
        Tensor w_q = TENSOR(name);
        snprintf(name, sizeof(name), "blk.%d.attn_k.weight", l);
        Tensor w_k = TENSOR(name);
        snprintf(name, sizeof(name), "blk.%d.attn_v.weight", l);
        Tensor w_v = TENSOR(name);
        snprintf(name, sizeof(name), "blk.%d.attn_output.weight", l);
        Tensor w_ao = TENSOR(name);
        snprintf(name, sizeof(name), "blk.%d.ffn_norm.weight", l);
        Tensor w_fn = TENSOR(name);
        snprintf(name, sizeof(name), "blk.%d.ffn_gate.weight", l);
        Tensor w_gg = TENSOR(name);
        snprintf(name, sizeof(name), "blk.%d.ffn_down.weight", l);
        Tensor w_fd = TENSOR(name);
        snprintf(name, sizeof(name), "blk.%d.ffn_up.weight", l);
        Tensor w_fu = TENSOR(name);

        if (!w_an.datos || !w_q.datos) continue;

        // Pre-attention norm
        Tensor an = _vista_tensor(mc->w_attn_norm, 1, E);
        _syn_rmsnorm(an, hid, w_an, 1e-5f);

        // Q/K/V projections
        Tensor qp = _vista_tensor(mc->w_q, 1, H * HD);
        _syn_multiplicar_matrices_transpuesta_b(an, w_q, qp);
        Tensor kp = _vista_tensor(mc->w_k, 1, KH * HD);
        _syn_multiplicar_matrices_transpuesta_b(an, w_k, kp);
        Tensor vp = _vista_tensor(mc->w_v, 1, KH * HD);
        _syn_multiplicar_matrices_transpuesta_b(an, w_v, vp);

        // RoPE
        _rope_mh(mc->w_q, H, HD, NP, mc->rope_theta);
        _rope_mh(mc->w_k, KH, HD, NP, mc->rope_theta);

        // KV cache store
        _kvc_guardar(mc, l, mc->w_k, mc->w_v);

        // Attention
        int G = H / KH;
        float iscale = 1.0f / sqrtf((float)HD);
        memset(mc->w_attn_out, 0, (size_t)E * sizeof(float));

        for (int g = 0; g < G; g++) {
            for (int hk = 0; hk < KH; hk++) {
                int hq = g * KH + hk;
                Tensor kch = _kvc_vista(mc, mc->k_cache, l, hk);
                Tensor vch = _kvc_vista(mc, mc->v_cache, l, hk);

                // scores[0..NP] = Q[hq] @ K_cache[hk]^T  (dot product)
                for (int p = 0; p < NP; p++) {
                    float s = 0;
                    for (int d = 0; d < HD; d++) s += mc->w_q[hq * HD + d] * kch.datos[p * HD + d];
                    mc->w_scores[hq * mc->max_seq_len + p] = s * iscale;
                }

                // softmax
                float mx = -1e30f;
                for (int p = 0; p < NP; p++) { float v = mc->w_scores[hq * mc->max_seq_len + p]; if (v > mx) mx = v; }
                float se = 0;
                for (int p = 0; p < NP; p++) { float e = expf(mc->w_scores[hq * mc->max_seq_len + p] - mx); mc->w_scores[hq * mc->max_seq_len + p] = e; se += e; }
                if (se > 0) for (int p = 0; p < NP; p++) mc->w_scores[hq * mc->max_seq_len + p] /= se;

                // weighted V sum
                for (int d = 0; d < HD; d++) {
                    float sv = 0;
                    for (int p = 0; p < NP; p++) sv += mc->w_scores[hq * mc->max_seq_len + p] * vch.datos[p * HD + d];
                    mc->w_attn_out[hq * HD + d] = sv;
                }
            }
        }

        // Output projection
        Tensor ao = _vista_tensor(mc->w_attn_out, 1, E);
        Tensor aop = _vista_tensor(mc->w_attn_out, 1, E);
        _syn_multiplicar_matrices_transpuesta_b(ao, w_ao, aop);
        for (int i = 0; i < E; i++) mc->w_hidden[i] += mc->w_attn_out[i];

        // Pre-FFN norm
        Tensor fn = _vista_tensor(mc->w_ffn_norm, 1, E);
        _syn_rmsnorm(fn, hid, w_fn, 1e-5f);

        // Gate and up projections
        Tensor gp = _vista_tensor(mc->w_gate, 1, FF);
        _syn_multiplicar_matrices_transpuesta_b(fn, w_gg, gp);
        Tensor up = _vista_tensor(mc->w_up, 1, FF);
        _syn_multiplicar_matrices_transpuesta_b(fn, w_fu, up);
        _syn_silu(gp, gp);
        for (int i = 0; i < FF; i++) mc->w_down[i] = mc->w_gate[i] * mc->w_up[i];

        // Down projection
        Tensor gu = _vista_tensor(mc->w_down, 1, FF);
        Tensor dp = _vista_tensor(mc->w_down, 1, E);
        _syn_multiplicar_matrices_transpuesta_b(gu, w_fd, dp);
        for (int i = 0; i < E; i++) mc->w_hidden[i] += mc->w_down[i];
    }

    // Final norm
    _syn_rmsnorm(hid, hid, w_out_norm, 1e-5f);

    // LM head (logits = hidden @ output.T)
    logits.datos = (float*)malloc((size_t)mc->vocab_size * sizeof(float));
    if (!logits.datos) return logits;
    logits.filas = 1; logits.columnas = (uint32_t)mc->vocab_size;
    for (int j = 0; j < mc->vocab_size; j++) {
        float s = 0;
        for (int k = 0; k < E; k++) s += mc->w_hidden[k] * w_out.datos[j * (uint32_t)E + k];
        logits.datos[j] = s;
    }
    return logits;
}
#undef TENSOR

// --- Sampling ---

static int _sample_argmax(const float* logits, int vs) {
    int b = 0; float mv = logits[0];
    for (int i = 1; i < vs; i++) { if (logits[i] > mv) { mv = logits[i]; b = i; } }
    return b;
}

static int _sample_multinomial(const float* logits, int vs, float temp) {
    if (temp <= 0.0f) return _sample_argmax(logits, vs);
    float it = 1.0f / temp, mx = -1e30f;
    for (int i = 0; i < vs; i++) if (logits[i] > mx) mx = logits[i];
    float* probs = (float*)malloc((size_t)vs * sizeof(float));
    if (!probs) return _sample_argmax(logits, vs);
    float sum = 0;
    for (int i = 0; i < vs; i++) { float p = expf((logits[i] - mx) * it); probs[i] = p; sum += p; }
    if (sum <= 0) { free(probs); return _sample_argmax(logits, vs); }
    for (int i = 0; i < vs; i++) probs[i] /= sum;
    float r = (float)rand() / (float)RAND_MAX, cum = 0;
    for (int i = 0; i < vs; i++) { cum += probs[i]; if (r <= cum) { free(probs); return i; } }
    free(probs); return vs - 1;
}

static void _filtro_top_k(float* logits, int vs, int k) {
    if (k <= 0 || k >= vs) return;
    float* sorted = (float*)malloc((size_t)vs * sizeof(float));
    if (!sorted) return;
    memcpy(sorted, logits, (size_t)vs * sizeof(float));
    for (int i = 0; i < k; i++) { int mi = i; for (int j = i+1; j < vs; j++) if (sorted[j] > sorted[mi]) mi = j; float t = sorted[i]; sorted[i] = sorted[mi]; sorted[mi] = t; }
    float thr = sorted[k-1]; free(sorted);
    for (int i = 0; i < vs; i++) if (logits[i] < thr) logits[i] = -1e30f;
}

typedef struct { float v; int i; } _ParValor;
static int _cmp_par_desc(const void* a, const void* b) {
    const _ParValor* pa = (const _ParValor*)a;
    const _ParValor* pb = (const _ParValor*)b;
    return (pa->v > pb->v) ? -1 : (pa->v < pb->v) ? 1 : 0;
}

static void _filtro_top_p(float* logits, int vs, float p) {
    if (p <= 0.0f || p >= 1.0f || vs <= 0) return;
    // ME_opensyn_ia: antes ordenaba con seleccion O(vs^2) -> 2.3e10 ops por
    // token con vocab 151k (~30 s/token). Ahora qsort O(vs log vs).
    _ParValor* pa = (_ParValor*)malloc((size_t)vs * sizeof(_ParValor));
    if (!pa) return;
    for (int i = 0; i < vs; i++) { pa[i].v = logits[i]; pa[i].i = i; }
    qsort(pa, (size_t)vs, sizeof(_ParValor), _cmp_par_desc);
    float mx = pa[0].v, se = 0;
    for (int i = 0; i < vs; i++) { float e = expf(pa[i].v - mx); pa[i].v = e; se += e; }
    float cum = 0; int cut = vs;
    for (int i = 0; i < vs; i++) { cum += pa[i].v / se; if (cum > p) { cut = i + 1; break; } }
    for (int i = cut; i < vs; i++) logits[pa[i].i] = -1e30f;
    free(pa);
}

// --- Public API ---

void* _syn_modelo_cargar(CadenaSegura ruta) {
    GGUF_Contexto gc = _syn_gguf_abrir(ruta);
    if (!gc.es_valido) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: No se pudo abrir modelo GGUF\n"); return NULL; }
    InternalData* id = (InternalData*)gc.datos_internos;
    if (!id || !id->architecture) { _syn_gguf_cerrar_contex(gc); fprintf(stderr, "ESCAPA_DEL_ALCANCE: Modelo sin arquitectura\n"); return NULL; }

    ModeloContexto* mc = _mc_crear();
    if (!mc) { _syn_gguf_cerrar_contex(gc); return NULL; }

    mc->datos_internos = id;
    mc->datos_mmap = gc.datos_mmap;
    mc->tamano_mmap = gc.tamano_mmap;
    mc->handle_plataforma = gc.handle_plataforma;
    mc->handle_archivo = gc.handle_archivo;
    strncpy(mc->arch_name, id->architecture, sizeof(mc->arch_name)-1);

    char* ap = id->architecture;
    char mk[128];
    snprintf(mk, sizeof(mk), "%s.block_count", ap);              mc->n_layers = _meta_entero(id, mk);
    snprintf(mk, sizeof(mk), "%s.attention.head_count", ap);     mc->n_heads = _meta_entero(id, mk);
    snprintf(mk, sizeof(mk), "%s.attention.head_count_kv", ap); mc->n_kv_heads = _meta_entero(id, mk);
    if (mc->n_kv_heads <= 0) mc->n_kv_heads = mc->n_heads;
    snprintf(mk, sizeof(mk), "%s.embedding_length", ap);         mc->n_embd = _meta_entero(id, mk);
    snprintf(mk, sizeof(mk), "%s.feed_forward_length", ap);      mc->n_ff = _meta_entero(id, mk);
    snprintf(mk, sizeof(mk), "%s.rope.freq_base", ap);           mc->rope_theta = _meta_decimal(id, mk, 10000.0f);
    snprintf(mk, sizeof(mk), "%s.context_length", ap);           mc->max_seq_len = _meta_entero(id, mk);
    if (mc->max_seq_len <= 0 || mc->max_seq_len > MODELO_MAX_SEQ_LEN) mc->max_seq_len = MODELO_MAX_SEQ_LEN;
    // Vocabulario: primero el array real de GGUF (tokenizer.ggml.tokens,
    // formato llama.cpp/Qwen); respaldo al escalar legacy "vocab_size".
    // (Antes solo leía el escalar → 0 con GGUFs reales → rechazo del modelo.)
    // cumple Manual 7 §3.1: soporte de modelos GGUF (cuantizados) locales.
    int vs_vocab = _syn_gguf_arreglo_cantidad(id, "tokenizer.ggml.tokens");
    if (vs_vocab <= 0) vs_vocab = _syn_vocab_tamano(id);
    mc->vocab_size = vs_vocab;
    mc->head_dim = mc->n_embd / mc->n_heads;

    if (mc->n_layers <= 0 || mc->n_heads <= 0 || mc->n_embd <= 0 || mc->n_ff <= 0 || mc->vocab_size <= 0 ||
        mc->n_embd > MODELO_MAX_EMBD || mc->n_ff > MODELO_MAX_FF ||
        mc->n_heads > MODELO_MAX_HEADS || mc->head_dim > 128 || mc->n_layers > MODELO_MAX_LAYERS) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: Parametros invalidos: arch=%s layers=%d embd=%d heads=%d kv=%d ff=%d vocab=%d hd=%d maxseq=%d (MAX layers=%d embd=%d ff=%d heads=%d)\n",
                mc->arch_name, mc->n_layers, mc->n_embd, mc->n_heads, mc->n_kv_heads, mc->n_ff, mc->vocab_size, mc->head_dim, mc->max_seq_len, MODELO_MAX_LAYERS, MODELO_MAX_EMBD, MODELO_MAX_FF, MODELO_MAX_HEADS);
        _mc_destruir(mc); return NULL;
    }
    if (_kvc_inicializar(mc) != 0) { _mc_destruir(mc); fprintf(stderr, "ESCAPA_DEL_ALCANCE: Error KV cache\n"); return NULL; }

    // Load tokenizer
    mc->bpe = _bpe_crear_desde_gguf(id);
    if (!mc->bpe) {
        fprintf(stderr, "AVISO: No se pudo cargar tokenizer BPE\n");
    }

    mc->n_past = 0;
    return mc;
}

void _syn_modelo_cerrar(void* ctx) { _mc_destruir((ModeloContexto*)ctx); }

Tensor _syn_modelo_evaluar(void* ctx, int token_id) {
    if (!ctx) return (Tensor){0,0,NULL,0};
    ModeloContexto* mc = (ModeloContexto*)ctx;
    if (mc->n_past >= mc->max_seq_len) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: max seq len\n"); return (Tensor){0,0,NULL,0}; }
    Tensor logits = _modelo_evaluar_token(mc, token_id);
    mc->n_past++;
    return logits;
}

// Muestreo desde un buffer de logits (top_k/top_p/temperatura). Consume lc.
static int _muestrear_logits(float* lc, int vs, float temperature, int top_k, float top_p) {
    if (top_k > 0) _filtro_top_k(lc, vs, top_k);
    if (top_p > 0.0f && top_p < 1.0f) _filtro_top_p(lc, vs, top_p);
    return _sample_multinomial(lc, vs, temperature);
}

int _syn_modelo_generar(void* ctx, int token_id, float temperature, int top_k, float top_p) {
    if (!ctx) return -1;
    Tensor logits = _syn_modelo_evaluar(ctx, token_id);
    if (!logits.datos || logits.columnas <= 0) return -1;
    int vs = (int)logits.columnas;
    float* lc = (float*)malloc((size_t)vs * sizeof(float));
    if (!lc) { free(logits.datos); return -1; }
    memcpy(lc, logits.datos, (size_t)vs * sizeof(float));
    free(logits.datos);
    int tok = _muestrear_logits(lc, vs, temperature, top_k, top_p);
    free(lc);
    return tok;
}

int _syn_modelo_n_past(void* ctx) { return ctx ? ((ModeloContexto*)ctx)->n_past : 0; }

// ME-R8 (D5): metadatos del modelo que el contrato std.modelo declara y el
// runtime no implementaba. Lectura directa de ModeloContexto (datos cargados
// del header GGUF al abrir el modelo).
int _syn_modelo_obtener_n_ctx(void* ctx) {
    if (!ctx) return 0;
    return ((ModeloContexto*)ctx)->max_seq_len;
}

void _syn_modelo_establecer_n_ctx(void* ctx, int max_tokens) {
    if (!ctx || max_tokens <= 0) return;
    ModeloContexto* mc = (ModeloContexto*)ctx;
    mc->max_seq_len = max_tokens;
    if (mc->n_past > max_tokens) mc->n_past = max_tokens;
}

int _syn_modelo_obtener_n_layers(void* ctx) {
    if (!ctx) return 0;
    return ((ModeloContexto*)ctx)->n_layers;
}

int _syn_modelo_obtener_n_embd(void* ctx) {
    if (!ctx) return 0;
    return ((ModeloContexto*)ctx)->n_embd;
}

int _syn_modelo_obtener_n_heads(void* ctx) {
    if (!ctx) return 0;
    return ((ModeloContexto*)ctx)->n_heads;
}

CadenaSegura _syn_modelo_obtener_arquitectura(void* ctx) {
    if (!ctx || ((ModeloContexto*)ctx)->arch_name[0] == 0) {
        return (CadenaSegura){0, ""};
    }
    const char* n = ((ModeloContexto*)ctx)->arch_name;
    return (CadenaSegura){ .longitud = (int)strlen(n), .datos = strdup(n) };
}

CadenaSegura _syn_modelo_obtener_metadato(void* ctx, CadenaSegura clave) {
    if (!ctx || !clave.datos) return (CadenaSegura){0, ""};
    ModeloContexto* mc = (ModeloContexto*)ctx;
    // Buscar en la tabla de metadatos GGUF del header del modelo
    if (mc->datos_internos) {
        InternalData* idata = (InternalData*)mc->datos_internos;
        for (int i = 0; i < idata->cantidad_metadatos; i++) {
            if (idata->metadatos[i].clave && idata->metadatos[i].valor &&
                strcmp(idata->metadatos[i].clave, clave.datos) == 0) {
                return (CadenaSegura){ .longitud = (int)strlen(idata->metadatos[i].valor),
                                       .datos = strdup(idata->metadatos[i].valor) };
            }
        }
    }
    return (CadenaSegura){0, ""};
}

void _syn_modelo_reiniciar(void* ctx) {
    if (!ctx) return;
    ModeloContexto* mc = (ModeloContexto*)ctx;
    mc->n_past = 0;
    if (mc->k_cache) memset(mc->k_cache, 0, (size_t)(mc->n_layers * mc->kvc_capa_stride) * sizeof(float));
    if (mc->v_cache) memset(mc->v_cache, 0, (size_t)(mc->n_layers * mc->kvc_capa_stride) * sizeof(float));
}

// Convenience: decode a token given a model context (extracts datos_internos)
CadenaSegura _syn_modelo_decodificar_token(void* ctx, int token_id) {
    if (!ctx) return (CadenaSegura){0, ""};
    ModeloContexto* mc = (ModeloContexto*)ctx;
    // Prefer BPE token table: las piezas guardan los bytes como chars
    // mapeados GPT-2 (U+0120 = espacio...); hay que volver a bytes reales.
    if (mc->bpe && token_id >= 0 && token_id < mc->bpe->vocab_size && mc->bpe->tokens[token_id]) {
        const char* pieza = mc->bpe->tokens[token_id];
        int plen = (int)strlen(pieza);
        int blen = 0;
        char* bytes = _pieza_a_bytes(pieza, plen, &blen);
        if (bytes) return (CadenaSegura){ .longitud = blen, .datos = bytes };
        return (CadenaSegura){0, ""};
    }
    return _syn_decodificar_token(mc->datos_internos, token_id);
}

int _syn_modelo_vocab_tamano(void* ctx) {
    if (!ctx) return 0;
    ModeloContexto* mc = (ModeloContexto*)ctx;
    if (mc->bpe) return mc->bpe->vocab_size;
    return _syn_vocab_tamano(mc->datos_internos);
}

// Encode text using BPE tokenizer from model context
// Result cached in model context; subsequent calls to _syn_modelo_codificar_obtener retrieve tokens
// Returns token count (0 if error or no BPE available)
int _syn_modelo_codificar_contar(void* ctx, CadenaSegura texto) {
    if (!ctx || !texto.datos || texto.longitud <= 0) return 0;
    ModeloContexto* mc = (ModeloContexto*)ctx;
    if (!mc->bpe) return 0;

    // Free previous encoding
    free(mc->ultima_codificacion);
    mc->ultima_codificacion = NULL;
    mc->ultima_codificacion_len = 0;

    // Convert to null-terminated
    char* cstr = (char*)malloc((size_t)(texto.longitud + 1));
    if (!cstr) return 0;
    memcpy(cstr, texto.datos, (size_t)texto.longitud);
    cstr[texto.longitud] = '\0';

    int out_len = 0;
    int* ids = _bpe_codificar_texto(mc->bpe, cstr, texto.longitud, &out_len);
    free(cstr);

    if (ids) {
        mc->ultima_codificacion = ids;
        mc->ultima_codificacion_len = out_len;
    }
    return mc->ultima_codificacion_len;
}

// Get token ID at index from the last encoding (must call _syn_modelo_codificar_contar first)
// Returns token ID or -1 if index out of range
int _syn_modelo_codificar_obtener(void* ctx, int indice) {
    if (!ctx) return -1;
    ModeloContexto* mc = (ModeloContexto*)ctx;
    if (!mc->ultima_codificacion || indice < 0 || indice >= mc->ultima_codificacion_len) return -1;
    return mc->ultima_codificacion[indice];
}

// --- Oracle: end-to-end text generation from prompt ---

// Generate text from a prompt auto-regressively.
// Returns malloc'd string of generated text (caller must free with _syn_texto_liberar).
// Stops at EOS token or max_tokens.
CadenaSegura _syn_modelo_generar_texto(void* ctx, CadenaSegura prompt, int max_tokens, float temperature, int top_k, float top_p) {
    if (!ctx || !prompt.datos || prompt.longitud <= 0) return (CadenaSegura){0, NULL};
    ModeloContexto* mc = (ModeloContexto*)ctx;
    if (!mc->bpe) return (CadenaSegura){0, NULL};

    // Encode prompt
    int n_prompt = _syn_modelo_codificar_contar(ctx, prompt);
    if (n_prompt <= 0) return (CadenaSegura){0, NULL};

    // Prompt processing: feed each token; conservamos los logits del ultimo
    // token del prompt para muestrear el PRIMER token generado (sin volver a
    // evaluar un token extra que desfasa posiciones del KV cache).
    _syn_modelo_reiniciar(ctx);
    Tensor ult_logits = { .datos = NULL, .columnas = 0 };
    for (int i = 0; i < n_prompt; i++) {
        int tok = _syn_modelo_codificar_obtener(ctx, i);
        if (tok < 0) break;
        if (ult_logits.datos) free(ult_logits.datos);
        ult_logits = _syn_modelo_evaluar(ctx, tok);
        if (!ult_logits.datos) { ult_logits.datos = NULL; break; }
    }

    // Auto-regressive generation
    int last_tok = 0;
    // Start with a pre-allocated output buffer
    int out_cap = 256;
    int out_len = 0;
    char* out_buf = (char*)malloc((size_t)out_cap);
    if (!out_buf) return (CadenaSegura){0, NULL};
    out_buf[0] = '\0';

    for (int i = 0; i < max_tokens; i++) {
        if (i == 0 && ult_logits.datos) {
            int vs = (int)ult_logits.columnas;
            float* lc = (float*)malloc((size_t)vs * sizeof(float));
            if (lc) {
                memcpy(lc, ult_logits.datos, (size_t)vs * sizeof(float));
                last_tok = _muestrear_logits(lc, vs, temperature, top_k, top_p);
                free(lc);
            } else {
                last_tok = -1;
            }
            free(ult_logits.datos);
            ult_logits.datos = NULL;
        } else {
            last_tok = _syn_modelo_generar(ctx, last_tok, temperature, top_k, top_p);
        }
        if (last_tok < 0 || last_tok == mc->bpe->eos_id || last_tok == mc->bpe->bos_id) break;

        // Decode token
        CadenaSegura tok_str = _syn_modelo_decodificar_token(ctx, last_tok);
        if (!tok_str.datos) continue;

        // Append to output buffer; handle escaping for special chars
        // Replace </s> and similar control tokens with empty
        int skip = 0;
        if (tok_str.longitud == 1 && (unsigned char)tok_str.datos[0] < 32) skip = 1;
        if (!skip && tok_str.longitud > 0) {
            // Grow buffer if needed
            if ((size_t)(out_len + tok_str.longitud + 1) > (size_t)out_cap) {
                out_cap = (out_len + tok_str.longitud + 1) * 2;
                char* tmp = (char*)realloc(out_buf, (size_t)out_cap);
                if (!tmp) { free(out_buf); free((void*)tok_str.datos); return (CadenaSegura){0, NULL}; }
                out_buf = tmp;
            }
            memcpy(out_buf + out_len, tok_str.datos, (size_t)tok_str.longitud);
            out_len += tok_str.longitud;
            out_buf[out_len] = '\0';
        }
        free((void*)tok_str.datos);
    }

    // Recorte de marcadores de fin de turno que escapen como piezas sueltas
    // (tokens agregados tipo added; no detienen el bucle por no ser == eos_id).
    {
        char* fin = strstr(out_buf, "<|im_end|>");
        if (fin) { *fin = '\0'; out_len = (int)(fin - out_buf); }
        fin = strstr(out_buf, "<|endoftext|>");
        if (fin) { *fin = '\0'; out_len = (int)(fin - out_buf); }
    }
    if (out_len == 0) { free(out_buf); return (CadenaSegura){0, NULL}; }
    return (CadenaSegura){ .longitud = out_len, .datos = out_buf };
}

// --- Oracle: in-process Synapse compilation via helper script ---

// State for last compilation result
static char* _cached_codigo_c = NULL;
static char* _cached_error_comp = NULL;
static int _cached_error_linea = 0;

// Free cached compilation state
static void _liberar_cache_compilacion(void) {
    free(_cached_codigo_c); _cached_codigo_c = NULL;
    free(_cached_error_comp); _cached_error_comp = NULL;
    _cached_error_linea = 0;
}

// Simple JSON string value extractor: finds "key":"value" or "key": "value"
// Returns malloc'd string or NULL if not found
static char* _json_extract_string(const char* json, const char* key) {
    if (!json || !key) return NULL;
    // Build search pattern: "key":
    char* pattern = (char*)malloc((size_t)(strlen(key) + 5));
    if (!pattern) return NULL;
    sprintf(pattern, "\"%s\"", key);
    char* start = strstr(json, pattern);
    free(pattern);
    if (!start) return NULL;
    start = strchr(start + strlen(key) + 2, '"');
    if (!start) return NULL;
    start++; // skip opening quote
    char* end = strchr(start, '"');
    if (!end) return NULL;
    int len = (int)(end - start);
    if (len <= 0) return NULL;
    char* val = (char*)malloc((size_t)(len + 1));
    if (!val) return NULL;
    memcpy(val, start, (size_t)len);
    val[len] = '\0';
    // Unescape JSON strings
    // Handle \n, \t, \", \\ etc.
    char* src = val;
    char* dst = val;
    while (*src) {
        if (*src == '\\' && *(src+1)) {
            src++;
            switch (*src) {
                case 'n': *dst++ = '\n'; break;
                case 't': *dst++ = '\t'; break;
                case 'r': *dst++ = '\r'; break;
                case '"': *dst++ = '"'; break;
                case '\\': *dst++ = '\\'; break;
                default: *dst++ = '\\'; *dst++ = *src; break;
            }
        } else {
            *dst++ = *src;
        }
        src++;
    }
    *dst = '\0';
    return val;
}

// Extract boolean value from JSON: "key":true or "key": false
static int _json_extract_bool(const char* json, const char* key) {
    if (!json || !key) return 0;
    char* pattern = (char*)malloc((size_t)(strlen(key) + 10));
    if (!pattern) return 0;
    sprintf(pattern, "\"%s\": true", key);
    int found = (strstr(json, pattern) != NULL);
    if (!found) {
        sprintf(pattern, "\"%s\":true", key);
        found = (strstr(json, pattern) != NULL);
    }
    free(pattern);
    return found;
}

// Extract integer from JSON: "key":123
static int _json_extract_int(const char* json, const char* key) {
    if (!json || !key) return 0;
    char* pattern = (char*)malloc((size_t)(strlen(key) + 5));
    if (!pattern) return 0;
    sprintf(pattern, "\"%s\"", key);
    char* start = strstr(json, pattern);
    free(pattern);
    if (!start) return 0;
    start = strchr(start, ':');
    if (!start) return 0;
    start++;
    while (*start == ' ') start++;
    if (*start < '0' || *start > '9') return 0;
    char* end = NULL;
    long v = strtol(start, &end, 10);
    return (end && *end == '\0') ? (int)v : 0;
    // cumple Manual 7 3: metadatos GGUF parseados con strtol+endptr
}

// Compile Synapse source code and store result in cached state.
// Returns 0 on success (generated C code available via _syn_obtener_codigo_generado),
// or -1 on error (error info via _syn_obtener_error_compilacion / _syn_obtener_linea_error).
int _syn_compilar_codigo(CadenaSegura fuente) {
    _liberar_cache_compilacion();
    if (!fuente.datos || fuente.longitud <= 0) {
        _cached_error_comp = strdup("Fuente vacia");
        return -1;
    }

    // Write source to temp file
    const char* temp_syn = "oraculo_temp.syn";
    FILE* f = fopen(temp_syn, "wb");
    if (!f) { _cached_error_comp = strdup("No se pudo crear archivo temporal"); return -1; }
    fwrite(fuente.datos, 1, (size_t)fuente.longitud, f);
    fclose(f);

    // Build command: python _compilar_helper.py oraculo_temp.syn
    char cmd[512];
    snprintf(cmd, sizeof(cmd), "py -3 _compilar_helper.py \"%s\" 2>nul", temp_syn);

#ifdef _WIN32
    FILE* pipe = _popen(cmd, "r");
#else
    FILE* pipe = popen(cmd, "r");
#endif
    if (!pipe) {
        _cached_error_comp = strdup("No se pudo ejecutar compilador");
        remove(temp_syn);
        return -1;
    }

    // Read all output
    char json_buf[65536];
    size_t json_len = 0;
    char line[4096];
    while (fgets(line, sizeof(line), pipe)) {
        size_t llen = strlen(line);
        if (json_len + llen < sizeof(json_buf) - 1) {
            memcpy(json_buf + json_len, line, llen);
            json_len += llen;
        }
    }
    json_buf[json_len] = '\0';
#ifdef _WIN32
    _pclose(pipe);
#else
    pclose(pipe);
#endif
    remove(temp_syn);

    if (json_len == 0) {
        _cached_error_comp = strdup("Sin respuesta del compilador");
        return -1;
    }

    // Parse JSON response
    int exito = _json_extract_bool(json_buf, "exito");
    if (exito) {
        _cached_codigo_c = _json_extract_string(json_buf, "codigo_c");
        if (!_cached_codigo_c) {
            _cached_error_comp = strdup("Respuesta JSON mal formada");
            return -1;
        }
        return 0;
    } else {
        // Extract first error
        _cached_error_comp = _json_extract_string(json_buf, "mensaje");
        _cached_error_linea = _json_extract_int(json_buf, "linea");
        // If the above fails (array of errors), try simpler extraction
        if (!_cached_error_comp) {
            // Fallback: extract from first error object in array
            char* err_start = strstr(json_buf, "\"mensaje\"");
            if (err_start) {
                // Find the value after "mensaje":
                char* val_start = strchr(err_start, ':');
                if (val_start) {
                    val_start++;
                    while (*val_start == ' ') val_start++;
                    if (*val_start == '"') {
                        val_start++;
                        char* val_end = strchr(val_start, '"');
                        if (val_end) {
                            int elen = (int)(val_end - val_start);
                            _cached_error_comp = (char*)malloc((size_t)(elen + 1));
                            if (_cached_error_comp) {
                                memcpy(_cached_error_comp, val_start, (size_t)elen);
                                _cached_error_comp[elen] = '\0';
                            }
                        }
                    }
                }
            }
            // Try to extract line number
            _cached_error_linea = _json_extract_int(json_buf, "linea");
        }
        if (!_cached_error_comp) _cached_error_comp = strdup("Error de compilacion desconocido");
        return -1;
    }
}

// Get the generated C code from the last successful compilation
CadenaSegura _syn_obtener_codigo_generado(void) {
    if (!_cached_codigo_c) return (CadenaSegura){0, ""};
    return (CadenaSegura){ .longitud = (int)strlen(_cached_codigo_c), .datos = strdup(_cached_codigo_c) };
}

// Get the error message from the last failed compilation
CadenaSegura _syn_obtener_error_compilacion(void) {
    if (!_cached_error_comp) return (CadenaSegura){0, ""};
    return (CadenaSegura){ .longitud = (int)strlen(_cached_error_comp), .datos = strdup(_cached_error_comp) };
}

// Get the error line number from the last failed compilation
int _syn_obtener_linea_error(void) {
    return _cached_error_linea;
}

// --- Oracle: extract code block from model output ---

// Extract the first Synapse code block from text (between ```synapse and ``` or just ``` ... ```)
// Returns malloc'd string or NULL if no code block found
CadenaSegura _syn_extraer_bloque_codigo(CadenaSegura texto) {
    if (!texto.datos || texto.longitud <= 0) return (CadenaSegura){0, NULL};

    // Convert to null-terminated for easier parsing
    char* cstr = (char*)malloc((size_t)(texto.longitud + 1));
    if (!cstr) return (CadenaSegura){0, NULL};
    memcpy(cstr, texto.datos, (size_t)texto.longitud);
    cstr[texto.longitud] = '\0';

    char* start = NULL;
    char* end = NULL;

    // Try ```synapse ... ``` first, then ``` ... ```
    char* markers[] = {"```synapse", "```", "```Synapse", "```sinaptico", NULL};
    for (int i = 0; markers[i]; i++) {
        start = strstr(cstr, markers[i]);
        if (start) {
            start += strlen(markers[i]);
            // Skip whitespace/newline after marker
            while (*start == ' ' || *start == '\t' || *start == '\n' || *start == '\r') start++;
            end = strstr(start, "```");
            if (end) break;
        }
    }

    if (!start || !end) {
        // No code block found; try to use the whole text (strip leading/trailing whitespace)
        start = cstr;
        while (*start == ' ' || *start == '\t' || *start == '\n' || *start == '\r') start++;
        if (*start == '\0') { free(cstr); return (CadenaSegura){0, NULL}; }
        end = cstr + texto.longitud;
        // Trim trailing whitespace
        while (end > start && (*(end-1) == ' ' || *(end-1) == '\t' || *(end-1) == '\n' || *(end-1) == '\r')) end--;
        if (end <= start) { free(cstr); return (CadenaSegura){0, NULL}; }
    }

    int len = (int)(end - start);
    char* code = (char*)malloc((size_t)(len + 1));
    if (!code) { free(cstr); return (CadenaSegura){0, NULL}; }
    memcpy(code, start, (size_t)len);
    code[len] = '\0';
    free(cstr);
    return (CadenaSegura){ .longitud = len, .datos = code };
}
