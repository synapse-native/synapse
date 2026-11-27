# Plan ME r276_multiplataforma_release

**Fase del roadmap:** Frente H (release industrial), P0 tras r274/r275/r275b.
**Micro-entregable:** `r276_multiplataforma_release`.
**Depende de:** `r270_bootstrap_emision_paridad` (CERRADO), `r273_installer_modelo_grande` (CERRADO),
`r275b_str_eq_texto_indexado` (CERRADO).
**Manuales:** Manual 9 §6.1, §6.3, §6.2, §2.4, §2.5.

> Alcance real de esta sesión: la matriz de CI ya construye y firma en cuatro
> plataformas, y `release_matrix.yml` ya verifica las firmas de lo publicado,
> pero **nadie probaba que el binario distribuido funcione**: no había smoke de
> `--version`, de compilar/ejecutar un programa ni de los artefactos que el
> usuario descarga. Este ME añade ese gate (`scripts/verificar_release_limpio.py`),
> lo cablea a la matriz antes de publicar y lo hace fallar de verdad (bundle
> incompleto, byte manipulado, firma ausente). Límite declarado: la ejecución en
> VM limpia Windows y en runners Linux/macOS/ARM no se puede medir desde esta
> máquina; aquí se mide el caso Windows con el bundle real y la regresión
> sintética cubre ambos lados del gate.

---

requisito: Manual 9 §6.1
texto: "□ **Instalador unificado**: probado en sistemas limpios (sin instalación previa) y funciona correctamente."
implementacion: `scripts/verificar_release_limpio.py` verifica el bundle que recibe el usuario: artefactos obligatorios (binario, `install.sh`, `synapse.iss`, SBOM, attestation, `synapse.pub`, manifiesto), integridad SHA-256 contra sidecars y manifiesto, firmas Ed25519 y smoke real con el binario distribuido (`--version`, compilar y ejecutar un programa, `opensyn --version` si está). Devuelve rc=1 con la causa si falta un artefacto o si algo no verifica; nunca devuelve verde sin medir.
oraculo: tests/auditoria/test_r276_release_limpio.py

requisito: Manual 9 §6.3
texto: "- Cada artefacto se firma con la clave privada Ed25519 del proyecto."
implementacion: el gate exige `.sig` válida con `synapse.pub` para **cada** artefacto del manifiesto y para `MANIFEST.sha256`, y además que todo artefacto firmado esté listado en el manifiesto (un artefacto fuera del manifiesto es una brecha). La verificación es offline (`instaladores.common.verificar_firma`), así que corre igual en CI y en local.
oraculo: tests/auditoria/test_r276_release_limpio.py

requisito: Manual 9 §2.4
texto: "El instalador para Unix es un script Bash que:"
implementacion: `install.sh` pasa a ser artefacto obligatorio del bundle verificado (junto con su `.sha256` y `.sig`), de modo que un release sin instalador Unix falla el gate en lugar de publicarse incompleto.
oraculo: tests/auditoria/test_r276_release_limpio.py

requisito: Manual 9 §2.5
texto: "El script `installer.iss` de Inno Setup para Windows:"
implementacion: `synapse.iss` es artefacto obligatorio y firmado del bundle verificado; el gate falla si falta el instalador de Windows o su firma (caso cubierto por la regresión con firma eliminada).
oraculo: tests/auditoria/test_r276_release_limpio.py

requisito: Manual 9 §6.2
texto: "El pipeline de CI/CD ejecuta automáticamente:"
implementacion: `release_matrix.yml` gana el job `smoke_release_limpio` con matriz de cuatro runners (ubuntu x64, ubuntu arm64, macos arm64, windows x64): descarga el artefacto de su plataforma, ejecuta el gate con smoke y sube la evidencia JSON. `create_release` pasa a depender de ese job, así que un release no se publica si el smoke de una plataforma falla.
oraculo: tests/auditoria/test_r276_release_limpio.py

## Criterio de cierre

1. `python scripts/verificar_release_limpio.py` → `PASS` sobre el bundle real
   Windows (`instaladores/dist/distribucion`), con firma y smoke.
2. El gate falla (rc=1) con un byte manipulado y con una firma ausente
   (medido en copia, sin tocar el bundle real).
3. `pytest tests/auditoria/test_r276_release_limpio.py` 5/5.
4. `contrastar --plan docs/plan_ME_r276_multiplataforma_release.md` PASS y
   `verificar_alineacion.py` 0 brechas.
5. Documentar en `docs/reportes/R276.md` el límite: VM limpia y
   Linux/macOS/ARM no medidos en esta sesión; la matriz queda cableada y su
   evidencia es el artefacto `smoke-<plataforma>` del run de CI.
