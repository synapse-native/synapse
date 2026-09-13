# MANUAL 32: AGENTE DE CODIFICACIÓN AVANZADO Y MEMORIA PERSISTENTE

**Archivo:** `32_AGENTE_AVANZADO_Y_MEMORIA.md`  
**Versión:** 8.3.0-industrial  
**Propósito:** Especificar la Fase 32 del ecosistema Synapse/Syquex/OpenSyn. Esta fase transforma a OpenSyn de un asistente de código en un **agente de codificación autónomo de grado industrial**, incorporando: grafo de conocimiento construido desde el AST canónico, memoria persistente cifrada, análisis de impacto determinista, pipeline multi-agente optimizado para hardware local, verificación AOT con auto-refutación, y modos de operación especializados. El objetivo es superar a OpenCode, Kilo, Claude Code, Codex y Cursor en el único eje donde podemos ganar: **contexto profundo + confianza verificable + privacidad absoluta**.

---

## 1. VISIÓN GENERAL DE LA FASE 32

### 1.1. El Diferenciador Estratégico

OpenCode, Cursor, Claude Code y Codex compiten en velocidad de generación de código. Ese eje es un **commodity**: la ejecución técnica (LLM → código) ya está resuelta y todos la tienen.

La ventaja competitiva real está en **la capa de contexto y confianza**:

| Eje | Competidores | OpenSyn Fase 32 |
|-----|--------------|-----------------|
| Velocidad de generación | Optimizado | Importante, pero no crítico |
| Contexto del sistema | Heurístico (embeddings, grep) | **Determinista desde el AST** |
| Análisis de impacto | Aproximado (LLM) | **Exacto (grafo O(V+E))** |
| Memoria entre sesiones | Limitada o nula | **Persistente y cifrada** |
| Verificación del código | Tests + linters externos | **Auto-refutación AOT + grafo de contratos** |
| Privacidad | Cloud con telemetría | **100% local, cero telemetría** |

**La regla de oro de la Fase 32:** ningún competidor puede replicar nuestro grafo de conocimiento porque ninguno controla el AST del compilador. Esa es nuestra ventaja estructural.

### 1.2. Los Cinco Componentes de la Fase 32

| Componente | Descripción | Archivo principal |
|------------|-------------|-------------------|
| **32.1 Grafo de Conocimiento** | Construcción de grafo de dependencias y contratos desde `SemNodo[]` | `nucleo/grafo_builder.syn` |
| **32.2 Memoria Persistente Cifrada** | Tres capas de memoria (sesión, evolución, proyecto) con cifrado AES-XSalsa20 | `opensyn/memoria.syn` |
| **32.3 Análisis de Impacto Determinista** | Algoritmos BFS/DFS/Tarjan sobre el grafo, sin LLM | `opensyn/explorer_det.syn`, `opensyn/architect_det.syn` |
| **32.4 Pipeline Multi-Agente Optimizado** | 2-3 inferencias máximo (Coder + Reviewer + Fixer opcional) | `opensyn/orquestador_multi.syn` |
| **32.5 Verificación AOT con Auto-Refutación** | Casos límite autogenerados, compilados y ejecutados con timeout | `opensyn/verificacion.syn` + `runtime/core/proceso.c` |

### 1.3. Alcance Explícitamente Descartado

Los siguientes elementos **NO** forman parte de la Fase 32 y se posponen indefinidamente por abrir vectores de ataque innecesarios o no aportar valor significativo:

- ❌ Sistema de plugins (superficie de ataque)
- ❌ Soporte MCP (integración con herramientas externas)
- ❌ Panel visual de grafo (mejora cosmética, no funcional)
- ❌ App GUI/escritorio (la TUI + extensión VS Code cubren el 90% del uso)
- ❌ Cualquier integración cloud, telemetría o gateway externo

**Duración total de la Fase 32:** 8 meses (reducido de 17 según auditoría técnica).

---

## 2. COMPONENTE 32.1: GRAFO DE CONOCIMIENTO

### 2.1. Objetivo

Construir un grafo dirigido de dependencias, contratos y relaciones entre todos los nodos del proyecto, **directamente desde el AST canónico (`SemNodo[]`) durante el pipeline del compilador**, sin análisis heurístico ni embeddings.

### 2.2. Ventaja Estructural

Al construir el grafo en el compilador:
- **Cero alucinaciones:** El grafo refleja exactamente lo que el compilador ve.
- **Determinista:** El mismo AST produce el mismo grafo (hash SHA-256 idéntico).
- **Sin coste adicional:** Se genera durante cualquier compilación, no en un paso separado.

### 2.3. Ubicación en el Pipeline

```
[Fuente .syn/.syq] → Lexer → Parser → AST
                                        ↓
                                    Traductor (Syquex)
                                        ↓
                                    SemNodo[]
                                        ↓
        ┌───────────────────────────────┼───────────────────────────────┐
        ↓                               ↓                               ↓
  Analizador Semántico          GRAFO BUILDER (32.1)              Generador C
        ↓                               ↓                               ↓
  AST Validado                    Grafo Proyecto                  Código C
                                        ↓
                                  (cacheado por hash)
```

### 2.4. Estructura del Grafo

**Archivo:** `nucleo/grafo_builder.syn`

