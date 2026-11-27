# Generar Clases con OpenSyn

Este capítulo muestra cómo usar OpenSyn para generar clases completas con propiedades, métodos y documentación. Aprenderás a describir tus necesidades y obtener código bien estructurado.

Generar clases acelera el diseño de sistemas orientados a objetos.

<!-- cumple Manual 7 §6.3 -->

## 1. Generación de Estructuras (Syquex)

### Prompt Básico

```
Prompt: "estructura Producto con campos: nombre (texto), precio (decimal), 
stock (entero con valor por defecto 0), constructor y métodos: 
obtener_precio_con_iva(), agregar_stock(cantidad), retirar_stock(cantidad) -> Resultado<entero, texto>"
```

### Resultado Generado

```syquex
estructura Producto:
    nombre: texto
    precio: decimal
    stock: entero = 0

    crear(nombre: texto, precio: decimal, stock: entero = 0):
        self.nombre = nombre
        self.precio = precio
        self.stock = stock

    metodo obtener_precio_con_iva() -> decimal:
        return self.precio * 1.21  // IVA 21%

    metodo agregar_stock(cantidad: entero):
        self.stock = self.stock + cantidad

    metodo retirar_stock(cantidad: entero) -> Resultado<entero, texto>:
        si cantidad > self.stock:
            return err("Stock insuficiente")
        self.stock = self.stock - cantidad
        return ok(self.stock)
```

### Prompt Detallado

```
Prompt: "estructura Banco con:
- Campos: numero_cuenta (texto), saldo (decimal), cliente (texto)
- Constructor con saldo_inicial
- Métodos:
  - depositar(monto: decimal) -> nulo
  - retirar(monto: decimal) -> Resultado<decimal, texto>
  - consultar_saldo() -> decimal
  - transferir(otro: Banco, monto: decimal) -> Resultado<nulo, texto>
- Método especial __str__ para representación"
```

## 2. Generación con Herencia y Traits

### Prompt

```
Prompt: "estructura Vehiculo con: marca, modelo, año, metodo arrancar() -> texto.
Luego estructura Auto que 'hereda' de Vehiculo con: puertas (entero), 
metodo abrir_puertas() -> texto.
Usar composición (no herencia clásica)."
```

### Resultado

```syquex
estructura Vehiculo:
    marca: texto
    modelo: texto
    año: entero

    crear(marca: texto, modelo: texto, año: entero):
        self.marca = marca
        self.modelo = modelo
        self.año = año

    metodo arrancar() -> texto:
        return "El vehículo " + self.marca + " " + self.modelo + " está arrancando"

estructura Auto:
    vehiculo_base: Vehiculo
    puertas: entero

    crear(marca: texto, modelo: texto, año: entero, puertas: entero):
        self.vehiculo_base = Vehiculo(marca, modelo, año)
        self.puertas = puertas

    metodo arrancar() -> texto:
        // Override
        return self.vehiculo_base.arrancar() + " (auto)"

    metodo abrir_puertas() -> texto:
        return "Abriendo " + self.puertas.texto() + " puertas"
```

## 3. Generación con Traits/Interfaces

### Prompt

```
Prompt: "trait Volador con metodo volar() -> texto.
trait Nadador con metodo nadar() -> texto.
estructura Pato que implementa ambos traits."
```

### Resultado

```syquex
trait Volador:
    metodo volar() -> texto

trait Nadador:
    metodo nadar() -> texto

estructura Pato:
    nombre: texto

    crear(nombre: texto):
        self.nombre = nombre

    implementa Volador:
        metodo volar() -> texto:
            return self.nombre + " vuela"

    implementa Nadador:
        metodo nadar() -> texto:
            return self.nombre + " nada"
```

## 4. Generación con Sistema de Tipos Avanzado

### Prompt

```
Prompt: "estructura Repositorio<T> genérica con:
- Campo elementos: Lista<T>
- Métodos: agregar(item: T), obtener(indice: entero) -> Opcion<T>, 
  eliminar(indice: entero) -> Resultado<T, texto>, 
  buscar(predicado: funcion(T) -> booleano) -> Opcion<T>"
```

### Resultado

```syquex
estructura Repositorio<T>:
    elementos: Lista<T>

    crear():
        self.elementos = Lista<T>()

    metodo agregar(item: T):
        self.elementos.agregar(item)

    metodo obtener(indice: entero) -> Opcion<T>:
        si indice < 0 o indice >= self.elementos.len():
            return ninguno
        return algun(self.elementos[indice])

    metodo eliminar(indice: entero) -> Resultado<T, texto>:
        intentar:
            let elemento = self.elementos[indice]
            self.elementos.eliminar(indice)
            return ok(elemento)
        atrapar e:
            return err("Error al eliminar: " + e)

    metodo buscar(predicado: funcion(T) -> booleano) -> Opcion<T>:
        para elemento en self.elementos:
            si predicado(elemento):
                return algun(elemento)
        return ninguno
```

## 5. Generación con Patrones de Diseño

### Singleton

