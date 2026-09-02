// cumple Manual 6 2: HTTP runtime
// runtime/core/http.h — std.http: HTTP Server API (minimalista, síncrono)
// D-9(d) corte 10: extraído de synapse_rt.c (texto byte-idéntico)
// Manual 5 §6 (std.net, primitivas de socket sobre las que monta el servidor)
#ifndef SYNAPSE_HTTP_H
#define SYNAPSE_HTTP_H

#include "synapse_rt_types.h"

int _syn_servidor_escuchar(int puerto);
int _syn_servidor_aceptar(int fd_servidor);
CadenaSegura _syn_http_leer_peticion(int fd_cliente);
int _syn_http_enviar_respuesta(int fd_cliente, CadenaSegura respuesta);
void _syn_http_cerrar_cliente(int fd_cliente);
CadenaSegura _syn_http_respuesta_ok(int codigo, const char* tipo, const char* cuerpo, int lon);

#endif /* SYNAPSE_HTTP_H */