```synapse
#lang: es
// nucleo/grafo_builder.syn
// Construye el grafo de conocimiento desde el AST canónico.
// Se ejecuta en la Pasada 3 del analizador semántico.

estructura NodoGrafo:
    id: texto                      // "src/web/handlers.syq.handle_req"
    tipo: texto                    // "funcion", "estructura", "modulo", "constante"
    archivo: texto
    linea: entero
    columna: entero
    firma: texto                   // Firma completa de la función
    num_dependientes: entero       // Cuántos nodos dependen de este
    num_dependencias: entero       // Cuántos nodos usa este
    contratos: Lista<ContratoInfo> // requiere/garantiza
    es_publico: booleano           // Tiene @export o está en un módulo público
    nivel_riesgo: texto            // "bajo", "medio", "alto", "crítico"

estructura ContratoInfo:
    tipo: texto                    // "requiere" o "garantiza"
    expresion: texto               // La expresión booleana
    linea: entero

estructura AristaGrafo:
    origen_id: texto
    destino_id: texto
    tipo: texto                    // "llamada", "importacion", "herencia", "uso_tipo"
    es_contrato_critico: booleano  // Si la API destino tiene > 5 dependientes
    linea: entero

estructura GrafoProyecto:
    proyecto: texto
    hash_ast: texto                // SHA-256 del SemNodo[]
    timestamp: entero
    nodos: Lista<NodoGrafo>
    aristas: Lista<AristaGrafo>
    indice_por_id: Mapa<texto, entero>  // id -> índice en nodos
    metricas: MetricasGrafo

estructura MetricasGrafo:
    total_nodos: entero
    total_aristas: entero
    max_dependientes: entero
    densidad: decimal
    ciclos_detectados: entero

// ============================================================
// FUNCIÓN PRINCIPAL
// ============================================================

funcion construir_grafo_desde_semnodo(semnodos: SemNodo[], total: entero, proyecto: texto) -> GrafoProyecto:
    let grafo = GrafoProyecto(
        proyecto: proyecto,
        hash_ast: calcular_hash_ast(semnodos, total),
        timestamp: tiempo_actual(),
        nodos: Lista<NodoGrafo>(),
        aristas: Lista<AristaGrafo>(),
        indice_por_id: Mapa<texto, entero>(),
        metricas: MetricasGrafo()
    )
    
    // PASADA 1: Crear nodos
    para i = 0 mientras i < total:
        let semnodo = semnodos[i]
        si semnodo.tipo_nodo == NODO_FUNCION o semnodo.tipo_nodo == NODO_ESTRUCTURA:
            let id = construir_id_nodo(semnodo)
            let nodo = NodoGrafo(
                id: id,
                tipo: tipo_nodo_a_texto(semnodo.tipo_nodo),
                archivo: semnodo.archivo,
                linea: semnodo.linea,
                columna: semnodo.columna,
                firma: extraer_firma(semnodo),
                num_dependientes: 0,
                num_dependencias: 0,
                contratos: extraer_contratos(semnodo),
                es_publico: semnodo.es_exportado,
                nivel_riesgo: "bajo"
            )
            grafo.indice_por_id[id] = grafo.nodos.len()
            grafo.nodos.agregar(nodo)
    
    // PASADA 2: Crear aristas (llamadas, importaciones, uso de tipos)
    para i = 0 mientras i < total:
        let semnodo = semnodos[i]
        coincidir semnodo.tipo_nodo:
            NODO_LLAMADA:
                let origen = construir_id_nodo_desde_contexto(semnodo, semnodos, total)
                let destino = semnodo.archivo + "." + semnodo.llamada.nombre
                _agregar_arista(grafo, origen, destino, "llamada", semnodo.linea)
            NODO_IMPORT:
                let origen = semnodo.archivo
                let destino = semnodo.import.ruta
                _agregar_arista(grafo, origen, destino, "importacion", semnodo.linea)
            NODO_TIPO:
                // Uso de tipos en parámetros/retornos
                para tipo_usado en extraer_tipos_usados(semnodo):
                    let origen = construir_id_nodo_desde_contexto(semnodo, semnodos, total)
                    _agregar_arista(grafo, origen, tipo_usado, "uso_tipo", semnodo.linea)
    
    // PASADA 3: Calcular dependientes (índice invertido)
    para arista en grafo.aristas:
        let idx_origen = grafo.indice_por_id.obtener(arista.origen_id)
        let idx_destino = grafo.indice_por_id.obtener(arista.destino_id)
        si idx_origen != nulo:
            grafo.nodos[idx_origen].num_dependencias = grafo.nodos[idx_origen].num_dependencias + 1
        si idx_destino != nulo:
            grafo.nodos[idx_destino].num_dependientes = grafo.nodos[idx_destino].num_dependientes + 1
            // Marcar contrato crítico
            si grafo.nodos[idx_destino].num_dependientes > 5:
                arista.es_contrato_critico = verdadero
    
    // PASADA 4: Calcular nivel de riesgo
    para nodo en grafo.nodos:
        nodo.nivel_riesgo = calcular_nivel_riesgo(nodo)
    
    // PASADA 5: Detectar ciclos (Tarjan)
    grafo.metricas.ciclos_detectados = contar_ciclos_tarjan(grafo)
    
    // PASADA 6: Calcular métricas agregadas
    grafo.metricas.total_nodos = grafo.nodos.len()
    grafo.metricas.total_aristas = grafo.aristas.len()
    grafo.metricas.max_dependientes = max_por_campo(grafo.nodos, "num_dependientes")
    grafo.metricas.densidad = calcular_densidad(grafo)
    
    retornar grafo

// ============================================================
// FUNCIONES AUXILIARES
// ============================================================

funcion construir_id_nodo(semnodo: SemNodo) -> texto:
    retornar semnodo.archivo + "." + semnodo.funcion.nombre

funcion calcular_nivel_riesgo(nodo: NodoGrafo) -> texto:
    si nodo.num_dependientes > 20 o nodo.es_publico:
        retornar "crítico"
    si nodo.num_dependientes > 10:
        retornar "alto"
    si nodo.num_dependientes > 5:
        retornar "medio"
    retornar "bajo"

funcion calcular_hash_ast(semnodos: SemNodo[], total: entero) -> texto:
    // Serializar AST a JSON canónico (orden alfabético de campos)
    let json = serializar_ast_canonico(semnodos, total)
    retornar sha256(json)

// ============================================================
// PERSISTENCIA DEL GRAFO
// ============================================================

funcion grafo_guardar(grafo: GrafoProyecto, ruta: texto) -> Resultado<nulo, texto>:
    // Guardar como JSON comprimido con gzip
    let json = grafo_a_json(grafo)
    let comprimido = gzip_comprimir(json)
    escribir_archivo(ruta, comprimido)
    retornar ok()

funcion grafo_cargar(ruta: texto) -> Resultado<GrafoProyecto, texto>:
    let contenido = leer_archivo(ruta)?
    let json = gzip_descomprimir(contenido)?
    retornar ok(json_a_grafo(json))
```

### 2.5. Persistencia y Caché

El grafo se guarda en `~/.synapse/cache/grafo/<hash_ast>.json.gz`. Si el AST no cambia (mismo hash), el grafo se reutiliza.

### 2.6. Criterios de Aceptación

- Construir grafo de un proyecto de 1,000 archivos en < 100 ms.
- Grafo es determinista: mismo AST → mismo hash SHA-256.
- Sin fugas de memoria (ASan).
- Persistencia funciona: cargar grafo cacheado es < 10 ms.

---

## 3. COMPONENTE 32.2: MEMORIA PERSISTENTE CIFRADA

### 3.1. Objetivo

Implementar tres capas de memoria persistente **cifradas en reposo**, usando exclusivamente las primitivas criptográficas del ecosistema (TweetNaCl/XSalsa20-Poly1305), sin dependencias externas.

### 3.2. Las Tres Capas

| Capa | Persistencia | Contenido | Cifrado |
|------|--------------|-----------|---------|
| **Sesión** | RAM, volátil | Contexto actual, turnos, referencias | No (efímero) |
| **Evolución** | SQLite cifrado | Patrones, fallos, aprendizajes | AES-XSalsa20-Poly1305 |
| **Proyecto** | JSON cifrado | Estructura, dependencias, historial | AES-XSalsa20-Poly1305 |

### 3.3. Derivación de Clave

**Archivo:** `runtime/core/key_derivation.c`

```c
// runtime/core/key_derivation.c
// Derivación de clave maestra usando Argon2id + hardware UUID

#include <stdint.h>
#include <string.h>
#include "key_derivation.h"

// Argon2id (implementación ligera embebida, sin dependencias externas)
int argon2id_derivar(
    const uint8_t* passphrase, size_t pass_len,
    const uint8_t* salt, size_t salt_len,
    uint32_t iteraciones, uint32_t memoria_kb, uint32_t paralelismo,
    uint8_t* salida, size_t salida_len
);

// Derivación completa
int key_derivation_maestra(
    const char* passphrase,
    const char* hardware_uuid,
    const char* machine_id,
    uint8_t* clave_salida /* 32 bytes */
) {
    // 1. Construir salt desde hardware + machine_id
    uint8_t salt[64];
    size_t salt_len = 0;
    
    memcpy(salt, hardware_uuid, strlen(hardware_uuid));
    salt_len += strlen(hardware_uuid);
    memcpy(salt + salt_len, machine_id, strlen(machine_id));
    salt_len += strlen(machine_id);
    
    // Hash del salt para tamaño fijo
    uint8_t salt_hash[32];
    sha256(salt, salt_len, salt_hash);
    
    // 2. Derivar con Argon2id (parámetros: 3 iteraciones, 64 MB, 4 hilos)
    return argon2id_derivar(
        (const uint8_t*)passphrase, strlen(passphrase),
        salt_hash, 32,
        3,          // iteraciones
        64 * 1024,  // memoria KB (64 MB)
        4,          // paralelismo
        clave_salida, 32
    );
}
```

### 3.4. Estructura de la Memoria Cifrada

**Archivo:** `opensyn/memoria.syn`

