// runtime/core/tiempo.c — std.tiempo: Time & Profiling
// D-9(d) corte 10: extraído de synapse_rt.c (modularización, patrón toml.c R64)
// Texto byte-idéntico al original (CRLF preservado).
//
// Manual 5 §10 (std.tiempo: ahora_ms/dormir_ms); regla 13 (modularización)
// + canon D-9(d).

#include "synapse_rt_types.h"
#include "runtime/core/tiempo.h"

#ifdef _WIN32
  #include <windows.h>
#else
  #include <time.h>
#endif

// ============================================================
// std.tiempo — Time & Profiling
// ============================================================

int64_t _syn_ahora_ms(void) {
#ifdef _WIN32
    FILETIME ft;
    GetSystemTimeAsFileTime(&ft);
    uint64_t t = ((uint64_t)ft.dwHighDateTime << 32) | ft.dwLowDateTime;
    // Convert from 100-ns intervals since 1601-01-01 to ms since 1970-01-01
    return (int64_t)((t - 116444736000000000ULL) / 10000);
#else
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    return (int64_t)ts.tv_sec * 1000 + (int64_t)ts.tv_nsec / 1000000;
#endif
}

void _syn_dormir_ms(int ms) {
#ifdef _WIN32
    Sleep((DWORD)ms);
#else
    struct timespec ts;
    ts.tv_sec = ms / 1000;
    ts.tv_nsec = (long)(ms % 1000) * 1000000L;
    nanosleep(&ts, NULL);
#endif
}
