// runtime/core/axon.h — Axon: HTTP download + TAR extraction + SHA-256 Lock
// D-9(d) corte 11: extraído de synapse_rt.c (modularización, patrón toml.c R64)
// Manual 6 §6.1 (path traversal protection en extracción TAR); regla 13 + canon D-9(d).
// Consumido por nucleo/principal.syn (asm blocks) y tests/*.c.
#ifndef SYNAPSE_AXON_H
#define SYNAPSE_AXON_H

#include "synapse_rt_types.h"

CadenaSegura _syn_sha256_hex(CadenaSegura datos);
CadenaSegura _syn_sha256_archivo(const char* ruta);
int _syn_http_get_archivo(CadenaSegura host, int puerto, CadenaSegura ruta, const char* salida_ruta);
int _syn_tar_extraer(const char* tar_ruta, const char* salida_dir);
int _syn_axon_verificar_lock(const char* paquete, const char* version, const char* archivo_ruta, const char* lock_ruta);
int _syn_axon_verificar_firma(const char* tar_ruta, const char* sig_ruta, const char* clave_publica_hex);
void _syn_axon_limpiar_toml(void* n);
int _syn_axon_buscar_local(const char* paquete, const char* version, char* tar_path, int tar_sz, char* extract_dir, int ext_sz);
int _syn_axon_escribir_lock(const char* paquete, const char* version, const char* hash_sha256);

#endif /* SYNAPSE_AXON_H */
