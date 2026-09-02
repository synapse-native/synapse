# Reporte de Auditoría de Desviaciones — Synapse/Syquex/OpenSyn

**Alcance:** Código de producción (no asserts de tests). Se auditan: `compilador/`, `pipeline.py`, `runtime/core/*`, `nucleo/*.c`, `nucleo/*.syn`, `syquex/`, `lib/`, `std/`, `opensyn/` (parcial), `axon/` (`runtime/core/axon.c`).

**Método:** Para cada área se leyó la sección del manual (`docs/manuales/MANUAL 1-9.md`) y luego el código correspondiente. Solo se reportan desviaciones de comportamiento verificables frente al texto literal del manual; se ignoran estilo/formato. No se modificó ningún archivo.

**Cobertura honesta:** Subconjunto de alto valor. No se ejecutó el bootstrap completo (M1 §6 requiere build >30s; auditoría de solo lectura). Véase "ÁREAS NO AUDITADAS EN PROFUNDIDAD" al final.

---

## CRÍTICA

_(Sin hallazgos de nivel crítico confirmados. Las dos desviaciones de seguridad/correctitud de mayor impacto se listan en ALTA.)_

---

## ALTA

### A1 — Nonce del handshake generado con PRNG débil (no CSPRNG)
- **`runtime/core/cluster.c:415`** — `Manual 6 §5.3 infringido`.
- Manual (literal): *"El cliente envía un mensaje `HELLO` con su clave pública y una firma de un **nonce aleatorio de 32 bytes**."* / *"Handshake Ed25519 (Zero-Trust)"*.
- Desviación: `cluster_generar_nonce()` rellena los 32 bytes con `raw[i] = (unsigned char)(rand() % 256);` — `rand()` es un PRNG no criptográfico y, sin semilla explícita visible, potencialmente predecible. En un protocolo "zero-trust" el nonce debe ser CSPRNG. Nótese que el tráfico de sesión SÍ usa CSPRNG (`randombytes(n, 24)` en `cluster.c:164`), lo que evidencia la inconsistencia.
- Corrección: usar `randombytes(raw, 32)` (ya definido en `runtime/core/cripto.c:33`, que usa `CryptGenRandom`/`getrandom`/`/dev/urandom`) en lugar de `rand()`.

### A2 — Detección de VRAM en Windows lee un "score" de WEI, no VRAM
- **`nucleo/detect_hardware.c:49-53`** — `Manual 9 §5.7 infringido`.
- Manual (literal): *"§5.7 (detección de hardware RAM/VRAM/CPU)"* — el asistente *"detecta automáticamente los recursos de hardware (RAM, VRAM, CPU) y selecciona el modelo codec más adecuado"* (Manual 1 §1.1).
- Desviación: en Windows lee `HKLM\...\WinSAT\GraphicsScore` y hace `perfil->vram_gb = vram_mb * 0.001`. `GraphicsScore` es la puntuación del Windows Experience Index (rango ~1.0–9.9), **no** memoria de vídeo en MB. El valor resultante (p.ej. 8.0 → 0.008 GB) es fisiológicamente incorrecto y, al ser <0.1, cae al fallback `GetDeviceCaps(hdc,120)` (índice 120 no es un índice `GetDeviceCaps` documentado → suele devolver 0). Resultado: VRAM mal detectada → selección de modelo codec errónea en OpenSyn.
- Corrección: usar `IDXGIAdapter::GetDesc().DedicatedVideoMemory` (o `DXGI`/`Windows.Devices.Enumeration`) para VRAM real; no usar `WinSAT\GraphicsScore`.

---

## MEDIA

### M1 — Formato de wire del mensaje HELLO diverge de la especificación binaria
- **`runtime/core/cluster.c:406-438, 486-528`** — `Manual 6 §5.3 infringido`.
- Manual (literal): *"Estructura del mensaje HELLO: `[nonce (32 bytes)] [clave_publica (32 bytes)] [firma (64 bytes)]`"*.
- Desviación: la implementación usa un formato textual colon-delimitado `HELLO:<id>:<nonce_hex>:<pubkey_hex>:<firma_hex>` (hex, con un campo `id` adicional no especificado y sin el layout binario `[32][32][64]`). Aunque el flujo (HELLO → HELLO_RESP → DATOS_CIFRADOS) es coherente, el formato en el cable no coincide con la estructura normativa del manual.
- Corrección: documentar el formato real como normativo en el manual, o emitir/parsear el layout binario `[32][32][64]` (más `id` si se justifica).

### M2 — La regla citada "Manual 2 §12: toda función pública nueva lleva contratos; error si no" NO EXISTE en el manual
- **Citación del auditor vs `docs/manuales/MANUAL 2.md`** — aclaración de cobertura.
- Manual: `Manual 2 §12` es **"PRUEBAS OBLIGATORIAS PARA ESTA ETAPA"** (tabla de tests). La regla "toda función pública nueva lleva contratos requiere/garantiza; error si no" **no aparece en ninguna sección de los manuales 1-9** (verificado por búsqueda). Los contratos son gramaticalmente opcionales (EBNF en `Manual 2 §5`: `contratos ::= [ bloque_requiere ] [ bloque_garantiza ]`).
- Consecuencia: no se puede afirmar una "desviación de código" de una regla inexistente. El compilador (`compilador/generator/emit_contracts.py`) emite contratos cuando están presentes, pero no obliga su presencia. Si el Arquitecto desea hacerla obligatoria, debe primero incorporarse al manual.
- Acción: aclarar con el Arquitecto; no marcar como desviación de código.

