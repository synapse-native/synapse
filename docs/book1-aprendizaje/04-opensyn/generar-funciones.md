# Generar Funciones con OpenSyn

Este capítulo explora cómo usar OpenSyn para generar funciones completas a partir de descripciones en lenguaje natural. Aprenderás a escribir prompts efectivos y refinar los resultados.

Generar funciones es una de las capacidades más productivas de OpenSyn.

<!-- cumple Manual 7 §6.3 -->

## 1. Escribir Prompts Efectivos

### Principios Básicos

1. **Sé específico sobre el lenguaje**
   ```
   # Bueno
   "función factorial en Syquex que use recursión"
   
   # Mejor
   "función Syquex que calcule factorial de n usando recursión, 
    con tipo de retorno entero y caso base n <= 1"
   ```

2. **Especifica los tipos**
   ```
   # Incluye tipos de parámetros y retorno
   "función sumar(a: entero, b: entero) -> entero que retorne a + b"
   ```

3. **Menciona contratos (Synapse)**
   ```
   "función dividir en Synapse con contrato requiere b != 0"
   ```

## 2. Generación Paso a Paso

### Paso 1: Contexto

OpenSyn analiza:
- El archivo actual y su AST
- Imports y símbolos definidos
- Diagnósticos activos
- Configuración del proyecto

### Paso 2: Construcción del Prompt

```text
[SYSTEM]
--- Reglas de Syquex ---
- estructura Nombre:
- metodo nombre()
- Resultado<T, E>, operador ?
- Canal<T> para concurrencia

[CONTEXT]
Archivo: servicio.syq, líneas 10-15
```syquex
estructura Servicio:
    dao: Dao

    metodo crear(entrada: Entrada) -> Resultado<Salida, Texto>:
        // cursor aquí
```

[INSTRUCCIÓN]
Completa la función crear con validación y guardado
```

### Paso 3: Generación

OpenSyn genera el código:

```syquex
metodo crear(entrada: Entrada) -> Resultado<Salida, Texto>:
    // Validar entrada
    si entrada.nombre.len() == 0:
        retornar err("El nombre es requerido")
    
    si entrada.email.es_vacio():
        retornar err("El email es requerido")
    
    // Guardar
    intentar:
        let entidad = Entidad(entrada.nombre, entrada.email)
        let resultado = self.dao.guardar(entidad)
        retornar ok(resultado)
    atrapar e:
        retornar err("Error al guardar: " + e)
```

### Paso 4: Validación

El LSP valida con `synapse check --no-emit`:

```bash
✅ Análisis léxico: OK
✅ Análisis sintáctico: OK
✅ Análisis semántico: OK
✅ Contratos: OK
```

## 3. Comandos de Generación

### Terminal

```bash
# Generación básica
opensyn generate "función que sume dos enteros - syquex"

# Con tipo de retorno
opensyn generate --lang syquex "función sumar(a: entero, b: entero) -> entero"

# Guardar en archivo
opensyn generate --output funcion.syq "función factorial recursiva"
```

### VS Code

| Comando | Atajo | Descripción |
|---------|-------|-------------|
| Generate Code | `Ctrl+Shift+G` | Generar código bajo el cursor |
| Complete Line | `Tab` | Completar la línea actual |
| Generate Block | `Ctrl+Shift+B` | Generar bloque de código |

## 4. Plantillas de Prompts Comunes

### Función básica en Syquex

```
Prompt: "función en Syquex que reciba una Lista<entero> y retorne el promedio, 
usa operaciones funcionales (map, filter, reduce) y Resultado para errores"
```

Salida:
```syquex
funcion promedio(numeros: Lista<entero>) -> Resultado<decimal, texto>:
    si numeros.len() == 0:
        retornar err("Lista vacía")
    
    let suma = numeros.reducir(lambda acc, x: acc + x, 0)
    retornar ok(suma.decimal() / numeros.len().decimal())
```

### Función con contratos en Synapse

```
Prompt: "función en Synapse que valide un email usando regex, 
con contrato requiere email != '' y garantiza retorna booleano"
```

Salida:
```synapse
funcion validar_email(email: texto) -> booleano:
    requiere:
        email.len() > 0
    garantiza:
        _resultado_ == verdadero o _resultado_ == falso
    retornar regex_coincidir(email, "^[^@]+@[^@]+\\.[^@]+$")
```

