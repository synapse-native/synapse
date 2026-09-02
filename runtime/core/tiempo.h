// cumple Manual 6 §3: tiempo runtime
// runtime/core/tiempo.h — Time module declarations for Syquex standard library
// Manual 3 §12.1: lib/tiempo.syq

#ifndef SYNAPSE_RT_TIEMPO_H
#define SYNAPSE_RT_TIEMPO_H

#include <stdint.h>

// §12.1 — Timestamp
int64_t _syn_timestamp_unix(void);
int64_t _syn_timestamp_ms(void);

// §12.1 — Componentes de fecha
int64_t _syn_tiempo_anio(void);
int64_t _syn_tiempo_mes(void);
int64_t _syn_tiempo_dia(void);

// §12.1 — Componentes de hora
int64_t _syn_tiempo_hora(void);
int64_t _syn_tiempo_minuto(void);
int64_t _syn_tiempo_segundo(void);

// §12.1 — Día de la semana (0=domingo, 6=sábado)
int64_t _syn_tiempo_dia_semana(void);

// §12.1 — Día del año
int64_t _syn_tiempo_dia_anio(void);

// §12.1 — Formateo (retorna CadenaSegura)
CadenaSegura _syn_tiempo_fecha_actual(void);
CadenaSegura _syn_tiempo_hora_actual(void);
CadenaSegura _syn_tiempo_datetime_actual(void);

// §12.1 — Diferencia
int64_t _syn_tiempo_diferencia_segundos(int64_t ts1, int64_t ts2);

#endif // SYNAPSE_RT_TIEMPO_H
