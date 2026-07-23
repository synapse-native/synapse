# Roadmap del Nuevo Generador Nativo (Modular)

## Estado Actual

`nucleo/generator.syn` → **`nucleo/generator_legacy.syn`** (en cuarentena).

El monolito legacy queda inactivo como referencia lógica. No se modificará más.

---

## Anti-patrones Documentados (Lecciones Aprendidas)

### Anti-patrón 1: Bloques `asm()` Masivos sin Seguridad de Tipos

**Problema:** ~200 bloques `asm()` dentro del generador legacy emiten código C crudo
con cadenas literales de tipo `const char*`. La función `gen_emitir_linea` exige
`CadenaSegura` (un struct pasado por valor), creando una incompatibilidad de tipos
que requirió parches complejos (`_L` macro, `_Generic`, `void*`).

**Lección:** El generador nativo NO puede usar `asm()` para emitir líneas de C.
La emisión debe hacerse mediante llamadas a funciones Synapse tipadas, donde el
compilador Synapse (Python) se encarga de la conversión string → `CadenaSegura`.

### Anti-patrón 2: Archivo Monolítico de ~1300 líneas

**Problema:** Un solo archivo con constantes, estado, 20+ visitantes, y emisores
embebidos (tokenizar, parsear, generar, volcar_ast). Cualquier error de sintaxis
en una función propagaba errores en cascada por todo el archivo.

**Lección:** Separar por responsabilidad: contexto (estructuras), emisión base,
visitantes de nodos, emisores especiales (tokenizar/parsear/generar).

### Anti-patrón 3: Fuga de Tipos entre `void*` y `CadenaSegura`

**Problema:** Cambiar el parámetro de `gen_emitir_linea` a `void*` para aceptar
tanto `CadenaSegura` como `const char*` rompió la escritura porque C no resuelve
el paso por valor de un struct frente a un puntero plano. El resultado fue
corrupción del buffer de salida.

**Lección:** La API de emisión debe ser estricta: `CadenaSegura` siempre. Cero
tolerancia a `void*` o despachos `_Generic`.

### Anti-patrón 4: Estado Global Compartido (`_G_*`, `_P_*`)

**Problema:** Variables globales sin `static` entre el AST Walker y el parser
embebido crean dependencias ocultas y colisiones de linker.

**Lección:** Centralizar en `GeneradorCEst` (estructura de estado única, pasada
como primer parámetro).

---

## Estructura de Módulos

```
nucleo/generador/
├── contexto.syn       ← Definiciones de estado y tipos (Fase 1)
├── emision_c.syn      ← API de escritura C de bajo nivel (Fase 1)
├── nodos_flujo.syn    ← Visitantes: si, mientras, para, coincidir (Fase 2)
├── nodos_tipos.syn    ← Visitantes: declaración, asignación, estructura (Fase 2)
├── nodos_expresiones.syn ← Evaluación de expresiones y llamadas (Fase 3)
├── nodos_especiales.syn  ← tokenizar, parsear, generar, volcar_ast (Fase 3)
└── orquestador.syn    ← Punto de entrada, despacho principal (Fase 4)
```

---

## Fases de Implementación

### Fase 1 — Base (ESTA TAREA)
- `contexto.syn`: Estructura `GeneradorCEst`, typedefs nombrados, constantes
- `emision_c.syn`: `gen_emitir_linea()`, `traducir_tipo_c()`, helpers de buffer

### Fase 2 — Control de Flujo y Tipos (Micro-tests 01, 02, 03)
- `nodos_flujo.syn`: Visitantes `si`, `mientras`, `para`, `retornar`, `coincidir`
- `nodos_tipos.syn`: Visitantes `declaracion`, `asignacion`, `estructura`, `constante`,
  `externo`, `importar_c`

### Fase 3 — Expresiones y Llamadas
- `nodos_expresiones.syn`: Evaluación de expresiones, llamadas, operadores,
  coerción de tipos, boxing/unboxing, log

### Fase 4 — Emisores Especiales e Integración
- `nodos_especiales.syn`: `gen_emitir_tokenizar_c`, `gen_emitir_parsear_c`,
  `gen_emitir_generar_c`, `gen_emitir_volcar_ast_c`
- `orquestador.syn`: `gen_visitar_nodo()`, integración con `principal.syn`

---

## Criterios de Aceptación

1. ✅ Micro-test `test_01_flujo.syn` compila con el nuevo generador nativo
2. ✅ Micro-test `test_02_tipos.syn` compila con tipos básicos
3. ✅ Micro-test `test_03_scope.syn` compila con scoping correcto
4. ✅ Todos los micro-tests generan código C que GCC compila sin errores
5. ✅ El compilador completo (self-hosted) puede compilar `principal.syn`

## Historial

| Fecha       | Cambio                                  |
|-------------|-----------------------------------------|
| 2026-07-23  | Cuarentena de generator.syn legacy      |
| 2026-07-23  | Creación de nucleo/generador/ (Fase 1)  |
