Synapse Native | Infraestructura para la Soberanía
Bienvenido a la casa del ecosistema Synapse v2.0.

Synapse no es un experimento. Es un lenguaje de programación de sistemas de grado industrial, 100% auto-alojado, diseñado para resolver la crisis de soberanía de datos y la ineficiencia de los entornos de ejecución modernos. Nuestro objetivo es simple: llevar el máximo rendimiento nativo a la infraestructura crítica y la Inteligencia Artificial del borde (Edge AI), sin la burocracia de los intérpretes ni el peso de las máquinas virtuales.

⚡ La Visión
El software moderno ha olvidado cómo hablar con el silicio. Hemos construido una torre de abstracciones (intérpretes, recolectores de basura, gestores de paquetes pesados) que sacrifican el control del hardware en favor de una comodidad ilusoria.

Synapse rompe este paradigma garantizando:

El Monolito Operativo (Cero Dependencias): Todo el ecosistema (Compilador, Lexer, Parser, Analizador Semántico y Linker) vive en un solo binario autónomo (synapse.exe). No requiere Python, ni C, ni librerías dinámicas externas.

Seguridad Zero-Cost (RAII Estático): Memoria determinista sin Recolector de Basura (GC). El compilador es consciente del ámbito y teje la red de seguridad inyectando destructores automáticamente en tiempo de compilación. Cero fugas, cero pausas.

Concurrencia Zero-Copy: El paso de mensajes a través de canales sin estado compartido. El Analizador Semántico previene las condiciones de carrera (data races) por diseño estructural.

Gestión Criptográfica (Axon): Gestor de dependencias integrado nativamente. Las librerías se fijan mediante hashes inmutables SHA-256 (axon.lock), garantizando compilaciones 100% reproducibles.

📦 Arquitectura del Repositorio Único
En Synapse no fragmentamos el conocimiento. Todo el ecosistema reside en este único repositorio, garantizando que el compilador y su librería estándar evolucionen en perfecta sincronía:

/src: El código fuente del compilador (ahora escrito íntegramente en Synapse puro).

/librerias/std: El Sysroot nativo. Incluye redes TCP (std.net), deserializadores sin memoria dinámica manual (std.json, std.toml), interacción con el SO y fundaciones de tensores matemáticos.

/vscode-extension: Nuestro cliente LSP (Language Server Protocol) para una experiencia de desarrollo (DX) impecable.

/docs: El código fuente de "El Libro de Synapse" (nuestra especificación oficial).

🚀 Instalación de Fricción Cero
Instala Synapse v2.0 y configúralo en tu sistema operativo en menos de 5 segundos con un solo comando:

Windows (PowerShell Administrador):

PowerShell
powershell -c "iwr -useb https://github.com/synapse-native/synapse/releases/download/v2.0.0/instalar.ps1 | iex"
(Nota: El compilador ahora distribuye binarios nativos multiplataforma para Windows, Linux y macOS ARM64).

🛡️ Filosofía de Colaboración
No construimos para "lo que está de moda". Construimos para lo que es técnicamente superior y perdurable:

Estabilidad antes que características: Preferimos un lenguaje pequeño, estricto y predecible a uno masivo y caótico.

Soberanía del Código: Nuestra librería estándar no depende de librerías de terceros (cero left-pad). Synapse puede compilarse en entornos air-gapped (sin internet).

Auditoría y Transparencia: Todo el código en esta organización debe ser auditable a nivel de puntero de C, limpio y brutalmente eficiente.

📄 Licencia y Documentación
Licencia: Distribuido bajo la Licencia MIT. Creemos en el software como herramienta de libertad tecnológica.

Aprende Synapse: Lee nuestra documentación oficial y domina el manejo de memoria en El Libro de Synapse.

¿Quieres ser parte de la infraestructura del futuro? Únete a la singularidad.