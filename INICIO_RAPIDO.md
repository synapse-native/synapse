# Synapse: Guía de Inicio (Directo al Metal)

### Bienvenido a la Resistencia del Silicio

Has pasado años escribiendo código para máquinas virtuales pesadas, lidiando con recolectores de basura impredecibles y descargando gigabytes de dependencias ocultas solo para imprimir una sola línea de texto en una consola.

Eso termina hoy.

Bienvenido a **Synapse**. Un lenguaje de sistemas diseñado para hablar directamente con el hardware sin intermediarios ni burocracia. Aquí compilamos a binarios nativos puros, asignamos memoria con precisión determinista y descargamos módulos desde una red descentralizada. 

Esta guía no te enseñará a usar un *framework* de moda. Te enseñará a recuperar el control de tu máquina.

---

### 1. El Arsenal: Preparando tu Entorno

Para forjar tu primer programa, necesitas clonar el motor principal desde nuestra organización matriz. No hay instaladores pesados, solo herramientas de grado industrial.

Abre tu terminal y ejecuta:

```bash
# 1. Clona el compilador base
git clone https://github.com/synapse-native/core.git
cd core

# 2. Verifica que el motor respira (requiere Python 3.x para el bootstrap)
python main.py --version
```

> **Nota del Sistema:** El compilador Synapse utiliza actualmente GCC en segundo plano (Auto-Linker) para el enlazado binario final. Asegúrate de tener MinGW (en Windows) o GCC nativo (en Linux/Mac) en tu variable de entorno PATH.

---

### 2. El Gestor Descentralizado: Conociendo a Axon

Synapse no depende de repositorios centrales que puedan caerse. Nuestro gestor de paquetes, Axon, extrae código directamente desde la nube a tu disco duro local de forma quirúrgica.

Vamos a inyectar la librería de sistema estándar (std.sys) en tu proyecto:

```bash
# Inicializa tu ecosistema local
python axon_src/axon.py init

# Instala la librería estándar oficial desde la nube
python axon_src/axon.py instalar std.sys
```

En milisegundos, Axon aislará la dependencia dentro de la carpeta `axon_modules/`. Sin conflictos globales. Sin contaminación de tu sistema operativo.

---

### 3. El Ritual: Tu Primer "Hola Mundo"

Crea un archivo de texto en blanco llamado `hola.syn`. Ábrelo con tu editor de código de confianza y escribe exactamente esto:

```synapse
// archivo: hola.syn
importar "std.sys"

funcion principal() -> entero {
    imprimir("Hola, Silicio. El mundo exterior te saluda.")
    
    // Retornamos 0 al sistema operativo indicando éxito absoluto
    retornar 0
}
```

Mira bien ese código. Es limpio, es legible, pero bajo la superficie, es una instrucción directa a los registros de tu procesador.

---

### 4. La Fusión: Compilación a Metal

Es hora de encender el motor. Vamos a tomar ese texto y transformarlo en un ejecutable nativo e independiente.

Vuelve a tu terminal y ejecuta el compilador:

```bash
python main.py hola.syn
```

Si tu código está libre de errores, Synapse analizará tu léxico, resolverá las rutas en tu ecosistema local, invocará al Auto-Linker y generará un archivo `hola.exe` (o simplemente `hola` en sistemas Unix).

Ejecútalo:

```bash
./hola
```

**Salida esperada:**
```
Hola, Silicio. El mundo exterior te saluda.
```

---

### El Siguiente Nivel

Acabas de compilar tu primer programa en Synapse. Tienes un binario puro que pesa unos pocos kilobytes y se ejecuta en microsegundos.

Pero esto es solo la superficie. Synapse tiene la capacidad nativa de abrir puertos de red, manipular archivos del sistema operativo y, en su horizonte más cercano, orquestar tensores matemáticos para Inteligencia Artificial.

¿Estás listo para abandonar las abstracciones?

- Explora la Librería Estándar (SSL).
- Revisa el manual de sintaxis para dominar los punteros seguros.
- Contribuye al núcleo de la resistencia.
