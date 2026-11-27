@echo off
:: build_vsix.bat — Build and sign VSIX package for Synapse VS Code Extension
:: ============================================================================
:: Requisitos:
::   1. Node.js + npm (para vsce)
::   2. vsce instalado globalmente: npm install -g vsce
::   3. OpenSSL (para SHA-256) — incluido en Git Bash / MSYS2
::
:: Uso:
::   build_vsix.bat [version]
::
:: Política de Seguridad:
::   - Zero telemetría: .vscodeignore excluye cualquier rastro de analytics
::   - Binarios firmados opcionalmente vía CI/CD con Ed25519
::   - SHA-256 generado para verificación de integridad
:: ============================================================================

setlocal enabledelayedexpansion
set VSIX_DIR=%~dp0
set PROJECT_ROOT=%VSIX_DIR%..
set VERSION=8.1.0

if not "%1"=="" set VERSION=%1

echo ============================================================
echo  Synapse VS Code Extension — Build v%VERSION%
echo ============================================================
echo.

:: 1. Verificar dependencias
where vsce >nul 2>&1
if errorlevel 1 (
    echo [FAIL] vsce no encontrado. Instalar: npm install -g vsce
    exit /b 1
)

where openssl >nul 2>&1
if errorlevel 1 (
    echo [WARN] openssl no encontrado. SHA-256 no se generara.
    set NO_SSL=1
) else (
    set NO_SSL=0
)

:: 2. Actualizar version en package.json
echo [*] Version: %VERSION%
powershell -NoProfile -Command ^
    "(gc '%VSIX_DIR%package.json') -replace '\"version\": \"[^\"]+\"', '\"version\": \"%VERSION%\"' | Out-File -Encoding UTF8 '%VSIX_DIR%package.json'"

:: 3. Instalar dependencias npm (si no existen)
if not exist "%VSIX_DIR%node_modules\vscode-languageclient" (
    echo [*] Instalando dependencias npm...
    cd /d "%VSIX_DIR%"
    call npm install --production
    if errorlevel 1 (
        echo [FAIL] npm install fallo
        exit /b 1
    )
) else (
    echo [OK] Dependencias npm ya instaladas
)

:: 4. Empaquetar VSIX
echo [*] Ejecutando vsce package...
cd /d "%VSIX_DIR%"
call vsce package --out "synapse-vscode-v%VERSION%.vsix"
if errorlevel 1 (
    echo [FAIL] vsce package fallo
    exit /b 1
)

set VSIX_FILE=synapse-vscode-v%VERSION%.vsix
echo [OK] VSIX generado: %VSIX_FILE%

:: 5. Generar SHA-256 del VSIX
if "%NO_SSL%"=="0" (
    echo [*] Generando SHA-256...
    for /f "delims=" %%i in ('openssl dgst -sha256 "%VSIX_FILE%" ^| find /v "stdin"') do set SHA256=%%i
    echo !SHA256! > "%VSIX_FILE%.sha256"
    set SHA_ONLY=!SHA256:* =!
    echo [OK] SHA-256: !SHA_ONLY!
    
    :: Opcional: firmar con Ed25519 si hay clave
    if exist "%PROJECT_ROOT%\signing_key.hex" (
        echo [*] Firmando VSIX con Ed25519...
        for /f %%i in (%PROJECT_ROOT%\signing_key.hex) do set SK=%%i
        :: Nota: requires custom sign tool — placeholder
        echo [WARN] Firma Ed25519 configurada pero requiere herramienta externa
        echo        Usar: sign_tool ed25519 "%VSIX_FILE%" "%VSIX_FILE%.sig" "!SK!"
    ) else (
        echo [INFO] Sin clave de firma. Solo SHA-256 generado.
    )
) else (
    echo [WARN] SHA-256 omitido (openssl no disponible)
)

:: 6. Verificar integridad del .vsix
if exist "%VSIX_FILE%" (
    for %%i in ("%VSIX_FILE%") do set SIZE=%%~zi
    echo [OK] Verificado: %VSIX_FILE% (!SIZE! bytes)
    echo.
    echo ============================================================
    echo  BUILD COMPLETE
    echo ============================================================
    echo  Archivo: %VSIX_FILE%
    if not "%NO_SSL%"=="0" (
        echo  SHA-256: !SHA_ONLY!
    )
    echo.
    echo  Instalar: code --install-extension "%VSIX_FILE%"
    echo ============================================================
    exit /b 0
) else (
    echo [FAIL] %VSIX_FILE% no encontrado tras build
    exit /b 1
)
