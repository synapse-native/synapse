// cumple Manual 6 3: tiempo runtime
// runtime/core/tiempo.c — Time module for Syquex standard library
// Manual 3 §12.1: lib/tiempo.syq — Fechas y tiempos
// Compilar: gcc -c runtime/core/tiempo.c -o tiempo.o

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
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
    char* buf = (char*)malloc(11); /* YYYY-MM-DD\0 */
    if (!buf) return (CadenaSegura){0, ""};
    struct tm* t = _tiempo_local();
    if (!t) { free(buf); return (CadenaSegura){0, ""}; }
    int len = snprintf(buf, 11, "%04d-%02d-%02d",
                       t->tm_year + 1900, t->tm_mon + 1, t->tm_mday);
    return (CadenaSegura){.longitud = len, .datos = buf};
}

CadenaSegura _syn_tiempo_hora_actual(void) {
    char* buf = (char*)malloc(9); /* HH:MM:SS\0 */
    if (!buf) return (CadenaSegura){0, ""};
    struct tm* t = _tiempo_local();
    if (!t) { free(buf); return (CadenaSegura){0, ""}; }
    int len = snprintf(buf, 9, "%02d:%02d:%02d",
                       t->tm_hour, t->tm_min, t->tm_sec);
    return (CadenaSegura){.longitud = len, .datos = buf};
}

CadenaSegura _syn_tiempo_datetime_actual(void) {
    char* buf = (char*)malloc(20); /* YYYY-MM-DD HH:MM:SS\0 */
    if (!buf) return (CadenaSegura){0, ""};
    struct tm* t = _tiempo_local();
    if (!t) { free(buf); return (CadenaSegura){0, ""}; }
    int len = snprintf(buf, 20, "%04d-%02d-%02d %02d:%02d:%02d",
                       t->tm_year + 1900, t->tm_mon + 1, t->tm_mday,
                       t->tm_hour, t->tm_min, t->tm_sec);
    return (CadenaSegura){.longitud = len, .datos = buf};
}

// ============================================================
// §12.1 — Diferencia
// ============================================================

int64_t _syn_tiempo_diferencia_segundos(int64_t ts1, int64_t ts2) {
    return ts2 - ts1;
}
