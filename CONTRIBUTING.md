# Protocolo QA-Driven — Synapse

## 🧪 Tests obligatorios

Todo Pull Request DEBE incluir uno o más tests en `tests/e2e/` que cubran el cambio propuesto.

## ✅ Validación local

Antes de abrir el PR, el código debe pasar:

```bash
# 1. Tests unitarios y de integración
python -m pytest tests/ -q --tb=short

# 2. Linter (flake8) — 0 errores
python -m flake8 . --count --statistics

# 3. Bootstrap — 0 errores GCC
python main.py nucleo/principal.syn 2>&1 | grep "error:" && \
  { echo "❌ ERROR: Errores GCC en bootstrap"; exit 1; } || \
  echo "✅ Bootstrap OK (0 errores GCC)"

# 4. Stage1 — compila
python main.py src/main.syn -o dist/bin/synapse_stage1.exe
```

## 🔄 CI/CD Pipeline

El proyecto utiliza GitHub Actions para:

| Workflow | Trigger | Propósito |
|----------|---------|-----------|
| `ci-tests.yml` | Push/PR a `main` | Tests (3 OS × 3 Python), linting, bootstrap verification |
| `release-binaries.yml` | Tag `v*` | Build binarios multiplataforma y subir a Release |
| `windows_release.yml` | Tag `v*` o manual | Build Windows estático |
| `deploy-docs.yml` | Push a `main` (docs/) | Despliegue de documentación mdBook a GitHub Pages |

### Jobs del CI (`ci-tests.yml`)

1. **test**: Corre en matrix 3 OS × 3 Python:
   - Linting (flake8) con configuración en `.flake8`
   - Tests unitarios e integración con cobertura
   - Compilación del runtime C
   - Smoke test: compilar programas Synapse de ejemplo

2. **bootstrap**: Corre SECUENCIALMENTE después de `test`:
   - Genera `synapse_unity.c` desde `nucleo/principal.syn`
   - Verifica 0 errores GCC
   - Compila Stage1 desde `src/main.syn`
   - Verifica que todos los tests pasan sin regresiones

## 📏 Estándares de código

- **Python**: Seguir PEP 8 con las excepciones definidas en `.flake8` (longitud máxima 100 chars)
- **Synapse**: Seguir `GUIA_ESTILO_IDIOMATICA.md`
- **C**: Seguir `INTERNOS_COMPILADOR.md` y convenciones del runtime

## 🚫 Sin excepciones

Cualquier contribución que no cumpla estos puntos será rechazada sin revisión de contenido.
