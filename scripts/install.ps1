# =========================================================================
# install.ps1 — Script de provisionamiento MinGW Toolchain para Windows
# =========================================================================
# cumple Manual 9 §2.5: Configuración de Inno Setup (Windows)
# Provisiona MSYS2 + MinGW-w64 para compilar el runtime Synapse en Windows.
# =========================================================================

param(
    [string]$MingwRoot = "${env:ProgramFiles}\MSYS2",
    [string]$InstallLog = "$env:TEMP\synapse-mingw-provision.log"
)

$ErrorActionPreference = "Stop"
$requiredPackages = @("mingw-w64-x86_64-gcc", "make", "pkg-config")
$requiredExes = @("gcc.exe", "g++.exe", "ld.exe")

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$timestamp] $Message"
    Write-Host $line
    Add-Content -Path $InstallLog -Value $line -Encoding UTF8
}

function Test-Command {
    param([string]$Name)
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    return $null -ne $cmd
}

function Invoke-GccVersion {
    $gcc = Get-Command gcc.exe -ErrorAction SilentlyContinue
    if ($gcc) {
        $ver = & gcc --version 2>$null | Select-Object -First 1
        Write-Log "GCC encontrado: $ver"
        return $true
    }
    return $false
}

Write-Log "=== Provisionamiento MinGW Toolchain (Synapse) ==="

if (Invoke-GccVersion) {
    Write-Log "GCC ya está en PATH — instalación previa detectada"
    exit 0
}

if (Test-Path $MingwRoot) {
    Write-Log "MSYS2 ya instalado en $MingwRoot"
} else {
    Write-Log "MSYS2 no encontrado — instalando via winget..."

    if (Test-Command winget) {
        Write-Log "winget disponible — ejecutando: winget install MSYS2.MSYS2"
        winget install MSYS2.MSYS2 --accept-package-agreements --accept-source-agreements 2>&1 | Tee-Object -Variable wingetOutput | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Log "[WARN] winget install falló (código $LASTEXITCODE)"
        }
    } elseif (Test-Command choco) {
        Write-Log "Chocolatey disponible — ejecutando: choco install msys2 -y"
        choco install msys2 -y 2>&1 | Tee-Object -Variable chocoOutput | Out-Null
    } else {
        Write-Log "[ERROR] Ni winget ni chocolatey disponibles — requiere instalación manual de MSYS2"
        Write-Log "Descargar de: https://www.msys2.org/"
        exit 1
    }
}

if (-not (Test-Path $MingwRoot)) {
    $MingwRoot = "${env:ProgramFiles}\MSYS2"
}

$mingw64Bin = Join-Path $MingwRoot "mingw64\bin"
if (-not (Test-Path $mingw64Bin)) {
    $mingw64Bin = Join-Path $MingwRoot "usr\bin"
}

Write-Log "MinGW bin path: $mingw64Bin"

$currentUserPath = [Environment]::GetEnvironmentVariable("Path", "CurrentUser")
if ($currentUserPath -notmatch [regex]::Escape($mingw64Bin)) {
    Write-Log "Agregando $mingw64Bin al PATH del usuario"
    $newPath = $currentUserPath.TrimEnd(';') + ";" + $mingw64Bin
    [Environment]::SetEnvironmentVariable("Path", $newPath, "CurrentUser")
}

$processPath = $env:PATH
if ($processPath -notmatch [regex]::Escape($mingw64Bin)) {
    $env:PATH = $processPath + ";" + $mingw64Bin
}

if (Invoke-GccVersion) {
    Write-Log "✅ GCC funcionando después de la provision"
    Write-Log "=== Provisionamiento completado ==="
    exit 0
} else {
    Write-Log "[ERROR] GCC no disponible tras provisionamiento"
    exit 1
}
