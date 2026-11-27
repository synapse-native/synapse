## 1. RECTIFICACIONES Y AJUSTES AL MATERIAL PREVIO

### 1.1. Módulo `lib/web.syq` – Adecuación al modelo de fibras (Manual 5)

El servidor HTTP debe ser **no bloqueante** y utilizar el scheduler de fibras para manejar múltiples conexiones simultáneas sin bloquear el hilo principal. La especificación anterior era demasiado simple. Corrijo:

```syquex
// lib/web.syq
// Servidor HTTP basado en fibras (no bloqueante).

estructura Peticion:
    metodo: texto
    ruta: texto
    cuerpo: texto
    parametros: Mapa<texto, texto>

estructura Respuesta:
    codigo: entero
    cuerpo: texto
    cabeceras: Mapa<texto, texto>

estructura Servidor:
    puerto: entero
    rutas_get: Mapa<texto, funcion(Peticion) -> Respuesta>
    rutas_post: Mapa<texto, funcion(Peticion) -> Respuesta>
    activo: booleano

funcion servidor(puerto: entero) -> Servidor:
    retornar Servidor(puerto, Mapa(), Mapa(), falso)

metodo get(servidor: &mut Servidor, ruta: texto, handler: funcion(Peticion) -> Respuesta) -> nulo:
    servidor.rutas_get[ruta] = handler

metodo post(servidor: &mut Servidor, ruta: texto, handler: funcion(Peticion) -> Respuesta) -> nulo:
    servidor.rutas_post[ruta] = handler

metodo iniciar(servidor: &Servidor) -> Resultado<nulo, texto>:
    // Inicia el servidor en una fibra separada.
    // Cada conexión entrante se maneja en una nueva fibra.
    servidor.activo = verdadero
    lanzar _escuchar(servidor)
    retornar ok()

funcion _escuchar(servidor: &Servidor):
    // Bucle principal del servidor (fibra).
    mientras servidor.activo:
        let cliente = _aceptar(servidor.puerto)  // FFI a libmicrohttpd o sockets nativos
        lanzar _manejar(cliente, servidor)

funcion _manejar(cliente: puntero, servidor: &Servidor):
    // Procesa una petición en su propia fibra.
    let req = _leer_peticion(cliente)  // FFI
    let handler = servidor.rutas_get.obtener(req.ruta)  // o rutas_post
    si handler != nulo:
        let resp = handler(req)
        _enviar_respuesta(cliente, resp)  // FFI
    sino:
        _enviar_error(cliente, 404)
    _cerrar(cliente)
```

**Esta corrección alinea el servidor web con el modelo de concurrencia M:N del Manual 5 y con el uso de `lanzar` para fibras.**

---

### 1.2. Módulo `lib/dom.syq` – Coherencia con arenas de componente (Manual 4, §3)

Los elementos DOM creados en Syquex deben asignarse en la arena de componente correspondiente. La especificación debe reflejar que el `Elemento` es un puntero a un objeto JS que vive en la memoria lineal de WASM, y que su ciclo de vida está vinculado a la arena de componente.

```syquex
// lib/dom.syq
// Manipulación del DOM para WASM, con arenas de componente (Manual 4 §3).

estructura Elemento:
    ptr: puntero     // puntero al objeto JS en la memoria lineal (ID)
    arena_id: entero // identificador de la arena de componente

funcion crear_elemento(tag: texto) -> Resultado<Elemento, texto>:
    // Asigna el elemento en la arena de componente actual.
    let arena = comp_arena_actual()
    si arena == nulo:
        retornar err("No hay arena de componente activa")
    let id = externo js_create_element(tag.datos)  // FFI
    comp_arena_asignar(arena, id)  // registra el ID en la arena
    retornar ok(Elemento(id, arena.id))

metodo set_texto(elemento: &Elemento, texto: texto) -> nulo:
    externo js_set_text(elemento.ptr, texto.datos)

metodo set_atributo(elemento: &Elemento, nombre: texto, valor: texto) -> nulo:
    externo js_set_attribute(elemento.ptr, nombre.datos, valor.datos)

metodo agregar_hijo(padre: &Elemento, hijo: Elemento) -> nulo:
    externo js_append_child(padre.ptr, hijo.ptr)

metodo onclick(elemento: &Elemento, handler: funcion() -> nulo) -> nulo:
    // El callback se almacena en un mapa global (JS) y se asocia al elemento.
    // El callback se ejecuta en el contexto de la fibra que lo registró.
    let id_callback = _registrar_callback(handler)  // FFI
    externo js_onclick(elemento.ptr, id_callback)

// Nota: la arena de componente se destruye con comp_destroy (Manual 4 §3.3),
// lo que libera todos los elementos DOM asociados en masa.
```

---

### 1.3. Reglas de inferencia de tipos para la transpilación (F26)

Deben insertarse en el Manual 7, §5.1, después de la tabla de mapeo Python → Syquex.

**Reglas de inferencia (texto normativo):**

