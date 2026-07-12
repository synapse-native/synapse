# Librería Estándar (Sysroot)

La librería estándar incluye:

| Módulo | Descripción |
|---|---|
| `std.io` | Entrada/salida por terminal (`escribir`, `leer_linea`) |
| `std.mem` | Gestión de memoria raw (`reserva`, `libera`) |
| `std.net` | Sockets TCP cliente (`conectar`, `enviar`, `recibir`) |
| `std.json` | Parseo de JSON (`desde_texto`, `obtener_campo`) |
| `std.toml` | Parseo de TOML |
| `std.math` | Operaciones con tensores (`crear_tensor`, `producto_punto`, `relu`) |
| `std.err` | Tipos algebraicos (`Resultado`, `Opcion`) |

Todas las funciones que asignan recursos requieren liberación explícita mediante transferencia de ownership:

```synapse
importar std.json

nodo = desde_texto("{\"clave\": \"valor\"}")
escribir("campo: ", obtener_campo(nodo, "clave"))
liberar_nodo(-> nodo)
```
