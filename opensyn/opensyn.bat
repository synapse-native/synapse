@echo off
REM opensyn.bat — Wrapper del comando opensyn (Manual 9 §2.5, Manual 7 §2.1)
REM El orquestador opensyn.exe gestiona el ciclo de vida de llama-server:
REM resuelve {app}\opensyn\ia|models desde el directorio real del binario.
setlocal

set "BIN_DIR=%~dp0"
if "%BIN_DIR:~-1%"=="\" set "BIN_DIR=%BIN_DIR:~0,-1%"
set "OPENSYN_EXE=%BIN_DIR%\opensyn.exe"

if not exist "%OPENSYN_EXE%" set "OPENSYN_EXE=%BIN_DIR%\..\bin\opensyn.exe"
if not exist "%OPENSYN_EXE%" set "OPENSYN_EXE=%BIN_DIR%\..\opensyn\opensyn.exe"
if not exist "%OPENSYN_EXE%" (
    for %%I in (opensyn.exe) do if not "%%~$PATH:I"=="" set "OPENSYN_EXE=%%~$PATH:I"
)
if not exist "%OPENSYN_EXE%" (
    echo [ERROR] opensyn.exe no encontrado
    exit /b 1
)

"%OPENSYN_EXE%" %*
exit /b %errorlevel%
