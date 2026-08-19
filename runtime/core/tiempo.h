// runtime/core/tiempo.h — std.tiempo: Time & Profiling API
// D-9(d) corte 10: extraído de synapse_rt.c (texto byte-idéntico)
// Manual 5 §10 (ejemplo: importar std.tiempo / tiempo.dormir(100))
#ifndef SYNAPSE_TIEMPO_H
#define SYNAPSE_TIEMPO_H

#include <stdint.h>

int64_t _syn_ahora_ms(void);
void _syn_dormir_ms(int ms);

#endif /* SYNAPSE_TIEMPO_H */
