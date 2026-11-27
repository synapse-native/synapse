# Plan ME r212 - Memoria persistente cifrada

## Contexto

`opensyn/memoria_persistente_cifrada.syn` esta en el baseline porque usa APIs
inexistentes en el runtime real: `bytes(32)`, `crypto_argon2id`,
`crypto_randombytes`, `crypto_secretbox`, SQLite (`abrir_db_cifrada`,
`ejecutar_sql_blob`, ...), `os.hardware_uuid()` y `os.machine_id()`. Ademas
declara estado global mutable con `var`, que S1 no acepta a nivel de modulo.

El plan maestro exige compilar el modulo, retirarlo del baseline y demostrar
escritura/lectura cifrada sin fuga de texto en claro. La implementacion usa las
primitivas reales disponibles:

- XSalsa20-Poly1305 real de TweetNaCl mediante
  `cluster_sesion_cifrar_buffer`/`cluster_sesion_descifrar_buffer`
  (`runtime/core/cluster.c`), con nonce CSPRNG por entrada.
- Derivacion de clave SHA-256 iterada con sal de hardware (Argon2id no existe
  en el runtime; ver desviacion H-R212-1).
- Almacen cifrado plano linea-a-linea en `~/.opensyn/memoria.db` (no hay API
  SQLite expuesta a Synapse; ver desviacion H-R212-2).
- Estado explicito `MemoriaCifrada` devuelto por cada operacion mutadora, en
  lugar de variables globales mutables no soportadas por S1 (H-R212-3).

## Requisitos (MTS)

requisito: Manual 6 §1.1
texto: "El ecosistema Synapse se basa en un **Arbol de Sintaxis Abstracta (AST) canonico y unificado** denominado `SemNodo[]`."
implementacion: `opensyn/memoria_persistente_cifrada.syn` conserva el modelo de tres capas del agente y usa estructuras canonicas planas (`PatronAprendido`, `MemoriaNegativa`, `CapaMemoria`) sin duplicar el AST ni introducir un backend paralelo.
oraculo: tests/opensyn/test_memoria_cifrada_comportamiento.py

requisito: Manual 7 §7.3
texto: "**Cero telemetria:** Verificado con monitoreo de red (sin conexiones salientes)." / "**Sandboxing:** El servidor de inferencia se ejecuta con permisos minimos."
implementacion: la clave maestra vive solo en RAM y `memoria_cerrar` la borra con `crypto_memzero`; el almacen solo contiene blobs XSalsa20-Poly1305 en hexadecimal, sin texto legible ni telemetria.
oraculo: tests/opensyn/test_memoria_cifrada_comportamiento.py

requisito: Manual 2 §5.1
texto: "**`requiere`:** Se evalua antes de la primera instruccion del cuerpo. Todas las expresiones deben ser booleanas." / "**`garantiza`:** Se evalua inmediatamente antes de cada `retornar`."
implementacion: toda funcion publica del modulo declara `requiere`/`garantiza` booleanos y usa `_resultado_`; las funciones internas tambien los declaran para mantener el contrato verificable.
oraculo: tests/opensyn/test_memoria_cifrada.py

## Archivos

- `opensyn/memoria_persistente_cifrada.syn` - implementacion compilable con
  cifrado real, tres capas, estado explicito y KDF SHA-256 iterado.
- `tests/opensyn/test_memoria_cifrada_comportamiento.py` - oraculo E2E nuevo:
  escritura/lectura cifrada, no-fuga en claro y rechazo de passphrase erronea.
- `tests/fixtures/compilacion_baseline.txt` - retirar la ruta del modulo.
- `docs/alineacion/r212_memoria_cifrada.md` - expediente.
- `docs/verificacion_ME_r212_memoria_cifrada.md` - verificacion.
- `docs/reportes/R212.md` - reporte.

## Desviaciones declaradas

- H-R212-1: Argon2id no esta implementado en el runtime (solo SHA-256 y
  Ed25519). Se usa KDF SHA-256 iterado (20000 rondas) con sal derivada de
  hardware. Resolucion: implementar `runtime/core/key_derivation.c` con Argon2id
  en un ME posterior; el modulo queda aislado tras `derivar_clave`.
- H-R212-2: no hay API SQLite expuesta a Synapse. La capa Evolucion usa un
  almacen cifrado plano con una entrada cifrada por linea; la semantica
  (patrones, fallos, proyecto) se conserva. Resolucion: binding SQLite cifrado
  cuando el runtime lo exponga.
- H-R212-3: S1 no soporta variables globales mutables. La API usa
  `MemoriaCifrada` explicito; el llamador reasigna el estado devuelto.
- No se toca `docs/gobernancia/GUIA_DE_GOBERNANZA.md` ni los artefactos no
  rastreados `nucleo/embedded_libs.h`, `nucleo/lsp_v3.c.bak`,
  `nucleo/lsp_v3.c.new`.
- Los tests existentes no se modifican; se ejecutan como regresion.

## Oraculos de cierre

1. `.venv\Scripts\python.exe main.py opensyn/memoria_persistente_cifrada.syn --check --no-emit` -> rc 0.
2. `.venv\Scripts\python.exe -m pytest tests/opensyn/test_memoria_cifrada.py -v` -> verde sin modificar el test.
3. `.venv\Scripts\python.exe -m pytest tests/opensyn/test_memoria_cifrada_comportamiento.py -v` -> E2E verde.
4. `.venv\Scripts\python.exe -m pytest tests/integration/test_compilacion_fase32.py -v` -> verde.
5. `.venv\Scripts\python.exe auditoria/verificar_alineacion.py` -> 0 brechas.
6. `.venv\Scripts\python.exe auditoria/alineacion.py --verificar --me r212_memoria_cifrada` -> sin brechas.
7. `.venv\Scripts\python.exe auditoria/contrastar.py --plan docs/plan_ME_r212_memoria_cifrada.md` -> sin brechas.
