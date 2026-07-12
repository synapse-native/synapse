# El Pacto de Memoria

Synapse implementa un sistema de **ownership afín** (affine types) con **RAII determinista** —no hay recolector de basura, no hay borrow checker al estilo Rust, no hay reference counting. Cada valor tiene exactamente un propietario en cada momento, y el compilador inyecta automáticamente las llamadas a destructores cuando una variable sale de su ámbito.

## Ownership y Transferencia

El analizador semántico [analizador_semantico.syn](/src/analizador_semantico.syn) implementa una máquina de estados sobre cada símbolo. Cada variable tiene una bandera `vivo: booleano` que el compilador muta durante el análisis:

```synapse
estructura Simbolo:
    nombre: texto
    tipo: texto
    scope_nivel: entero
    vivo: booleano
```

Cuando se invoca `marcar_movido()`, el símbolo pasa a estado `vivo = falso`. Cualquier acceso posterior dispara un error semántico E-502:

```synapse
funcion marcar_movido(analizador: AnalizadorSemantico, nombre: texto) -> nulo:
    simbolo = buscar_simbolo(analizador, nombre)
    si simbolo.nombre != "":
        log("Moviendo variable: " + nombre)
        simbolo.vivo = falso

funcion validar_acceso(analizador: AnalizadorSemantico, nombre: texto) -> nulo:
    simbolo = buscar_simbolo(analizador, nombre)
    si simbolo.nombre == "" o simbolo.vivo == falso:
        error_semantico("Acceso a variable fuera de scope o movida")
```

### Transferencia explícita con `->`

La sintaxis de transferencia usa el operador `->` como prefijo del argumento:

```synapse
funcion liberar_nodo(-> n: NodoJson) -> nulo:
    _syn_json_liberar(n)
    retornar

funcion principal() -> nulo:
    nodo = desde_texto("[1, 2, 3]")
    liberar_nodo(-> nodo)   # ← transferencia de ownership
    # nodo ya no es accesible aquí — error E-502 en compilación
```

### Transferencia en retorno

```synapse
funcion generar_tensor() -> tensor:
    datos = reserva(64)
    retornar -> datos   # transfiere ownership al caller
```

## Cómo el generador inyecta C

El generador de código [generator.syn](/librerias/compiler/generator.syn) traduce cada asignación de variable en una declaración C con un scope determinista. Al final de cada bloque, inyecta código de limpieza que recorre los símbolos vivos y llama a sus destructores.

Para una función como:

```synapse
funcion procesar() -> nulo:
    a = reserva(16)
    b = reserva(32)
    liberar(-> a)
```

El generador produce C equivalente a:

```c
void procesar(void) {
    Bloque* _scope_1 = _push_scope();
    Bloque* _scope_2 = _push_scope();

    void* a = reserva(16);
    void* b = reserva(32);

    _pop_scope(&_scope_2);  // libera b (aún vivo en _scope_1)

    liberar(a);              // a se transfirió — desactivado manualmente

    _pop_scope(&_scope_1);  // a ya fue liberado, no se libera dos veces
}
```

`_pop_scope` itera la tabla de símbolos del ámbito y llama a `liberar_nodo()`, `_syn_texto_liberar()` o `_syn_cerrar_socket()` según el tipo de cada variable. Esto garantiza que **ningún recurso quede sin liberar**, incluso en presencia de retornos tempranos o excepciones.

La lista completa de destructores inyectados automáticamente vive en los módulos de la librería estándar —todo recurso que no se transfiera explícitamente con `->` recibe cleanup al salir de scope.

## Ejemplo real: JSON

Tomado de [tests/smoke_json.syn](/tests/smoke_json.syn):

```synapse
#lang: es
importar std.json

funcion principal() -> nulo:
    nodo = desde_texto("42")
    si nodo.tipo >= 0:
        log("entero OK")
    sino:
        log("FALLO entero")
    liberar_nodo(-> nodo)

    nodo = desde_texto("[1, 2, 3]")
    si nodo.tipo >= 0:
        log("array OK len=", nodo.longitud)
    sino:
        log("FALLO array")
    liberar_nodo(-> nodo)

    nodo = desde_texto("{mal}")
    si nodo.tipo < 0:
        log("error OK: ", nodo.valor_str)
    sino:
        log("FALLO: debio dar error")
    liberar_nodo(-> nodo)
```

Cada `desde_texto()` produce un `NodoJson` con memoria dinámica. Si no se llama a `liberar_nodo(-> nodo)`, el generador inyecta la liberación automática al salir de `principal()`. Si se llama, el símbolo se marca como movido y el destructor automático se omite —**doble free es imposible por construcción**.

## Seguridad Zero-Cost

El costo de todo este sistema es **cero en tiempo de ejecución**. No hay RCU, no hay atomicos, no hay contadores de referencia. La máquina de ownership opera exclusivamente en compilación. El binario generado ejecuta `malloc`/`free` directos sin capas intermedias.
