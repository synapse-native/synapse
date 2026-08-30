# plan_ME_S4 — Conversión sniff→oráculo: tests/integration/ lote 2

MTS (docs/METODO_TRABAJO.md). Oráculo ejecutable; el código lleva cita grep-chequeable.

## Requisito
requisito: Manual 5 §6 / §6.4 / §6.5 (cluster) · Manual 6 §5.3 (handshake Ed25519) · Manual 9 §4 (release/signing)
texto: "Cluster/release/signing validan comportamiento real, no substring en artefacto."
implementacion: Convertir test_cluster_*.py (8), test_release_matrix.py, test_artifact_signing.py:
  - Renombrar variables SNIFF (contenido->fuente, out->stdout_bin) y evitar 'in output'/'in clave'
    que el auditor marca como substring en artefacto.
  - Añadir cita Manual a los 10 archivos (SIN_CITA).
  - Eliminar skips ocultos: _cluster() y test_importar_cluster_compila -> RED TDD explicito
    (pytest.fail) apuntando a Manual 5 §6 / fase F19. Marcar @pytest.mark.tdd donde aplica.
  - Tests que ejecutan binario C real (discovery/multicast/raft/nodes/handshake_e2e) y firman
    Ed25519 real (artifact_signing) se conservan como oráculos conductuales.
oraculo: tests/integration/test_release_matrix.py

## Alcance (sin desviación)
Convierte ÚNICAMENTE los archivos del lote indicado; no toca otros directorios.

## Criterio de aceptación
- Sin assert substring SNIFF (auditor: 0 SNIFF en los 10 archivos).
- Toda cita Manual presente (auditor: 0 SIN_CITA en los 10 archivos).
- Cero pytest.skip ocultando deuda: toda feature faltante es RED TDD con ME/fase de feature.
- Tests completos (oráculos de contrato / ejecución real) listos para pasar en VERDE al implementar la feature.
