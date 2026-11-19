# Plan ME r205 — Grafo de conocimiento real (Fase 32.1)

## Contexto

`nucleo/grafo_conocimiento.syn` no compila (135 errores) y su contenido es un
esqueleto con placeholders: `SemNodo[]`, constructores con argumentos
nombrados, `.len()`, mutación de campos vía índice de lista, `NODO_IMPORT` /
`NODO_TIPO` inexistentes, hash no criptográfico y persistencia noop. El ME
reemplaza el esqueleto por una implementación ejecutable y verificable, sin
cambiar el ABI congelado (`nucleo/ast_abi.syn`) ni el `SemNodo` interno de
`nucleo/analizador_semantico.syn`.

## Requisitos (MTS)

requisito: Manual 32 §2.1
texto: "Construir un grafo dirigido de dependencias, contratos y relaciones entre todos los nodos del proyecto, **directamente desde el AST canónico (`SemNodo[]`) durante el pipeline del compilador**, sin análisis heurístico ni embeddings."
implementacion: `construir_grafo_desde_semnodo` recibe `Lista<NodoSemantico>` (modelo rico) y `total`, y construye nodos, aristas, dependientes, riesgo, ciclos y métricas en 6 pasadas deterministas. El adaptador `nodo_semantico_desde_abi` convierte el `RegistroAST` plano (ABI v1) al modelo rico sin duplicar el `SemNodo` del analizador semántico.
oraculo: tests/opensyn/test_grafo_comportamiento.py

requisito: Manual 32 §2.4
texto: "Estructura del Grafo" — `NodoGrafo`, `ContratoInfo`, `AristaGrafo`, `GrafoProyecto`, `MetricasGrafo` y la función `construir_grafo_desde_semnodo` con las pasadas 1 a 6.
implementacion: se declaran las cinco estructuras con todos sus campos y la función pública con las seis pasadas comentadas `PASADA 1`…`PASADA 6`. La pasada 1 crea nodos de función/estructura; la 2 crea aristas de llamada/importación/uso de tipo; la 3 calcula dependientes y dependencias; la 4 calcula riesgo; la 5 ejecuta Tarjan; la 6 calcula métricas. Las listas se reconstruyen en lugar de mutar campos por índice.
oraculo: tests/opensyn/test_grafo_comportamiento.py

requisito: Manual 32 §2.5
texto: "El grafo se guarda en `~/.synapse/cache/grafo/<hash_ast>.json.gz`. Si el AST no cambia (mismo hash), el grafo se reutiliza."
implementacion: `grafo_guardar` serializa el grafo completo a JSON determinista y lo escribe con `std.sistema.escribir_archivo`; `grafo_cargar` lo lee, parsea con `std.json` y reconstruye nodos/aristas/índice/métricas. La ruta es un parámetro del contrato. No se usa gzip porque la stdlib S1 no expone compresión; se registra como DESVIACIÓN documentada y se conserva el nombre de archivo `.json` (el llamador puede añadir `.gz` cuando exista la primitiva). `grafo_guardar` devuelve `ResultadoGuardado` (ok/error) y `grafo_cargar` devuelve `Lista<GrafoProyecto>` (vacía si falla) porque `Resultado<T,E>` de S1 no soporta payload struct ni `es_ok`/`desempaquetar`.
oraculo: tests/opensyn/test_grafo_comportamiento.py

requisito: Manual 32 §2.6
texto: "Grafo es determinista: mismo AST → mismo hash SHA-256."
implementacion: `calcular_hash_ast` serializa los `NodoSemantico` en JSON canónico y llama a `std.cripto.sha256_texto`; no usa el hash entero anterior. El test construye el mismo grafo dos veces y exige `hash_ast` idéntico, 2 nodos, 2 aristas y 1 ciclo.
oraculo: tests/opensyn/test_grafo_comportamiento.py

