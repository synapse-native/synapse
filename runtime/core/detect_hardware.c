// runtime/core/detect_hardware.c — Detección de hardware del sistema
// cumple Manual 9 5.7: implementación de _syn_memoria_total, _syn_memoria_libre,
//   _syn_vram_total, _syn_cpu_nucleos, _syn_arquitectura

#include "detect_hardware.h"

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#else
#include <unistd.h>
#include <string.h>
// cumple Manual 9 §5.7: deteccion de hardware via runtime (FFI).
// cumple Manual 9 §6.2 (r317): sys/sysinfo.h es solo de Linux; macOS no lo
// tiene y el bootstrap de la matriz fallaba al compilar este archivo.
#if defined(__linux__)
#include <sys/sysinfo.h>
#elif defined(__APPLE__)
// cumple Manual 9 §6.2 (r318): macOS no expone memoria disponible por sysconf;
// se consulta el VM del kernel por mach (misma llamada al SO, via FFI).
#include <mach/mach.h>
#endif
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
#elif defined(__linux__)
    // Linux: memoria disponible de /proc/meminfo via sysinfo
    struct sysinfo si;
    if (sysinfo(&si) == 0) {
        return (int64_t)si.freeram * (int64_t)si.mem_unit;
    }
    return 0;
#elif defined(__APPLE__)
    // cumple Manual 9 §6.2 (r319): la consulta sysconf de memoria disponible
    // es Linux-only; macOS da libre+inactiva+especulativa por host_statistics64
    // (constantes mach HOST_VM_INFO64 / HOST_VM_INFO64_COUNT de mach/host_info.h).
    mach_port_t host = mach_host_self();
    vm_size_t page_size = 0;
    vm_statistics64_data_t vms;
    mach_msg_type_number_t count = HOST_VM_INFO64_COUNT;
    if (host_page_size(host, &page_size) == KERN_SUCCESS &&
        host_statistics64(host, HOST_VM_INFO64, (host_info64_t)&vms, &count) == KERN_SUCCESS) {
        return ((int64_t)vms.free_count + (int64_t)vms.inactive_count +
                (int64_t)vms.speculative_count) * (int64_t)page_size;
    }
    return 0;
#else
    // cumple Manual 9 §6.2 (r317): POSIX sin API de memoria disponible; 0
    // (no inventar dato).
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
