// runtime/core/ffi_marshaling.h
// FASE 24.B — Marshaling automático de tipos para FFI
// Manual 4 §7: FFI Marshaling y Zero-Copy
#ifndef FFI_MARSHALING_H
#define FFI_MARSHALING_H

#include <stdint.h>
#include "synapse_rt_types.h"

// =====================================================================
// §7.2.1: Conversión de texto a C string (zero-copy)
// =====================================================================

// Convierte un CadenaSegura a const char* añadiendo \0 al final
// en la arena actual (sin copiar el buffer entero).
// Retorna NULL si texto o arena son nulos.
const char* ffi_texto_a_c_string(CadenaSegura* texto, Arena* arena);

// =====================================================================
// §7.2.2: Conversión de tipos primitivos
// =====================================================================

// entero → int64_t (directo, sin copia)
int64_t ffi_entero_a_i64(int64_t valor);

// decimal → double (directo, sin copia)
double ffi_decimal_a_f64(double valor);

// booleano → int (0 = falso, 1 = verdadero)
int ffi_booleano_a_int(int valor);

// =====================================================================
// §7.2.3: Conversión de colecciones
// =====================================================================

// Lista<T> → puntero a datos + longitud
// Retorna el puntero interno de la lista (zero-copy) y la longitud.
const void* ffi_lista_a_slice(void* ptr_lista, int tipo_elem);
int64_t ffi_lista_longitud(void* ptr_lista);

// Mapa<K,V> → hash table C
const void* ffi_mapa_a_handle(void* ptr_mapa);
int64_t ffi_mapa_tamano(void* ptr_mapa);

// =====================================================================
// §7.2.4: Callback registry para lifecycle management
// =====================================================================

#define FFI_MAX_CALLBACKS 256

typedef struct {
    void (*funcion)(void*);
    void* dato;
    int es_debil;           // 1 = referencia débil
    int activo;             // 1 = registrado, 0 = des-registrado
} FFI_Callback;

// Registra un callback de C con referencia débil al dato.
// Retorna el ID del callback (0..FFI_MAX_CALLBACKS-1), o -1 si no hay espacio.
int ffi_registrar_callback(void (*funcion)(void*), void* dato, int es_debil);

// Des-registra un callback previamente registrado.
void ffi_desregistrar_callback(int id);

// Invoca un callback de forma segura.
// Si el dato débil fue destruido (NULL), retorna sin ejecutar.
void ffi_invocar_callback(int id);

#endif // FFI_MARSHALING_H
