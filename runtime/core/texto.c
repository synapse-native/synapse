// runtime/core/texto.c — Text module for Syquex standard library
// Manual 3 §12.1: lib/texto.syq — Manipulación avanzada de cadenas
// Compilar: gcc -c runtime/core/texto.c -o texto.o

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "synapse_rt_types.h"
#include "texto.h"

// ============================================================
// Internal: split list storage (simple static array)
// ============================================================

#define SPLIT_MAX 256
#define SPLIT_STR_MAX 4096

static char* _split_store[SPLIT_MAX][SPLIT_STR_MAX];
static int _split_count[SPLIT_MAX];
static int _split_used = 0;

static int64_t _split_alloc(void) {
    for (int i = 0; i < SPLIT_MAX; i++) {
        if (_split_count[i] == 0 && _split_store[i][0] == NULL) {
            _split_used++;
            return i;
        }
    }
    return -1;
}

static void _split_free(int64_t id) {
    if (id < 0 || id >= SPLIT_MAX) return;
    for (int i = 0; i < _split_count[id]; i++) {
        if (_split_store[id][i]) {
            free(_split_store[id][i]);
            _split_store[id][i] = NULL;
        }
    }
    _split_count[id] = 0;
}

// ============================================================
// §12.1 — Longitud
// ============================================================

int64_t _syn_texto_longitud(CadenaSegura t) {
    if (t.datos == NULL) return 0;
    return (int64_t)t.longitud;
}

// ============================================================
// §12.1 — Subcadena
// ============================================================

CadenaSegura _syn_texto_subcadena(CadenaSegura t, int64_t inicio, int64_t fin) {
    if (t.datos == NULL || t.longitud <= 0) return (CadenaSegura){0, ""};
    if (inicio < 0) inicio = 0;
    if (fin > t.longitud) fin = t.longitud;
    if (inicio >= fin) return (CadenaSegura){0, ""};
    int len = (int)(fin - inicio);
    char* buf = (char*)malloc(len + 1);
    if (!buf) return (CadenaSegura){0, ""};
    memcpy(buf, t.datos + inicio, len);
    buf[len] = '\0';
    return (CadenaSegura){.longitud = len, .datos = buf};
}

// ============================================================
// §12.1 — Contiene
// ============================================================

int _syn_texto_contiene(CadenaSegura t, CadenaSegura patron) {
    if (t.datos == NULL || patron.datos == NULL) return 0;
    if (patron.longitud == 0) return 1;
    if (patron.longitud > t.longitud) return 0;
    for (int i = 0; i <= t.longitud - patron.longitud; i++) {
        if (memcmp(t.datos + i, patron.datos, patron.longitud) == 0) return 1;
    }
    return 0;
}

// ============================================================
// §12.1 — Reemplazar
// ============================================================

CadenaSegura _syn_texto_reemplazar(CadenaSegura t, CadenaSegura viejo, CadenaSegura nuevo) {
    if (t.datos == NULL || viejo.datos == NULL || nuevo.datos == NULL)
        return (CadenaSegura){0, ""};
    if (viejo.longitud == 0) return t;

    /* Count occurrences */
    int count = 0;
    int i = 0;
    while (i <= t.longitud - viejo.longitud) {
        if (memcmp(t.datos + i, viejo.datos, viejo.longitud) == 0) {
            count++;
            i += viejo.longitud;
        } else {
            i++;
        }
    }
    if (count == 0) return t;

    /* Build result */
    int new_len = t.longitud + count * (nuevo.longitud - viejo.longitud);
    char* buf = (char*)malloc(new_len + 1);
    if (!buf) return (CadenaSegura){0, ""};

    int pos = 0;
    int src = 0;
    while (src <= t.longitud - viejo.longitud) {
        if (memcmp(t.datos + src, viejo.datos, viejo.longitud) == 0) {
            memcpy(buf + pos, nuevo.datos, nuevo.longitud);
            pos += nuevo.longitud;
            src += viejo.longitud;
        } else {
            buf[pos++] = t.datos[src++];
        }
    }
    /* Copy remaining */
    while (src < t.longitud) {
        buf[pos++] = t.datos[src++];
    }
    buf[pos] = '\0';
    return (CadenaSegura){.longitud = pos, .datos = buf};
}

