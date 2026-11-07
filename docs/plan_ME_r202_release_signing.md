# Plan ME-r202 — Release firmado real y actualizador con Ed25519

Contexto: r201 dejó el actualizador con SHA-256 y documentó la firma como fuera
de alcance. Este ME cierra el sellado criptográfico: claves PEM reales, firma
de cada artefacto, verificación fail-closed en el actualizador, workflow de
release que firma y verifica, e instaladores Linux/macOS que ya no ignoran la
firma con `|| true`.

## Ley citada (MTS: requisito / texto / implementacion / oraculo)

requisito: Manual 9 §3.2 (Verificación de firma)
texto: "**Verificación de firma**: Comprueba la firma Ed25519 del artefacto."
implementacion: `instaladores/common/auto_actualizar.py` — `verificar_version()` expone `url_sig`/`firma_disponible`; el CLI exige el asset `.sig`, descarga la firma hex, verifica Ed25519 contra `release_keys/public.pem` (o `SYNAPSE_PUBLIC_KEY`/`--clave`) y borra el artefacto si la firma no coincide. `obtener_firma_desde_asset()` y `verificar_firma_actualizacion()` fallan cerrado.
oraculo: tests/installers/test_auto_actualizar_firma.py

requisito: Manual 9 §6.3 (Sellado Criptográfico Definitivo)
texto: "Cada artefacto se firma con la clave privada Ed25519 del proyecto. Se generan:"
implementacion: `distribuir.py` firma y verifica cada artefacto firmable (`.exe`, `.msi`, `.sh`, `.iss`, `.dmg`, `.pkg`, `.tar.gz`, `.zip`), genera `.sig`, `.sha256`, SBOM SPDX, attestation SLSA y firma `MANIFEST.sha256`; `instaladores/common/verificar_firma.py` implementa firma/verificación PEM, hex y raw con CLI fail-closed. `scripts/ci_sign.py` usa el mismo verificador en CI.
oraculo: tests/integration/test_artifact_signing.py

requisito: Manual 9 §4.1 (GitHub Releases)
texto: "Archivos de firma (`.sig`) y checksums (`.sha256`)."
implementacion: `.github/workflows/release_matrix.yml` construye las 4 plataformas, ejecuta `distribuir.py --requerir-firma` con `ED25519_PRIVATE_KEY`, verifica cada `.sig` contra `synapse.pub` (`SIGNATURE_VALID=YES`), valida `.sha256`/SBOM/attestation y solo publica el release en tags `v*`; `verificar_firma.py` valida los `.sig` publicados.
oraculo: tests/integration/test_release_matrix.py

requisito: Manual 9 §2.1 (Artefactos Generados)
texto: "El proceso de empaquetado genera artefactos para las plataformas soportadas:"
implementacion: `distribuir.py` conserva el empaquetado de stage2, instaladores y metadatos para Windows, Linux y macOS, y añade la firma/checksum a cada artefacto antes de subirlo.
oraculo: tests/integration/test_distribucion.py

requisito: Manual 1 §3.1 (Pipeline unificado)
texto: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido:"
implementacion: `instaladores/common/auto_actualizar.py` mantiene la herramienta Python del ecosistema y verifica el mismo artefacto que produce el pipeline antes de instalarlo.
oraculo: tests/installers/test_auto_actualizar_producto.py

## Fuera de alcance
- Custodiar la clave privada fuera de GitHub Secrets: el workflow exige
  `ED25519_PRIVATE_KEY`; la privada local `release_keys/private.pem` sigue
  ignorada y nunca se commitea.
- `synapse update` nativo en Synapse: este ME corrige el actualizador Python y
  la cadena de release; el comando nativo queda para el siguiente ME.
- No se toca `nucleo/lsp_v3.syn` ni trabajo sin stagear de otro agente.

## Pasos de verificación
1. `.venv\Scripts\python.exe -m pytest tests/installers/test_auto_actualizar_firma.py tests/installers/test_firma.py -v`
2. `.venv\Scripts\python.exe -m pytest tests/integration/test_distribucion.py tests/integration/test_artifact_signing.py tests/integration/test_release_matrix.py -v`
3. `.venv\Scripts\python.exe distribuir.py --requerir-firma`
4. `.venv\Scripts\python.exe scripts\ci_sign.py verify instaladores\dist\distribucion\synapse.exe instaladores\dist\distribucion\synapse.exe.sig instaladores\dist\distribucion\synapse.pub`
5. `python auditoria/contrastar.py --plan docs/plan_ME_r202_release_signing.md`
6. `git add` de los archivos del ME; `python auditoria/alineacion.py --verificar --me r202_release_signing`

## Gates
- `contrastar.py` debe resolver los 5 requisitos con el oráculo ejecutado.
- Cada archivo de producción modificado lleva `# cumple Manual X §Y` (Python/CI).
- `verificar_alineacion.py` debe reportar 0 brechas.
- No commit hasta que el Arquitecto lo pida.
