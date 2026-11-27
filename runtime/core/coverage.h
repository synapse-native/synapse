// runtime/core/coverage.h — Instrumentación de aristas (ME coverage_aristas, Fase 33.2)
// cumple Manual 9 §6.1: synapse test --coverage genera informes de cobertura.
// cumple Manual 5 §2.6: memoria del runtime sin GC — el buffer de aristas es
// estático (sin malloc/free propio), patrón trazas del debug; cumple Manual 1 §6: OFF.
// API mínima consumida por los probes SYN_COV(l,d) del emisor (S1 Python y
// nativo) y por nucleo/coverage.syn (informe HTML desde el JSON volcado).
#ifndef SYNAPSE_COVERAGE_H
#define SYNAPSE_COVERAGE_H

#include <stdint.h>

/* Registra la arista (l -> d) del archivo fuente activo. ON si la variable
 * de entorno SYNAPSE_COVERAGE=1 fue leída por el constructor del módulo
 * (registrado atexit para volcar <SYNAPSE_COVERAGE_OUT>.coverage.json).
 * Sin gestión de memoria: las etiquetas viajan como punteros internados. */
void _syn_cov(int64_t l, int64_t d);

/* Activa el registro en programas sin constructor (rutas embebidas). */
void _syn_cov_habilitar(void);

/* Vuelca el JSON de aristas a la ruta configurada (idempotente). */
void _syn_cov_volcar(void);

/* Configura ruta de salida y nombre de archivo fuente (desde el emisor). */
void _syn_cov_configurar(const char* archivo_fuente, const char* ruta_salida);

/* Catálogo estático de ramas emitido por el compilador: "l:d,l:d,..."
 * (l = clave de rama, d = rama padre). Alimenta las aristas NO ejecutadas. */
void _syn_cov_ramas_estaticas(const char* pares);

/* Total de ramas estáticas instrumentadas (declaración temprana; el detalle
 * llega por _syn_cov_ramas_estaticas). */
void _syn_cov_total(int total);

#endif /* SYNAPSE_COVERAGE_H */
