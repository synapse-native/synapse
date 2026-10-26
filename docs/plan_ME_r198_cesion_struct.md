# PLAN ME r198_cesion_struct — cesión texto→campo de struct (cierre H-R197-1)

**Causa raíz (H-R197-1)** repro determinista del E2E instalador (2026-10-25):
`estructura ModeloInfo.ruta = texto` — asignar el resultado de un concat a un
campo de struct marcaba el campo, no el origen; el emisor RAII del scope
liberaba el origen local (`_syn_texto_liberar(p)` en `armado`) y el slab TLS
recicla el buffer → el siguiente concat corrompía el campo (`ruta` con NUL al
aire en `~/.opensyn/opensyn.toml`).

requisito: Manual 2 §5.1 — la cesión de propiedad transfiere la titularidad al
DESTINO (el campo), el ámbito no libera lo cedido; semántica de consumo
H-R182c-1 (ArgumentoTransferido) extendida de args a asignación-campo.
Paridad: Manual 1 §3.1 (M1 S3.1) — ambos emisores S1 y nativo comparten la
misma semántica RAII.

## R1 — S1: transferir la marca al ORIGEN en asignación a campo de struct

texto: compilador/generator/emit_declarations.py `visitar_asignacion_campo`:
cuando el destino es `struct Campo = <expr texto>` → marcar el ORIGEN
TRANSFERIDO (omitirlo del cleanup del scope, igual que la marca en llamada
H-R182c-1). Ancla: `// cumple Manual 2 §5.1 (ME r198)`.
implementacion: emit_declarations.py + comentar (2 sitios: origen local y tmp).
oraculo: auditoria/oraculos/oraculo_r198_cesion.py — (A1) probe
recompila rc=0; (A2) el C emitido NO libera `p` en `armado`; (A3) salida
íntegra `pre:…ruta…gguf:post`, rc=0.

## R2 — nativo: paridad en `gen_visitar_asignacion_campo` + resello

texto: nucleo/generador/nodos_flujo.syn `gen_visitar_asignacion_campo` — misma
marca sobre el origen. Resello: `python nucleo/_rebuild_generator.py` regenera
nucleo/generator.syn (lección H-R180-2). Ancla: `// cumple Manual 2 §5.1`.
implementacion: nodos_flujo.syn + generator.syn (regenerado).
oraculo: mismo oráculo (A1–A3) + py_compile OK de generator.syn.

## Deuda nueva derivada (con seguimiento en plan_maestro_deudas)

- H-R196-3 (preexistente, continua): `garantiza` sobre el valor de retorno
  texto evalúa con `_resultado_` después del cleanup del pool — test fixture
  probe de contratos rc=127 (antes 0xC0000374), falla limpia pero falla.
- NUEVA: compilación S1 de opensyn/principal.syn falla — `garantiza:
  longitud(resultado)` NO se renombra a `_resultado_` (C "did you mean
  '_resultado_'") y en otra función el `garantiza` roba el `_resultado_` de
  tipo int64: el emisor de contratos S1 necesita resolver el símbolo del
  valor de retorno por tipos, no por nombre de variable. Resolución asignada:
  ME r198b (emisor de contratos).

## Checklist de cierre (fase 4b + 5)

- `auditoria/alineacion.py --nuevo --me r198_cesion_struct` → expediente
- `contrastar.py --plan docs/plan_ME_r198_cesion_struct.md` RC=0
- `verificar_alineacion.py` SIN BRECHAS
- suite instalador (familia afectada) passed; E2E real con ruta íntegra
