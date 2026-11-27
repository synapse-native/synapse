# Plan ME opensyn_exe_fresco — H-AUD-OP-2 (auditoría de operatividad OpenSyn, 2026-09-25)

**Hallazgo:** `dist/bin/opensyn.exe` (17-sep 21:11) es anterior al último cambio
efectivo del fuente que compila (`opensyn/principal.syn`, fix H-R149-WIP del
17-sep 22:19 y todos los posteriores, incluido ME eof_cierre_chat 830074a).
El binario "distribuido" local está stale: un usuario que lo ejecute prueba un
OpenSyn SIN las correcciones recientes (H-AUD-OP-1 incluido).

**Alcance:** `dist/bin/` NO está trackeado por git (artefacto local de build;
`git ls-files dist/bin/` vacío). La reparación es (1) regenerar el artefacto con
el pipeline real y (2) añadir un oráculo PERMANENTE que detecte la staleness
futura (sin cambios en archivos de producción → sin expediente de alineación;
el plan MTS cita igualmente los requisitos).

## R1 — Regeneración + smoke del binario distribuido
requisito: Manual 9 §6.1
texto: "□ **OpenSyn**: detección de hardware, descarga de modelo y consulta de
prueba exitosas." — el checklist DoD exige un OpenSyn operativo; un exe stale
que no contiene los fixes vigentes no puede pasar el DoD.
implementacion: regenerar con el pipeline REAL de OpenSyn (bootstrap M1 §6:
la ruta nativa stage1/stage2 hornea el main del compilador nucleo y produce
OTRO compilador, NO OpenSyn):
  `.venv/Scripts/python.exe main.py opensyn/principal.syn -o dist/bin/opensyn.exe`
Verificación de humo: ejecutar el exe con stdin "1\n" → rc==0 y arranque
reconocible: modo compilador puro ("Uso:" en stdout; sin config el menú consume
"1" y cae a modo_compilador — con config pre-existente el input ni se consume)
o modo oráculo con cierre por EOF ("Tu>" + "[EOF]", fix H-AUD-OP-1). El test
acepta ambos (no amarra a quirks de entorno) y rechaza colga/rc!=0. Usa
USERPROFILE/HOME virtual + cwd tmp (H-EOF-2: el binario puede mutar
.synapse_config del cwd).
// cumple Manual 9 §6.1
oraculo: tests/auditoria/test_oraculos_opensyn_exe.py

## R2 — Guard de frescura fuente↔exe (anti-regresión)
requisito: Manual 9 §6.2
texto: "El pipeline de CI/CD ejecuta automáticamente: La suite de tests completa
en cada target." — la validación cruzada debe detectar el artefacto desincronizado
del fuente; el guard añade esa verificación a la suite de auditoría.
implementacion: `tests/auditoria/test_oraculos_opensyn_exe.py` (NUEVO), fixture
de módulo: si `dist/bin/opensyn.exe` NO existe se construye on-demand con el
pipeline real (máquina limpia/CI: el artefacto es untracked); R2 compara el
mtime del exe contra la fecha del ÚLTIMO COMMIT que tocó
`opensyn/principal.syn` (`git log -1 --format=%ct -- opensyn/principal.syn`)
y EXIGE exe más nuevo que el último commit del fuente → si un futuro commit
toca el fuente sin regenerar dist/bin, la suite de auditoría FALLA y lo
obliga (H-AUD-OP-2 se vuelve estructuralmente imposible sin detección).
// cumple Manual 9 §6.2
oraculo: tests/auditoria/test_oraculos_opensyn_exe.py (auto-referencial)

## Archivos a modificar
- dist/bin/opensyn.exe (ARTEFACTO local, NO commiteado — regenerado en R1)
Tests (NUEVOS, TDD):
- tests/auditoria/test_oraculos_opensyn_exe.py (R1 + R2)

## Notas
- `opensyn_lsp` (dist/bin/synapse_lsp.exe, 10-sep) queda fuera de alcance del
  hallazgo H-AUD-OP-2 (solo opensyn.exe); posible deuda futura si se distribuye.
- Sin archivos de producción modificados → gate de alineación "no aplica";
  el oráculo se ejecuta igualmente via contrastar (MTS fase 4b).
