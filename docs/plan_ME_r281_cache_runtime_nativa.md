# Plan ME r281_cache_runtime_nativa

**Fase del roadmap:** Frente H (sostenibilidad), continuación de `r279b_suite_paralela`.
**Micro-entregable:** `r281_cache_runtime_nativa` (cierra H-R279-2).
**Depende de:** `r279b_suite_paralela` (CERRADO, `a460377`).
**Manuales:** Manual 8 §4.1; Manual 8 §4.2; Manual 9 §6.2.
**Origen:** H-R279-2. Medición: `synapse_stage2.exe tests/fixtures/tmp_r3_s2.syn
-o tmp_r3_s2.exe` tarda **93,18 s** con caché de runtime ya caliente; bajo la
suite cargada cruza el `timeout=120` del test y falla. El coste es la
recompilación de ~50 fuentes del runtime en **cada** invocación del compilador
nativo: `pipeline.py` ya cachea esos `.o` en `~/.synapse/cache/runtime_obj/`
con sidecar `.sha` (fuente+flags), pero `nucleo/principal.syn` no los consulta.

> Alcance: hacer que el enlace nativo use esos objetos cuando los 50 estén
> presentes y el SHA-256 de cada fuente coincida con su sidecar; si falta uno o
> el hash no coincide, enlaza desde fuente **exactamente como hoy**. No se toca
> ningún test ni el timeout.

---

requisito: Manual 8 §4.1
texto: "| `synapse build <archivo>` | Compila el archivo (`.syn` o `.syq`) a binario. |"
implementacion: el comando nativo sigue compilando a binario; lo único que cambia es de dónde salen los objetos del runtime. Se construye una lista de fuentes (synapse_rt.c + runtime/core/*.c + tweetnacl + sqlite3 + IA opcionales + federated) y, si **todas** tienen objeto cacheado con sidecar cuyo primer campo es el SHA-256 del fuente, el `gcc` enlaza esos `.o`; en cualquier otro caso se enlazan las fuentes como antes. El binario producido es el mismo (mismos objetos, mismos flags de enlace); el programa de prueba debe seguir imprimiendo `42`.
oraculo: auditoria/oraculos/oraculo_r281_cache_nativa.py

requisito: Manual 8 §4.2
texto: "| `--release` | Compila en modo release (optimizaciones). |"
implementacion: el reuso solo se activa con la optimización por defecto (`-O2`). Con `--release` (`-O3 -flto -DNDEBUG`), `--debug` (`-O0 -g`) o `--profile` se enlaza desde fuente, para no mezclar objetos compilados con otras flags. `_gcc_opt`, `_gcc_flags` y `_static_flag` no cambian.
oraculo: auditoria/oraculos/oraculo_r281_cache_nativa.py

requisito: Manual 9 §6.2
texto: "La verificación del bootstrap (diff 0 bytes)."
implementacion: los `.o` reutilizados son byte-idénticos a los recién compilados (el sidecar los valida por SHA-256 del fuente) y el orden del enlace es el mismo de la lista de fuentes, así que S2 y S3 siguen siendo byte-idénticos y el bootstrap no cambia. La suite completa por target sigue siendo la ley; el test que fallaba por timeout (inmutable) debe pasar sin tocar su aserción.
oraculo: tests/unit/test_r3_param_adt.py

## Criterio de cierre

1. `synapse_stage2.exe` compila el fixture en < 20 s con la caché caliente
   (antes 93,18 s) y el binario imprime `42`.
2. `pytest tests/unit/test_r3_param_adt.py -q` → 2 passed (sin tocar el test).
3. Bootstrap S1→S2→S3 con `diff` 0 bytes entre stage2 y stage3.
4. `python auditoria/contrastar.py --plan docs/plan_ME_r281_cache_runtime_nativa.md`
   PASS; `python auditoria/verificar_alineacion.py` 0 brechas; encoding OK.
5. H-R279-2 cerrado en `docs/plan_maestro_deudas.md` con la medición antes/después.

## Riesgos y mitigación

- **Objeto obsoleto:** imposible sin editar la fuente sin cambiar su SHA; el
  sidecar se compara contra el hash calculado en el momento.
- **Caché incompleta:** fallback completo a fuentes (all-or-nothing), sin
  mezclar objetos y fuentes.
- **Instalación sin `~/.synapse/cache`:** `getenv` vacío → fallback; el
  comportamiento es el actual.