```synapse
#lang: es
// opensyn/memoria.syn
// Memoria persistente cifrada del agente OpenSyn.
// Tres capas: sesión (RAM), evolución (SQLite cifrado), proyecto (JSON cifrado).
// Cifrado: XSalsa20-Poly1305 (TweetNaCl) con clave derivada de Argon2id.

importar std.io
importar std.json
importar std.crypto
importar std.os
importar std.tiempo

// ============================================================
// ESTADO GLOBAL
// ============================================================

// Clave maestra: NUNCA se escribe a disco. Solo en RAM.
var _clave_maestra: bytes(32) = bytes_vacios(32)
var _clave_inicializada: booleano = falso
var _db_evolucion: puntero = nulo
var _indice_contexto: Mapa<texto, Lista<entero>> = Mapa()

// ============================================================
// ESTRUCTURAS
// ============================================================

estructura PatronAprendido:
    id: entero
    patron: texto
    contexto: texto
    exito_ratio: decimal
    num_usos: entero
    ultimo_uso: entero

estructura MemoriaNegativa:
    id: entero
    intento_fallido: texto
    razon_fallo: texto
    solucion_correcta: texto
    fecha: entero

estructura EntradaCifrada:
    nonce: bytes(24)
    cifrado: bytes
    tag: bytes(16)

// ============================================================
// INICIALIZACIÓN
// ============================================================

funcion memoria_inicializar(passphrase: texto) -> Resultado<nulo, texto>:
    // 1. Derivar clave maestra del hardware + passphrase
    let hw_uuid = os.hardware_uuid()
    let machine_id = os.machine_id()
    
    _clave_maestra = crypto_argon2id(
        passphrase,
        salt: sha256(hw_uuid + machine_id),
        iteraciones: 3,
        memoria_mb: 64,
        paralelismo: 4,
        longitud: 32
    )
    
    // 2. Abrir SQLite cifrado
    let ruta = os.home() + "/.opensyn/memoria.db"
    _db_evolucion = abrir_db_cifrada(ruta, _clave_maestra)?
    
    si _db_evolucion == nulo:
        retornar err("No se pudo abrir la base de datos cifrada")
    
    // 3. Verificar integridad (MAC sobre header)
    si no verificar_header_db(_db_evolucion, _clave_maestra):
        retornar err("DB corrupta o clave incorrecta")
    
    // 4. Crear tablas si no existen
    ejecutar_sql(_db_evolucion, 
        "CREATE TABLE IF NOT EXISTS patrones (
            id INTEGER PRIMARY KEY,
            nonce BLOB NOT NULL,
            datos BLOB NOT NULL
        )")
    ejecutar_sql(_db_evolucion,
        "CREATE TABLE IF NOT EXISTS fallos (
            id INTEGER PRIMARY KEY,
            nonce BLOB NOT NULL,
            datos BLOB NOT NULL
        )")
    ejecutar_sql(_db_evolucion,
        "CREATE TABLE IF NOT EXISTS proyecto (
            id INTEGER PRIMARY KEY,
            hash_ast TEXT NOT NULL,
            nonce BLOB NOT NULL,
            datos BLOB NOT NULL
        )")
    
    // 5. Construir índice en RAM para búsquedas rápidas
    _indice_contexto = construir_indice_contexto(_db_evolucion, _clave_maestra)
    
    _clave_inicializada = verdadero
    retornar ok()

// ============================================================
// CAPA 2: MEMORIA DE EVOLUCIÓN (patrones + fallos)
// ============================================================

funcion memoria_guardar_patron(patron: texto, contexto: texto, exito: decimal) -> Resultado<nulo, texto>:
    si no _clave_inicializada:
        retornar err("Memoria no inicializada")
    
    // 1. Serializar
    let entrada = json_stringificar({
        "patron": patron,
        "contexto": contexto,
        "exito": exito,
        "timestamp": tiempo_actual()
    })
    
    // 2. Cifrar con XSalsa20-Poly1305
    let nonce = crypto_randombytes(24)
    let cifrado = crypto_secretbox(entrada, nonce, _clave_maestra)
    
    // 3. Guardar blob cifrado
    let sql = "INSERT INTO patrones (nonce, datos) VALUES (?, ?)"
    ejecutar_sql_blob(_db_evolucion, sql, nonce, cifrado)
    
    // 4. Actualizar índice en RAM
    let id = ultimo_id_insertado(_db_evolucion)
    para palabra en tokenizar(contexto):
        _indice_contexto.obtener_o_crear(palabra).agregar(id)
    
    retornar ok()

funcion memoria_consultar_patrones(contexto: texto) -> Lista<PatronAprendido>:
    si no _clave_inicializada:
        retornar Lista<PatronAprendido>()
    
    // 1. Buscar IDs candidatos vía índice en RAM
    let ids_candidatos = Set<entero>()
    para palabra en tokenizar(contexto):
        si palabra en _indice_contexto:
            para id en _indice_contexto[palabra]:
                ids_candidatos.agregar(id)
    
    // 2. Descifrar solo los candidatos (no toda la DB)
    let resultados = Lista<PatronAprendido>()
    para id en ids_candidatos:
        let (nonce, cifrado) = leer_patron_por_id(_db_evolucion, id)
        let descifrado = crypto_secretbox_open(cifrado, nonce, _clave_maestra)
        si descifrado.es_error:
            continuar
        let patron = json_parsear(descifrado.texto)
        resultados.agregar(PatronAprendido(
            id: id,
            patron: patron.patron,
            contexto: patron.contexto,
            exito_ratio: patron.exito,
            num_usos: 1,
            ultimo_uso: patron.timestamp
        ))
    
    // 3. Ordenar por éxito y limitar
    resultados.ordenar_por(p -> p.exito_ratio, descendente: verdadero)
    retornar resultados.limitar(10)

funcion memoria_registrar_fallo(intento: texto, razon: texto, solucion: texto) -> Resultado<nulo, texto>:
    si no _clave_inicializada:
        retornar err("Memoria no inicializada")
    
    let entrada = json_stringificar({
        "intento": intento,
        "razon": razon,
        "solucion": solucion,
        "fecha": tiempo_actual()
    })
    
    let nonce = crypto_randombytes(24)
    let cifrado = crypto_secretbox(entrada, nonce, _clave_maestra)
    
    let sql = "INSERT INTO fallos (nonce, datos) VALUES (?, ?)"
    ejecutar_sql_blob(_db_evolucion, sql, nonce, cifrado)
    
    retornar ok()

funcion memoria_evitar_fallos(contexto: texto) -> Lista<MemoriaNegativa>:
    // Similar a consultar_patrones, pero sobre la tabla de fallos
    // Busca fallos previos que compartan palabras clave con el contexto actual
    let ids_candidatos = buscar_por_contexto(_db_evolucion, "fallos", contexto, _clave_maestra)
    let resultados = Lista<MemoriaNegativa>()
    
    para id en ids_candidatos:
        let (nonce, cifrado) = leer_fallo_por_id(_db_evolucion, id)
        let descifrado = crypto_secretbox_open(cifrado, nonce, _clave_maestra)
        si descifrado.es_error:
            continuar
        let fallo = json_parsear(descifrado.texto)
        resultados.agregar(MemoriaNegativa(
            id: id,
            intento_fallido: fallo.intento,
            razon_fallo: fallo.razon,
            solucion_correcta: fallo.solucion,
            fecha: fallo.fecha
        ))
    
    retornar resultados.limitar(5)

// ============================================================
// CAPA 3: MEMORIA DE PROYECTO
// ============================================================

funcion memoria_guardar_proyecto(hash_ast: texto, datos: texto) -> Resultado<nulo, texto>:
    let entrada = json_stringificar({
        "hash_ast": hash_ast,
        "datos": datos,
        "timestamp": tiempo_actual()
    })
    
    let nonce = crypto_randombytes(24)
    let cifrado = crypto_secretbox(entrada, nonce, _clave_maestra)
    
    // Reemplazar entrada existente para el mismo hash_ast
    ejecutar_sql_blob(_db_evolucion,
        "INSERT OR REPLACE INTO proyecto (hash_ast, nonce, datos) VALUES (?, ?, ?)",
        hash_ast, nonce, cifrado)
    
    retornar ok()

// ============================================================
// CIERRE Y LIMPIEZA
// ============================================================

funcion memoria_cerrar():
    // Limpiar clave de memoria (zeroing)
    crypto_memzero(_clave_maestra)
    _clave_inicializada = falso
    
    si _db_evolucion != nulo:
        cerrar_db(_db_evolucion)
        _db_evolucion = nulo
    
    _indice_contexto.limpiar()
```

### 3.5. Integración con el Pipeline RAG

**Modificación en `synapse_rag.c`:**

