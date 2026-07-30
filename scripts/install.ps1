param(
    [string]$Version = "v1.5.0",
    [string]$InstallDir = "C:\Synapse"
)

$ErrorActionPreference = "Stop"
$RepoUrl = "https://github.com/gedeon1972-svg/synapse-lang"
$ZipUrl = "$RepoUrl/releases/download/$Version/synapse-$Version-windows-x64.zip"
$ZipPath = "$env:TEMP\synapse-$Version.zip"

# MinGW-w64 (WinLibs) - solo C, portable, sin C++
# Fuente: https://winlibs.com/
$MingwUrl = "https://github.com/brechtsanders/winlibs_mingw/releases/download/13.2.0posix-17.0.6-11.0.0-ucrt-r1/winlibs-x86_64-posix-seh-gcc-13.2.0-mingw-w64ucrt-11.0.0-r1.zip"
$MingwZipPath = "$env:TEMP\winlibs-mingw.zip"

Write-Host "Synapse $Version - Instalador Automatico" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

if (Test-Path $InstallDir) {
    Remove-Item -Path "$InstallDir\*" -Recurse -Force -ErrorAction SilentlyContinue
} else {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

Write-Host "[1/5] Descargando binarios de Synapse..." -NoNewline
try {
    Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipPath -UseBasicParsing -ErrorAction Stop
    Write-Host " OK" -ForegroundColor Green
} catch {
    Write-Host " ERROR" -ForegroundColor Red
    Write-Host "No se pudo descargar desde:`n$ZipUrl" -ForegroundColor Red
    exit 1
}

Write-Host "[2/5] Extrayendo binarios en $InstallDir..." -NoNewline
try {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($ZipPath, $InstallDir)
    Write-Host " OK" -ForegroundColor Green
} catch {
    Write-Host " ERROR" -ForegroundColor Red
    exit 1
}

Remove-Item $ZipPath -Force -ErrorAction SilentlyContinue

# Toolchain interno (MinGW-w64 portable) - solo C
$ToolchainDir = Join-Path $InstallDir "toolchain"
$GccPath = Join-Path $ToolchainDir "bin\gcc.exe"

if (-not (Test-Path $GccPath)) {
    Write-Host "[3/5] Provisionando toolchain C interno (MinGW-w64)..." -NoNewline
    try {
        # Descargar WinLibs MinGW-w64
        Write-Host ""
        Write-Host "   Descargando MinGW-w64 (WinLibs)..." -NoNewline
        Invoke-WebRequest -Uri $MingwUrl -OutFile $MingwZipPath -UseBasicParsing -ErrorAction Stop
        Write-Host " OK" -ForegroundColor Green

        Write-Host "   Extrayendo toolchain..." -NoNewline
        [System.IO.Compression.ZipFile]::ExtractToDirectory($MingwZipPath, $InstallDir)
        Write-Host " OK" -ForegroundColor Green

        # WinLibs extrae como "mingw64/", mover a "toolchain/"
        $MingwExtracted = Join-Path $InstallDir "mingw64"
        if (Test-Path $MingwExtracted) {
            Move-Item -Path "$MingwExtracted\*" -Destination $ToolchainDir -Force
            Remove-Item -Path $MingwExtracted -Recurse -Force
        }

        Remove-Item $MingwZipPath -Force -ErrorAction SilentlyContinue

        if (Test-Path $GccPath) {
            Write-Host "   Toolchain C listo en $ToolchainDir" -ForegroundColor Green
        } else {
            throw "gcc.exe no encontrado despues de extraer"
        }
    } catch {
        Write-Host " ERROR" -ForegroundColor Red
        Write-Host "No se pudo provisionar el toolchain: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[3/5] Toolchain C ya presente en $ToolchainDir" -ForegroundColor Green
}

Write-Host "[4/5] Configurando PATH de usuario..." -NoNewline
$BinPath = Join-Path $InstallDir "bin"
$CurrentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($CurrentPath -split ";" -notcontains $BinPath) {
    $NewPath = $CurrentPath + ";" + $BinPath
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
    Write-Host " OK" -ForegroundColor Green
} else {
    Write-Host " ya presente" -ForegroundColor Yellow
}

Write-Host "[5/5] Verificando instalacion..." -NoNewline
if (Test-Path (Join-Path $InstallDir "synapse.exe") -and (Test-Path $GccPath)) {
    Write-Host " OK" -ForegroundColor Green
} else {
    Write-Host " ADVERTENCIA: Faltan componentes" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Synapse $Version instalado correctamente." -ForegroundColor Green
Write-Host "Reinicia tu terminal para usar el comando 'synapse'." -ForegroundColor Cyan
Write-Host "Toolchain C interno: $GccPath" -ForegroundColor Gray