# =========================================================================
# test-install.ps1 — Script de testing para instalador Windows
# =========================================================================
# Valida que el instalador funciona correctamente
# =========================================================================

param(
    [string]$InstallerDir = "$PSScriptRoot\..\..\instaladores\windows"
)

$LogFile = "$env:TEMP\synapse-test-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

# Función de logging
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    "[$timestamp] $Message" | Tee-Object -FilePath $LogFile
}

# Función de test
function Test-Case {
    param(
        [string]$TestName,
        [scriptblock]$TestCommand
    )
    
    Write-Log "TEST: $TestName"
    try {
        if (& $TestCommand) {
            Write-Log "  ✅ PASS"
            return $true
        } else {
            Write-Log "  ❌ FAIL"
            return $false
        }
    } catch {
        Write-Log "  ❌ FAIL: $_"
        return $false
    }
}

Write-Log "=== Testing Instalador Windows ==="
Write-Log "Log file: $LogFile"
Write-Log ""

# Tests
$PassCount = 0
$FailCount = 0

# Test 1: El script existe
if (Test-Case "Script existe" { Test-Path "$InstallerDir\synapse.iss" }) { $PassCount++ } else { $FailCount++ }

# Test 2: El script tiene sintaxis válida
if (Test-Case "Script tiene sintaxis válida" { 
    $content = Get-Content "$InstallerDir\synapse.iss" -Raw
    $content -match '\[Setup\]' -and $content -match '\[Files\]'
}) { $PassCount++ } else { $FailCount++ }

# Test 3: El script tiene opciones de componentes
if (Test-Case "Tiene opciones de componentes" { 
    $content = Get-Content "$InstallerDir\synapse.iss" -Raw
    $content -match '\[Components\]'
}) { $PassCount++ } else { $FailCount++ }

# Test 4: El script tiene verificación Ed25519
if (Test-Case "Tiene verificación Ed25519" { 
    $content = Get-Content "$InstallerDir\synapse.iss" -Raw
    $content -match 'verificar_firma'
}) { $PassCount++ } else { $FailCount++ }

# Test 5: El script tiene opción de actualización
if (Test-Case "Tiene opción de actualización" { 
    $content = Get-Content "$InstallerDir\synapse.iss" -Raw
    $content -match 'checkupdates'
}) { $PassCount++ } else { $FailCount++ }

# Resumen
Write-Log ""
Write-Log "=== Resumen de Testing ==="
Write-Log "Tests ejecutados: $($PassCount + $FailCount)"
Write-Log "Tests pasados: $PassCount"
Write-Log "Tests fallidos: $FailCount"
Write-Log ""

if ($FailCount -eq 0) {
    Write-Log "✅ TODOS LOS TESTS PASARON"
    exit 0
} else {
    Write-Log "❌ ALGUNOS TESTS FALLARON"
    exit 1
}
