# POLÍTICA DE MANUALES Y DOCUMENTACIÓN CANÓNICA

**Estado:** ratificada por el Arquitecto el 2026-11-19 (D-MAN-1/2/3, opción A).
**Ámbito:** `docs/manuales/` es la única fuente de verdad de producción. El
resto de la documentación (`docs/book2-desarrollo/`, `docs/reportes/`,
`docs/auditorias/`, `MEMORIA_PROYECTO.md`, etc.) es **informativa** y debe
alinearse con los manuales, nunca sustituirlos.
**Normas que implementa:** Manual 2 §1.2 (UTF-8 sin BOM), Manual 1 §7.4
(Definition of Done), Manual 9 §6.2 (validación cruzada en CI) y Manual 1 §5.7
(cero telemetría y soberanía del usuario).

---

## 1. Problema que resuelve

La ley del proyecto vive en archivos Markdown que se editan a mano, se citan
por sección y se indexan con `auditoria/indice_manual.py`. Esa cadena tiene
puntos frágiles ya observados:

- nombres de archivo no canónicos (caso histórico: `MANUAL  FASE 32 AGENTE DE
  CODIFICACIÓN.md` tenía doble espacio y no coincidía con `MANUAL N.md`);
- manuales y anexos que no entran al índice (Manual 31, Manual 32, anexos);
- citas `Manual N §X` que pueden apuntar a secciones inexistentes o cambiar de
  número;
- corrupción de encoding en documentos históricos y en comentarios de código;
- documentos informativos que repiten reglas y quedan desfasados;
- consolas Windows que muestran mojibake aunque el archivo sea UTF-8 válido,
  induciendo a "reparar" archivos que no están rotos.

La política convierte esas fragilidades en invariantes verificables. No cambia
el contenido de la ley: cambia cómo se conserva, se cita y se valida.

---

## 2. Invariantes

### I1. Una sola fuente de verdad

- Los manuales de producción son exclusivamente los archivos de
  `docs/manuales/`.
- Un documento informativo que contradiga un manual es un defecto del
  documento informativo.
- Ningún test, reporte, bitácora o comentario puede crear una regla nueva.
- Las decisiones ratificadas por el Arquitecto se registran como `D-*` o
  `H-*`; no se "corrigen" revirtiéndolas.

### I2. Nombres canónicos

- Manual numerado: `MANUAL <N>.md`, con un solo espacio y `N` sin ceros a la
  izquierda (`MANUAL 7.md`, no `MANUAL 07.md`).
- Anexos: `ANEXO-<TEMA>.md` o `ANEXO_<TEMA>.md`, en mayúsculas y sin número de
  manual.
- Pruebas obligatorias: `MANUAL_TESTS_OBLIGATORIOS.md`.
- Un archivo con `FASE`, doble espacio o acentos en el nombre no es canónico.
  Los manuales 31/32 fueron renombrados a `MANUAL 31.md` y `MANUAL 32.md`
  (D-MAN-1 opción A, 2026-11-19); sus nombres históricos quedan solo como
  alias de trazabilidad, nunca como segunda copia de la ley.

### I3. Encoding único

- Todo `.md` de `docs/manuales/` y todo documento informativo versionado debe
  ser **UTF-8 sin BOM**, con LF y newline final.
- Prohibido: U+FFFD, caracteres de control C1 (U+0080–U+009F), secuencias de
  doble codificación (`U+00C3`, `U+00C2`, `U+00E2`, `U+00EF`, `U+00F0` usadas
  como texto) y bytes inválidos.
- Los ejemplos históricos de mojibake se escriben como notación (`U+00C3`,
  `U+00C2`, etc.), nunca como caracteres literales.
- La consola no es evidencia: un `Get-Content` sin `-Encoding UTF8` puede
  mostrar un carácter de reemplazo (U+FFFD) sobre un archivo correcto. La
  verificación se hace con Python o con `Get-Content -Encoding UTF8`.

### I4. Índice completo y reproducible

- `docs/manuales/.indice.json` se genera con
  `.venv\Scripts\python.exe auditoria\indice_manual.py --generar`.
- El índice debe incluir todos los manuales numerados y todos los anexos
  declarados en el registro canónico.
- Cada entrada conserva: archivo, SHA-256 del contenido, secciones, línea de
  encabezado y oraciones citables con id estable.
- El índice no se edita a mano. Si un manual cambia, se regenera y se revisa
  el diff.
- Un índice desactualizado es un fallo de gate, no una advertencia.

### I5. Citas resolubles

