# Plan ME: Expandir ejemplos Syquex

## Problema

`examples/syquex/` tiene solo 3 archivos mínimos (counter=retornar 42, fibonacci básico).
Fase 22 completada pero los ejemplos no cubren las features principales de Syquex.

## Requisitos

requisito: Manual 2 §8.3
texto: "Tipos Algebraicos de Datos: Resultado<T,E> y Opcion<T>"
implementacion: ejemplo 04_resultado.syq que use coincidir con ok/err.
oraculo: examples/syquex/04_resultado.syq compila con stage3

requisito: Manual 2 §2
texto: "estructuras con métodos y constructores"
implementacion: ejemplo 05_estructuras.syq con metodo, crear, campos.
oraculo: examples/syquex/05_estructuras.syq compila con stage3

requisito: Manual 5 §3
texto: "Canales: canal(T), ch <-, ch ->"
implementacion: ejemplo 06_concurrencia.syq con canal y fibras.
oraculo: examples/syquex/06_concurrencia.syq compila con stage3

requisito: Manual 4 §3.2
texto: "rc<T> / arc<T> reference counting"
implementacion: ejemplo 07_memoria.syq con rc y débil.
oraculo: examples/syquex/07_memoria.syq compila con stage3

requisito: Manual 2 §9
texto: "Ownership & Borrowing"
implementacion: ejemplo 08_ownership.syq con préstamo inmutable/mutable.
oraculo: examples/syquex/08_ownership.syq compila con stage3

## Cambios

| Archivo | Cambio |
|---|---|
| `examples/syquex/04_resultado.syq` | NUEVO: Error handling con Resultado |
| `examples/syquex/05_estructuras.syq` | NUEVO: Structs con métodos |
| `examples/syquex/06_concurrencia.syq` | NUEVO: Canales y fibras |
| `examples/syquex/07_memoria.syq` | NUEVO: rc/débil reference counting |
| `examples/syquex/08_ownership.syq` | NUEVO: Ownership y borrowing |
| `examples/syquex/README.md` | Actualizar con lista de ejemplos |

## Validación

1. `./synapse_stage3.exe <ejemplo>.syq <ejemplo>.exe` — cada ejemplo compila
2. `python auditoria/verificar_alineacion.py` — 0 brechas
3. `python auditoria/contrastar.py --plan docs/plan_ME_syquex_examples.md` — gate
