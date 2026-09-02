// cumple Manual 6 §3: lista enlazada
// runtime/core/lista.c — Dynamic list (vector) for Syquex lib/lista.syq
// Manual 3 §5.2: Lista<T> — lista dinámica
// Implementación simple: array dinámico con realloc

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define LISTA_CAP_INICIAL 16

typedef struct {
    int64_t* datos;
    int longitud;
    int capacidad;
} ListaSyn;

// --- Creación ---

void* _syn_lista_crear(void) {
    ListaSyn* l = (ListaSyn*)malloc(sizeof(ListaSyn));
    if (!l) return NULL;
    l->datos = (int64_t*)malloc(LISTA_CAP_INICIAL * sizeof(int64_t));
    if (!l->datos) { free(l); return NULL; }
    l->longitud = 0;
    l->capacidad = LISTA_CAP_INICIAL;
    return l;
}

// --- Operaciones básicas ---

int _syn_lista_longitud(void* l) {
    if (!l) return 0;
    return ((ListaSyn*)l)->longitud;
}

static void _lista_asegurar_capacidad(ListaSyn* l, int nueva_cap) {
    if (nueva_cap <= l->capacidad) return;
    int cap = l->capacidad;
    while (cap < nueva_cap) cap *= 2;
    int64_t* tmp = (int64_t*)realloc(l->datos, cap * sizeof(int64_t));
    if (tmp) {
        l->datos = tmp;
        l->capacidad = cap;
    }
}

void _syn_lista_agregar(void* l, int64_t elemento) {
    if (!l) return;
    ListaSyn* ls = (ListaSyn*)l;
    _lista_asegurar_capacidad(ls, ls->longitud + 1);
    ls->datos[ls->longitud++] = elemento;
}

int64_t _syn_lista_obtener(void* l, int indice) {
    if (!l) return 0;
    ListaSyn* ls = (ListaSyn*)l;
    if (indice < 0 || indice >= ls->longitud) return 0;
    return ls->datos[indice];
}

void _syn_lista_establecer(void* l, int indice, int64_t valor) {
    if (!l) return;
    ListaSyn* ls = (ListaSyn*)l;
    if (indice < 0 || indice >= ls->longitud) return;
    ls->datos[indice] = valor;
}

// --- Eliminación ---

void _syn_lista_eliminar(void* l, int indice) {
    if (!l) return;
    ListaSyn* ls = (ListaSyn*)l;
    if (indice < 0 || indice >= ls->longitud) return;
    // Desplazar elementos hacia atrás
    for (int i = indice; i < ls->longitud - 1; i++) {
        ls->datos[i] = ls->datos[i + 1];
    }
    ls->longitud--;
}

void _syn_lista_limpiar(void* l) {
    if (!l) return;
    ((ListaSyn*)l)->longitud = 0;
}

// --- Liberación ---

void _syn_lista_liberar(void* l) {
    if (!l) return;
    ListaSyn* ls = (ListaSyn*)l;
    if (ls->datos) free(ls->datos);
    free(ls);
}
