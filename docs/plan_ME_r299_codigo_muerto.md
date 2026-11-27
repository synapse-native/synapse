# Plan de Micro-Entregable r299_codigo_muerto

## Objetivo

Cerrar **H-R285-2**: implementar el barrido de código muerto en las fuentes
`.syn` que se enlazan en el binario, resolver lo encontrado y dejarlo bajo gate.
Hasta hoy el verificador medía tamaño de módulo (D-9) y contratos, pero no
detectaba funciones sin ninguna llamada.

Alcance del barrido: módulos **alcanzables** desde `nucleo/principal.syn`
(clausura de `importar` + `_files[]` del build). Los módulos que ningún import ni
`_files[]` referencia (`nucleo/llvm_backend.syn`, `nucleo/wasm_backend.syn`,
`nucleo/lsp_v3.syn`, `nucleo/puente_ffi_lista_mapa.syn`) no se enlazan en el
producto: son corpus de tests, no código muerto del binario, y quedan fuera del
alcance por diseño (documentado en el propio auditor).

## Requisito 1 — Definition of Done sin código muerto

requisito: Manual 1 §7.4
texto: "- Aprobación del 100% de los tests unitarios, de integración y fuzzing sin regresiones."
implementacion: nuevo `auditoria/verificar_codigo_muerto.py` (alcance por alcanzabilidad, exentos `@export` y puntos de entrada, baseline ratchet). Sobre el alcance real había 4 funciones sin referencias en `nucleo/cache.syn` y `nucleo/formatter.syn`; al podarlas quedaron huérfanas 2 auxiliares privadas de caché: se eliminan las 6. Resultado: 346 funciones definidas en 32 módulos, 0 muertas.
oraculo: tests/auditoria/test_codigo_muerto.py

## Requisito 2 — los contratos no cambian con la poda

requisito: Manual 2 §5.1
texto: "**`garantiza`:** Se evalúa inmediatamente antes de cada `retornar`. La variable `_resultado_` contiene el valor que se va a retornar."
implementacion: la poda solo quita funciones inalcanzables; `calcular_clave`, `cache_buscar`, `cache_guardar`, `cache_stats` y el resto de la superficie pública conservan sus bloques `requiere`/`garantiza` intactos, y el `fmt` del CLI sigue usando `formatear_texto`/`fmt_archivo`.
oraculo: tests/auditoria/test_codigo_muerto.py

## Evidencia

| check | resultado |
|---|---|
| `python auditoria/verificar_codigo_muerto.py --estricto` | 0 muertas (346 funciones, 32 módulos) |
| `pytest tests/auditoria/test_codigo_muerto.py` | 4 passed |
| `pytest tests/integration/test_backend_10.py` | 22 passed |
| `pytest tests/nucleo/test_fmt.py tests/auditoria/test_oraculos_formatter_fix.py tests/nucleo/test_modulos_compilan.py` | 23 passed, 1 failed preexistente (`test_nucleo_formateado`, H-R299-1) |
| `python build.py --skip-test` | OK, bootstrap determinista S2==S3 `f3ad54ee8861` |
| `auditoria/verificar_alineacion.py` | 0 brechas |
| `auditoria/verificar_encoding.py --estricto` | OK (2373 archivos) |
| Gate pre-commit de código muerto | añadido (bloquea muertas NUEVAS) |

## Hallazgos

- **H-R285-2**: **RESUELTO** — barrido implementado, 6 funciones podadas, gate
  en pre-commit y oráculo de 4 tests.
- Los `nucleo/_tmp_*` que aparecían en el primer barrido no están versionados
  (`git ls-files "nucleo/_tmp*"` vacío): eran archivos de trabajo locales, se
  excluyen escaneando solo lo versionado.
- **H-R299-1** (nuevo, preexistente): `tests/auditoria/test_oraculos_formatter_fix.py::test_nucleo_formateado`
  falla sobre `nucleo/generator.syn`, `nucleo/lint.syn` y `nucleo/lsp_v3.syn`
  con el binario actual. No es regresión de este ME: el contenido de HEAD de
  esos 3 archivos también falla `synapse fmt --check`. Resolución asignada:
  ME `r300_formatter_comentarios` (decidir si la alineación deliberada dentro
  de comentarios se preserva o el formateador la colapsa, y normalizar los 3
  módulos según el manual de estilo).
