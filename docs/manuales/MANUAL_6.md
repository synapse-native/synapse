MANUAL 6: GESTOR DE PAQUETES AXON
Archivo: 06_GESTOR_PAQUETES_AXON.md
Versión: 5.0.0 (v2.0 runtime)
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
version	SemVer válido (ej. 1.2.3)	ERR_AXON_VERSION
dependencias.version	Restricción SemVer o exacta	ERR_AXON_VERSION
6.3 Restricciones SemVer (Soportadas)
Sintaxis	Semántica	Ejemplo: 1.2.3
"1.2.3"	Exacta	Solo 1.2.3
"^1.2.3"	Compatible (>=1.2.3, <2.0.0)	1.2.3 a 1.9.9
"^0.2.3"	Especial para 0.x: (>=0.2.3, <0.3.0)	0.2.3 a 0.2.9
"~1.2.3"	Parche (>=1.2.3, <1.3.0)	1.2.3 a 1.2.9
6.4 Criptografía Ed25519 (TweetNaCl)
Generación de par de claves (C API):

c
void crypto_sign_ed25519_tweet_keypair(unsigned char* pk, unsigned char* sk);
Firmar:

c
int crypto_sign_ed25519_tweet(unsigned char* sm, unsigned long long* smlen,
                              const unsigned char* m, unsigned long long mlen,
                              const unsigned char* sk);
Verificar:

c
int crypto_sign_ed25519_tweet_open(unsigned char* m, unsigned long long* mlen,
                                   const unsigned char* sm, unsigned long long smlen,
                                   const unsigned char* pk);
Formato de .sig: 64 bytes binarios (sin cabecera).

Pipeline de verificación en axon fetch:

Descargar <paquete>.tar y <paquete>.tar.sig.

Leer autor del axon.toml (clave pública).

Calcular SHA-256 del TAR.

Verificar firma con la clave pública.

Si falla → purgar archivos temporales y abortar con ERR_AXON_COMPROMISED.

Si pasa, extraer TAR con protección path traversal.

6.5 Lockfile (axon.lock)
Formato TOML:

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
synapse axon fetch --online	Descarga desde HTTP (localhost:8080 o configurado).
synapse axon publish (v5.0)	Publica paquete en Axon Hub (IPFS).
synapse axon verify (v5.0)	Verifica firma y hashes de un paquete descargado.
synapse axon search (v5.0)	Busca en el índice descentralizado.
6.7 Axon Hub Descentralizado (v5.0)
Arquitectura: IPFS + registro de mantenedores.

Requisitos para publicación:

Mínimo 3 firmas Ed25519 de mantenedores distintos.

Suite de tests de verificación adjunta.

Reputación del mantenedor > 3.0 (escala 0-5).

Estructura de paquete en IPFS:

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
