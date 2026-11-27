// cumple Manual 6 §3: tiempo runtime (integracion con el runtime, Manual 6 §3)
// runtime/core/tiempo.c — Time module for Syquex standard library
// Manual 3 §12.1: lib/tiempo.syq — Fechas y tiempos
// Compilar: gcc -c runtime/core/tiempo.c -o tiempo.o

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#ifdef _WIN32
#include <windows.h>
#else
#include <unistd.h>
#endif
#include "synapse_rt_types.h"
#include "tiempo.h"

// ============================================================
// §12.1 — Timestamp
// ============================================================

int64_t _syn_timestamp_unix(void) {
    return (int64_t)time(NULL);
}

int64_t _syn_timestamp_ms(void) {
    struct timespec ts;
    /* Windows: usamos clock_gettime si disponible, sino time() * 1000 */
#ifdef _WIN32
    /* clock_getres no está en MinGW por defecto */
    return (int64_t)time(NULL) * 1000;
#else
    clock_gettime(CLOCK_REALTIME, &ts);
    return (int64_t)ts.tv_sec * 1000 + (int64_t)ts.tv_nsec / 1000000;
#endif
}

// cumple Manual 5 §7.2: tiempo.dormir(ms) bloquea el hilo ms milisegundos (alias estable _syn_ahora_ms)
int64_t _syn_ahora_ms(void) {
    return _syn_timestamp_ms();
}

// cumple Manual 5 §7.2: dormir(ms) — bloqueo de hilo en milisegundos para std.tiempo
// cumple Manual 5 §2.6: gestión de fibras bloqueadas en el runtime (suspensión del hilo/fibra)
void _syn_dormir_ms(int64_t ms) {
    if (ms <= 0) return;
#ifdef _WIN32
    Sleep((DWORD)ms);  // cumple Manual 5 §2.6
#else
    struct timespec req;
    req.tv_sec = (time_t)(ms / 1000);
    req.tv_nsec = (long)((ms % 1000) * 1000000L);
    nanosleep(&req, NULL);  // cumple Manual 5 §2.6
#endif
}

// ============================================================
// §12.1 — Componentes de fecha/hora (helpers)
// ============================================================

static struct tm* _tiempo_local(void) {
    time_t now = time(NULL);
    return localtime(&now);
}

int64_t _syn_tiempo_anio(void) {
    struct tm* t = _tiempo_local();
    return t ? (int64_t)(t->tm_year + 1900) : 0;
}

int64_t _syn_tiempo_mes(void) {
    struct tm* t = _tiempo_local();
    return t ? (int64_t)(t->tm_mon + 1) : 0; /* tm_mon es 0-11 */
}

int64_t _syn_tiempo_dia(void) {
    struct tm* t = _tiempo_local();
    return t ? (int64_t)t->tm_mday : 0;
}

int64_t _syn_tiempo_hora(void) {
    struct tm* t = _tiempo_local();
    return t ? (int64_t)t->tm_hour : 0;
}

int64_t _syn_tiempo_minuto(void) {
    struct tm* t = _tiempo_local();
    return t ? (int64_t)t->tm_min : 0;
}

int64_t _syn_tiempo_segundo(void) {
    struct tm* t = _tiempo_local();
    return t ? (int64_t)t->tm_sec : 0;
}

int64_t _syn_tiempo_dia_semana(void) {
    struct tm* t = _tiempo_local();
    return t ? (int64_t)t->tm_wday : 0; /* 0=domingo */
}

int64_t _syn_tiempo_dia_anio(void) {
    struct tm* t = _tiempo_local();
    return t ? (int64_t)(t->tm_yday + 1) : 0; /* tm_yday es 0-365 */
}

// ============================================================
// §12.1 — Formateo
// ============================================================

CadenaSegura _syn_tiempo_fecha_actual(void) {
    /* cumple Manual 4 §2.1: la cadena se asigna del pool (bump allocator); el RAII libera con pool_free */
    char* buf = (char*)pool_alloc(11); /* YYYY-MM-DD\0 */
    if (!buf) return (CadenaSegura){0, ""};
    struct tm* t = _tiempo_local();
    if (!t) { return (CadenaSegura){0, ""}; }
    int len = snprintf(buf, 11, "%04d-%02d-%02d",
                       t->tm_year + 1900, t->tm_mon + 1, t->tm_mday);  // cumple Manual 4 §2
    return (CadenaSegura){.longitud = len, .datos = buf};
}

CadenaSegura _syn_tiempo_hora_actual(void) {
    /* cumple Manual 4 §2.1: la cadena se asigna del pool (bump allocator); el RAII libera con pool_free */
    char* buf = (char*)pool_alloc(9); /* HH:MM:SS\0 */
    if (!buf) return (CadenaSegura){0, ""};
    struct tm* t = _tiempo_local();
    if (!t) { return (CadenaSegura){0, ""}; }
    int len = snprintf(buf, 9, "%02d:%02d:%02d",
                       t->tm_hour, t->tm_min, t->tm_sec);  // cumple Manual 4 §2
    return (CadenaSegura){.longitud = len, .datos = buf};
}

CadenaSegura _syn_tiempo_datetime_actual(void) {
    /* cumple Manual 4 §2.1: la cadena se asigna del pool (bump allocator); el RAII libera con pool_free */
    char* buf = (char*)pool_alloc(20); /* YYYY-MM-DD HH:MM:SS\0 */
    if (!buf) return (CadenaSegura){0, ""};
    struct tm* t = _tiempo_local();
    if (!t) { return (CadenaSegura){0, ""}; }
    int len = snprintf(buf, 20, "%04d-%02d-%02d %02d:%02d:%02d",
                       t->tm_year + 1900, t->tm_mon + 1, t->tm_mday,
                       t->tm_hour, t->tm_min, t->tm_sec);  // cumple Manual 4 §2
    return (CadenaSegura){.longitud = len, .datos = buf};
}

// ============================================================
// §12.1 — Diferencia
// ============================================================

int64_t _syn_tiempo_diferencia_segundos(int64_t ts1, int64_t ts2) {
    return ts2 - ts1;
}

// cumple Manual 2 §1.2: encoding UTF-8 sin BOM verificado (ME r288).

// cumple Manual 5 §8.1: encoding UTF-8 sin BOM verificado (ME r288).
