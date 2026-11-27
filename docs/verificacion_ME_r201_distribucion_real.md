# Verificación ME r201_distribucion_real — distribucion real

Fecha: 2026-11-06 · Verificador: `auditoria/contrastar.py` (gate MTS fase 4b)
Oráculo: `tests/installers/test_auto_actualizar_producto.py` — PASS (15 tests)
Alcance: checksum SHA-256 fail-closed; la firma Ed25519 y la custodia de
`release_keys/private.pem` quedan registradas como bloqueo externo.

## R1 — Manual 9 §3.2 (verificación de versión) — CUMPLE
`instaladores/common/auto_actualizar.py:2` cita `cumple Manual 9 §3.2`.
`verificar_version()` consulta el endpoint de GitHub Releases, valida el tag
semántico y solo marca `nueva_disponible` si la remota es mayor; ante error de
red/JSON/tag devuelve `ok=False` con el error real. `_es_mas_nueva()` no degrada
8.1.0 a 8.0.9.
Oráculo: release válido, error de red fail-closed y comparación semántica PASS.

## R2 — Manual 9 §3.2 (descarga de la nueva versión) — CUMPLE
`instaladores/common/auto_actualizar.py:2` cita `cumple Manual 9 §3.2`.
`descargar_actualizacion()` exige SHA-256, descarga por bloques con límite de
2 GiB a temporal y solo hace `os.replace()` si el hash coincide; checksum
ausente o distinto no deja artefacto. `obtener_sha256_desde_asset()` lee el
asset `.sha256` del release.
Oráculo: checksum válido, inválido y ausente PASS.

## R3 — Manual 9 §3.2 (backup de la versión anterior) — CUMPLE
`instaladores/common/auto_actualizar.py:2` cita `cumple Manual 9 §3.2`.
`crear_backup()` copia a `~/.synapse/backup/<binario>.bak`; `rollback()`
restaura de forma atómica y falla con error accionable si no existe el backup.
Oráculo: backup y rollback restauran el contenido original PASS.

## R4 — Manual 9 §3.2 (instalación de la nueva versión) — CUMPLE
`instaladores/common/auto_actualizar.py:2` cita `cumple Manual 9 §3.2`.
`instalar_actualizacion()` rechaza archivos vacíos, ejecuta `.exe`/`.msi`
verificados en Windows con flags silenciosos y en Linux/macOS devuelve
`manual=True` en vez de simular una instalación.
Oráculo: ejecución Windows simulada y rechazo de instalador vacío PASS.

## R5 — Manual 9 §4.1 (GitHub Releases) — CUMPLE
`instaladores/common/auto_actualizar.py:3` cita `cumple Manual 9 §4.1`.
El repo canónico es `synapse-native/synapse`; `_seleccionar_asset()` elige el
artefacto por plataforma y su `.sha256`. `README.md`, `instaladores/README.md`,
`instaladores/windows/synapse.iss` y `docs/guia_usuario_instaladores.md` usan
ese repo y no citan `anomalyco/opencode` ni `synapse-lang/synapse`.
Oráculo: repo canónico, asset/checksum y URLs de documentación PASS.

## Evidencia ejecutada
- `pytest tests/installers/test_auto_actualizar_producto.py -v` — 15 passed.
- `pytest tests/installers/test_auto_actualizar.py tests/installers/test_auto_actualizar_producto.py -v` — 17 passed.
- `contrastar.py --plan docs/plan_ME_r200_opensyn_doctor.md --plan docs/plan_ME_r201_distribucion_real.md` — PASS (r200 y r201 en el mismo index).
- `verificar_alineacion.py` — 0 brechas.
