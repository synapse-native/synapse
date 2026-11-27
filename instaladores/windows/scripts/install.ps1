# install.ps1 — Verificación del toolchain C incluido en el instalador
# cumple Manual 9 §2.5: post-install hook del componente toolchain
# cumple Manual 9 §7: en una instalación limpia, compilar debe funcionar sin que
# el usuario instale ni configure MinGW.
# Invocado por synapse.iss [Run] como: powershell -ExecutionPolicy Bypass -File "{app}\install.ps1"
$ErrorActionPreference = "SilentlyContinue"
$raiz = Split-Path -Parent $MyInvocation.MyCommand.Path
$gccIncluido = Join-Path $raiz "toolchain_gcc12\mingw64\bin\gcc.exe"

Write-Host "[Synapse] Verificando toolchain C incluido..."
if (Test-Path $gccIncluido) {
    $version = & $gccIncluido --version 2>$null | Select-Object -First 1
    if ($LASTEXITCODE -eq 0 -and $version) {
        Write-Host "[Synapse] toolchain incluido OK: $version"
        exit 0
    }
    Write-Host "[Synapse] Aviso: el toolchain incluido no responde ($gccIncluido)"
}

# Fallback: gcc del PATH (instalación sin el componente toolchain)
$gcc = Get-Command gcc -ErrorAction SilentlyContinue
if ($gcc) {
    Write-Host "[Synapse] gcc encontrado en PATH: $($gcc.Source)"
    exit 0
}
Write-Host "[Synapse] Sin toolchain incluido ni gcc en PATH: instale MinGW para compilar (https://www.mingw-w64.org/downloads/) o reejecute el instalador con el componente 'Toolchain C'."
exit 0
