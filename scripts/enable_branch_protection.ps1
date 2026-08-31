# Habilita branch protection en main con los checks de control requeridos.
#
# Usa GitHub Repository Rules API (protección de ramas moderna).
# Requiere: gh CLI autenticado (gh auth login) con permisos de admin en el repo.
#
# Uso (PowerShell):  .\scripts\enable_branch_protection.ps1

$ErrorActionPreference = "Stop"

# 0. Helper: API version constant
$API_VERSION = "2022-11-28"

# 1. Resolver el repo
$repo = gh repo view --json nameWithOwner -q .nameWithOwner
if (-not $repo) { throw "No se pudo resolver el repo (¿gh auth login?)" }
$owner, $repoName = $repo -split "/"

# 2. Listar rulesets existentes para "branch" target
$allRulesets = gh api "repos/$repo/rulesets" --method GET -H "X-GitHub-Api-Version: $API_VERSION" | ConvertFrom-Json -ErrorAction SilentlyContinue
$mainRulesetId = $nil
if ($allRulesets -and $allRulesets.rulesets) {
    foreach ($rs in $allRulesets.rulesets) {
        if ($rs.source -eq $repo -and $rs.target -eq "branch") {
            $mainRulesetId = $rs.id
            break
        }
    }
}

# 3. Construir el ruleset (crea o reemplaza)
if ($mainRulesetId) {
    Write-Host "Actualizando ruleset existente (id=$mainRulesetId)..."
    $uri = "repos/$repo/rulesets/$mainRulesetId"
    $method = "PUT"
} else {
    Write-Host "Creando nuevo ruleset para main..."
    $uri = "repos/$repo/rulesets"
    $method = "POST"
}

# NOTA: La API de rulesets requiere todos los parámetros de pull_request si se envía el bloque.
#       No permite parciales. Aquí se envían todos con valores correctos.
$payload = @{
    name        = "main-protection"
    target      = "branch"
    enforcement = "active"
    conditions  = @{
        ref_name = @{
            include = @("refs/heads/main")
            exclude = @()
        }
    }
    rules = @(
        @{
            type       = "required_status_checks"
            parameters = @{
                strict_required_status_checks_policy = $true
                required_status_checks = @(
                    @{ context = "lint-and-check" }
                    @{ context = "test" }
                    @{ context = "auditoria" }
                    @{ context = "calidad-tests" }
                    @{ context = "trazabilidad-codigo" }
                    @{ context = "lectura-previa" }
                )
            }
        }
        @{
            type       = "pull_request"
            parameters = @{
                require_code_owner_review          = $true
                dismiss_stale_reviews_on_push      = $true
                required_approving_review_count     = 1
                require_last_push_approval         = $false
                required_review_thread_resolution  = $false
                allowed_merge_methods              = @("merge", "squash", "rebase")
                require_extra_approval_for_unattributed_changes = $true
                dismissal_restriction              = @{ enabled = $false; allowed_actors = @() }
                required_reviewers                 = @()
            }
        }
        @{
            type       = "non_fast_forward"
        }
    )
} | ConvertTo-Json -Depth 10

# 4. Escribir JSON sin BOM ni escapes de PowerShell (Out-File escapa; usar WriteAllText)
$tmp = Join-Path $env:TEMP "synapse_ruleset.json"
[System.IO.File]::WriteAllText($tmp, $payload)

Write-Host "Aplicando reglas de protección a $repo (branch main)..."
gh api "$uri" --method $method `
    -H "Accept: application/vnd.github+json" `
    -H "X-GitHub-Api-Version: $API_VERSION" `
    --input $tmp

Write-Host "✅ Branch protection activada. main ahora exige: lint-and-check, test, auditoria, calidad-tests, trazabilidad-codigo, lectura-previa + 1 revisión + code owner review."
Write-Host "⚠️  Recuerda fijar el equipo/handle real en .github/CODEOWNERS (hoy: @synapse-architect)."
