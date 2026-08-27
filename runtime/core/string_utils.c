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

// ============================================================
// LSP Document storage (avoids Synapse RAII destruction)
// Manual 8 §1.4: didOpen/didChange store document text here;
// hover/completion/definition read from here across messages.
// ============================================================
static char _G_lsp_doc_buf[1048576];
static int _G_lsp_doc_len = 0;

void lsp_doc_store(CadenaSegura s) {
    int len = s.longitud;
    if (len > 1048575) len = 1048575;
    if (len < 0) len = 0;
    memcpy(_G_lsp_doc_buf, s.datos, len);
    _G_lsp_doc_buf[len] = '\0';
    _G_lsp_doc_len = len;
}

CadenaSegura lsp_doc_get(void) {
    // Return a malloc'd copy so Synapse RAII can safely free it
    // (previous: returned pointer to static buffer, RAII freed it -> heap corruption)
    if (_G_lsp_doc_len <= 0) return (CadenaSegura){0, ""};
    char* dup = (char*)malloc((size_t)(_G_lsp_doc_len + 1));
    if (!dup) return (CadenaSegura){0, ""};
    memcpy(dup, _G_lsp_doc_buf, (size_t)_G_lsp_doc_len);
    dup[_G_lsp_doc_len] = '\0';
    return (CadenaSegura){ .longitud = _G_lsp_doc_len, .datos = dup };
}

void lsp_doc_clear(void) {
    _G_lsp_doc_len = 0;
    _G_lsp_doc_buf[0] = '\0';
}

// ============================================================

// ============================================================

// ============================================================
// LSP: Extract function names from document as JSON array
// Avoids Synapse RAII use-after-free with var = var + pattern
// ============================================================
static char _result_buf_fn[4096];

CadenaSegura lsp_extract_doc_functions(void) {
    int pos = 0;
    int doc_len = _G_lsp_doc_len;
    const char* doc = _G_lsp_doc_buf;
    const char* patron = "funcion ";
    int patron_len = 8;
    int first = 1;

    pos += snprintf(_result_buf_fn + pos, sizeof(_result_buf_fn) - pos, "[");
    int search_pos = 0;
    while (search_pos < doc_len) {
        int found_offset = -1;
        int limit = doc_len - patron_len;
        if (limit < 0) break;
        for (int i = search_pos; i <= limit; i++) {
            if (memcmp(doc + i, patron, patron_len) == 0) {
                found_offset = i;
                break;
            }
        }
        if (found_offset < 0) break;
        int name_start = found_offset + patron_len;
        int name_end = name_start;
        while (name_end < doc_len) {
            char c = doc[name_end];
            if (c == '(' || c == ' ' || c == ':' || c == '\n') break;
            name_end++;
        }
        if (name_end > name_start) {
            int name_len = name_end - name_start;
            if (name_len > 200) name_len = 200;
            if (!first) {
                pos += snprintf(_result_buf_fn + pos, sizeof(_result_buf_fn) - pos, ",");
            }
            first = 0;
            pos += snprintf(_result_buf_fn + pos, sizeof(_result_buf_fn) - pos,
                "{\"label\":\"%.*s\",\"kind\":3,\"detail\":\"funcion\"}",
                name_len, doc + name_start);
        }
        search_pos = name_end + 1;
    }
    pos += snprintf(_result_buf_fn + pos, sizeof(_result_buf_fn) - pos, "]");

    char* dup = (char*)malloc((size_t)(pos + 1));
    if (!dup) return (CadenaSegura){0, ""};
    memcpy(dup, _result_buf_fn, (size_t)pos);
    dup[pos] = '\0';
    return (CadenaSegura){ .longitud = pos, .datos = dup };
}


// ============================================================
// LSP: Get enclosing function's return type for a variable
// Input: word = variable name
// Returns: malloc'd CadenaSegura with the return type (e.g. "entero"),
//          or empty CadenaSegura if not found.
// Avoids Synapse RAII: pure C, no Synapse string ops.
// ============================================================
static char _result_buf_ret[256];

CadenaSegura lsp_get_enclosing_return_type(CadenaSegura word) {
    int doc_len = _G_lsp_doc_len;
    const char* doc = _G_lsp_doc_buf;

    if (doc_len <= 0 || word.longitud <= 0) {
        return (CadenaSegura){0, ""};
    }

    // Step 1: Find the variable assignment in the document
    // Search for "word = " or "let word = "
    int var_pos = -1;

    // Try "let word = " first (more specific)
    if (word.longitud + 5 <= doc_len) {
        for (int i = 0; i <= doc_len - (word.longitud + 5); i++) {
            if (memcmp(doc + i, "let ", 4) == 0 &&
                memcmp(doc + i + 4, word.datos, word.longitud) == 0 &&
                doc[i + 4 + word.longitud] == ' ' &&
                doc[i + 4 + word.longitud + 1] == '=') {
                var_pos = i;
                break;
            }
        }
    }

    // If not found, try "word = " (without let)
    if (var_pos < 0 && word.longitud + 3 <= doc_len) {
        for (int i = 0; i <= doc_len - (word.longitud + 3); i++) {
            if (memcmp(doc + i, word.datos, word.longitud) == 0 &&
                doc[i + word.longitud] == ' ' &&
                doc[i + word.longitud + 1] == '=') {
                var_pos = i;
                break;
            }
        }
    }

    if (var_pos < 0) {
        return (CadenaSegura){0, ""};
    }

    // Step 2: Scan backwards from var_pos to find "funcion "
    int func_start = -1;
    const char* patron = "funcion ";
    int patron_len = 8;
    for (int i = var_pos - 1; i >= patron_len; i--) {
        if (memcmp(doc + i - patron_len + 1, patron, patron_len) == 0) {
            func_start = i - patron_len + 1;
            break;
        }
    }

    if (func_start < 0) {
        return (CadenaSegura){0, ""};
    }

    // Step 3: Find the line containing the function signature
    // Go back to the start of the line (previous newline or start of doc)
    int line_start = func_start;
    while (line_start > 0 && doc[line_start - 1] != '\n') {
        line_start--;
    }

    // Go forward to the end of the line
    int line_end = func_start;
    while (line_end < doc_len && doc[line_end] != '\n') {
        line_end++;
    }

    // Step 4: Find "-> " in the function signature line
    const char* arrow = "-> ";
    int arrow_len = 3;
    int arrow_pos = -1;
    for (int i = line_start; i <= line_end - arrow_len; i++) {
        if (memcmp(doc + i, arrow, arrow_len) == 0) {
            arrow_pos = i;
            break;
        }
    }

    if (arrow_pos < 0) {
        return (CadenaSegura){0, ""};
    }

    // Step 5: Extract the return type (after "-> " until ":" or end of line)
    int type_start = arrow_pos + arrow_len;
    int type_end = type_start;
    while (type_end < line_end && doc[type_end] != ':') {
        type_end++;
    }

    int type_len = type_end - type_start;
    if (type_len <= 0 || type_len > 200) {
        return (CadenaSegura){0, ""};
    }

    // Step 6: Return a malloc'd copy
    char* result = (char*)malloc((size_t)(type_len + 1));
    if (!result) return (CadenaSegura){0, ""};
    memcpy(result, doc + type_start, (size_t)type_len);
    result[type_len] = '\0';
    return (CadenaSegura){ .longitud = type_len, .datos = result };
}
