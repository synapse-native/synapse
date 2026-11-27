# Plan ME f32_4b_cita_principal — Re-anclar cita de nucleo/principal.syn

> **Resolución (2026-09-17):** este ME se consolidó dentro de
> ME r149_reparacion (mismo working tree / mismo cambio_hash 94c9b9fff045f0e2).
> El expediente vigente es `docs/alineacion/r149_reparacion.md` (bloque
> `nucleo/principal.syn`): la cita heredada `Manual 3 §12.1: CLI debe aceptar -o`
> quedó como DESVIACION con decisión D-R149-1 y el ancla real es
> `Manual 1 §3.1` (pipeline del compilador unificado, nucleo/principal.syn:887).

## Requisito 1: CLI debe aceptar -o
requisito: Manual 1 §3.1 — CLI debe aceptar -o para ruta de salida
texto: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn)"
implementacion: Comentario // cumple Manual 1 §3.1 en nucleo/principal.syn línea 887 (la cita Manual 3 §12.1 original era fabricada: §12.1 no existe, Manual 3 termina §12 sin subsecciones; corregida a sección real)
oraculo: tests/nucleo/test_lint.py
