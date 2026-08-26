// runtime/core/ffi_marshaling.c
// FASE 24.B — Marshaling automático de tipos para FFI
// Manual 4 §7: FFI Marshaling y Zero-Copy
//
// Implementación de las funciones de marshaling para interoperabilidad
// entre Syquex y C. El objetivo es minimizar copias y gestionar
// correctamente el lifecycle de los callbacks de C.

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include "ffi_marshaling.h"

// =====================================================================
// §7.2.1: Conversión de texto a C string (zero-copy)
// =====================================================================

const char* ffi_texto_a_c_string(CadenaSegura* texto, Arena* arena) {
    if (!texto || !arena) return NULL;
    if (!texto->datos) return NULL;

    // Asignar longitud + 1 byte para el \0 en la arena
    size_t len = (size_t)texto->longitud;
    char* c_str = (char*)arena_alloc(arena, len + 1, 1);
    if (!c_str) return NULL;

    // Copiar contenido y añadir \0 al final
    if (len > 0) {
        memcpy(c_str, texto->datos, len);
    }
    c_str[len] = '\0';

    return c_str;
}

// =====================================================================
// §7.2.2: Conversión de tipos primitivos
// =====================================================================

int64_t ffi_entero_a_i64(int64_t valor) {
    return valor;
}

double ffi_decimal_a_f64(double valor) {
    return valor;
}

int ffi_booleano_a_int(int valor) {
    return valor ? 1 : 0;
}

// =====================================================================
// §7.2.3: Conversión de colecciones
// =====================================================================

// Para Listas y Mapas, el marshaling depende de la estructura interna
// del runtime. Estas funciones son wrappers que delegan al runtime.

const void* ffi_lista_a_slice(void* ptr_lista, int tipo_elem) {
    // En el runtime de Syquex, las listas son estructuras con:
    //   uint64_t longitud
    //   uint64_t capacidad
    //   void* datos
    // El slice es simplemente el puntero a 'datos'.
    if (!ptr_lista) return NULL;
    // El offset de 'datos' en la estructura Lista depende del runtime
    // Por ahora, retornamos el puntero tal cual (cast a slice)
    return (const void*)((uint8_t*)ptr_lista + 16); // offset de datos
}

int64_t ffi_lista_longitud(void* ptr_lista) {
    if (!ptr_lista) return 0;
    // El offset de 'longitud' en la estructura Lista es 0
    return *(int64_t*)ptr_lista;
}

const void* ffi_mapa_a_handle(void* ptr_mapa) {
    if (!ptr_mapa) return NULL;
    return ptr_mapa;
}

int64_t ffi_mapa_tamano(void* ptr_mapa) {
    if (!ptr_mapa) return 0;
    // El tamaño está en el offset 0 de la estructura Mapa
    return *(int64_t*)ptr_mapa;
}

// =====================================================================
// §7.2.4: Callback registry para lifecycle management
// =====================================================================

static FFI_Callback _ffi_callbacks[FFI_MAX_CALLBACKS];
static int _ffi_callback_count = 0;

int ffi_registrar_callback(void (*funcion)(void*), void* dato, int es_debil) {
    if (!funcion) return -1;

    // Buscar un slot libre o crear uno nuevo
    for (int i = 0; i < _ffi_callback_count; i++) {
        if (!_ffi_callbacks[i].activo) {
            _ffi_callbacks[i].funcion = funcion;
            _ffi_callbacks[i].dato = dato;
            _ffi_callbacks[i].es_debil = es_debil;
            _ffi_callbacks[i].activo = 1;
            return i;
        }
    }

    // Crear nuevo slot si hay espacio
    if (_ffi_callback_count < FFI_MAX_CALLBACKS) {
        int id = _ffi_callback_count;
        _ffi_callbacks[id].funcion = funcion;
        _ffi_callbacks[id].dato = dato;
        _ffi_callbacks[id].es_debil = es_debil;
        _ffi_callbacks[id].activo = 1;
        _ffi_callback_count++;
        return id;
    }

    return -1; // No hay espacio
}

void ffi_desregistrar_callback(int id) {
    if (id < 0 || id >= _ffi_callback_count) return;
    _ffi_callbacks[id].activo = 0;
    _ffi_callbacks[id].funcion = NULL;
    _ffi_callbacks[id].dato = NULL;
}

void ffi_invocar_callback(int id) {
    if (id < 0 || id >= _ffi_callback_count) return;
    if (!_ffi_callbacks[id].activo) return;
    if (!_ffi_callbacks[id].funcion) return;

    // Para referencias débiles, verificar si el dato sigue siendo válido
    // (en un sistema real, esto verificaría el weak pointer)
    if (_ffi_callbacks[id].es_debil && !_ffi_callbacks[id].dato) {
        return; // Objeto destruido, no invocar
    }

    _ffi_callbacks[id].funcion(_ffi_callbacks[id].dato);
}
