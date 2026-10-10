# Plan ME r182a — backend WASM F25 funcional (wat2wasm GREEN)

requisito: Manual 1 §3.2
texto: "Traduce el AST validado a código intermedio: C (C99/C11), LLVM IR o WAT (WASM)." y "Salida: `synapse_unity.c`, `.ll` o `.wat`."
implementacion: reparar `compilador/wat_generator.py` para que el WAT emitido sea VÁLIDO (wat2wasm rc=0): (1) toda `LlamadaFuncion` a una función no definida en el AST se declara como `(import "env" "<nombre>" (func ...))` con firma inferida best-effort de los tipos de argumentos y del contexto de uso; (2) declarar `(local ...)` para cada variable de `DeclaracionVariable`/parámetro usada antes de `local.set`/`local.get`; (3) exportar `principal`/`main` automáticamente.
oraculo: tests/auditoria/test_oraculos_r182a_wasm_valido.py — probe .syn compilado con "synapse build --target wasm" produce .wat que wat2wasm compila a .wasm rc=0 (magic 0asm), export "principal", import de llamadas externas y orden imports-primero.

requisito: Manual 8 §4.2
texto: "| `--target` | `native`, `wasm`, `llvm` (por defecto `native`). |"
implementacion: en `pipeline.py` (rama `target == 'wasm'`), ampliar la búsqueda de `wat2wasm` al emsdk local (`C:/emsdk/node/*/wat2wasm.CMD`) para que la fase `.wat → .wasm` sea operativa en esta estación (hoy imprime "[INFO] wat2wasm no encontrado"); no cambia la API ni los flags.
oraculo: tests/auditoria/test_oraculos_r182a_wasm_valido.py — test_wasm_magic_y_export_entrada verifica "[OK] WASM generado" y .wasm con magic 0asm.

requisito: Manual 1 §3.2
texto: "Emite funciones en orden alfabético (determinismo)."
implementacion: los imports automáticos se emiten en orden determinista (orden de primera aparición en el AST; el orden de funciones ya es el del AST canónico).
oraculo: tests/auditoria/test_oraculos_r182a_wasm_valido.py — test_determinismo_wat verifica hash idéntico entre compilaciones.

estado: PENDIENTE
