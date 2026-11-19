# Plan ME r270b — guard de frescura por contenido (H-R252-5)

**Fase del roadmap:** Frente H (release industrial), Ola H1 — deuda residual del
ME `r270_bootstrap_emision_paridad`.
**Micro-entregable:** `r270b_guard_frescura_contenido`.
**Hallazgo:** H-R252-5 (BAJA, registrado en `docs/plan_maestro_deudas.md`).

**Problema medido.** El guard de frescura del oráculo r252 compara `mtime`:
`_mas_nuevo(raiz, "synapse_stage2.exe", "nucleo/principal.syn")`. Reproducido en
aislamiento con etapa 2 y etapa 3 byte-idénticas: con los artefactos más nuevos
que la fuente el sello da `RC=0`; tras tocar **sólo** el `mtime` de la fuente
(`git checkout`, guardado del editor) da `RC=1` con el mismo hash
`3ec3ed9b76ce3b6e` y el mensaje «artefacto stale». Ocurrió en la verificación de
r270 y obligó a reconstruir la cadena completa para descubrir que el binario era
válido. El gate correcto para la regla de hierro es el **contenido** de la
fuente que produjo la etapa 2, no la hora del sistema de archivos.

---

requisito: Manual 1 §6
texto: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0). El determinismo se verifica obligatoriamente en la CI mediante la comparación de los hashes SHA‑256 de las etapas 2 y 3."
implementacion: `auditoria/oraculos/oraculo_r252_paridad_bootstrap.py` gana un
  sello de contenido (`synapse_stage2.stamp`) con el SHA-256 de
  `nucleo/principal.syn` en el momento del build. Si el hash sellado coincide con
  el contenido actual, la etapa 2 se considera fresca **sin mirar `mtime`**; si
  difiere, el sello falla nombrando ambos hashes. El criterio del manual no
  cambia: sigue siendo `diff 0 bytes` entre etapa 2 y etapa 3 por SHA-256.
oraculo: tests/auditoria/test_r270b_frescura_contenido.py

requisito: Manual 9 §6.2
texto: "- La verificación del bootstrap (diff 0 bytes)."
implementacion: El sello lo escribe el mismo oráculo (`--sellar`), que es la
  única implementación del sello, y lo invocan `build.py` y el job `bootstrap` de
  `.github/workflows/ci-tests.yml` tras construir las tres etapas. El sello sólo
  se escribe si la verificación ya pasó, así que un build roto nunca deja una
  certificación detrás.
oraculo: tests/auditoria/test_r270b_frescura_contenido.py

requisito: Manual 9 §6.1
texto: "□ **Bootstrap exitoso**: en cada target, el proceso de bootstrap de 3 etapas produce `diff 0 bytes` entre Stage 2 y Stage 3."
implementacion: Sin sello presente (checkout limpio, artefactos ajenos al
  repositorio) el oráculo conserva el criterio de `mtime` con un aviso
  `[WARN] sin sello de frescura`, de modo que el comportamiento previo y sus
  tests siguen siendo válidos y ningún pipeline depende de un archivo que no
  está versionado.
oraculo: tests/auditoria/test_r270b_frescura_contenido.py

---

## Archivos de producción

- `auditoria/oraculos/oraculo_r252_paridad_bootstrap.py`: sello de contenido,
  bandera `--sellar`, guard por hash con respaldo `mtime`.
- `build.py`: sella tras cerrar las 3 etapas (`--artefactos --sellar`).
- `.github/workflows/ci-tests.yml`: el job `bootstrap` sella igual que local.
- `.gitignore`: `synapse_stage2.stamp` no se versiona (artefacto de máquina).

## No se toca

- `tests/auditoria/test_r270_bootstrap_paridad.py` y
  `test_oraculos_r252_paridad_bootstrap.py`: siguen siendo válidos sin cambios
  porque el criterio `mtime` se mantiene como respaldo cuando no hay sello.
- `nucleo/principal.syn` y el enlace nativo: r270 ya cerró H-R252-4.
