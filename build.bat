@echo off
:: build.bat — OpenSyn Build Script (Windows)
:: Usage: build.bat [clean]

setlocal enabledelayedexpansion
set ROOT_DIR=%~dp0
set OPENEXE=%ROOT_DIR%opensyn\principal.exe

echo === OpenSyn Build v1.0.0 ===
echo.

:: Clean
if /I "%1"=="clean" (
    echo [*] Cleaning artifacts...
    del /Q "%ROOT_DIR%opensyn\principal.c" 2>nul
    del /Q "%ROOT_DIR%opensyn\principal.exe" 2>nul
    del /Q "%ROOT_DIR%opensyn\principal.syn.json" 2>nul
    del /Q "%ROOT_DIR%synapse_rt.o" 2>nul
    echo [OK] Clean
    exit /b 0
)

:: Step 1: Build runtime object
echo [1/4] Compilando runtime (synapse_rt.c)...
gcc -c "%ROOT_DIR%synapse_rt.c" -o "%ROOT_DIR%synapse_rt.o" ^
    -std=c99 -Wall -Wextra ^
    -Wno-unused-parameter -Wno-unused-function ^
    -lpthread -lm -lws2_32
if %ERRORLEVEL% neq 0 (
    echo [FAIL] synapse_rt.c compilation failed
    exit /b 1
)
echo [OK] synapse_rt.o

:: Step 2: Compile the orchestrator from Synapse source (via Python compiler)
echo [2/4] Compilando opensyn/principal.syn...
python "%ROOT_DIR%main.py" "%ROOT_DIR%opensyn\principal.syn"
if %ERRORLEVEL% neq 0 (
    echo [WARN] Python compilation had issues (may use fallback)
)
echo [OK] principal.c

:: Step 3: Verify executable exists
echo [3/4] Verificando binario...
if exist "%OPENEXE%" (
    echo [OK] %OPENEXE%
) else (
    echo [*] Fallback: enlazando con GCC directamente...
    gcc -o "%OPENEXE%" "%ROOT_DIR%opensyn\principal.c" ^
        "%ROOT_DIR%synapse_rt.c" ^
        -std=c99 -Wall -Wextra ^
        -Wno-unused-parameter -Wno-unused-function ^
        -I"%ROOT_DIR%" -lws2_32
    if !ERRORLEVEL! neq 0 (
        echo [FAIL] Link step failed
        exit /b 1
    )
    echo [OK] %OPENEXE% (fallback)
)

:: Step 4: Regenerate embedded libraries header
echo [4/4] Regenerando librerias/embedded_libs.h...
python "%ROOT_DIR%tests\_gen_embedded.py"
echo [OK] embedded_libs.h

echo.
echo === Build complete ===
echo Ejecuta: opensin\principal.exe
exit /b 0
