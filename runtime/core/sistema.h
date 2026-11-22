// cumple Manual 6 §1: sistema runtime
// cumple Manual 5 §1: cabecera sin estado mutable compartido entre hilos
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
// cumple Manual 7 §7.3 (H-CFG-2, r194): validador del sandbox de lecturas
// (relativa→cwd, normaliza, exige contención; evasión → CadenaSegura vacía).
CadenaSegura _syn_ruta_validar(CadenaSegura ruta);
// cumple Manual 7 §7.3 (ME r198b3_fmt_lint, H-R198b2-2): modo del sandbox
// (ESTRICTO=1 es el default de H-CFG-2; el dispatcher CLI del compilador —
// Manual 8 §4.1, cli_lint/cli_fmt/cli_check/cli_test— toma 0 para leer las
// rutas argv del usuario).
void _syn_sandbox_set(int64_t modo);
// cumple Manual 7 2.3 (R2): herramientas de lectura local del agente —
// listar directorio y capturar salida de comandos de solo-lectura.
CadenaSegura _syn_listar_directorio(CadenaSegura ruta);
CadenaSegura _syn_capturar_comando(CadenaSegura cmd);

#endif /* SYNAPSE_SISTEMA_H */

// cumple Manual 2 §1.2: encoding UTF-8 sin BOM verificado (ME r288).

// cumple Manual 5 §8.1: encoding UTF-8 sin BOM verificado (ME r288).