```c
void rag_construir_prompt_con_memoria(RagContext* ctx, int n_ctx) {
    // 1. Consultar patrones relevantes
    ListaPatrones* patrones = memoria_consultar_patrones(ctx->instruccion);
    
    // 2. Consultar fallos previos similares
    ListaFallos* fallos = memoria_evitar_fallos(ctx->instruccion);
    
    // 3. Inyectar en el prompt
    char* bloque_memoria = "";
    
    if (patrones->num > 0) {
        bloque_memoria = concatenar(bloque_memoria, 
            "\n# PATRONES EXITOSOS EN CONTEXTOS SIMILARES:\n");
        for (int i = 0; i < patrones->num; i++) {
            bloque_memoria = concatenar(bloque_memoria, "- ");
            bloque_memoria = concatenar(bloque_memoria, patrones->items[i].patron);
            bloque_memoria = concatenar(bloque_memoria, " (éxito: ");
            bloque_memoria = concatenar(bloque_memoria, 
                a_texto(patrones->items[i].exito_ratio));
            bloque_memoria = concatenar(bloque_memoria, ")\n");
        }
    }
    
    if (fallos->num > 0) {
        bloque_memoria = concatenar(bloque_memoria,
            "\n# ENFOQUES QUE FALLARON (EVITAR):\n");
        for (int i = 0; i < fallos->num; i++) {
            bloque_memoria = concatenar(bloque_memoria, "- NO ");
            bloque_memoria = concatenar(bloque_memoria, fallos->items[i].intento_fallido);
            bloque_memoria = concatenar(bloque_memoria, " porque ");
            bloque_memoria = concatenar(bloque_memoria, fallos->items[i].razon_fallo);
            bloque_memoria = concatenar(bloque_memoria, ". En su lugar: ");
            bloque_memoria = concatenar(bloque_memoria, fallos->items[i].solucion_correcta);
            bloque_memoria = concatenar(bloque_memoria, "\n");
        }
    }
    
    // 4. Añadir al contexto del prompt
    ctx->memoria = bloque_memoria;
}
```

### 3.6. Ciclo de Feedback Automático

Cuando el usuario corrige el código generado por OpenSyn:

```synapse
// En el LSP, cuando se detecta una corrección manual
funcion registrar_feedback(codigo_generado: texto, codigo_corregido: texto, error: texto):
    // Calcular diff
    let diff = calcular_diff(codigo_generado, codigo_corregido)
    
    // Registrar el fallo con la solución
    memoria_registrar_fallo(
        intento: codigo_generado,
        razon: error,
        solucion: codigo_corregido
    )
    
    // Si el resultado final es correcto, registrar como patrón
    si error == "":
        memoria_guardar_patron(
            patron: extraer_patron(codigo_corregido),
            contexto: extraer_contexto(codigo_corregido),
            exito: 1.0
        )
```

### 3.7. Criterios de Aceptación

- `strings ~/.opensyn/memoria.db` no muestra texto legible.
- La clave nunca se escribe a disco, logs ni archivos temporales.
- El descifrado de 100 entradas tarda < 50 ms (con índice en RAM).
- Derivación de clave con Argon2id tarda < 500 ms.
- Al reiniciar OpenSyn sin passphrase, la memoria no es accesible.

---

## 4. COMPONENTE 32.3: ANÁLISIS DE IMPACTO DETERMINISTA

### 4.1. Objetivo

Implementar el análisis de impacto **sin LLM**, usando algoritmos de teoría de grafos sobre el grafo de conocimiento (32.1). Esto elimina alucinaciones y reduce la latencia de segundos a milisegundos.

### 4.2. Regla Arquitectónica

| Fase del pipeline | Herramienta | Coste |
|-------------------|-------------|-------|
| Explorer (encontrar archivos relevantes) | BFS sobre grafo | O(V+E), < 1 ms |
| Architect (análisis de impacto) | DFS invertido + Tarjan | O(V+E), < 5 ms |
| Coder (escribir código) | LLM | ~10 s |
| Reviewer (criticar) | LLM | ~10 s |
| Fixer (corregir) | LLM (solo si Reviewer falla) | ~10 s |

**Total:** 2-3 inferencias máximo, ~20-30 segundos por ciclo.

### 4.3. Explorer Determinista

**Archivo:** `opensyn/explorer_det.syn`

```synapse
#lang: es
// opensyn/explorer_det.syn
// Explorer determinista: BFS sobre el grafo para encontrar archivos relevantes.
// NO usa LLM. O(V+E).

importar std.grafo
importar std.lista

estructura ArchivoRelevante:
    archivo: texto
    razon: texto
    distancia: entero
    tipo_relacion: texto

funcion explorar_contexto(archivo_objetivo: texto, grafo: GrafoProyecto, radio: entero) -> Lista<ArchivoRelevante>:
    // BFS desde el archivo objetivo hasta `radio` niveles
    let visitados = Set<texto>()
    let cola = Cola<texto>()
    let resultados = Lista<ArchivoRelevante>()
    
    cola.encolar(archivo_objetivo)
    visitados.agregar(archivo_objetivo)
    
    mientras no cola.vacia():
        let actual = cola.desencolar()
        let nodo = grafo.buscar_nodo(actual)
        si nodo == nulo:
            continuar
        
        // Añadir archivos que este nodo usa
        para dep_id en nodo.dependencias:
            si dep_id no en visitados:
                visitados.agregar(dep_id)
                let dep = grafo.buscar_nodo(dep_id)
                resultados.agregar(ArchivoRelevante(
                    archivo: dep.archivo,
                    razon: "dependencia directa de " + actual,
                    distancia: calcular_distancia(grafo, archivo_objetivo, dep_id),
                    tipo_relacion: "dependencia"
                ))
                si radio > 1:
                    cola.encolar(dep_id)
        
        // Añadir archivos que usan este nodo (dependientes)
        para dep_id en nodo.dependientes:
            si dep_id no en visitados:
                visitados.agregar(dep_id)
                let dep = grafo.buscar_nodo(dep_id)
                resultados.agregar(ArchivoRelevante(
                    archivo: dep.archivo,
                    razon: "usa " + actual,
                    distancia: calcular_distancia(grafo, archivo_objetivo, dep_id),
                    tipo_relacion: "dependiente"
                ))
                si radio > 1:
                    cola.encolar(dep_id)
    
    // Ordenar por distancia
    resultados.ordenar_por(r -> r.distancia, ascendente: verdadero)
    retornar resultados

funcion calcular_distancia(grafo: GrafoProyecto, origen: texto, destino: texto) -> entero:
    // BFS desde origen hasta destino
    let visitados = Set<texto>()
    let cola = Cola<(texto, entero)>()
    cola.encolar((origen, 0))
    visitados.agregar(origen)
    
    mientras no cola.vacia():
        let (actual, dist) = cola.desencolar()
        si actual == destino:
            retornar dist
        let nodo = grafo.buscar_nodo(actual)
        para vecino en nodo.dependencias + nodo.dependientes:
            si vecino no en visitados:
                visitados.agregar(vecino)
                cola.encolar((vecino, dist + 1))
    
    retornar -1  // No alcanzable
```

### 4.4. Architect Determinista

**Archivo:** `opensyn/architect_det.syn`

