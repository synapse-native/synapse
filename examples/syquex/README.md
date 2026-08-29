# Ejemplos de Syquex

Esta carpeta contiene ejemplos del lenguaje Syquex que cubren las features principales.

## Ejemplos

| Archivo | Feature | Manual |
|---|---|---|
| `04_resultado.syq` | Manejo de errores con condicionales | Manual 2 §8.3 |
| `05_estructuras.syq` | Structs con campos | Manual 2 §2 |
| `06_concurrencia.syq` | Canal básico | Manual 5 §3 |
| `07_memoria.syq` | Structs y gestión de memoria | Manual 4 §2 |
| `08_ownership.syq` | Ownership y borrowing | Manual 2 §9 |
| `python_pipeline/fibonacci.syq` | Fibonacci (pipeline Python→Syquex) | — |
| `counter/test_counter.syq` | Contador básico | — |

## Compilación

```bash
./synapse_stage3.exe <ejemplo>.syq <ejemplo>.exe
```

## Notas

- Los ejemplos usan `let` para declaraciones (Manual 2 L134)
- `coincidir` con Resultado ADT requiere codegen pendiente (deuda D-2)
- Canales tipados y `lanzar`/`escuchar` requieren implementación pendiente
