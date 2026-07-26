@echo off
REM run_benchmarks.bat — Lanza toda la suite de benchmarks M5.1
REM Uso: benchmarks\run_benchmarks.bat
REM Requiere: Python 3.8+, GCC >= 12 (MinGW-w64 con SSE4.1/AVX2)
REM           compilador Synapse (main.py)
REM
REM Toolchain: Inyecta temporalmente toolchain_gcc12/mingw64/bin en PATH
REM             sin contaminar el PATH global del sistema.

setlocal enabledelayedexpansion
set ROOT=%~dp0..
set BENCH=%~dp0

REM --- Toolchain MinGW-w64 GCC 12.4.0 (WinLibs standalone) ---
set TOOLCHAIN_DIR=%ROOT%\toolchain_gcc12\mingw64\bin
if exist "%TOOLCHAIN_DIR%\gcc.exe" (
    set "PATH=%TOOLCHAIN_DIR%;%PATH%"
    set "SYNAPSE_GCC_PATH=%TOOLCHAIN_DIR%\gcc.exe"
    echo [TOOLCHAIN] MinGW-w64 GCC 12.4.0 inyectado desde %TOOLCHAIN_DIR%
) else (
    echo [WARN] Toolchain no encontrado en %TOOLCHAIN_DIR%
    echo        Los benchmarks Synapse pueden fallar si GCC ^>= 12 no esta en PATH.
)
echo.

echo === Synapse Benchmark Suite M5.1 ===
echo.

REM 1. Verificar Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [FAIL] Python no encontrado en PATH
    echo        Instale Python 3.8+ desde https://python.org
    exit /b 1
)
echo [OK]  Python encontrado

REM 2. Verificar GCC >= 12 para compilacion SIMD
where gcc >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARN] GCC no encontrado en PATH
    echo        Los benchmarks Synapse requieren GCC ^>= 12 (MinGW-w64)
    echo        Descargue: https://github.com/brechtsanders/winlibs_mingw/releases
    echo        Los benchmarks Python se ejecutaran igualmente.
    echo.
) else (
    for /f "tokens=1,2,3 delims=. " %%a in ('gcc -dumpversion 2^>nul') do (
        set GCC_MAJOR=%%a
    )
    if !GCC_MAJOR! LSS 12 (
        echo [WARN] GCC !GCC_MAJOR! detectado (se requiere ^>= 12 para SIMD/AVX2)
    ) else (
        echo [OK]  GCC !GCC_MAJOR! detectado (compatible con SIMD/AVX2)
    )
)

REM 3. Verificar compilador Synapse
if exist "%ROOT%\main.py" (
    echo [OK]  Compilador Synapse encontrado (main.py)
) else (
    echo [WARN] main.py no encontrado en raiz del proyecto
)

echo.

REM 4a. Inyectar flags SIMD para compilacion Synapse
set "SYNAPSE_GCC_FLAGS=-O3 -mavx2"
echo [SIMD] Flags AVX2 inyectados: %%SYNAPSE_GCC_FLAGS%%
echo.

REM 4b. Ejecutar suite principal
python "%BENCH%todo_benchmarks.py"

if %ERRORLEVEL% neq 0 (
    echo ERROR: La suite fallo con codigo %ERRORLEVEL%
    exit /b 1
)

echo.
echo === Benchmarks completados exitosamente ===
echo.
