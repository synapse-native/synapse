# prewarm_runtime_cache.ps1 — Precalentamiento de la cache de objetos del runtime
# cumple Manual 8 §4.1, Manual 9 §2.2, Manual 9 §7 (H-RUNTIME-CACHE-COLD-1):
# en una instalacion nueva, la primera compilacion nativa recompila ~50 fuentes
# C del runtime (~90-180 s). Este script compila esos .o UNA VEZ durante la
# instalacion, con el toolchain incluido, y los deja en
#   %USERPROFILE%\.synapse\cache\runtime_obj\
# (la misma ruta que resuelve nucleo/principal.syn), con el sidecar .sha que
# exige el guard de frescura (SHA-256 del fuente + toolchain).
# Invocado por synapse.iss [Run] como:
#   powershell -ExecutionPolicy Bypass -NoProfile -File "{app}\prewarm_runtime_cache.ps1"
$ErrorActionPreference = "SilentlyContinue"

$raiz = Split-Path -Parent $MyInvocation.MyCommand.Path
$gcc = Join-Path $raiz "toolchain_gcc12\mingw64\bin\gcc.exe"
if (-not (Test-Path $gcc)) {
    # Fallback: gcc del PATH
    $g = Get-Command gcc -ErrorAction SilentlyContinue
    if ($g) { $gcc = $g.Source } else {
        Write-Host "[Synapse] prewarm: sin toolchain incluido ni gcc en PATH, se omite."
        exit 0
    }
}

$rtDir = Join-Path $raiz "bin"
if (-not (Test-Path (Join-Path $rtDir "synapse_rt.c"))) {
    # Algunos layouts dejan el runtime junto al exe dos niveles arriba
    $cand = Join-Path $raiz "bin"
    if (Test-Path (Join-Path $cand "synapse_rt.c")) { $rtDir = $cand }
}

$cacheDir = Join-Path $env:USERPROFILE ".synapse\cache\runtime_obj"
New-Item -ItemType Directory -Force -Path $cacheDir | Out-Null

function Sha256File($p) {
    try { (Get-FileHash -Algorithm SHA256 -Path $p).Hash.ToLower() } catch { "" }
}

# Lista de fuentes del runtime (paridad con pipeline.py _RT_FUENTES + escaneo
# de runtime/core/*.c que hace el compilador nativo).
$fuentes = @()
$rt = Join-Path $rtDir "synapse_rt.c"
if (Test-Path $rt) { $fuentes += $rt }
$coreDir = Join-Path $rtDir "runtime\core"
if (Test-Path $coreDir) {
    Get-ChildItem -Path $coreDir -Filter "*.c" | ForEach-Object { $fuentes += $_.FullName }
}
$axon = Join-Path $rtDir "axon\tweetnacl.c"
if (Test-Path $axon) { $fuentes += $axon }
$sqlite = Join-Path $rtDir "vendor\sqlite3\sqlite3.c"
if (Test-Path $sqlite) { $fuentes += $sqlite }
foreach ($ia in @("nucleo\fine_tuning.c","nucleo\distillation.c","nucleo\quantization.c")) {
    $p = Join-Path $rtDir $ia
    if (Test-Path $p) { $fuentes += $p }
}
$fed = Join-Path $rtDir "nucleo\federated.c"
if (Test-Path $fed) { $fuentes += $fed }

$ok = 0; $fail = 0
foreach ($src in $fuentes) {
    $name = [System.IO.Path]::GetFileNameWithoutExtension($src)
    $obj = Join-Path $cacheDir ($name + ".o")
    $sidecar = $obj + ".sha"
    $sha = Sha256File $src
    if ($sha -eq "") { $fail++; continue }
    # Compilar con el toolchain incluido (mismo gcc que usara el binario).
    $args = @("-O2", "-c", "-I", $rtDir, "`"$src`"", "-o", "`"$obj`"")
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $gcc
    $psi.Arguments = ($args -join " ")
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $p = [System.Diagnostics.Process]::Start($psi)
    $p.WaitForExit()
    if ($p.ExitCode -ne 0 -or -not (Test-Path $obj)) { $fail++; continue }
    # Sidecar: <sha>|<gcc>|...  (el guard nativo valida sha + toolchain)
    $key = "$sha|$gcc|-O2|-I $rtDir|"
    Set-Content -Path $sidecar -Value $key -NoNewline
    $ok++
}

Write-Host "[Synapse] prewarm runtime cache: $ok OK, $fail fallos (dir: $cacheDir)"
exit 0