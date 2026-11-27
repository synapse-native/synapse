# Expediente de alineación r202_release_signing

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: a48ecf5a77bedfc0

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## distribuir.py
- manual: 9
  seccion: 6.3
  cita: "Cada artefacto se firma con la clave privada Ed25519 del proyecto."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: distribuir.py:4
  oraculo: tests/integration/test_artifact_signing.py

- manual: 9
  seccion: 2.1
  cita: "El proceso de empaquetado genera artefactos para las plataformas soportadas:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: distribuir.py:3
  oraculo: tests/integration/test_distribucion.py

## instaladores/common/verificar_firma.py
- manual: 9
  seccion: 6.3
  cita: "Cada artefacto se firma con la clave privada Ed25519 del proyecto."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: instaladores/common/verificar_firma.py:2
  oraculo: tests/installers/test_firma.py

- manual: 9
  seccion: 4.1
  cita: "Archivos de firma (`.sig`) y checksums (`.sha256`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: instaladores/common/verificar_firma.py:3
  oraculo: tests/installers/test_firma.py
