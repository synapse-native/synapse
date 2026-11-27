# Verificación — ME r314_installer_workflow

CUMPLE.

## Requisitos del plan y su verificación

| requisito | verificación | resultado |
|---|---|---|
| Manual 9 §6.1 — CUMPLE — workflow válido y build canónico | `pytest tests/auditoria/test_r314_installer_workflow.py` | 3 passed |
| Manual 9 §6.1 — CUMPLE — sin artefactos ausentes | idem | 3 passed |

## Causa y cambio

1. **Workflow descartado en 0 s.** El paso "Install Inno Setup" declaraba
   `shell: powershell` dos veces en el mismo mapa. PyYAML lo acepta (por eso el
   YAML "parseaba"), GitHub no: reporta *workflow file issue* y no crea jobs.
   Se eliminó la clave duplicada y el oráculo detecta claves repetidas.
2. **Build del binario.** El paso 4b usaba `main.py --output dist/bin/
   synapse.exe`, que no enlaza el runtime modular. Ahora usa `python build.py`
   y copia la etapa 2; añade `dist\bin\opensyn.exe` para el componente opensyn.
3. **`dl_helper.exe`.** `Cross-Compile Synapse` (run `45170587871`) abortaba con
   `Error on line 124 ... dl_helper.exe does not exist`. El helper no está
   versionado ni tiene fuente; la entrada pasa a `skipifsourcedoesntexist` y el
   `.iss` ya degrada a `curl` (`DownloadFile`). Registrado como **H-R314-1**
   con decisión del Arquitecto pendiente (versionar la fuente o retirarlo).

## Otros checks

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r314_installer_workflow.py` | 3 passed |
| `yaml.safe_load` sobre los 11 workflows | todos parsean |
| `contrastar.py --plan docs/plan_ME_r314_installer_workflow.md` | PASS (2/2) |
| `verificar_alineacion.py` | 0 brechas |

## Limitación declarada

El job real corre en `windows-latest` con Inno Setup; aquí solo se valida la
estructura del workflow, el build canónico en Windows local y la coherencia del
`.iss` con los archivos versionados. La corrida de CI del push siguiente es la
verificación efectiva.
