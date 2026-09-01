# Testing en Syquex

Este capítulo explora las herramientas de testing integradas en Syquex: unit tests, integration tests y benchmarks. Aprenderás a escribir tests automatizados que garanticen la calidad de tu código.

El testing es una práctica esencial para el desarrollo de software confiable.

<!-- cumple Manual 3 §12.1 -->

## 1. Marco de Testing (`lib/pruebas`)

Syquex incluye un framework de testing integrado similar a Python's `unittest`, pero con inferencia estática y concurrencia.

### Estructura Básica

```syquex
importar lib.pruebas

estructura TestCalculadora:
    // Se ejecuta antes de cada test
    metodo setup():
        self.calc = Calculadora()

    // Se ejecuta después de cada test
    metodo teardown():
        self.calc.limpiar()

    // Test individual
    metodo probar_suma():
        let resultado = self.calc.sumar(2, 3)
        pruebas.afirmar(resultado == 5)

    // Test con nombre descriptivo
    metodo probar_division_por_cero_throws():
        pruebas.lanzar_error(funcion():
            self.calc.dividir(10, 0)
        )
```

### Ejecutar Tests

```bash
syquex test tests/
syquex test tests/test_calculadora.syq --verbose
syquex test tests/ --filter probar_suma
```

## 2. Afirmaciones (Assertions)

### Afirmaciones básicas

```syquex
pruebas.afirmar(condicion: booleano)
pruebas.afirmar_igual(valor1, valor2)
pruebas.afirmar_diferente(valor1, valor2)
pruebas.afirmar_mayor(que: entero, que2: entero)
pruebas.afirmar_menor(que: entero, que2: entero)
```

### Afirmaciones con mensajes personalizados

```syquex
pruebas.afirmar(
    usuario.edad >= 0,
    "La edad no puede ser negativa: " + usuario.edad.texto()
)
```

### Verificar errores

```syquex
// Verificar que se lanza un error
pruebas.lanzar_error(tipo_error: TipoError, funcion: funcion())

// Verificar el mensaje de error
pruebas.lanzar_error_con_mensaje(
    "División por cero",
    funcion(): dividir(10, 0)
)

// Verificar resultado de Resultado
pruebas.afirmar_ok(resultado)
pruebas.afirmar_err(resultado)
```

## 3. Fixtures

### Fixture de Método

```syquex
estructura TestBaseDeDatos:
    db: BaseDatos

    // Setup: ejecuta antes de cada test
    metodo setup():
        self.db = BaseDatos(":memory:")
        self.db.inicializar_schema()

    // Teardown: ejecuta después de cada test
    metodo teardown():
        self.db.cerrar()

    metodo probar_insertar():
        self.db.insertar("usuarios", {"nombre": "Ana"})
        pruebas.afirmar_igual(self.db.contar("usuarios"), 1)
```

### Fixtures con Scopes

```syquex
// Fixture de sesión (ejecuta una vez)
fixture_sesion db_connexion():
    let db = BaseDatos("test.sqlite")
    yield db
    db.cerrar()

// Fixture de función (ejecuta por test)
fixture_funcion usuario_prueba(db: BaseDatos):
    let usuario = Usuario("Test", "test@test.com")
    db.insertar(usuario)
    yield usuario
    db.eliminar(usuario.id)

estructura TestUsuario:
    metodo probar_crud(usuario: Usuario, db: BaseDatos):
        // usuario y db inyectados automáticamente por fixtures
        pruebas.afirmar(db.existe(usuario.id))
```

## 4. Mocks y Stubs

### Mock de Funciones

```syquex
importar lib.pruebas.mock

estructura ApiClientMock:
    metodo obtener_usuario(id: entero) -> Resultado<Usuario, texto>:
        retornar ok(Usuario(id, "Mock User", "mock@test.com"))

    metodo crear_usuario(usuario: Usuario) -> entero:
        registrado = verdadero
        retornar 999

// Usar el mock
funcion enviar_bienvenida(api: ApiClient):
    let resultado = api.obtener_usuario(1)
    coincidir resultado:
        caso ok(usuario):
            email.enviar(usuario.email, "Bienvenido!")
        caso err(e):
            log.error("Error: " + e)

// En tests
funcion test_enviar_bienvenida():
    let mock_api = ApiClientMock()
    pruebas.afirmar_no_lanza(funcion():
        enviar_bienvenida(mock_api)
    )
```

### Patching de Módulos

```syquex
// Mockear una función específica
with_patch("lib.fs.leer", lambda ruta: "contenido de prueba"):
    test_leer_config()
    // Dentro de este bloque, fs.leer siempre retorna "contenido de prueba"
```

## 5. Tests Parametrizados

