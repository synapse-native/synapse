# Plan Maestro de Quema de Deuda de Contratos (H-R277-1) — r286 a r290

**Fecha de formulación:** 2026-11-21  
**Referencia:** Mandato de Deuda Cero, Manual 2 §5.1 y Manual 2 §12  
**Estado de partida:** 590 funciones públicas sin contratos en 68 archivos `.syn` (medición oficial `auditoria/verificar_contratos.py`).  
**Objetivo final:** Cierre total de `H-R277-1` con `python auditoria/verificar_contratos.py --estricto` retornando rc=0 y baseline limpio.

---

## 1. Principios de Ejecución y Reglas de Calidad

1. **Invariantes semánticos reales (Prohibición de contratos placebo):**  
   Queda estrictamente prohibido colocar `requiere: verdadero` o `garantiza: verdadero`. Los contratos deben expresar invariantes del dominio: punteros y estructuras no nulas, rangos válidos, cadenas de longitud válida, o poscondiciones que verifiquen el estado retornado (`_resultado_`).
2. **Saneamiento de visibilidad (Privatización de helpers internos):**  
   Toda función de soporte que solo se invoque dentro del propio módulo debe renombrarse con prefijo `_` (ej. `_calcular_offset`), quedando clasificada como privada e interna según la regla 12 del repositorio. Esto reduce la deuda técnica de forma limpia y reduce la superficie de API pública.
3. **Ratchet estricto por entrega:**  
   Al concluir cada micro-entregable se regenera el archivo de control con:
   ```bash
   .venv\Scripts\python.exe auditoria/verificar_contratos.py --baseline
   ```
   El gate en CI prohíbe mecánicamente que la deuda vuelva a subir.
4. **Protección del Bootstrap ($S2 == S3$):**  
   Cualquier intervención en `nucleo/` debe validarse ejecutando `build.py` y verificando que el oráculo `auditoria/oraculos/oraculo_r252_paridad_bootstrap.py --construir --estricto` mantenga la paridad binaria exacta.

---

## 2. Desglose en 5 Bloques Ejecutables

### Bloque 1: `r286_contratos_std_util` — Utilidades de Biblioteca Estándar y OpenSyn
* **Prioridad:** P1 (Bajo riesgo en bootstrap)
* **Alcance:** ~85 funciones en 20 archivos.
* **Archivos objetivo:**
  - `std/math.syn` (4), `std/json.syn` (4), `std/io.syn` (5), `std/cripto.syn` (2), `std/mem.syn` (2)
  - `std/tiempo.syn` (2), `std/toml.syn` (2), `std/debug.syn` (4), `std/sistema.syn` (6), `std/testing.syn` (5)
  - `std/texto.syn` (7), `std/oraculo.syn` (6), `std/cluster.syn` (4)
  - `opensyn/principal.syn` (12), `opensyn/installer.syn` (5), `opensyn/memoria_persistente_cifrada.syn` (3), `opensyn/architect_det.syn` (1)
* **Oráculos y Verificación:**
  - `pytest tests/unit/test_string_utils.py`
  - `pytest tests/opensyn/`
  - `auditoria/verificar_contratos.py` (deuda debe bajar de 590 a ~505)

### Bloque 2: `r287_contratos_std_avanzado` — Módulos Científicos, Simbólicos y Distribuidos
* **Prioridad:** P1 (Riesgo medio)
* **Alcance:** ~145 funciones en 14 archivos.
* **Archivos objetivo:**
  - `std/modelo.syn` (21), `std/atp_engine.syn` (17), `std/symbolic_exec.syn` (15)
  - `std/dist_orchestrator.syn` (13), `std/proof_bridge.syn` (12)
  - `std/quantum.syn` (10), `std/quantum_err_corr.syn` (6), `std/surface_code.syn` (7), `std/quantum_memory.syn` (3)
  - `std/federated.syn` (9), `std/tensor.syn` (9), `std/ai.syn` (8), `std/net.syn` (8), `std/simd.syn` (8)
* **Oráculos y Verificación:**
  - Suites unitarias y avanzadas de `tests/unit/`
  - `auditoria/verificar_contratos.py` (deuda debe bajar a ~360)

