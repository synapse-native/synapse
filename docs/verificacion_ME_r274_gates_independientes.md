# Verificación ME r274 — gates independientes

**Fecha:** 2026-11-20
**Plan:** `docs/plan_ME_r274_gates_independientes.md`
**Oráculo:** `auditoria/oraculos/oraculo_r274_gates_independientes.py`

> Este expediente faltaba: el reporte R274 original afirmaba «expediente
> sellado» sin que existiera archivo alguno. Se crea con la evidencia medida.

## Manual 9 §6.1 CUMPLE — bootstrap de 3 etapas con diff 0 bytes

Cita literal: "□ **Bootstrap exitoso**: en cada target, el proceso de bootstrap
de 3 etapas produce `diff 0 bytes` entre Stage 2 y Stage 3."

Evidencia medida (`oraculo_r274_gates_independientes.py`):

```
[i] synapse_stage2.exe sha256 49d7c51ac63e28a6 (2573663 bytes)
[i] synapse_stage3.exe sha256 49d7c51ac63e28a6 (2573663 bytes)
[OK] bootstrap determinista: S2==S3 (diff 0 bytes, 2573663 bytes, 49d7c51ac63e28a6)
```

## Manual 9 §6.2 CUMPLE — el pipeline ejecuta la verificación del bootstrap

Cita literal: "El pipeline de CI/CD ejecuta automáticamente:" / "- La
verificación del bootstrap (diff 0 bytes)."

Evidencia: `.github/workflows/ci-tests.yml`, job `bootstrap`, paso
«Gate independiente de bootstrap (oráculo r274)», inmediatamente después de
generar las 3 etapas. El paso invoca el oráculo sin `--sin-oraculos`; si el
oráculo falla, el job falla.

## Manual 1 §7.4 CUMPLE — bootstrap determinista y hash SHA-256

Cita literal: "En caso de modificaciones en el compilador base, verificación de
bootstrapped determinista (`diff 0 bytes` entre Stage 2 y Stage 3)." /
"Generación automática de hash SHA‑256."

Evidencia:

```
$ python auditoria/oraculos/oraculo_r274_gates_independientes.py --estricto
[r274] PASS: gate determinista verificado (Manual 1 §7.4, Manual 9 §6.2)
[r274] PASS: los binarios distribuidos corresponden a la etapa 2

$ python auditoria/oraculos/oraculo_r274_gates_independientes.py --mutar
[r274] [OK] mutación de contenido detectada por el sello (9e72e10c716dfc01 -> 70b9e74aab612b6f)
```

`--mutar` trabaja sobre un archivo temporal: `git status --short
nucleo/principal.syn` queda vacío (el árbol no se toca).

## Manual 9 §6.3 CUMPLE — firma `.sig` y hash por artefacto

Cita literal: "Archivo de firma (`.sig`) para cada binario/instalador." /
"Archivo `.sha256` con el hash del artefacto."

Evidencia (resuelve H-R274-1):

```
$ python distribuir.py --requerir-firma
[distribuir] firma verificada: synapse.exe.sig
[distribuir] firma verificada: MANIFEST.sha256.sig
[distribuir] OK 19 artefactos … SIGNATURE_VALID=YES

$ python auditoria/oraculos/oraculo_r274_gates_independientes.py --firmas
[r274] [OK] firmas Ed25519 verificadas: 6 artefactos distribuidos
[r274] PASS: firmas Ed25519 de la distribución verificadas (Manual 9 §6.1, §6.3)

$ printf 'X' >> instaladores/dist/distribucion/install.sh  # manipulación
$ python … --firmas
[r274] [FAIL] firma Ed25519 INVÁLIDA: install.sh                       (rc=1)
```

Manual 9 §6.1 («Firmas Ed25519: todos los artefactos distribuidos están
firmados y verificados») queda cubierto por `--firmas`, incluido en
`--estricto`. Regresión: `tests/auditoria/test_oraculo_r274_firmas.py` 4/4
(firmada, manipulada, sin firma, sin distribución).

## Evidencia de gates

- `contrastar --plan docs/plan_ME_r274_gates_independientes.md` → 3/3 requisitos, oráculos ejecutados, rc=0.
- `verificar_alineacion.py` → SIN BRECHAS.
