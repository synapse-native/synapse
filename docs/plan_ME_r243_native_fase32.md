# Plan ME r243 — compilación nativa (S2) de Fase 32 y reporte de errores accionable

**Fase del roadmap:** Ola 3/4 — endurecimiento del compilador nativo.
**Micro-entregable:** `r243_native_fase32`.
**Alcance:** el binario nativo (`synapse check`) valida los module de producción de
Fase 32 con rc=0 y reporta la causa de cada fallo con línea/columna.

---

requisito: Manual 2 §1.1
texto: "Si el archivo omite esta directiva, el lexer rechazará el archivo con el error `ERR_LEX_MISSING_LANG`."
implementacion: `nucleo/lexer.syn` normaliza un BOM UTF-8 inicial antes de
  `lexer_detectar_idioma`, de modo que la directiva se evalúa sobre la línea 1
  real; `lexer_error` emite el diagnóstico con línea, columna y mensaje en vez
  de fallar en silencio. Los fuentes de Fase 32 abren con `#lang: es` en la
  línea 1 (verificado por bytes en el oráculo).
oraculo: tests/integration/test_compilacion_fase32_s2.py

requisito: Manual 2 §1.2
texto: "Todos los archivos fuente deben estar codificados en **UTF‑8 sin BOM**."
implementacion: se retiró el BOM UTF-8 de `opensyn/chat.syn`,
  `opensyn/verificacion_aot.syn` y `nucleo/grafo_conocimiento.syn`; el lexer
  nativo omite un BOM inicial para mantener paridad con S1, que también lo
  acepta.
oraculo: tests/integration/test_compilacion_fase32_s2.py

requisito: Manual 2 §4.2
texto: "tipo Resultado<T, E> = ok(T) | err(E)"
implementacion: `nucleo/analizador_semantico.syn` incluye `Resultado` y `Opcion`
  en la tabla `_prim` de tipos base conocidos, por ser tipos del prelude
  declarados en §4.2; sin ello, `Resultado<texto, texto>` (usado por
  `opensyn/installer.syn`) se reportaba como tipo no definido.
oraculo: tests/integration/test_compilacion_fase32_s2.py

requisito: Manual 8 §4.2
texto: "| **`--check`** / **`--no-emit`** | **Modo de validación:** Solo verifica la sintaxis y semántica, sin generar código de salida. Útil para el bucle de corrección de OpenSyn. |"
implementacion: `nucleo/principal.syn` agrega `fallo_etapa(cod)` que traduce el
  código de etapa (memoria, apertura, lexer, codegen, GCC, tamaño, módulo no
  encontrado, sintaxis, verificación formal, semántico) a una causa legible;
  `cli_check` imprime `[Check] ERROR de validacion` y delega el detalle a
  `fallo_etapa`, con rc=1.
oraculo: tests/integration/test_compilacion_fase32_s2.py

requisito: Manual 2 §10.2
texto: "Cada error incluye: código de error, ubicación exacta (archivo, línea, columna), mensaje explicativo y, cuando sea posible, sugerencias de corrección."
implementacion: `lexer_error` imprime `[Synapse] Error lexico (linea L, columna C): <mensaje>`
  en vez de fallar en silencio; `fallo_etapa` en `nucleo/principal.syn` agrega la
  causa de la etapa que fallo para que el bucle de corrección reciba la razón y
  no solo un código de salida.
oraculo: tests/integration/test_compilacion_fase32_s2.py

requisito: Manual 9 §6.2
texto: "La suite de tests completa en cada target."
implementacion: `nucleo/principal.syn` resuelve los `importar` relativos contra
  el directorio del módulo importador (pila `_dirstk`, paridad con S1), lo que
  permite compilar `opensyn/herramientas.syn` (`importar permisos`) y la cadena
  `nucleo/grafo_conocimiento.syn` → `parser_constantes`; los 14 módulos
  `opensyn/*.syn` y `nucleo/grafo_conocimiento.syn` compilan con S2 (rc=0).
oraculo: tests/integration/test_compilacion_fase32_s2.py

---

## Verificación

- `pytest tests/integration/test_compilacion_fase32_s2.py` — 8 tests (sin SKIP).
- `pytest tests/integration/test_compilacion_fase32.py` — gate S1 (sin regresión).
- `python auditoria/contrastar.py --plan docs/plan_ME_r243_native_fase32.md`
- `python auditoria/alineacion.py --verificar --me r243_native_fase32`
- `python auditoria/verificar_alineacion.py` — 0 brechas.
