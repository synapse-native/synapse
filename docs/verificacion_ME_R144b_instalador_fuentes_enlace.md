# Verificación ME — R144b instalador: fuentes de enlace + hash reales + extracción completa

Plan: `docs/plan_ME_R144b_instalador_fuentes_enlace.md` (bloques 1-5)
Código: `instaladores/windows/synapse.iss`, `scripts/update_hashes.ps1`
Fecha: 2026-09-07 · Máquina de test: D:\SynapseTest (5 reinstalaciones v1→v6b)

## Manual 9 §2.5 — componente synapse autosuficiente (CUMPLE)

Bloques 1-3 (fuentes/headers de enlace del compilador nativo: synapse_rt.c/.h,
synapse_rt_memory.h, axon/, vendor/sqlite3/, nucleo/federated.*, librerias/):
el `synapse.exe` instalado compila programas de usuario desde cwd neutral.
Oráculo e2e: `D:\SynapseTest> bin\synapse.exe humo.syn salida.exe` →
"[Synapse] Compilacion nativa exitosa" (1,987,167 B) → ejecutado:
`Instalacion Synapse 8.1.0 OK` / `2+3 = 5`, rc=0. Antes del fix el enlazador
invocaba GCC con rutas inexistentes en el dir de instalación (bloqueante R144).

## Manual 9 §5.3 — descarga + verificación SHA256 (CUMPLE)

Bloque 4 (hash reales):
- `LLAMA_SERVER_SHA256` = hash del EXE extraído de b10819 (no del ZIP): log v6b
  `llama-server.exe SHA256 verificado correctamente` (antes: mismatch 100%).
- `MODEL_SHA256_*` reales (LFS oid HF): log v5c/v6b
  `Descargas completadas OK: D:\SynapseTest\opensyn\models\deepseek-coder-1.3b-Q4_K_M.gguf`
  (873,582,624 B, descargado 2 veces, tamaño idéntico).
- `MODEL_URL_1B` corregido a `deepseek-coder-1.3b-instruct-GGUF` (el repo con
  `1.3B` daba 401; el modo silencioso sin Ollama elige siempre el 1B).
- `DownloadFile` con curl `--fail --connect-timeout 30` (reproducido: GitHub 504
  guardado como "ZIP" de 92 B con exit 0).

Bloque 5 (extracción completa): log v6b
`llama-server.exe + DLLs extraidos correctamente a: D:\SynapseTest\opensyn\ia (51 archivos)`.
Oráculo e2e del stack IA instalado:
- `ia\llama-server.exe --version` → `version: 0.4.0-dev (build 10819)` (antes
  moría por falta de llama-server-impl.dll).
- Serve con el modelo instalado → `/health` `{"status":"ok"}` y completion real
  vía `/v1/chat/completions` (fingerprint `b10819-6a1a922d2`).

## Oráculos complementarios (exes instalados, cwd neutral)

- Banner (R141): OK (bloques ████ al arrancar, pipe mode).
- Historial + navegación ↑↓ (R142): `tests/e2e_oracle_opensyn_historial.py`
  corrido contra `D:\SynapseTest\bin\opensyn.exe` → OK (4 tests).
- Autocompletado Tab (R142): `tests/e2e_oracle_opensyn_autocomplete.py` contra
  el exe instalado → OK (comandos + rutas + menú doble Tab).
- Motor GGUF (R143): `tests/e2e_oracle_opensyn_ia_gguf.py` → OK (carga + vocab +
  ingesta + generación determinista + cierre limpio).
- PATH H-F30b-3: 5 instalaciones sucesivas → exactamente 1 entrada por hive
  (sin duplicados).
- Gates: `verificar_alineacion.py` SIN BRECHAS; `contrastar.py --plan` OK;
  `tests/validate_installer.py` VALIDACION EXITOSA.

## Hallazgos con resolución

| ID | Hallazgo | Resolución |
|----|----------|------------|
| H-R144-1 | Extracción copiaba solo el launcher sin sus DLLs (51 archivos del ZIP) | RESUELTA (bloque 5; validada en v6b) |
| H-R144-2 | VRAM/RAM/CPU detectan -1 en contexto elevado → siempre elige modelo 1B (conservador) | REGISTRADA — mejora futura (logging de detección + fallback WMI alternativo) |
| H-R144-3 | `opensyn/modelos.toml` distribuido contiene URLs/hash placeholder (`abc123...`) — catálogo runtime con datos falsos | REGISTRADA — requiere regeneración de modelos.toml con datos reales (ME futuro, afecta gestión de modelos desde OpenSyn, no al instalador) |
| H-R144-4 | La variable `/LANG` la mangleaba MSYS Git Bash en los tests (artefacto de entorno, no del instalador); el diálogo de idioma se muestra en VERYSILENT si no se pasa /LANG (comportamiento Inno documentado) | DOCUMENTADA |
| H-R144-5 | Upgrade silencioso con GGUF existente salta la provisión de llama-server (bloque `if not UseExisting`) | REGISTRADA — caso borde: crash previo sin modelo ni llama-server; ME futuro |

## Limpieza del sistema de test

- Carpeta stale `C:\TestSynapseInstall` (exes rotos del 4-6 Sep que sombreaban
  el PATH, previos a esta sesión) eliminada con consentimiento del usuario.
- Entradas PATH muertas (`C:\Program Files\Synapse\bin`,
  `C:\TestSynapseInstall\bin`) eliminadas de HKLM y HKCU. Estado final: única
  entrada Synapse = `D:\SynapseTest\bin` en ambas colas.
- Instalación D:\SynapseTest conservada (validada funcional).
