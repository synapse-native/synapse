@echo off
REM opensyn.bat — Wrapper para comando opensyn (Manual 9 §2.5, Manual 7 §6)
REM Arranca llama-server automaticamente si no esta corriendo.
setlocal EnableDelayedExpansion

set SYNAPSE_BIN=%~dp0
set IA_DIR=%SYNAPSE_BIN%ia
set MODELS_DIR=%SYNAPSE_BIN%models

REM Verificar si llama-server ya esta corriendo en puerto 11434
netstat -an 2>nul | findstr ":11434 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    goto :run_opensyn
)

REM Buscar modelo GGUF en models/
set MODEL_PATH=
for %%f in ("%MODELS_DIR%\*.gguf") do (
    set MODEL_PATH=%%f
    goto :found_model
)
for %%f in ("%IA_DIR%\*.gguf") do (
    set MODEL_PATH=%%f
    goto :found_model
)

REM No hay modelo: continuar sin servidor IA
echo [OpenSyn] No se encontro modelo GGUF en ia/ o models/
goto :run_opensyn

:found_model
REM Verificar que llama-server.exe existe
if not exist "%IA_DIR%\llama-server.exe" (
    echo [OpenSyn] llama-server.exe no encontrado en ia/
    goto :run_opensyn
)

echo [OpenSyn] Iniciando llama-server con modelo: %MODEL_PATH%
start "llama-server" /B "%IA_DIR%\llama-server.exe" --model "%MODEL_PATH%" --port 11434 --host 0.0.0.0 --ctx-size 2048 --n-gpu-layers 0

REM Esperar a que el servidor este listo (max 15 segundos)
set WAIT=0
:wait_loop
if %WAIT% GEQ 15 goto :run_opensyn
netstat -an 2>nul | findstr ":11434 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [OpenSyn] llama-server listo en puerto 11434
    goto :run_opensyn
)
timeout /t 1 /nobreak >nul
set /a WAIT+=1
goto :wait_loop

:run_opensyn
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
