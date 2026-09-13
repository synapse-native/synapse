# MANUAL 31: HERRAMIENTAS DE DESARROLLO NATIVAS (TOOLING COMPLETO)

**Archivo:** `31_HERRAMIENTAS_NATIVAS.md`  
**Versión:** 8.2.0-industrial  
**Propósito:** Especificar la implementación del conjunto completo de herramientas de desarrollo nativas para el ecosistema Synapse/Syquex, eliminando toda dependencia de Python en la cadena de desarrollo. Este manual cubre el aislamiento de workspaces en Axon, el testing nativo sin genéricos, el linter y formateador nativos sobre el AST unificado, y los reportes de CI/CD.

---

## 1. VISIÓN GENERAL DE LA FASE 31

### 1.1. Objetivo

Implementar el conjunto completo de herramientas de desarrollo (package manager, testing, linting, formateo, CI/CD) de forma nativa en Synapse/Syquex, eliminando toda dependencia de Python en la cadena de desarrollo.

### 1.2. Filosofía

Las herramientas nativas deben ser:
- **Compiladas:** Ejecutarse como binarios autocontenidos (`synapse.exe`).
- **Deterministas:** Producir la misma salida en cualquier máquina.
- **Rápidas:** Procesar el AST directamente, sin overhead de parsing repetido.
- **Integradas:** Usar el mismo AST canónico (`SemNodo[]`) que el compilador.

### 1.3. Módulos que cubre

| Módulo | Descripción | Comando |
|--------|-------------|---------|
| Aislamiento de Workspaces | Axon gestiona dependencias por proyecto | `synapse fetch` |
| Testing Nativo | `lib/pruebas.syq` con sobrecarga estática | `synapse test` |
| Linter Nativo | Procesa el AST unificado para emitir advertencias | `synapse lint` |
| Formateador Nativo | Reescribe el código fuente según reglas de estilo | `synapse fmt` |
| CI/CD Reporting | Genera reportes en formatos estándar | `synapse test --junit` |

---

## 2. MÓDULO 31.1: AISLAMIENTO DE WORKSPACES EN AXON

### 2.1. Problema Actual

Axon actualmente gestiona dependencias en un caché global (`~/.axon/cache/`). Esto provoca colisiones cuando múltiples proyectos requieren versiones divergentes de la misma sublibrería C.

### 2.2. Solución: Workspace‑Local Cache

Cada proyecto tiene su propio directorio de caché y su propio `axon.lock`. Las dependencias se resuelven localmente por proyecto, no globalmente.

**Estructura:**

```
mi_proyecto/
├── axon.toml
├── axon.lock
└── .axon/                      # Workspace local (generado)
    └── cache/
        ├── libcurl-7.88.1/
        ├── sqlite-3.42.0/
        └── ...
```

**Comportamiento de `synapse fetch`:**
1. Lee `axon.toml` y resuelve dependencias (como antes).
2. Descarga las dependencias en `.axon/cache/` (no en `~/.axon/cache/`).
3. Escribe el lockfile con los hashes SHA‑256 de las dependencias específicas del proyecto.
4. Si el proyecto tiene un `axon.lock` existente, usa las versiones lockeadas (offline‑first).

### 2.3. Cambios en `axon/axon_rt.c`

```c
// axon/axon_rt.h - Nuevas funciones
int axon_workspace_crear(const char* ruta_proyecto);
int axon_workspace_resolver(const char* ruta_proyecto, const char* lock_path);
char* axon_workspace_cache_path(const char* ruta_proyecto);
```

### 2.4. Cambios en `axon/axon.toml` (Esquema)

```toml
[paquete]
nombre = "mi-proyecto"
version = "0.1.0"

[dependencias]
libcurl = { version = "7.88.1", tipo = "c" }
sqlite = { version = "3.42.0", tipo = "c" }
```

### 2.5. Criterios de Aceptación

- `synapse fetch` en dos proyectos diferentes descarga las mismas dependencias en directorios separados.
- `synapse fetch` en un proyecto con lockfile no descarga nada si las dependencias ya están en `.axon/cache/`.
- El lockfile (`axon.lock`) registra las dependencias con sus hashes SHA‑256.

---

## 3. MÓDULO 31.2: TESTING NATIVO SIN GENÉRICOS

### 3.1. Problema Actual

El Manual 7 especifica `assert_eq<T>` con genéricos, pero el sistema de tipos Hindley‑Milner aún no soporta genéricos completos en todas las fases del bootstrap. Esto bloquea la implementación del testing nativo.

### 3.2. Solución: Sobrecarga Estática Explícita

Se implementa `lib/pruebas.syq` con sobrecarga estática explícita para tipos primitivos, evitando la dependencia de genéricos.

