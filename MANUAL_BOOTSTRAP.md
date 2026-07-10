# Synapse: Manual de Compilación Base (Bootstrapping)

## 1. El Problema del Huevo y la Gallina
Synapse es un compilador auto-alojado (*self-hosted*). Está escrito en su propio lenguaje (`main.syn`). Para compilar el compilador, necesitas el compilador. Cuando un ingeniero clona el repositorio en una máquina nueva y limpia, se enfrenta a este ciclo.

Este documento explica cómo levantar el lenguaje desde cero utilizando nuestro puente de Python.

## 2. El Ciclo de Tres Fases

### Fase 0: El Entorno
Se requiere Python 3.10+ y GCC/Clang instalado y configurado en el `PATH`.

### Fase 1: El Puente de Python (`synapse_py`)
El repositorio contiene una versión mínima y congelada del frontend escrita en Python (`lexer.py`, `parser.py`, `generator.py`). Esta versión no es para desarrollo, es únicamente el motor de arranque.

**Comando de inyección:**
```bash
python main.py src/main.syn -o dist/bin/synapse_stage1.exe

Resultado: Python lee el código fuente de Synapse y genera el primer binario nativo (Stage 1). Este binario funciona, pero no está optimizado por sí mismo.

Fase 2: Autocompilación (Stage 2)
Usamos el binario nativo recién creado para compilarse a sí mismo. Esto verifica que el código C generado por Synapse es capaz de entender la gramática de Synapse.

Comando de validación:

Bash
./dist/bin/synapse_stage1.exe src/main.syn -o dist/bin/synapse_stage2.exe
Fase 3: Equivalencia Matemática (Stage 3)
Para probar que el compilador no tiene mutaciones o fugas lógicas introducidas en la Fase 2, repetimos el proceso.

Comando final:

Bash
./dist/bin/synapse_stage2.exe src/main.syn -o dist/bin/synapse_final.exe
diff dist/bin/synapse_stage2.exe dist/bin/synapse_final.exe
Criterio de éxito: Si los binarios o el código C generado en la Fase 2 y Fase 3 son exactamente idénticos (bit a bit), el Bootstrap ha sido exitoso. synapse_final.exe se convierte en tu compilador oficial.


***

### Documento 11: `ESPECIFICACION_STD.md`

```markdown
# Synapse: Arquitectura de la Librería Estándar (STD)

## 1. Filosofía Baterías Incluidas
Synapse no delega la funcionalidad esencial al gestor de paquetes. Axon es para lógica de negocio de terceros; la librería `std` provee las interfaces de sistemas (OS), entrada/salida y manejo de memoria seguras por defecto. Todo módulo `std` está respaldado por implementaciones optimizadas en C.

## 2. Jerarquía de Módulos Core

### `std.io` (Entrada/Salida)
Manejo de consola y descriptores de archivo de forma segura.
* `escribir_linea(c: cadena) -> nulo`
* `leer_archivo(ruta: cadena) -> Resultado<cadena, ErrorIO>`

### `std.err` (Manejo de Errores)
Contiene las Uniones Etiquetadas fundamentales del lenguaje (ADTs).
* `Resultado<T, E>`: Con variantes `ok(T)` y `err(E)`.
* `Opcion<T>`: Con variantes `algun(T)` y `ninguno`.

### `std.concurrencia` (Física de Hilos)
Primitivas de paso de mensajes sin memoria compartida.
* `Canal<T>`: Estructura de comunicación atómica.
* `crear_canal() -> Canal<T>`

### `std.memoria` (Utilidades de bajo nivel)
Herramientas para interactuar con bloques `inseguro`. Exclusivo para ingenieros de sistemas.
* `direccion_de(ref: T) -> Puntero<T>` (Equivalente al `&` en C).
* `tamaño_de(tipo: T) -> entero` (Equivalente a `sizeof()`).

## 3. Inyección Automática
El módulo `std.err` (que contiene `Resultado` y `Opcion`) se inyecta automáticamente en