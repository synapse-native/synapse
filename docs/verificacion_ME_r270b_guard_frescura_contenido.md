# Verificación ME r270b — guard de frescura por contenido (H-R252-5)

- Manual 1 §6 CUMPLE: el sello del bootstrap sigue siendo la comparación
  SHA-256 de las etapas 2 y 3 (diff 0 bytes) y no cambia de criterio; lo que
  cambia es cómo se decide que la etapa 2 corresponde al código actual: por el
  hash del contenido de `nucleo/principal.syn` sellado en
  `synapse_stage2.stamp`, no por `mtime`. Tocar el archivo sin cambiar su
  contenido ya no invalida el bootstrap; cambiarlo sí (`[FAIL] … cambio desde
  el build`, con ambos hashes). El sello guarda también el SHA-256 de la etapa
  2 y no acredita si el binario presente es otro (commit `8e2c41f`), así que la
  frescura nunca se apoya en un artefacto distinto del sellado.
  Evidencia: `auditoria/oraculos/oraculo_r252_paridad_bootstrap.py`,
  `build.py:70-75`.
- Manual 9 §6.2 CUMPLE: el sello lo escribe el propio oráculo con `--sellar`,
  que es la única implementación del sello, y lo invocan tanto `build.py` como
  el job `bootstrap` de `.github/workflows/ci-tests.yml`. Se escribe sólo
  después de verificar, así que un build roto no deja certificación.
- Manual 9 §6.1 CUMPLE: sin sello (checkout limpio, artefactos no versionados)
  el oráculo conserva el criterio de `mtime` con el aviso
  `[WARN] sin synapse_stage2.stamp`, de modo que el comportamiento previo y sus
  tests siguen siendo válidos.

Oráculo del ME: `tests/auditoria/test_r270b_frescura_contenido.py` (6 casos:
mtime ignorado con sello, fuente modificada falla, sello de otra etapa 2 no
acredita (commit `8e2c41f`), respaldo `mtime` sin sello, `--sellar` escribe el
hash, `--sellar` no certifica un sello roto).

Comprobación end-to-end sobre los artefactos reales: `--artefactos --estricto
--sellar` → `RC=0` con sello `9e72e10c716dfc01…`; tras `touch
nucleo/principal.syn` (sin cambio de contenido) `--artefactos --estricto` sigue
en `RC=0` con `[OK] sello de frescura`, que es exactamente el falso rojo que
describía H-R252-5. La cadena se reconstruyó después (`build.py --skip-test`,
`EXIT=0`) y el sello vigente corresponde a S2==S3 `30c07ef61c5f25a7`
(2.559.482 B).