**Archivo:** `lib/pruebas.syq`

```syquex
// lib/pruebas.syq - Framework de testing nativo (sin genéricos)

// ASSERTIONS BÁSICAS
funcion assert(condicion: booleano) -> Resultado<nulo, texto>:
    si no condicion:
        retornar err("Assertion failed")
    retornar ok()

funcion assert_eq_int(esperado: entero, actual: entero) -> Resultado<nulo, texto>:
    si esperado != actual:
        retornar err("Expected " + a_texto(esperado) + " but got " + a_texto(actual))
    retornar ok()

funcion assert_eq_decimal(esperado: decimal, actual: decimal) -> Resultado<nulo, texto>:
    si esperado != actual:
        retornar err("Expected " + a_texto(esperado) + " but got " + a_texto(actual))
    retornar ok()

funcion assert_eq_texto(esperado: texto, actual: texto) -> Resultado<nulo, texto>:
    si esperado != actual:
        retornar err("Expected " + esperado + " but got " + actual)
    retornar ok()

funcion assert_eq_booleano(esperado: booleano, actual: booleano) -> Resultado<nulo, texto>:
    si esperado != actual:
        retornar err("Expected " + a_texto(esperado) + " but got " + a_texto(actual))
    retornar ok()

funcion assert_eq_tensor(esperado: tensor, actual: tensor) -> Resultado<nulo, texto>:
    // Comparación de tensores: mismas dimensiones y datos
    si esperado.filas != actual.filas o esperado.columnas != actual.columnas:
        retornar err("Tensors have different dimensions")
    para i = 0 mientras i < esperado.filas * esperado.columnas:
        si esperado.datos[i] != actual.datos[i]:
            retornar err("Tensors differ at index " + a_texto(i))
    retornar ok()

// ESTRUCTURA DE PRUEBAS
funcion test(nombre: texto, fn: funcion() -> Resultado<nulo, texto>) -> Resultado<nulo, texto>:
    io.escribir("Running test: " + nombre + "... ")
    let resultado = fn()
    coincidir resultado:
        ok() => io.escribir_linea("PASS")
        err(e) => io.escribir_linea("FAIL: " + e)
    retornar resultado

funcion suite(nombre: texto, tests: Lista<funcion() -> Resultado<nulo, texto>>) -> Resultado<nulo, texto>:
    io.escribir_linea("Suite: " + nombre)
    let fallos = 0
    para test_fn en tests:
        let r = test_fn()
        si r es err:
            fallos = fallos + 1
    si fallos == 0:
        io.escribir_linea("All tests passed")
        retornar ok()
    sino:
        retornar err("" + a_texto(fallos) + " tests failed")
```

### 3.3. Modo `--junit` y `--coverage`

El CLI `synapse test` se extiende con dos flags adicionales:

| Flag | Descripción | Salida |
|------|-------------|--------|
| `--junit` | Genera reporte JUnit XML | `test-results.xml` |
| `--coverage` | Genera informe de cobertura en HTML | `coverage.html` |
| `--json` | Genera reporte en JSON | `test-results.json` |

### 3.4. Criterios de Aceptación

- `lib/pruebas.syq` existe y contiene las funciones de aserción sobrecargadas.
- `synapse test` ejecuta todas las funciones `test_*` en los archivos `.syq`.
- `synapse test --junit` genera un archivo `test-results.xml` válido.
- `synapse test --coverage` genera un informe de cobertura con los módulos cubiertos.
- Todos los tests originales (184+) siguen pasando.

---

## 4. MÓDULO 31.3: LINTER NATIVO (`synapse lint`)

### 4.1. Problema Actual

No existe un linter nativo para Synapse/Syquex. El formateo y linting dependen de herramientas externas (Python).

### 4.2. Solución: Linter sobre el AST Unificado

`synapse lint` procesa el AST canónico (`SemNodo[]`) y emite advertencias sobre código que no cumpla con las guías de estilo.

**Comando:**
```bash
synapse lint [archivo.syn|archivo.syq] [--fix] [--check]
```

**Archivo:** `nucleo/lint.syn`