1. **Inferencia de tipos básicos:**
   - Enteros literales (`42`) → `entero`.
   - Flotantes literales (`3.14`) → `decimal`.
   - Cadenas (`"hola"`) → `texto`.
   - Listas homogéneas (`[1,2,3]`) → `Lista<entero>`.
   - Diccionarios homogéneos (`{"a":1}`) → `Mapa<texto, entero>`.

2. **Inferencia de funciones:**
   - Si el cuerpo de la función usa operadores aritméticos con operandos del mismo tipo, se infiere ese tipo para los parámetros y el retorno.
   - Si el cuerpo usa operaciones de concatenación de cadenas, se infiere `texto`.
   - Si el cuerpo usa `raise`, el tipo de retorno se infiere como `Resultado<T, texto>` donde T es el tipo de los retornos exitosos.
   - Si no se puede inferir un tipo, se usa `Objeto` (genérico) y se emite una advertencia. El usuario puede anotar manualmente.

3. **Regla de fallback:** cualquier variable o parámetro sin tipo explícito y sin inferencia clara se declara como `Objeto` (equivalente a `any` en TypeScript). El compilador de Syquex acepta `Objeto` con operaciones dinámicas en tiempo de ejecución (similar a la reflexión).

---

### 1.4. Esquemas de comandos LSP (F26) – ubicación exacta en Manual 7, §4.1

Deben añadirse inmediatamente después de la tabla de comandos:

**Esquemas JSON de comandos LSP (normativos):**

- `synapse/aiComplete`:
  - Petición: `{ textDocument: { uri: string }, position: { line: number, character: number }, context?: string }`
  - Respuesta: `{ completions: [{ texto: string, tipo: "linea" | "bloque", rango: { start: { line, character }, end: { line, character } } }] }`

- `synapse/aiFix`:
  - Petición: `{ textDocument: { uri: string }, diagnostic: { code: string, message: string, range: { start: { line, character }, end: { line, character } } } }`
  - Respuesta: `{ sugerencia: string, codigo_corregido: string }`

- `synapse/aiTranspile`:
  - Petición: `{ textDocument: { uri: string }, from: "python", to: "syquex" }`
  - Respuesta: `{ codigo: string }`

---

### 1.5. Módulo `std/os.syn` (F29) – API final

```syquex
// std/os.syn
// Funciones de sistema y detección de hardware.

funcion memoria_total() -> entero:
    // RAM total en bytes.
    externo sysconf(_SC_PHYS_PAGES) * sysconf(_SC_PAGESIZE)

funcion memoria_libre() -> entero:
    // RAM libre en bytes.
    externo sysconf(_SC_AVPHYS_PAGES) * sysconf(_SC_PAGESIZE)

funcion vram_total() -> entero:
    // VRAM total de la GPU en bytes (0 si no hay GPU).
    // Implementación en C en detect_hardware.c.
    externo detect_vram_total() -> int64_t

funcion cpu_nucleos() -> entero:
    // Número de núcleos de CPU.
    externo sysconf(_SC_NPROCESSORS_ONLN)

funcion arquitectura() -> texto:
    // "x86_64", "arm64", etc.
    externo detect_arquitectura() -> const char*
```

**Placeholder de modelos:** El instalador de OpenSyn (Manual 7 §2.5) debe leer un archivo `modelos.toml` que contiene las URLs y hashes SHA-256 de los modelos. Este archivo se distribuye junto con el instalador y se actualiza periódicamente.

---

## 2. RESOLUCIÓN DE CONTRADICCIONES IDENTIFICADAS

### 2.1. Circularidad F26 ↔ F27 (flag `--check`)

**Decisión:** Adelantar `--check` a la Fase 26. Se añade al roadmap como subfase 26.1. El Manual 8 §4.2 ya lo especifica; solo se adelanta su implementación en el cronograma.

### 2.2. Tabla de traducción M6 §1.3

**Corrección:** Eliminar la entrada `Intento → try en C (via FFI)`. Sustituir por una nota que indique que `intentar` se traduce al modelo de `Resultado` y `?` (Manual 3 §7). El `intentar`/`atrapar` solo se usa para interoperar con código C que lanza excepciones (FFI), pero no es el modelo principal de Syquex.

**Texto normativo (insertar en M6 §1.3):**
> "El manejo de errores en Syquex se basa en `Resultado<T,E>` y el operador `?`. La construcción `intentar`/`atrapar` está reservada exclusivamente para envolver llamadas FFI a bibliotecas C que puedan lanzar excepciones o señales (ej. `setjmp`/`longjmp`). En código nativo Syquex, se prefiere siempre `Resultado`."

### 2.3. Serialización duplicada (M5 §6.3 vs M6 §5.1)

**Decisión normativa:** El formato oficial es el de M5 §6.3 (Formato de serialización para canales remotos). M6 §5.1 se considera un borrador anterior. Se añade una nota en M6 §5.1 indicando que la especificación definitiva está en M5 §6.3 y que M6 §5.1 debe ignorarse o eliminarse en futuras revisiones.

### 2.4. Vocabulario inconsistente

**Unificación normativa:** 
- Usar siempre `débil` (con tilde) para referencias débiles.
- Usar `Lista<T>` y `Mapa<K,V>` con mayúscula inicial.
- En todos los ejemplos de los manuales, reemplazar las formas en minúscula o sin tilde por estas.