- Toda cita de producción usa `Manual N §X` o `Manual N §X.Y`.
- `X` debe existir en el manual vigente y en el índice.
- Una cita sin sección (`Manual 7`) solo es válida para un requisito que
  afecta al manual completo; en la práctica se prefiere la sección puntual.
- Todo manual numerado debe estar en el índice; una cita a un manual no
  indexado se considera deuda hasta que el índice lo cubra.
- Renumerar una sección exige buscar y actualizar todas las citas del
  repositorio en el mismo ME.

### I6. Cambio de manual con expediente

Todo cambio de contenido en `docs/manuales/` sigue este orden:

1. Propuesta escrita: qué requisito cambia, por qué y qué citas afecta.
2. Aprobación explícita del Arquitecto si cambia una regla, renombra un
   manual o elimina una sección.
3. Edición UTF-8 sin BOM.
4. `indice_manual.py --generar`.
5. Barrido de citas (`rg "Manual N §"`) y corrección de referencias.
6. Ejecución de los tests-guarda que citan el manual.
7. Registro en el changelog de manuales y actualización de la versión.
8. Evidencia y reporte con el hash real del commit.

Sin los pasos 4–6 el cambio no está integrado, aunque el Markdown "se vea
bien".

### I7. Documentos informativos alineados

- Todo documento informativo lleva una cabecera visible:
  `> Documento informativo. La fuente de verdad es docs/manuales/.`
- No duplica el texto de un manual; lo resume y enlaza a la sección canónica.
- Si un documento informativo y un manual discrepan, gana el manual y se
  corrige el informativo.
- Los reportes históricos no se reescriben para "mejorar" su contenido; solo
  se corrige encoding, se añaden notas de vigencia o se marcan como
  históricos.
- `docs/book2-desarrollo/` y demás material de formación se revisa contra los
  manuales en un ME específico, no de forma oportunista.

### I8. Seguridad y privacidad

- La política no introduce telemetría, nube, MCP ni gateway externo
  (Manual 1 §5.7; Manual 32 §1.3).
- Las verificaciones son locales, deterministas y sin red.
- Los documentos no deben contener claves, tokens ni rutas personales.

---

## 3. Modelo canónico del índice

El índice debe poder responder, sin leer el manual completo:

```json
{
  "version": 2,
  "manuales": {
    "32": {
      "archivo": "docs/manuales/MANUAL 32.md",
      "alias": ["docs/manuales/MANUAL  FASE 32 AGENTE DE CODIFICACIÓN.md"],
      "sha256": "...",
      "secciones": [
        {"num": "1.3", "titulo": "Alcance Explícitamente Descartado", "linea": 38,
         "oraciones": [{"id": "...", "linea": 40, "texto": "..."}]}
      ]
    }
  }
}
```

Reglas:

- `version` sube cuando cambia el esquema, no cuando cambia un manual.
- `sha256` permite detectar ediciones sin regeneración.
- `alias` permite migrar nombres sin romper citas históricas.
- Los ids de oración son hashes del texto normalizado; si el texto cambia,
  cambia el id y el gate lo detecta.
- Los manuales sin sección numérica se indexan por título y línea, pero no
  pueden ser citados como `§N`.

---

## 4. Gate automático propuesto

El ME `r271_manuales_canonicos` implementa
`auditoria/verificar_manuales.py` (stdlib only, sin red) con estos comandos:

```text
python auditoria/verificar_manuales.py --encoding
python auditoria/verificar_manuales.py --nombres
python auditoria/verificar_manuales.py --indice
python auditoria/verificar_manuales.py --citas
python auditoria/verificar_manuales.py --todo
```

Comportamiento:

| Comando | Comprueba | Falla si |
|---|---|---|
| `--encoding` | UTF-8 válido, sin BOM, sin U+FFFD, sin C1, sin patrones de doble codificación | hay un archivo enfermo |
| `--nombres` | `MANUAL N.md`, anexos y alias declarados | hay un nombre no canónico sin alias |
| `--indice` | cobertura completa, SHA-256, secciones y oraciones | el índice no cubre un manual o está desactualizado |
| `--citas` | `Manual N §X` resoluble contra el índice | una cita apunta a una sección inexistente |
| `--todo` | todo lo anterior | cualquier fallo |

Requisitos del gate:

- Salida legible con archivo, línea y causa; rc=0 solo si todo pasa.
- Modo `--json` para CI, además del modo humano.
- No reescribe archivos ni "arregla" nada: detecta y reporta.
- Se ejecuta en pre-commit y en CI (Manual 9 §6.2).
- Un fallo no se silencia con `--no-verify`; se corrige el archivo o se
  registra una excepción aprobada por el Arquitecto.

