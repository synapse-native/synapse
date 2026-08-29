#include "detect_hardware.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#define INITGUID  // cumple Manual 9 §5.7: define GUIDs de DXGI (MinGW los necesita)
#include <windows.h>
#include <dxgi.h>
#else
#include <unistd.h>
#include <sys/sysinfo.h>
#endif

#ifdef _WIN32
// cumple Manual 9 §5.7: VRAM total de la GPU en bytes (0 si no hay GPU).
// DXGI DedicatedVideoMemory es la fuente correcta; WinSAT GraphicsScore y
// GetDeviceCaps no reportan VRAM real (hallazgo A2 de R_AUDIT_DESV).
static int64_t _hw_vram_bytes_dxgi(void) {
    int64_t total = 0;
    HRESULT hr = CoInitializeEx(NULL, COINIT_MULTITHREADED);
    if (FAILED(hr) && hr != RPC_E_CHANGED_MODE) return 0;
    IDXGIFactory1* factory = NULL;
    if (SUCCEEDED(CreateDXGIFactory1(&IID_IDXGIFactory1, (void**)&factory)) && factory) {
        IDXGIAdapter* adapter = NULL;
        for (UINT i = 0; factory->lpVtbl->EnumAdapters(factory, i, &adapter) == S_OK; i++) {
            DXGI_ADAPTER_DESC desc;
            if (adapter->lpVtbl->GetDesc(adapter, &desc) == S_OK)
                total += (int64_t)desc.DedicatedVideoMemory;
            adapter->lpVtbl->Release(adapter);
        }
        factory->lpVtbl->Release(factory);
        CoUninitialize();
    }
    return total;
}
#endif

