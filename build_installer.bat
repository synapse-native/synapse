@echo off
REM build_installer.bat — Automatización del Instalador Maestro (Fase 4.1)
REM Invoca al compilador de Inno Setup: iscc instalador_synapse.iss
REM Valida que el artefacto binario resultante se empaquete correctamente en dist/Synapse-2.2.2-Windows-x64.exe

setlocal enabledelayedexpansion

echo ============================================================
echo  SYNAPSE LANGUAGE - BUILD INSTALLER MAESTRO (Fase 4.1)
echo ============================================================
echo.

REM Verificar que Inno Setup Compiler (iscc) esté disponible
where iscc >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Inno Setup Compiler (iscc) no encontrado en PATH.
    echo          Instale Inno Setup 6+ y agregue su carpeta bin al PATH.
    echo          Ejemplo: C:\Program Files (x86)\Inno Setup 6\ISCC.exe
    exit /b 1
)

echo [INFO] Inno Setup Compiler encontrado: 
for %%I in (iscc.exe) do echo         %%~$PATH:I
echo.

REM Verificar que el script .iss existe
if not exist "instalador_synapse.iss" (
    echo [ERROR] instalador_synapse.iss no encontrado en %CD%
    exit /b 1
)

echo [INFO] Compilando instalador con Inno Setup...
echo [CMD]  iscc instalador_synapse.iss
echo.

REM Ejecutar compilador Inno Setup
iscc instalador_synapse.iss
set ISCC_EXIT=%errorlevel%

echo.
if %ISCC_EXIT% neq 0 (
    echo [ERROR] iscc fallo con codigo de salida %ISCC_EXIT%
    exit /b %ISCC_EXIT%
)

echo [OK] Compilacion Inno Setup exitosa (codigo %ISCC_EXIT%)
echo.

REM Validar artefacto de salida
set OUTPUT_EXE=dist\Synapse-2.2.2-Windows-x64.exe
echo [VALIDACION] Verificando artefacto: %OUTPUT_EXE%

if not exist "%OUTPUT_EXE%" (
    echo [ERROR] Artefacto NO encontrado: %OUTPUT_EXE%
    echo [INFO]   Contenido de dist\:
    dir dist\ 2>nul || echo           (directorio vacio o no existe)
    exit /b 1
)

REM Obtener tamaño del archivo
for %%F in ("%OUTPUT_EXE%") do set FILESIZE=%%~zF
set FILESIZE_MB=%FILESIZE% / 1024 / 1024

echo [OK] Artefacto encontrado: %OUTPUT_EXE%
echo [INFO] Tamano: %FILESIZE% bytes (~%FILESIZE_MB% MB)

REM Validación básica: archivo > 10MB (instalador completo con MinGW + IA)
set MIN_SIZE=10485760
if %FILESIZE% lss %MIN_SIZE% (
    echo [WARN] Tamano sospechosamente pequeno (< 10 MB). Verificar contenido.
) else (
    echo [OK] Tamano dentro de rango esperado (> 10 MB).
)

REM Verificar que el ejecutable es PE válido (Windows)
echo [VALIDACION] Verificando firma PE...
powershell -NoProfile -Command ^
    "try { $f = Get-Item '%OUTPUT_EXE%'; $bytes = [System.IO.File]::ReadAllBytes($f.FullName); if ($bytes[0] -eq 0x4D -and $bytes[1] -eq 0x5A) { Write-Host '[OK] Cabecera MZ valida'; exit 0 } else { Write-Host '[ERROR] No es ejecutable PE valido'; exit 1 } } catch { Write-Host '[ERROR] Excepcion: ' $_; exit 1 }"
set PE_CHECK=%errorlevel%

if %PE_CHECK% neq 0 (
    echo [ERROR] Validacion PE fallida.
    exit /b 1
)

echo.
echo ============================================================
echo  BUILD INSTALLER COMPLETADO CON EXITO
echo ============================================================
echo  Artefacto: %OUTPUT_EXE%
echo  Tamano:    %FILESIZE% bytes
echo  Fecha:     %DATE% %TIME%
echo ============================================================

exit /b 0