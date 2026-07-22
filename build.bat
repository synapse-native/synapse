@echo off
:: build.bat — Synapse Build & Bootstrap Pipeline (Windows)
:: Usage: build.bat [clean|test|bootstrap|full]
::
:: Pipeline: regenerate -> fixup_generator.py -> fix_2errors.py -> gcc
::
setlocal enabledelayedexpansion
set ROOT_DIR=%~dp0
set NUCLEO=%ROOT_DIR%nucleo
set BUILD=%ROOT_DIR%build

if /I "%1"=="clean" goto :clean
if /I "%1"=="test" goto :test
if /I "%1"=="bootstrap" goto :bootstrap
if /I "%1"=="full" goto :full
if /I "%1"=="fixup" goto :fixup

echo === Synapse Build v2.1.0 ===
echo Usage: build.bat [clean^|test^|bootstrap^|fixup^|full]
echo.
echo   clean     Remove build artifacts (exe, o, c, json)
echo   fixup     Run post-processing fixup scripts on generator.c
echo   test      Run full pytest suite
echo   bootstrap Bootstrap pipeline: python main.py src/main.syn
echo   full      Clean + fixup + test + bootstrap
exit /b 0

:clean
echo [*] Cleaning build artifacts...
if exist "%ROOT_DIR%synapse_rt.o" del "%ROOT_DIR%synapse_rt.o"
if exist "%NUCLEO%\generator.o" del "%NUCLEO%\generator.o"
echo [OK] Clean
exit /b 0

:fixup
echo [FIXUP] Running post-processing on generator.c...
python "%BUILD%\fixup_generator.py"
python "%BUILD%\fix_2errors.py"
echo [OK] Fixup complete
exit /b 0

:test
echo [TEST] Running pytest...
python -m pytest tests/ -v
exit /b %ERRORLEVEL%

:bootstrap
echo [BOOTSTRAP] Compiling synapse_rt.o...
gcc -c -O2 -msse -msse2 -msse3 "%ROOT_DIR%synapse_rt.c" -o "%ROOT_DIR%synapse_rt.o"
if errorlevel 1 (
    echo [FAIL] synapse_rt.o compilation failed
    exit /b 1
)
echo [OK] synapse_rt.o compiled

echo [BOOTSTRAP] Stage 1: Python -> Native
python "%ROOT_DIR%main.py" "%ROOT_DIR%src\main.syn"
if errorlevel 1 (
    echo [FAIL] Bootstrap Stage 1 failed
    exit /b 1
)
echo [OK] Stage 1 complete (src/main.c + src/main.exe + src/main.syn.json)
exit /b 0

:full
call :clean
call :fixup
call :test
if errorlevel 1 exit /b 1
call :bootstrap
if errorlevel 1 exit /b 1
echo === Full pipeline complete ===
exit /b 0
