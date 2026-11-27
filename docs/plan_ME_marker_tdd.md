# Plan ME marker_tdd — H-AUD-OP-3 (auditoría de operatividad OpenSyn, 2026-09-25)

**Hallazgo:** `@pytest.mark.tdd` se usa en 24 archivos de tests
(`tests/installers/`, `tests/integration/`, `tests/opensyn/`, `tests/auditoria/`)
pero NO está registrado en la sección `markers` de `pytest.ini` → warnings
`PytestUnknownMarkWarning` en cada sesión y selección por categoría poco fiable
(`pytest -m tdd`). Los headers OBL del protocolo MTO llevan la etiqueta `| TDD`
como convención ratificada de facto (ver bitácora MTO, 49 entradas OBL).

## R1 — Registro del marker tdd en pytest.ini
requisito: Manual 9 §6.2
texto: "**Nuevo (Fase 31):** `synapse test --junit --coverage` para generar
reportes de tests y cobertura." — la validación cruzada de CI (§6.2) exige
suites limpias y seleccionables por categoría; un marker desconocido ensucia la
salida con warnings y deja la selección `-m tdd` sin garantías (un
`--strict-markers` futuro rompería la suite completa).
implementacion: `pytest.ini`, sección `markers`: añadir las líneas
`tdd: Tests de desarrollo guiado por tests (TDD)` y
`e2e: Tests end-to-end` a continuación de
`bootstrap: Tests del proceso de bootstrap`. Sin comentario interno en el valor
multi-línea del INI (los `#` intermedios pasan a formar parte del valor).
Hallazgo del ME (H-TDD-1): además de `tdd` (8 warnings), el marker `e2e`
(`tests/test_e2e_spa_counter.py:19`, 1 warning) también estaba sin registrar —
el oráculo de colección limpia lo detectó; se registra ambos para 0
PytestUnknownMarkWarning.
oraculo: tests/auditoria/test_oraculos_marker_tdd.py

## R2 — Oráculo de registro limpio + ancla OBL-MTO
requisito: Manual 9 §6.2
texto: (misma validación cruzada de CI; el oráculo ejecuta la suite como lo haría
el pipeline y exige salida sin warnings de markers desconocidos).
implementacion: `tests/auditoria/test_oraculos_marker_tdd.py` (NUEVO):
(a) subproceso autoritativo `pytest tests/ --co -q -m tdd` → rc==0 y SIN
`PytestUnknownMarkWarning` en stdout+stderr; (b) anti-sniff estructural: `tdd:`
presente en la sección markers de `pytest.ini`; (c) ancla OBL-MTO: el oráculo
del ME eof_cierre_chat (`tests/auditoria/test_oraculos_eof_cierre.py`) declara
su encabezado `OBL-EOF-R1 ... | TDD`, el mismo marcador ahora registrado.
oraculo: tests/auditoria/test_oraculos_marker_tdd.py (auto-referencial)

## Archivos a modificar
Config (NO producción según contrastar: ext .ini):
- pytest.ini (R1)
Tests (NUEVOS, TDD):
- tests/auditoria/test_oraculos_marker_tdd.py (R2)

## Notas
- Sin archivos de producción modificados → gate de alineación "no aplica";
  el oráculo se ejecuta igualmente via contrastar (MTS fase 4b).
- El subproceso del oráculo corre la colección completa (~4 s) porque la
  advertencia de marker desconocido solo aparece al colectar los archivos que
  aplican el mark.
