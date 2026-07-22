# Axon: Especificación del Gestor de Paquetes v2.0

> **Documento:** `AXON_SPEC.md`
> **Versión:** 2.0 — PRODUCTION-READY
> **Última actualización:** 22 Julio 2026

---

## 1. Visión General

Axon es el gestor de paquetes nativo de Synapse. Opera bajo un modelo
**descentralizado, criptográficamente verificado y sin ejecución de scripts**.

**Principios de diseño:**
1. **Inmutabilidad** — Los paquetes nunca se modifican in-situ
2. **Verificación obligatoria** — Toda descarga requiere firma Ed25519
3. **Sin pre/post-instalación** — No se ejecutan scripts arbitrarios
4. **Offline-first** — Resolución local antes que descarga remota
5. **Reproducibilidad** — `axon.lock` garantiza builds deterministas

---

## 2. Manifiesto (`axon.toml`)

### 2.1 Formato Canónico

```toml
[paquete]
nombre = "mi-libreria"
version = "1.2.3"
autor = "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
tipo = "libreria"
punto_entrada = "lib.syn"

[dependencias]
synapse-std = { version = "^0.2.0" }
synapse-net = { version = "~1.0.0" }
```

### 2.2 Campos

| Clave | Requerido | Tipo | Descripción |
|-------|-----------|------|-------------|
| `[paquete].nombre` | ✅ | `texto` | Nombre único del paquete |
| `[paquete].version` | ✅ | `texto` | Versión SemVer (ej: `1.2.3`) |
| `[paquete].autor` | ✅ | `texto` | Clave pública Ed25519 (64 hex chars) |
| `[paquete].tipo` | ✅ | `texto` | `"libreria"` o `"ejecutable"` |
| `[paquete].punto_entrada` | ✅ | `texto` | Archivo `.syn` principal |
| `[dependencias].<nombre>` | ❌ | `tabla` | Dependencia con restricción de versión |

### 2.3 Restricciones de Versión (SemVer)

| Formato | Significado | Ejemplo: `1.2.3` |
|---------|-------------|------------------|
| `"1.2.3"` | Versión exacta | Solo `1.2.3` |
| `"^1.2.3"` | Compatible (`>=1.2.3`, `<2.0.0`) | `1.2.3`–`1.9.9` |
| `"^0.2.3"` | Compatible en 0.x (`>=0.2.3`, `<0.3.0`) | `0.2.3`–`0.2.9` |
| `"^0.0.3"` | Compatible en 0.0.x (`==0.0.3`) | Solo `0.0.3` |
| `"~1.2.3"` | Parche (`>=1.2.3`, `<1.3.0`) | `1.2.3`–`1.2.9` |

---

## 3. Comandos

### 3.1 `axon init`

Inicializa el ecosistema local:

```bash
synapse.exe axon init
```

Crea `axon.toml` con valores por defecto si no existe.

### 3.2 `axon fetch`

Descarga e instala dependencias:

```bash
synapse.exe axon fetch              # Solo resolución local
synapse.exe axon fetch --online     # Descarga desde HTTP
```

**Pipeline de fetch:**
```
1. Leer axon.toml
2. Validar [paquete].autor (≥64 hex chars)
3. Buscar localmente (paquetes_oficiales/ + .axon_cache/)
4. Si no encontrado y --online: descargar vía HTTP
5. Buscar archivo .sig (múltiples ubicaciones)
6. Si autor definido y .sig no encontrado → ERR_AXON_COMPROMISED
7. Verificar firma Ed25519
8. Si firma inválida → purgar temporales + ERR_AXON_COMPROMISED
9. Verificar axon.lock (SHA-256)
10. Extraer TAR
11. Escribir axon.lock
```

---

## 4. Criptografía (Ed25519)

### 4.1 Algoritmo

Axon usa **Ed25519** (Curve25519) implementado via TweetNaCl para firmas digitales.

- **Clave pública:** 32 bytes (64 caracteres hex)
- **Firma:** 64 bytes
- **Hash del mensaje:** SHA-256

### 4.2 Formato de Firma (.sig)

El archivo `.sig` contiene exactamente **64 bytes binarios** de la firma Ed25519,
sin cabeceras ni metadatos.

### 4.3 Verificación

```c
int _syn_ed25519_verificar(CadenaSegura mensaje, CadenaSegura firma, CadenaSegura clave_publica);
// Retorna: 0 = firma válida, -1 = inválida
```

### 4.4 Tolerancia Cero

| Condición | Resultado |
|-----------|-----------|
| `autor` vacío o < 64 hex chars | `ERR_AXON_COMPROMISED` inmediato |
| `.sig` no encontrado | `ERR_AXON_COMPROMISED` (aborto, no warning) |
| Firma Ed25519 no coincide | `ERR_AXON_COMPROMISED` + purge de temporales |
| Hash SHA-256 del TAR no coincide con lock | `ERR_AXON_COMPROMISED` |

---

## 5. Lockfile (`axon.lock`)

### 5.1 Formato

```toml
[lock]
"mi-libreria" = { version = "1.2.3", hash = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" }
```

### 5.2 Propósito

