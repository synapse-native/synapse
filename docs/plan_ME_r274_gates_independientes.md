# Plan ME r274_gates_independientes

**Fase del roadmap:** Frente H (release industrial), Ola H1.
**Micro-entregable:** `r274_gates_independientes`.
**Depende de:** `r270_bootstrap_emision_paridad` (CERRADO), `r273_installer_modelo_grande` (CERRADO).
**Manuales:** Manual 9 §6.1, §6.2; Manual 1 §7.4.

---

requisito: Manual 9 §6.2
texto: "Validación Cruzada en CI/CD: los gates del sistema de construcción deben tener oráculos propios y deterministas, fuera del job de CI principal. Romper el sello (tocar la fuente sin cambiar el contenido que justifica el sello) debe hacer fallar el gate. La CI debe funcionar también sin `--sin-oraculos`."
implementacion: 1. Extraer los sellos de `build.py` y del job de CI `.github/workflows/*.yml` a oráculos independientes en `auditoria/oraculos/`. 2. Cada gate debe tener su propio oracle que compile las 3 etapas (S1→S2→S3) y compare S2==S3 (diff 0 bytes), verifique la firma Ed25519 de los artefactos distribuidos, mida el tiempo de hashing y reporte `Verificacion SHA-256: N ms (M MB/s)`, y falle si la fuente se toca sin justificación de contenido (no solo mtime). 3. Los oráculos deben ser resistentes a mutaciones menores del código fuente que no cambien el comportamiento observable (usando `--construir` para recomilar desde fuente). 4. El pipeline de CI debe invocar los oráculos como pasos independientes; si un oracle falla, el job falla, pero el pipeline no debería requerir una bandera especial para ejecutarlos.
oraculo: auditoria/oraculos/oraculo_r274_gates_independientes.py con estas banderas: `--construir` (lanza `build.py --skip-test` y compara S2==S3), `--sellar` (escribe `synapse_stage2.stamp` con el hash de la fuente sólo si la verificación pasó), `--estricto` (además de S2==S3, exige que `synapse.exe` y `dist/bin/synapse.exe` coincidan con la etapa 2), `--mutar` (aplica una mutación menor y verifica que el oracle siga pasando; si falla, el gate es frágil y debe reportarse).

 criterio_cierre: `contrastar --plan docs/plan_ME_r274_gates_independientes.md` → 3/3 PASS (requisito, implementacion, oraculo). `alinelacion.py --leer --me r274_gates_independientes` → sin brechas. `alinelacion.py --nuevo --me r274_gates_independientes` → expediente sellado. `verificar_alineacion.py` → 0 brechas. Los oráculos pasan en modo release con `SYNAPSE_BUILD_MODE=release` RC=0. CI (GitHub Actions) ejecuta los oráculos como pasos independientes sin bandera `--sin-oraculos` y RC=0. Romper el sello (editar `nucleo/principal.syn` sin actualizar el stamp) hace fallar `--estricto` y el gate correspondiente.

 producción_modificada: Cada archivo `.c`, `.h`, `.py`, `.syn`, `.syq` nuevo o modificado que introduzca un gate debe llevar el comentario: `// cumple Manual 9 §6.2 // cumple Manual 1 §7.4`