```synapse
// nucleo/lint.syn - Linter nativo
estructura Advertencia:
    tipo: texto           // "estilo", "seguridad", "rendimiento"
    mensaje: texto
    linea: entero
    columna: entero
    archivo: texto

funcion lint_programa(programa: Programa) -> Lista<Advertencia>:
    let advertencias = Lista<Advertencia>()
    
    // Regla 1: Variables no utilizadas
    let variables_utilizadas = recorrer_usos(programa)
    para decl en programa.declaraciones:
        si decl es DeclaracionVariable:
            si decl.nombre no en variables_utilizadas:
                advertencias.agregar(
                    Advertencia("estilo", "Variable no utilizada: " + decl.nombre, decl.linea, decl.columna, decl.archivo)
                )
    
    // Regla 2: Funciones sin requiere/garantiza
    para funcion en programa.funciones:
        si funcion.contratos == nulo:
            advertencias.agregar(
                Advertencia("seguridad", "Función sin contratos (requiere/garantiza): " + funcion.nombre, funcion.linea, funcion.columna, funcion.archivo)
            )
    
    // Regla 3: Indentación incorrecta (detectada en lexer, pero se verifica aquí)
    // ...
    
    retornar advertencias
```

### 4.3. Reglas a Implementar (Mínimo Viable)

| Regla | Tipo | Código de error |
|-------|------|-----------------|
| Variables no utilizadas | Estilo | `WARN_LINT_UNUSED_VAR` |
| Funciones sin `requiere`/`garantiza` | Seguridad | `WARN_LINT_NO_CONTRACT` |
| Indentación incorrecta | Estilo | `WARN_LINT_INDENT` |
| Nombres no estándar (snake_case) | Estilo | `WARN_LINT_NAMING` |
| Código muerto (bloques inaccesibles) | Rendimiento | `WARN_LINT_DEAD_CODE` |

### 4.4. Criterios de Aceptación

- `synapse lint` analiza archivos `.syn` y `.syq` sin errores.
- Emite advertencias con ubicación exacta (archivo, línea, columna).
- `synapse lint --fix` corrige automáticamente los errores de estilo (indentación, espacios).
- `synapse lint --check` retorna código de salida 1 si hay advertencias.

---

## 5. MÓDULO 31.4: FORMATEADOR NATIVO (`synapse fmt`)

### 5.1. Problema Actual

No existe un formateador nativo para Synapse/Syquex. Dependencia de herramientas externas.

### 5.2. Solución: Formateador sobre el AST Unificado

`synapse fmt` reescribe el código fuente según las reglas de estilo (indentación de 4 espacios, espacios alrededor de operadores, etc.).

**Comando:**
```bash
synapse fmt [archivo.syn|archivo.syq] [--check] [--dry-run]
```

**Archivo:** `nucleo/formatter.syn`

```synapse
// nucleo/formatter.syn - Formateador nativo
funcion formatear_programa(programa: Programa) -> texto:
    let resultado = "#lang: es\n"
    para decl en programa.declaraciones:
        resultado = resultado + formatear_declaracion(decl)
    retornar resultado

funcion formatear_declaracion(decl: Declaracion) -> texto:
    coincidir decl:
        FuncionDef:
            retornar "funcion " + decl.nombre + "(" + formatear_parametros(decl.parametros) + ")" + " -> " + decl.tipo_retorno + ":\n" + indentar(formatear_bloque(decl.cuerpo))
        // ...
```

### 5.3. Reglas de Estilo (Normativas)

| Regla | Valor |
|-------|-------|
| Indentación | 4 espacios (prohibido tabs) |
| Espacios alrededor de operadores | Sí (ej. `a + b` no `a+b`) |
| Llaves de bloque | No se usan (indentación) |
| Comas | Un espacio después de coma (ej. `funcion(a, b)` no `funcion(a,b)`) |
| Líneas vacías | Entre funciones, entre secciones de módulo |

### 5.4. Criterios de Aceptación

- `synapse fmt` reescribe el archivo en el lugar (sin cambios si ya está formateado).
- `synapse fmt --check` retorna código de salida 1 si el archivo no está formateado.
- `synapse fmt --dry-run` muestra los cambios sin escribir en disco.

---

## 6. MÓDULO 31.5: CI/CD REPORTING MEJORADO

### 6.1. Problema Actual

`synapse test` solo imprime en consola. No se integra con sistemas de CI/CD (GitHub Actions, Jenkins, etc.).

### 6.2. Solución: Generación de Reportes Estándar

Se extiende `synapse test` con flags adicionales para generar reportes en formatos estándar.

**Comandos:**
```bash
synapse test --junit        # Genera test-results.xml (JUnit)
synapse test --coverage     # Genera coverage.html (cobertura)
synapse test --json         # Genera test-results.json
```

**Formato JUnit (ejemplo):**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <testsuite name="lib.io" tests="5" failures="0" errors="0" time="0.123">
    <testcase name="test_escribir_linea" time="0.001"/>
    <testcase name="test_leer_archivo" time="0.002"/>
  </testsuite>
