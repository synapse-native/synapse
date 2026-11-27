# Verificación ME r273 — instalador con modelo grande

**Fecha:** 2026-11-19
**Plan:** `docs/plan_ME_r273_installer_modelo_grande.md`
**Expediente de alineación:** `docs/alineacion/r273_installer_modelo_grande.md`
**Cita textual (Manual 9 §5.3):** «El modelo se descarga desde Hugging Face o
Axon Hub, y se verifica su integridad mediante SHA‑256.»

## 1. Manual 9 §5.3 CUMPLE — descarga y verificación SHA‑256

- `runtime/core/cripto.c:119` y `:177` — `sha256_transform` con ventana rodante
  de 16 palabras (desenrollado) y `sha256_update` por bloques con `memcpy`.
  Mismo digest FIPS 180-4: contrastado contra `hashlib` en 11 tamaños que cruzan
  bordes de bloque (0, 1, 55, 56, 63, 64, 65, 127, 128, 1 MiB+7, 4 MiB+3).
- `runtime/core/axon.c:47` — streaming con buffer acotado de 1 MiB (fallback a
  pila de 8 KiB si no hay memoria); nunca se carga el archivo entero.
- `runtime/core/hash_cache.c` + `hash_cache.h` (nuevos) — caché de digest por
  ruta + tamaño + mtime en `~/.synapse/cache/hash/`, escritura atómica
  (`.tmp` + `rename`), `SYNAPSE_HASH_CACHE=0` la desactiva, archivos con mtime
  < 5 s no se cachean, y cualquier diferencia de tamaño/mtime invalida la
  entrada. Nunca devuelve un digest que este runtime no haya calculado.
- `runtime/core/modelo.c:988` — `_syn_hash_archivo` consulta la caché y solo
  guarda el digest si el hasheo terminó (64 hex); `_syn_tamano_archivo` añade la
  variante con ABI `CadenaSegura` (la nativa recibe `const char*`; invocarla
  desde Synapse repetía el ABI mismatch de R197 y devolvía -1).

**Medición (máquina de trabajo, GGUF 873.582.624 B):**

| escenario | antes | después |
|---|---|---|
| hashing del GGUF (sonda `_syn_ahora_ms`) | 9.000 ms | 6.000 ms (138 MB/s) |
| corrida completa del instalador, caché fría | 10,3 s | 6,5 s |
| corrida completa del instalador, caché caliente | 10,3 s | 0,07 s |
| `tests/opensyn/test_installer.py` (timeout 10 s) | fallaba | **PASSED** |

Desglose de la medición original (sonda temporal con `_syn_ahora_ms`, en `logs/`): hardware 0 ms,
`_syn_existe_archivo` 0 ms, **hash 9.000 ms**, resto 0 ms → el coste era la
verificación, no la detección de hardware ni la configuración.

## 2. Manual 9 §6.1 CUMPLE (con límite declarado) — instalador en sistemas limpios

El instalador informa el coste real en vez de aparentar un cuelgue:

```
Verificando integridad (SHA-256) de 833 MB...
Verificacion SHA-256: 6000 ms (138 MB/s)
Modelo ya descargado y verificado
```

y con el digest ya cacheado:

```
Verificando integridad (SHA-256) de 833 MB...
Verificacion SHA-256: 0 ms (desde cache de digest)
Modelo ya descargado y verificado
```

`tests/opensyn/test_installer.py` (inmutable, sin cambios) pasa en 9,76 s
incluyendo la compilación previa del `.exe`.

**Límite declarado:** la matriz de instalación limpia en Windows/Linux/macOS es
el ME `r276_multiplataforma_release`; aquí solo se certifica el caso local
medido. En una máquina que nunca verificó el modelo la primera corrida cuesta
~6,5 s (dentro del timeout de 10 s) y las siguientes ~0,07 s.

## 3. Manual 7 §6.1 CUMPLE — instalación de un solo clic

`opensyn/installer.syn:148` — `verificar_hash` mantiene el flujo de un solo clic
(hardware → modelo → descarga/verificación → configuración) y emite el aviso
`Verificando integridad (SHA-256) de N MB...` antes de hashear, con `fflush`
desde `_syn_hash_archivo` para que el mensaje salga a pantalla de inmediato
(`runtime/core/modelo.c`), más el tiempo medido al terminar.

## 4. Manual 9 §5.5 — prueba de humo (fuera del alcance de este ME)

La prueba de humo de inferencia (`prueba_inferencia`, §5.5) requiere
`llama-server` en ejecución y es el objeto del ME `r275_opensyn_e2e_bench`. El
plan r273 no la modifica y ningún ancla del expediente la declara.

## Oráculos ejecutados

```
pytest tests/integration/test_installer_modelo_grande.py -v   → 17 passed
pytest tests/opensyn/test_installer.py -v                     → 1 passed (9,76 s)
pytest tests/unit/test_axon_crypto.py tests/integration/test_axon_e2e.py → 11 passed
pytest tests/axon -q                                          → 9 passed
python auditoria/contrastar.py --plan docs/plan_ME_r273_installer_modelo_grande.md → OK
python auditoria/alineacion.py --verificar --me r273_installer_modelo_grande → OK (6 archivos)
python auditoria/verificar_alineacion.py                      → SIN BRECHAS
```

## Riesgo residual

Un archivo que cambie de contenido conservando tamaño **y** mtime reutiliza la
entrada cacheada. Es el compromiso que fija el plan (ruta + tamaño + mtime); se
mitiga no cachear archivos recién escritos (< 5 s) y queda cubierto por
`test_cache_guarda_y_reutiliza_digest`, que documenta la semántica esperada.
