# Habilita branch protection en main con los checks de control requeridos.
#
# Esto es la pieza final que hace "que funcione de verdad": aunque un agente use
# --no-verify en su maquina, el PR no puede mergear y el push directo esta bloqueado.
# Requiere: gh CLI autenticado (gh auth login) con permisos de admin en el repo.
#
# Uso (PowerShell):  .\scripts\enable_branch_protection.ps1

$ErrorActionPreference = "Stop"

$repo = gh repo view --json nameWithOwner -q .nameWithOwner
if (-not $repo) { throw "No se pudo resolver el repo (¿gh auth login?)" }

$body = @{
    required_status_checks = @{
        strict   = $true
        contexts = @(
            "lint-and-check",
            "test",
            "auditoria",
            "calidad-tests",
            "trazabilidad-codigo",
            "lectura-previa"
        )
    }
    enforce_admins                 = $true
    required_pull_request_reviews = @{
        required_approving_review_count = 1
        dismiss_stale_reviews           = $true
    }
    restrictions                   = $null
} | ConvertTo-Json -Depth 5

$tmp = Join-Path $env:TEMP "branch_protection.json"
$body | Out-File -Encoding utf8 $tmp

Write-Host "Aplicando branch protection a $repo (branch main)..."
gh api "repos/$repo/branches/main/protection" `
    --method PUT `
    -H "Accept: application/vnd.github+json" `
    --input $tmp

Write-Host "✅ Branch protection activada. main ahora exige: lint-and-check, test, auditoria, calidad-tests, trazabilidad-codigo, lectura-previa + 1 revision (CODEOWNERS)."
Write-Host "⚠️  Recuerda fijar el equipo/handle real en .github/CODEOWNERS (hoy: @synapse-architect)."
