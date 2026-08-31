// runtime/core/detect_hardware.c — Detección de hardware del sistema
// Cumple Manual 9 §5.7: implementación de _syn_memoria_total, _syn_memoria_libre,
//   _syn_vram_total, _syn_cpu_nucleos, _syn_arquitectura

#include "detect_hardware.h"

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#else
#include <unistd.h>
#include <sys/sysinfo.h>
#include <string.h>
#endif

// Windows: GlobalMemoryStatusEx para RAM
// Linux: sysconf(_SC_PHYS_PAGES) * sysconf(_SC_PAGE_SIZE) para RAM
// Ambos: sysconf / GetSystemInfo para CPU cores

int64_t _syn_memoria_total(void) {
#ifdef _WIN32
    MEMORYSTATUSEX ms;
    ms.dwLength = sizeof(ms);
    if (GlobalMemoryStatusEx(&ms)) {
        return (int64_t)ms.ullTotalPhys;
    }
    return 0;
#else
    long pages = sysconf(_SC_PHYS_PAGES);
    long page_size = sysconf(_SC_PAGE_SIZE);
    if (pages > 0 && page_size > 0) {
        return (int64_t)pages * (int64_t)page_size;
    }
    return 0;
#endif
}

int64_t _syn_memoria_libre(void) {
#ifdef _WIN32
    MEMORYSTATUSEX ms;
    ms.dwLength = sizeof(ms);
    if (GlobalMemoryStatusEx(&ms)) {
        return (int64_t)ms.ullAvailPhys;
    }
    return 0;
#else
    // Linux: memoria disponible de /proc/meminfo via sysinfo
    struct sysinfo si;
    if (sysinfo(&si) == 0) {
        return (int64_t)si.freeram * (int64_t)si.mem_unit;
    }
    return 0;
#endif
}

int64_t _syn_vram_total(void) {
    // VRAM detection requires DXGI (DirectX) on Windows or /sys/class/drm on Linux.
    // Not reliably detectable without GPU-specific APIs. Return 0 as fallback.
    return 0;
}

int64_t _syn_cpu_nucleos(void) {
#ifdef _WIN32
    SYSTEM_INFO si;
    GetSystemInfo(&si);
    return (int64_t)si.dwNumberOfProcessors;
#else
    long n = sysconf(_SC_NPROCESSORS_ONLN);
    return (n > 0) ? (int64_t)n : 1;
#endif
}

const char* _syn_arquitectura(void) {
#ifdef _WIN32
    #ifdef _M_X64
        return "x86_64";
    #elif defined(_M_IX86)
        return "x86";
    #elif defined(_M_ARM64)
        return "ARM64";
    #else
        return "unknown";
    #endif
#else
    #if defined(__x86_64__) || defined(_M_X64)
        return "x86_64";
    #elif defined(__i386__)
        return "x86";
    #elif defined(__aarch64__)
        return "ARM64";
    #elif defined(__arm__)
        return "ARM";
    #else
        return "unknown";
    #endif
#endif
}
