# REPORTE ME_M1_HELLO - ME: M1_HELLO (formato binario HELLO)

--- REPORTE DE MICRO-ENTREGABLE ---
TAREA: Implementar handshake HELLO/HELLO_RESP en layout binario `[nonce 32B][pubkey 32B][firma 64B]` (128 B) con prefijo identificador, sin delimitadores de texto (sin `-`/`|`). Emisor firma Ed25519; receptor verifica firma y parsea HELLO_RESP.
FASE: 27 / Fase 2 nativa (feature/fase2-nativa-hm) - ME M1_HELLO
MANUAL REFERENCIADO: Manual 6 §5.3 (Handshake Ed25519 Zero-Trust)
HASH COMMIT: d8d0ef9 (bundle WIP del otro agente: implementación cluster.c + oráculo test_hello_wire)
COMPILACION: N/A para el compilador S1 (runtime/core/cluster.c es código C del runtime, compilado con el toolchain gcc del repo). El oráculo se builda vía conftest integrando el binario de prueba con las dependencias del runtime.
TESTS:
  - `pytest tests/integration/test_hello_wire.py` -> 1/1 PASS (emisor empaqueta binario 128B [32][32][64]; receptor parsea HELLO_RESP y verifica firma Ed25519 válida).
  - Oráculo C `tests/test_hello_wire.c` incluido en el binario; 1 assert de wire PASS.
VERIFICADOR: `python auditoria/verificar_alineacion.py` -> 0 brechas (las 3 [!] de este turno se resuelven con este reporte). `python auditoria/contrastar.py --plan docs/plan_ME_M1_HELLO.md` -> PASS.
MODIFICACIONES DE TESTS: ninguna debilitante; se verificó oráculo existente del otro agente.
PROXIMO PASO: ninguno para M1_HELLO (completado). El Arquitecto resuelve Fase 23 (runtime .o) si se desea ejecución end-to-end de cluster.
--- FIN ---
