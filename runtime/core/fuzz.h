// cumple Manual 6 9: fuzzing
// runtime/core/fuzz.h — Public API of runtime/core/fuzz.c
// Extraido de synapse_rt.c (deuda D-9(d), corte 6 tras debug.c R41).
// Fuzzing Distribuido Multi-Nodo (M10.4): coordinador/agentes, envio de
// casos, procesamiento de paquetes SYNFUZZ, reporte de resultados.
// Consumido por std.cluster (externs fz_*, link-time) y tests de fuzzing.
#ifndef SYNAPSE_RT_FUZZ_H
#define SYNAPSE_RT_FUZZ_H

#include "synapse_rt_types.h"

#ifdef __cplusplus
extern "C" {
#endif

// --- API publica (11 funciones, texto byte-identico al original) ---
int fz_iniciar_coordinador(int puerto);
int fz_enviar_caso(CadenaSegura ip, int puerto, int caso_id, CadenaSegura contenido);
CadenaSegura fz_procesar_mensaje(CadenaSegura paquete);
int fz_reportar_resultado(CadenaSegura ip_coord, int puerto_coord,
                          int caso_id, int exit_code, CadenaSegura stderr_resumen);
CadenaSegura fz_obtener_resultado(int indice);
int fz_ultimo_caso_id(void);
int fz_total_casos_enviados(void);
int fz_total_resultados_recibidos(void);
int fz_total_crashes(void);
int fz_num_resultados(void);
CadenaSegura fz_info(void);

#ifdef __cplusplus
}
#endif

#endif /* SYNAPSE_RT_FUZZ_H */
