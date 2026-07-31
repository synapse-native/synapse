MANUAL 6: GESTOR DE PAQUETES AXON
Archivo: 06_GESTOR_PAQUETES_AXON.md
Versión: 5.1.1-industrial (v2.0 runtime)
Propósito: Especificar el gestor de paquetes descentralizado y criptográficamente verificado.

6.1 Principios de Seguridad (Zero Trust)
Axon no confía en repositorios centralizados. Opera bajo estas reglas:

Sin scripts: No se ejecutan preinstall/postinstall. La descarga es pura transferencia de texto.

Firma obligatoria: Todo paquete debe estar firmado con Ed25519.

Lockfile determinista: axon.lock con SHA-256 garantiza builds reproducibles.

Path traversal protection: Bloquea ../ en nombres de archivo dentro del TAR.

Offline-first: Busca localmente antes de intentar descargar.

6.2 Manifiesto axon.toml (Esquema completo)
toml
[paquete]
nombre = "mi-libreria"
version = "1.2.3"
autor = "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
tipo = "libreria"                 # "libreria" o "ejecutable"
punto_entrada = "lib.syn"

[dependencias]
synapse-std = { version = "^0.2.0" }
synapse-net = { version = "~1.0.0" }
Validaciones del compilador:

Campo	Validación	Código de error
autor	64 caracteres hexadecimales	ERR_AXON_COMPROMISED si no
version	SemVer válido	ERR_AXON_VERSION
dependencias.version	Restricción SemVer o exacta	ERR_AXON_VERSION
6.3 Restricciones SemVer (Soportadas)
"1.2.3": Exacta

"^1.2.3": Compatible (>=1.2.3, <2.0.0)

"^0.2.3": Especial (>=0.2.3, <0.3.0)

"~1.2.3": Parche (>=1.2.3, <1.3.0)

6.4 Criptografía Ed25519 (TweetNaCl)
API C:

c
void crypto_sign_ed25519_tweet_keypair(unsigned char* pk, unsigned char* sk);
int crypto_sign_ed25519_tweet(unsigned char* sm, unsigned long long* smlen,
                              const unsigned char* m, unsigned long long mlen,
                              const unsigned char* sk);
int crypto_sign_ed25519_tweet_open(unsigned char* m, unsigned long long* mlen,
                                   const unsigned char* sm, unsigned long long smlen,
                                   const unsigned char* pk);
Formato de .sig: 64 bytes binarios (sin cabecera).
Pipeline de verificación en axon fetch:

Descargar <paquete>.tar y <paquete>.tar.sig.

Leer autor del axon.toml (clave pública).

Calcular SHA-256 del TAR.

Verificar firma. Si falla → purgar y abortar con ERR_AXON_COMPROMISED.

Si pasa, extraer TAR con protección path traversal.

6.5 Lockfile (axon.lock)
toml
[lock]
"mi-libreria" = { version = "1.2.3", hash = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" }
Verificación en tiempo de compilación:

c
int _syn_axon_verificar_lock(const char* paquete, const char* version,
                             const char* tar_path, const char* lock_path);
// Retorna 0 si OK, -1 si ERR_AXON_COMPROMISED.
6.6 Comandos Axon (CLI)
Comando	Descripción
synapse axon init	Crea axon.toml por defecto.
synapse axon fetch	Resuelve dependencias localmente (sin red).
synapse axon fetch --online	Descarga desde HTTP.
synapse axon publish	Publica paquete en Axon Hub (IPFS).
synapse axon verify	Verifica firma y hashes.
synapse axon search	Busca en el índice descentralizado.
6.7 Axon Hub Descentralizado (v5.0)
Requisitos para publicación:

Mínimo 3 firmas Ed25519 de mantenedores distintos.

Suite de tests de verificación adjunta.

Reputación del mantenedor > 3.0 (escala 0-5).

Estructura en IPFS:

json
{
  "nombre": "mi-libreria",
  "version": "1.2.3",
  "mantenedores": ["pk1", "pk2", "pk3"],
  "hash_sha256": "...",
  "hash_ipfs": "Qm...",
  "firmas": ["sig1", "sig2", "sig3"],
  "tests": ["test_assert.syn", ...],
  "reputacion": 4.5
}
6.8 Tests Obligatorios para esta Etapa
Test	Comando	Criterio
Ed25519 firma/verificación	pytest tests/unit/test_axon_crypto.py -v	100% pass
Path traversal	pytest tests/security/test_path_traversal.py -v	Bloquea ../
Lockfile	pytest tests/integration/test_axon_lock.py -v	SHA-256 match
Axon Hub	pytest tests/integration/test_axon_hub.py -v	Publicar/verificar/buscar OK