# Verificación ME r212 - Memoria persistente cifrada

Plan: `docs/plan_ME_r212_memoria_cifrada.md`.
Expediente: `docs/alineacion/r212_memoria_cifrada.md`.
Evidencia: `auditoria/evidencia/cc3cf959ff0b1a25.json`.

## Requisitos verificados

- Manual 6 §1.1 - AST canónico `SemNodo[]` y modelo de tres capas sin backend paralelo - CUMPLE (`opensyn/memoria_persistente_cifrada.syn:3`).
- Manual 7 §7.3 - cero telemetría, clave solo en RAM y almacén cifrado - CUMPLE (`opensyn/memoria_persistente_cifrada.syn:4`).
- Manual 2 §5.1 - contratos `requiere`/`garantiza` booleanos en funciones públicas - CUMPLE (`opensyn/memoria_persistente_cifrada.syn:5`).

## Oráculos ejecutados

- `.venv\Scripts\python.exe main.py opensyn/memoria_persistente_cifrada.syn --check --no-emit` -> rc 0, sintaxis y semántica OK.
- `.venv\Scripts\python.exe -m pytest tests/opensyn/test_memoria_cifrada.py -q` -> 14 passed; test existente sin modificar.
- `.venv\Scripts\python.exe -m pytest tests/opensyn/test_memoria_cifrada_comportamiento.py -q` -> 1 passed; E2E nuevo (escritura/lectura cifrada, persistencia, no fuga en claro, rechazo de passphrase errónea).
- `.venv\Scripts\python.exe -m pytest tests/integration/test_compilacion_fase32.py -q` -> 2 passed; el módulo ya compila y se retiró del baseline.
- `.venv\Scripts\python.exe auditoria/verificar_alineacion.py` -> sin brechas.
- `.venv\Scripts\python.exe auditoria/alineacion.py --verificar --me r212_memoria_cifrada` -> 1 archivo, citas textuales verificadas, 2 oráculos ejecutados, evidencia `cc3cf959ff0b1a25`.
- `.venv\Scripts\python.exe auditoria/contrastar.py --plan docs/plan_ME_r212_memoria_cifrada.md` -> 3 requisitos, 2 oráculos release, sin brechas.

## Notas

- H-R212-1: Argon2id no existe en el runtime; `derivar_clave` usa SHA-256 iterado (20000 rondas) con sal de hardware. Resolución: implementar Argon2id en un ME posterior.
- H-R212-2: no hay API SQLite expuesta a Synapse; la capa Evolución usa un almacén plano con una entrada cifrada por línea. Resolución: binding SQLite cifrado cuando el runtime lo exponga.
- H-R212-3: S1 no soporta variables globales mutables; la API usa `MemoriaCifrada` explícito y el llamador reasigna el estado devuelto.
- El E2E destapó una corrupción de pool en `tokenizar`: `tokens.agregar(minusculas(actual))` duplicaba la expresión en el constructor de la estructura y `minusculas` (función pura) libera su parámetro, produciendo un triple free del mismo bloque. Se corrigió asignando `let token = minusculas(_syn_strcpy(actual))` antes de `agregar`, de modo que `minusculas` libere solo la copia.
- El driver del E2E es idempotente: si el proyecto ya existe, no vuelve a guardar; así la prueba de persistencia no duplica entradas.
- El aviso de `test_ffi_marshaling_auto` por `ffi_marshaling.h` es preexistente y ajeno a este ME.
- `nucleo/embedded_libs.h`, `nucleo/lsp_v3.c.bak` y `nucleo/lsp_v3.c.new` son artefactos no rastreados de otro agente; no forman parte de este cambio.
- No se modificaron tests existentes; el test E2E `tests/opensyn/test_memoria_cifrada_comportamiento.py` es nuevo de este ME.