```
Prompt: "estructura ConfiguracionSingleton con:
- Campo estatico instancia: Opcion<ConfiguracionSingleton>
- Campo config: Mapa<texto, texto>
- Método obtener_instancia() -> ConfiguracionSingleton (singleton)
- Método get(clave: texto) -> Opcion<texto>
- Método set(clave: texto, valor: texto)"
```

```syquex
estructura ConfiguracionSingleton:
    estatico instancia: Opcion<ConfiguracionSingleton> = ninguno
    config: Mapa<texto, texto>

    crear():
        self.config = Mapa<texto, texto>()

    metodo estatico obtener_instancia() -> ConfiguracionSingleton:
        coincidir ConfiguracionSingleton.instancia:
            caso algun(instancia):
                return instancia
            caso ninguno:
                ConfiguracionSingleton.instancia = algun(ConfiguracionSingleton())
                return ConfiguracionSingleton.instancia

    metodo get(clave: texto) -> Opcion<texto>:
        return self.config.obtener(clave)

    metodo set(clave: texto, valor: texto):
        self.config[clave] = valor
```

### Factory Pattern

```
Prompt: "trait Producto con metodo usar() -> texto.
estructura ProductoA, ProductoB que implementan Producto.
estructura Fabrica con metodo crear(tipo: texto) -> Opcion<Producto>."
```

```syquex
trait Producto:
    metodo usar() -> texto

estructura ProductoA:
    implementa Producto:
        metodo usar() -> texto:
            return "Usando ProductoA"

estructura ProductoB:
    implementa Producto:
        metodo usar() -> texto:
            return "Usando ProductoB"

estructura Fabrica:
    metodo crear(tipo: texto) -> Opcion<Producto>:
        coincidir tipo:
            caso "A": return algun(new ProductoA())
            caso "B": return algun(new ProductoB())
            caso _: return ninguno
```

## 6. Generación con Documentación

### Prompt

```
Prompt: "estructura Usuario con nombre, email, edad. 
Incluye docstrings en español para cada campo y método.
Métodos: saludar(), es_mayor_de_edad() -> booleano, cumpleaños()"
```

### Resultado con Documentación

```syquex
estructura Usuario:
    /// Nombre completo del usuario
    nombre: texto
    
    /// Dirección de correo electrónico válida
    email: texto
    
    /// Edad en años del usuario
    edad: entero

    /// Crea un nuevo usuario con los datos proporcionados
    /// @param nombre Nombre completo
    /// @param email Email válido
    /// @param edad Edad en años
    crear(nombre: texto, email: texto, edad: entero):
        self.nombre = nombre
        self.email = email
        self.edad = edad

    /// Muestra un saludo personalizado
    metodo saludar() -> texto:
        return "Hola, soy " + self.nombre + " (" + self.edad.texto() + " años)"

    /// Verifica si el usuario es mayor de edad (18+)
    /// @return verdadero si edad >= 18, falso en caso contrario
    metodo es_mayor_de_edad() -> booleano:
        return self.edad >= 18

    /// Incrementa la edad en un año
    metodo cumpleaños():
        self.edad = self.edad + 1
```

## 7. Generación con Métodos Especiales

```
Prompt: "estructura Punto2D con x, y (decimal). 
Incluye __add__ (suma de puntos), __eq__ (comparación), __str__ (representación)."
```

```syquex
estructura Punto2D:
    x: decimal
    y: decimal

    crear(x: decimal, y: decimal):
        self.x = x
        self.y = y

    metodo __add__(otro: Punto2D) -> Punto2D:
        return Punto2D(self.x + otro.x, self.y + otro.y)

    metodo __eq__(otro: Punto2D) -> booleano:
        return self.x == otro.x and self.y == otro.y

    metodo __str__() -> texto:
        return "(" + self.x.texto() + ", " + self.y.texto() + ")"
```

## 8. Personalización de Generación

### Configuración de Estilo

```jsonc
// .vscode/settings.json
{
    "synapse.opensyn.classStyle": "docstrings",
    "synapse.opensyn.includeTypes": true,
    "synapse.opensyn.includeDocs": true,
    "synapse.opensyn.preferComposition": true,
    "synapse.opensyn.methodVisibility": "public"
}
```

### Prompt Templates

```toml
[generacion.clases]
# Templates predefinidos
class_template = """
{{description}}

{{fields}}

{{methods}}
"""

method_template = """
[{{access}}] {{method_name}}({{params}}) -> {{return_type}}:
    {{body}}
"""
```

## 9. Limitaciones y Consideraciones

- OpenSyn no puede generar código que haga referencia a APIs no especificadas en los manuales
- Las estructuras generadas siguen las convenciones del lenguaje (Manual 3 §6)
- El código generado siempre es validado por el compilador real

## Referencias

- **Manual 7 §6.3**: Bucle de corrección automática
- **Manual 3 §6**: Estructuras, métodos y constructores (OOP nativo)
- **Manual 7 §5.1**: Transpilación y mapeo conceptual
- **Manual 7 §2.3**: Inyección de contexto estático

// cumple Manual 7 §6.3