```syquex
estructura TestValidacionEmail:
    // Ejecuta el test con múltiples valores
    @parametrizado([
        ("test@example.com", verdadero),
        ("invalid", falso),
        ("user@domain", falso),
        ("@nodomain.com", falso)
    ])
    metodo probar_validar_email(email: texto, esperado: booleano):
        let resultado = validar_email(email)
        pruebas.afirmar_igual(resultado, esperado)
```

## 6. Tests Asíncronos

```syquex
estructura TestAPIAsync:
    @async
    metodo probar_fetch_usuario():
        let resultado = await api.fetch_usuario(1)
        pruebas.afirmar_ok(resultado)
        
        let usuario = resultado.desenvolver_ok()
        pruebas.afirmar_igual(usuario.nombre, "Ana")

    @async
    metodo probar_timeout():
        let resultado = await Timeout(1000, api.llamada_lenta())
        pruebas.afirmar_err(resultado)
```

## 7. Benchmarks

```syquex
estructura BenchmarkCalculadora:
    @benchmark
    metodo bench_suma():
        para i en 1..10000:
            let _ = 2 + 2

    @benchmark(iteraciones: 5)  // Ejecutar 5 veces y promediar
    metodo bench_fibonacci():
        fibonacci(30)

// Ejecutar benchmarks
// syquex bench tests/benchmark_calculadora.syq
```

### Comparaciones de Rendimiento

```syquex
@benchmark_comparacion
estructura CompararSorting:
    metodo bubble_sort(lista: Lista<entero>) -> Lista<entero>:
        // Implementación...

    metodo quick_sort(lista: Lista<entero>) -> Lista<entero>:
        // Implementación...

    metodo setup() -> Lista<entero>:
        retornar Lista<entero>.aleatoria(1000)
```

## 8. Cobertura de Código

```bash
# Generar reporte de cobertura
syquex test tests/ --coverage

# Reporte HTML
syquex test tests/ --coverage --formato html

# Solo mostrar cobertura por módulo
syquex test tests/ --coverage --detallado
```

### Exclusiones de Cobertura

```syquex
// @coverage-ignore-start
funcion codigo_de_debug():
    if DEBUG:
        dump_internals()
// @coverage-ignore-end
```

## 9. Integración con CI/CD

### Configuración de GitHub Actions

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: synapse-dev/setup-syquex@v1
      - run: syquex test tests/ --coverage
      - uses: codecov/codecov-action@v3
```

### Testing en Paralelo

```bash
# Ejecutar tests en paralelo
syquex test tests/ --paralelos 4

# Ejecutar tests de una categoría específica
syquex test tests/ --categoria integration
```

## 10. TDD (Test-Driven Development)

### Flujo de trabajo TDD

```syquex
// 1. Escribe el test primero (falla)
estructura TestUsuario:
     metodo probar_crear_usuario():
        let u = Usuario("Ana", 28)
        pruebas.afirmar_igual(u.nombre, "Ana")

// 2. Implementa mínimo necesario para pasar
estructura Usuario:
    nombre: texto
    edad: entero
    
    crear(nombre: texto, edad: entero):
        self.nombre = nombre
        self.edad = edad

// 3. Refactoriza manteniendo los tests verdes
```

## Ejemplo Completo

```syquex
#lang: es
importar lib.pruebas
importar lib.pruebas.mock

estructura Calculadora:
    funcion sumar(a: entero, b: entero) -> entero:
        retornar a + b
    
    funcion dividir(a: entero, b: entero) -> Resultado<entero, texto>:
        si b == 0:
            retornar err("División por cero")
        retornar ok(a / b)

estructura TestCalculadora:
    calc: Calculadora
    
    metodo setup():
        self.calc = Calculadora()
    
    @parametrizado([
        (2, 3, 5),
        (-1, 1, 0),
        (0, 0, 0),
        (100, 200, 300)
    ])
    metodo probar_suma(a: entero, b: entero, esperado: entero):
        pruebas.afirmar_igual(self.calc.sumar(a, b), esperado)
    
    metodo probar_dividir_por_cero():
        let resultado = self.calc.dividir(10, 0)
        pruebas.afirmar_err(resultado)
    
    @async
    metodo probar_dividir_asincrono():
        let resultado = await async:
            self.calc.dividir(10, 2)
        pruebas.afirmar_ok(resultado)
        pruebas.afirmar_igual(resultado.desenvolver_ok(), 5)

pruebas.ejecutar()
```

## Referencias

- **Manual 3 §12.1**: Módulos incluidos (lib/pruebas)
- **Manual 3 §13**: Ejemplo completo
- **Manual 2 §12**: Contratos y pruebas obligatorias
- **Manual 5 §6**: Concurrencia en tests

// cumple Manual 3 §12
