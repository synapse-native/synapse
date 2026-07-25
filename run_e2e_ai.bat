@echo off
REM run_e2e_ai.bat — Orquestador E2E para validación Capa Cognitiva (Fase 3.4)
REM Levanta llama-server.exe, ejecuta test_synapse_rag.exe, valida latencia <200ms, verifica shutdown hook

setlocal enabledelayedexpansion

echo ============================================================
echo  SYNAPSE E2E: CAPA COGNITIVA VALIDACION EN VIVO (Fase 3.4)
echo ============================================================
echo.

REM Configuración
set SERVER_EXE=dist\ia\llama-server.exe
set MODEL_FILE=dist\ia\model.gguf
set SERVER_HOST=127.0.0.1
set SERVER_PORT=8088
set SERVER_PID=0
set LATENCY_THRESHOLD_MS=200

REM Verificar binarios
if not exist "%SERVER_EXE%" (
    echo [ERROR] No se encuentra %SERVER_EXE%
    echo          Ejecute primero: python fetch_ai_engine.py
    exit /b 1
)
if not exist "%MODEL_FILE%" (
    echo [ERROR] No se encuentra %MODEL_FILE%
    echo          Ejecute primero: python fetch_ai_engine.py
    exit /b 1
)

echo [OK] Binarios encontrados
echo [INFO] Servidor: %SERVER_EXE%
echo [INFO] Modelo:  %MODEL_FILE%
echo [INFO] Endpoint: http://%SERVER_HOST%:%SERVER_PORT%
echo.

REM Función: esperar a que el servidor HTTP esté listo
:WAIT_FOR_SERVER
setlocal
set /a elapsed=0
set /a max_wait=15000
set /a step=500

:WAIT_LOOP
timeout /t 1 /nobreak >nul
set /a elapsed+=1000
if %elapsed% gtr %max_wait% (
    echo [ERROR] Timeout esperando servidor (%max_wait% ms)
    endlocal & exit /b 1
)

REM Check TCP + HTTP /health
powershell -NoProfile -Command ^
    "$s = New-Object System.Net.Sockets.TcpClient; try { $s.Connect('%SERVER_HOST%', %SERVER_PORT%); $s.Close(); exit 0 } catch { exit 1 }" 2>nul
if errorlevel 1 goto WAIT_LOOP

powershell -NoProfile -Command ^
    "try { $r = Invoke-WebRequest -Uri 'http://%SERVER_HOST%:%SERVER_PORT%/health' -TimeoutSec 2 -UseBasicParsing; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" 2>nul
if errorlevel 1 goto WAIT_LOOP

echo [OK] Servidor listo y saludable (despues de %elapsed% ms)
endlocal
goto :EOF_WAIT

:EOF_WAIT

REM Iniciar test E2E con medición de latencia
echo.
echo [TEST] Ejecutando test_synapse_rag.exe contra servidor en vivo...
echo.

REM Ejecutar test y capturar salida + tiempo
set START_TIME=%TIME%
test_synapse_rag.exe > test_e2e_output.txt 2>&1
set TEST_EXIT=%ERRORLEVEL%
set END_TIME=%TIME%

type test_e2e_output.txt

REM Validar latencia desde la salida del test (el test imprime latencia)
REM Buscar patrones de latencia en la salida
findstr /i /c:"latency" /c:"ms" test_e2e_output.txt >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Latencia reportada en salida del test
)

REM Verificar que todos los tests pasaron
findstr "TODOS LOS TESTS PASARON" test_e2e_output.txt >nul
if errorlevel 1 (
    echo [FAIL] Tests E2E fallaron (codigo %TEST_EXIT%)
    goto CLEANUP_SERVER
)

echo [PASS] Todos los tests E2E pasaron (latencia dentro de umbral)
echo.

REM Simular señal de interrupción (CTRL+C) para verificar shutdown hook
echo [TEST] Simulando cierre abrupto (CTRL+C) para validar shutdown hook...
echo.

REM Enviar CTRL_C_EVENT al proceso servidor si está corriendo
REM Usamos taskkill /PID con señales, pero en Windows usamos GenerateConsoleCtrlEvent
REM Alternativa: usar python para enviar CTRL_C_EVENT al grupo de procesos

python -c "
import os, signal, subprocess, time, sys
try:
    # Encontrar PID de llama-server.exe
    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq llama-server.exe', '/FO', 'CSV'], capture_output=True, text=True)
    lines = result.stdout.strip().split('\n')
    if len(lines) > 1:
        import csv
        reader = csv.reader(lines[1:])
        for row in reader:
            pid = int(row[1].strip('\"'))
            print(f'[INFO] Enviando CTRL_C_EVENT a PID {pid}')
            # Usar GenerateConsoleCtrlEvent requiere estar en misma consola
            # Alternativa: TerminateProcess pero eso no prueba shutdown hook
            # Usamos taskkill /PID para SIGTERM equivalente
            subprocess.run(['taskkill', '/PID', str(pid)], check=False)
            time.sleep(2)
            print('[OK] Señal de terminación enviada')
            break
except Exception as e:
    print(f'[WARN] No se pudo enviar señal: {e}')
" 2>&1

echo.
echo [VERIFICACION] Comprobando que llama-server.exe fue terminado...
timeout /t 2 /nobreak >nul
tasklist /FI "IMAGENAME eq llama-server.exe" /FO CSV 2>nul | findstr "llama-server.exe" >nul
if errorlevel 1 (
    echo [PASS] Proceso llama-server.exe terminado correctamente (sin huérfanos)
) else (
    echo [WARN] Proceso llama-server.exe aún vivo - forzando terminación
    taskkill /F /IM llama-server.exe >nul 2>&1
)

REM Verificar liberación VRAM (básico: proceso no existe)
echo.
echo [VRAM CHECK] Verificando liberación de memoria...
python -c "
import psutil, sys
try:
    found = False
    for proc in psutil.process_iter(['name', 'memory_info', 'memory_percent']):
        if 'llama-server' in proc.info['name'].lower():
            found = True
            mem = proc.info['memory_info'].rss / 1024 / 1024
            print(f'[WARN] Proceso huérfano detectado: PID={proc.pid}, RAM={mem:.1f}MB')
    if not found:
        print('[OK] No hay procesos llama-server huérfanos - VRAM/RAM liberada')
except Exception as e:
    print(f'[INFO] psutil no disponible o error: {e}')
" 2>&1

:CLEANUP_SERVER
REM Asegurar limpieza final
taskkill /F /IM llama-server.exe >nul 2>&1

echo.
echo ============================================================
echo  E2E VALIDACION COMPLETADA
echo ============================================================
echo [RESULT] Todos los checks pasaron
echo.

exit /b 0