int synapse_detectar_hardware(HwProfile* perfil) {
    if (!perfil) return -1;
    memset(perfil, 0, sizeof(HwProfile));

#ifdef _WIN32
    MEMORYSTATUSEX mem = { .dwLength = sizeof(mem) };
    if (GlobalMemoryStatusEx(&mem)) {
        perfil->total_ram_gb = (double)mem.ullTotalPhys / (1024.0 * 1024.0 * 1024.0);
    }

    SYSTEM_INFO sys = {0};
    GetSystemInfo(&sys);
    perfil->cpu_logicos = (int)sys.dwNumberOfProcessors;

    DWORD sz = 0;
    GetLogicalProcessorInformation(NULL, &sz);
    if (GetLastError() == ERROR_INSUFFICIENT_BUFFER && sz > 0) {
        SYSTEM_LOGICAL_PROCESSOR_INFORMATION* buf = (SYSTEM_LOGICAL_PROCESSOR_INFORMATION*)malloc(sz);
        if (buf && GetLogicalProcessorInformation(buf, &sz)) {
            int n = (int)(sz / sizeof(SYSTEM_LOGICAL_PROCESSOR_INFORMATION));
            int cores = 0;
            for (int i = 0; i < n; i++) {
                if (buf[i].Relationship == RelationProcessorCore)
                    cores++;
            }
            perfil->cpu_fisicos = cores;
            free(buf);
        }
    }
    if (perfil->cpu_fisicos < 1) perfil->cpu_fisicos = perfil->cpu_logicos / 2;
    if (perfil->cpu_fisicos < 1) perfil->cpu_fisicos = 1;

    // cumple Manual 9 §5.7: VRAM via DXGI DedicatedVideoMemory
    // WinSAT GraphicsScore era un WEI score (1-9.9), NO VRAM en MB.
    // GetDeviceCaps(hdc,120) es indocumentado y devuelve 0.
    // DXGI provee DedicatedVideoMemory (bytes) del adaptador dedicado.
    IDXGIFactory1* factory = NULL;
    if (SUCCEEDED(CreateDXGIFactory1(&IID_IDXGIFactory1, (void**)&factory))) {
        IDXGIAdapter1* adapter = NULL;
        SIZE_T max_vram = 0;
        for (UINT i = 0; factory->lpVtbl->EnumAdapters1(factory, i, &adapter) == S_OK; i++) {
            DXGI_ADAPTER_DESC1 desc;
            if (SUCCEEDED(adapter->lpVtbl->GetDesc1(adapter, &desc))) {
                if (desc.DedicatedVideoMemory > max_vram)
                    max_vram = desc.DedicatedVideoMemory;
            }
            adapter->lpVtbl->Release(adapter);
        }
        factory->lpVtbl->Release(factory);
        if (max_vram > 0)
            perfil->vram_gb = (double)max_vram / (1024.0 * 1024.0 * 1024.0);
    }

#else
    struct sysinfo si;
    if (sysinfo(&si) == 0) {
        perfil->total_ram_gb = (double)si.totalram * si.mem_unit / (1024.0 * 1024.0 * 1024.0);
    }
    long cores = sysconf(_SC_NPROCESSORS_CONF);
    perfil->cpu_logicos = (cores > 0) ? (int)cores : 1;
    perfil->cpu_fisicos = (perfil->cpu_logicos + 1) / 2;
    if (perfil->cpu_fisicos < 1) perfil->cpu_fisicos = 1;

    FILE* f = fopen("/proc/mtrr", "r");
    if (!f) f = fopen("/proc/iomem", "r");
    if (f) {
        char line[256];
        while (fgets(line, sizeof(line), f)) {
            if (strstr(line, "VGA") || strstr(line, "vga")) {
                perfil->vram_gb = 0.5;
                break;
            }
        }
        fclose(f);
    }
    if (perfil->vram_gb < 0.1) {
        FILE* nv = popen("nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2> /dev/null", "r");
        if (nv) {
            char buf[64];
            if (fgets(buf, sizeof(buf), nv)) {
                int mb = atoi(buf);
                if (mb > 0) perfil->vram_gb = mb / 1024.0;
            }
            pclose(nv);
        }
    }
#endif

    if (perfil->cpu_fisicos < 1) perfil->cpu_fisicos = 1;
    if (perfil->cpu_logicos < 1) perfil->cpu_logicos = 1;
    if (perfil->total_ram_gb < 0.1) perfil->total_ram_gb = 4.0;

    synapse_hw_sugerir_config(perfil);
    return 0;
}

int64_t detect_vram_total(void) {
    // cumple Manual 9 §5.7 / ANEXO: VRAM total de la GPU en bytes (0 si no hay GPU).
#ifdef _WIN32
    return _hw_vram_bytes_dxgi();
#else
    FILE* nv = popen("nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null", "r");
    if (nv) {
        char buf[64];
        if (fgets(buf, sizeof(buf), nv)) {
            int mb = atoi(buf);
            pclose(nv);
            if (mb > 0) return (int64_t)mb * 1024 * 1024;
        } else {
            pclose(nv);
        }
    }
    return 0;
#endif
}

void synapse_hw_sugerir_config(HwProfile* perfil) {
    if (!perfil) return;

    if (perfil->total_ram_gb >= 64.0) {
        perfil->tier = HW_TIER_70B;
        strncpy(perfil->modelo_sugerido, HW_MODEL_70B, sizeof(perfil->modelo_sugerido) - 1);
        perfil->ctx_size_sugerido = 8192;
    } else if (perfil->total_ram_gb >= 32.0) {
        perfil->tier = HW_TIER_7B;
        strncpy(perfil->modelo_sugerido, HW_MODEL_7B, sizeof(perfil->modelo_sugerido) - 1);
        perfil->ctx_size_sugerido = 8192;
    } else if (perfil->total_ram_gb >= 8.0) {
        perfil->tier = HW_TIER_1B;
        strncpy(perfil->modelo_sugerido, HW_MODEL_1B, sizeof(perfil->modelo_sugerido) - 1);
        perfil->ctx_size_sugerido = 4096;
    } else {
        perfil->tier = HW_TIER_INSUFICIENTE;
        strncpy(perfil->modelo_sugerido, HW_MODEL_UNKNOWN, sizeof(perfil->modelo_sugerido) - 1);
        perfil->ctx_size_sugerido = 2048;
    }
    perfil->modelo_sugerido[sizeof(perfil->modelo_sugerido) - 1] = '\0';

    int cores = perfil->cpu_fisicos > 0 ? perfil->cpu_fisicos : 4;
    perfil->threads_sugeridos = cores > 2 ? cores - 1 : 1;

    if (perfil->vram_gb >= 6.0) {
        perfil->ngl_sugerido = 999;
    } else if (perfil->vram_gb >= 4.0) {
        perfil->ngl_sugerido = 20;
    } else if (perfil->vram_gb >= 2.0) {
        perfil->ngl_sugerido = 8;
    } else {
        perfil->ngl_sugerido = 0;
    }
}

