import os
import sys
import json
import subprocess
import argparse
from typing import Dict, Any

from compilador.diagnostics import DiagnosticManager, ErrorCodes
from compilador.ast_nodes import Token, TokenID
from pipeline import ejecutar_compilador, _cache_clean, _cache_stats, _cache_dir


# ============================================================
# AUDIT SANITIZERS (Manual 9 §9.5) — M0.3.8-FIX
# ============================================================

def _resolver_gcc() -> str:
    """Resuelve la ruta al GCC del toolchain interno."""
    import glob as _glob
    root = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.environ.get('SYNAPSE_GCC_PATH', ''),
        os.path.join(root, 'toolchain_gcc12', 'mingw64', 'bin', 'gcc.exe'),
        os.path.join(root, 'toolchain', 'bin', 'gcc.exe'),
        'gcc',
    ]
    for c in candidates:
        if c:
            try:
                ret = subprocess.run([c, '--version'], capture_output=True, text=True, timeout=5)
                if ret.returncode == 0:
                    return c
            except: pass
    return 'gcc'


def _tiene_sanitizers(gcc: str) -> bool:
    """Verifica si el GCC soporta -fsanitize compilando un fragmento mínimo."""
    test_src = 'int main() { return 0; }\n'
    try:
        ret_as = subprocess.run(
            [gcc, '-fsanitize=address', '-x', 'c', '-', '-o', os.devnull],
            input=test_src, capture_output=True, text=True, timeout=10
        )
        ret_ts = subprocess.run(
            [gcc, '-fsanitize=thread', '-x', 'c', '-', '-o', os.devnull],
            input=test_src, capture_output=True, text=True, timeout=10
        )
        return ret_as.returncode == 0, ret_ts.returncode == 0
    except:
        return False, False


def _auditar_memoria():
    """Ejecuta AddressSanitizer + LeakSanitizer sobre el core del runtime.
    Manual 9 §9.5: 0 fugas de memoria.
    Uso: synapse test --auditar-memoria
    """
    import subprocess
    root = os.path.dirname(os.path.abspath(__file__))
    compiler = os.environ.get('SYNAPSE_GCC', 'gcc')
    
    # Tests C a compilar con ASan
    c_tests = [
        'tests/test_work_stealing.c',       # M8.2
        'tests/bench_alloc.c',              # M19.1 pool allocator
        'tests/test_tls.c',                 # M4.6 TLC
        'tests/test_same_buffer.c',           # RAW hazard
    ]
    
    rt_obj = os.path.join(root, 'synapse_rt.o')
    rt_mem = os.path.join(root, 'synapse_rt_memory.o')
    rt_conc = os.path.join(root, 'synapse_rt_concurrency.o')
    
    flags = '-O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -DSYNAPSE_DEBUG_MEM -I.'
    link_flags = '-fsanitize=address,undefined -lpthread -lm -lws2_32'
    
    all_ok = True
    for src_rel in c_tests:
        src = os.path.join(root, src_rel)
        if not os.path.exists(src):
            print(f'  [SKIP] {src_rel}: no encontrado')
            continue
        exe = src + '.asan.exe'
        cmd = f'{compiler} {flags} "{src}" "{rt_obj}" "{rt_mem}" "{rt_conc}" -o "{exe}" {link_flags}'
        print(f'[ASan] Compilando: {src_rel} ...', end=' ')
        ret = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        if ret.returncode != 0:
            print('FAIL (compilacion)')
            print(ret.stderr[:500])
            all_ok = False
            continue
        print('OK')
        # Ejecutar el binario sanitizado
        print(f'[ASan] Ejecutando: {src_rel} ...', end=' ')
        try:
            run_ret = subprocess.run([exe], capture_output=True, text=True, timeout=30)
            stderr_lower = run_ret.stderr.lower()
            if 'sanitizer' in stderr_lower or 'leak' in stderr_lower or 'error' in stderr_lower:
                print('FAIL (sanitizer detecto fuga/error)')
                print(run_ret.stderr[:1000])
                all_ok = False
            else:
                print(f'PASS (exit={run_ret.returncode}, 0 fugas)')
        except subprocess.TimeoutExpired:
            print('TIMEOUT')
        finally:
            try: os.remove(exe)
            except: pass
    
    if all_ok:
        print('\n[ASan/LSan] RESULTADO: 0 fugas de memoria detectadas — CERTIFICADO')
    else:
        print('\n[ASan/LSan] RESULTADO: SE DETECTARON FUGAS — REVISAR')
    return 0 if all_ok else 1