```synapse
#lang: es
// opensyn/architect_det.syn
// Architect determinista: análisis de impacto sin LLM.
// Usa DFS invertido + Tarjan para detección de ciclos.

importar std.grafo
importar std.lista

estructura AnalisisImpacto:
    nodos_afectados: Lista<NodoAfectado>
    contratos_criticos: Lista<ContratoCritico>
    ciclos: Lista<Ciclo>
    metricas: MetricasImpacto

estructura NodoAfectado:
    id: texto
    archivo: texto
    distancia: entero
    tipo_relacion: texto

estructura ContratoCritico:
    nodo_id: texto
    razon: texto
    nivel_riesgo: texto

estructura Ciclo:
    nodos: Lista<texto>
    longitud: entero

estructura MetricasImpacto:
    total_afectados: entero
    profundidad_maxima: entero
    contratos_criticos: entero
    ciclos_potenciales: entero

funcion analizar_impacto_completo(archivo: texto, grafo: GrafoProyecto) -> AnalisisImpacto:
    let nodos_afectados = Lista<NodoAfectado>()
    let contratos_criticos = Lista<ContratoCritico>()
    let ciclos_detectados = Lista<Ciclo>()
    
    let nodos_objetivo = grafo.buscar_nodos_por_archivo(archivo)
    
    para nodo in nodos_objetivo:
        // 1. Calcular dependientes transitivos (DFS invertido)
        let dependientes = dfs_invertido(nodo.id, grafo)
        para dep in dependientes:
            nodos_afectados.agregar(NodoAfectado(
                id: dep.id,
                archivo: dep.archivo,
                distancia: dep.distancia,
                tipo_relacion: dep.tipo_arista
            ))
        
        // 2. Detectar contratos críticos
        si nodo.num_dependientes > 5:
            contratos_criticos.agregar(ContratoCritico(
                nodo_id: nodo.id,
                razon: "API pública usada por " + a_texto(nodo.num_dependientes) + " módulos",
                nivel_riesgo: nodo.nivel_riesgo
            ))
        
        // 3. Detectar ciclos potenciales (Tarjan)
        let ciclo = detectar_ciclo_tarjan(nodo.id, grafo)
        si ciclo != nulo:
            ciclos_detectados.agregar(ciclo)
    
    // 4. Calcular métricas
    let metricas = MetricasImpacto(
        total_afectados: nodos_afectados.len(),
        profundidad_maxima: max_por_campo(nodos_afectados, "distancia"),
        contratos_criticos: contratos_criticos.len(),
        ciclos_potenciales: ciclos_detectados.len()
    )
    
    retornar AnalisisImpacto(
        nodos_afectados: nodos_afectados,
        contratos_criticos: contratos_criticos,
        ciclos: ciclos_detectados,
        metricas: metricas
    )

funcion dfs_invertido(id_inicio: texto, grafo: GrafoProyecto) -> Lista<(texto, entero, texto)>:
    // DFS sobre dependientes (aristas invertidas)
    let visitados = Set<texto>()
    let resultados = Lista<(texto, entero, texto)>()
    let pila = Pila<(texto, entero)>()
    
    pila.apilar((id_inicio, 0))
    
    mientras no pila.vacia():
        let (actual, dist) = pila.desapilar()
        si actual en visitados:
            continuar
        visitados.agregar(actual)
        
        let nodo = grafo.buscar_nodo(actual)
        para dep_id en nodo.dependientes:
            si dep_id no en visitados:
                resultados.agregar((dep_id, dist + 1, "llamada"))
                pila.apilar((dep_id, dist + 1))
    
    retornar resultados

funcion detectar_ciclo_tarjan(id_inicio: texto, grafo: GrafoProyecto) -> Ciclo:
    // Implementación de Tarjan para SCC (Strongly Connected Components)
    // Si el SCC tiene > 1 nodo, hay un ciclo
    let scc = tarjan_scc(id_inicio, grafo)
    si scc.len() > 1:
        retornar Ciclo(nodos: scc, longitud: scc.len())
    retornar nulo
```

### 4.5. Integración en el Prompt

```synapse
funcion generar_prompt_con_impacto(archivo: texto, instruccion: texto, grafo: GrafoProyecto) -> texto:
    let impacto = analizar_impacto_completo(archivo, grafo)
    
    let prompt_impacto = "# ANÁLISIS DE IMPACTO (DETERMINISTA):\n\n"
    
    si impacto.metricas.total_afectados == 0:
        prompt_impacto = prompt_impacto + "Ningún nodo afectado. Cambio localizado.\n"
    sino:
        prompt_impacto = prompt_impacto + "Nodos afectados: " + a_texto(impacto.metricas.total_afectados) + "\n"
        para nodo in impacto.nodos_afectados.limitar(10):
            prompt_impacto = prompt_impacto + "- `" + nodo.id + "` (distancia: " + a_texto(nodo.distancia) + ")\n"
    
    si impacto.contratos_criticos.len() > 0:
        prompt_impacto = prompt_impacto + "\n## CONTRATOS CRÍTICOS (NO ROMPER):\n"
        para contrato in impacto.contratos_criticos:
            prompt_impacto = prompt_impacto + "- `" + contrato.nodo_id + "`: " + contrato.razon + "\n"
    
    si impacto.ciclos.len() > 0:
        prompt_impacto = prompt_impacto + "\n## CICLOS DETECTADOS (PRECAUCIÓN):\n"
        para ciclo in impacto.ciclos:
            prompt_impacto = prompt_impacto + "- Ciclo de " + a_texto(ciclo.longitud) + " nodos\n"
    
    retornar prompt_impacto + "\n" + instruccion
```

### 4.6. Criterios de Aceptación

- BFS de dependencias: < 1 ms en proyecto de 1,000 archivos.
- Análisis de impacto completo: < 5 ms.
- Detección de ciclos: O(V+E), correcta según Tarjan.
- Cero falsos positivos en 100 proyectos de prueba.

---

## 5. COMPONENTE 32.4: PIPELINE MULTI-AGENTE OPTIMIZADO

### 5.1. Objetivo

Implementar un pipeline multi-agente **secuencial con 2-3 inferencias máximo**, donde los roles deterministas (Explorer, Architect) se resuelven con el grafo (32.3) y solo los roles creativos (Coder, Reviewer, Fixer) usan LLM.

### 5.2. Los Tres Roles con LLM

| Rol | Propósito | Cuándo se ejecuta |
|-----|-----------|-------------------|
| **Coder** | Implementar el cambio | Siempre |
| **Reviewer** | Criticar el código generado | Siempre |
| **Fixer** | Corregir basándose en críticas | Solo si Reviewer detecta problemas |

### 5.3. Pipeline Completo

**Archivo:** `opensyn/orquestador_multi.syn`

