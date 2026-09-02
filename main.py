# cumple Manual 1 §1: infraestructura Python del compilador Synapse
# cumple Manual 8 §4: toolchain de construcción
#!/usr/bin/env python3
"""
Synapse Compiler v8.1.0-industrial - Punto de entrada minimalista.
Delega todo el trabajo a cli.py y pipeline.py.
"""
from cli import main

if __name__ == "__main__":
    main()
