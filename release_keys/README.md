# Claves de release (Ed25519)

`public.pem` es la clave pública de confianza del producto y **sí se versiona**.
`private.pem` es la clave privada y **nunca se versiona** (`.gitignore` la excluye).

## Formatos aceptados

Las herramientas aceptan PEM, hex de 64 caracteres o raw de 32 bytes:

- `instaladores/common/verificar_firma.py`
- `nucleo/ed25519_signer.py`
- `distribuir.py` (a través de `ED25519_PRIVATE_KEY`)

## Custodia

- La clave privada de producción debe vivir en un gestor de secretos y exponerse
  en CI como `ED25519_PRIVATE_KEY` (hex de 64 caracteres).
- Para releases locales: `release_keys/private.pem` (ignorado por git).
- La clave pública debe publicarse junto al release (`synapse.pub` / `public.pem`).

## Rotación

```bash
.venv\Scripts\python.exe instaladores\common\verificar_firma.py --generar \
  --directorio release_keys --forzar
```

Rotar la clave invalida las firmas anteriores: hay que volver a firmar el release
y actualizar la clave pública distribuida en el instalador.