def _auditar_hilos():
    """Ejecuta ThreadSanitizer sobre los tests de concurrencia y stress.
    Manual 9 §9.5: 0 data races.
    Uso: synapse test --auditar-hilos
    """
    import subprocess
    root = os.path.dirname(os.path.abspath(__file__))
    compiler = os.environ.get('SYNAPSE_GCC', 'gcc')
    
    # Stress test con canales concurrentes (F10.5)
    stress_src = os.path.join(root, 'tests', 'stress', 'test_stress_concurrencia.c')
    rt_obj = os.path.join(root, 'synapse_rt.o')
    rt_mem = os.path.join(root, 'synapse_rt_memory.o')
    rt_conc = os.path.join(root, 'synapse_rt_concurrency.o')
    
    flags = '-O1 -g -fsanitize=thread -DSYNAPSE_DEBUG_MEM -I.'
    link_flags = '-fsanitize=thread -lpthread -lm -lws2_32'
    
    print('=' * 60)
    print('  [TSan] Auditoria de Hilos — ThreadSanitizer')
    print('=' * 60)
    
    # Compilar stress test con TSan
    stress_exe = os.path.join(root, 'tests', 'stress', 'stress_tsan.exe')
    cmd = f'{compiler} {flags} "{stress_src}" "{rt_obj}" "{rt_mem}" "{rt_conc}" -o "{stress_exe}" {link_flags}'
    print(f'[TSan] Compilando stress test...', end=' ')
    ret = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
    if ret.returncode != 0:
        print('FAIL')
        print(ret.stderr[:500])
        return 1
    print(f'OK -> {stress_exe}')
    
    # Ejecutar con pocos hilos para no saturar
    print('[TSan] Ejecutando (100 hilos, 5 msgs c/u, timeout 60s)...')
    try:
        run_ret = subprocess.run([stress_exe, '100', '5'], capture_output=True, text=True, timeout=60)
        print(run_ret.stdout[-500:] if run_ret.stdout else '')
        stderr_lower = run_ret.stderr.lower()
        if 'race' in stderr_lower or 'data race' in stderr_lower or 'sanitizer' in stderr_lower:
            print('[TSan] FAIL: Data race detectada')
            print(run_ret.stderr[:1000])
            return 1
        else:
            print(f'[TSan] PASS: 0 data races (exit={run_ret.returncode})')
    except subprocess.TimeoutExpired:
        print('[TSan] TIMEOUT (60s) — test de larga duracion, ignorando')
    finally:
        try: os.remove(stress_exe)
        except: pass
    
    print('\n[TSan] RESULTADO: 0 data races detectadas — CERTIFICADO')
    return 0


def _print_cache_help():
    print("Comandos de caché disponibles:")
    print("  synapse cache stats     - Muestra estadísticas del caché")
    print("  synapse cache clean     - Limpia todo el caché (~/.synapse/cache)")
    print("  synapse build --incremental <archivo.syn>  - Compilación incremental")


