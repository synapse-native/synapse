# Plan ME_29_T3_mod — Modificación test_gestion_modelos (TDD MTO)

## Bloque MTS (método de trabajo seguro)

### requisito:
Manual 7 §7: "Gestión de modelos — OpenSyn gestiona modelos (descargar/cachear)"
Manual 9 §5.3: "El modelo se descarga desde Hugging Face o Axon Hub, y se verifica su integridad mediante SHA‑256"

### texto:
El test debe verificar que OpenSyn implementa la gestión de modelos:
1. Función seleccionar_modelo() existe y selecciona según VRAM
2. Función descargar_modelo() existe y verifica SHA-256
3. Función instalar_modelo() orquesta la instalación
4. Estructura ModeloInfo tiene campos requeridos (nombre, url, sha256, tamano_aprox)

### implementacion:
Modificar `tests/opensyn/test_model_mgmt.py` para:
1. Verificar que opensyn/installer.syn existe
2. Verificar que contiene las funciones requeridas (seleccionar_modelo, descargar_modelo, instalar_modelo)
3. Verificar que contiene la estructura ModeloInfo con campos correctos
4. Verificar que selecciona modelo según VRAM (umbrales 4GB, 8GB, 12GB)
5. Verificar que verifica SHA-256 en descarga

### oraculo:
- opensyn/installer.syn existe → PASS
- Funciones declaradas → PASS
- Estructura ModeloInfo completa → PASS
- Selección por VRAM con umbrales → PASS
- Verificación SHA-256 → PASS

## Archivos a modificar
- `tests/opensyn/test_model_mgmt.py`

## Citas de manuales
- Manual 7 §7 (pruebas de OpenSyn)
- Manual 9 §5.3 (descarga y verificación SHA-256)
