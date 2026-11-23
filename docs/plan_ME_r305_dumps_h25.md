# Plan de Micro-Entregable r305_dumps_h25

## Objetivo

Cerrar la deuda histórica **H25** (registrada desde F0: "artefactos generados
trackeados obsoletos vs `.syn` renombrados … higiene en ME-R8"). Quedan ocho
dumps del compilador S1 versionados con `.syn` homónimo:

`nucleo/generator.c`, `generator_pgo.c`, `lexer.c`, `memoria.c`, `parser.c`,
`principal.c`, `resolvedor_axon.c`, `tabla_simbolos.c`.

Mismo criterio que r303 (H-R302-1): no se regeneran; se retiran. El build
compila desde los `.syn` y escribe objetos `_<módulo>.c`; ningún gate, test ni
instalador los usa (el instalador empaqueta `ai_orchestrator.c`, `federated.c`,
`llama_client.c`, que **no tienen** `.syn` y se conservan).

Efecto colateral: `scripts/migrate_to_canonical_header.py` (migración D-9(e),
ya aplicada) apunta a `nucleo/lexer.c` en `TARGETS` y fallaría al abrir un
archivo inexistente; se quita de la lista.

## Requisito 1 — ninguna regresión por el retiro

requisito: Manual 1 §7.4
texto: "Aprobación del 100% de los tests unitarios, de integración y fuzzing sin regresiones."
implementacion: se retiran de git los ocho dumps y se actualiza `TARGETS` del script de migración; el oráculo exige que ningún `.c` versionado bajo `nucleo/` tenga `.syn` homónimo (la clase completa, sin allowlist) y que las fuentes `.syn` sigan presentes.
oraculo: tests/auditoria/test_r305_dumps_h25_retirados.py

## Requisito 2 — inventario SPDX coherente

requisito: Manual 9 §6.1
texto: "□ **SBOM y SLSA**: generados y firmados correctamente."
implementacion: `synapse.spdx.json` se regenera con `nucleo/sbom.py --versionados` y se recalcula su `.sha256`; el oráculo r304 verifica que no queden entradas de los retirados ni rutas inexistentes.
oraculo: tests/auditoria/test_r304_sbom_determinista.py

## Evidencia

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r305_dumps_h25_retirados.py` | 4 passed |
| `pytest tests/auditoria/test_r304_sbom_determinista.py` | 5 passed |
| `nucleo/sbom.py --versionados --check` | rc=0 |
| `build.py --skip-test` | rc=0, S2==S3 `ad65693a51c2` |
| `verificar_alineacion.py` | 0 brechas |
| `contrastar.py --plan docs/plan_ME_r305_dumps_h25.md` | PASS (2/2) |
