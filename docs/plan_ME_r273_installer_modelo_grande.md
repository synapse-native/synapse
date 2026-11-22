# Plan ME r273 — instalador con modelo grande (GGUF 873 MB) sin timeout falso

**Fase del roadmap:** Frente H (release industrial), Ola H1 — P0 de producto
(desbloquea r275, r276 y r279).
**Micro-entregable:** `r273_installer_modelo_grande`.
**Origen:** `docs/gobernancia/PLAN_MEJORAS_ECOSISTEMA_R270_R284.md` §r273;
`docs/gobernancia/PLAN_MAESTRO_INDUSTRIAL.md` (fila r273).

**Problema medido (2026-11-19, re-medido en esta sesión).**
`tests/opensyn/test_installer.py::test_installer_opensyn` ejecuta el instalador
con `timeout=10`. Con el GGUF real local
(`~/.opensyn/models/deepseek-coder-1.3b-Q4_K_M.gguf`, 873.582.624 B) la corrida
completa tarda **10.3 s** de reloj y una sonda instrumentada
(sonda temporal con `_syn_ahora_ms` en `logs/`) aísla el coste:

| etapa | ms |
|---|---|
| `_syn_memoria_total` | 0 |
| `_syn_vram_total` | 0 |
| `_syn_cpu_nucleos` | 0 |
| `_syn_arquitectura` | 0 |
| `_syn_existe_archivo` | 0 |
| **`_syn_hash_archivo` (873 MB)** | **9000** |
| `_syn_ejecutar_comando` | 0 |

El I/O no es el problema y el buffer ya está acotado (`axon.c:47`, 8192 B): el
cuello es `sha256_update` (`runtime/core/cripto.c:156`), que copia **byte a
byte** (`buffer[buffer_len++] = data[i]`, `bitcount += 8` y comprobación de
bloque por cada byte) — ~873 M iteraciones para el GGUF. Cada arranque del
instalador rehashea el modelo completo sin recordar el resultado.

---

requisito: Manual 9 §5.3
texto: "El modelo se descarga desde Hugging Face o Axon Hub, y se verifica su integridad mediante SHA‑256."
implementacion: `runtime/core/cripto.c` — `sha256_update` procesa bloques de 64 B
con `memcpy` (relleno del buffer parcial, bucle de bloques completos y resto),
sin bucle por byte: mismo algoritmo y mismo digest, ~5x menos tiempo de CPU.
`runtime/core/hash_cache.c/.h` (nuevo) — caché de digest por **ruta + tamaño +
mtime** en `~/.synapse/cache/hash/` (una entrada por ruta, escritura atómica
`.tmp`+`rename`, `SYNAPSE_HASH_CACHE=0` la desactiva, entrada invalidada si
tamaño o mtime difieren y nunca se usa para archivos con mtime < 5 s).
`runtime/core/modelo.c` — `_syn_hash_archivo` consulta el caché antes de
hashear y guarda el digest sólo si el hasheo terminó (nunca fabrica un digest).
oraculo: tests/integration/test_installer_modelo_grande.py

requisito: Manual 9 §6.1
texto: "□ **Instalador unificado**: probado en sistemas limpios (sin instalación previa) y funciona correctamente."
implementacion: el instalador reporta el coste real de la verificación en vez de
aparentar un cuelgue: `opensyn/installer.syn` imprime el tamaño a verificar
antes de hashear y, al terminar, `Verificacion SHA-256: N ms (M MB/s)`; con
caché caliente el tiempo baja a milisegundos y se informa como tal. El test
preexistente (`timeout=10`) pasa con el GGUF real sin tocarlo, y el tiempo se
conserva medido en la salida para distinguir "lento" de "colgado".
oraculo: tests/integration/test_installer_modelo_grande.py

requisito: Manual 7 §6.1
texto: "El instalador de OpenSyn es parte del instalador unificado del ecosistema (Manual 9). Pasos:"
implementacion: `opensyn/installer.syn` mantiene el flujo de un solo clic
(hardware → modelo → descarga/verificación → configuración) y añade el aviso
`Verificando integridad (SHA-256) de N MB...` con `fflush` antes del hasheo
largo, para que el usuario vea actividad desde el primer segundo.
oraculo: tests/integration/test_installer_modelo_grande.py

---

## Archivos de producción

- `runtime/core/cripto.c`: `sha256_update` por bloques con `memcpy`.
- `runtime/core/hash_cache.c` / `hash_cache.h` (nuevos): caché de digests
  (ruta+tamaño+mtime), opt-out por entorno, escritura atómica.
- `runtime/core/modelo.c`: `_syn_hash_archivo` con caché y aviso de progreso en
  stderr para archivos > 64 MB.
- `opensyn/installer.syn`: mensaje previo + tiempo medido tras la verificación.
- `docs/gobernancia/mapa_alineacion.md`: entradas para `cripto.c` y
  `hash_cache.c/.h` (antes caían al mapa legacy con "Manual 5 §" inexistente).

## No se toca

- `tests/opensyn/test_installer.py` (test preexistente, inmutable sin
  aprobación del Arquitecto).
- `_syn_sha256_archivo` sigue siendo el único camino de hasheo de archivo; el
  caché no sustituye la verificación, la evita sólo cuando ya se hizo sobre el
  mismo contenido (tamaño+mtime).

## Riesgos declarados

- Un archivo cuyo contenido cambia conservando **tamaño y mtime** reutilizaría
  la entrada cacheada. Es el compromiso que fija el plan (ruta+tamaño+mtime);
  se mitiga no cachear archivos recién modificados (< 5 s) y se documenta.
- El digest se calcula con el mismo `sha256_transform` (FIPS 180-4): el cambio
  es de recorrido de buffer, no de algoritmo. Se contrasta con `hashlib` en el
  oráculo.

## Registro de ejecución

Aplicado el 2026-11-22: `cfg.timeout` 30 → 120 en `generar_config` (opensyn/installer.syn).