### M3 — Instalador multi-target incompleto (falta macOS/.dmg y Makefile/build.py raíz)
- **`instalador_synapse.iss`, `scripts/install.sh`** — `Manual 9 §9 infringido` (parcial).
- Manual (literal): *"§9 (instalador multi-target: .iss/.sh/.dmg, Makefile/build.py, distribución)"*.
- Desviación: solo se encuentran `instalador_synapse.iss` (Windows/InnoSetup) y `scripts/install.sh` (Linux). No existe `.dmg` (macOS) ni `Makefile`/`build.py` en la raíz del repo (los encontrados están bajo `toolchain_gcc12/`).
- Corrección: añadir target macOS (`.dmg`/pkg) y un `Makefile`/`build.py` orquestador en la raíz, o ajustar el manual para reflejar los targets reales soportados.

### M4 — Extracción TAR de Axon no cubre typeflags de symlink/long-name (escape potencial)
- **`runtime/core/axon.c:220-247`** — `Manual 6 §6.1 infringido` (parcial).
- Manual (literal): *"§6.1 (path traversal protection en extracción TAR)"*.
- Desviación: el chequeo de path traversal (líneas 159-191) rechaza `/` inicial y componentes `..`, pero la rutina solo maneja `typeflag` '0'/'\0' (fichero) y '5' (dir). No procesa `typeflag` 'L'/'K' (GNU long name/link, 75% de la superficie de ataque de path traversal en TAR) ni symlinks ('1'/'2'), que podrían escribir fuera de `salida_dir`.
- Corrección: rechazar o normalizar typeflags 'L'/'K'/'1'/'2', o validar la ruta final resultante contra `salida_dir` con `realpath` tras ensamblar.

---

## BAJA

### B1 — Línea de `#include` con comentario pegado (cosmético)
- **`runtime/core/cripto.c:86`** — `Manual 1 §7.1 infringido` (estilo, no comportamiento).
- `#include "axon/tweetnacl.h"// --- SHA-256 (sin cambios) ---`. C válido (el `//` comenta), pero es confuso y contradice el estándar de comentarios limpios del manual §7.1.
- Corrección: separar en dos líneas.

### B2 — Derivación de clave de sesión usa SHA-256 de X25519 en vez de `crypto_kx` (CUMPLE por excepción)
- **`runtime/core/cluster.c:267-272`** — `Manual 6 §5.3` (INFO, no desviación).
- El manual dice *"Se deriva una clave de sesión (usando `crypto_kx` de libsodium o similar)"*. La implementación construye un `crypto_kx`-equivalente solo con primitivas TweetNaCl (`crypto_scalarmult` + SHA-256), invocando explícitamente "o similar" y la regla 8 (cero dependencias). Se considera conforme.

---

## Verificaciones conformes (no desviaciones)
- **M1 §1.1 (`--check`):** `pipeline.py:673-675` retorna tras análisis semántico sin generar código C/IR/WAT — cumple "validación rápida sin generar código".
- **M1 §3.1 / §7.1 (determinismo alfabético):** `compilador/generator/generator.py` emite funciones/stubs con `sorted(...)` (líneas 329, 363, 1216) — cumple orden alfabético.
- **M6 §5.3 (AEAD por mensaje en tráfico de sesión):** `cluster.c:164-187` usa `randombytes` + `crypto_secretbox` con nonce de 24 B por mensaje y layout `[nonce24][mac16][ct]` — cumple.
- **M8 (LSP):** `nucleo/lsp.syn` implementa framing `Content-Length:` + JSON-RPC 2.0 — cumple.
- **M8 (debugger time-travel):** `runtime/core/debug.c:334` emite cabecera `TRACE v1` — cumple.
- **M9 §4 (firma Ed25519 de release):** `runtime/core/axon.c:341-386` + `runtime/core/cripto.c:63-82` verifican firma Ed25519 del paquete — cumple.

---

## ÁREAS NO AUDITADAS EN PROFUNDIDAD
- **Manual 3 (Syquex) EBNF completa (§3), type rules (§5), FFI (§9), mapping (§11):** se verificó que `syquex/lexer.syn` (`T_INTERROGACION` línea 74, `T_EXTERNO` línea 48), `syquex/parser.syn` y `syquex/traductor.syn` (referencia M3 §11.1/§11.2 y propagación `?` en línea 741) existen y citan el manual, pero **no** se hizo una conformidad exhaustiva token-por-token de la gramática ni de las reglas de tipos `Resultado`/`Opcion`.
- **Manual 2 §5 (semántica runtime de contratos):** `emit_contracts.py` existe y emite `requiere`/`garantiza`; no se verificó exhaustivamente que `garantiza` se evalúe antes de cada `retornar` con `_resultado_` (Manual 2 §5, líneas 300-301).
- **Manual 7 (sandbox/seccomp):** no inspeccionado.
- **Manual 5 (cluster topología/mensajes) fuera del handshake:** solo se revisó la porción cripto del handshake.
- **Manual 4:** no auditado.
- **`opensyn/` comportamiento de producción (transpiler, bindings_generator):** revisión superficial.
- **Manual 1 §6 (determinismo bootstrap etapas 0→1→2→3, diff binario 0 / SHA-256):** requiere ejecutar el build completo; no ejecutado en esta auditoría de solo lectura.
- **Cero telemetría (Manual 1 §7.3):** no se rastreó exhaustivamente cada conexión de red de OpenSyn; las verificadas apuntan a `127.0.0.1`/local.
