# Plan ME r275b_str_eq_texto_indexado

**Fase del roadmap:** Frente H (release industrial), deuda H-R275-1.
**Micro-entregable:** `r275b_str_eq_texto_indexado`.
**Depende de:** `r275_opensyn_e2e_bench` (CERRADO).
**Manuales:** Manual 2 §8.2, §4.1; Manual 1 §6; Manual 7 §7.3.

> Corrección 2026-11-20: el comentario de `opensyn/permisos.syn` atribuía a
> «Manual 7 §2.3» la regla «indexar texto produce texto». §2.3 real es
> *Pipeline RAG*: la cita es falsa y se retira en este ME. La regla no está
> enunciada en ningún manual como tal; lo que sí es ley es la tabla de tipos
> (Manual 2 §4.1), la inferencia Hindley‑Milner (Manual 2 §8.2) y la regla de
> hierro del bootstrap (Manual 1 §6), que exige que todas las etapas emitan lo
> mismo. Este plan se apoya en esas tres, no en una sección inventada.

---

requisito: Manual 2 §8.2
texto: "Synapse utiliza un algoritmo de inferencia de tipos basado en **Hindley‑Milner** (algoritmo W). Las variables de tipo se representan como `TVar(id)`."
implementacion: `_syn_nativo_expr_tipo_c` (`nucleo/generator.syn`) resuelve `ExprIndice` sólo para `Lista<T>` y `Mapa<K,V>`; con receptor `texto` devolvía `0`, y el llamador caía a `int64_t`. Se añade la rama `texto`/`cadena`/`CadenaSegura` que infiere `CadenaSegura`, igual que la etapa 1 (`compilador/`), de modo que la inferencia deja de ser un fallback ciego.
oraculo: auditoria/oraculos/oraculo_r275b_texto_indexado.py

requisito: Manual 2 §4.1
texto: "| `texto` / `cadena` / `string` | Cadena UTF-8 segura (longitud + buffer) | 16 bytes | No termina en `\0` internamente, se convierte para FFI |"
implementacion: `_oo_expr_a_c` (`nucleo/generator.syn`) emitía la expresión `ExprIndice` sobre texto como el literal `0` (la rama sólo cubría Lista/Mapa), perdiendo el carácter. Ahora emite `((CadenaSegura){ .longitud = 1, .datos = &(<texto>.datos[(int)(<índice>)]) })`, la misma forma que la etapa 1, así que el valor es un `texto` de un carácter y no un entero. Se retira además la cita falsa `Manual 7 §2.3` de `opensyn/permisos.syn`.
oraculo: auditoria/oraculos/oraculo_r275b_texto_indexado.py

requisito: Manual 1 §6
texto: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0). El determinismo se verifica obligatoriamente en la CI mediante la comparación de los hashes SHA‑256 de las etapas 2 y 3."
implementacion: el cambio vive en el emisor autohospedado, así que se reconstruye la cadena completa y se exige `S2==S3` (`build.py` + `oraculo_r274_gates_independientes.py --estricto`). No se toca ningún test existente: la sonda OpenSyn de r275 usa S2 en cuanto compila, sin cambiar sus aserciones.
oraculo: auditoria/oraculos/oraculo_r274_gates_independientes.py

requisito: Manual 7 §7.3
texto: "- **Sandboxing:** El servidor de inferencia se ejecuta con permisos mínimos."
implementacion: el indexado de texto es lo que decide el separador de ruta en `opensyn/permisos.syn` (`es_ruta_en_workspace`). Con S2 la comprobación no compilaba (`str_eq(int64_t, CadenaSegura)`); tras el arreglo compila y el sandbox E2E se ejecuta con el binario nativo, no con la etapa 1. Cierra H-R275-1.
oraculo: auditoria/oraculos/oraculo_r275_opensyn_e2e_bench.py

requisito: Manual 8 §4.1
texto: "| `synapse build <archivo>` | Compila el archivo (`.syn` o `.syq`) a binario. |"
implementacion: con `str_eq` resuelto, la sonda E2E seguía sin poder compilarse con S2 porque `nucleo/principal.syn` resolvía los `importar` y las fuentes del runtime **sólo** desde el cwd (con `cwd=tmp` fallaba `ERR_MODULE_NOT_FOUND` / `synapse_rt.c: No such file or directory`). Se añade el directorio del ejecutable y sus dos padres a la búsqueda de módulos (ramas `std.*` y de proyecto) y a la base del runtime. El orden previo (cwd, `axon_modules`, …) se conserva, así que un checkout normal no cambia de comportamiento.
oraculo: auditoria/oraculos/oraculo_r275b_texto_indexado.py

requisito: Manual 9 §6.2
texto: "- La verificación del bootstrap (diff 0 bytes)."
implementacion: `build.py` abortaba para siempre tras editar `nucleo/principal.syn`: el sello de frescura ya no certificaba la fuente y `oraculo_r252_paridad_bootstrap.py` se negaba a re-sellar (punto muerto). Ahora, con `--sellar`, se re-sella cuando la etapa 2 es posterior a la fuente y `S2==S3`; un artefacto stale sigue fallando. Sin `--sellar` el comportamiento es el anterior.
oraculo: auditoria/oraculos/oraculo_r252_paridad_bootstrap.py

criterio_cierre: `contrastar --plan docs/plan_ME_r275b_str_eq_texto_indexado.md` PASS con los 4 requisitos y oráculos ejecutados. `oraculo_r275b_texto_indexado.py` rc=0 (compila con S2 y verifica el valor del carácter indexado). `oraculo_r275_opensyn_e2e_bench.py` rc=0 **sin** `[R275][WARN]`. `oraculo_r274 --estricto` rc=0 con `S2==S3`. `verificar_alineacion.py` → 0 brechas.

produccion_modificada: `nucleo/generator.syn` (ramas `ExprIndice` con `// cumple Manual 2 §8.2`/`§4.1`), `nucleo/principal.syn` (resolución de módulos y del runtime con `// cumple Manual 8 §4.1`), `opensyn/permisos.syn` (retiro de la cita falsa), `auditoria/oraculos/oraculo_r252_paridad_bootstrap.py` (re-sellado, H-R275-2) y `auditoria/oraculos/oraculo_r275b_texto_indexado.py` (oráculo nuevo). No se modifica ningún test existente; se añade `tests/auditoria/test_oraculo_r252_resellado.py`.
