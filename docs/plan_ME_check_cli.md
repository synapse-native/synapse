# Plan ME check_cli — `synapse check` en el CLI (H-R176-2)

**Fuente:** plan maestro `docs/plan_maestro_deudas.md` (mandato Arquitecto
2026-10-03). **Base:** 4ebd025 (R177). **Método:** MTS.

## R1 — check_nativo: subcomando `check --no-emit` en el dispatcher nativo
requisito: Manual 8 §4.2
texto: "| **`--check`** / **`--no-emit`** | **Modo de validación:** Solo verifica la sintaxis y semántica, sin generar código de salida. Útil para el bucle de corrección de OpenSyn. |"
(M8 §4.2 tabla, L431; consumidor M8 §5.2 L505: "El LSP ... ejecuta el
compilador ... en modo `--check` (usando el flag `--no-emit`). Esto se hace
mediante el CLI `synapse check --no-emit <archivo>`"; M8 §5.1 L448:
`synapse check --no-emit temp.syq`).
implementacion: `nucleo/principal.syn`:
(a) subcomando `check` en principal(): parsea flags (`--no-emit`, `--release`,
`--debug`, `--safe` — misma tabla de flags) y toma la PRIMERA ruta no-flag
(patrón cli_lint/cli_fmt H-33.5-2); valida _argc y ruta.
(b) centinela en `generar_etapa` (variable local `_check`, inyectada por el
bloque de dispatch; `__check__` se sustituye por "1" o "0"): corte tras el
análisis semántico (F8: parsear + analizar, etapas 2/3/7/8) ANTES de generar C
(4) y de gcc (5); rc=0 si el análisis pasa; NUNCA escribe `salida` ni crea
archivos; paridad de diagnóstico con la ruta normal (stderr de errores parseo/
semántico idéntico).
// cumple Manual 8 §4.2 (ME check_cli R1)
oraculo: tests/auditoria/test_oraculos_check_cli.py (test_r1)

## R2 — check_py: paridad del dispatcher Python (cli.py)
requisito: Manual 8 §4.1
texto: "synapse lint: ... `synapse fmt`: ..." — subcomandos por dominio
despachados a su backend (tabla M8 §4.1); `check` es el comando de validación
del bucle OpenSyn/LSP (M8 §5.2).
implementacion: `cli.py`: (a) subcomando 'check' en la tupla de detección y
despacho `_cmd_herramienta_nativa('check', ...)` (backend nativo stage2,
patrón R166 de backing on-demand ya existente — sin duplicar pipelines);
(b) el docstring de _cmd_herramienta_nativa pasa a citar los tres comandos.
// cumple Manual 8 §4.1 (ME check_cli R2)
oraculo: tests/auditoria/test_oraculos_check_cli.py (test_r2)

## R3 — check_exe: binario `synapse` instalable para el bucle de validación
requisito: Manual 8 §4
texto: "## 4. CLI UNIFICADO (`synapse`)" (M8 §4 L402 — el CLI unificado se
invoca como `synapse`; M8 §9 criterio de aceptación L565: "El flag funciona
correctamente y no genera binario", verificado con
`pytest tests/integration/test_cli_check.py -v`).
implementacion: `synapse.exe` = COPIA byte-idéntica de synapse_stage2.exe
(mismo compilador, `GetModuleFileNameA` resuelve runtime junto al exe):
mismo subcomando check, mismo rc, main de biblioteca sin efecto colateral
(D-R150-4). synapse.exe es artefacto ignorado (.gitignore L28) — el
entorno de release/installer es quien lo despliega (M8 §4; instalación
bin/ de Fase 30).
// cumple Manual 8 §4 (ME check_cli R3)
oraculo: tests/auditoria/test_oraculos_check_cli.py (test_r3)

## R4 — check_test_oraculo: oráculo E2E del ME
requisito: Manual 2 §12
texto: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |" (tabla M2 §12 — pruebas obligatorias de la etapa;
la etapa exige su oráculo).
implementacion: `tests/auditoria/test_oraculos_check_cli.py`: (r1) nativo
stage2: check --no-emit válido rc=0, inválido rc!=0, sin binario de salida;
(r2) cli.py check parity ambas rc; (r3) binario synapse.exe fresco + check
rc=0/valid, rc!=0/inválido, sin binario. E2E real vía stage2/cli.py, sin
mocks; anti-fabricación: exige binario fresco (mtime >= fuentes nucleo) y
rechaza "Uso: ... check" tratado como archivo.
// cumple Manual 2 §12 (ME check_cli R4)
oraculo: tests/auditoria/test_oraculos_check_cli.py

## TDD/MTO (dirección del Arquitecto, sesión 2026-10-03)
- RED: `synapse check --no-emit` hoy: el dispatcher nativo NO reconoce el
  subcomando (cae al pipeline de compilación → "Error de compilacion", rc=2
  porque "check" no es un archivo) — verificado probe. El test inmutable
  test_cli_check (M8 §9) FALLA por binario ausente. Implementación GREEN.
- El test de integración NO se toca (código la deuda, no el test).
- MTO: el oráculo del ME cita el criterio OBL del M8 §9 (tabla M8 §9 L565).

## Verificación global
- unit 514✓; nucleo 30✓; matriz 35✓; fase2 familia intacta (10✓/1✗ r27).
- bootstrap S1→S2 regenerado (principal.syn cambia).
- verificar_alineacion.py 0 brechas; contrastar gate; commit; docs post-commit.
