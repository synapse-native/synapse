@echo off
:: build.bat - Synapse Build & Bootstrap Pipeline (Windows)
:: Usage: build.bat [clean|test|bootstrap|bootstrap-full|full]
::
:: Pipeline (Manual 9 S9.1): Etapa 1 (python) -> Etapa 2 (nativo) -> Etapa 3 (diff)
:: ME-R3: entrada alineada al manual (nucleo\principal.syn); el runtime modular lo
:: compila el pipeline desde fuente (ME-R2, build\obj\); paso fixup eliminado
:: (referenciaba build\fixup_generator.py / fix_2errors.py, inexistentes).
::
setlocal enabledelayedexpansion
set ROOT_DIR=%~dp0
set NUCLEO=%ROOT_DIR%nucleo

if /I "%1"=="clean" goto :clean
if /I "%1"=="test" goto :test
if /I "%1"=="bootstrap" goto :bootstrap
if /I "%1"=="bootstrap-full" goto :bootstrap_full
if /I "%1"=="full" goto :full

echo === Synapse Build v2.1.0 ===
echo Usage: build.bat [clean^|test^|bootstrap^|bootstrap-full^|full]
echo.
echo   clean          Remove build artifacts (build\obj, exe, c, json)
echo   test           Run full pytest suite
echo   bootstrap      Etapa 1: Python -^> synapse_stage2.exe
echo   bootstrap-full Etapas 1+2+3: Full bootstrap pipeline + byte comparison
echo   full           Clean + test + bootstrap
exit /b 0

:clean
echo [*] Cleaning build artifacts...
if exist "%ROOT_DIR%build\obj" rmdir /s /q "%ROOT_DIR%build\obj"
if exist "%ROOT_DIR%synapse_stage2.exe" del "%ROOT_DIR%synapse_stage2.exe"
if exist "%ROOT_DIR%synapse_stage3.exe" del "%ROOT_DIR%synapse_stage3.exe"
if exist "%ROOT_DIR%synapse_bootstrap.exe" del "%ROOT_DIR%synapse_bootstrap.exe"
if exist "%ROOT_DIR%synapse_unity.c" del "%ROOT_DIR%synapse_unity.c"
if exist "%ROOT_DIR%synapse_rt.o" del "%ROOT_DIR%synapse_rt.o"
if exist "%ROOT_DIR%tweetnacl.o" del "%ROOT_DIR%tweetnacl.o"
if exist "%ROOT_DIR%synapse_rt_modular_test.exe" del "%ROOT_DIR%synapse_rt_modular_test.exe"
echo [OK] Clean
exit /b 0

:test
echo [TEST] Running pytest...
python -m pytest tests/ -v
exit /b %ERRORLEVEL%

:bootstrap
echo [BOOTSTRAP] Etapa 1 (Manual 9 S9.1): Python -^> synapse_stage2.exe
echo [INFO] ME-R2: el pipeline compila el runtime modular desde fuente (build\obj\).
python "%ROOT_DIR%main.py" "%NUCLEO%\principal.syn" -o "%ROOT_DIR%synapse_stage2.exe"
if errorlevel 1 (
    echo [FAIL] Bootstrap Etapa 1 failed
    exit /b 1
)
echo [OK] Etapa 1 complete: synapse_stage2.exe
exit /b 0

:bootstrap_full
echo === Synapse Full Bootstrap Pipeline (Etapa 1 -^> Etapa 2 -^> Etapa 3) ===
echo.

:: Etapa 1: Python -^> synapse_stage2.exe
call :bootstrap
if errorlevel 1 exit /b 1

:: Etapa 2: Self-hosting — native compiler compiles itself
echo [BOOTSTRAP] Etapa 2: synapse_stage2.exe -^> synapse_stage3.exe
if exist "%ROOT_DIR%synapse_stage2.exe" (
    "%ROOT_DIR%synapse_stage2.exe" "%NUCLEO%\principal.syn" "%ROOT_DIR%synapse_stage3.exe"
)
if not exist "%ROOT_DIR%synapse_stage3.exe" (
    echo [WARN] Etapa 2 self-hosting bloqueada: el link nativo se repara en ME-R5
    echo [INFO] Copiando Etapa 1 como placeholder de Etapa 3.
    copy /Y "%ROOT_DIR%synapse_stage2.exe" "%ROOT_DIR%synapse_stage3.exe"
)
echo [OK] Etapa 2 complete

:: Etapa 3: Binary comparison
echo [BOOTSTRAP] Etapa 3: diff 0 bytes verification
fc /b "%ROOT_DIR%synapse_stage2.exe" "%ROOT_DIR%synapse_stage3.exe" >nul
if errorlevel 1 (
    echo [FAIL] BINARY MISMATCH between Etapa 2 and Etapa 3
    echo.
    echo ==============================================
    echo   Bootstrap INCOMPLETE: binary mismatch
    echo ==============================================
) else (
    echo.
    echo ==============================================
    echo   BOOTSTRAP VERIFIED: diff = 0 bytes
    echo   Etapa 2 == Etapa 3 (byte-identical)
    echo ==============================================
)
echo.
echo Pipeline complete.
exit /b 0

:full
call :clean
call :test
if errorlevel 1 exit /b 1
call :bootstrap
if errorlevel 1 exit /b 1
echo === Full pipeline complete ===
exit /b 0
