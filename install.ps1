param(
    [string]$Version = "v1.5.0",
    [string]$InstallDir = "C:\Synapse"
)

$ErrorActionPreference = "Stop"
$RepoUrl = "https://github.com/gedeon1972-svg/synapse-lang"
$ZipUrl = "$RepoUrl/releases/download/$Version/synapse-$Version-windows-x64.zip"
$ZipPath = "$env:TEMP\synapse-$Version.zip"

Write-Host "Synapse $Version - Instalador Automatico" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

if (Test-Path $InstallDir) {
    Remove-Item -Path "$InstallDir\*" -Recurse -Force -ErrorAction SilentlyContinue
} else {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

Write-Host "[1/4] Descargando binarios..." -NoNewline
try {
    Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipPath -UseBasicParsing -ErrorAction Stop
    Write-Host " OK" -ForegroundColor Green
} catch {
    Write-Host " ERROR" -ForegroundColor Red
    Write-Host "No se pudo descargar desde:`n$ZipUrl" -ForegroundColor Red
    exit 1
}

Write-Host "[2/4] Extrayendo en $InstallDir..." -NoNewline
try {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($ZipPath, $InstallDir)
    Write-Host " OK" -ForegroundColor Green
} catch {
    Write-Host " ERROR" -ForegroundColor Red
    exit 1
}

Remove-Item $ZipPath -Force -ErrorAction SilentlyContinue

Write-Host "[3/4] Configurando PATH de usuario..." -NoNewline
$BinPath = Join-Path $InstallDir "bin"
$CurrentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($CurrentPath -split ";" -notcontains $BinPath) {
    $NewPath = $CurrentPath + ";" + $BinPath
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
    Write-Host " OK" -ForegroundColor Green
} else {
    Write-Host " ya presente" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Synapse $Version instalado correctamente." -ForegroundColor Green
Write-Host "Reinicia tu terminal para usar el comando 'synapse'." -ForegroundColor Cyan
