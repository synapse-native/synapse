# Synapse v1.5.0 — Lenguaje políglota de sistemas para inferencia local

## Características Clave
- **Hilos asíncronos nativos (`lanzar`):** Ejecuta funciones en hilos del sistema operativo con un solo comando. La concurrencia es un ciudadano de primera clase.
- **Auto-Wait automático:** El runtime espera a que todos los hilos lanzados finalicen antes de cerrar el proceso principal, eliminando bucles de espera activa.
- **Auto-Linker integrado con GCC:** El compilador invoca GCC automáticamente para producir el ejecutable final. No hay pasos manuales de linkeo.
- **I/O thread-safe:** Las funciones de entrada/salida (`log`, `escribir`) están protegidas por mutex, seguras para usar desde múltiples hilos.
- **Pool Allocator seguro para hilos (Mutex):** Gestión de memoria determinista con bloques fijos y protección pthread, sin GC ni malloc/free caótico.
- **Compilación directa a C nativo:** Sin dependencias pesadas. El binario del compilador es autocontenido y genera C puro vinculable a un runtime propio.
- **Evaluación lógica de cortocircuito:** Los operadores `y`/`o` evalúan en cortocircuito, optimizando flujos booleanos sin efectos secundarios innecesarios.
- **Tensor como ciudadano de primera clase:** Tipo `Tensor` 2D con producto punto, suma y ReLU como operaciones nativas del lenguaje.

## Novedades v1.5.0
- **Modo de Memoria Insegura y FFI:** Soporte oficial para `importar_c`, `externo`, bloques `inseguro` y punteros nativos `*` / `&`.
- **Layouts de memoria estrictos:** Control explícito de estructuras y acceso de punteros para interoperabilidad binaria segura.
- **Librería estándar del sistema:** Incluye los módulos `std.fs` y `std.sys` para operaciones de archivos y sistema desde Synapse.
- **Compatibilidad ampliada:** El compilador ahora empaqueta la carpeta `std/` junto al runtime para su distribución.

## Instalación Rápida (One-Liner)

Abre PowerShell y ejecuta:

```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/synapse-native/core/main/install.ps1" -UseBasicParsing | Invoke-Expression
```

El script descargará la última versión, la instalará en `C:\Synapse`, configurará el PATH del usuario y activará el coloreado sintáctico en VS Code automáticamente.

## Instalación Manual
1. Descarga `synapse-v1.5.0-windows-x64.zip` desde [Releases](https://github.com/synapse-native/core/releases).
2. Extrae en `C:\Synapse`.
3. Ejecuta `install.ps1` (clic derecho → "Ejecutar con PowerShell").
4. Reinicia tu terminal. Ahora `synapse` está disponible globalmente.

## Synapse v1.4.0 — Concurrencia Nativa

Synapse ahora soporta hilos asíncronos reales del sistema operativo mediante la instrucción `lanzar`, con protección automática de I/O y sincronización de ciclo de vida.

```synapse
lanzar hilo_trabajador(parametro)

# Al finalizar principal(), el runtime
# espera automáticamente todos los hilos
```

### Mecanismo Interno
- **Thread Tracker:** Contador atómico de hilos activos con variable de condición (`pthread_cond_t`). Cuando un hilo termina, decrementa el contador y emite broadcast si llega a cero.
- **synapse_esperar_hilos():** Se inyecta automáticamente al final de `main()` en el C generado. Bloquea con `pthread_cond_wait` hasta que todos los hilos lancen hayan finalizado.
- **synapse_lanzar_hilo():** Reserva un `_HiloArgs`, llama a `pthread_create` con un wrapper interno y hace `pthread_detach`. La función wrapper ejecuta el closure del usuario y gestiona el contador.
- **Auto-Linker:** El generador invoca GCC automáticamente tras escribir el `.c`, sin intervención manual.
- **I/O Thread-Safe:** `escribir()` y `escribir_linea()` usan `io_mutex` global para evitar entremezclado de salida entre hilos.

## Arquitectura Interna
- **Frontend:** Python (lexer, parser, generador de AST canónico en JSON).
- **Backend:** Generación de C puro + runtime propio (`synapse_rt.o`) con pool allocator, tensores y concurrencia pthread.
