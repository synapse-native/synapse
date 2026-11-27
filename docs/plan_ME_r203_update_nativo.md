# Plan ME-r203 — `synapse update` nativo

Contexto: r202 dejó el release firmado y el actualizador Python fail-closed, pero
el binario nativo todavía no expone `synapse update`. Este ME implementa el
comando en el compilador autoalojado con consulta a GitHub Releases, selección
del binario de la plataforma, checksum SHA-256, firma Ed25519, backup y
reemplazo/instalación, manteniendo el transporte TLS en `curl` del sistema
(mismo precedente ratificado de `opensyn/installer.syn`, M9 §5.3).

## Ley citada (MTS: requisito / texto / implementacion / oraculo)

requisito: Manual 9 §3.1 (Comando `synapse update`)
texto: "Sin argumentos: actualiza a la última versión disponible."
implementacion: `nucleo/actualizador.syn` implementa `cli_update()` sin objetivo: consulta `/releases/latest`, compara semver contra `VERSION` y, si hay una versión mayor, continúa al pipeline de descarga/verificación/instalación.
oraculo: tests/integration/test_update_nativo.py

requisito: Manual 9 §3.1 (Comando `synapse update`)
texto: "`--version <version>`: actualiza a una versión específica."
implementacion: `nucleo/actualizador.syn` valida el objetivo (solo dígitos y puntos), consulta `/releases/tags/v<version>` y aplica exactamente esa versión; `nucleo/principal.syn` despacha `synapse update [--version <v>] [--check]`.
oraculo: tests/integration/test_update_nativo.py

requisito: Manual 9 §3.1 (Comando `synapse update`)
texto: "`--check`: solo verifica si hay actualizaciones disponibles, sin instalarlas."
implementacion: `nucleo/actualizador.syn` retorna tras imprimir la versión remota y el asset cuando `solo_check` es verdadero; no descarga ni reemplaza binarios.
oraculo: tests/integration/test_update_nativo.py

requisito: Manual 9 §3.2 (Pipeline de Actualización)
texto: "1. **Verificación de versión**: Consulta el endpoint de versiones en GitHub Releases (o Axon Hub)."
implementacion: `nucleo/actualizador.syn` descarga el JSON de `api.github.com/repos/synapse-native/synapse/releases/{latest|tags/vX}` con `curl -L -fsS` y lo parsea con `std.json`; `runtime/core/actualizador.c` aporta plataforma, ruta del ejecutable y verificación criptográfica.
oraculo: tests/integration/test_update_nativo.py

requisito: Manual 9 §3.2 (Pipeline de Actualización)
texto: "2. **Descarga de la nueva versión**: Descarga el instalador o los binarios actualizados."
implementacion: `nucleo/actualizador.syn::_act_descargar()` descarga el asset, el `.sha256` y el `.sig` con `curl -L -fsS` (transporte TLS del sistema) y `runtime/core/actualizador.c::_syn_actualizador_ejecutar()` ejecuta el comando con quoting robusto en Windows (`cmd /S /C`) para rutas con espacios.
oraculo: tests/integration/test_update_nativo.py

requisito: Manual 9 §3.2 (Pipeline de Actualización)
texto: "3. **Verificación de firma**: Comprueba la firma Ed25519 del artefacto."
implementacion: `runtime/core/actualizador.c::_syn_actualizador_verificar_firma()` decodifica el `.sig` hex de 128 caracteres y la clave pública canónica (o `SYNAPSE_PUBLIC_KEY` hex de 64, misma convención que `install.sh`), y llama a `_syn_ed25519_verificar()`; `nucleo/actualizador.syn` aborta y elimina el artefacto si la firma no es válida.
oraculo: tests/integration/test_update_nativo.py

requisito: Manual 9 §3.2 (Pipeline de Actualización)
texto: "4. **Backup de la versión anterior**: Guarda la versión actual en `~/.synapse/backup/`."
implementacion: `runtime/core/actualizador.c::_syn_actualizador_backup()` resuelve el ejecutable actual y copia a `~/.synapse/backup/synapse.exe.bak` antes de autorizar la instalación.
oraculo: tests/integration/test_update_nativo.py

requisito: Manual 9 §3.2 (Pipeline de Actualización)
texto: "5. **Instalación de la nueva versión**: Reemplaza los binarios y archivos."
implementacion: `runtime/core/actualizador.c::_syn_actualizador_instalar()` ejecuta un instalador silencioso si el asset es `setup`/`installer`; si el release solo publica el binario, en Windows lanza un helper PowerShell que espera al proceso y reemplaza el `.exe`, y en POSIX usa reemplazo atómico.
oraculo: tests/integration/test_update_nativo.py

requisito: Manual 9 §4.1 (GitHub Releases)
texto: "Archivos de firma (`.sig`) y checksums (`.sha256`)."
implementacion: `nucleo/actualizador.syn` exige el `.sha256` y el `.sig` del asset elegido, verifica ambos antes de invocar el backup/instalación y falla cerrado si el release no los publica.
oraculo: tests/integration/test_update_nativo.py

requisito: Manual 2 §5.1 (Semántica Formal de contratos)
texto: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
implementacion: `nucleo/actualizador.syn` declara `requiere`/`garantiza` en `cli_update()` y en las funciones públicas del módulo; `runtime/core/actualizador.c` documenta la API C y su precondición de rutas.
oraculo: tests/integration/test_update_nativo.py

## Fuera de alcance
- Publicar un instalador Inno nuevo en el workflow: el comando prefiere un
  asset `setup`/`installer` si existe y, mientras el release actual solo publica
  `synapse-win_x64.exe`, usa el reemplazo nativo con backup.
- Custodia de `ED25519_PRIVATE_KEY`: sigue en GitHub Secrets.
- No se toca `nucleo/lsp_v3.syn` ni `nucleo/embedded_libs.h`.

## Pasos de verificación
1. `.venv\Scripts\python.exe -m pytest tests/integration/test_update_nativo.py -v`
2. Compilar `nucleo/principal.syn` y ejecutar `synapse --help`, `synapse update --check` con fixture local.
3. `python auditoria/contrastar.py --plan docs/plan_ME_r203_update_nativo.md`
4. `python auditoria/alineacion.py --verificar --me r203_update_nativo`
5. `python auditoria/verificar_alineacion.py` (0 brechas).

## Gates
- Cada archivo de producción modificado lleva `// cumple Manual 9 §3.1` y/o
  `// cumple Manual 9 §3.2` según corresponda.
- El oráculo no usa red real ni la clave privada del proyecto.
- No commit hasta que el Arquitecto lo pida.
