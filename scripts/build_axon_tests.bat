@echo off
REM scripts/build_axon_tests.bat
REM Compila los binarios de test necesarios para la suite Axon E2E
REM (Manual 6.4, 6.5 - F18)
REM Ejecutar desde la raiz del proyecto

setlocal enabledelayedexpansion
set PATH=toolchain_gcc12\mingw64\bin;%PATH%

set ERR=0

REM --- gen_axon_test_fixtures.exe ---
echo [1/3] Compilando gen_axon_test_fixtures.exe...
gcc -I. -O2 tests\gen_axon_test_fixtures.c axon/tweetnacl.c -o tests\gen_axon_test_fixtures.exe -lm
if %ERRORLEVEL% neq 0 (
    echo [FAIL] gen_axon_test_fixtures.exe
    set /a ERR+=1
) else (
    echo [OK] gen_axon_test_fixtures.exe
)

REM --- test_ed25519_axon_new.exe ---
echo [2/3] Compilando test_ed25519_axon_new.exe...
gcc -I. -O2 tests\test_ed25519_axon.c synapse_rt.o synapse_rt_memory.o tweetnacl.o -o tests\test_ed25519_axon_new.exe -lpthread -lm -lws2_32
if %ERRORLEVEL% neq 0 (
    echo [FAIL] test_ed25519_axon_new.exe
    set /a ERR+=1
) else (
    echo [OK] test_ed25519_axon_new.exe
)

REM --- test_path_traversal_new.exe ---
echo [3/3] Compilando test_path_traversal_new.exe...
gcc -I. -O2 tests\test_path_traversal.c synapse_rt.o synapse_rt_memory.o tweetnacl.o -o tests\test_path_traversal_new.exe -lpthread -lm -lws2_32
if %ERRORLEVEL% neq 0 (
    echo [FAIL] test_path_traversal_new.exe
    set /a ERR+=1
) else (
    echo [OK] test_path_traversal_new.exe
)

REM --- Verificar que los .o existen ---
if not exist synapse_rt.o (
    echo [WARN] synapse_rt.o no encontrado - compilando...
    gcc -I. -O2 -c synapse_rt.c -o synapse_rt.o
)
if not exist synapse_rt_memory.o (
    echo [WARN] synapse_rt_memory.o no encontrado - compilando...
    gcc -I. -O2 -c synapse_rt_memory.c -o synapse_rt_memory.o
)
if not exist tweetnacl.o (
    echo [WARN] tweetnacl.o no encontrado - compilando...
    gcc -I. -O2 -c axon/tweetnacl.c -o tweetnacl.o
)

REM --- Preparar directorio .axon_cache para tests ---
if not exist tests\.axon_cache mkdir tests\.axon_cache

echo.
echo === BUILD COMPLETADO: %ERR% errores ===
exit /b %ERR%
