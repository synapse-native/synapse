# Plan ME r218_bootstrap_json - Bootstrap nativo S2 con std.json

FASE: POST-FASE 33 - DEUDA CERO
ID: r218_bootstrap_json
ESTADO: implementacion
ORIGEN: bootstrap S2 roto (`struct NodoJson` incompleto + inferencia `int64_t` en `actualizador.syn`) que bloquea los oraculos de auditoria.

## 1. Resumen del micro-entregable

### Requisito R1 - Bootstrap de 3 etapas sin brechas (diff 0 bytes)

requisito: Manual 9 §6.2
texto: "El pipeline de CI/CD ejecuta automáticamente: - La suite de tests completa en cada target. - La verificación del bootstrap (diff 0 bytes)."
implementacion:
  - `nucleo/principal.syn`: agregar `std/json.syn` y `std/texto.syn` a `_files[]` antes de `nucleo/actualizador.syn`, para que el unity build nativo parsee y registre `ParJson`/`NodoJson` y `termina_con`/`indice_de`.
  - El generador nativo ya emite campos de struct como punteros; `NodoJson`/`ParJson` deben coincidir con `synapse_rt_types.h` (recursion por puntero).
  - No se toca `std/json.syn`, `std/texto.syn` ni `runtime/core/json.c`: la firma by-value de los externos se conserva.
  - Buffer de emision C de 4 MB (`1048576` -> `4194304`) en `nucleo/generador/emision_c.syn`, `nucleo/generador/orquestador.syn`, `nucleo/generador/nodos_flujo.syn` y `compilador/generator/generator.py`: el C del compilador supera 1 MB (1.072.939 bytes con CRLF) y `gen_emitir_linea` truncaba lineas en silencio, borrando `int main` y dejando `return _rc;` fuera de funcion.
  - `nucleo/generator.syn` se regenera desde `nucleo/generador/*.syn` con `python nucleo/_rebuild_generator.py`; los arreglos se hacen en los submodulos, no en el archivo generado.
oraculo: tests/auditoria/test_oraculos_formatter_fix.py

### Requisito R2 - Inferencia de tipos Hindley-Milner en el generador nativo

requisito: Manual 2 §8.2
texto: "Synapse utiliza un algoritmo de inferencia de tipos basado en Hindley-Milner (algoritmo W). Las variables de tipo se representan como TVar(id). La unificación incluye occurs check para evitar tipos recursivos. Si una expresión tiene tipo ambiguo (ej. []), se emite ERR_SEM_TYPE_AMBIGUOUS."
implementacion:
  - `nucleo/generador/funciones.syn`: en el pre-pass de hoisting, la rama `OpBinaria` deja de asumir `int64_t` y delega en `_syn_nativo_expr_tipo_c` (paridad S1 `tipo_de_expr`); el `else` final de tipos no literales usa la misma paridad.
  - `nucleo/generador/orquestador.syn` `_syn_nativo_expr_tipo_c` OpBinaria: operadores logicos/comparacion -> `int`; si algun lado es `double` -> `double`; si no, tipo izquierdo y fallback derecho (paridad `emit_expressions.py` L141-150).
  - `nucleo/generador/orquestador.syn` `_syn_nativo_expr_tipo_c` LlamadaFuncion: fallback a `_G_native_tipo_retorno` + `traducir_tipo_c` para llamadas que no son ADT/generico/estructura/coleccion/metodo (p. ej. `_syn_home()`, `concat()`).
  - `nucleo/generador/orquestador.syn` `ExprAccesoCampo`: si el objeto no es un identificador con tipo registrado, resuelve el tipo via `_syn_nativo_expr_tipo_c` antes de `_G_native_campo_tipo`.
  - `nucleo/generator.syn` se regenera con `_rebuild_generator.py`; se reformatean los submodulos y `nucleo/parser_sentencias.syn` para que `synapse fmt --check` quede GREEN.
oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## 2. Archivos a modificar

- `nucleo/principal.syn` - `_files[]` incluye `std/json.syn` y `std/texto.syn` antes de `actualizador.syn`
- `nucleo/generador/emision_c.syn` - buffer de emision C de 4 MB
- `nucleo/generador/nodos_flujo.syn` - buffer de emision C de 4 MB + reformato
- `nucleo/generador/orquestador.syn` - buffer, `OpBinaria`, `LlamadaFuncion`, `ExprAccesoCampo` + reformato
- `nucleo/generador/funciones.syn` - hoisting `OpBinaria` y `else` final via `_syn_nativo_expr_tipo_c`
- `nucleo/generador/monomorfizacion.syn` - reformato del submodulo
- `nucleo/generator.syn` - regenerado desde los submodulos
- `nucleo/parser_sentencias.syn` - reformato del parser
- `compilador/generator/generator.py` - buffer de emision C de 4 MB (S1)
- `nucleo/_rebuild_generator.py` - header del generador alineado con `synapse fmt --check`

## 3. Cita del manual (grep-chequeable)

```c
// cumple Manual 9 §6.2: el unity build nativo incluye std/json.syn/std/texto.syn y el buffer de 4 MB preserva el bootstrap S2
// cumple Manual 2 §8.2: inferencia de tipos determinista (paridad S1 tipo_de_expr) en OpBinaria, llamadas y acceso a campo
```

## 4. Verificacion

- `.venv\Scripts\python.exe main.py nucleo/principal.syn -o synapse_stage1.exe` - rc=0
- `.\synapse_stage1.exe nucleo/principal.syn -o synapse_stage2.exe` - rc=0
- `.\synapse_stage2.exe nucleo/principal.syn -o synapse_stage3.exe` - rc=0 y S2==S3 (SHA256 `950AA09B...A71B2A`)
- `.venv\Scripts\python.exe nucleo\_rebuild_generator.py` - `generator.syn` regenerado
- `.\synapse_stage2.exe fmt --check nucleo\generator.syn` - formato correcto
- `.venv\Scripts\python.exe -m pytest tests/auditoria/test_oraculos_check_cli.py tests/auditoria/test_oraculos_cli_lint_fmt.py tests/auditoria/test_oraculos_formatter_fix.py -v` - 16 passed
- `.venv\Scripts\python.exe auditoria\verificar_alineacion.py` - 0 brechas
- `.venv\Scripts\python.exe auditoria\contrastar.py --plan docs/plan_ME_r218_bootstrap_json.md` - verde
