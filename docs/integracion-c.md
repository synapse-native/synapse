# Integración con C

Synapse expone FFI directo con C mediante la palabra clave `externo`:

```synapse
externo funcion puts(s: char*) -> entero
externo funcion malloc(tamano: entero) -> char*
externo funcion free(-> ptr: char*) -> nulo
```

Los tipos se mapean automáticamente:

| Synapse | C |
|---|---|
| `entero` | `int64_t` |
| `decimal` | `double` |
| `texto` | `CadenaSegura` (struct con ptr + len) |
| `logico` | `bool` |

Para operaciones que requieren punteros crudos, Synapse provee `BloqueInseguro`:

```synapse
BloqueInseguro:
    buf = malloc(64)
    // operaciones con punteros
    free(-> buf)
```
