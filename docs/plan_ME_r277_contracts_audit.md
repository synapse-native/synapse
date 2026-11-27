# Plan ME r277_contracts_audit

**Fase del roadmap:** Frente H, P1 tras r276.
**Micro-entregable:** `r277_contracts_audit`.
**Depende de:** —.
**Manuales:** Manual 2 §5.1, Manual 2 §12.

> Alcance real. El manual hace de `requiere`/`garantiza` una promesa central del
> lenguaje (Manual 2 §5.1) y les asigna prueba obligatoria (Manual 2 §12), pero
> no existía ninguna medición de cuántas funciones públicas los declaran. La
> medición de hoy: **600 funciones públicas de producción sin ambos contratos en
> 68 archivos** (`nucleo/generator.syn` 36, `nucleo/analizador_semantico.syn` 34,
> `nucleo/lexer.syn` 26, …). Escribir 600 precondiciones/postcondiciones
> significativas en una sesión sería inventar contratos — exactamente lo que el
> propio ME prohíbe. Por eso este ME entrega el **gate con ratchet**: mide la
> deuda, la congela en un baseline y **falla ante cualquier función pública
> nueva sin contratos**; la quema queda registrada con resolución asignada
> (H-R277-1) y `--estricto` es el criterio de cierre final.

---

requisito: Manual 2 §5.1
texto: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
implementacion: `auditoria/verificar_contratos.py` escanea las funciones públicas (sin prefijo `_`, archivos sin prefijo `_`) de `nucleo/`, `std/`, `opensyn/`, `syquex/`, `lib/` y `runtime/` y reporta las que no declaran `requiere:` **y** `garantiza:`. Las declaraciones `externo` (FFI) se cuentan como exentas, no se les inventan contratos. La deuda histórica queda en `auditoria/contratos_baseline.txt` (`ruta::nombre`, regenerable sólo con `--baseline`); el modo normal falla si aparece una violación nueva y `--estricto` falla ante cualquier violación. `--resumen` da la deuda por archivo y `--json` deja evidencia.
oraculo: auditoria/verificar_contratos.py

requisito: Manual 2 §12
texto: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
implementacion: el gate se cablea como job `contratos` de `.github/workflows/ci-tests.yml` (necesita `lint-and-check`), de modo que un commit con `--no-verify` no mergea sin pasar la auditoría. La prueba de comportamiento existente `pytest tests/integration/test_contracts.py` sigue al 100% (5/5, no se toca), y se añade regresión propia del gate `tests/auditoria/test_verificar_contratos.py` (4 casos: verde con contratos completos, rojo con contrato incompleto, baseline congela deuda y `--estricto` la rechaza, FFI y privadas exentas).
oraculo: tests/auditoria/test_verificar_contratos.py

## Criterio de cierre de este ME

1. `python auditoria/verificar_contratos.py` → `OK`, 0 violaciones nuevas contra
   el baseline (`600` deuda registrada, `561` FFI exentas, `1161` auditadas).
2. `pytest tests/auditoria/test_verificar_contratos.py` 4/4 y
   `pytest tests/integration/test_contracts.py` 5/5.
3. Job `contratos` presente en `ci-tests.yml` y ejecutando el gate.
4. `contrastar --plan docs/plan_ME_r277_contracts_audit.md` PASS;
   `verificar_alineacion.py` 0 brechas.
5. H-R277-1 abierto con la deuda y su resolución (quema por archivo hasta
   `--estricto` en verde). Este ME **no** declara 0 contratos faltantes: declara
   deuda medida, congelada y con el gate impidiendo que crezca.
