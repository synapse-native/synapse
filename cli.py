import os
import sys
import json
import subprocess
import argparse
from typing import Dict, Any

from compilador.diagnostics import DiagnosticManager, ErrorCodes
from compilador.ast_nodes import Token, TokenID
from pipeline import ejecutar_compilador


def main():
    parser = argparse.ArgumentParser(description="Synapse Compiler v2.0 - Poliglota", add_help=False)
    parser.add_argument("-h", "--help", action="store_true", help="Mostrar ayuda y salir")
    parser.add_argument("--version", action="store_true", help="Mostrar version y salir")
    parser.add_argument("archivo", nargs="?", default="programa.syn",
                        help="Archivo fuente .syn (o .syn.json para canonico)")
    parser.add_argument("-o", "--output", type=str, default=None,
                        help="Ruta del ejecutable de salida")
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
    args, _ = parser.parse_known_args()

    if args.help:
        parser.print_help()
        sys.exit(0)

    if args.version:
        print("Synapse Compiler v2.0.0")
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
        codigo = ejecutar_compilador(args.archivo, mostrar_tokens=args.tokens,
                                     output_lang=args.lang, dump_ast=args.dump_ast,
                                     output_path=args.output)
        sys.exit(codigo)


if __name__ == "__main__":
    main()
