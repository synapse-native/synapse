# Fase 17 — PGO/LTO Pipeline Completo + Release Flags

## Estado: COMPLETADA ✓

## Resumen
Fase 17 implementa Profile-Guided Optimization (PGO) y Link-Time Optimization (LTO) conectando
el módulo `generator_pgo.syn` al generador de código C nativo (`generator.syn`), y unificando
los flags de optimización `--release`/`--debug`/`--profile` entre `principal.syn` y `pipeline.py`.

## Cambios

### 1. Release/Debug Flags Unificados (`nucleo/principal.syn`)
- **Antes**: gcc command hardcodeaba `-O2` (`gcc -O2 %s ...`).
- **Después**: detecta `--release` (`-O3 -flto -DNDEBUG`, Manual 1 §165) y `--debug`
  (`-O0 -g -fsanitize=address,undefined -fno-omit-frame-pointer`, Manual 8 §4.2).
- Paridad con `pipeline.py` que ya tenía `--release`/`--debug` flags (F17-flags, commit `eda73c8`).

### 2. `--profile` Flag Fix (`nucleo/principal.syn:611`)
- **Bug**: `_pa.longitud > 9` excluía `--profile` (longitud 9) — el flag nunca se activaba.
- **Fix**: cambiado a `>= 9`. Ahora `--profile release-pgo` inyecta `-fprofile-generate`,
  y `--profile release-pgo-use` inyecta `-fprofile-use -flto`.

### 3. Instrumentación PGO en Código Generado (`nucleo/generador/`)
- `nucleo/generador/nodos_flujo.syn`: conecta `pgo_emitir_incremento_bb(est)` en las
  fronteras de bloques `if-true`, `if-else`, `while`, `for`.
- `nucleo/generador/orquestador.syn`: llama `pgo_inicializar()` al inicio de `generar()`.
- `nucleo/generador/recorrido.syn`: llama `pgo_finalizar(est)` antes del `main()` generado,
  y `pgo_registrar_atexit(est)` dentro de `main()` después de `pool_init()`.

### 4. Emisión PGO Correcta (`nucleo/generator_pgo.syn`)
- `pgo_emitir_incremento_bb`: emite `extern uint64_t __pgo_counter_N;` + `__pgo_counter_N++`
  (declaración extern para acceso global, definición en `pgo_finalizar`).
- `pgo_emitir_volcado`: emite definiciones globales `uint64_t __pgo_counter_N = 0;` +
  función `__pgo_dump()` que volca a `synapse.profdata` en CSV.
- `pgo_finalizar`: **siempre** emite `__pgo_dump` (aunque `total == 0`), para que
  `atexit(__pgo_dump)` sea válido en todos los programas.
- `pgo_registrar_atexit`: emite `extern void __pgo_dump(void);` forward declaration
  antes del `atexit()`, evitando enlaces rotos.

## Validación

### Bootstrap S2==S3 (Manual 9 §9.7)
```
S2 sha256: cca44227a60313f62efe79ea697855fff77e641cb4ffd66bb343f6a26428a4ae
S3 sha256: cca44227a60313f62efe79ea697855fff77e641cb4ffd66bb343f6a26428a4ae
S2==S3: BYTE-IDENTICAL
```

### Pipeline PGO Completo
- **Step 1** (Instrumentado): `synapse_stage2.exe nucleo/principal.syn .pgo/synapse_pgo_instr.exe --profile release-pgo`
  → gcc command: `gcc -O2 -fprofile-generate ...`
- **Step 2** (Entrenamiento): ejecutar binario instrumentado sobre archivos .syn
  → 23 arvhivos `.gcda` generados
- **Step 3** (Optimizado): `synapse_stage3.exe nucleo/principal.syn .pgo/synapse_pgo_opt.exe --profile release-pgo-use`
  → gcc command: `gcc -O2 -fprofile-use -flto ...`
  → Tamaño: 1,735,458 bytes → 1,075,704 bytes (**38% reducción**)

### Validación de Binario PGO-Optimizado
- El binario `synapse_pgo_opt.exe` compila correctamente programas usuarios
- El programa `test_pgo.sol` (con `mientras`/`si`) produce código PGO instrumentado:
  - `extern uint64_t __pgo_counter_N;` en fronteras de bloques
  - `void __pgo_dump(void)` definido globalmente
  - `atexit(__pgo_dump)` dentro de `main()`
- Ejecución produce `synapse.profdata` con contadores de hot/cold paths

### Verifier
```
RESULTADO: SIN BRECHAS — trazabilidad verificada
```

## Archivos Modificados
- `nucleo/principal.syn` — flags release/debug/profile unificados
- `nucleo/generator_pgo.syn` — emisión PGO corregida (extern/extern def)
- `nucleo/generador/nodos_flujo.syn` — instrumentación PGO en visitantes
- `nucleo/generador/orquestador.syn` — `pgo_inicializar()` en `generar()`
- `nucleo/generador/recorrido.syn` — `pgo_finalizar()` + `pgo_registrar_atexit()`
- `nucleo/generator.syn` — regenerado (289,514 chars)

## Deuda Técnica Registrada (regla 9 — todo hallazgo se resuelve o se registra)
- **D-T1 (preexistente, Fases 8-11):** Warning GCC `integer overflow in expression`
  en `synapse_unity.c:12402` (`(long long)9223372036854775807LL + 1` → INT64_MIN).
  En emisión de literal `-9223372036854775808` por `_oo_expr_a_c`.
  **Resolución asignada:** sanitizar en `_oo_expr_a_c` (emitir literal directamente
  sin `+ 1`); prioridad baja, registrada en `MEMORIA_PROYECTO.md` §D-T1.
- **D-T2 (preexistente, Fases 8-11):** Warning LTO `_toml_parse` type mismatch:
  `struct NodoToml _toml_parse(CadenaSegura)` (extern en `synapse_unity.c:283`) vs
  `NodoToml _toml_parse(CadenaSegura)` (`runtime/core/toml.c:261`).
  **Resolución asignada:** añadir `-fno-strict-aliasing` al gcc command (`principal.syn:665`,
  `pipeline.py:637`) o alinear declaraciones; prioridad baja, registrada en
  `MEMORIA_PROYECTO.md` §D-T2.
