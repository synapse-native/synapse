# Synapse: Especificación ABI, Padding y Alineación de Memoria

## 1. El Problema del Hardware
Para que Synapse sea el núcleo de un sistema operativo, sus estructuras de datos (`structs`) deben coincidir exactamente con lo que espera el procesador y los controladores de hardware. Los procesadores modernos exigen que los datos estén alineados en memoria (ej. un `entero` de 8 bytes debe comenzar en una dirección de memoria múltiplo de 8).

## 2. Reglas de Relleno (Padding)
Cuando el compilador C subyacente (y por ende, Synapse) genera un `struct`, inyecta bytes vacíos (padding) para alinear los datos, calculados mediante la siguiente fórmula formal de alineamiento donde $P$ es el relleno, $A$ es el requisito de alineación y $O$ es el *offset* actual:

$P = (A - (O \bmod A)) \bmod A$

### Ejemplo Crítico:
```synapse
// Representación en Synapse
estructura PaqueteRed:
    activo: booleano    // 1 byte
    secuencia: entero   // 8 bytes
    flag: caracter      // 1 byte

Si este código se compila tal cual, la memoria resultante no será de 10 bytes. Será de 24 bytes debido al padding:
1 byte (booleano) + 7 bytes (padding) + 8 bytes (entero) + 1 byte (caracter) + 7 bytes (padding final para alinear el bloque completo).

3. Directiva [empaquetado] (Packed Structs)
Si estás escribiendo el driver de una tarjeta de red o un sistema de archivos, el padding corromperá la lectura binaria. Para obligar al compilador a agrupar los bytes sin relleno, debes usar la anotación [empaquetado] antes del struct.

Fragmento de código
[empaquetado]
estructura CabeceraIP:
    version: caracter
    longitud: entero
Advertencia: Acceder a memoria no alineada en arquitecturas ARM puede generar una penalización de rendimiento severa o un fallo de hardware (Bus Error). Úsalo exclusivamente para comunicación FFI o lectura de buffers crudos.