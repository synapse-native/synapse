@echo off
REM opensyn.bat — Wrapper para comando opensyn (Manual 9 §2.5, Manual 7 §6)
REM Uso: opensyn [status|chat|explain|...]
setlocal

set SYNAPSE_BIN=%~dp0
if exist "%SYNAPSE_BIN%opensyn.exe" (
    "%SYNAPSE_BIN%opensyn.exe" %*
) else if exist "%SYNAPSE_BIN%synapse.exe" (
    "%SYNAPSE_BIN%synapse.exe" "%~dp0..\opensyn\principal.syn" %*
) else (
    where opensyn >nul 2>&1
    if not errorlevel 1 (
        opensyn.exe %*
        exit /b %errorlevel%
    )
    where synapse >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] synapse.exe no encontrado en PATH
        exit /b 1
    )
    synapse.exe "%~dp0..\opensyn\principal.syn" %*
)