// ============================================================
// §12.1 — Dividir (split)
// ============================================================

int64_t _syn_texto_dividir(CadenaSegura t, CadenaSegura separador) {
    if (t.datos == NULL) return -1;
    int64_t id = _split_alloc();
    if (id < 0) return -1;

    if (separador.datos == NULL || separador.longitud == 0) {
        /* Split by nothing = single element */
        char* copy = (char*)malloc(t.longitud + 1);
        if (copy) {
            memcpy(copy, t.datos, t.longitud);
            copy[t.longitud] = '\0';
            _split_store[id][0] = copy;
            _split_count[id] = 1;
        }
        return id;
    }

    int count = 0;
    int start = 0;
    while (start <= t.longitud) {
        int found = -1;
        if (start <= t.longitud - separador.longitud) {
            for (int i = start; i <= t.longitud - separador.longitud; i++) {
                if (memcmp(t.datos + i, separador.datos, separador.longitud) == 0) {
                    found = i;
                    break;
                }
            }
        }
        if (found >= 0) {
            int seg_len = found - start;
            char* seg = (char*)malloc(seg_len + 1);
            if (seg) {
                memcpy(seg, t.datos + start, seg_len);
                seg[seg_len] = '\0';
                if (count < SPLIT_STR_MAX) {
                    _split_store[id][count++] = seg;
                } else {
                    free(seg);
                }
            }
            start = found + separador.longitud;
        } else {
            int seg_len = t.longitud - start;
            char* seg = (char*)malloc(seg_len + 1);
            if (seg) {
                memcpy(seg, t.datos + start, seg_len);
                seg[seg_len] = '\0';
                if (count < SPLIT_STR_MAX) {
                    _split_store[id][count++] = seg;
                } else {
                    free(seg);
                }
            }
            break;
        }
    }
    _split_count[id] = count;
    return id;
}

int64_t _syn_texto_dividir_longitud(int64_t lista_id) {
    if (lista_id < 0 || lista_id >= SPLIT_MAX) return 0;
    return _split_count[lista_id];
}

CadenaSegura _syn_texto_dividir_obtener(int64_t lista_id, int64_t indice) {
    if (lista_id < 0 || lista_id >= SPLIT_MAX) return (CadenaSegura){0, ""};
    if (indice < 0 || indice >= _split_count[lista_id]) return (CadenaSegura){0, ""};
    char* s = _split_store[lista_id][indice];
    if (!s) return (CadenaSegura){0, ""};
    return (CadenaSegura){.longitud = (int)strlen(s), .datos = s};
}

void _syn_texto_dividir_liberar(int64_t lista_id) {
    _split_free(lista_id);
}

// ============================================================
// §12.1 — Unir (join)
// ============================================================

CadenaSegura _syn_texto_unir(int64_t lista_id, CadenaSegura separador) {
    if (lista_id < 0 || lista_id >= SPLIT_MAX) return (CadenaSegura){0, ""};
    int count = _split_count[lista_id];
    if (count == 0) return (CadenaSegura){0, ""};

    /* Calculate total length */
    int total = 0;
    for (int i = 0; i < count; i++) {
        char* s = _split_store[lista_id][i];
        if (s) total += (int)strlen(s);
    }
    if (count > 1) total += (count - 1) * separador.longitud;

    char* buf = (char*)malloc(total + 1);
    if (!buf) return (CadenaSegura){0, ""};

    int pos = 0;
    for (int i = 0; i < count; i++) {
        char* s = _split_store[lista_id][i];
        if (s) {
            int slen = (int)strlen(s);
            memcpy(buf + pos, s, slen);
            pos += slen;
        }
        if (i < count - 1 && separador.datos) {
            memcpy(buf + pos, separador.datos, separador.longitud);
            pos += separador.longitud;
        }
    }
    buf[pos] = '\0';
    return (CadenaSegura){.longitud = pos, .datos = buf};
}

// ============================================================
// §12.1 — Recortar (trim)
// ============================================================

