<#
.SYNOPSIS
    Actualiza hashes SHA256 en synapse.iss descargando archivos y calculando hashes.
.DESCRIPTION
    Descarga llama-server y modelos GGUF, calcula SHA256, y actualiza los defines en synapse.iss.
    Usa cache local para evitar re-descargas innecesarias.
.NOTES
    Requiere: PowerShell 5.1+, curl.exe (Windows 10+), conexion a internet.
#>

param(
    [string]$IssPath = "instaladores\windows\synapse.iss",
    [string]$CacheDir = "$env:TEMP\SynapseInstallerCache",
    [switch]$ForceDownload,
    [switch]$VerifyOnly
)

$ErrorActionPreference = "Stop"

$Downloads = @(
    @{ Name="llama-server"; Url="https://github.com/ggml-org/llama.cpp/releases/download/b10819/llama-b10819-bin-win-cpu-x64.zip"; Define="LLAMA_SERVER_SHA256"; OutputName="llama-b10819-bin-win-cpu-x64.zip"; SizeHintMB=35 }
)

function Get-SHA256 {
    param([string]$FilePath)
    if (Test-Path $FilePath) { return (Get-FileHash -Algorithm SHA256 -Path $FilePath).Hash.ToLower() }
    return $null
}

function Download-WithResume {
    param([string]$Url, [string]$OutputPath, [int]$ExpectedSizeMB)
    $pinfo = New-Object System.Diagnostics.ProcessStartInfo
    $pinfo.FileName = if (Test-Path "C:\Windows\System32\curl.exe") { "C:\Windows\System32\curl.exe" } else { "curl.exe" }
    $tmpFile = $OutputPath + ".tmp"
$pinfo.Arguments = "-L -C - --progress-bar --fail --connect-timeout 30 --max-time 3600 -o `"$tmpFile`" `"$Url`""
    $pinfo.UseShellExecute = $false
    $pinfo.RedirectStandardOutput = $true
    $pinfo.RedirectStandardError = $true
    $pinfo.CreateNoWindow = $true
    $proc = [System.Diagnostics.Process]::Start($pinfo)
    $proc.WaitForExit()
    $exitCode = $proc.ExitCode
    if ($exitCode -eq 0 -and (Test-Path ($OutputPath + ".tmp"))) {
        Move-Item -Path ($OutputPath + ".tmp") -Destination $OutputPath -Force
        Write-Host " OK" -ForegroundColor Green
        return $true
    } else {
        Write-Host " FALLÓ (exit $exitCode)" -ForegroundColor Red
        if (Test-Path ($OutputPath + ".tmp")) { Remove-Item ($OutputPath + ".tmp") -Force -ErrorAction SilentlyContinue }
        return $false
    }
}

function Get-SHA256 {
    param([string]$FilePath)
    if (Test-Path $FilePath) { return (Get-FileHash -Algorithm SHA256 -Path $FilePath).Hash.ToLower() }
    return $null
}

$results = @()
$totalSize = 0
foreach ($dl in $Downloads) { $totalSize += $dl["SizeHintMB"] }
Write-Host "Total estimado: ${totalSize}MB"
Write-Host "Cache: $CacheDir"
Write-Host ""

foreach ($dl in $Downloads) {
    $outputPath = Join-Path $CacheDir $dl["OutputName"]
    $needsDownload = $ForceDownload -or (-not (Test-Path $outputPath))
    
    if (-not (Test-Path $outputPath)) { $needsDownload = $true }
    else {
        $sizeMB = [math]::Round((Get-Item $outputPath).Length / 1MB, 1)
        $minExpected = [math]::Floor($dl["SizeHintMB"] * 0.9)
        if ($sizeMB -lt $minExpected) {
            Write-Host "  Archivo existente demasiado pequeno ($sizeMB MB LT $minExpected MB), re-descargando..." -ForegroundColor Yellow
            $needsDownload = $true
        } else {
            Write-Host ("  Usando cache: {0} ({1} MB)" -f $dl["Name"], $sizeMB) -ForegroundColor Cyan
        }
    }
    
    if ($ForceDownload) { $needsDownload = $true }
    if ($needsDownload) {
        Write-Host ("  Descargando {0} (~{1} MB)..." -f $dl["Name"], $dl["SizeHintMB"]) -NoNewline
        $success = Download-WithResume -Url $dl["Url"] -OutputPath (Join-Path $CacheDir $dl["OutputName"]) -ExpectedSizeMB $dl["SizeHintMB"]
        if (-not $success) { Write-Error "Error descargando $($dl["Name"])"; exit 1 }
    }
    
    $sha = Get-SHA256 -FilePath (Join-Path $CacheDir $dl["OutputName"])
    if (-not $sha) { Write-Error "No se pudo calcular SHA256 para $($dl["Name"])"; exit 1 }
    
    $results += @{ Define = $dl["Define"]; Hash = $sha; Name = $dl["Name"] }
    Write-Host "  SHA256: $sha"
    Write-Host ""
}

if ($VerifyOnly) { Write-Host "Modo verificación: hashes calculados pero NO se actualizó el .iss" -ForegroundColor Yellow; exit 0 }

$issContent = Get-Content -Path $IssPath -Raw -Encoding UTF8
$updated = $false

foreach ($r in $results) {
    $oldPattern = '#define ' + $r.Define + ' "TODO_ACTUALIZAR_AL_COMPILAR"'
    $newLine = '#define ' + $r.Define + ' "' + $r.Hash + '"'
    
    if ($issContent -match [regex]::Escape($oldPattern)) {
        $issContent = $issContent -replace [regex]::Escape($oldPattern), $newLine
        Write-Host "  Actualizado $($r.Define) = $($r.Hash)" -ForegroundColor Green
        $updated = $true
    } elseif ($issContent -match '#define ' + $r.Define + ' "[a-f0-9]{64}"') {
        $issContent = $issContent -replace '#define ' + $r.Define + ' "[a-f0-9]{64}"', $newLine
        Write-Host "  Reemplazado $($r.Define) = $($r.Hash)" -ForegroundColor Green
        $updated = $true
    } else {
        Write-Warning "No se encontro define $($r.Define) en .iss"
    }
}

if ($updated) {
    Copy-Item $IssPath ("$IssPath.bak.$(Get-Date -Format 'yyyyMMdd_HHmmss')") -Force
    Set-Content -Path $IssPath -Value $issContent -Encoding UTF8
    Write-Host "`n.iss actualizado correctamente. Backup en .bak" -ForegroundColor Green
} else { Write-Warning "No se realizaron cambios en .iss" }

Write-Host "`n¡Listo! Puedes compilar con: iscc $IssPath" -ForegroundColor Cyan