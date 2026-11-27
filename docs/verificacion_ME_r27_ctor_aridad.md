# Verificación ME r27_ctor_aridad (R179) — H-R177-1

**Base:** 97b3728 (R178). **Commit:** (post-commit). **Método:** MTS + TDD + MTO.

## Marcas por requisito

- Manual 2 §2 poblar `SemEstructuraInfo.total_campos` contando la cadena de NODO_PARAMETRO vía slot [6] (nucleo/analizador_semantico.syn:806, oráculo test_oraculos_r27_ctor_aridad.py r1/r4, probes `Punto(1,2)`→`12` y `Punto()`→`0`): CUMPLE
  - Acceso canónico slot [6] (patrón de registro ADT de `analizar_paso_estructuras`); lección H-R179-1: no usar el miembro `hijo_izq` del struct SemNodo.

- Manual 2 §8.2 restaurar check de aridad del ctor de struct con paridad exacta S1 (nucleo/analizador_semantico.syn:733, oráculo test_oraculos_r27_ctor_aridad.py r2/r3, probe `Punto(1)`→rc=7 "Cantidad de argumentos invalida para 'Punto': se esperaban 2", paridad S1 rc!=0): CUMPLE
  - H-R153-4: `Struct()` o `Struct(c1..cn)`, n = campos; otros → ERR_SEM_ARGUMENTOS_INVALIDOS rc=7. H-R153-4b queda SUPERADA (la metadata que faltaba ahora se puebla).

- Manual 7 §2.3 test r27 alineado de la forma pre-r153 deprecada a la ley vigente via TDD/MTO (tests/integration/test_fase2_nativa_hm.py: test_r27_struct_ctor_posicional_valido + test_r27_struct_ctor_aridad_invalida_rechazada, 3/3 PASSED con `-k r27`): CUMPLE
  - Regla 5: el test se alinea al manual, no al revés; mapeo OBL-M2-05 del MTO; se agrega cobertura del caso válido que no existía.

- Manual 2 §12 oráculo E2E del ME con bootstrap real, sin sniff (tests/auditoria/test_oraculos_r27_ctor_aridad.py, 4/4 PASSED en 144 s): CUMPLE

## Bootstrap y regresión ejecutada (timestamps frescos 2026-10-04)

- Stage1 rc=0 08:19; Stage2 rc=0 08:20 (auto-compilación del compilador pasa
  CON el check activo: 37747 nodos, cero falsos positivos).
- Probes /tmp/probe_r27: r27_ok `12` rc=0; r27_bad rc=7 msg paridad;
  r27_zero `0` rc=0.
- Regresión: oráculo 4/4 (144 s); fase2 `-k r27` 3/3; fase2 muestra
  `-k "r9 or r20 or f37 or f313"` 13✓; oráculo R177 5✓; oráculo R178 4✓;
  unit 514✓; micro+nucleo+synapse 30✓; matriz 35✓.

## Hallazgos del ME

- **H-R179-1 (cerrado en este ME):** el patrón de registro ADT usa el slot [6]
  del nodo plano (`nodo_expr()`), NO el miembro `hijo_izq` del struct SemNodo,
  pese a que el puente lee `hi = ((int*)&nodos[i])[8]` para el mismo nodo.
  La primera implementación de R1 usó `hijo_izq` y contó 0 campos para todo →
  el check rechazó la auto-compilación (rc=7 en stage2) — detectado por el
  propio bootstrap y corregido al accessor canónico. Lección: en el analizador
  nativo los recorridos de hijos DEBEN usar los accessors (`nodo_expr`,
  `nodo_hijo_izq`) o el slot verificado por el patrón existente, nunca el
  miembro del struct asumido.

## Deuda bloqueada restante (decisión Arquitecto)

- **H-R177-2:** parser nativo de `coincidir` sin literales/wildcard (S1 los
  acepta vía H-R90-6). No abordada en R179 (alcance separado).
