# install.ps1 — Provisioning MinGW Toolchain (Manual 9 §2.5)
# cumple Manual 9 §2.5: post-install hook para MinGW
# Invocado por synapse.iss [Run] como: powershell -ExecutionPolicy Bypass -File "{app}\install.ps1"
$ErrorActionPreference = "SilentlyContinue"
Write-Host "[Synapse] Provisionando MinGW Toolchain..."
# Verificar si gcc existe
try {
    $gcc = Get-Command gcc -ErrorAction SilentlyContinue
    if ($gcc) {
        Write-Host "[Synapse] gcc encontrado: $($gcc.Source) $($gcc.Version)"
        exit 0
    }
    Write-Host "[Synapse] gcc no encontrado en PATH — usuario debe instalar MinGW manualmente (https://www.mingw-w64.org/downloads/)"
    Write-Host "[Synapse] Alternativa: winget install --id=MSYS2.MSYS2"
} catch {
    Write-Host "[Synapse] Aviso: no se pudo verificar gcc: $_"
}
exit 0