```synapse
#lang: es
// opensyn/orquestador_multi.syn
// Pipeline multi-agente optimizado: 2-3 inferencias máximo.

importar std.grafo
importar std.io
importar opensyn.explorer_det
importar opensyn.architect_det
importar opensyn.validation_loop

estructura ContextoPipeline:
    instruccion: texto
    archivo: texto
    grafo: GrafoProyecto
    archivos_relevantes: Lista<ArchivoRelevante>
    analisis_impacto: AnalisisImpacto
    codigo_generado: texto
    criticas: texto
    codigo_final: texto

estructura ResultadoPipeline:
    exito: booleano
    codigo: texto
    razonamiento: texto
    num_inferencias: entero
    tiempo_total_ms: entero

funcion ejecutar_pipeline(instruccion: texto, archivo: texto) -> ResultadoPipeline:
    let inicio = tiempo_actual_ms()
    let grafo = cargar_grafo_proyecto()
    let contexto = ContextoPipeline(
        instruccion: instruccion,
        archivo: archivo,
        grafo: grafo,
        archivos_relevantes: Lista<ArchivoRelevante>(),
        analisis_impacto: nulo,
        codigo_generado: "",
        criticas: "",
        codigo_final: ""
    )
    
    // ============================================================
    // FASE 1: EXPLORER (determinista, sin LLM)
    // ============================================================
    contexto.archivos_relevantes = explorer_det.explorar_contexto(archivo, grafo, radio: 2)
    
    // ============================================================
    // FASE 2: ARCHITECT (determinista, sin LLM)
    // ============================================================
    contexto.analisis_impacto = architect_det.analizar_impacto_completo(archivo, grafo)
    
    // ============================================================
    // FASE 3: CODER (LLM)
    // ============================================================
    let prompt_coder = construir_prompt_coder(contexto)
    let respuesta_coder = llama_client.completar(prompt_coder, max_tokens: 2048, temperature: 0.3)
    contexto.codigo_generado = extraer_codigo(respuesta_coder)
    
    // Validar con compilador
    si no validar_codigo(contexto.codigo_generado):
        // El bucle de validación (32.5) se encarga de los reintentos
        let corregido = validation_loop.corregir(contexto.codigo_generado, archivo)
        si corregido.es_error:
            retornar ResultadoPipeline(exito: falso, codigo: contexto.codigo_generado,
                                        razonamiento: corregido.error, num_inferencias: 2, tiempo_total_ms: tiempo_actual_ms() - inicio)
        contexto.codigo_generado = corregido.codigo
    
    // ============================================================
    // FASE 4: REVIEWER (LLM)
    // ============================================================
    let prompt_reviewer = construir_prompt_reviewer(contexto)
    let respuesta_reviewer = llama_client.completar(prompt_reviewer, max_tokens: 1024, temperature: 0.2)
    contexto.criticas = respuesta_reviewer
    
    // ============================================================
    // FASE 5: FIXER (LLM, solo si hay críticas)
    // ============================================================
    si tiene_criticas_relevantes(contexto.criticas):
        let prompt_fixer = construir_prompt_fixer(contexto)
        let respuesta_fixer = llama_client.completar(prompt_fixer, max_tokens: 2048, temperature: 0.3)
        contexto.codigo_final = extraer_codigo(respuesta_fixer)
    sino:
        contexto.codigo_final = contexto.codigo_generado
    
    // Validación final
    si no validar_codigo(contexto.codigo_final):
        retornar ResultadoPipeline(exito: falso, codigo: contexto.codigo_final,
                                    razonamiento: "Código final no compila", num_inferencias: 3, tiempo_total_ms: tiempo_actual_ms() - inicio)
    
    retornar ResultadoPipeline(
        exito: verdadero,
        codigo: contexto.codigo_final,
        razonamiento: contexto.criticas,
        num_inferencias: si tiene_criticas_relevantes(contexto.criticas): 3 sino: 2,
        tiempo_total_ms: tiempo_actual_ms() - inicio
    )

// ============================================================
// CONSTRUCCIÓN DE PROMPTS
// ============================================================

funcion construir_prompt_coder(contexto: ContextoPipeline) -> texto:
    let prompt = "# CONTEXTO DEL PROYECTO\n\n"
    
    // Archivos relevantes
    prompt = prompt + "## Archivos relevantes:\n"
    para arch in contexto.archivos_relevantes.limitar(5):
        prompt = prompt + "- `" + arch.archivo + "` (" + arch.razon + ")\n"
    
    // Análisis de impacto
    prompt = prompt + "\n" + generar_prompt_con_impacto(contexto.archivo, contexto.instruccion, contexto.grafo)
    
    // Reglas del lenguaje
    prompt = prompt + "\n# REGLAS DE SINTAXIS (SYNAPSE/SYQUEX)\n"
    prompt = prompt + reglas_sintaxis_estaticas()
    
    // Instrucción
    prompt = prompt + "\n# INSTRUCCIÓN\n" + contexto.instruccion + "\n"
    prompt = prompt + "\nGenera SOLO el código, sin explicaciones.\n"
    
    retornar prompt

funcion construir_prompt_reviewer(contexto: ContextoPipeline) -> texto:
    let prompt = "# REVISIÓN DE CÓDIGO\n\n"
    prompt = prompt + "## Código a revisar:\n```\n" + contexto.codigo_generado + "\n```\n\n"
    prompt = prompt + "## Contexto:\n" + contexto.instruccion + "\n\n"
    prompt = prompt + "## Analiza y critica:\n"
    prompt = prompt + "1. ¿Compila correctamente?\n"
    prompt = prompt + "2. ¿Maneja casos límite?\n"
    prompt = prompt + "3. ¿Rompe contratos críticos?\n"
    prompt = prompt + "4. ¿Sigue las reglas de sintaxis?\n"
    prompt = prompt + "5. ¿Hay problemas de rendimiento?\n\n"
    prompt = prompt + "Sé brutalmente honesto. Si el código es bueno, dilo. Si tiene problemas, sé específico.\n"
    retornar prompt

funcion construir_prompt_fixer(contexto: ContextoPipeline) -> texto:
    let prompt = "# CORRECCIÓN DE CÓDIGO\n\n"
    prompt = prompt + "## Código original:\n```\n" + contexto.codigo_generado + "\n```\n\n"
    prompt = prompt + "## Críticas:\n" + contexto.criticas + "\n\n"
    prompt = prompt + "## Genera el código corregido:\n"
    prompt = prompt + "Aplica SOLO las correcciones necesarias. No refactorices innecesariamente.\n"
    retornar prompt
```

### 5.4. Modos de Operación

Los modos determinan qué fases del pipeline se ejecutan:

| Modo | Fases activas | Herramientas permitidas |
|------|---------------|-------------------------|
| **Ask** | Solo LLM explicativo | Lectura |
| **Plan** | Explorer + Architect | Lectura + escritura de plan |
| **Code** | Pipeline completo | Edición + validación |
| **Debug** | Explorer + Coder + Reviewer | Lectura + edición limitada |
| **Orchestrator** | Explorer + Architect + delegación | Solo coordinación |

### 5.5. Criterios de Aceptación

- Ciclo completo: 2-3 inferencias máximo.
- Tiempo total: < 30 segundos en hardware medio.
- Tasa de corrección exitosa en ≤3 intentos: > 95%.
- Latencia de fases deterministas (Explorer + Architect): < 6 ms.

---

## 6. COMPONENTE 32.5: VERIFICACIÓN AOT CON AUTO-REFUTACIÓN

### 6.1. Objetivo

Expandir el bucle de validación actual (`synapse check --no-emit`) con **auto-refutación**: generar casos límite, compilarlos y ejecutarlos para verificar que el código es robusto.

### 6.2. Aclaración sobre Ejecución

**Synapse es AOT, no interpretado.** La validación de casos límite **debe** pasar por el pipeline completo: compilar → enlazar → ejecutar. No existe un REPL o intérprete dinámico.

### 6.3. Pipeline AOT Asíncrono

**Archivo:** `opensyn/verificacion.syn`

```synapse
#lang: es
// opensyn/verificacion.syn
// Verificación AOT con auto-refutación.

importar std.io
importar std.os
importar std.proceso

estructura CasoLimite:
    descripcion: texto
    codigo_ejecucion: texto
    valor_esperado: texto

estructura ResultadoCaso:
    caso: CasoLimite
    estado: texto  // "completado", "timeout_compilacion", "timeout_ejecucion", "error_compilacion"
    codigo_salida: entero
    stdout: texto
    stderr: texto
    error: texto

funcion verificar_caso_limite(codigo: texto, caso: CasoLimite) -> ResultadoCaso:
    // 1. Crear archivo temporal con el código + el caso
    let archivo_temp = os.temp_file("opensyn_test_", ".syq")
    let codigo_completo = codigo + "\n\n" + caso.codigo_ejecucion
    escribir_archivo(archivo_temp, codigo_completo)
    
    // 2. Compilar AOT con timeout estricto (30 s)
    let resultado_compilacion = proceso.ejecutar_async(
        comando: "synapse build " + archivo_temp + " -o " + archivo_temp + ".exe",
        timeout_segundos: 30
    )
    
    si resultado_compilacion.timed_out:
        os.eliminar(archivo_temp)
        retornar ResultadoCaso(
            caso: caso,
            estado: "timeout_compilacion",
            error: "La compilación excedió 30 segundos"
        )
    
    si resultado_compilacion.codigo_salida != 0:
        os.eliminar(archivo_temp)
        retornar ResultadoCaso(
            caso: caso,
            estado: "error_compilacion",
            error: resultado_compilacion.stderr
        )
    
    // 3. Ejecutar el binario con timeout (5 s)
    let resultado_ejecucion = proceso.ejecutar_async(
        comando: archivo_temp + ".exe",
        timeout_segundos: 5
    )
    
    // 4. Limpiar archivos temporales
    os.eliminar(archivo_temp)
    os.eliminar(archivo_temp + ".exe")
    
    // 5. Interpretar resultado
    si resultado_ejecucion.timed_out:
        retornar ResultadoCaso(
            caso: caso,
            estado: "timeout_ejecucion",
            error: "El binario excedió 5 segundos (posible bucle infinito)"
        )
    
    retornar ResultadoCaso(
        caso: caso,
        estado: "completado",
        codigo_salida: resultado_ejecucion.codigo_salida,
        stdout: resultado_ejecucion.stdout,
        stderr: resultado_ejecucion.stderr
    )

// ============================================================
// GENERACIÓN DE CASOS LÍMITE
// ============================================================

funcion generar_casos_limite(codigo: texto) -> Lista<CasoLimite>:
    let casos = Lista<CasoLimite>()
    let ast = parsear(codigo)
    
    para nodo en ast:
        si nodo.tipo == NODO_FUNCION:
            para param en nodo.funcion.params:
                si param.tipo == "entero":
                    casos.agregar(CasoLimite("cero", "principal(0)", "0"))
                    casos.agregar(CasoLimite("negativo", "principal(-1)", "error"))
                    casos.agregar(CasoLimite("maximo", "principal(9223372036854775807)", "sin_crash"))
                    casos.agregar(CasoLimite("minimo", "principal(-9223372036854775808)", "sin_crash"))
                si param.tipo == "texto":
                    casos.agregar(CasoLimite("vacío", 'principal("")', "sin_crash"))
                    casos.agregar(CasoLimite("largo", 'principal("' + repetir("a", 10000) + '")', "sin_crash"))
                    casos.agregar(CasoLimite("unicode", 'principal("ñáéíóú")', "sin_crash"))
                si param.tipo == "decimal":
                    casos.agregar(CasoLimite("cero", "principal(0.0)", "0.0"))
                    casos.agregar(CasoLimite("nan", "principal(0.0/0.0)", "error"))
                    casos.agregar(CasoLimite("infinito", "principal(1.0/0.0)", "error"))
    
    retornar casos.limitar(5)  // Máximo 5 casos por verificación

// ============================================================
// VERIFICACIÓN COMPLETA
// ============================================================

funcion verificar_codigo_generado(codigo: texto, archivo_original: texto) -> Resultado<Verificacion, texto>:
    let resultados = Lista<ResultadoCaso>()
    
    // 1. Verificación sintáctica (ya existente)
    si no validar_con_compilador(codigo):
        retornar err("Error sintáctico")
    
    // 2. Verificación de contratos
    let contratos_ok = verificar_contratos(codigo)
    si no contratos_ok:
        retornar err("Contratos no se cumplen")
    
    // 3. Auto-refutación: generar y ejecutar casos límite
    let casos = generar_casos_limite(codigo)
    para caso in casos:
        let resultado = verificar_caso_limite(codigo, caso)
        resultados.agregar(resultado)
    
    // 4. Analizar resultados
    let fallos = resultados.filtrar(r -> r.estado != "completado")
    
    retornar ok(Verificacion(
        casos_ejecutados: resultados.len(),
        fallos: fallos.len(),
        resultados: resultados
    ))
```

