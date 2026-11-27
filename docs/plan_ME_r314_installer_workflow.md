# Plan de Micro-Entregable r314_installer_workflow

## Objetivo

`Build Synapse Installer (Fase 4.1)` falla desde hace varios pushes en **0 s y
sin jobs**. GitHub lo reporta como "workflow file issue": el YAML repite la
clave `shell: powershell` en el mismo mapa del paso "Install Inno Setup", y
GitHub descarta el workflow entero al parsearlo (PyYAML la acepta, por eso no se
detectó antes).

Además, dentro del mismo job:

- El paso 4b construye con `python main.py ... --output dist/bin/synapse.exe`,
  que no enlaza el runtime modular (mismo defecto que r311 en cross-compile).
- El `.iss` exige `instaladores/windows/dl_helper.exe`, que no está versionado y
  no tiene fuente en el repositorio.

Y en `Cross-Compile Synapse` (run `45170587871`) el instalador avanzó hasta
`Error on line 124: Source file ... dl_helper.exe does not exist`.

## Requisito 1 — workflow válido y build canónico

requisito: Manual 9 §6.1
texto: "□ **Instaladores multiplataforma**: se generan instaladores para Windows (.exe), Linux (.deb, .AppImage) y macOS (.dmg) desde el mismo código fuente."
implementacion: se elimina la clave `shell` duplicada del paso "Install Inno Setup" (GitHub descartaba el workflow sin ejecutar jobs) y el paso de build usa `python build.py` + `copy synapse_stage2.exe dist\bin\synapse.exe` + `python main.py opensyn/principal.syn -o dist\bin\opensyn.exe`.
oraculo: tests/auditoria/test_r314_installer_workflow.py

## Requisito 2 — el instalador no exige artefactos ausentes

requisito: Manual 9 §6.1
texto: "□ **Compilación sin errores**: todos los targets (Windows, Linux, macOS, WASM) compilan sin errores ni warnings."
implementacion: la entrada `dl_helper.exe` del `.iss` lleva `skipifsourcedoesntexist` (el script ya degrada a `curl` en `DownloadFile`); se registra H-R314-1 con la decisión pendiente del Arquitecto sobre versionar la fuente o retirar el helper.
oraculo: tests/auditoria/test_r314_installer_workflow.py

## Evidencia

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r314_installer_workflow.py` | 3 passed |
| YAML de workflows parseado con `yaml.safe_load` | 11/11 OK |
| CI `Build Synapse Installer` tras el push | pendiente de corrida |
| `contrastar.py --plan docs/plan_ME_r314_installer_workflow.md` | PASS (2/2) |
