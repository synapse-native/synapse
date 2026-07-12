# Concurrencia Zero-Copy

Synapse no expone memoria compartida, mutexes ni locks. El único mecanismo de concurrencia son los **canales** con **transferencia de ownership**: enviar un valor por un canal mueve la propiedad del emisor al receptor sin copiar memoria.

## Canales

Un canal se declara con el tipo del mensaje que transporta:

```synapse
canal: CanalConcurrencia* = crear_canal()
```

O con tipo explícito:

```synapse
canal: Canal<entero> = canal_nuevo()
```

### Envío: `<-`

El operador `<-` envía un valor al canal. La variable origen **pierde ownership** inmediatamente:

```synapse
valor = 42
canal <- valor       # valor ya no es accesible aquí
# log(valor) → error E-502: use-after-move
```

### Recepción: `->`

El operador `->` recibe del canal y otorga ownership al receptor:

```synapse
resultado = canal ->     # recibe ownership del mensaje
```

El receptor puede usar `coincidir` para manejar el cierre del canal:

```synapse
coincidir resultado:
    ok(v) => log("recibido: ", v)
    error => log("canal cerrado")
```

## Transferencia de ownership entre hilos

Tomado de [tests/falla_semantica.syn](/tests/falla_semantica.syn), que demuestra el error E-502 al usar una variable después de enviarla por un canal:

```synapse
funcion principal() -> nulo:
    paquete = "datos_confidenciales"
    ch <- paquete
    log(paquete)              # ← E-502: variable movida
```

El analizador semántico detecta que `paquete` fue transferido al canal en `ch <- paquete` y rechaza el acceso posterior. Esto previene **data races por construcción**: nunca puede haber dos hilos escribiendo o leyendo la misma dirección de memoria porque la propiedad es única y se transfiere atómicamente en la operación de canal.

## Productor-Consumidor con `lanzar`

La palabra clave `lanzar` crea un hilo ligero (fibra/os-thread). Combinada con canales, forma el patrón productor-consumidor sin estado compartido:

Tomado de [tests/test_metal.syn](/tests/test_metal.syn):

```synapse
#lang: es

funcion productor(ch: Canal<entero>) -> nulo:
    i: entero = 0
    mientras i < 10:
        ch <- i
        i = i + 1
    cerrar_canal(-> ch)

funcion consumidor(ch: Canal<entero>) -> nulo:
    valor: entero
    mientras recibir(ch, -> valor) == 0:
        log("consumido: ", valor)

funcion principal() -> nulo:
    ch = canal_nuevo()
    lanzar productor(ch)
    lanzar consumidor(ch)
    esperar()
```

En este ejemplo:

1. `lanzar productor(ch)` clona el descriptor del canal y lanza un hilo. El `ch` original retiene ownership.
2. El productor envía 10 enteros usando `ch <- i`, cada envío transfiere el entero por copia (los tipos primitivos se copian; los tipos complejos transfieren ownership).
3. `cerrar_canal(-> ch)` transfiere ownership del canal y lo cierra.
4. El consumidor recibe con `recibir(ch, -> valor)` donde `-> valor` indica que el canal transferirá ownership a `valor`.

## Sin estado compartido

El sistema de tipos garantiza que no existan referencias globales mutables. Toda comunicación entre `lanzar`/`lanzar` ocurre exclusivamente por canales. Como cada valor tiene un único propietario en cada momento y los canales transfieren esa propiedad, **dos hilos nunca pueden acceder concurrentemente a la misma dirección de memoria**.

Esto es análogo al modelo de actores, pero con la diferencia fundamental de que Synapse no requiere un runtime de actores —los canales se compilan a operaciones atómicas sobre colas lock-free o bloqueantes según la plataforma.

## Bajo el capó: AST del compilador

El compilador representa canales como nodos específicos en el AST, definidos en [ast_nodes.syn](/librerias/compiler/ast_nodes.syn):

```synapse
estructura ExprCrearCanal:
    tipo_elemento: texto

estructura SentenciaEnviarCanal:
    canal: Nodo
    valor: Nodo

estructura ExprRecibirCanal:
    canal: Nodo
```

El parser reconoce la sintaxis `<-` y `->` en [parser.syn](/librerias/compiler/parser.syn):

```synapse
funcion parsear_enviar_canal() -> Nodo:
    nodo = SentenciaEnviarCanal()
    nodo.canal = parsear_expresion()
    consumir_token(FECHA_IZQUIERDA)      # <-
    nodo.valor = parsear_expresion()
    retornar nodo
```

El generador de C traduce esto a primitivas de sincronización del sistema operativo, manteniendo la semántica de transferencia de ownership en toda la cadena de herramientas.