void synapse_hw_imprimir_perfil(const HwProfile* perfil) {
    if (!perfil) return;
    printf("========================================\n");
    printf("  Synapse — Perfil de Hardware\n");
    printf("========================================\n");
    printf("  RAM total:       %.1f GB\n", perfil->total_ram_gb);
    printf("  VRAM detectada:  %.1f GB\n", perfil->vram_gb);
    printf("  CPUs lógicos:    %d\n", perfil->cpu_logicos);
    printf("  CPUs físicos:    %d\n", perfil->cpu_fisicos);
    printf("----------------------------------------\n");
    printf("  Tier:            ");
    switch (perfil->tier) {
        case HW_TIER_INSUFICIENTE: printf("INSUFICIENTE (< 8 GB)\n"); break;
        case HW_TIER_1B:           printf("1B (8–31 GB)\n"); break;
        case HW_TIER_7B:           printf("7B (32–63 GB)\n"); break;
        case HW_TIER_70B:          printf("70B (≥ 64 GB)\n"); break;
        default:                   printf("desconocido\n"); break;
    }
    printf("  Modelo sugerido:  %s\n", perfil->modelo_sugerido);
    printf("  ctx-size sugerido: %d\n", perfil->ctx_size_sugerido);
    printf("  threads sugeridos: %d\n", perfil->threads_sugeridos);
    if (perfil->ngl_sugerido > 0)
        printf("  ngl (GPU layers): %d\n", perfil->ngl_sugerido);
    else
        printf("  ngl (GPU layers): desactivado (sin VRAM suficiente)\n");
    printf("========================================\n");
}

int synapse_hw_to_json(const HwProfile* perfil, char* buf, size_t cap) {
    if (!perfil || !buf || cap < 256) return -1;
    const char* tier_str = "desconocido";
    switch (perfil->tier) {
        case HW_TIER_INSUFICIENTE: tier_str = "insuficiente"; break;
        case HW_TIER_1B:           tier_str = "1b"; break;
        case HW_TIER_7B:           tier_str = "7b"; break;
        case HW_TIER_70B:          tier_str = "70b"; break;
        default: break;
    }
    snprintf(buf, cap,
        "{"
        "\"ram_gb\":%.1f,"
        "\"vram_gb\":%.1f,"
        "\"cpu_logicos\":%d,"
        "\"cpu_fisicos\":%d,"
        "\"tier\":\"%s\","
        "\"modelo\":\"%s\","
        "\"ctx_size\":%d,"
        "\"threads\":%d,"
        "\"ngl\":%d"
        "}",
        perfil->total_ram_gb,
        perfil->vram_gb,
        perfil->cpu_logicos,
        perfil->cpu_fisicos,
        tier_str,
        perfil->modelo_sugerido,
        perfil->ctx_size_sugerido,
        perfil->threads_sugeridos,
        perfil->ngl_sugerido);
    return 0;
}

// Standalone CLI entry point — build separately as detect_hardware_cli.c
