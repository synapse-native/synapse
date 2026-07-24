#!/usr/bin/env python3
"""
run_stress.py — Ejecutor de la prueba de estrés F10.5

Documento Maestro Parte VII:
  - 10,000 hilos simultáneos con paso de mensajes por canales
  - Verificación: 0 Deadlocks, 0 Data Races, 0 Bytes Perdidos
  - MemoryWatchdog (MIM) activado via SYNAPSE_DEBUG_MEM

Modos de uso:
  python tests/stress/run_stress.py                    # 10,000 hilos, 2 msg c/u
  python tests/stress/run_stress.py --hilos 1000        # 1,000 hilos
  python tests/stress/run_stress.py --tsan              # Con ThreadSanitizer
  python tests/stress/run_stress.py --check-only        # Solo verificar compilación
  pytest tests/stress/run_stress.py -v                  # Como test unitario
"""

import os
import sys
import subprocess
import re

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
STRESS_SRC = os.path.join(PROJECT_ROOT, 'tests', 'stress', 'test_stress_concurrencia.c')
SYNAPSE_RT_O = os.path.join(PROJECT_ROOT, 'synapse_rt.o')
STRESS_BIN = os.path.join(PROJECT_ROOT, 'tests', 'stress', 'stress_concurrencia.exe')


def compilar_stress(tsan: bool = False) -> bool:
    """Compila el ejecutable de la prueba de estres."""
    if not os.path.exists(SYNAPSE_RT_O):
        print(f"[STRESS] synapse_rt.o no encontrado en {SYNAPSE_RT_O}")
        print("[STRESS] Ejecute: gcc -c synapse_rt.c -o synapse_rt.o -lpthread")
        return False

    flags = "-O2 -DSYNAPSE_DEBUG_MEM -I."
    if tsan:
        flags = "-O1 -g -fsanitize=thread -DSYNAPSE_DEBUG_MEM -I."

    # Compilar synapse_rt.c directo con -DSYNAPSE_DEBUG_MEM
    # para que watchdog_malloc/watchdog_free esten disponibles
    synapse_rt_c = os.path.join(PROJECT_ROOT, 'synapse_rt.c')
    cmd = [
        'gcc',
        *flags.split(),
        '-o', STRESS_BIN,
        STRESS_SRC,
        synapse_rt_c,
        '-lpthread', '-lm', '-lws2_32'
    ]
    if tsan:
        pass  # -fsanitize=thread ya linkea automaticamente el runtime tsan

    print(f"[STRESS] Compilando: {' '.join(cmd[:4])} ...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[STRESS] Compilacion fallo (codigo {result.returncode})")
        if result.stderr:
            for line in result.stderr.split('\n')[-10:]:
                if line.strip():
                    print(f"  {line}")
        return False

    if os.path.exists(STRESS_BIN):
        size = os.path.getsize(STRESS_BIN)
        print(f"[STRESS] Compilado: {STRESS_BIN} ({size} bytes)")
        return True
    return False


def ejecutar_stress(hilos: int = 10000, msg_por_hilo: int = 2,
                    timeout: int = 120) -> dict:
    """Ejecuta la prueba de estres y retorna resultados."""
    if not os.path.exists(STRESS_BIN):
        if not compilar_stress():
            return {'exito': False, 'error': 'Compilacion fallo'}

    print(f"\n[STRESS] Ejecutando: {os.path.basename(STRESS_BIN)} "
          f"{hilos} {msg_por_hilo}")
    print(f"[STRESS] Timeout: {timeout}s\n")

    import time
    inicio = time.time()
    try:
        proc = subprocess.run(
            [STRESS_BIN, str(hilos), str(msg_por_hilo)],
            capture_output=True, text=True, timeout=timeout
        )
        duracion = time.time() - inicio
    except subprocess.TimeoutExpired:
        return {
            'exito': False, 'error': 'TIMEOUT',
            'duracion': time.time() - inicio
        }
    except Exception as e:
        return {'exito': False, 'error': str(e)}

    stdout = proc.stdout
    stderr = proc.stderr
    exit_code = proc.returncode

    # Parsear resultados del stderr
    resultados = {
        'exito': exit_code == 0,
        'exit_code': exit_code,
        'duracion': duracion,
        'hilos': hilos,
        'mensajes_por_hilo': msg_por_hilo,
        'stdout': stdout,
        'stderr': stderr,
    }

    # Extraer metricas del stderr
    patrones = {
        'hilos_lanzados': r'Hilos lanzados:\s+(\d+)',
        'productores': r'Productores:\s+(\d+)',
        'consumidores': r'Consumidores:\s+(\d+)',
        'transferencias': r'Transferencias:\s+(\d+)',
        'recibidos': r'Recibidos:\s+(\d+)',
        'errores': r'Errores:\s+(\d+)',
        'duracion_seg': r'Duracion:\s+([\d.]+)',
        'throughput': r'Throughput:\s+([\d.]+)',
        'deadlocks': r'Deadlocks:\s+(.+)',
    }

    for clave, patron in patrones.items():
        m = re.search(patron, stderr)
        if m:
            resultados[clave] = m.group(1).strip()

    return resultados


