# Plan de Micro-Entregable r331_ci_verde

## Objetivo

Desbloquear la medición de la suite y el CI: `nucleo/lsp_v3.syn` no compilaba
(80 usos de `cmp_texto` sin definición), `nucleo/generator.syn` no era la
salida de sus submódulos y el nativo devolvía rc=10 donde el oráculo de
aridad exige 7. Sin estos tres fallos resueltos, `--medir --comparar` no
puede publicar una corrida limpia.

## Requisito 1 - comparación de texto pública y contratada

requisito: Manual 2 §5.1
texto: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
implementacion: `std/texto.syn` recupera la única definición pública de `cmp_texto(a, b)` con `requiere:`/`garantiza:`; `nucleo/lsp_v3.syn` deja de tener 80 símbolos indefinidos y vuelve a pasar `--check`.
oraculo: tests/auditoria/test_r331_lsp_compila.py

## Requisito 2 - trazabilidad del primer diagnóstico semántico

requisito: Manual 2 §8.1
texto: "**Pasada 3 (Cuerpos de Código y Verificación de Ownership):** Analiza sintácticamente los bloques internos de cada función, evaluando expresiones, asignaciones, llamadas y flujos de control. Además, verifica el ownership, el borrowing y los lifetimes, y ejecuta el motor ATP en modo `--safe`."
implementacion: `AnalizadorSemanticoEst.codigo_error` registra el primer código de error y el pipeline nativo mapea `ERR_SEM_ARGUMENTOS_INVALIDOS` (19) a rc=7, con el resto de errores semánticos en 10.
oraculo: tests/auditoria/test_oraculos_r27_ctor_aridad.py

## Requisito 3 - generador reconciliado

requisito: Manual 2 §8.2
texto: "Synapse utiliza un algoritmo de inferencia de tipos basado en **Hindley‑Milner** (algoritmo W)."
implementacion: `python nucleo/_rebuild_generator.py` regeneró `nucleo/generator.syn` desde sus submódulos; el combinado vuelve a ser reproducible y conserva la inferencia de tipos y la emisión C.
oraculo: tests/auditoria/test_r301_generator_reconciliacion.py
