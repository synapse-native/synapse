# Synapse: Manual del Lenguaje v2.2.2

> **Documento:** `MANUAL_LENGUAJE.md`
> **Versión:** 2.2.2 — RELEASE CANDIDATE
> **Última actualización:** 24 Julio 2026

---

## 1. Filosofía

Synapse es un lenguaje de programación **nativo, compilado y de grado de sistemas**.
Su filosofía rectora es **"El Pacto"**: el compilador es un auditor implacable que
prefiere detener la compilación ante la más mínima ambigüedad antes que permitir
código inseguro o comportamiento indefinido.

**Principios fundamentales:**
- **Sin recolector de basura** — Ownership único con RAII
- **Sin null** — Tipos algebraicos (`Resultado<T,E>`, `Opcion<T>`)
- **Sin estado compartido** — Concurrencia por paso de mensajes
- **Indentación estricta** — 4 espacios, sin llaves `{}`
- **Contratos lógicos** — `requiere`/`garantiza` con aserciones en tiempo real

---

## 2. Sintaxis Básica

### 2.1 Directiva de Archivo

Todo archivo `.syn` debe comenzar con la directiva de idioma:

```synapse
#lang: es
```

Idiomas soportados: `es` (español), `en` (inglés), `fr` (francés), `pt` (portugués).

### 2.2 Comentarios

```synapse
// Comentario de línea

/* Comentario
   de bloque */
```

### 2.3 Funciones

```synapse
funcion nombre(param1: Tipo1, param2: Tipo2) -> TipoRetorno:
    // cuerpo
    retornar valor
```

### 2.4 Variables y Asignación

```synapse
nombre = expresion
```

Todas las variables se declaran con `=`. El tipo se infiere del contexto.

### 2.5 Constantes

```synapse
constante N = 42
constante MENSAJE = "hola"
```

### 2.6 Estructuras

```synapse
estructura Punto:
    x: entero
    y: entero
```

---

## 3. Tipos Nativos

| Tipo Synapse | Tipo C | Descripción |
|-------------|--------|-------------|
| `entero` | `int64_t` | Entero con signo de 64 bits |
| `decimal` | `double` | Punto flotante de doble precisión |
| `booleano` | `bool` | `verdadero` / `falso` |
| `texto` | `CadenaSegura` | String con longitud (no null-terminated inseguro) |
| `caracter` | `char` | Carácter UTF-8 |
| `nulo` | `void` | Ausencia de valor de retorno |
| `puntero` | `void*` | Puntero opaco (solo en bloques `inseguro`) |

### 3.1 Tipos Algebraicos

```synapse
// Resultado (Retorno con manejo de errores)
tipo ResultadoExitoso = Resultado<entero, texto>
//  → C: struct { int tag; union { int ok; char* err; }; }

// Opcional (Valor o nada)
tipo ValorOpcional = Opcion<entero>
//  → C: struct { int tag; union { int some; }; }
```

### 3.2 Coincidir (Pattern Matching)

```synapse
resultado = leer_archivo("config.txt")
coincidir resultado:
    ok(datos) =>
        escribir_linea(datos)
    err(motivo) =>
        escribir_linea(motivo)
```

---

## 4. Flujo de Control

### 4.1 Condicional (`si`/`sino`)

```synapse
si condicion:
    // cuerpo

sino:
    // cuerpo alternativo
```

### 4.2 Bucle (`mientras`)

```synapse
mientras condicion:
    // cuerpo
```

### 4.3 Bucle (`para`)

```synapse
para i = 0 mientras i < 10:
    // cuerpo
```

### 4.4 Romper y Siguiente

```synapse
romper       // Sale del bucle
siguiente    // Salta a la siguiente iteración
```

---

## 5. Contratos Lógicos (`requiere`/`garantiza`)

### 5.1 Sintaxis

```synapse
funcion calcular_descuento(precio: decimal, porcentaje: decimal) -> decimal:
    requiere:
        precio > 0.0
        porcentaje >= 0.0
        porcentaje <= 100.0

    garantiza:
        _resultado_ <= precio
        _resultado_ >= 0.0

    monto = precio * (porcentaje / 100.0)
    retornar precio - monto
```

### 5.2 Semántica

- **`requiere`**: Pre-condiciones evaluadas **antes** de ejecutar el cuerpo
- **`garantiza`**: Post-condiciones evaluadas **antes** de cada `retornar`
- **`_resultado_`**: Variable implícita que captura el valor de retorno

### 5.3 Generación C

```c
// requiere:
assert(precio > 0.0 && "Fallo de contrato (requiere): precio > 0.0");
assert(porcentaje >= 0.0 && "Fallo de contrato (requiere): porcentaje >= 0.0");

// cuerpo...

// garantiza (antes de cada return):
double _temp_ret = precio - monto;
assert(_temp_ret <= precio && "Fallo de contrato (garantiza): _resultado_ <= precio");
return _temp_ret;
```

### 5.4 Modos de Compilación

| Modo | Comportamiento |
|------|---------------|
| Debug (por defecto) | `#ifndef SYNAPSE_RELEASE` — aserciones activas |
| Release | `#define SYNAPSE_RELEASE` — aserciones eliminadas (costo cero) |

---

## 6. Concurrencia por Canales

### 6.1 Creación de Canal

```synapse
mi_canal = canal<entero>(100)  // Canal de enteros con capacidad 100
```

### 6.2 Envío y Recepción

```synapse
mi_canal <- 42        // Enviar: bloquea si el canal está lleno
valor = mi_canal ->   // Recibir: bloquea si el canal está vacío
```

### 6.3 Lanzar (Hilo)

