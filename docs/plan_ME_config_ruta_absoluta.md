# Plan ME config_ruta_absoluta — H-EOF-3 (deuda de ME eof_cierre_chat, R155; 2026-09-26)

**Deuda:** `leer_modo_config()`/`guardar_modo_config()` (opensyn/principal.syn)
leen/escriben `ARCHIVO_CONFIG = ".synapse_config"` RELATIVO al cwd a través de
`leer_archivo`/`escribir_archivo` de std.sistema, cuya validación
`_validar_ruta_segura` (std/sistema.syn:16) SIEMPRE rechaza rutas relativas:
`_syn_ruta_en_directorio` exige que la ruta contenga al cwd como prefijo
(`ruta.longitud < dir.longitud → 0`) y una ruta relativa nunca lo contiene →
`""`. Consecuencia: la lectura de config cae SIEMPRE a los fallbacks
HOME/Program Files (pasos 2/3 con bypass asm) y el menú de bienvenida es
inrunnable en instalación pre-configurada (E2E del menú con skip condicional).

**Hallazgos estructurales de este ME (H-EOF-3a/b, se reparan aquí):**
- **H-EOF-3a:** `_syn_normalizar_ruta` (runtime/core/sistema.c) emite
  separadores `/`, pero `GetCurrentDirectoryA` devuelve cwd con `\` → el
  comparador por prefijo NUNCA matchea ni siquiera para rutas absolutas: el
  sandbox de std.sistema rechaza TODAS las rutas y todos los consumidores
  terminan en bypass `inseguro/asm` (el sandbox es teatro).
- **H-EOF-3b:** `_syn_ruta_en_directorio` compara con `memcmp` de
  `dir.longitud` bytes SIN borde de componente: `proyecto_synapse_evil`
  pasaría como "dentro de" `proyecto_synapse` (POSIX); además es sensible a
  mayúsculas en Windows.

## R1 — Runtime: separadores consistentes con el SO en `_syn_normalizar_ruta`
requisito: Manual 5 §1
texto: "**El estado mutable compartido entre hilos está prohibido** a nivel de
compilación." (M5 §1 Filosofía; las funciones de runtime/core/sistema.c son
puras y thread-safe — sin estado global, `pool_alloc` para el resultado.)
implementacion: `runtime/core/sistema.c` `_syn_normalizar_ruta`: en la emisión
del separador (`normalized[nlen++] = '/'`), usar el separador de la
plataforma: `'\\'` bajo `_WIN32`, `'/'` en POSIX (la absorción de entradas ya
acepta ambos, se mantiene). El trailing también se recorta con el separador de
plataforma. Resultado: la salida es comparable byte a byte con el cwd crudo.
// cumple Manual 5 §1
oraculo: tests/auditoria/test_oraculos_config_ruta.py

## R2 — Runtime: borde de componente y punto de montaje en `_syn_ruta_en_directorio`
requisito: Manual 5 §1
texto: "La comunicación entre fibras se realiza exclusivamente a través de
**canales tipados**" — M5 §1 gobierna el módulo runtime; la corrección del
comparador es pura (sin estado compartido) y endurece el sandbox de rutas que
std.sistema expone.
implementacion: `runtime/core/sistema.c` `_syn_ruta_en_directorio`:
1. Comparación carácter a carácterInsensitive a mayúsculas SOLO en `_WIN32`
   (ASCII tolower en ambos lados); POSIX memcmp exacto.
2. Tras el prefijo de `dir.longitud` caracteres, exigir borde: `ruta ==
   dir`, O `dir` termina en separador, O el siguiente carácter de `ruta` es
   separador. `proyecto_synapse_evil` ya no pasa como hijo de
   `proyecto_synapse`.
3. Punto de montaje: si la primera componente (letra de unidad / `/` raíz)
   difiere, retornar 0 inmediatamente (rechazo de `D:\x` con cwd `C:\y`).
// cumple Manual 5 §1
oraculo: tests/auditoria/test_oraculos_config_ruta.py

## R3 — std/sistema.syn: normalizar cwd antes de comparar + contratos
requisito: Manual 2 §5.1
texto: "- **`requiere`:** Se evalúa antes de la primera instrucción del cuerpo.
Todas las expresiones deben ser booleanas.\n- **`garantiza`:** Se evalúa
inmediatamente antes de cada `retornar`. La variable `_resultado_` contiene el
valor que se va a retornar."
implementacion: `std/sistema.syn` `_validar_ruta_segura`:
1. `cwd = _syn_normalizar_ruta(_syn_obtener_cwd())` (hoy se compara crudo con
   `\` contra la ruta normalizada — causa directa del rechazo universal).
2. Contratos `requiere: longitud(ruta) > 0` y `garantiza: resultado == "" o
   longitud(resultado) >= longitud(ruta)` (normalizar acorta a lo sumo: `.`,
   `..` y duplicados colapsan).
3. Caso ruta `.` (normalizada vacía/`.`): retornar el cwd normalizado (el
   directorio de trabajo es una ruta válida DENTRO del sandbox: listing/
   existe sí; leer/escribir archivo sobre un directorio falla en runtime de
   forma segura).
// cumple Manual 2 §5.1
// cumple Manual 5 §1
oraculo: tests/auditoria/test_oraculos_config_ruta.py

## R4 — OpenSyn: config del cwd resuelta a absoluta en leer y guardar
requisito: Manual 7 §2.1
texto: "El orquestador es un proceso en C que gestiona el ciclo de vida del
servidor de inferencia (`llama-server`)." — robustez del ciclo de vida del
asistente local (misma ancla de los ME eof_*; la config decide el modo y su
lectura/escritura debe funcionar en la instalación real).
implementacion: `opensyn/principal.syn`:
1. NUEVA función `ruta_config_absoluta() -> texto` (contratos: requiere
   `longitud(ARCHIVO_CONFIG) > 0`; garantiza `longitud(resultado) > 0`):
   `cwd = _syn_obtener_cwd()`; si no vacío, concatenar separador solo si el
   cwd no termina ya en uno (caso raíz de unidad `D:\`) + `ARCHIVO_CONFIG`.
2. `leer_modo_config`: `leer_archivo(ARCHIVO_CONFIG)` →
   `leer_archivo(ruta_config_absoluta())`.
3. `guardar_modo_config`: `escribir_archivo(ARCHIVO_CONFIG, linea)` →
   `escribir_archivo(ruta_config_absoluta(), linea)`.
Equivalencia con el comportamiento histórico (cwd como base) cuando el sandbox
funciona; corrección cuando no: la config escrita por el menú en el cwd se
VUELVE legible en la siguiente ejecución (persistencia por carpeta). Los
fallbacks HOME/Program Files quedan intactos como respaldo.
// cumple Manual 7 §2.1
oraculo: tests/auditoria/test_oraculos_config_ruta.py

## R5 — Oráculo: roundtrip relativo real + config del cwd decide el modo
requisito: Manual 9 §6.2
texto: "El pipeline de CI/CD ejecuta automáticamente: La suite de tests completa
en cada target."
implementacion: `tests/auditoria/test_oraculos_config_ruta.py` (NUEVO, sin
skips):
(a) estructural anti-sniff: sistema.c emite separador de plataforma y el
comparador tiene borde de componente; sistema.syn normaliza el cwd y lleva
contratos; principal.syn define `ruta_config_absoluta` y la usa en leer y
guardar.
(b) probe .syn compilado on-demand con `python main.py` (pipeline real) que
ejercita `_validar_ruta_segura` de extremo a extremo en cwd temporal:
roundtrip relativo `escribir_archivo("probe_cfg.txt", ...)` +
`leer_archivo(...)` con contenido exacto; escape `..\..\` rechazado
(rc/return -1); lectura fuera del cwd devuelve "".
(c) E2E OpenSyn: compila `opensyn/principal.syn` on-demand (la ruta nativa
stage1 hornea el main del compilador núcleo, NO OpenSyn — usar main.py, R158) y
ejecuta en cwd temporal con config relativa `modo_oraculo=falso` → debe entrar
en Modo Lenguaje Puro ("Modo: Lenguaje Puro" en stdout, sin menú "Opcion",
rc==0): si la lectura relativa fallara, el fallback HOME/Program Files
decidiría el modo y el test falla. Aislamiento USERPROFILE/HOME virtual
(lección R145).
// cumple Manual 9 §6.2
oraculo: tests/auditoria/test_oraculos_config_ruta.py (auto-referencial)

## R6 — Mapa de alineación: entrada explícita para std/sistema.syn
requisito: Manual 5 §1 (runtime helpers C) y Manual 2 §5.1 (contratos) — el
legacy difuso manda std/sistema.syn a `std/* → Manual 2` sin ancla puntual del
sandbox de rutas.
implementacion: `docs/gobernancia/mapa_alineacion.md` (NUEVA entrada JSON):
`"std/sistema.syn": ["Manual 5 §1", "Manual 2 §5.1"]` (gana por
especificidad; corrección de higiene del mapa, no cambio de reglas).
oraculo: auditoria/verificar_alineacion.py (gate del pre-commit)
// cumple Manual 5 §1

## Archivos a modificar
Producción:
- runtime/core/sistema.c (R1, R2 — ancla M5 §1)
- std/sistema.syn (R3 — anclas M2 §5.1 + M5 §1)
- opensyn/principal.syn (R4 — ancla M7 §2.1 vigente)
Docs de gobernanza:
- docs/gobernancia/mapa_alineacion.md (R6)
Tests (NUEVOS, TDD):
- tests/auditoria/test_oraculos_config_ruta.py (R5)
- tests/fixtures/probe_config_ruta/probe_config_ruta.syn (R5b, fixture del probe)

## Notas de riesgo
- Consumidores de std.sistema NO cambian de contrato: `leer_archivo` relativa
  pasa a FUNCIONAR (antes `""` garantizado). El bypass asm de
  leer_modo_config paso 2/3 y el resto de bypass quedan intactos (fuera de
  alcance; limpieza de bypass = ME futuro si el Arquitecto lo ratifica).
- Cache runtime: los .o se invalidan solos (clave = SHA-256 fuente + flags,
  pipeline.py — lección R145 verificada).
- Guard de frescura OBL-EXE-R2: tras COMITEAR, regenerar
  dist/bin/opensyn.exe inmediatamente (comportamiento diseñado del guard).
- `leer_archivo` del cwd sobre un DIRECTORIO (`.` → cwd): fopen falla → `""`,
  seguro; `existe_archivo(".")` pasa a ser verdadero (correcto).
- lsp/lsp_v3 definen wrappers propios y NO consumen std.sistema — no se tocan.