### Función asíncrona

```
Prompt: "función async en Syquex que haga fetch HTTP y retorne el JSON parseado,
con manejo de errores usando Resultado"
```

Salida:
```syquex
async funcion fetch_json(url: texto) -> Resultado<Mapa<texto, Objeto>, texto>:
    intentar:
        let resp = await http.get(url)
        let datos = resp.cuerpo.parse_json()
        retornar ok(datos)
    atrapar e:
        retornar err("Error en fetch: " + e.texto())
```

### Estructura con métodos

```
Prompt: "estructura Banco con campo saldo, métodos depositar, retirar y consultar_saldo,
método crear con saldo_inicial, retirar debe retornar Resultado"
```

Salida:
```syquex
estructura Banco:
    saldo: decimal

    crear(saldo_inicial: decimal):
        self.saldo = saldo_inicial

    metodo depositar(monto: decimal):
        self.saldo = self.saldo + monto

    metodo retirar(monto: decimal) -> Resultado<decimal, texto>:
        si monto > self.saldo:
            retornar err("Saldo insuficiente")
        self.saldo = self.saldo - monto
        retornar ok(self.saldo)

    metodo consultar_saldo() -> decimal:
        retornar self.saldo
```

## 5. Refinamiento Iterativo

### Bucle de Corrección Automática

```text
Intento 1: OpenSyn genera código → Compilador valida → ❌ Error
Intento 2: Se añade el error al prompt → OpenSyn corrige → ❌ Error
Intento 3: Se añade el error al prompt → OpenSyn corrige → ✅ Válido
```

### Feedback Manual

Si el código corregido no es correcto, puedes:
1. Corregir manualmente
2. Guardar el par (instrucción, código corregido) como feedback
3. El sistema aprenderá de este patrón en futuras consultas

## 6. Generación Contextual

### Usar Contexto del Archivo

OpenSyn utiliza el contexto del archivo actual:

```syquex
// Archivo actual: utils.syq
importar lib.lista

funcion procesar_lista(items: Lista<texto>) -> Lista<texto>:
    // Cursor aquí - OpenSyn conoce que items es Lista<texto>
    // y que ya importaste lib.lista
```

Prompt: "filtra elementos vacíos y convierte a mayúsculas"

OpenSyn sabe que:
- `items` es `Lista<texto>`
- Ya importaste `lib.lista`
- Puedes usar operaciones como `.filtrar()`, `.mapear()`

## 7. Personalización de Estilo

```toml
[prompts]
# Estilo de generación
code_style = "idiomatic"  # "idiomatic", "verbose", "concise"

# Idioma del código generado
code_language = "es"  # o "en"

# Preferencias de estructura
prefer_structures = true
prefer_functions = true
prefer_composition = true
```

## 8. Buenas Prácticas

### Escribe Prompts Claros

```text
# ❌ Vago
"haz algo con una lista"

# ✅ Específico
"función Syquex que filtre números pares de una Lista<entero>,
 los multiplique por 2, y retorne la suma total usando operaciones funcionales"
```

### Divide y Vencerás

```text
# En lugar de:
"crea un servidor web completo con CRUD de usuarios"

# Haz:
1. "estructura Usuario con nombre, email, edad"
2. "middleware de autenticación JWT en Syquex"
3. "endpoint REST GET /usuarios en Syquex"
```

### Verifica Tipos

```text
# Incluye tipos en el prompt
"función (a: entero, b: entero) -> Resultado<decimal, texto>"
```

## 9. Limitaciones Conocidas

- No genera código para operaciones no especificadas en los manuales
- Puede sugerir sintaxis que aún no está implementada
- El rendimiento varía según el modelo seleccionado

## Referencias

- **Manual 7 §6.3**: Bucle de corrección automática (3 intentos)
- **Manual 7 §5.1**: Mapeo de conceptos (Python → Syquex)
- **Manual 7 §2.3**: Inyección de contexto estático
- **Manual 3 §1-3**: Sintaxis de Syquex
- **Manual 2 §1-2**: Sintaxis de Synapse

// cumple Manual 7 §6.3
