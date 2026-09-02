$ErrorActionPreference = 'Continue'
$root = 'D:\proyecto_synapse'
cd $root

function Stage {
    param($Exe, $Out)
    & ".\$Exe" nucleo/principal.syn -o $Out *> "logs\bootstrap_d12_$Out.log"
    return $LASTEXITCODE
}

Write-Output "$(Get-Date) [D-1.2] Etapa 1: S1 -> stage1"
python main.py nucleo/principal.syn -o synapse_stage1.exe *> logs\bootstrap_d12_s1.log
Write-Output "S1 rc=$LASTEXITCODE" | Out-File logs\bootstrap_d12_status.log
if ($LASTEXITCODE -ne 0) { Write-Output "STAGE1 FALLO"; exit 1 }

Write-Output "$(Get-Date) [D-1.2] Etapa 2: stage1 -> stage2"
$r2 = Stage synapse_stage1.exe synapse_stage2.exe
Write-Output "S2 rc=$r2" | Out-File -Append logs\bootstrap_d12_status.log
if ($r2 -ne 0) { Write-Output "STAGE2 FALLO"; exit 1 }

Write-Output "$(Get-Date) [D-1.2] Etapa 3: stage2 -> stage3"
$r3 = Stage synapse_stage2.exe synapse_stage3.exe
Write-Output "S3 rc=$r3" | Out-File -Append logs\bootstrap_d12_status.log
if ($r3 -ne 0) { Write-Output "STAGE3 FALLO"; exit 1 }

$a = (Get-FileHash synapse_stage2.exe -Algorithm SHA256).Hash
$b = (Get-FileHash synapse_stage3.exe -Algorithm SHA256).Hash
"STAGE2_SHA=$a" | Out-File logs\bootstrap_d12_cmp.log
"STAGE3_SHA=$b" | Out-File -Append logs\bootstrap_d12_cmp.log
if ($a -eq $b) { "S2==S3 BYTE-IDENTICAL: YES" | Out-File -Append logs\bootstrap_d12_cmp.log } else { "S2==S3 BYTE-IDENTICAL: NO" | Out-File -Append logs\bootstrap_d12_cmp.log }
Write-Output "$(Get-Date) [D-1.2] Bootstrap completado."
