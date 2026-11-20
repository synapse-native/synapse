# Plan ME r274_gates_independientes

**Fase del roadmap:** Frente H (release industrial), Ola H1.
**Micro-entregable:** `r274_gates_independientes`.
**Depende de:** `r270_bootstrap_emision_paridad` (CERRADO), `r273_installer_modelo_grande` (CERRADO).
**Manuales:** Manual 9 §6.1, §6.2; Manual 1 §7.4.

> Corrección 2026-11-20: la versión anterior de este plan atribuía a Manual 9
> §6.2 un texto que **no existe** («los gates del sistema de construcción deben
> tener oráculos propios y deterministas…»). §6.2 real sólo enumera lo que el
> pipeline ejecuta. Las citas de abajo son literales del manual; el alcance se
> ajustó a lo que el oráculo verifica de verdad y lo no cubierto (firmas
> Ed25519 de *todos* los artefactos) queda registrado como H-R274-1.

---

requisito: Manual 9 §6.1
texto: "□ **Bootstrap exitoso**: en cada target, el proceso de bootstrap de 3 etapas produce `diff 0 bytes` entre Stage 2 y Stage 3."
implementacion: Oráculo propio e independiente de `build.py` que compara `synapse_stage2.exe` con `synapse_stage3.exe` por SHA-256 y tamaño: PASS sólo si son byte-idénticos. Reporta el hash y el tamaño medidos; falla si falta cualquiera de las dos etapas (no hay verde por omisión).
oraculo: auditoria/oraculos/oraculo_r274_gates_independientes.py

requisito: Manual 9 §6.2
texto: "El pipeline de CI/CD ejecuta automáticamente:" / "- La verificación del bootstrap (diff 0 bytes)."
implementacion: El oráculo corre como paso independiente del job `bootstrap` de `.github/workflows/ci-tests.yml`, después de generar las 3 etapas: si el oráculo falla, el job falla. No se invoca con `--sin-oraculos`: el pipeline ejecuta la verificación sin bandera especial.
oraculo: auditoria/oraculos/oraculo_r274_gates_independientes.py

requisito: Manual 1 §7.4
texto: "En caso de modificaciones en el compilador base, verificación de bootstrapped determinista (`diff 0 bytes` entre Stage 2 y Stage 3)." / "Generación automática de hash SHA‑256."
implementacion: `--construir` reproduce la cadena (`build.py --skip-test`) antes de comparar; `--sellar` escribe `synapse_stage2.stamp` con el SHA-256 del contenido de `nucleo/principal.syn` y de la etapa 2 **sólo si la verificación pasó**; `--estricto` exige además que `synapse.exe` y `dist/bin/synapse.exe` coincidan con la etapa 2; `--mutar` verifica que una mutación de contenido sea detectada por el sello, mutando un archivo temporal (nunca el árbol de trabajo).
oraculo: auditoria/oraculos/oraculo_r274_gates_independientes.py

criterio_cierre: `contrastar --plan docs/plan_ME_r274_gates_independientes.md` PASS con los 3 requisitos y oráculos ejecutados. `python auditoria/oraculos/oraculo_r274_gates_independientes.py --estricto` rc=0. `python auditoria/oraculos/oraculo_r274_gates_independientes.py --mutar` rc=0 con sello previo. El job `bootstrap` de CI invoca el oráculo como paso propio. `verificar_alineacion.py` → 0 brechas.

produccion_modificada: `auditoria/oraculos/oraculo_r274_gates_independientes.py` (cabecera `# cumple Manual 9 §6.1`, `§6.2`, `Manual 1 §7.4`), `.github/workflows/ci-tests.yml` (paso del gate) y `docs/gobernancia/mapa_alineacion.md` (trazabilidad de los archivos del instalador). No se modifica `build.py` ni ningún archivo del compilador.
