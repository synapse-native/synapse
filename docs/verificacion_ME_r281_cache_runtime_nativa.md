# Verificación ME r281_cache_runtime_nativa

**Plan:** `docs/plan_ME_r281_cache_runtime_nativa.md`
**Fecha:** 2026-11-21
**Alcance:** cerrar H-R279-2 haciendo que el compilador nativo reutilice los
`.o` del runtime que `pipeline.py` cachea, verificados por SHA-256 del fuente.
Ningún test se modifica; el `timeout=120` del test queda intacto.

## Requisitos

- Manual 8 §4.1 — CUMPLE: `synapse build <archivo>` sigue compilando a binario.
  Medición real con `synapse_stage1.exe` sobre un `.syn` mínimo:
  **93,18 s → 1,25 s (1ª) y 1,37 s (2ª)**, salida `42` idéntica a la del
  compilador Python. Evidencia: `nucleo/principal.syn:796`; oráculo
  `auditoria/oraculos/oraculo_r281_cache_nativa.py` (`OK`).
- Manual 8 §4.2 — CUMPLE: el reuso solo se activa con la optimización por
  defecto (`-O2`); `--release`, `--debug` y `--profile` enlazan desde fuente
  como antes y las flags no cambian. Evidencia: `nucleo/principal.syn:830`.
- Manual 9 §6.2 — CUMPLE: `synapse_stage2.exe` y `synapse_stage3.exe` son
  byte-idénticos (`sha256 027f1fdd8803d07b32737207dc0e5a27ab88c9fdd786f86bad17dc3513a1a020`)
  y S3 se construyó en 20,33 s. El test que fallaba por timeout (inmutable)
  pasa sin tocar su aserción: `2 passed in 24,54 s`. Evidencia:
  `nucleo/principal.syn:854`.

## Gates ejecutados

- `pytest tests/unit -q` → **517 passed en 207,19 s** (antes: 515 passed + 2
  failed en 537,82 s).
- `pytest tests/unit/test_r3_param_adt.py -v` → **2 passed en 24,54 s**
  (antes: 2 failed por `TimeoutExpired` a 120 s en 250,41 s).
- `synapse_stage2.exe nucleo/principal.syn -o synapse_stage3.exe` → rc=0 en
  20,33 s; `sha256sum` de stage2 y stage3 idéntico.
- `auditoria/oraculos/oraculo_r281_cache_nativa.py` → `OK: oraculo r281`.
- `auditoria/contrastar.py --plan docs/plan_ME_r281_cache_runtime_nativa.md`
  → 3/3 requisitos, oráculos ejecutados, PASS.
- `auditoria/alineacion.py --verificar --me r281_cache_runtime_nativa` →
  citas textuales verificadas, 2 oráculos, evidencia
  `auditoria/evidencia/8140c12bce93120e.json`.
- `auditoria/verificar_alineacion.py`, `auditoria/verificar_encoding.py`,
  `auditoria/verificar_suite.py` → OK (abajo).

## Fallback verificado por diseño

La reutilización es **todo o nada**: si falta un `.o`, falta su sidecar, el
SHA-256 del fuente no coincide o el segundo campo del sidecar (ruta del
compilador) no es el toolchain resuelto, se enlazan las fuentes como antes. La
primera prueba de este ME falló justamente por mezclar objetos de TDM-GCC con
los del toolchain incluido (`undefined reference to stat64i32`); por eso el
sidecar ahora se compara también contra el compilador resuelto y se añadió
`toolchain_gcc12\mingw64\bin\gcc.exe` a la búsqueda junto al ejecutable.

## Límites

- La caché se usa solo con `-O2`: `--release` (`-O3 -flto`) sigue compilando el
  runtime desde fuente (93 s la primera vez). Extenderlo exige objetos
  compilados con esas flags y su propio sidecar.
- En una instalación sin `~/.synapse/cache/runtime_obj` (primera compilación
  nativa de la máquina) el tiempo es el histórico; a partir de ahí hay HIT.
