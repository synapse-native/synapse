@echo off
REM opensyn.bat — Wrapper para comando opensyn (Manual 9 §2.5, Manual 7 §6)
REM Arranca llama-server automaticamente si no esta corriendo.
setlocal EnableDelayedExpansion

REM SYNAPSE_HOME = raiz de instalacion (padre de opensyn/ o bin/)
set SYNAPSE_HOME=%~dp0..
set OPENSYN_DIR=%~dp0
set BIN_DIR=%SYNAPSE_HOME%\bin
set IA_DIR=%OPENSYN_DIR%ia
set MODELS_DIR=%OPENSYN_DIR%models

REM Buscar opensyn.exe en bin/ o en el directorio actual
set OPENSYN_EXE=
if exist "%BIN_DIR%\opensyn.exe" (
    set "OPENSYN_EXE=%BIN_DIR%\opensyn.exe"
) else if exist "%OPENSYN_DIR%opensyn.exe" (
    set "OPENSYN_EXE=%OPENSYN_DIR%opensyn.exe"
) else (
    where opensyn >nul 2>&1
    if not errorlevel 1 (
        opensyn.exe %*
        exit /b %errorlevel%
    )
    echo [ERROR] opensyn.exe no encontrado
    exit /b 1
)

REM Verificar si llama-server ya esta corriendo en puerto 8088
netstat -an 2>nul | findstr ":8088 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    goto :run_opensyn
)

REM Buscar modelo GGUF en models/ o ia/
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
start "llama-server" /B "%IA_DIR%\llama-server.exe" --model "%MODEL_PATH%" --port 8088 --host 0.0.0.0 --ctx-size 2048 --n-gpu-layers 0

REM Esperar a que el servidor este listo (max 15 segundos)
set WAIT=0
:wait_loop
if %WAIT% GEQ 15 goto :run_opensyn
netstat -an 2>nul | findstr ":8088 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [OpenSyn] llama-server listo en puerto 8088
    goto :run_opensyn
)
timeout /t 1 /nobreak >nul
set /a WAIT+=1
goto :wait_loop

:run_opensyn
"%OPENSYN_EXE%" %*