### Bloque 3: `r288_contratos_syquex` — Frontend y Concurrencia de Syquex
* **Prioridad:** P1 (Riesgo medio)
* **Alcance:** 84 funciones en 4 archivos.
* **Archivos objetivo:**
  - `syquex/parser.syn` (24)
  - `syquex/lexer.syn` (23)
  - `syquex/expr.syn` (19)
  - `syquex/traductor.syn` (18)
* **Oráculos y Verificación:**
  - `pytest tests/syquex/` (281 tests sin regresiones ni caídas de cobertura)
  - `auditoria/verificar_contratos.py` (deuda debe bajar a ~276)

### Bloque 4: `r289_contratos_nucleo_front` — Compilador: Lexer, Parsers y Análisis Semántico
* **Prioridad:** P0 (Alto riesgo / Afecta compilador autohospedado)
* **Alcance:** ~140 funciones en 13 archivos.
* **Archivos objetivo:**
  - `nucleo/analizador_semantico.syn` (34), `nucleo/lexer.syn` (26), `nucleo/lexer_keywords.syn` (4)
  - `nucleo/parser_base.syn` (20), `nucleo/parser.syn` (11), `nucleo/parser_sentencias.syn` (10)
  - `nucleo/parser_expr.syn` (7), `nucleo/parser_declaraciones.syn` (6), `nucleo/parser_stmt.syn` (5), `nucleo/parser_canales.syn` (3)
  - `nucleo/lifetimes.syn` (13), `nucleo/diagnostics.syn` (10), `nucleo/puente_ast.syn` (9)
* **Estrategia clave:** Privatizar rutinas auxiliares mediante prefijo `_`; contratos estrictos en funciones públicas de AST y contexto semántico.
* **Oráculos y Verificación:**
  - `pytest tests/unit/`
  - `python build.py`
  - `auditoria/verificar_contratos.py` (deuda debe bajar a ~136)

### Bloque 5: `r290_contratos_nucleo_codegen` — Compilador: Generador C y Cierre Deuda Cero
* **Prioridad:** P0 (Crítico / Sellado final)
* **Alcance:** ~136 funciones en 17 archivos.
* **Archivos objetivo:**
  - `nucleo/generator.syn` (36), `nucleo/generator_pgo.syn` (14)
  - `nucleo/generador/nodos_flujo.syn` (14), `nucleo/generador/emision_c.syn` (12), `nucleo/generador/escaneo.syn` (4), `nucleo/generador/orquestador.syn` (2)
  - `nucleo/generador/compilar.syn` (1), `nucleo/generador/frontend_nativo.syn` (1), `nucleo/generador/funciones.syn` (1), `nucleo/generador/monomorfizacion.syn` (1), `nucleo/generador/recorrido.syn` (1)
  - `nucleo/cache.syn` (8), `nucleo/optimizador_ia.syn` (10), `nucleo/principal.syn` (5)
  - `nucleo/coverage.syn` (2), `nucleo/resolvedor_axon.syn` (2), `nucleo/lsp.syn` (1), `nucleo/lsp_v3.syn` (1)
* **Oráculos y Verificación de Cierre:**
  - `python build.py` (Etapas 0, 1, 2, 3)
  - `python auditoria/oraculos/oraculo_r252_paridad_bootstrap.py --construir --estricto` (S2 == S3 hash idéntico)
  - `python auditoria/verificar_contratos.py --estricto` (código de salida 0 con baseline vacío)

---

## 3. Protocolo de Trabajo por Cada Bloque (MTS)

1. Crear `docs/plan_ME_<id>.md` citando Manual 2 §5.1 y §12.
2. Registrar lectura dirigida del día:
   ```bash
   python auditoria/alineacion.py --leer --me <id>
   ```
3. Editar código agregando `requiere:` y `garantiza:` semánticos y el comentario `// cumple Manual 2 §5.1`.
4. Ejecutar tests correspondientes y actualizar el baseline:
   ```bash
   python auditoria/verificar_contratos.py --baseline
   ```
5. Verificar gates:
   ```bash
   python auditoria/contrastar.py --plan docs/plan_ME_<id>.md
   python auditoria/alineacion.py --verificar --me <id>
   python auditoria/verificar_alineacion.py
   ```
6. Commitear y registrar reporte `docs/reportes/<ID>.md` y actualización en `MEMORIA_PROYECTO.md`.
