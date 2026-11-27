# Plan ME_29_T6b — Fix test_installer_opensyn (pipeline.py → main.py)

## Bloque MTS (método de trabajo seguro)

### requisito:
Manual 7 §2.3: "El instalador de OpenSyn: opensyn/installer.syn compila y ejecuta. Detecta hardware, selecciona modelo segun VRAM, descarga con SHA-256 verificacion. Salida: Hardware:/Modelo:/Hilos:/Capas GPU:"
Manual 8 §1.2: "CLI unificado: synapse check --no-emit, opensyn download <modelo>, opensyn status. Punto de entrada principal es main.py/cli.py, no pipeline.py directamente."

### texto:
"tierras/hardware y gestión de modelos... Instalador de un solo clic... Si elige OpenSyn, se ejecuta opensyn/installer.syn que: Detecta hardware. Selecciona y descarga el modelo apropiado."

### implementacion:
Modificar _compilar_syq() en tests/opensyn/test_installer.py para usar main.py en lugar de pipeline.py como entry point. main.py delega a cli.py que llama ejecurar_compilador() de pipeline.py. El flag --output ya es soportado por cli.py.

### oraculo:
- rc == 0
- Ejecutable generado en tests/fixtures/installer.exe
- Salida contiene 'Hardware:', 'Modelo:', 'Hilos:', 'Capas GPU:'

## Archivos a modificar
- tests/opensyn/test_installer.py (línea 23: pipeline.py → main.py)

## Citas de manuales
- Manual 7 §2.3 (instalador OpenSyn)
- Manual 8 §1.2 (CLI unificado entry point)