</testsuites>
```

**Formato JSON (ejemplo):**

```json
{
  "tests": [
    { "name": "test_escribir_linea", "status": "passed", "time": 0.001 },
    { "name": "test_leer_archivo", "status": "failed", "message": "File not found", "time": 0.002 }
  ],
  "summary": { "total": 5, "passed": 4, "failed": 1, "time": 0.123 }
}
```

### 6.3. Implementación en `nucleo/principal.syn`

```synapse
// nucleo/principal.syn - Extensión para reportes
funcion generar_junit(resultados: Lista<ResultadoTest>) -> texto:
    let xml = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
    xml = xml + "<testsuites>\n"
    // Agrupar por suite
    para suite en agrupar_por_suite(resultados):
        xml = xml + "  <testsuite name=\"" + suite.nombre + "\" tests=\"" + a_texto(suite.total) + "\" failures=\"" + a_texto(suite.fallos) + "\">\n"
        para test en suite.tests:
            xml = xml + "    <testcase name=\"" + test.nombre + "\" time=\"" + a_texto(test.tiempo) + "\"/>\n"
        xml = xml + "  </testsuite>\n"
    xml = xml + "</testsuites>\n"
    retornar xml

funcion generar_coverage(programa: Programa) -> texto:
    // Recorre el AST y calcula cobertura (líneas ejecutadas vs total)
    let cubiertas = 0
    let total = 0
    para nodo en programa.nodos:
        total = total + 1
        si nodo.marcado_ejecutado:
            cubiertas = cubiertas + 1
    let porcentaje = (cubiertas / total) * 100
    retornar "<html><body><h1>Coverage: " + a_texto(porcentaje) + "%</h1></body></html>"
```

### 6.4. Criterios de Aceptación

- `synapse test --junit` genera un archivo `test-results.xml` válido para JUnit.
- `synapse test --coverage` genera un informe HTML con cobertura de código.
- `synapse test --json` genera un archivo JSON con los resultados.

---

## 7. INTEGRACIÓN CON EL ROADMAP

### 7.1. Dependencias

| Dependencia | Fase | Justificación |
|-------------|------|---------------|
| CLI unificado (`synapse`) | Fase 27 | Las herramientas se integran en el CLI |
| `lib/pruebas.syq` | Fase 24.B | Testing nativo depende de la biblioteca estándar |
| AST canónico (`SemNodo[]`) | Fase 22 | Linter y formateador procesan el AST |
| Axon (`axon_rt.c`) | Fase 6 | Aislamiento de workspaces |

### 7.2. Duración Estimada

| Módulo | Meses |
|--------|-------|
| 31.1 Aislamiento de workspaces (Axon) | 2 |
| 31.2 Testing nativo (`lib/pruebas.syq`) | 1 |
| 31.3 Linter nativo (`synapse lint`) | 2 |
| 31.4 Formateador nativo (`synapse fmt`) | 2 |
| 31.5 CI/CD reporting mejorado | 1 |
| **TOTAL** | **8 meses** |

### 7.3. Hitos de la Fase 31

| Hito | Entregable | Mes |
|------|------------|-----|
| Hito 31.1 | `synapse fetch` con workspaces aislados | Mes 2 |
| Hito 31.2 | `lib/pruebas.syq` y `synapse test` básico | Mes 3 |
| Hito 31.3 | `synapse lint` funcional | Mes 5 |
| Hito 31.4 | `synapse fmt` funcional | Mes 7 |
| Hito 31.5 | `synapse test --junit`, `--coverage`, `--json` | Mes 8 |

---

## 8. PRUEBAS OBLIGATORIAS PARA LA FASE 31

| Test | Comando | Criterio |
|------|---------|----------|
| Aislamiento de workspaces | `pytest tests/axon/test_workspace.py -v` | 100% pass |
| Testing nativo (`lib/pruebas.syq`) | `pytest tests/syquex/test_pruebas.py -v` | 100% pass |
| Linter (`synapse lint`) | `pytest tests/nucleo/test_lint.py -v` | 100% pass |
| Formateador (`synapse fmt`) | `pytest tests/nucleo/test_fmt.py -v` | 100% pass |
| Reportes JUnit y JSON | `pytest tests/integration/test_reports.py -v` | 100% pass |
| Cobertura de código | `pytest tests/integration/test_coverage.py -v` | 100% pass |

---

## 9. SIGUIENTES PASOS

Con la Fase 31 especificada, el siguiente paso es actualizar el ROADMAP.md para incluir esta fase y los hitos asociados. Luego, se deben modificar los manuales 4, 7, 8 y 9 para añadir referencias a las herramientas nativas cuando corresponda.

---

*Este manual proporciona la especificación completa de las herramientas de desarrollo nativas del ecosistema. La implementación debe seguir estos lineamientos para eliminar la dependencia de Python y garantizar una experiencia de desarrollo completa y profesional.*

**Fin del Manual 31**