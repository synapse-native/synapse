// runtime/core/detect_hardware.h — Detección de hardware del sistema
// cumple Manual 9 5.7: std.os wrappers sobre funciones C del runtime
#ifndef DETECT_HARDWARE_H
#define DETECT_HARDWARE_H

#include <stdint.h>

// Retorna bytes de RAM total del sistema
int64_t _syn_memoria_total(void);

// Retorna bytes de RAM disponible
int64_t _syn_memoria_libre(void);

// Retorna bytes de VRAM total (0 si no detectable)
int64_t _syn_vram_total(void);

// Retorna número de cores lógicos de CPU
int64_t _syn_cpu_nucleos(void);

// Retorna nombre de la arquitectura CPU (ej: "x86_64", "ARM64")
// El puntero retornado es estático, no liberar.
const char* _syn_arquitectura(void);

#endif // DETECT_HARDWARE_H
