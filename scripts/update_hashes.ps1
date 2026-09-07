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

# cumple Manual 9 §5.3: el instalador verifica el llama-server.exe EXTRAIDO del zip,
# no el zip — extraer y hashear el exe real. HF LFS oid = SHA256 del contenido.
function Get-LlamaServerExeSHA256 {
    param([string]$ZipPath)
    $extractDir = Join-Path $env:TEMP ("llama_hash_extract_" + [guid]::NewGuid().ToString("N"))
    try {
        Expand-Archive -Path $ZipPath -DestinationPath $extractDir -Force
        $exe = Get-ChildItem -Path $extractDir -Recurse -Filter "llama-server.exe" | Select-Object -First 1
        if ($exe) { return (Get-FileHash -Algorithm SHA256 -Path $exe.FullName).Hash.ToLower() }
        return $null
    } finally {
        if (Test-Path $extractDir) { Remove-Item $extractDir -Recurse -Force -ErrorAction SilentlyContinue }
    }
}

function Get-HuggingFaceLfsOid {
    param([string]$Repo, [string]$FileName)
    $api = "https://huggingface.co/api/models/$Repo/tree/main"
    $entries = Invoke-RestMethod -Uri $api -TimeoutSec 30
    foreach ($e in $entries) {
        if ($e.path -eq $FileName) { return $e.lfs.oid }
    }
    return $null
}

$ModelDefs = @(
    @{ Define="MODEL_SHA256_1B";    Repo="TheBloke/deepseek-coder-1.3b-instruct-GGUF"; File="deepseek-coder-1.3b-instruct.Q4_K_M.gguf" },
    @{ Define="MODEL_SHA256_7B_Q4"; Repo="TheBloke/CodeLlama-7B-GGUF";  File="codellama-7b.Q4_K_M.gguf" },
    @{ Define="MODEL_SHA256_7B_Q5"; Repo="TheBloke/CodeLlama-7B-GGUF";  File="codellama-7b.Q5_K_M.gguf" },
    @{ Define="MODEL_SHA256_13B";   Repo="TheBloke/CodeLlama-13B-GGUF"; File="codellama-13b.Q4_K_M.gguf" },
    @{ Define="MODEL_SHA256_34B";   Repo="TheBloke/CodeLlama-34B-GGUF"; File="codellama-34b.Q4_K_M.gguf" }
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
if (-not (Test-Path $CacheDir)) { New-Item -ItemType Directory -Path $CacheDir -Force | Out-Null }
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

    # cumple Manual 9 §5.3: hashear el EXE extraído, no el zip (el instalador verifica el exe)
    $exeSha = Get-LlamaServerExeSHA256 -ZipPath (Join-Path $CacheDir $dl["OutputName"])
    if (-not $exeSha) { Write-Error "No se pudo extraer/hashear llama-server.exe"; exit 1 }

    $results += @{ Define = $dl["Define"]; Hash = $exeSha; Name = $dl["Name"] }
    Write-Host "  SHA256 (exe extraído): $exeSha"
    Write-Host ""
}

# Modelos GGUF: SHA256 = LFS oid de HuggingFace (sin descargar GBs)
foreach ($m in $ModelDefs) {
    Write-Host ("  Consultando LFS oid de {0} / {1}..." -f $m["Repo"], $m["File"]) -NoNewline
    $oid = Get-HuggingFaceLfsOid -Repo $m["Repo"] -FileName $m["File"]
    if (-not $oid) { Write-Error "No se encontro $($m["File"]) en $($m["Repo"])(repo renombrado/eliminado?)"; exit 1 }
    Write-Host " OK" -ForegroundColor Green
    $results += @{ Define = $m["Define"]; Hash = $oid.ToLower(); Name = $m["File"] }
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