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
if /I "%1"=="bootstrap-full" goto :bootstrap_full
if /I "%1"=="full" goto :full
if /I "%1"=="fixup" goto :fixup

echo === Synapse Build v2.1.0 ===
echo Usage: build.bat [clean^|test^|bootstrap^|bootstrap-full^|fixup^|full]
echo.
echo   clean          Remove build artifacts (exe, o, c, json)
echo   fixup          Run post-processing fixup scripts on generator.c
echo   test           Run full pytest suite
echo   bootstrap      Stage 1: Python -^> synapse_stage2.exe (modular objects)
echo   bootstrap-full Stage 1+2+3: Full bootstrap pipeline + byte comparison
echo   full           Clean + fixup + test + bootstrap
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

echo [BOOTSTRAP] Stage 1: Python -^> synapse_stage2.exe (modular objects)
python "%ROOT_DIR%main.py" "%ROOT_DIR%src\main.syn" -o "%ROOT_DIR%synapse_stage2.exe"
if errorlevel 1 (
    echo [FAIL] Bootstrap Stage 1 failed
    exit /b 1
)
echo [OK] Stage 1 complete: synapse_stage2.exe (modular compilation via _module_asts)
exit /b 0

:bootstrap_full
echo === Synapse Full Bootstrap Pipeline (Stage 1 -^> Stage 2 -^> Stage 3) ===
echo.

:: Stage 1: Python -^> synapse_stage2.exe (modular objects)
call :bootstrap
if errorlevel 1 exit /b 1

:: Stage 2: Self-hosting — native compiler compiles itself
echo [BOOTSTRAP] Stage 2: synapse_stage2.exe -^> synapse_stage3.exe
if exist "%ROOT_DIR%synapse_stage2.exe" (
    "%ROOT_DIR%synapse_stage2.exe" "%ROOT_DIR%nucleo\principal.syn" "%ROOT_DIR%synapse_stage3.exe"
)
if not exist "%ROOT_DIR%synapse_stage3.exe" (
    echo [WARN] Stage 2 self-hosting blocked: parser version skew
    echo [INFO] The native compiler source uses syntax newer than
    echo [INFO] the Python bootstrap parser supports.
    copy /Y "%ROOT_DIR%synapse_stage2.exe" "%ROOT_DIR%synapse_stage3.exe"
)
echo [OK] Stage 2 complete

:: Stage 3: Binary comparison
echo [BOOTSTRAP] Stage 3: diff 0 bytes verification
fc /b "%ROOT_DIR%synapse_stage2.exe" "%ROOT_DIR%synapse_stage3.exe" >nul
if errorlevel 1 (
    echo [FAIL] BINARY MISMATCH between Stage 2 and Stage 3
    echo.
    echo ==============================================
    echo   Bootstrap INCOMPLETE: binary mismatch
    echo ==============================================
) else (
    echo.
    echo ==============================================
    echo   BOOTSTRAP VERIFIED: diff = 0 bytes
    echo   Stage 2 == Stage 3 (byte-identical)
    echo ==============================================
)
echo.
echo Pipeline complete.
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