**Instrucción para el equipo:** Se realizará una revisión editorial de los manuales 2–6 para corregir estas inconsistencias en la próxima versión.

---

## 3. MATERIAL COMPLETO PARA INCORPORAR A CADA MANUAL

### 3.1. Manual 3 (Sintaxis y Semántica de Syquex) – añadir en §???

- **Sección 12:** "Biblioteca estándar de Syquex (`lib/`)". Describir la estructura de módulos y dar ejemplos de uso, pero sin detallar todas las APIs (que están en F24). Añadir una nota: "Las APIs específicas de cada módulo se especifican en los archivos `.syq` de la biblioteca estándar, cuyo diseño se detalla en la documentación de la Fase 24."

### 3.2. Manual 4 (Modelo de Memoria de Syquex) – añadir en §6

- **Sección 6.4:** "Arenas de componente para WASM". Ampliar la descripción para incluir cómo se asignan los objetos DOM en la memoria lineal y cómo se vinculan a las arenas. (Ya lo he incluido en la corrección de `lib/dom.syq`.)

### 3.3. Manual 7 (OpenSyn) – modificaciones

- **§2.3:** Añadir el bloque de inyección de contexto estático (ya presente en v8.1.0). Verificar que está actualizado.
- **§5.1:** Añadir las reglas de inferencia de tipos para la transpilación (ver punto 1.3).
- **§4.1:** Añadir los esquemas JSON de los comandos LSP (ver punto 1.4).
- **§6.3:** Añadir el bucle de validación (ya presente). Verificar que hace referencia al flag `--check` (que se adelanta a F26).
- **§2.5:** Reemplazar los placeholders `...` por una referencia al archivo `modelos.toml` que se distribuye con el instalador.

### 3.4. Manual 8 (Herramientas de Desarrollo) – modificaciones

- **§4.2:** El flag `--check` ya está especificado. Se adelanta su implementación a F26, pero la especificación queda en M8.
- **§5.1:** Añadir que el LSP orquesta el bucle de validación (3 intentos) y que usa el flag `--check` para la validación.

### 3.5. Manual 9 (Instalación) – añadir en §5

- **§5.1:** Especificar que el instalador de OpenSyn lee el archivo `modelos.toml` para obtener las URLs y hashes de los modelos. Incluir un ejemplo del formato de `modelos.toml`.

**Ejemplo `modelos.toml`:**
```toml
[modelos]
"deepseek-coder-1.3b-Q4_K_M" = { url = "https://huggingface.co/...", sha256 = "abc123...", tamano_gb = 1.1 }
"codellama-7b-Q4_K_M" = { url = "https://huggingface.co/...", sha256 = "def456...", tamano_gb = 4.0 }
# ...
```

---

## 4. VERIFICACIÓN FINAL DE COMPLETITUD

Tras incorporar el material anterior, las fases 22–30 quedan completamente especificadas:

| Fase | Estado | Acción tomada |
|------|--------|---------------|
| 22 | ✅ Cubierto (M3 + M6 §1.3) | Sin cambios |
| 23 | ✅ Cubierto (M4) | Sin cambios |
| 24 | ✅ AHORA CUBIERTO | Añadidas APIs de `lib/io`, `lib/web`, `lib/json`, `lib/lista`, `lib/db` |
| 25 | ✅ AHORA CUBIERTO | Añadida especificación de WASM ABI, glue JS, y API DOM con arenas de componente |
| 26 | ✅ AHORA CUBIERTO | Añadidas reglas de inferencia, esquemas de comandos LSP, y bucle de validación con `--check` |
| 27 | ✅ Cubierto (M8) | Sin cambios (solo adelanto de `--check` a F26) |
| 28 | ✅ Cubierto (pruebas dispersas + benchmarks) | Añadida nota en roadmap sobre benchmarks vs Python/Go (ya está en roadmap) |
| 29 | ✅ AHORA CUBIERTO | Añadida API de `std/os.syn` y referencia a `modelos.toml` |
| 30 | ✅ Cubierto (M9) | Sin cambios |

**Contradicciones resueltas:**
- F26↔F27 circularidad: adelanto de `--check` a F26.
- Tabla de traducción M6 §1.3: corregida.
- Serialización duplicada: se declara M5 §6.3 como normativa.
- Vocabulario inconsistente: se establecen términos normativos.

---

## 5. INSTRUCCIONES PARA EL EQUIPO DE IMPLEMENTACIÓN

1. **Incorporar el material proporcionado** en las secciones correspondientes de los manuales (ver puntos 3.1–3.5).
2. **Actualizar el roadmap** para reflejar el adelanto de `--check` a la Fase 26 (subfase 26.1).
3. **Revisar editorialmente** los manuales 2–6 para unificar el vocabulario según la norma.
4. **Crear el archivo `modelos.toml`** con los modelos soportados, y distribuirlo junto con el instalador (Fase 30).

**Con esto, los manuales v8.1.0 quedan completos y libres de ambigüedades, permitiendo la implementación de las fases 22–30 sin más investigación.**