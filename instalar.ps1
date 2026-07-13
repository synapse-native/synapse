$ErrorActionPreference = "Stop"
$InstallDir = "C:\Synapse"
$ExeUrl = "https://github.com/synapse-native/synapse/releases/download/v2.1.0/synapse-windows-amd64.exe"
$ExePath = "$InstallDir\synapse.exe"

Write-Host "Synapse v2.1 - Instalador Automatico" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

Write-Host "[1/2] Descargando binario..." -NoNewline
try {
    Invoke-WebRequest -Uri $ExeUrl -OutFile $ExePath -UseBasicParsing -ErrorAction Stop
    Write-Host " OK" -ForegroundColor Green
} catch {
    Write-Host " ERROR" -ForegroundColor Red
    Write-Host "No se pudo descargar desde:`n$ExeUrl" -ForegroundColor Red
    exit 1
}

Write-Host "[2/2] Configurando PATH de usuario..." -NoNewline
try {
    $CurrentPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($CurrentPath -split ";" -notcontains $InstallDir) {
        $NewPath = $CurrentPath + ";" + $InstallDir
        [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
    }
    Write-Host " OK" -ForegroundColor Green
} catch {
    Write-Host " ERROR" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🚀 Synapse v2.1 instalado con éxito." -ForegroundColor Green
Write-Host "Reinicia tu terminal para usar el comando 'synapse'." -ForegroundColor Cyan
