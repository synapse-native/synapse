# Instaladores — Synapse Ecosystem

## Manual 9 §4.1: Distribución multiplataforma

### Estructura

```
instaladores/
├── windows/          # Windows (Inno Setup)
│   └── synapse.iss   # Script Inno Setup
├── linux/            # Linux (Bash)
│   └── install.sh    # Script de instalación
├── macos/            # macOS (.dmg/.pkg)
│   └── create_dmg.sh # Script para crear .dmg
└── common/           # Scripts compartidos
```

### Opciones de instalación

1. **Solo Synapse**: Compilador y runtime básico
2. **Ecosistema completo**: Synapse + Syquex + OpenSyn

### Windows

1. Descargar `synapse-setup.exe`
2. Ejecutar el instalador
3. Seleccionar componentes
4. Completar instalación

### Linux

```bash
chmod +x install.sh
./install.sh
```

### macOS

1. Descargar `synapse-x.x.x-macos.dmg`
2. Abrir el .dmg
3. Arrastrar Synapse a Applications

### Verificación de firmas

Todos los artefactos están firmados con Ed25519 (TweetNaCl).
Verificar con: `synapse verify <archivo>`
