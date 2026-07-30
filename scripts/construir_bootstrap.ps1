# Build script for synapse_bootstrap.exe — Fase 12.5: Unity Build
$ErrorActionPreference = "Stop"
$root = "D:\proyecto_synapse"
Push-Location $root

Write-Host "[GEN] Unity Build (nucleo/principal.syn)"
try { $null = python main.py "nucleo/principal.syn" 2>&1 } catch {}
if (!(Test-Path "synapse_unity.c")) { Write-Error "Failed to generate synapse_unity.c"; exit 1 }

Write-Host "[COMPILE] synapse_rt.o"
gcc -c -O2 synapse_rt.c -o synapse_rt.o

Write-Host "[COMPILE] synapse_bootstrap.exe"
$link = "gcc -O2 synapse_unity.c synapse_rt.o -o synapse_bootstrap.exe -lpthread -lm -lws2_32 2>&1"
$output = Invoke-Expression $link
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] synapse_bootstrap.exe generado"
} else {
    Write-Error "Link failed: $output"
    exit 1
}

Pop-Location

