// runtime/core/string_utils.c — NEW string utilities for Synapse LSP
// Manual 8 §1.7: leer_bytes, escapar_json, a_texto_entero, a_texto_decimal
// Compilar: gcc -c runtime/core/string_utils.c -o string_utils.o

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "synapse_rt_types.h"

// ============================================================
// §1.7.1 — leer_bytes (lectura binaria de stdin)
// ============================================================

CadenaSegura _syn_leer_bytes(int64_t cantidad) {
    if (cantidad <= 0) return (CadenaSegura){0, ""};
    char* buf = (char*)malloc((size_t)(cantidad + 1));
    if (!buf) return (CadenaSegura){0, ""};

    int64_t leidos = 0;
    while (leidos < cantidad) {
        size_t n = fread(buf + leidos, 1, (size_t)(cantidad - leidos), stdin);
        if (n == 0) {
            free(buf);
            return (CadenaSegura){0, ""};
        }
        leidos += (int64_t)n;
    }
    buf[cantidad] = '\0';
    return (CadenaSegura){.longitud = (int)cantidad, .datos = buf};
}

// ============================================================
// §1.7.2 — escapar_json (escapado de strings JSON)
// ============================================================

CadenaSegura _syn_escapar_json(CadenaSegura t) {
    if (t.datos == NULL || t.longitud == 0) return t;

    int max_len = t.longitud * 6 + 1;
    char* buf = (char*)malloc(max_len);
    if (!buf) return (CadenaSegura){0, ""};

    int pos = 0;
    for (int i = 0; i < t.longitud; i++) {
        char c = t.datos[i];
        switch (c) {
            case '"':  buf[pos++] = '\\'; buf[pos++] = '"'; break;
            case '\\': buf[pos++] = '\\'; buf[pos++] = '\\'; break;
            case '\n': buf[pos++] = '\\'; buf[pos++] = 'n'; break;
            case '\r': buf[pos++] = '\\'; buf[pos++] = 'r'; break;
            case '\t': buf[pos++] = '\\'; buf[pos++] = 't'; break;
            default:
                if ((unsigned char)c < 0x20) {
                    pos += sprintf(buf + pos, "\\u%04x", (unsigned char)c);
                } else {
                    buf[pos++] = c;
                }
        }
    }
    buf[pos] = '\0';
    return (CadenaSegura){.longitud = pos, .datos = buf};
}

// ============================================================
// §1.7.2 — a_texto_entero (conversión entero a texto)
// ============================================================

CadenaSegura _syn_a_texto_entero(int64_t valor) {
    char buf[32];
    int len = snprintf(buf, sizeof(buf), "%lld", (long long)valor);
    char* dup = (char*)malloc(len + 1);
    if (!dup) return (CadenaSegura){0, ""};
    memcpy(dup, buf, len + 1);
    return (CadenaSegura){.longitud = len, .datos = dup};
}

CadenaSegura _syn_a_texto_decimal(double valor) {
    char buf[64];
    int len = snprintf(buf, sizeof(buf), "%g", valor);
    char* dup = (char*)malloc(len + 1);
    if (!dup) return (CadenaSegura){0, ""};
    memcpy(dup, buf, len + 1);
    return (CadenaSegura){.longitud = len, .datos = dup};
}

// ============================================================
// §1.7 — Funciones string de bajo nivel para LSP
// ============================================================

int64_t _syn_strcmp(CadenaSegura a, CadenaSegura b) {
    if (a.datos == NULL && b.datos == NULL) return 0;
    if (a.datos == NULL) return -1;
    if (b.datos == NULL) return 1;
    int min_len = a.longitud < b.longitud ? a.longitud : b.longitud;
    for (int i = 0; i < min_len; i++) {
        if ((unsigned char)a.datos[i] != (unsigned char)b.datos[i])
            return (unsigned char)a.datos[i] - (unsigned char)b.datos[i];
    }
    return a.longitud - b.longitud;
}

int64_t _syn_strlen(CadenaSegura a) {
    if (a.datos == NULL) return 0;
    return a.longitud;
}

int64_t _syn_strstr(CadenaSegura texto, CadenaSegura patron) {
    if (texto.datos == NULL || patron.datos == NULL) return -1;
    if (patron.longitud == 0) return 0;
    if (patron.longitud > texto.longitud) return -1;
    for (int i = 0; i <= texto.longitud - patron.longitud; i++) {
        if (memcmp(texto.datos + i, patron.datos, patron.longitud) == 0)
            return i;
    }
    return -1;
}

int64_t _syn_strchr(CadenaSegura texto, int64_t caracter) {
    if (texto.datos == NULL) return -1;
    char c = (char)caracter;
    for (int i = 0; i < texto.longitud; i++) {
        if (texto.datos[i] == c) return i;
    }
    return -1;
}

int64_t _syn_atoi(CadenaSegura texto) {
    if (texto.datos == NULL || texto.longitud == 0) return 0;
    char buf[64];
    int len = texto.longitud < 63 ? texto.longitud : 63;
    memcpy(buf, texto.datos, len);
    buf[len] = '\0';
    return (int64_t)atoi(buf);
}

CadenaSegura _syn_strcpy(CadenaSegura texto) {
    if (texto.datos == NULL || texto.longitud == 0) return (CadenaSegura){0, ""};
    char* dup = (char*)malloc(texto.longitud + 1);
    if (!dup) return (CadenaSegura){0, ""};
    memcpy(dup, texto.datos, texto.longitud);
    dup[texto.longitud] = '\0';
    return (CadenaSegura){.longitud = texto.longitud, .datos = dup};
}

CadenaSegura _syn_strncpy(CadenaSegura texto, int64_t max_len) {
    if (texto.datos == NULL || texto.longitud == 0) return (CadenaSegura){0, ""};
    int len = texto.longitud < (int)max_len ? texto.longitud : (int)max_len;
    char* dup = (char*)malloc(len + 1);
    if (!dup) return (CadenaSegura){0, ""};
    memcpy(dup, texto.datos, len);
    dup[len] = '\0';
    return (CadenaSegura){.longitud = len, .datos = dup};
}
