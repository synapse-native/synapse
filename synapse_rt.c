// cumple Manual 1 §5: runtime principal Synapse
// cumple Manual 8 §4.1: compilador nativo S2
// synapse_rt.c — Synapse runtime (modular: types, memory, concurrency)
// Compilar: gcc -c synapse_rt.c -o synapse_rt.o
// Linkear con: synapse_rt_memory.o synapse_rt_concurrency.o

#include "synapse_rt_types.h"
#include "runtime/core/tensor.h"  // D-9(d): std.math/std.tensor/std.simd extraidos a tensor.c
#include "runtime/core/cluster.h"  // D-9(d): std.cluster (M8.1-M8.6) extraido a cluster.c
#include "runtime/core/debug.h"  // D-9(d): debug (M9.0-M9.4) extraido a debug.c
#include "runtime/core/network.h"  // D-9(d): std.net (networking) extraido a network.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include <pthread.h>
#include <time.h>
#include "librerias/embedded_libs.h"
#include "axon/tweetnacl.h"

#ifdef _WIN32
  #include <winsock2.h>
  #include <ws2tcpip.h>
  #include <windows.h>
  #include <direct.h>
  #include <wincrypt.h>
#else
  #include <sys/socket.h>
  #include <netinet/in.h>
  #include <arpa/inet.h>
  #include <unistd.h>
  #include <sys/mman.h>
  #include <sys/stat.h>
  #include <fcntl.h>
#endif
// -----------------------------------------------------------
// (Canal abrir/leer/cerrar + librerias virtuales movidos a runtime/core/io.c en F3-2;
//  externs _syn_abrir/_syn_leer/_syn_escribir/_syn_escribir_linea/_syn_leer_linea
//  definidos alli tambien — std/io.syn ya enlaza)
// (std.net movido a runtime/core/network.c en D-9(d) corte 6)
// (std.json movido a runtime/core/json.c en D-9(d) corte 7)

#include "runtime/core/json.h"  // D-9(d) corte 7: std.json extraido a json.c
#include "runtime/core/cripto.h"  // D-9(d) corte 8: std.cripto extraido a cripto.c
#include "runtime/core/toml.h"  // D-9(d) corte 9: std.toml extraido a toml.c
#include "runtime/core/tiempo.h"  // D-9(d) corte 10: std.tiempo extraido a tiempo.c
#include "runtime/core/http.h"  // D-9(d) corte 10: std.http extraido a http.c

// --- std.conv ---

int64_t texto_a_entero(CadenaSegura str) {
    if (str.datos == NULL || str.longitud == 0) return 0;
    return (int64_t)strtoll(str.datos, NULL, 10);
}

double texto_a_decimal(CadenaSegura str) {
    if (str.datos == NULL || str.longitud == 0) return 0.0;
    return strtod(str.datos, NULL);
}

CadenaSegura decimal_a_texto(double n) {
    char buf[64];
    int len = snprintf(buf, sizeof(buf), "%f", n);
    char* data = (char*)malloc(len + 1);
    if (!data) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en decimal_a_texto\n"); exit(1); }
    memcpy(data, buf, len + 1);
    return (CadenaSegura){ .longitud = len, .datos = data };
}

// A5.1 (D-7): entero -> int64_t (Manual 2 S4.1 L267-268). Ensayo de runtime:
// %lld con cast (long long) para portabilidad; salida identica para valores
// pequenos, sin truncar en rangos 32->64 bits. Los mapeos se migran en A5.2.
CadenaSegura entero_a_texto(int64_t n) {
    char buf[64];
    int len = snprintf(buf, sizeof(buf), "%lld", (long long)n);
    char* data = (char*)malloc(len + 1);
    if (!data) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en entero_a_texto\n"); exit(1); }
    memcpy(data, buf, len + 1);
    return (CadenaSegura){ .longitud = len, .datos = data };
}
// ============================================================
// std.toml — TOML Parser (Subset para Axon) extraido a
// runtime/core/toml.c (D-9(d) corte 9, patron json.c R42).
// ============================================================

// ============================================================
// D-9(d) — Modularización de synapse_rt.c (regla 13, canon D-9(d)):
//   cada bloque extraído a runtime/core/<modulo>.c + <modulo>.h (auto-link).
//   cortes 1-6: io, tensor, modelo, cluster, debug, fuzz, network.
//   cortes 7-10: json, cripto, toml, tiempo, http.
//   corte 11: axon (HTTP/TAR/SHA-256 lock/Ed25519), cache (nucleo/cache.syn),
//             std.sistema (path helpers).
// El monolito queda reducido a tipos + std.conv (ver includes al inicio).
// ============================================================

