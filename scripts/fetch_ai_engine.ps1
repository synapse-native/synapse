<# 
.SYNOPSIS
    Aprovisionamiento automatizado del motor IA local (llama-server.exe + modelo .gguf)
    Para Synapse Language - Fase 3.4

.DESCRIPTION
    Descarga binarios oficiales de llama.cpp y modelo GGUF, verifica integridad y emplaza en dist/ia/
    Requiere: PowerShell 5.1+, curl disponible

.NOTES
    Versión llama.cpp validada: b4380 (compatible API nativa /completion, /slot_save, /slot_restore, /embedding)
    Modelo: Llama-3.2-1B-Instruct-Q4_K_M.gguf (~700MB)
#>

param(
    [string]$LlamaCppVersion = "b4380",
    [string]$TargetDir = "dist\ia",
    [switch]$ForceRedownload,
    [switch]$SkipModelDownload
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# Colores para output
function Write-Status { param($msg) Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $msg" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✓ $msg" -ForegroundColor Green }
function Write-Warning { param($msg) Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ⚠ $msg" -ForegroundColor Yellow }
function Write-ErrorMsg { param($msg) Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✗ $msg" -ForegroundColor Red }

# URLs oficiales
$LlamaServerUrl = "https://github.com/ggerganov/llama.cpp/releases/download/$LlamaCppVersion/llama-server.exe"
$ModelUrl = "https://huggingface.co/TheBloke/Llama-3.2-1B-Instruct-GGUF/resolve/main/llama-3.2-1b-instruct.Q4_K_M.gguf"

# Hashes SHA256 conocidos (actualizar al cambiar versión)
$ExpectedHashes = @{
    "llama-server.exe" = "TODO_ACTUALIZAR_CON_HASH_REAL"
    "llama-3.2-1b-instruct.Q4_K_M.gguf" = "TODO_ACTUALIZAR_CON_HASH_REAL"
}

Write-Status "=== SYNAPSE AI ENGINE PROVISIONING ==="
Write-Status "Versión llama.cpp: $LlamaCppVersion"
Write-Status "Directorio destino: $TargetDir"

# Crear directorio
if (-not (Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
    Write-Status "Directorio creado: $TargetDir"
}

# Función: Verificar hash SHA256
function Verify-FileHash {
    param($FilePath, $ExpectedHash)
    if (-not (Test-Path $FilePath)) { return $false }
    $actual = (Get-FileHash -Path $FilePath -Algorithm SHA256).Hash.ToLower()
    return $actual -eq $ExpectedHash.ToLower()
}

# Función: Descargar con progreso y reintentos
function Download-WithRetry {
    param($Url, $OutPath, $MaxRetries = 3)
    
    for ($i = 1; $i -le $MaxRetries; $i++) {
        try {
            Write-Status "Descargando: $Url (intento $i/$MaxRetries)"
            $progress = $null
            Invoke-WebRequest -Uri $Url -OutFile $OutPath -UseBasicParsing `
                -ProgressAction SilentlyContinue `
                -ErrorAction Stop
            Write-Success "Descarga completa: $OutPath"
            return $true
        } catch {
            Write-Warning "Intento $i falló: $($_.Exception.Message)"
            if ($i -eq $MaxRetries) { throw }
            Start-Sleep -Seconds 5
        }
    }
    return $false
}

# 1. Descargar llama-server.exe
$ServerExe = Join-Path $TargetDir "llama-server.exe"
if ($ForceRedownload -or -not (Test-Path $ServerExe)) {
    Write-Status "Bajando llama-server.exe..."
    Download-WithRetry -Url $LlamaServerUrl -OutPath $ServerExe
    if ($ExpectedHashes["llama-server.exe"] -ne "TODO_ACTUALIZAR_CON_HASH_REAL") {
        if (-not (Verify-FileHash $ServerExe $ExpectedHashes["llama-server.exe"])) {
            Write-ErrorMsg "HASH MISMATCH: llama-server.exe no coincide con hash esperado"
            Remove-Item $ServerExe -Force
            exit 1
        }
        Write-Success "Hash verificado: llama-server.exe"
    } else {
        Write-Warning "Hash de llama-server.exe NO verificado (placeholder)"
    }
} else {
    Write-Success "llama-server.exe ya existe, omitiendo descarga"
}

# 2. Descargar modelo GGUF
if (-not $SkipModelDownload) {
    $ModelFile = Join-Path $TargetDir "llama-3.2-1b-instruct.Q4_K_M.gguf"
    if ($ForceRedownload -or -not (Test-Path $ModelFile)) {
        Write-Status "Bajando modelo GGUF (~700MB)..."
        Download-WithRetry -Url $ModelUrl -OutPath $ModelFile -MaxRetries 2
        if ($ExpectedHashes["llama-3.2-1b-instruct.Q4_K_M.gguf"] -ne "TODO_ACTUALIZAR_CON_HASH_REAL") {
            if (-not (Verify-FileHash $ModelFile $ExpectedHashes["llama-3.2-1b-instruct.Q4_K_M.gguf"])) {
                Write-ErrorMsg "HASH MISMATCH: modelo GGUF no coincide con hash esperado"
                Remove-Item $ModelFile -Force
                exit 1
            }
            Write-Success "Hash verificado: modelo GGUF"
        } else {
            Write-Warning "Hash de modelo GGUF NO verificado (placeholder)"
        }
    } else {
        Write-Success "Modelo GGUF ya existe, omitiendo descarga"
    }
}

# 3. Verificar ejecutable
Write-Status "Verificando binario llama-server.exe..."
try {
    $versionOutput = & $ServerExe --version 2>&1
    Write-Success "llama-server.exe responde: $versionOutput"
} catch {
    Write-ErrorMsg "llama-server.exe falló al ejecutar --version"
    exit 1
}

Write-Success "=== APROVISIONAMIENTO COMPLETADO ==="
Write-Status "Binario: $ServerExe"
Write-Status "Modelo: $ModelFile"
Write-Status "Para iniciar: $ServerExe -m $ModelFile --host 127.0.0.1 --port 8088 --ctx-size 4096 --threads 4 --no-mmap --mlock"