CadenaSegura _syn_texto_recortar(CadenaSegura t) {
    if (t.datos == NULL || t.longitud == 0) return t;

    int start = 0;
    while (start < t.longitud && isspace((unsigned char)t.datos[start])) start++;

    int end = t.longitud - 1;
    while (end >= start && isspace((unsigned char)t.datos[end])) end--;

    int new_len = end - start + 1;
    if (new_len <= 0) return (CadenaSegura){0, ""};

    char* buf = (char*)malloc(new_len + 1);
    if (!buf) return (CadenaSegura){0, ""};
    memcpy(buf, t.datos + start, new_len);
    buf[new_len] = '\0';
    return (CadenaSegura){.longitud = new_len, .datos = buf};
}

// ============================================================
// §12.1 — Mayúsculas / Minúsculas
// ============================================================

CadenaSegura _syn_texto_mayusculas(CadenaSegura t) {
    if (t.datos == NULL || t.longitud == 0) return t;
    char* buf = (char*)malloc(t.longitud + 1);
    if (!buf) return (CadenaSegura){0, ""};
    for (int i = 0; i < t.longitud; i++) {
        buf[i] = (char)toupper((unsigned char)t.datos[i]);
    }
    buf[t.longitud] = '\0';
    return (CadenaSegura){.longitud = t.longitud, .datos = buf};
}

CadenaSegura _syn_texto_minusculas(CadenaSegura t) {
    if (t.datos == NULL || t.longitud == 0) return t;
    char* buf = (char*)malloc(t.longitud + 1);
    if (!buf) return (CadenaSegura){0, ""};
    for (int i = 0; i < t.longitud; i++) {
        buf[i] = (char)tolower((unsigned char)t.datos[i]);
    }
    buf[t.longitud] = '\0';
    return (CadenaSegura){.longitud = t.longitud, .datos = buf};
}

// ============================================================
// §12.1 — Comienza con / Termina con
// ============================================================

int _syn_texto_comienza_con(CadenaSegura t, CadenaSegura prefijo) {
    if (prefijo.datos == NULL || prefijo.longitud == 0) return 1;
    if (t.datos == NULL || t.longitud < prefijo.longitud) return 0;
    return memcmp(t.datos, prefijo.datos, prefijo.longitud) == 0;
}

int _syn_texto_termina_con(CadenaSegura t, CadenaSegura sufijo) {
    if (sufijo.datos == NULL || sufijo.longitud == 0) return 1;
    if (t.datos == NULL || t.longitud < sufijo.longitud) return 0;
    return memcmp(t.datos + t.longitud - sufijo.longitud, sufijo.datos, sufijo.longitud) == 0;
}

// ============================================================
// §12.1 — Índice de
// ============================================================

int64_t _syn_texto_indice_de(CadenaSegura t, CadenaSegura patron) {
    if (t.datos == NULL || patron.datos == NULL) return -1;
    if (patron.longitud == 0) return 0;
    if (patron.longitud > t.longitud) return -1;
    for (int i = 0; i <= t.longitud - patron.longitud; i++) {
        if (memcmp(t.datos + i, patron.datos, patron.longitud) == 0) return i;
    }
    return -1;
}

// ============================================================
// §12.1 — Repetir
// ============================================================

CadenaSegura _syn_texto_repetir(CadenaSegura t, int64_t veces) {
    if (t.datos == NULL || t.longitud == 0 || veces <= 0) return (CadenaSegura){0, ""};
    if (veces > 10000) veces = 10000; /* safety cap */
    int total = (int)(t.longitud * veces);
    char* buf = (char*)malloc(total + 1);
    if (!buf) return (CadenaSegura){0, ""};
    int pos = 0;
    for (int64_t i = 0; i < veces; i++) {
        memcpy(buf + pos, t.datos, t.longitud);
        pos += t.longitud;
    }
    buf[pos] = '\0';
    return (CadenaSegura){.longitud = pos, .datos = buf};
}

// ============================================================
// §12.1 — Invertir
// ============================================================

CadenaSegura _syn_texto_invertir(CadenaSegura t) {
    if (t.datos == NULL || t.longitud <= 1) return t;
    char* buf = (char*)malloc(t.longitud + 1);
    if (!buf) return (CadenaSegura){0, ""};
    for (int i = 0; i < t.longitud; i++) {
        buf[i] = t.datos[t.longitud - 1 - i];
    }
    buf[t.longitud] = '\0';
    return (CadenaSegura){.longitud = t.longitud, .datos = buf};
}
