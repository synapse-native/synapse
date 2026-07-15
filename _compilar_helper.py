# _compilar_helper.py - Compilador interno de Synapse (usado por el Bucle del Oraculo)
# Toma codigo fuente .syn via archivo temporal, emite JSON con resultado.
# Uso: python _compilar_helper.py <archivo.syn>
#   -> stdout: JSON con { exito: bool, codigo_c?: str, errores?: [{linea, columna, mensaje}] }

import sys, json, os, io

# Ensure we can import from parent directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import compilar_desde_texto
from generator import GeneradorC
from diagnostics import DiagnosticManager

def compilar(ruta_archivo):
    diag = DiagnosticManager(idioma='es', ruta_archivo=ruta_archivo)

    # Read source to provide line context for diagnostics
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            fuente_lineas = f.readlines()
        diag.fuente_lineas = fuente_lineas
    except:
        pass

    archivos_procesados = set()
    try:
        programa, diag = compilar_desde_texto(
            ruta_archivo,
            archivos_procesados,
            dir_base='',
            mostrar_tokens=False,
            diag=diag
        )

        if diag.hay_errores():
            errores = []
            for err in diag.errores:
                errores.append({
                    "linea": err.get("linea", 0),
                    "columna": err.get("columna", 0),
                    "mensaje": err.get("mensaje", "Error desconocido"),
                })
            print(json.dumps({"exito": False, "errores": errores}, ensure_ascii=False))
            return

        # Generate C code
        gen = GeneradorC(programa)
        codigo_c = gen.generar()

        # Read the full generated .c file if it was written
        ruta_c = ruta_archivo.rsplit('.', 1)[0] + '.c'
        if os.path.exists(ruta_c):
            with open(ruta_c, 'r', encoding='utf-8') as f:
                codigo_c = f.read()

        print(json.dumps({"exito": True, "codigo_c": codigo_c}, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({
            "exito": False,
            "errores": [{"linea": 0, "columna": 0, "mensaje": f"Error interno: {str(e)}"}]
        }, ensure_ascii=False))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({
            "exito": False,
            "errores": [{"linea": 0, "columna": 0, "mensaje": "Uso: python _compilar_helper.py <archivo.syn>"}]
        }))
        sys.exit(1)
    compilar(sys.argv[1])
