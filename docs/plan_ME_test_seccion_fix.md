# Plan MTS: Reparación test_seccion_es_de_manual (H-TEST-FIX-1)

## Contexto

El test `tests/test_auditoria_alineacion.py::test_seccion_es_de_manual` falla por construcción: la cadena de prueba no contiene el carácter `§` que busca `.index("§")`. Esto genera un `ValueError: substring not found`.

## Cambio 1: Corregir cadena de prueba

```yaml
requisito: Manual 8 §6.3
texto: "Los tests deben ser verificables y reproducibles"
implementacion: Agregar el carácter § faltante a la cadena de prueba en test_seccion_es_de_manual
oraculo: tests/test_auditoria_alineacion.py
```

## Cambio 2: Eliminar registro obsoleto en MEMORIA

```yaml
requisito: Manual 8 §6.3
texto: "Los tests deben ser verificables y reproducibles"
implementacion: Eliminar la deuda H-TEST-FIX-1 de MEMORIA_PROYECTO.md
oraculo: tests/test_auditoria_alineacion.py
```

## Archivos a modificar

1. `tests/test_auditoria_alineacion.py` — Línea 22: cambiar `"cumple Manual 2 3 en el codigo"` por `"cumple Manual 2 §3 en el codigo"`
2. `MEMORIA_PROYECTO.md` — Eliminar la entrada "Preexistente detectado (NO corregido)" sobre test_seccion_es_de_manual

## Verificación

```bash
.venv\Scripts\python.exe -m pytest tests/test_auditoria_alineacion.py -v
python auditoria/verificar_alineacion.py
python auditoria/contrastar.py --plan docs/plan_ME_test_seccion_fix.md
```
