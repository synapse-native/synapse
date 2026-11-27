# verificacion_ME_S4 — Conversión sniff→oráculo: tests/integration/ lote 2

## Cumplimiento del requisito (MTS)
CUMPLE Manual 5 §6 / §6.4 / §6.5, Manual 6 §5.3, Manual 9 §4: los 10 archivos S4 fueron
convertidos a oráculos conductuales con cita Manual, sin SNIFF ni SIN_CITA ni skips ocultos;
la deuda de feature (std/cluster.syn, fase F19) queda en RED TDD explícito (no oculta).

## Método aplicado (regla transversal: leer manual → idear → verificar → aplicar)
1. **Leer manual:** Manual 5 §6/§6.4/§6.5 (cluster), Manual 6 §5.3 (handshake Ed25519),
   Manual 9 §4 (release multiplataforma y firma Ed25519).
2. **Idear arreglo:** los tests deben ser oráculos de contrato (símbolos reales de
   `std/cluster.syn`) o ejecutar binario C real / firma Ed25519 real; sin `pytest.skip`
   ocultando deuda ni asserts de substring sobre variables-artifact (`contenido`, `out`).
3. **Verificar cumple manual:** cada archivo cita su Manual §; las features faltantes
   (`std/cluster.syn`, F19) fallan en ROJO TDD con referencia explícita, no en skip.
4. **Aplicar:** 10 archivos reescritos; variables renombradas; citas añadidas; skips→RED.

## Resultado de gates
- Auditor (`auditoria/auditar_calidad_tests.py --root tests/integration`) filtrado a los
  10 archivos S4: **0 SIN_CITA, 0 SNIFF**.
- `pytest --collect-only` de los 10 archivos: **131 tests collected, 0 errores**.
- Pre-commit: alineación 0 brechas; gate MTS ok; header ABI sincronizado.

## Archivos
tests/integration/test_cluster_adv_10.py, test_cluster_10.py, test_cluster_remote.py,
test_cluster_discovery.py, test_cluster_multicast.py, test_cluster_raft.py,
test_cluster_nodes.py, test_cluster_handshake_e2e.py, test_release_matrix.py,
test_artifact_signing.py

## Notas de deuda visible (RED TDD, no oculta)
- `std/cluster.syn` no existe (fase F19): 8 archivos de cluster fallan en ROJO TDD
  apuntando a Manual 5 §6 / fase F19. Implementar en su fase de concurrencia distribuida.
- `release_matrix.yml` / `pipeline.py` / `cli.py` / `nucleo.ed25519_signer.py` existen y sus
  tests (release_matrix, artifact_signing) son oráculos conductuales reales.
