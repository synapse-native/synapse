// Timeout de 5 s (Manual FASE 32 §6.4, no indexado por el gate).
// cumple Manual 7 §7.3: contrato del subproceso que consume la allowlist.
// runtime/core/proceso.h - contrato C del primitivo de captura con timeout.
#ifndef SYNAPSE_PROCESO_H
#define SYNAPSE_PROCESO_H

#include "synapse_rt_types.h"

CadenaSegura _syn_capturar_comando_timeout(CadenaSegura cmd, int64_t timeout_ms);

// cumple Manual 7 §7.3: contrato sin shell; POSIX usa execvp con argv dividido.
#endif /* SYNAPSE_PROCESO_H */