---

## 5. Protocolo de consola Windows

Para leer sin falsos positivos:

```powershell
Get-Content -LiteralPath "docs\manuales\MANUAL 7.md" -Encoding UTF8
```

Para inspeccionar bytes y caracteres:

```powershell
.venv\Scripts\python.exe -c "from pathlib import Path; t=Path('docs/manuales/MANUAL 7.md').read_text(encoding='utf-8'); print(t.count('\ufffd'), t.count('\u00c3'), t.count('\u00c2'))"
```

Prohibido para editar manuales:

- `Set-Content` o `Out-File` sin `-Encoding utf8` en PowerShell 5.1.
- `Get-Content` + `Set-Content` como "normalizador" (puede duplicar la
  codificación).
- Añadir BOM "para que se vea bien en la consola".
- Reescribir un archivo entero para corregir una línea.

La edición se hace con una herramienta que preserve UTF-8, o con un script
Python que lea y escriba bytes de forma explícita.

---

## 6. Estado actual (2026-11-18)

Verificado con lectura de bytes, no con la consola:

- `docs/manuales/*.md`: UTF-8 válido, sin BOM, sin U+FFFD, sin C1 y sin
  patrones de doble codificación. **No requieren reparación de contenido.**
- `docs/auditorias/AUDITORIA_ALINEACION_MANUALES.md`: tenía corrupción real
  (triple codificación en amplias zonas). Reparado a UTF-8 sin BOM; se
  conservaron las 1.275 líneas y no quedan patrones enfermos.
- `docs/reportes/R205.md` y `MEMORIA_PROYECTO.md`: los únicos restos eran
  ejemplos históricos literales; se reescribieron como notación U+00C2/U+00C3.
- `docs/manuales/.indice.json`: cubre 11 manuales (1–9, 31 y 32) y los tres
  anexos declarados; 395 secciones y 1.649 oraciones citables.
- `docs/manuales/MANUAL 31.md` y `MANUAL 32.md`: nombres canónicos desde
  D-MAN-1 (2026-11-19). Los nombres históricos con `FASE` quedan como alias
  de trazabilidad en el índice, sin archivo duplicado.
- Comentarios y cadenas de producción con U+FFFD o C1: `runtime/core/axon.h`,
  `runtime/core/concurrency.c`, `runtime/core/debug.c`, `std/texto.syn`,
  `tests/validate_distillation.c` y `axon/axon_rt.c`. No se corrigen en esta
  tarea documental: requieren un ME de código con compilación y tests.

---

## 7. Decisiones ratificadas (2026-11-19)

| Id | Decisión | Opción ratificada |
|---|---|---|
| D-MAN-1 | Nombre canónico de Manual 31/32 | **A:** renombrar a `MANUAL 31.md` y `MANUAL 32.md`, conservando el alias histórico para citas y trazabilidad; el contenido no cambia. |
| D-MAN-2 | Estatus de los anexos | **A:** indexarlos como material de apoyo citable, sin número de manual. |
| D-MAN-3 | Alcance del barrido de `docs/book2-desarrollo/` | **A:** barrido único en `r282_docs_informativos`; el resto queda congelado mientras tanto. |

Las decisiones están ratificadas. Cualquier cambio posterior de nombre,
numeración o alcance exige una nueva `D-MAN` y aprobación explícita del
Arquitecto.

---

## 8. Criterios de aceptación de la política

1. `auditoria/verificar_manuales.py --todo` rc=0 sobre el árbol limpio.
2. Un fixture con BOM, U+FFFD, C1, nombre no canónico o índice desactualizado
   produce rc=1 y un mensaje que identifica el archivo y la línea.
3. Las citas `Manual N §X` de producción resuelven contra el índice; las que
   no, aparecen como deuda con resolución asignada.
4. El índice incluye todos los manuales y anexos declarados, con SHA-256.
5. El pre-commit y el CI ejecutan el gate sin `--no-verify`.
6. Los documentos informativos llevan la cabecera de vigencia y no contradicen
   la ley.
7. Cero telemetría, cero red y cero dependencias externas en el gate.
8. Manual 31/32 usan `MANUAL N.md`; los anexos se citan por su clave, nunca
   como `Manual N`.

---

*Esta política no es un manual: es el procedimiento que protege a los
manuales. Cualquier cambio en ella sigue el mismo protocolo de aprobación y
evidencia que un cambio de gobernanza.*
