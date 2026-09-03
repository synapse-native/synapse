@echo off
REM opensyn.bat — Wrapper para comando opensyn (Manual 9 §2.5, Manual 7 §6)
REM Uso: opensyn [status|chat|explain|...]
setlocal

set SYNAPSE_BIN=%~dp0
if exist "%SYNAPSE_BIN%synapse.exe" (
    "%SYNAPSE_BIN%synapse.exe" opensyn principal.syn %*
) else (
    where synapse >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] synapse.exe no encontrado en PATH
        exit /b 1
    )
    synapse.exe opensyn principal.syn %*
)
