#ifndef DETECT_HARDWARE_H
#define DETECT_HARDWARE_H

#include <stdint.h>

#define HW_MODEL_1B "Llama-3.2-1B-Instruct-Q4_K_M.gguf"
#define HW_MODEL_7B "Llama-3.2-7B-Instruct-Q4_K_M.gguf"
#define HW_MODEL_70B "Llama-3.2-70B-Instruct-Q4_K_M.gguf"
#define HW_MODEL_UNKNOWN "desconocido"

typedef enum {
    HW_TIER_INSUFICIENTE = 0,
    HW_TIER_1B = 1,
    HW_TIER_7B = 7,
    HW_TIER_70B = 70
} HwTier;

typedef struct {
    double total_ram_gb;
    double vram_gb;
    int cpu_logicos;
    int cpu_fisicos;
    HwTier tier;
    char modelo_sugerido[128];
    int ctx_size_sugerido;
    int threads_sugeridos;
    int ngl_sugerido;
} HwProfile;

int synapse_detectar_hardware(HwProfile* perfil);
void synapse_hw_sugerir_config(HwProfile* perfil);
void synapse_hw_imprimir_perfil(const HwProfile* perfil);
int synapse_hw_to_json(const HwProfile* perfil, char* buf, size_t cap);

#endif