- **Determinismo:** Mismo TAR → mismo SHA-256 → mismo lock
- **Integridad:** Si el TAR se modifica post-instalación, el hash no coincide
- **Reproducibilidad:** `axon.lock` se versiona en el repositorio

### 5.3 Verificación

```c
int _syn_axon_verificar_lock(const char* paquete, const char* version,
                             const char* archivo_ruta, const char* lock_ruta);
// Retorna: 0 = hash coincide, -1 = ERR_AXON_COMPROMISED
```

### 5.4 Escritura

```c
int _syn_axon_escribir_lock(const char* paquete, const char* version,
                            const char* hash_sha256);
// Añade entrada a axon.lock en formato TOML
```

---

## 6. Resolución Local

### 6.1 Rutas de Búsqueda

```
paquetes_oficiales/<nombre>/<version>.tar   → exacto
paquetes_oficiales/<nombre>/<version>.tar.sig
paquetes_oficiales/<nombre>/               → escanea con SemVer
  └── *.tar                                → elige mejor match
.axon_cache/<nombre>.tar                   → caché de descarga
```

### 6.2 Algoritmo de Búsqueda

```c
int _syn_axon_buscar_local(const char* nombre, const char* version,
                           char* tar_path, int tar_path_max,
                           char* extract_dir, int extract_dir_max);
// 1. Construir ruta exacta: paquetes_oficiales/<nombre>/<version>.tar
// 2. Si existe → OK
// 3. Si no → escanear paquetes_oficiales/<nombre>/ con _syn_semver_match()
// 4. Elegir la versión más alta que cumpla la restricción
// 5. Si no hay match → buscar en .axon_cache/
```

---

## 7. Descarga HTTP

### 7.1 Especificación

```c
int _syn_http_get_archivo(const char* url, const char* salida_ruta);
// HTTP/1.0 GET sobre socket TCP (puerto 80)
// Sin TLS (entorno simulado / red local)
// Retorna: 0 = éxito, -1 = error
```

### 7.2 Cache

Los archivos descargados se almacenan en `.axon_cache/<nombre>.tar`.

---

## 8. Extracción TAR

### 8.1 Especificación

```c
int _syn_tar_extraer(const char* tar_ruta, const char* salida_dir);
// Parseo de cabeceras POSIX (512 bytes)
// Soporta: tipo '0' (archivo regular), tipo '5' (directorio)
// Combina prefix + name para rutas largas
```

### 8.2 Path Traversal Protection

```c
// Bloquea:
//   - "../etc/passwd"      (escape de directorio)
//   - "/etc/shadow"         (ruta absoluta)
//   - "archivo/../../../tmp" (recursivo)
// Permite:
//   - "lib.syn"
//   - "subdir/archivo.txt"
```

---

## 9. E2E Test Suite

### 9.1 Suite Nativa (C)

**Compilación:**
```bash
gcc -I. -o tests/test_axon_e2e_native.exe tests/test_axon_e2e_native.c axon_rt.c tweetnacl.c -lm -lpthread -lws2_32
```

**Escenarios (8 tests, 19 subtests):**
| Escenario | Subtests | Propósito |
|-----------|----------|-----------|
| 1. Ed25519 crypto | 4 | RFC 8032 vector, firma corrupta, clave errónea, mensaje erróneo |
| 2. File I/O (.sig) | 4 | Firma válida, corrupta, hex inválido, .sig ausente |
| 3. Path traversal | 3 | Archivo normal, ../ bloqueado, ruta absoluta bloqueada |
| 4. axon.lock | 5 | SHA-256 generado, determinismo, hash diferente, escritura, contenido |
| 5. Verificar lock | 2 | Hash coincide, hash mismatch |
| 6. SemVer | 18 | Exacto, ^, ~, edge cases (NULL) |
| 7. TOML parsing | 8 | Secciones, campos, dependencias, versiones |
| 8. Zero-tolerance | 3 | Autor vacío, autor corto, .sig ausente |

### 9.2 Suite Python (Orquestador)

```bash
python tests/test_axon_e2e.py
```

**Resultado:** 19/19 tests pasan ✅

---

## 10. Códigos de Error

| Código | Constante | Descripción |
|--------|-----------|-------------|
| -1 | `ERR_AXON_NOT_FOUND` | Paquete no encontrado |
| -2 | `ERR_AXON_COMPROMISED` | Firma inválida, lock mismatch, o autor vacío |
| -3 | `ERR_AXON_NETWORK` | Error de red/HTTP |
| -4 | `ERR_AXON_EXTRACT` | Error de extracción TAR |
| -5 | `ERR_AXON_MANIFEST` | `axon.toml` mal formado |
| -6 | `ERR_AXON_VERSION` | Versión SemVer no satisface restricción |

---

## 11. Tamaños del Runtime

| Componente | Archivo | Tamaño (.o) |
|-----------|---------|-------------|
| Runtime base | `synapse_rt.o` | 98 KB |
| Axon | `axon_rt.o` | 10 KB |
| TweetNaCl | `tweetnacl.o` | 35 KB |
| **Total runtime** | — | **< 139 KB** (< 500 KB ✅) |
