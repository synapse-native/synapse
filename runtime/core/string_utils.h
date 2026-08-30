// runtime/core/string_utils.h — NEW string utility declarations
// Manual 8 §1.7: leer_bytes, escapar_json, a_texto

#ifndef SYNAPSE_RT_STRING_UTILS_H
#define SYNAPSE_RT_STRING_UTILS_H

#include "synapse_rt_types.h"

// §1.7.1 — Leer bytes (lectura binaria de stdin)
CadenaSegura _syn_leer_bytes(int64_t cantidad);

// §1.7.2 — Escapar JSON
CadenaSegura _syn_escapar_json(CadenaSegura t);

// §1.7.2 — Conversión entero/decimal a texto
CadenaSegura _syn_a_texto_entero(int64_t valor);
CadenaSegura _syn_a_texto_decimal(double valor);

// §1.7 — Funciones string de bajo nivel para LSP
int64_t _syn_strcmp(CadenaSegura a, CadenaSegura b);
int64_t _syn_strlen(CadenaSegura a);
int64_t _syn_strstr(CadenaSegura texto, CadenaSegura patron);
int64_t _syn_strchr(CadenaSegura texto, int64_t caracter);
int64_t _syn_atoi(CadenaSegura texto);
CadenaSegura _syn_strcpy(CadenaSegura texto);
CadenaSegura _syn_strncpy(CadenaSegura texto, int64_t max_len);

#endif // SYNAPSE_RT_STRING_UTILS_H
