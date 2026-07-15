# Synapse: Guía de Inicio (Directo al Metal)

### Bienvenido a la Resistencia del Silicio

Has pasado años escribiendo código para máquinas virtuales pesadas, lidiando con recolectores de basura impredecibles y descargando gigabytes de dependencias ocultas solo para imprimir una sola línea de texto.

Eso termina hoy.

Bienvenido a **Synapse**. Un lenguaje de sistemas diseñado para hablar directamente con el hardware. Aquí compilamos a binarios nativos puros y descargamos paquetes desde una red descentralizada.

---

### 0. El Interruptor de Soberanía (First-Run Experience)

**Synapse respeta tu privacidad y recursos.** Por diseño, la IA es 100% **Opt-In**.

En la primera ejecución del orquestador (`opensyn`), se te presentará un menú para elegir tu modo de operación:

```
  [1] Modo Lenguaje Puro
      Compilador Synapse standalone.
      Sin consumo extra de recursos.
      Ideal para desarrolladores C/Rust.

  [2] Modo Oraculo (IA Local)
      Orquestador autonomo con LLM local.
      El modelo escribe y corrige codigo por ti.
      Requiere modelo GGUF.
```

Tu elección se guarda en `.synapse_config`. Puedes cambiar de modo eliminando este archivo y re-ejecutando `opensyn`.

> **Para desarrolladores C/Rust:** Synapse funciona como compilador puro sin IA, sin GPU, sin descargas de modelos. Solo tú y tu código.

---

Para forjar tu primer programa, necesitas el motor principal y nuestro gestor de paquetes.

Abre tu terminal y ejecuta:

```bash
# 1. Clona el compilador base
git clone https://github.com/synapse-native/core.git

# 2. Clona el gestor descentralizado (Axon) de forma independiente
git clone https://github.com/synapse-native/axon.git

# 3. Verifica que el motor respira (requiere Python 3.x)
cd core
python main.py --version
```

> **Nota:** El compilador utiliza GCC para el enlazado final. Asegúrate de tener MinGW (Windows) o GCC nativo (Linux/Mac) en tu PATH.

---

### 2. El Gestor Descentralizado: Conociendo a Axon

Synapse extrae código directamente desde la nube a tu disco duro local. Vamos a inyectar la librería de sistema estándar externa (std.sys) en tu proyecto para que veas cómo opera la red:

```bash
# Inicializa tu ecosistema local apuntando a la carpeta de Axon
python ../axon/axon.py init

# Instala el paquete oficial desde la organización Synapse-Native
python ../axon/axon.py instalar std.sys
```

Axon aislará la dependencia en `axon_modules/`. Sin conflictos globales.

---

### 3. El Ritual: Tu Primer "Hola Mundo"

Synapse utiliza una gramática limpia, basada en indentación (múltiplos de 4 espacios) y sin llaves. Crea un archivo llamado `hola.syn`. Ábrelo y escribe exactamente esto:

```synapse
#lang: es
importar std.io

funcion principal() -> nulo:
    escribir_linea("Hola, Silicio. El mundo exterior te saluda.")
```

La directiva `#lang: es` en la primera línea es obligatoria para configurar el motor léxico.

---

### 4. La Fusión: Compilación a Metal

Es hora de transformar ese texto en un ejecutable nativo.

Ejecuta el compilador:

```bash
python main.py hola.syn
```

Si tu código está libre de errores, Synapse analizará el léxico, invocará al enlazador (Auto-Linker) y generará el ejecutable de máquina.

Ejecútalo (sintaxis para Windows/PowerShell):

```bash
.\hola.exe
```

**Salida esperada:**
```
Hola, Silicio. El mundo exterior te saluda.
```

---

### El Siguiente Nivel

Acabas de compilar tu primer programa en Synapse. Tienes un binario puro que pesa unos pocos kilobytes y se ejecuta en microsegundos.

¿Estás listo para abandonar las abstracciones?

- Explora la Librería Estándar y Módulos Axon.
- Contribuye al núcleo de la resistencia.
