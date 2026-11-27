# Plan ME-r201 — Distribución real: actualizador seguro y repo canónico

Contexto: el instalador y la documentación publicaban URLs de otro proyecto
(`anomalyco/opencode` y `synapse-lang/synapse`), y `auto_actualizar.py` era una
demostración: descargaba el primer asset, no comparaba versiones, no verificaba
checksum, no hacía backup/rollback y silenciaba los errores. Este ME convierte
esa pieza en un actualizador fail-closed y alinea las URLs públicas con el repo
canónico `synapse-native/synapse`.

## Ley citada (MTS: requisito / texto / implementacion / oraculo)

requisito: Manual 9 §3.2 (Verificación de versión)
texto: "**Verificación de versión**: Consulta el endpoint de versiones en GitHub Releases (o Axon Hub)."
implementacion: `instaladores/common/auto_actualizar.py` — `verificar_version()` consulta `api.github.com/repos/synapse-native/synapse/releases/latest`, valida el tag semántico, compara con la versión instalada (sin degradar) y devuelve `ok=False` con el error real si la red, el JSON o el tag fallan. `_es_mas_nueva()` implementa comparación numérica 8.2.0 > 8.1.0.
oraculo: tests/installers/test_auto_actualizar_producto.py — release válido, error de red fail-closed y comparación semántica.

requisito: Manual 9 §3.2 (Descarga de la nueva versión)
texto: "**Descarga de la nueva versión**: Descarga el instalador o los binarios actualizados."
implementacion: `instaladores/common/auto_actualizar.py` — `descargar_actualizacion()` exige SHA-256, descarga por bloques con límite de 2 GiB a un archivo temporal y solo hace `os.replace()` si el hash coincide; un checksum ausente o distinto no deja artefacto en destino. `obtener_sha256_desde_asset()` lee el asset `.sha256` del release y falla cerrado si no existe.
oraculo: tests/installers/test_auto_actualizar_producto.py — checksum válido, checksum inválido y checksum ausente.

requisito: Manual 9 §3.2 (Backup de la versión anterior)
texto: "**Backup de la versión anterior**: Guarda la versión actual en `~/.synapse/backup/`."
implementacion: `instaladores/common/auto_actualizar.py` — `crear_backup()` copia el binario actual a `~/.synapse/backup/<binario>.bak` y `rollback()` restaura el backup de forma atómica; ambos devuelven error accionable si la ruta no existe.
oraculo: tests/installers/test_auto_actualizar_producto.py — backup y rollback restauran el contenido original.

requisito: Manual 9 §3.2 (Instalación de la nueva versión)
texto: "**Instalación de la nueva versión**: Reemplaza los binarios y archivos."
implementacion: `instaladores/common/auto_actualizar.py` — `instalar_actualizacion()` rechaza archivos vacíos, solo ejecuta `.exe`/`.msi` verificados en Windows (silencioso con `/SILENT /NORESTART` o `/qn /norestart`) y en Linux/macOS devuelve `manual=True` en lugar de simular una instalación.
oraculo: tests/installers/test_auto_actualizar_producto.py — ejecución Windows simulada con `subprocess.run` y rechazo de instalador vacío.

requisito: Manual 9 §4.1 (GitHub Releases)
texto: "Los artefactos se publican en la sección **Releases** del repositorio de GitHub."
implementacion: `instaladores/common/auto_actualizar.py` usa `synapse-native/synapse` como repo canónico y selecciona el asset de la plataforma con `_seleccionar_asset()` (Windows `.exe`/`.msi`, Linux `.tar.gz`/`.AppImage`/`.deb`/`.rpm`, macOS `.dmg`/`.pkg`). `README.md`, `instaladores/README.md`, `instaladores/windows/synapse.iss` y `docs/guia_usuario_instaladores.md` apuntan al mismo repo y ya no citan `anomalyco/opencode` ni `synapse-lang/synapse`.
oraculo: tests/installers/test_auto_actualizar_producto.py — repo canónico, selección de asset/checksum y URLs de documentación/instalador.

## Fuera de alcance
- La firma Ed25519 de releases sigue pendiente: `release_keys/*.pem` está ignorado por git y el instalador invoca el verificador con `|| true`. No se inventa una cadena de firma sin custodia de la clave privada ni certificado. El actualizador exige checksum SHA-256; la verificación `.sig` se conectará cuando exista una clave pública válida y custodia de la privada.
- No se modifica `synapse update` nativo ni el workflow de CI; este ME corrige la herramienta Python que puede invocar el instalador.
- No se toca `nucleo/lsp_v3.syn` ni trabajo unstaged de otro agente.

## Pasos de verificación
1. `.venv\Scripts\python.exe -m pytest tests/installers/test_auto_actualizar_producto.py -v`
2. `.venv\Scripts\python.exe -m pytest tests/installers/test_auto_actualizar.py -v`
3. `python auditoria/contrastar.py --plan docs/plan_ME_r201_distribucion_real.md`
4. `python auditoria/alineacion.py --nuevo --me r201_distribucion_real` y `--verificar --me r201_distribucion_real`
5. `python auditoria/verificar_alineacion.py` — 0 brechas

## Gates
- `contrastar.py` debe resolver los 5 requisitos con el oráculo ejecutado.
- Cada archivo de producción modificado lleva `// cumple Manual X §Y` (en `.py`, `#`).
- No commit hasta que el Arquitecto lo pida.