```synapse
lanzar productor(mi_canal)
// Transfiere ownership del canal al nuevo hilo
```

### 6.4 Escuchar (Listener)

```synapse
escuchar mi_canal:
    // se ejecuta por cada mensaje recibido
    // bloquea hasta recibir el siguiente mensaje
```

### 6.5 Recuperar (Error Handling)

```synapse
lanzar tarea_peligrosa() recuperar:
    error_handler()
```

### 6.6 Ejemplo Completo

```synapse
funcion productor(c: Canal<entero>):
    para i = 0 mientras i < 10:
        c <- i   // enviar
    retornar

funcion consumidor(c: Canal<entero>):
    mientras verdadero:
        valor = c ->   // recibir
        escribir_linea(entero_a_texto(valor))
    retornar

funcion principal() -> nulo:
    ch = canal<entero>(5)
    lanzar productor(ch)
    lanzar consumidor(ch)
    esperar()
    retornar
```

---

## 7. Bloques Inseguros

```synapse
inseguro:
    // Código con acceso a punteros crudos
    ptr = direccion_memoria
    // ...
```

Solo disponible cuando se compila sin `#no_std`.

---

## 8. Importaciones

### 8.1 Sysroot (Librería Estándar)

```synapse
importar std.io            // E/S estándar
importar std.concurrencia  // Canales y hilos
importar std.tensor        // Tensores y SIMD
importar std.crypto         // Ed25519 (via Axon)
```

### 8.2 Paquetes Axon

```synapse
importar mi-paquete        // axon_modules/mi-paquete/principal.syn
```

---

## 9. Tabla de Operadores

| Precedencia | Operadores | Asociatividad |
|-------------|-----------|---------------|
| 1 (máxima) | `f(x)` llamadas | Izquierda |
| 2 | `-` (unario), `!` | Derecha |
| 3 | `*` `/` `%` | Izquierda |
| 4 | `+` `-` | Izquierda |
| 5 | `<` `>` `<=` `>=` | Izquierda |
| 6 | `==` `!=` | Izquierda |
| 7 | `y` (AND) | Izquierda |
| 8 | `o` (OR) | Izquierda |

---

## 10. Gramática Formal (EBNF)

```ebnf
Programa        ::= DirectivaLang (Sentencia)* EOF
DirectivaLang   ::= "#lang:" Identificador NEWLINE

Sentencia       ::= DeclaracionFuncion
                  | DeclaracionEstructura
                  | DeclaracionConstante
                  | Importacion
                  | SentenciaControl
                  | Asignacion
                  | Expresion NEWLINE

DeclaracionFuncion ::= "funcion" Identificador "(" Parametros? ")" "->" TipoRetorno ":"
                       NEWLINE (ContratoRequiere)? (ContratoGarantiza)? Bloque

Parametros      ::= Parametro ("," Parametro)*
Parametro       ::= ("->")? Identificador ":" Tipo

Bloque          ::= INDENT (Sentencia)+ DEDENT

ContratoRequiere  ::= "requiere" ":" NEWLINE INDENT (Expresion NEWLINE)+ DEDENT
ContratoGarantiza ::= "garantiza" ":" NEWLINE INDENT (Expresion NEWLINE)+ DEDENT

SentenciaControl ::= CondicionalSi | BucleMientras | BuclePara
                    | LanzarHilo | EscucharCanal | RecuperarError
                    | Romper | Siguiente | BloqueInseguro

CondicionalSi   ::= "si" Expresion ":" NEWLINE Bloque ("sino" ":" NEWLINE Bloque)?
BucleMientras   ::= "mientras" Expresion ":" NEWLINE Bloque
BuclePara       ::= "para" Identificador "=" Expresion "mientras" Expresion ":" NEWLINE Bloque

LanzarHilo      ::= "lanzar" LlamadaFuncion ("recuperar" Expresion)?
EscucharCanal   ::= "escuchar" Expresion ":" NEWLINE Bloque

CrearCanal      ::= "canal" "<" Tipo ">" "(" Expresion ")"
EnviarCanal     ::= Expresion "<-" Expresion
RecibirCanal    ::= Expresion "->"

Tipo            ::= "entero" | "decimal" | "booleano" | "texto" | "caracter"
                  | "nulo" | "puntero"
                  | Identificador           // struct definido por usuario
                  | "Canal" "<" Tipo ">"
                  | "Resultado" "<" Tipo "," Tipo ">"
                  | "Opcion" "<" Tipo ">"
```

---

## 11. Convenciones de Estilo

- **Indentación:** 4 espacios (no tabs)
- **Nombres de función:** `snake_case`
- **Constantes:** `MAYUSCULAS`
- **Tipos definidos:** `PascalCase`
- **Archivos:** `nombre_del_modulo.syn`
- **Límite de línea:** 100 caracteres (recomendado)

---

## 12. Ejemplo Completo

```synapse
#lang: es
importar std.io
importar std.concurrencia

constante MAX_ITEMS = 1000

funcion productor(c: Canal<entero>, inicio: entero, cantidad: entero) -> nulo:
    requiere:
        cantidad > 0
        cantidad <= MAX_ITEMS

    para i = 0 mientras i < cantidad:
        c <- inicio + i
    retornar

funcion consumidor(c: Canal<entero>, total: entero) -> nulo:
    suma = 0
    para i = 0 mientras i < total:
        valor = c ->
        suma = suma + valor
    escribir_linea("Suma total: " + entero_a_texto(suma))
    retornar

funcion principal() -> entero:
    ch = canal<entero>(100)
    lanzar productor(ch, 1, 100)
    lanzar consumidor(ch, 100)
    esperar()
    retornar 0
```
