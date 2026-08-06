"""Reproducir test F1.2d e2e S2 manualmente."""
import os
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)

# Exactamente el programa del test F1.2d
src = '''#lang: es

estructura NodoLista:
    valor: entero
    siguiente: arc<NodoLista>

@export (python) funcion sumar(a: entero, b: entero) -> entero:
    let r = a + b
    retornar r

funcion principal() -> nulo:
    let ref: debil<NodoLista> = nulo
    escribir_linea(entero_a_texto(sumar(2, 3)))
    retornar
'''

with tempfile.TemporaryDirectory() as tmp:
    path = os.path.join(tmp, "programa.syn")
    exe = os.path.join(tmp, "programa.exe")
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    
    # Limpiar synapse_unity.c
    unity_path = os.path.join(os.getcwd(), "synapse_unity.c")
    if os.path.exists(unity_path):
        os.remove(unity_path)
    
    # Compilar con stage2
    stg = os.path.join(RAIZ, "synapse_stage2.exe")
    proc = subprocess.run([stg, path, exe], capture_output=True, text=True, timeout=300)
    print("Stage2 rc:", proc.returncode)
    print("Stage2 stdout:", proc.stdout[-2000:])
    print("Stage2 stderr:", proc.stderr[-2000:])
    
    # Check if unity.c has the same content as our saved one
    if os.path.exists(unity_path):
        with open(unity_path) as f:
            c = f.read()
        for i, line in enumerate(c.splitlines()):
            if 'debil' in line or 'ref ' in line:
                print(f"unity.c line {i}: {line}")
    
    if os.path.exists(exe):
        run = subprocess.run([exe], capture_output=True, text=True, timeout=30)
        print("EXE stdout:", run.stdout)
        print("EXE stderr:", run.stderr)
        print("EXE rc:", run.returncode)
