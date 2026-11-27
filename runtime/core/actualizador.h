// cumple Manual 9 §3.1: API nativa del comando `synapse update`
// cumple Manual 9 §3.2: pipeline de verificación, backup e instalación
#ifndef ACTUALIZADOR_H
#define ACTUALIZADOR_H

#include <stdint.h>
#include "synapse_rt_types.h"

// Nombre del asset publicado por release_matrix para esta plataforma.
CadenaSegura _syn_actualizador_asset(void);

// Clave pública Ed25519 canónica (hex de 64) publicada por distribuir.py.
CadenaSegura _syn_actualizador_pubkey(void);

// Ruta absoluta del ejecutable en curso.
CadenaSegura _syn_actualizador_exe(void);

// Verifica la firma hex (128 caracteres) del artefacto con la clave hex (64).
// Retorna 0 si es válida; -1 si falta, es ilegible o no coincide.
int64_t _syn_actualizador_verificar_firma(CadenaSegura artefacto,
                                          CadenaSegura firma_hex,
                                          CadenaSegura clave_hex);

// Copia el ejecutable actual a <destino_dir>/<nombre>.bak.
// Retorna la ruta del backup (vacía si falla).
CadenaSegura _syn_actualizador_backup(CadenaSegura destino_dir);

// Instala el artefacto ya verificado. Si es un instalador setup/installer lo
// ejecuta en silencio; si es el binario, lo reemplaza tras cerrar el proceso.
// Retorna 0 si la instalación quedó lanzada/aplicada; -1 si falló.
int64_t _syn_actualizador_instalar(CadenaSegura nuevo, CadenaSegura destino);

// Ejecuta un comando externo (curl) preservando las comillas en Windows.
// Retorna el código de salida del proceso; -1 si no se pudo ejecutar.
int64_t _syn_actualizador_ejecutar(CadenaSegura cmd);

// Compara dos versiones semánticas (major.minor.patch). Retorna -1, 0 o 1.
// No libera las cadenas recibidas (el llamador conserva su ownership).
int64_t _syn_actualizador_comparar_versiones(CadenaSegura a, CadenaSegura b);

// Componente mayor de una versión semántica (0 si no se puede leer).
int64_t _syn_actualizador_version_mayor(CadenaSegura v);

#endif /* ACTUALIZADOR_H */
