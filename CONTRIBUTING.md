# Contribuir a Synapse

## Tests obligatorios

Todo Pull Request DEBE incluir uno o más tests que cubran el cambio propuesto.

## Validación local

Antes de abrir el PR, el código debe pasar:

```bash
# 1. Tests unitarios y de integración
python -m pytest tests/ -q --tb=short

# 2. Linter (flake8) — 0 errores
python -m flake8 . --count --statistics

# 3. Bootstrap — 0 errores GCC
python main.py nucleo/principal.syn 2>&1 | grep "error:" && \
  { echo "ERROR: Errores GCC en bootstrap"; exit 1; } || \
  echo "Bootstrap OK (0 errores GCC)"

# 4. Stage1 — compila
python main.py nucleo/principal.syn -o dist/bin/synapse_stage1.exe

# 5. Tests de instaladores
python -m pytest tests/installers/ -v
```

## CI/CD Pipeline

El proyecto utiliza GitHub Actions para:

| Workflow | Trigger | Propósito |
|----------|---------|-----------|
| `ci-tests.yml` | Push/PR a `main` | Tests multiplataforma, linting, bootstrap |
| `release-installers.yml` | Tag `v*` | Build instaladores y publicar en Releases |
| `release_matrix.yml` | Tag `v*` | Build binarios multiplataforma |
| `deploy-docs.yml` | Push a `main` | Despliegue mdBook a GitHub Pages |

### Jobs del CI (`ci-tests.yml`)

1. **test**: Corre en matrix 3 OS × 3 Python:
   - Linting (flake8) con configuración en `.flake8`
   - Tests unitarios e integración con cobertura
   - Compilación del runtime C
   - Smoke test: compilar programas Synapse de ejemplo

2. **bootstrap**: Corre SECUENCIALMENTE después de `test`:
   - Genera `synapse_unity.c` desde `nucleo/principal.syn`
   - Verifica 0 errores GCC
   - Compila Stage1 desde `nucleo/principal.syn`
   - Verifica que todos los tests pasan sin regresiones

### Instaladores (`release-installers.yml`)

Los instaladores se construyen automáticamente cuando se crea un tag `v*`:

- **Windows**: Inno Setup (`instalador_synapse.iss`)
- **Linux**: Script Bash (`instaladores/linux/install.sh`)
- **macOS**: DMG (`instaladores/macos/create_dmg.sh`)

Todos los instaladores incluyen:
- Verificación de integridad Ed25519
- Opciones de componentes
- Logging detallado
- Soporte para auto-actualización

## Estándares de código

- **Python**: Seguir PEP 8 con las excepciones definidas en `.flake8` (longitud máxima 100 chars)
- **Synapse**: Seguir `GUIA_ESTILO_IDIOMATICA.md`
- **C**: Seguir `INTERNOS_COMPILADOR.md` y convenciones del runtime
- **Instaladores**: Seguir Manual 9 §4.1

## Estructura de directorios

```
instaladores/
├── common/              # Componentes compartidos
│   ├── verificar_firma.py    # Verificación Ed25519
│   └── auto_actualizar.py    # Sistema de auto-actualización
├── linux/
│   ├── install.sh       # Instalador Bash
│   └── uninstall.sh     # Desinstalador
├── macos/
│   └── create_dmg.sh    # Creador de DMG
└── windows/
    └── synapse.iss      # Script Inno Setup
```

## Sin excepciones

Cualquier contribución que no cumpla estos puntos será rechazada sin revisión de contenido.
