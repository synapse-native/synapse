#!/usr/bin/env python3
"""
Smoke test para validar la generación de código C para la estructura coincidir
"""
import sys
from lexer import Lexer
from parser import Parser
from generator import GeneradorC
from diagnostics import DiagnosticManager


def main():
    # Leer el archivo de prueba
    with open('tests/test_lexer_ADTs.syn', 'r', encoding='utf-8') as f:
        fuente = f.read()
    
    print("=" * 60)
    print("SMOKE TEST: Generación de código C para coincidir")
    print("=" * 60)
    print(f"\nFuente:\n{fuente}")
    print("-" * 60)
    
    # Paso 1: Lexer
    print("\n[1] Tokenizando con Lexer...")
    lexer = Lexer(fuente)
    tokens = lexer.tokenizar()
    print(f"Tokens generados: {len(tokens)}")
    
    # Paso 2: Parser
    print("\n[2] Parseando con Parser...")
    diag = DiagnosticManager()
    parser = Parser(tokens, diag)
    ast = parser.parsear()
    
    # Verificar errores de parseo
    if diag.errores:
        print("\n[ERROR] Se encontraron errores durante el parseo:")
        for err in diag.errores:
            print(f"  {err}")
        sys.exit(1)
    else:
        print("[OK] AST generado exitosamente")
    
    # Paso 3: Generator
    print("\n[3] Generando código C...")
    generador = GeneradorC(ast)
    codigo_c = generador.generar()
    
    # Paso 4: Imprimir código C generado
    print("\n[4] Código C generado:")
    print("=" * 60)
    print(codigo_c)
    print("=" * 60)
    
    # Extraer y mostrar específicamente la función principal
    print("\n[5] Función principal() generada:")
    print("-" * 60)
    lines = codigo_c.split('\n')
    in_principal = False
    principal_lines = []
    indent_level = 0
    
    for line in lines:
        if 'void principal()' in line or 'int principal()' in line:
            in_principal = True
        if in_principal:
            principal_lines.append(line)
            if line.strip().startswith('}'):
                indent_level -= 1
                if indent_level == 0:
                    break
            if line.strip().endswith('{'):
                indent_level += 1
    
    print('\n'.join(principal_lines))
    print("-" * 60)


if __name__ == '__main__':
    main()
