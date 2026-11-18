# Plan ME r252 — sello de bootstrap reproducible y guard de binarios distribuidos

**Fase del roadmap:** Ola 4 — soporte del compilador (`r252_bootstrap_parity`).
**Micro-entregable:** `r252_bootstrap_parity`.
**Depende de:** `r243_native_fase32` (`379d978`) y `r244_paridad_lint_fmt_test` (`a4b6f6d`).
**Alcance:** que la regla de hierro del bootstrap (S2==S3 con diff 0 bytes) sea
verificable por cualquiera **sin** lanzar un build completo a mano, y que quede
detectado automáticamente el caso que ya rompió dos gates en esta rama: un
`synapse.exe` / `dist/bin/synapse.exe` que no corresponde al bootstrap actual.

**Estado medido antes de codificar** (HEAD `f36154e`):

| # | Comprobación | Resultado actual |
|---|---|---|
| D1 | ¿Existe un oráculo de S2==S3 invocable como test? | No: `auditoria/oraculos/oraculo_r192_bootstrap.py` solo compara artefactos que ya deben existir y ningún test lo invoca; el único sello real está dentro de `build.py` y del job `bootstrap` de `ci-tests.yml` |
| D2 | ¿Algo detecta que `dist/bin/synapse.exe` está stale? | No: en r243 el gate "verificó" un binario viejo (H-R247-1) y en r244 el oráculo necesitó refrescar los tres ejecutables a mano |
| D3 | `synapse_stage3.exe` | No existe en el checkout: el determinismo no es reproducible sin un build de ~40 min |

---

requisito: Manual 1 §6
texto: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0). El determinismo se verifica obligatoriamente en la CI mediante la comparación de los hashes SHA‑256 de las etapas 2 y 3."
implementacion: nuevo oráculo `auditoria/oraculos/oraculo_r252_paridad_bootstrap.py`
  con modo `--artefactos` (compara los hashes SHA-256 de `synapse_stage2.exe`
  y `synapse_stage3.exe` presentes) y modo `--construir` (lanza `build.py` y
  después compara), de modo que la regla de hierro es ejecutable por un
  desarrollador y por el job `bootstrap` de CI con el MISMO código;
  `build.py` deja de tener su propia copia del cálculo y delega en el oráculo.
oraculo: tests/auditoria/test_oraculos_r252_paridad_bootstrap.py

requisito: Manual 9 §6.2
texto: "- La verificación del bootstrap (diff 0 bytes)."
implementacion: el oráculo compara `sha256(synapse_stage2.exe)` contra
  `sha256(synapse_stage3.exe)` (no el tamaño ni la fecha) y devuelve rc=1 con
  el detalle de ambos hashes cuando difieren, que es exactamente el "diff 0
  bytes" que exige la validación cruzada de CI/CD; el resultado se publica en
  la salida estándar con el prefijo `[r252]` para quedar en el log del job.
oraculo: tests/auditoria/test_oraculos_r252_paridad_bootstrap.py

requisito: Manual 9 §2.3
texto: "   - Verificar el bootstrap (diff 0 bytes entre Stage 2 y Stage 3)."
implementacion: la verificación forma parte del pipeline de compilación: el
  mismo paso que ya sellaba S2==S3 en `build.py` pasa a invocar el oráculo, así
  que un bootstrap no determinista aborta el build con rc=1. El oráculo agrega
  además el guard de deriva (`--estricto`): compara el binario recién construido
  con `synapse.exe` y `dist/bin/synapse.exe` y falla si no coinciden, que es la
  forma de detectar un binario distribuido stale antes de publicarlo.
oraculo: tests/auditoria/test_oraculos_r252_paridad_bootstrap.py
