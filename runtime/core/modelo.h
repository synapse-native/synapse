// runtime/core/modelo.h — Public types for modelo.c (ME-SEC-3: testable interface)
// cumple Manual 7 §3: metadatos GGUF con strtol+endptr
// cumple Manual 2 §12: contratos requiere/garantiza expuestos
#ifndef MODELO_H
#define MODELO_H

#include <stdint.h>

#define HASH_TAM 256
#define MAX_METADATOS 128
#define MAX_ARRAY_METADATOS 32

typedef struct {
    char* nombre;
    int n_dimensiones;
    uint64_t dimensiones[4];
    int tipo;
    uint64_t offset;
} TensorInfo;

typedef struct EntradaHash {
    uint32_t indice_tensor;
    struct EntradaHash* siguiente;
} EntradaHash;

typedef struct {
    char* clave;
    char* valor;
} ParMetadato;

typedef struct {
    char* clave;
    int tipo_elemento;
    int cantidad;
    uint64_t data_pos;
} ArrayMetaEntry;

typedef struct InternalData {
    void* mmap_ptr;
    int64_t tamano_mmap;
    uint64_t tensor_data_base_offset;
    int cantidad_tensores;
    TensorInfo* tensores;
    EntradaHash* tabla_hash[HASH_TAM];
    int cantidad_metadatos;
    ParMetadato metadatos[MAX_METADATOS];
    char* architecture;
    ArrayMetaEntry arrays[MAX_ARRAY_METADATOS];
    int cantidad_arrays;
} InternalData;

// Public functions (ME-SEC-3: contratos requiere/garantiza)
// requiere: datos_internos != NULL o retorna 0
// garantiza: retorna 0 si clave no encontrada o valor no es entero válido
int _syn_vocab_tamano(void* datos_internos);

#endif // MODELO_H
