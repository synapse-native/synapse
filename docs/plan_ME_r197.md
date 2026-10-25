# Plan ME r197 — instalador OpenSyn verificado EJECUTANDO como usuario (M9 §5.2-§5.4, M7 §2.5)

**Base:** c3d1a4c (R196 docs). **Cierre de hallazgos de operación como usuario real
(2026-10-25):** el instalador compilaba rc=0 pero fallaba EN EJECUCIÓN con el
modelo correcto — rc=0 ≠ funciona (lección H-R182c-1 aplicada al instalador).

## R1 — hash de archivo con ABI CadenaSegura (hash vacío → "checksum incorrecto")

requisito: Manual 9 §5.3 — "El modelo se descarga desde Hugging Face o Axon
Hub, y se verifica su integridad mediante SHA-256."
texto: R269 en EJECUCIÓN real 2026-10-25: el binding externo del compilador
pasa CadenaSegura (struct por valor) y la implementación nativa
_syn_sha256_archivo (runtime/core/axon.c) recibe const char* — el callee leyó
`longitud` como puntero, fopen falló y el hash salió VACÍO: el instalador
reportó "Error: checksum incorrecto" con el archivo CORRECTO (vs
X-Linked-ETag de HF verificado con curl). Fix: wrapper _syn_hash_archivo
(CadenaSegura) en runtime/core/modelo.c con el patrón de
_syn_existe_archivo/_syn_eliminar_archivo; callers nativos de axon.c/axon_rt.c
no cambian.
implementacion: runtime/core/modelo.c wrapper _syn_hash_archivo
// cumple Manual 9 §5.3; opensyn/installer.syn externos re-anclados a
_syn_hash_archivo // cumple Manual 9 §5.3
oraculo: auditoria/oraculos/oraculo_r197_instalador.py — E2E real:
installer.exe RC=0 imprime "Modelo ya descargado y verificado" con el
gguf de 873 MB en ~/.opensyn/models (hash correcto ≠ vacío); A4b wrapper
declarado; A2b ningúno caller usa la nativa const char*.

## R2 — descarga TLS con redirecciones vía curl del sistema

requirements: Manual 9 §5.3 (misma cita R1) + Manual 7 §2.5 — "Detecta
hardware, selecciona y descarga el modelo apropiado."
texto: _syn_descargar (runtime/core/axon.c) es HTTP/1.0 plano sin TLS ni
redirecciones: a huggingface.co respondió 30x HTML ~1 KB y el checksum falló
con el archivo correcto (hallazgo de usuario 2026-10-25). Además curl(23)
"ERROR on write" sin --create-dirs si ~/.opensyn/models no existe. Fix:
descargar_url() usa _syn_ejecutar_comando con curl del sistema
(-L -fsS --create-dirs) — M9 §5.4 lo declara el camino descendente.
implementacion: opensyn/installer.syn descargar_url (curl -L -fsS
--create-dirs) // cumple Manual 9 §5.3; descargar_modelo/principal lo consumen
// cumple Manual 9 §5.4
oraculo: auditoria/oraculos/oraculo_r197_instalador.py — A2 el comando curl
exige -L/-fsS/--create-dirs; A4a sin externos `-> logico` (firmas entero
r194, installs previos MIPS fallaban con conflicting types, exe stale).

## R3 — configuración de llama-server escrita por el instalador

requisito: Manual 9 §5.4 — "El instalador configura `llama-server` con los
parámetros óptimos:" (tabla n_ctx/n_threads/n_gpu_layers/puerto/host/timeout
del mapa M9 §5.2 seleccionada por VRAM/núcleos).
texto: generar_config + escribir_config producían config.toml con la
convención de exit INCORRECTA (_syn_escribir_archivo devuelve 0=éxito en
runtime/core/io.c, -1 fallo: el instalador trataba !=logico como éxito) y
firmas `logico` vs `entero` en un TU (Manual 8 §1.7.3 r194). Fix mínimo:
convención canónica `== 0` + externos int64_t.
implementacion: opensyn/installer.syn escribir_config (== 0) // cumple
Manual 9 §5.4; cabecera de externos // cumple Manual 8 §1.7.3
oraculo: auditoria/oraculos/oraculo_r197_instalador.py — A3 config.toml con
secciones [general]/[modelo]/[server] y config_ollama.txt con model=<nombre>
generados por el E2E real; A1 umbrales VRAM de la tabla M9 §5.2.

## Record del ME (hallazgos EJECUTANDO, contexto del plan)

- H-R197-1 NUEVA a cola (repro determinista): el emisor libera el parámetro
  `texto` cedido a un campo de struct (extiende H-R182c-1 — use-after-transfer
  en canales — a structs): el slab recicla el buffer y el CONCAT siguiente
  corrompe el campo → config.toml `ruta` sale con el prefijo reciclado
  ("config.toml\0eek-coder..."). Fix: emisor + self-host + rebuild +
  bootstrap 3 etapas (ME propio). Bisect por stash: test_oraculos_config_ruta
  falla IGUAL en HEAD sin r197 → herencia, no regresión de este ME.
- H-R197-3 NUEVA a cola: seleccionar_modelo hardcodeado; el §7.2.5 exige leer
  modelos.toml (M9 §5.6) — ME propio con binding TOML; nota anclada al diff
  (installer.syn:10-11) como correccion de la DESVIACION del expediente.

## Checklist de cierre (fase 4b + 5)

- lecturas registradas (lecturas.jsonl, comas en --archivos)
- `alineacion.py --leer --me r197 --archivos "opensyn/installer.syn,runtime/core/modelo.c"` sello
- expediente docs/alineacion/r197.md --nuevo → --verificar 0 brechas (evidencia 0491b2530072b608)
- `contrastar.py --plan docs/plan_ME_r197.md` RC=0
- `verificar_alineacion.py` SIN BRECHAS
- familia instalador 17/17; bisect de preexistentes con stash; commit con hash real