### 6.4. Ejecución Asíncrona con Timeout

**Archivo:** `runtime/core/proceso.c`

```c
// runtime/core/proceso.c
// Ejecución asíncrona de subprocesos con timeout.

#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#include <signal.h>
#include <time.h>

typedef struct {
    pid_t pid;
    int stdin_fd;
    int stdout_fd;
    int stderr_fd;
    uint64_t timeout_ms;
} ProcesoAsync;

ProcesoAsync* proceso_ejecutar_async(const char* comando, uint64_t timeout_ms) {
    ProcesoAsync* p = malloc(sizeof(ProcesoAsync));
    p->timeout_ms = timeout_ms;
    
    int stdin_pipe[2], stdout_pipe[2], stderr_pipe[2];
    pipe(stdin_pipe);
    pipe(stdout_pipe);
    pipe(stderr_pipe);
    
    p->pid = fork();
    if (p->pid == 0) {
        // Hijo
        dup2(stdin_pipe[0], STDIN_FILENO);
        dup2(stdout_pipe[1], STDOUT_FILENO);
        dup2(stderr_pipe[1], STDERR_FILENO);
        close(stdin_pipe[1]);
        close(stdout_pipe[0]);
        close(stderr_pipe[0]);
        
        execl("/bin/sh", "sh", "-c", comando, NULL);
        _exit(127);
    }
    
    // Padre
    close(stdin_pipe[0]);
    close(stdout_pipe[1]);
    close(stderr_pipe[1]);
    
    p->stdin_fd = stdin_pipe[1];
    p->stdout_fd = stdout_pipe[0];
    p->stderr_fd = stderr_pipe[0];
    
    return p;
}

bool proceso_esperar(ProcesoAsync* p, int* codigo_salida) {
    struct timespec inicio;
    clock_gettime(CLOCK_MONOTONIC, &inicio);
    
    while (1) {
        int status;
        pid_t resultado = waitpid(p->pid, &status, WNOHANG);
        
        if (resultado == p->pid) {
            *codigo_salida = WEXITSTATUS(status);
            return true;
        }
        
        struct timespec ahora;
        clock_gettime(CLOCK_MONOTONIC, &ahora);
        uint64_t transcurrido_ms = 
            (ahora.tv_sec - inicio.tv_sec) * 1000 +
            (ahora.tv_nsec - inicio.tv_nsec) / 1000000;
        
        if (transcurrido_ms > p->timeout_ms) {
            proceso_matar(p);
            return false;  // timed out
        }
        
        usleep(10000);  // 10 ms
    }
}

void proceso_matar(ProcesoAsync* p) {
    kill(p->pid, SIGKILL);
    waitpid(p->pid, NULL, 0);
}
```

### 6.5. Coste y Mitigación

**Coste por caso límite:**
- Compilación: ~500 ms
- Ejecución: ~100 ms
- Total: ~600 ms por caso

**Mitigación:**
- Máximo 5 casos por verificación.
- Ejecución en paralelo (fibras del runtime).
- Caché de compilaciones: si el código base no cambió, reutilizar binario.

**Total añadido:** ~3 segundos, ejecutado en paralelo con el Reviewer.

### 6.6. Criterios de Aceptación

- Compilación de caso límite: < 1 s.
- Ejecución con timeout: funciona correctamente.
- Ejecución paralela de 5 casos: < 3 s.
- Detección de bucles infinitos: timeout de 5 s funciona.

---

## 7. MODOS DE OPERACIÓN DEL AGENTE

### 7.1. Los Cinco Modos

OpenSyn opera en cinco modos especializados, inspirados en Kilo y Claude Code, pero reescritos de forma determinista y local.

| Modo | Propósito | Herramientas permitidas | LLM |
|------|-----------|-------------------------|-----|
| **Ask** | Preguntas sobre el código | Lectura, búsqueda | Explicativo |
| **Plan** | Diseñar un cambio antes de ejecutarlo | Lectura + escritura de plan | Planificador |
| **Code** | Implementar un cambio | Edición + validación | Coder + Reviewer |
| **Debug** | Diagnosticar y corregir errores | Lectura + edición limitada | Diagnóstico + Coder |
| **Orchestrator** | Descomponer tareas complejas en subtareas | Coordinación (sin herramientas directas) | Descomponedor |

### 7.2. Implementación en `principal.syn`

```synapse
#lang: es
// opensyn/principal.syn - Tabla de modos

estructura Modo:
    nombre: texto
    descripcion: texto
    herramientas_permitidas: Lista<texto>
    fases_pipeline: Lista<texto>
    temperatura: decimal
    max_tokens: entero

var MODOS: Mapa<texto, Modo> = Mapa()

funcion inicializar_modos():
    MODOS["ask"] = Modo(
        nombre: "ask",
        descripcion: "Solo lectura. Preguntas sobre el código.",
        herramientas_permitidas: ["leer_archivo", "buscar", "git_status", "git_diff"],
        fases_pipeline: ["llm_explicativo"],
        temperatura: 0.2,
        max_tokens: 1024
    )
    MODOS["plan"] = Modo(
        nombre: "plan",
        descripcion: "Diseñar un cambio antes de ejecutarlo.",
        herramientas_permitidas: ["leer_archivo", "buscar", "escribir_plan"],
        fases_pipeline: ["explorer", "architect"],
        temperatura: 0.1,
        max_tokens: 2048
    )
    MODOS["code"] = Modo(
        nombre: "code",
        descripcion: "Implementar un cambio con validación.",
        herramientas_permitidas: ["leer_archivo", "buscar", "editar_archivo", "ejecutar_tests"],
        fases_pipeline: ["explorer", "architect", "coder", "reviewer", "fixer"],
        temperatura: 0.3,
        max_tokens: 2048
    )
    MODOS["debug"] = Modo(
        nombre: "debug",
        descripcion: "Diagnosticar y corregir errores.",
        herramientas_permitidas: ["leer_archivo", "buscar", "editar_archivo"],
        fases_pipeline: ["explorer", "coder", "reviewer"],
        temperatura: 0.2,
        max_tokens: 1536
    )
    MODOS["orchestrator"] = Modo(
        nombre: "orchestrator",
        descripcion: "Descomponer tareas complejas en subtareas.",
        herramientas_permitidas: [],
        fases_pipeline: ["descomponedor"],
        temperatura: 0.1,
        max_tokens: 1024
    )
```

### 7.3. Criterios de Aceptación

- Cambiar de modo con `/ask`, `/plan`, `/code`, `/debug`, `/orchestrator`.
- Cada modo solo permite las herramientas especificadas.
- El pipeline se ejecuta según las fases del modo.

