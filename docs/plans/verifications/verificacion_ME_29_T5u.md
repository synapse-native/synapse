# Verificación ME_29_T5u

## Cumple / No Cumple

### Manual 9 §5.3 (descarga/verificación)
- ✅ `instalar_modelo()` declarada en `opensyn/installer.syn`
- ✅ `descargar_modelo()` existente (implementado en ME_29_T5)
- ✅ Verificación SHA-256 presente (`_syn_sha256_archivo`, `_syn_eliminar_archivo`)
- ✅ Test: `test_instalar_modelo_funcion` — PASS

### Manual 9 §5.4 (config.toml)
- ✅ `ConfigInfo` struct con todos los campos requeridos
- ✅ `generar_config()` implementada
- ✅ `escribir_config()` implementada, escribe `~/.opensyn/config.toml`
- ✅ `_syn_escribir_archivo()` implementada en `runtime/core/modelo.c`
- ✅ Test: `test_config_info_estructura` — PASS
- ✅ Test: `test_escribir_config_funcion` — PASS
- ✅ Test: `test_config_toml_generado` — PASS

### Manual 9 §5.6 (modelos.toml)
- ✅ `opensyn/modelos.toml` existe con 5 modelos
- ✅ Formato TOML con [modelos] y campos url/sha256/tam
- ✅ Test: `test_modelos_toml_estructura` — PASS

### Manual 7 §2.3 (instalador)
- ✅ `opensyn/installer.syn` compila (rc=0)
- ✅ Ejecutable generado y ejecutado
- ✅ Test: `test_installer_opensyn` — PASS
