# El Ecosistema Axon

Axon es el gestor de paquetes y sistema de módulos de Synapse.

## Manifiesto (`axon.toml`)

```toml
[paquete]
nombre = "mi-proyecto"
version = "0.1.0"

[dependencias]
std = { git = "https://github.com/synapse-native/synapse" }
```

## Bloqueo (`axon.lock`)

Las dependencias se inmutabilizan mediante hashes SHA-256, garantizando builds reproducibles.

## Importar módulos

```synapse
importar std.io
importar std.json
importar std.net
importar std.math
```
