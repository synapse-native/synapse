# Verificación ME — OpenSyn con lo mejor de opencode + Kilo + freebuff

## ME-1: Modos del agente (R1, Manual 7 §1.1)

| Requisito | Estado | Archivo:Línea |
|-----------|--------|---------------|
| Manual 7 §1.1 — modos ASK/PLAN/CODE/DEBUG/ORCHESTRATOR | **CUMPLE** | `opensyn/principal.syn:631-636` |
| Manual 7 §1.1 — tabla de permisos por modo | **CUMPLE** | `opensyn/principal.syn:640-660` |
| Manual 7 §1.1 — verificación de permisos antes de ejecutar tool | **CUMPLE** | `opensyn/principal.syn:663-701` |
| Manual 7 §1.1 — comandos /ask /plan /code /debug /orchestrator | **CUMPLE** | `opensyn/principal.syn:1064-1088` |
| Manual 7 §1.1 — skills respetan modo actual | **CUMPLE** | `opensyn/principal.syn:1004-1018` |
| Manual 7 §1.1 — oráculo E2E valida modos | **CUMPLE** | `tests/e2e_oracle_opensyn_banner.py:68-73` |
| MTO §3 — test TDD para funciones de modos | **CUMPLE** | `tests/unit/test_modos_opensyn.py` (57 tests) |

### Bugs corregidos en esta sesión
1. **herramienta_permitida() orchestrator**: retornaba 0 sin verificar la lista de permitidas. Fix: usar `split(",")` y verificar pertenencia.
2. **tui_comando() recursión**: llamada recursiva sin parámetro `modo`. Fix: agregar `modo` al call site.
3. **Skills sin permisos**: `/tdd` y `/plan` se ejecutaban sin verificar el modo. Fix: verificar `herramienta_permitida()` antes de ejecutar.

### Tests TDD creados
- `tests/unit/test_modos_opensyn.py` — 57 tests:
  - `TestHerramientasPermitidas` (6 tests): valida lista por cada modo
  - `TestHerramientaPermitida` (22 tests): valida permisos por herramienta/modo
  - `TestNombreModo` (6 tests): valida nombre legible
  - `TestPctContexto` (5 tests): valida cálculo de % context
  - `TestIntegracionModos` (3 tests): flujos de cambio de modo

### Archivos modificados (ME-1)
- `opensyn/principal.syn` — bug fixes + skills con permisos
- `tests/e2e_oracle_opensyn_banner.py` — chequeo 4 de modos
- `tests/unit/test_modos_opensyn.py` — NUEVO (57 tests TDD)

---

## ME-2: File-finder + catálogo APIs locales (R2, Manual 7 §2.3)

| Requisito | Estado | Archivo:Línea |
|-----------|--------|---------------|
| Manual 7 §2.3 — catálogo de APIs std impide alucinaciones | **CUMPLE** | `opensyn/router.syn:obtener_catalogo_api()` |
| Manual 7 §2.3 — file-finder localiza archivos ANTES de generar código | **CUMPLE** | `opensyn/router.syn:file_finder()` |
| Manual 7 §2.3 — mapa keyword→archivo para búsqueda semántica | **CUMPLE** | `opensyn/router.syn:obtener_mapa_keywords()` |
| Manual 7 §2.3 — catálogo inyectado en cada prompt vía construir_prompt | **CUMPLE** | `opensyn/router.syn:construir_prompt()` |
| Manual 7 §2.3 — file-finder muestra archivos relevantes en prompt | **CUMPLE** | `opensyn/router.syn:construir_prompt()` |
| MTO §3 — test TDD para catálogo, mapa y file-finder | **CUMPLE** | `tests/unit/test_rag_file_finder.py` (21 tests) |

### Funciones implementadas
1. **obtener_catalogo_api()**: Retorna string con APIs públicas de cada `std/*.syn` (generado del repo, no del modelo).
2. **obtener_mapa_keywords()**: Retorna string `keyword:archivo;...` para búsqueda semántica.
3. **file_finder(consulta)**: Localiza archivos relevantes por keywords en la consulta.
4. **construir_prompt()**: Ahora inyecta catálogo API y archivos relevantes en cada prompt.

### Tests TDD creados
- `tests/unit/test_rag_file_finder.py` — 21 tests:
  - `TestCatalogoAPI` (7 tests): valida contenido y precisión del catálogo
  - `TestFileFinder` (11 tests): validan localización por keyword
  - `TestIntegracionFileFinderCatalogo` (3 tests): validan complementariedad

### Archivos modificados (ME-2)
- `opensyn/router.syn` — 3 funciones nuevas + integración en construir_prompt
- `tests/unit/test_rag_file_finder.py` — NUEVO (21 tests TDD)

---

## Requisitos pendientes (no implementados en ME-1/ME-2)

| Requisito | Estado | Notas |
|-----------|--------|-------|
| Manual 7 §2.4 — router-orquestador que delega + 3 siguientes pasos (R3) | **NO CUMPLE** | ME-3 pendiente |
| Manual 7 §6.3 — auto-recuperación: detectar error + tests + reintentar (R4) | **NO CUMPLE** | ME-4 pendiente |
| Manual 7 §4.2 — corrección IA con contexto (R5) | **NO CUMPLE** | ME-5 pendiente |
| Manual 7 §6.4 — historial de intentos persistentes (R6) | **NO CUMPLE** | ME-6 pendiente |
| Manual 7 §4.3 — integración LLM local GGUF (R7) | **NO CUMPLE** | ME-7 pendiente |
| Manual 7 §7.2 — RAG pipeline avanzado (R8) | **NO CUMPLE** | ME-8 pendiente |
| Manual 7 §8 — scoreboard/métricas (R9) | **NO CUMPLE** | ME-9 pendiente |
| Manual 7 §7.3 — contexto dinámico (R10) | **NO CUMPLE** | ME-10 pendiente |