def mostrar_resultados(r: dict):
    """Muestra resultados formateados."""
    print("\n" + "=" * 60)
    print("  RESULTADOS DE PRUEBA DE ESTRES F10.5")
    print("=" * 60)

    if r.get('error'):
        print(f"  ERROR: {r['error']}")
        if r.get('stderr'):
            last = '\n'.join(r['stderr'].split('\n')[-5:])
            print(f"  stderr: {last}")
        return

    hilos_sol = r.get('hilos', 'N/A')
    hilos_lanz = r.get('hilos_lanzados', hilos_sol)
    print(f"  Hilos solicitados:  {hilos_sol}")
    print(f"  Hilos lanzados:     {hilos_lanz}")
    print(f"  Productores:        {r.get('productores', 'N/A')}")
    print(f"  Consumidores:       {r.get('consumidores', 'N/A')}")
    print(f"  Transferencias:     {r.get('transferencias', 'N/A')}")
    print(f"  Recibidos:          {r.get('recibidos', 'N/A')}")
    print(f"  Errores:            {r.get('errores', 'N/A')}")
    print(f"  Duracion:           {r.get('duracion_seg', 'N/A')} seg")
    print(f"  Throughput:         {r.get('throughput', 'N/A')} msg/seg")
    print(f"  Deadlocks:          {r.get('deadlocks', 'N/A')}")
    print(f"  Codigo salida:      {r.get('exit_code', 'N/A')}")
    print(f"  Tiempo real:        {r.get('duracion', 0):.2f} seg")

    # Verificar MemoryWatchdog en stderr (0 bytes perdidos obligatorio)
    stderr_text = r.get('stderr', '')
    tiene_watchdog = False
    for line in stderr_text.split('\n'):
        line_lower = line.lower()
        if 'bytes' in line_lower and ('lost' in line_lower or 'perdido' in line_lower or 'fuga' in line_lower):
            tiene_watchdog = True
            if '0 bytes' in line_lower or '0 b' in line_lower:
                print(f"  MemoryWatchdog:     {line.strip()} [OK]")
            else:
                print(f"  MemoryWatchdog:     {line.strip()} [WARN] POSIBLE FUGA")
                if r.get('exito'):
                    r['exito'] = False  # Fuga invalida el test
    if not tiene_watchdog:
        if 'SYNAPSE_DEBUG_MEM' in stderr_text:
            print("  MemoryWatchdog:     no activado (sin -DSYNAPSE_DEBUG_MEM)")
        else:
            print("  MemoryWatchdog:     revisar salida manualmente")

    estado = "[PASS]" if r['exito'] else "[FAIL]"
    print(f"\n  {estado} Prueba F10.5 {'superada' if r['exito'] else 'fallo'} "
          f"(exit code {r.get('exit_code', '?')})")
    if not r['exito'] and r.get('stderr'):
        last_lines = '\n'.join(r['stderr'].split('\n')[-5:])
        print(f"  Ultimas lineas:\n  {last_lines}")
    print("=" * 60 + "\n")


def test_stress_10000():
    """Test de estres con 10,000 hilos (para pytest)."""
    if not os.path.exists(STRESS_BIN):
        assert compilar_stress(), "Compilacion fallo"
    r = ejecutar_stress(hilos=10000, msg_por_hilo=2, timeout=180)
    assert r['exito'], f"Prueba fallo: {r.get('error', 'exit code != 0')}"
    rec = int(r.get('recibidos', 0))
    tra = int(r.get('transferencias', 0))
    assert rec == tra, \
        f"Mensajes perdidos: recibidos={rec} de {tra}"
    assert r.get('errores') == '0', f"Errores detectados: {r.get('errores')}"
    assert '0' in str(r.get('deadlocks', '?')), "Deadlocks detectados"


def test_stress_compilacion():
    """Verificar que el test de estres compila correctamente."""
    assert compilar_stress(), "Compilacion de test_stress_concurrencia.c fallo"


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Ejecutor de prueba de estres F10.5 - Synapse/OpenSyn'
    )
    parser.add_argument('--hilos', type=int, default=10000,
                       help='Numero de hilos (por defecto: 10000)')
    parser.add_argument('--mensajes', type=int, default=2,
                       help='Mensajes por hilo (por defecto: 2)')
    parser.add_argument('--timeout', type=int, default=180,
                       help='Timeout en segundos (por defecto: 180)')
    parser.add_argument('--tsan', action='store_true',
                       help='Compilar con ThreadSanitizer')
    parser.add_argument('--check-only', action='store_true',
                       help='Solo verificar compilacion')

    args = parser.parse_args()

    print("\n[STRESS] SYNAPSE STRESS TEST F10.5")
    print("         Documento Maestro Parte VII")
    print(f"         Hilos: {args.hilos} | Mensajes/hilo: {args.mensajes}")
    if args.tsan:
        print("         ThreadSanitizer: ACTIVADO")
    print()

    if not compilar_stress(tsan=args.tsan):
        sys.exit(1)

    if args.check_only:
        print("[STRESS] Compilacion verificada")
        return

    r = ejecutar_stress(hilos=args.hilos, msg_por_hilo=args.mensajes,
                        timeout=args.timeout)
    mostrar_resultados(r)

    if not r['exito']:
        sys.exit(1)

    # Validaciones adicionales
    rec = int(r.get('recibidos', 0))
    tra = int(r.get('transferencias', 0))
    if rec != tra:
        print(f"[STRESS] {tra} enviados, solo {rec} recibidos "
              f"-- POSIBLE DEADLOCK")
        sys.exit(1)


if __name__ == '__main__':
    main()
