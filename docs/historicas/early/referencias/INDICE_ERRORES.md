# Synapse: Taxonomía y Códigos de Error (El Diagnóstico)

## 1. Estructura del Error
Como parte de la meta de "Developer Experience (DX)", Synapse no escupe *stack traces* incomprensibles. Todo error de compilación se clasifica bajo un código estricto (`E-XXX`), lo que permite su rápida búsqueda en la documentación y su correcta emisión hacia el servidor LSP.

## 2. Categoría E-100: Léxico y Sintaxis
Errores en la forma del texto fuente.
* **E-101 (Indentación Inválida):** Se rompió el múltiplo de 4 espacios o se detectó un tabulador (`\t`).
* **E-102 (Token Inesperado):** El parser encontró un símbolo que viola la gramática EBNF (ej. uso de `{`).
* **E-103 (Bloque Vacío):** Se definió una estructura con `:` pero no hay código indentado debajo.

## 3. Categoría E-200: Semántica y Tipado
Errores lógicos y operaciones ilegales en tiempo de compilación.
* **E-201 (Discrepancia de Tipos):** Intento de asignar un `flotante` a un `entero` sin casteo explícito.
* **E-202 (Variable no Declarada):** Uso de un identificador no presente en la Tabla de Símbolos.
* **E-203 (Coincidencia Exhaustiva Fallida):** Un bloque `coincidir` sobre un `Resultado` no contempló el caso `err()`.

## 4. Categoría E-300: Memoria y Posesión (Borrow Checker)
Los errores más críticos. Previenen las vulnerabilidades de memoria en tiempo de compilación.
* **E-301 (Use-After-Move):** Intento de leer o modificar una variable cuya propiedad ya fue transferida a otra variable o función.
* **E-302 (Lanzamiento Inseguro):** Intento de acceder en el hilo principal a una variable que fue pasada al bloque `lanzar`.
* **E-303 (Fuga en Bloque Inseguro):** Advertencia emitida por el analizador semántico al detectar punteros crudos sin liberación explícita.

## 5. Categoría E-400: Contratos Lógicos
* **E-401 (Contrato Imposible):** El compilador detecta estáticamente que una cláusula `requiere` o `garantiza` nunca podrá cumplirse.

