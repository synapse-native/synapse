# Synapse: Referencia Exhaustiva de la Librería Estándar (STD)

## 1. Módulo: `std.io` (Entrada y Salida Fuerte)
Provee acceso seguro a descriptores de archivo y consola. Nunca lanza excepciones fatales (panics); siempre retorna un `Resultado`.

* **`escribir_linea(mensaje: cadena) -> nulo`**
  Escribe la cadena en `stdout` seguida de un salto de línea (`\n`). Es atómica; múltiples hilos llamando a esta función no intercalarán caracteres.

* **`leer_archivo(ruta: cadena) -> Resultado<cadena, CadenaSegura>`**
  Abre un archivo en modo lectura estricta.
  * *Éxito:* Retorna `ok(datos)` con el contenido completo.
  * *Fallo:* Retorna `err(motivo)` si no existe, no hay permisos, o el archivo está bloqueado por otro proceso.

* **`escribir_archivo(ruta: cadena, datos: cadena) -> Resultado<booleano, CadenaSegura>`**
  Sobrescribe el archivo si existe, lo crea si no.

## 2. Módulo: `std.concurrencia` (Canales)
Primitivas de sincronización sin estado compartido.

* **`crear_canal() -> Canal<T>`**
  Instancia un canal síncrono. El tipo `T` es inferido por el primer uso.

* **`Canal.enviar(valor: T) -> nulo`**
  Inyecta un valor en el canal. Transfiere el *ownership* (posesión) del valor enviado. Bloquea el hilo actual hasta que el receptor lea el dato.

* **`Canal.recibir() -> Resultado<T, CadenaSegura>`**
  Lee el siguiente valor del canal.
  * *Éxito:* `ok(valor)`.
  * *Fallo:* `err("Canal cerrado")` si el hilo emisor colapsó o cerró el canal explícitamente. Evita deadlocks por abandono.

## 3. Módulo: `std.err` (ADTs Base)
Inyectado automáticamente en el *prelude*.

* **`Opcion<T>`**
  Variantes: `algun(T)`, `ninguno`.
* **`Resultado<T, E>`**
  Variantes: `ok(T)`, `err(E)`.

* **Método `.desempaquetar() -> T` (Solo para desarrollo):**
  Extrae el valor de un `ok` o un `algun`. Si contiene un error o está vacío, aborta el programa inmediatamente (`SIGABRT`). Prohibido en código de producción auditado.