---

## 8. REQUISITOS DE HARDWARE Y CONFIGURACIÓN

### 8.1. Hardware Mínimo

| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| CPU | 4 núcleos | 8 núcleos |
| RAM | 16 GB | 32 GB |
| VRAM | 4 GB | 8 GB |
| Disco | 20 GB libres | 50 GB libres |

### 8.2. Modelo Base

- **DeepSeek Coder 6.7B** (Q4_K_M, ~4 GB) para hardware medio.
- **CodeLlama 7B** (Q5_K_M, ~5 GB) para hardware con 8 GB VRAM.
- **CodeLlama 13B** (Q4_K_M, ~7 GB) para hardware de alta gama.

### 8.3. Archivo de Configuración

```toml
# ~/.opensyn/config.toml
[general]
idioma = "es"
editor = "vscode"
modo_default = "ask"

[modelo]
nombre = "codellama-7b-Q4_K_M"
ruta = "~/.opensyn/models/codellama-7b-Q4_K_M.gguf"
n_ctx = 4096
n_threads = 8
n_gpu_layers = 30

[server]
puerto = 8088
host = "127.0.0.1"
timeout = 30

[rag]
contexto_lineas = 5
max_prompt_tokens = 1200

[memoria]
cifrado = true
argon2_iteraciones = 3
argon2_memoria_mb = 64
argon2_paralelismo = 4

[verificacion]
max_casos_limite = 5
timeout_compilacion_seg = 30
timeout_ejecucion_seg = 5
ejecucion_paralela = true
```

---

## 9. PRUEBAS OBLIGATORIAS PARA LA FASE 32

| Test | Comando | Criterio |
|------|---------|----------|
| Grafo de conocimiento | `pytest tests/opensyn/test_grafo.py -v` | 100% pass, determinista |
| Construcción de grafo en 1000 archivos | `pytest tests/opensyn/test_grafo_perf.py -v` | < 100 ms |
| Memoria cifrada | `pytest tests/opensyn/test_memoria_cifrada.py -v` | 100% pass, `strings` no legible |
| Derivación de clave | `pytest tests/opensyn/test_key_derivation.py -v` | < 500 ms |
| Explorer determinista | `pytest tests/opensyn/test_explorer_det.py -v` | < 1 ms en 1000 archivos |
| Architect determinista | `pytest tests/opensyn/test_architect_det.py -v` | < 5 ms |
| Detección de ciclos | `pytest tests/opensyn/test_tarjan.py -v` | 0 falsos positivos |
| Pipeline multi-agente | `pytest tests/integration/test_pipeline_32.py -v` | 2-3 inferencias máximo |
| Verificación AOT | `pytest tests/opensyn/test_verificacion_aot.py -v` | < 3 s para 5 casos |
| Modos de operación | `pytest tests/opensyn/test_modos.py -v` | 100% pass |
| Ciclo completo end-to-end | `pytest tests/e2e/test_agente_completo.py -v` | < 30 s |

---

## 10. INTEGRACIÓN CON FASES ANTERIORES

### 10.1. Dependencias

| Componente | Fase requerida | Justificación |
|------------|----------------|---------------|
| AST canónico | Fase 22 | Base del grafo de conocimiento |
| Compilador funcional | Fase 5 | Necesario para validación AOT |
| LSP con `--check` | Fase 26.1 | Necesario para el bucle de validación |
| OpenSyn base | Fase 26 | Punto de partida del agente |
| Runtime de fibras | Fase 4 | Necesario para ejecución paralela |

### 10.2. Impacto en el Ecosistema

- **Synapse:** El grafo de conocimiento se construye desde el AST, aprovechando la arquitectura existente.
- **Syquex:** Se beneficia del grafo (análisis de impacto en código de alto nivel).
- **OpenSyn:** Se transforma de asistente a agente autónomo.
- **LSP:** Se extiende con comandos para los modos y la memoria.

---

## 11. CRONOGRAMA DETALLADO (8 MESES)

| Mes | Hito | Entregable | Criterio de Aceptación |
|-----|------|------------|------------------------|
| 1 | Grafo desde SemNodo[] | `nucleo/grafo_builder.syn` | Grafo determinista en 1000 archivos < 100 ms |
| 2 | Algoritmos de grafo | `opensyn/explorer_det.syn`, `opensyn/architect_det.syn` | BFS < 1 ms, DFS < 5 ms, Tarjan correcto |
| 3 | Memoria cifrada (XSalsa20) | `opensyn/memoria.syn` | `strings` no legible, clave nunca en disco |
| 4 | Derivación de clave (Argon2id) | `runtime/core/key_derivation.c` | < 500 ms, funciona en 3 SO |
| 5 | Verificación AOT | `runtime/core/proceso.c`, `opensyn/verificacion.syn` | Compilación < 1 s, ejecución con timeout |
| 6 | Integración RAG con memoria | Modificación de `synapse_rag.c` | Prompt incluye patrones y fallos |
| 7 | Pipeline multi-agente | `opensyn/orquestador_multi.syn` | 2-3 inferencias, < 30 s ciclo |
| 8 | Certificación y benchmark | Suite completa + benchmark vs OpenCode | Tasa éxito > 95%, latencia < 30 s |

### 11.1. Hitos Acumulativos

| Hito | Mes | Entregable |
|------|-----|------------|
| Hito 32.1 | 1 | Grafo de conocimiento funcional |
| Hito 32.2 | 2 | Explorer + Architect deterministas |
| Hito 32.3 | 3 | Memoria cifrada operativa |
| Hito 32.4 | 4 | Derivación de clave con Argon2id |
| Hito 32.5 | 5 | Verificación AOT con auto-refutación |
| Hito 32.6 | 6 | RAG con memoria persistente |
| Hito 32.7 | 7 | Pipeline multi-agente optimizado |
| Hito 32.8 | 8 | Certificación de la Fase 32 |

---

## 12. DIFERENCIADOR FINAL VS COMPETIDORES

| Capacidad | OpenCode | Kilo | Claude Code | Codex | Cursor | **OpenSyn Fase 32** |
|-----------|----------|------|-------------|-------|--------|---------------------|
| Análisis de impacto | Heurístico | Heurístico | Heurístico | Heurístico | Heurístico | **Determinista (AST)** |
| Memoria entre sesiones | ❌ | ⚠️ Limitada | ⚠️ Limitada | ❌ | ❌ | **✅ Cifrada 3 capas** |
| Memoria negativa | ❌ | ❌ | ❌ | ❌ | ❌ | **✅ Registro de fallos** |
| Auto-refutación | ❌ | ❌ | ❌ | ❌ | ❌ | **✅ Casos límite AOT** |
| Multi-agente | ❌ | ✅ (cloud) | ✅ (cloud) | ✅ (cloud) | ⚠️ | **✅ Determinista local** |
| Privacidad | ❌ Cloud | ❌ Cloud | ❌ Cloud | ❌ Cloud | ❌ Cloud | **✅ 100% local** |
| Latencia por ciclo | ~10 s | ~15 s | ~20 s | ~15 s | ~8 s | **~30 s (calidad > velocidad)** |
| Coste | Suscripción | Suscripción | Suscripción | Suscripción | Suscripción | **Gratis (open-source)** |

---

## 13. CONCLUSIÓN

La Fase 32 transforma a OpenSyn en un **agente de codificación de grado industrial** que:

1. **Entiende el sistema** mediante el grafo de conocimiento construido desde el AST.
2. **Aprende de cada interacción** mediante la memoria persistente cifrada.
3. **Analiza el impacto** de cada cambio de forma determinista, sin alucinaciones.
4. **Verifica su propio trabajo** generando y ejecutando casos límite.
5. **Respeta la privacidad** manteniendo todo local, sin telemetría.

El diferencial no es la velocidad de generación de código (commodity), sino la **capa de contexto y confianza** que ningún competidor puede replicar porque ninguno controla el AST del compilador.

**Regla de hierro:** Ninguna capacidad de la Fase 32 debe romper el bootstrap ni violar los principios de El Pacto (Manual 1).

---

*Este manual proporciona la especificación completa de la Fase 32. La implementación debe seguir estos lineamientos para transformar a OpenSyn en el agente de codificación definitivo.*

**Fin del Manual 32**