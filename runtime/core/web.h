// cumple Manual 6 §2: web runtime
// runtime/core/web.h — HTTP server module declarations
// Manual 3 §12.1: lib/web.syq

#ifndef SYNAPSE_RT_WEB_H
#define SYNAPSE_RT_WEB_H

#include "synapse_rt_types.h"

// §12.1 — Crear / Destruir
int64_t _syn_web_crear(int64_t puerto);
void _syn_web_destruir(int64_t servidor);

// §12.1 — Registrar rutas
int64_t _syn_web_registrar_ruta(int64_t servidor, CadenaSegura metodo, CadenaSegura ruta, CadenaSegura contenido);
int64_t _syn_web_registrar_ruta_codigo(int64_t servidor, CadenaSegura metodo, CadenaSegura ruta, int64_t codigo, CadenaSegura contenido);

// §12.1 — Iniciar / Detener
int64_t _syn_web_iniciar(int64_t servidor);
void _syn_web_detener(int64_t servidor);
int _syn_web_esta_corriendo(int64_t servidor);

// §12.1 — Petición actual
CadenaSegura _syn_web_peticion_ruta(int64_t peticion);
CadenaSegura _syn_web_peticion_metodo(int64_t peticion);
CadenaSegura _syn_web_peticion_body(int64_t peticion);
CadenaSegura _syn_web_peticion_header(int64_t peticion, CadenaSegura nombre);

// §12.1 — Respuesta
void _syn_web_responder(int64_t peticion, int64_t codigo, CadenaSegura contenido);
void _syn_web_responder_texto(int64_t peticion, CadenaSegura contenido);
void _syn_web_responder_json(int64_t peticion, CadenaSegura contenido);
void _syn_web_responder_html(int64_t peticion, CadenaSegura contenido);
void _syn_web_responder_404(int64_t peticion);

#endif // SYNAPSE_RT_WEB_H
