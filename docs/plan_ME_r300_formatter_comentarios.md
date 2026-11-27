# Plan de Micro-Entregable r300_formatter_comentarios

## Objetivo

Cerrar **H-R299-1**: `test_nucleo_formateado` fallaba porque el formateador
colapsaba los espacios dentro de los comentarios (`//    1. paso`,
`x = 0     // nota`), que el propio código documenta como alineación
deliberada. Se alinea el formateador con esa intención y se normalizan los tres
módulos que quedaron marcados (`generator.syn`, `lint.syn`, `lsp_v3.syn`).

Regla implementada en `normalizar_espacios`:
- `//` fuera de literal inicia comentario: desde el hueco de espacios que lo
  precede hasta el fin de línea se copia **verbatim** (no se re-formatea el
  texto del autor).
- El resto de la línea conserva las reglas de estilo (colapso de espacios fuera
  de literales y comentarios, un espacio tras coma, indentación de 4).

## Requisito 1 — `synapse fmt` respeta el contenido del autor

requisito: Manual 8 §4.1
texto: "| **`synapse fmt`** (Fase 31) | Ejecuta el formateador nativo sobre el código fuente. |"
implementacion: `nucleo/formatter.syn` agrega la rama `c == "/"` con lookahead `//` y el caso de hueco de espacios previo a comentario en `normalizar_espacios`; el comentario y su sangría de alineación se anexan tal cual al builder. `generator.syn` y `lsp_v3.syn` se normalizan con el formateador resultante.
oraculo: tests/auditoria/test_r300_formatter_comentarios.py

## Requisito 2 — el LSP sigue siendo el módulo nativo documentado

requisito: Manual 8 §1.1
texto: "El LSP es **nativo**, **sin telemetría** y **sin dependencias externas** (excepto el binario `synapse.exe` para compilar y analizar código)."
implementacion: en `nucleo/lsp_v3.syn` el formateo solo elimina líneas en blanco duplicadas y conserva las cabeceras `// cumple Manual 8 §1.x`; no cambia ninguna función ni mensaje JSON-RPC.
oraculo: tests/auditoria/test_r300_formatter_comentarios.py

## Requisito 3 — la emisión de código del generador no cambia

requisito: Manual 2 §8.2
texto: "Synapse utiliza un algoritmo de inferencia de tipos basado en **Hindley‑Milner** (algoritmo W)."
implementacion: en `nucleo/generator.syn` el reformato solo colapsa espacios dobles en dos condiciones `y` (`_G_emit_pos >= 0  y  ...`); la lógica de emisión y sus tipos quedan idénticos, verificado por el bootstrap determinista y la suite del formateador.
oraculo: tests/auditoria/test_r300_formatter_comentarios.py

## Evidencia

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r300_formatter_comentarios.py` | 4 passed |
| `pytest tests/auditoria/test_oraculos_formatter_fix.py tests/nucleo/test_fmt.py tests/auditoria/test_oraculos_cli_lint_fmt.py` | 25 passed |
| `synapse fmt --check` sobre `nucleo/*.syn` y `nucleo/generador/*.syn` | 0 mal formateados |
| `build.py --skip-test` | rc=0, S2==S3 `cc970f0b02bf` |
| `verificar_alineacion.py` / `verificar_encoding.py --estricto` | 0 brechas / OK (2379 archivos) |

## Hallazgos

- **H-R299-1**: **RESUELTO** — comentarios verbatim + 3 módulos normalizados.
- `nucleo/generator.syn` es auto-generado por `nucleo/_rebuild_generator.py`,
  pero el archivo versionado contiene correcciones manuales (contratos de
  `cdd409f`) que el rebuild descarta: regenerarlo en este ME cambiaría
  semántica (p. ej. `requiere: tipo_synapse != nulo`), así que se reformatea el
  archivo versionado y se deja constancia; la deriva generator↔submódulos queda
  registrada como H-R300-1 para un ME que reconcilie ambos (decisión de
  Arquitecto).
