// cumple Manual 6 §1: sistema runtime
// runtime/core/sistema.h — std.sistema: helpers de ruta/string
// D-9(d) corte 11: extraído de synapse_rt.c (modularización, patrón toml.c R64)
// Path traversal protection (regla 13 + canon D-9(d)); consumido por
// std/sistema.syn, nucleo/lexer_keywords.syn (str_eq) y
// nucleo/principal.syn (verificación de rutas).
#ifndef SYNAPSE_SISTEMA_H
#define SYNAPSE_SISTEMA_H

#include "synapse_rt_types.h"

int64_t str_eq(CadenaSegura a, CadenaSegura b);
CadenaSegura concat(CadenaSegura a, CadenaSegura b);
CadenaSegura _syn_normalizar_ruta(CadenaSegura ruta);
CadenaSegura _syn_obtener_cwd(void);
int _syn_ruta_en_directorio(CadenaSegura ruta, CadenaSegura dir);
// cumple Manual 7 2.3 (R2): herramientas de lectura local del agente —
// listar directorio y capturar salida de comandos de solo-lectura.
CadenaSegura _syn_listar_directorio(CadenaSegura ruta);
CadenaSegura _syn_capturar_comando(CadenaSegura cmd);

#endif /* SYNAPSE_SISTEMA_H */