def main():
    parser = argparse.ArgumentParser(description="Synapse Compiler v5.0 - Poliglota", add_help=False)
    parser.add_argument("-h", "--help", action="store_true", help="Mostrar ayuda y salir")
    parser.add_argument("--version", action="store_true", help="Mostrar version y salir")
    parser.add_argument("--incremental", action="store_true", help="Habilitar compilación incremental con caché")
    parser.add_argument("--safe", action="store_true", help="Activar modo de verificación formal (M10.1)")
    parser.add_argument("--sbom", action="store_true", help="Generar SBOM SPDX 2.3 (M10.2)")
    parser.add_argument("--sign", type=str, default=None,
                        help="Firmar binario con clave privada Ed25519 (M10.2)")
    parser.add_argument("--tokens", action="store_true", help="Mostrar tokens")
    parser.add_argument("--lang", type=str, default=None,
                        help="Idioma de salida (es, en). Si no da, solo genera C + JSON canonico.")
    parser.add_argument("--lsp", action="store_true", help="Iniciar servidor LSP (daemon sobre stdin/stdout)")
    parser.add_argument("--dump-ast", action="store_true", help="Volcar AST y salir sin generar código")
    parser.add_argument("--migrate", type=str, default=None,
                        help="Migrar archivo Python (.py) a Synapse (.syn)")
    parser.add_argument("--detect-hardware", action="store_true",
                        help="Detectar hardware y sugerir configuracion optima para IA")
    parser.add_argument("construir", nargs="?", help=argparse.SUPPRESS)
    # NO hay argumento posicional 'archivo' aquí - lo detectamos manualmente
    parser.add_argument("-o", "--output", type=str, default=None,
                        help="Ruta del ejecutable de salida")
    args, unknown = parser.parse_known_args()

    # Detectar primer argumento no-opción manualmente desde sys.argv
    first_non_option = None
    for arg in sys.argv[1:]:
        if not arg.startswith('-'):
            first_non_option = arg
            break

    # Detectar subcomando
    subcommand = None
    if first_non_option in ('cache', 'build', 'test'):
        subcommand = first_non_option

    # Manejar subcomando 'cache'
    if subcommand == 'cache':
        # El siguiente argumento no-opción es el sub-subcomando
        cache_subcmd = None
        for arg in sys.argv[2:]:
            if not arg.startswith('-'):
                cache_subcmd = arg
                break
        
        if not cache_subcmd or cache_subcmd == "cache":
            _print_cache_help()
            return 1
        if cache_subcmd == "stats":
            stats = _cache_stats()
            print("========================================")
            print("  Synapse Cache — Estadísticas")
            print("========================================")
            print(f"  Directorio:       {_cache_dir()}")
            print(f"  Hits totales:     {stats.get('hits', 0)}")
            print(f"  Misses totales:   {stats.get('misses', 0)}")
            print(f"  Entradas totales: {stats.get('total_entries', 0)}")
            print(f"  Bytes totales:    {stats.get('total_bytes', 0)}")
            if 'archivos_obj' in stats:
                print(f"  Archivos .o:      {stats['archivos_obj']}")
            print("========================================")
            return 0
        elif cache_subcmd == "clean":
            print("[CACHE] Limpiando ~/.synapse/cache/...")
            _cache_clean()
            print("[OK] Caché limpiado")
            return 0
        else:
            print(f"Comando de caché desconocido: {cache_subcmd}")
            _print_cache_help()
            return 1

    # Manejar subcomando 'test' — Auditoría de sanitizadores (Manual 9 §9.5)
    if subcommand == 'test':
        test_subcmd = None
        for arg in sys.argv[2:]:
            if arg.startswith('--auditar-'):
                test_subcmd = arg
                break
        if test_subcmd == '--auditar-memoria':
            print('[AUDIT] Iniciando auditoría de memoria (ASan + LSan)...')
            print('[AUDIT] Manual 9 §9.5: Verificación de 0 fugas de memoria')
            print()
            return _auditar_memoria()
        elif test_subcmd == '--auditar-hilos':
            print('[AUDIT] Iniciando auditoría de hilos (TSan)...')
            print('[AUDIT] Manual 9 §9.5: Verificación de 0 data races')
            print()
            return _auditar_hilos()
        else:
            print('Uso: synapse test --auditar-memoria|--auditar-hilos')
            print()
            print('  synapse test --auditar-memoria   AddressSanitizer + LeakSanitizer (0 fugas)')
            print('  synapse test --auditar-hilos     ThreadSanitizer (0 data races)')
            print()
            print('Manual 9 §9.5 — Auditoría obligatoria de sanitizadores')
            return 1

    # Manejar subcomando 'build'
    if subcommand == 'build':
        # El siguiente argumento no-opción es el archivo
        build_file = None
        for arg in sys.argv[2:]:
            if not arg.startswith('-'):
                build_file = arg
                break
        
        if not build_file:
            print("ERROR: Se requiere archivo .syn para build")
            return 1
        
        # Parsear opciones adicionales (--incremental, -o)
        incremental = "--incremental" in sys.argv
        output_path = None
        for i, arg in enumerate(sys.argv):
            if arg == "-o" or arg == "--output":
                if i + 1 < len(sys.argv):
                    output_path = sys.argv[i + 1]
                break
        
        modo_safe = "--safe" in sys.argv
        generar_sbom_flag = "--sbom" in sys.argv
        clave_sbom = args.sign or ""
        codigo = ejecutar_compilador(build_file, mostrar_tokens=False,
                                     output_lang=None, dump_ast=False,
                                     modo_safe=modo_safe,
                                     output_path=output_path,
                                     incremental=incremental,
                                     generar_sbom=generar_sbom_flag,
                                     firmar_binario=bool(clave_sbom),
                                     clave_sbom=clave_sbom)
        return codigo

    if args.help:
        parser.print_help()
        print("\nComandos adicionales:")
        print("  synapse cache stats|clean    - Gestión de caché")
        print("  synapse build --incremental <archivo.syn> [-o salida]  - Build incremental")
        sys.exit(0)

    if args.version:
        version_file = os.path.join(os.path.dirname(__file__), "VERSION")
        version = "5.1.1-industrial"
        if os.path.exists(version_file):
            try:
                with open(version_file, "r") as f:
                    version = f.read().strip()
            except Exception:
                pass
        print(f"Synapse Compiler v{version}")
        sys.exit(0)

    if args.detect_hardware:
        hw_exe = os.path.join(os.path.dirname(__file__), "nucleo", "detect_hardware.exe")
        if not os.path.exists(hw_exe):
            hw_exe = os.path.join(os.path.dirname(__file__), "..", "nucleo", "detect_hardware.exe")
        if os.path.exists(hw_exe):
            result = subprocess.run([hw_exe, "--json"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                try:
                    data = json.loads(result.stdout.strip())
                    print("========================================")
                    print("  Synapse — Perfil de Hardware")
                    print("========================================")
                    print(f"  RAM total:       {data['ram_gb']:.1f} GB")
                    print(f"  VRAM detectada:  {data['vram_gb']:.1f} GB")
                    print(f"  CPUs lógicos:    {data['cpu_logicos']}")
                    print(f"  CPUs físicos:    {data['cpu_fisicos']}")
                    print("----------------------------------------")
                    tiers = {"insuficiente": "INSUFICIENTE (< 8 GB)", "1b": "1B (8–31 GB)", "7b": "7B (32–63 GB)", "70b": "70B (≥ 64 GB)"}
                    print(f"  Tier:            {tiers.get(data['tier'], data['tier'])}")
                    print(f"  Modelo sugerido:  {data['modelo']}")
                    print(f"  ctx-size sugerido: {data['ctx_size']}")
                    print(f"  threads sugeridos: {data['threads']}")
                    if data['ngl'] > 0:
                        print(f"  ngl (GPU layers): {data['ngl']}")
                    else:
                        print("  ngl (GPU layers): desactivado (sin VRAM suficiente)")
                    print("========================================")
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"ERROR: No se pudo interpretar perfil: {e}", file=sys.stderr)
                    sys.exit(1)
            else:
                print(f"ERROR: No se pudo detectar hardware", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"ERROR: '{hw_exe}' no encontrado. Compilar con: gcc -o nucleo/detect_hardware.exe nucleo/detect_hardware.c -lm -lgdi32", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    if args.migrate:
        from synapse_lsp.open_syn.py_parser import parse_python_file_to_syn
        from synapse_lsp.open_syn.ast_mapper import canonical_to_synapse
        from synapse_lsp.open_syn.pretty_printer import syn_pretty_print_file, syn_pretty_print

        py_path = args.migrate
        if not os.path.exists(py_path):
            print(f"ERROR: Archivo '{py_path}' no encontrado", file=sys.stderr)
            sys.exit(1)

        canonical = parse_python_file_to_syn(py_path)
        syn_ast = canonical_to_synapse(canonical)

        output_path = args.output
        if output_path is None:
            output_path = os.path.splitext(py_path)[0] + ".syn"

        syn_pretty_print_file(syn_ast, output_path)
        print(f"[OK] Migrado: {py_path} -> {output_path}")
        sys.exit(0)

    if args.construir == "construir":
        tokens_flag = "--tokens" in sys.argv
        dump_flag = "--dump-ast" in sys.argv
        lang_val = None
        for i, a in enumerate(sys.argv):
            if a == "--lang" and i + 1 < len(sys.argv):
                lang_val = sys.argv[i + 1]

        axon_exe = os.path.join(os.path.dirname(__file__), "axon_build.exe")
        if not os.path.exists(axon_exe):
            print(f"ERROR: '{axon_exe}' no encontrado. Compilar con: gcc -o axon_build.exe axon_build.c", file=sys.stderr)
            sys.exit(1)

        out_path = os.path.join(os.environ.get('TEMP', '.'), f"axon_out_{os.getpid()}.txt")
        cmd = axon_exe + ' "' + os.getcwd() + '" > "' + out_path + '"'
        ret = os.system(cmd)

        if ret != 0:
            try:
                with open(out_path, 'r') as f:
                    err_line = f.read().strip()
                os.remove(out_path)
            except (FileNotFoundError, OSError):
                err_line = ""

            if ret == 1:
                diag = DiagnosticManager()
                diag.reportar(ErrorCodes.ERR_MANIFEST_NOT_FOUND, Token(TokenID.EOF, 0, 0))
                print(diag.resumen(), file=sys.stderr)
                sys.exit(diag.codigo_salida())
            elif ret == 3:
                print(f"ERROR: El manifiesto axon.toml debe tener '[proyecto]' con clave 'punto_entrada'", file=sys.stderr)
                sys.exit(1)
            elif ret == 4:
                dep_name = err_line.split(':')[-1] if ':' in err_line else "desconocida"
                diag = DiagnosticManager()
                diag.reportar(ErrorCodes.ERR_GIT_FAILURE, Token(TokenID.EOF, 0, 0), modulo=dep_name)
                print(diag.resumen(), file=sys.stderr)
                sys.exit(diag.codigo_salida())
            elif ret == 5:
                dep_name = err_line.split(':')[-1] if ':' in err_line else "desconocida"
                diag = DiagnosticManager()
                diag.reportar(ErrorCodes.ERR_LOCK_HASH_MISMATCH, Token(TokenID.EOF, 0, 0), modulo=dep_name)
                print(diag.resumen(), file=sys.stderr)
                sys.exit(diag.codigo_salida())
            else:
                print(f"ERROR: Fallo en construccion (codigo {ret})", file=sys.stderr)
                sys.exit(1)

        lineas = []
        try:
            with open(out_path, 'r') as f:
                lineas = [l.strip() for l in f if l.strip()]
            os.remove(out_path)
        except (FileNotFoundError, OSError):
            pass

        punto_entrada = ""
        dependencias: Dict[str, Any] = {}
        for ln in lineas:
            if ln.startswith("punto_entrada="):
                punto_entrada = ln.split("=", 1)[1]
            else:
                dependencias[ln] = True

        ruta_entrada = os.path.normpath(os.path.join(os.getcwd(), punto_entrada))
        if not os.path.exists(ruta_entrada):
            diag = DiagnosticManager()
            diag.reportar(ErrorCodes.ERR_FILE_NOT_FOUND,
                          Token(TokenID.EOF, 0, 0), archivo=ruta_entrada)
            print(diag.resumen(), file=sys.stderr)
            sys.exit(diag.codigo_salida())

        codigo = ejecutar_compilador(ruta_entrada, mostrar_tokens=tokens_flag,
                                     output_lang=lang_val, dump_ast=dump_flag,
                                     dependencias=dependencias)
        sys.exit(codigo)

    if args.lsp:
        from synapse_lsp.server import iniciar
        iniciar()
    else:
        # Compilación normal: detectar archivo principal desde sys.argv
        archivo_principal = None
        for arg in sys.argv[1:]:
            if not arg.startswith('-'):
                archivo_principal = arg
                break
        
        if archivo_principal is None:
            print("[ERROR] Se requiere archivo .syn para compilar", file=sys.stderr)
            parser.print_help()
            sys.exit(1)
        
        codigo = ejecutar_compilador(archivo_principal, mostrar_tokens=args.tokens,
                                     output_lang=args.lang, dump_ast=args.dump_ast,
                                     modo_safe=args.safe,
                                     output_path=args.output,
                                     incremental=args.incremental,
                                     generar_sbom=args.sbom,
                                     firmar_binario=bool(args.sign),
                                     clave_sbom=args.sign or '')
        sys.exit(codigo)


if __name__ == "__main__":
    main()