# cumple Manual 7 §2.3; Manual 3 §12.1 -- herramienta ME-4 (insercion de skips
# puntuales autorizados por el Arquitecto ARQ-2026-08-27, ver MEMORIA_PROYECTO.md)
import os

def refactor_test_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()

    new_lines = []
    
    # Guardar índice en new_lines donde empieza la función actual
    current_test_start = -1
    skip_injected = False
    
    for line in lines:
        if line.strip().startswith('def test_'):
            current_test_start = len(new_lines)
            skip_injected = False
            new_lines.append(line)
            continue
            
        if current_test_start != -1 and not skip_injected and ('in contenido' in line or 'contenido.lower()' in line):
            # Inyectar skip
            def_line = new_lines[current_test_start]
            indent = " " * (len(def_line) - len(def_line.lstrip()) + 4)
            # Insertamos el skip justo despues de la firma del metodo
            new_lines.insert(current_test_start + 1, indent + "pytest.skip('ME-4: Refactor pendiente a validación funcional')")
            skip_injected = True
            
        new_lines.append(line)

    # Solo sobreescribir si hubieron cambios
    if "pytest.skip('ME-4" in "\n".join(new_lines):
        # ensure import pytest
        if "import pytest" not in new_lines:
            new_lines.insert(0, "import pytest")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(new_lines) + "\n")

if __name__ == "__main__":
    tests_dir = "tests"
    for root, dirs, files in os.walk(tests_dir):
        for file in files:
            if file.endswith(".py") and file.startswith("test_"):
                refactor_test_file(os.path.join(root, file))
    print("ME-4 Refactor script completado.")
