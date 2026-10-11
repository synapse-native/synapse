# Plan MTS — ME r183d_flags_debug

> Formato estricto según docs/gobernancia/METODO_TRABAJO.md:
> bloques `requisito:`/`texto:`/`implementacion:`/`oraculo:`.
> Gate: `python auditoria/contrastar.py --plan docs/plan_ME_r183d_flags_debug.md`

## R1 — Fallback de salida no destruye el compilador autoalojado

requisito: Manual 8 §4.2 — "El CLI debe aceptar `--output <nombre>` para
especificar el binario de salida" (banderas de compilación del CLI).

texto: "| `--output` | Especifica el nombre del binario de salida. |"

implementacion: nucleo/principal.syn (prescan de flags argv + fallback
`<archivo>.exe` en dispatcher nativo R183d R2/R3). Al compilar sin `-o`,
la salida es `<base-del-fuente>.exe`, NUNCA synapse_stage2.exe: el
compilador autoalojado queda intacto (bootstrap Manual 9 §6.2 diff 0 bytes).

oraculo: auditoria/oraculos/oraculo_r183d.py (R1/R2/R3, 11/11 PASS,
evidencia auditoria/evidencia/oraculo_r183d.log; S2==S3 sha256
c3231f3406d15b24... byte-identical verificado con cmp).

## R2 — --debug sin sanitizers disponibles degrada documentado

requisito: Manual 9 §6.1 — "□ **Sanitizadores**: ASan/UBSan/TSan no
reportan errores (en los targets que lo soportan)."

texto: los sanitizers solo aplican "en los targets que lo soportan"; el
toolchain MinGW-w64 local no distribuye libasan/libubsan (probe de link:
`ld.exe: cannot find -lasan: No such file`).

implementacion: pipeline.py `_soporta_sanitizers()` + degradación a
`-O0 -g` con aviso a stderr; paridad en el compilador nativo
(nucleo/principal.syn:630, probe de link real, remove del probe).
La depurabilidad (objetivo real de --debug, Manual 8 §4.2) se conserva.

oraculo: auditoria/oraculos/oraculo_r183d.py R2 --debug rc=0 +
probe manual: synapse probe.syn --debug → "sanitizadores no disponibles
en este toolchain; se usa -O0 -g" y binario ejecutable (DBG_OK).

## R3 — Determinismo del bootstrap tras el cambio

requisito: Manual 9 §6.2 — "La verificación del bootstrap (diff 0 bytes)."

texto: "El pipeline de CI/CD ejecuta automáticamente: ... La verificación
del bootstrap (diff 0 bytes)."

implementacion: rebuild completo S1→S2→S3 con el compilador parcheado;
S2 y S3 byte-idénticos.

oraculo: auditoria/oraculos/oraculo_determinismo_r183d.py (S2==S3 sha256
autocompilación en estado estacionario, Manual 9 §6.2).
