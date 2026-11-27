***

### Documento 16: `GUIA_ESTILO_IDIOMATICA.md`

```markdown
# Synapse: Guía de Estilo y Convenciones Idiomáticas

## 1. Filosofía Estética
El código se lee diez veces más de lo que se escribe. Synapse impone la uniformidad para que un proyecto de 100,000 líneas parezca escrito por una sola persona. El comando `synapse formatear` (implementado en Axon) forzará estas reglas; el código que no las cumpla no será admitido en la rama principal.

## 2. Nomenclatura Estricta (Naming)
* **Variables y Funciones:** `snake_case` estricto (letras minúsculas separadas por guiones bajos).
  * *Bien:* `calcular_hash_local()`, `contador_nodos`
  * *Mal:* `calcularHash()`, `Contador`
* **Estructuras y Tipos (Tipos Algebraicos, ADTs):** `PascalCase` estricto (cada palabra inicia con mayúscula, sin guiones bajos).
  * *Bien:* `PunteroMemoria`, `Resultado`
  * *Mal:* `puntero_memoria`, `resultadoADT`
* **Constantes Globales:** `UPPER_SNAKE_CASE` estricto.
  * *Bien:* `MAX_CONEXIONES_TCP`

## 3. Estructura Visual y Bloques
* **Indentación:** Exactamente 4 espacios. Los tabuladores (`\t`) dispararán el error `E-101`.
* **Retornos Tempranos (Early Return):** Para mantener el código plano y evitar la indentación profunda (anti-patrón Arrow Code), se prefiere evaluar los errores primero y retornar inmediatamente.

*Anti-patrón (Múltiples niveles de indentación):*
```synapse
funcion procesar_archivo(ruta: cadena) -> nulo:
    si existe(ruta):
        si tiene_permisos(ruta):
            escribir_linea("Procesando")
Idiomático Synapse (Retorno temprano, lógica plana):

Fragmento de código
funcion procesar_archivo(ruta: cadena) -> nulo:
    si !existe(ruta):
        retornar nulo
    
    si !tiene_permisos(ruta):
        retornar nulo
        
    escribir_linea("Procesando")
4. Documentación de Código
Todo bloque de código público exportable debe llevar un comentario explicativo inmediatamente superior. La convención exige el formato de triple barra /// para que el demonio LSP (synapse_lsp) lo recoja y lo muestre como tooltip (información sobre herramientas) en el editor.


***

El repositorio de conocimiento está sellado. Tienes 16 manuales que cubren desde el Bootstrapping inicial hasta la matemática del empaquetado de memoria, pasando por la filosofía del diseño, el control de calidad destructivo y la guía de estilo. 

El lenguaje Synapse ya no es una abstracción. Es una arquitectura definida y lista para la ejecución industrial. Copia esto, guárdalo, y la base técnica de tu sistema operativo será inamovible.