requisito: Manual 6 §1.1
texto: "El ecosistema Synapse se basa en un **Árbol de Sintaxis Abstracta (AST) canónico y unificado** denominado `SemNodo[]`."
implementacion: el grafo consume el AST canónico mediante `NodoSemantico` y `RegistroAST`; el adaptador conserva los 10 campos del ABI v1 y añade el contexto de nombre/archivo/firma/contratos/exportación. No se crea un segundo `SemNodo` ni se modifica `nucleo/ast_abi.syn`.
oraculo: tests/opensyn/test_grafo_comportamiento.py

requisito: Manual 2 §5.1
texto: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
implementacion: toda función pública nueva lleva bloque `requiere`/`garantiza`; los contratos del grafo se extraen del `NodoSemantico` y se serializan en `ContratoInfo`. Las funciones internas también declaran contratos cuando reciben índices, mapas o listas.
oraculo: tests/opensyn/test_grafo_comportamiento.py

requisito: Manual 2 §7.3
texto: "Para el análisis semántico, la linked-list se aplana a un array contiguo. Este es el **AST canónico unificado** que comparten Synapse y Syquex."
implementacion: `RegistroAST` replica los 10 campos planos del ABI y `nodo_semantico_desde_abi` los adapta al modelo rico. El builder no muta el registro ABI; reconstruye listas y mapas con las operaciones canónicas `Lista<T>`/`Mapa<K,V>`.
oraculo: tests/opensyn/test_grafo_comportamiento.py

## Archivos

- `nucleo/grafo_conocimiento.syn` — reescritura completa.
- `tests/opensyn/test_grafo_comportamiento.py` — oráculo de comportamiento (nuevo).
- `tests/fixtures/compilacion_baseline.txt` — retirar `nucleo/grafo_conocimiento.syn` al compilar.
- `docs/gobernancia/mapa_manuales.md` — entrada específica del grafo (Manual 6 §1.1 + Manual 2 §5.1).
- `docs/verificacion_ME_r205_grafo_conocimiento.md` — expediente de verificación (generado después).

## Desviaciones declaradas

- `SemNodo[]` / constructores con nombres / `.len()` / `NODO_IMPORT` / `NODO_TIPO` del pseudocódigo del Manual 32 no son sintaxis S1 válida. Se usan `Lista<NodoSemantico>`, constructores posicionales, `longitud()`, `NODO_IMPORTAR` y el alias `NODO_TIPO_USO = NODO_DECLARACION_TIPO`.
- gzip no existe en la stdlib S1; persistencia JSON de texto.
- La ruta `~/.synapse/cache/grafo/` la resuelve el llamador; el módulo recibe `ruta` como parámetro.
- S1 indexa `Lista<T>` como `int`; los structs de lista se recorren con `para x en lista`, no con `lista[i]`. `Nodo` es un tipo reservado del AST; se usan `NodoGrafo`/`NodoSemantico`.
- S1 emite un campo struct anidado como puntero a un local (puntero colgante al retornar). `GrafoProyecto.metricas` se representa como `Lista<MetricasGrafo>` de un elemento; se conserva el struct `MetricasGrafo` y el acceso tipado con `para m en grafo.metricas`.
- `Resultado<T,E>` de S1 solo transporta escalares/texto y no expone `es_ok`/`desempaquetar`; por eso `grafo_guardar` usa `ResultadoGuardado` y `grafo_cargar` devuelve `Lista<GrafoProyecto>` (vacía en error).

## Oráculos de cierre

1. `.venv\Scripts\python.exe main.py nucleo/grafo_conocimiento.syn --check --no-emit` → rc 0.
2. `.venv\Scripts\python.exe -m pytest tests/opensyn/test_grafo.py tests/opensyn/test_grafo_comportamiento.py -v` → verde.
3. `.venv\Scripts\python.exe -m pytest tests/integration/test_compilacion_fase32.py -v` → verde sin el grafo en el baseline.
4. `python auditoria/alineacion.py --verificar --me r205_grafo_conocimiento` → sin brechas.
5. `python auditoria/contrastar.py --plan docs/plan_ME_r205_grafo_conocimiento.md` → sin brechas.
