// cumple Manual 6 3: texto runtime
// runtime/core/texto.h — Text module declarations for Syquex standard library
// Manual 3 §12.1: lib/texto.syq

#ifndef SYNAPSE_RT_TEXTO_H
#define SYNAPSE_RT_TEXTO_H

#include "synapse_rt_types.h"

// §12.1 — Longitud
int64_t _syn_texto_longitud(CadenaSegura t);

// §12.1 — Subcadena
CadenaSegura _syn_texto_subcadena(CadenaSegura t, int64_t inicio, int64_t fin);

// §12.1 — Contiene
int _syn_texto_contiene(CadenaSegura t, CadenaSegura patron);

// §12.1 — Reemplazar
CadenaSegura _syn_texto_reemplazar(CadenaSegura t, CadenaSegura viejo, CadenaSegura nuevo);

// §12.1 — Dividir (split) — retorna ID de lista interna
int64_t _syn_texto_dividir(CadenaSegura t, CadenaSegura separador);
int64_t _syn_texto_dividir_longitud(int64_t lista_id);
CadenaSegura _syn_texto_dividir_obtener(int64_t lista_id, int64_t indice);
void _syn_texto_dividir_liberar(int64_t lista_id);

// §12.1 — Unir (join)
CadenaSegura _syn_texto_unir(int64_t lista_id, CadenaSegura separador);

// §12.1 — Recortar (trim)
CadenaSegura _syn_texto_recortar(CadenaSegura t);

// §12.1 — Mayúsculas / Minúsculas
CadenaSegura _syn_texto_mayusculas(CadenaSegura t);
CadenaSegura _syn_texto_minusculas(CadenaSegura t);

// §12.1 — Comienza con / Termina con
int _syn_texto_comienza_con(CadenaSegura t, CadenaSegura prefijo);
int _syn_texto_termina_con(CadenaSegura t, CadenaSegura sufijo);

// §12.1 — Índice de
int64_t _syn_texto_indice_de(CadenaSegura t, CadenaSegura patron);

// §12.1 — Repetir
CadenaSegura _syn_texto_repetir(CadenaSegura t, int64_t veces);

// §12.1 — Invertir
CadenaSegura _syn_texto_invertir(CadenaSegura t);

#endif // SYNAPSE_RT_TEXTO_H
