import os
import sys
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
    parser.add_argument("construir", nargs="?", help=argparse.SUPPRESS)
    args, _ = parser.parse_known_args()

    if args.help:
        parser.print_help()
        sys.exit(0)

    if args.version:
        print("Synapse Compiler v2.0.0")
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
