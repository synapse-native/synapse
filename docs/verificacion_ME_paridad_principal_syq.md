# Verificación ME — paridad_principal_syq (gate MTS fase 4b, auditoria/contrastar.py)

# Commit: 90eb18c
# Scope: retirada de 2 stubs de `principal` obsoletos (pipeline.py H-R90-8b + puente ME-R90-8)
# que contaminaban el AST canónico del camino .syq → 4 warps de paridad estructural.
# Base: 121153d. Huella del cambio: 907275bc6b04e287.

Manual 1 §3.1 — R1 CUMPLE (pipeline.py compilar_desde_syq L605: retirada la inyección del
stub `funcion principal()` en el source (tempfile H-R90-8b); el frontend recibe la ruta REAL;
probe: el exe syq_frontend preserva las funciones locales sin principal — pretexto
"runtime S1 filtra funciones" FALSO con el frontend actual). Oráculo:
tests/integration/test_paridad_syn_syq.py 6/6 PASSED (antes 4 FAILED).

Manual 1 §3.1 — R2 CUMPLE (puente_canonico.py plano_a_programa L649: retirado el fallback
ME-R90-8 que añadía DefinicionFuncion(nombre='principal') al AST; el entry point es OPCIONAL
en .syq (M3 §3 L78) y el generador emite main de biblioteca sin principal
(H-R90-8/D-R150-4). Imports DefinicionFuncion/SentenciaRetornar siguen en uso L341/L357).
Oráculo: tests/integration/test_paridad_syn_syq.py 6/6 PASSED.

Manual 1 §3.1 — R3 CUMPLE (paridad estructural RESTAURADA: ser(Programa_syn) ==
ser(Programa_syq) para los 6 pares de fixtures — 4 warps CERRADOS:
struct_and_constant, control_flow, coincidir_basic, test_si_sino_paridad). E2E dual:
.syq con principal ejecuta rc=7 (q.x, estructura+campo); .syq de biblioteca SIN principal
compila/enlaza/ejecuta rc=0 (main de biblioteca, D-R150-4). Oráculo:
tests/integration/test_paridad_syn_syq.py 6/6 PASSED.

Gates: alineacion.py --verificar → 0 brechas (evidencia
auditoria/evidencia/907275bc6b04e287.json); verificar_alineacion.py → SIN BRECHAS;
contrastar --plan → 3 requisitos, 1 oráculo release GREEN; lectura previa verificada
(M1 §3.1 + M3 §3 + M1 §7.2, 2 archivos).

CUMPLE
