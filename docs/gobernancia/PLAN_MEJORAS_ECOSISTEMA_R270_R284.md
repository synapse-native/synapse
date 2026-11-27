# PLAN DE MEJORAS DEL ECOSISTEMA — FRENTE H (r270–r284)

**Fecha:** 2026-11-18
**Base:** `release/v8.1.0-industrial`, HEAD `1a408c2`
**Naturaleza:** cartera de programa, no un `plan_ME`. Cada ME se ejecuta con su
propio `docs/plan_ME_<id>.md` (bloques `requisito:`/`texto:`/`implementacion:`/
`oraculo:`), su expediente, su oráculo y su reporte. Este documento fija el
contenido mínimo y el orden; no sustituye al MTS.
**Alcance:** cerrar las deficiencias detectadas en la auditoría crítica del
ecosistema, con prioridad P0 (bloqueantes de release), P1 (calidad y
distribución) y P2 (deuda estructural).
**Restricciones de política:** Manual 1 §5.7 y Manual 32 §1.3. Nada de nube,
telemetría, MCP, gateway externo, multi-proveedor ni panel GUI. OpenSyn sigue
siendo 100% local y opt-in. Los tests existentes son inmutables salvo
aprobación explícita del Arquitecto.

> Los ids r270–r284 están libres: r218/r219, r240–r253 y r256 ya están
> ocupados. `r252b_emision_paridad` sigue reservado en
> `docs/plan_maestro_deudas.md`; r270 lo absorbe o lo referencia, no lo
> duplica.

---

## 0. Matriz de prioridad

| Id | ME | Prioridad | Deficiencia que cierra | Depende |
|---|---|---|---|---|
| `r270_bootstrap_emision_paridad` | Cerrar el bootstrap S2==S3 | P0 | H-R252-1: S1 modular `-static` vs S2 unity sin `-static` | — |
| `r271_manuales_canonicos` | Índice, nombres y gate de manuales | P0 | Manual 31/32 fuera del índice, nombre no canónico, sin gate de encoding | D-MAN-1/2 RATIFICADAS 2026-11-19 |
| `r272_docs_encoding` | Reparación y normalización documental | P0 | Corrupción real de la auditoría y ejemplos históricos | r271 |
| `r273_installer_modelo_grande` | Instalador con GGUF grande | P0 | Timeout de 10 s y verificación de 873 MB | — |
| `r274_gates_independientes` | Gates que no viven dentro del build | P0 | H-R252-2, H-CONTROL-1/2/3, binarios stale | r270 |
| `r275_opensyn_e2e_bench` | E2E real y benchmark local | P1 | Sin E2E con `llama-server` ni umbrales medidos | r273 |
| `r276_multiplataforma_release` | Instalación limpia y release | P1 | Linux/macOS sin evidencia; VM limpia pendiente | r270, r273 |
| `r277_contracts_audit` | Auditoría de contratos | P1 | r253 parcial: no se probó “0 funciones públicas sin contrato” | — |
| `r278_ide_debugger` | LSP/VS Code y debugger | P1 | r240/r241 parciales; comandos IA y time-travel sin E2E | r275 |
| `r279_suite_rapida` | Suite determinista y acotada | P1 | Suite de integración >2 h y fallos ambientales | r273, r274 |
| `r280_codigo_encoding` | Encoding en código de producción | P1 | U+FFFD/C1/mojibake en runtime, std y fuentes generadas | r271 |
| `r281_d9_dead_code` | D-9, duplicados y código muerto | P2 | Módulos >1200 líneas y duplicados de `std/texto.syn` | r279 |
| `r282_docs_informativos` | Alinear documentación informativa | P2 | `book2`, reportes y bitácoras desfasados | r271 |
| `r283_manual_versioning` | Versionado y changelog de manuales | P2 | Sin changelog, deprecación ni ids estables | r271, r282 |
| `r284_observabilidad_local` | Diagnóstico local opt-in | P2 | Falta de diagnóstico sin romper “cero telemetría” | — |

---

## 1. Reglas comunes de ejecución

1. **MTS completo:** plan, lectura registrada, código, oráculo, gates, commit,
   documentación post-commit. Sin `--no-verify`.
2. **Manual primero:** cada ME cita la sección que implementa. Si el manual y
   el código discrepan, se corrige el código; si el manual está mal, se
   detiene y se pregunta.
3. **Tests inmutables:** no se “arregla” un test para que pase. Un test nuevo
   debe probar comportamiento, no grep de fuente.
4. **Cero deuda sin seguimiento:** todo hallazgo se resuelve o se registra con
   resolución asignada.
5. **Cero red en los gates:** las verificaciones son locales y deterministas.
6. **Un ME, un commit:** no se mezclan MEs ni archivos de otros agentes.
7. **Evidencia:** hash real, reporte, fila de bitácora y memoria al cerrar.

---

## 2. MEs P0

### r270_bootstrap_emision_paridad — P0

**Deficiencia.** El sello S2==S3 no cierra: la etapa 2 la produce S1 con
`-static` y la etapa 3 la produce S2 en modo unity sin `-static`. Difieren
2.0 MB de 2.1 MB; no es ruido de timestamps. Mientras exista esa divergencia,
la regla de hierro no se cumple y todo gate S2 es frágil.

**Requisito.** Manual 1 §6 (regla de hierro del bootstrap); Manual 9 §6.1
(bootstrap exitoso en cada target); Manual 9 §6.2 (verificación en CI/CD).

**Texto literal.** “Ninguna característica nueva puede romper el *bootstrap*
(etapas 0→1→2→3 con diff binario 0).”

**Implementación.**
- Decidir con el Arquitecto la invocación canónica de GCC (modular/unity,
  `-static`/sin `-static`) y documentarla en el plan del ME.
- Unificar `build.py` y la emisión de `nucleo/principal.syn` para que S1 y S2
  usen la misma receta.
- Extender el oráculo existente
  `tests/auditoria/test_oraculos_r252_paridad_bootstrap.py` con un modo que
  compare etapa 2 y etapa 3 y falle si el hash o el tamaño difieren.
- Eliminar la duplicación de `sha256sum` en el job de CI; el job invoca el
  oráculo.
- Guard de binarios stale: `synapse.exe` y `dist/bin/synapse.exe` deben
  corresponder a la etapa 2.

**Oráculo.** `python auditoria/oraculos/oraculo_r252_paridad_bootstrap.py
--construir --estricto` rc=0; hashes iguales; sin binarios stale; el job
`bootstrap` de CI falla si el sello falla.

**Depende.** — (bloquea a r274 y r276).

**Política.** Si la decisión canónica afecta la distribución, se pregunta
antes de cambiar; no se usa force-push ni se reescribe la historia.

---

### r271_manuales_canonicos — P0

**Deficiencia (histórica).** `docs/manuales/.indice.json` cubría solo los
manuales 1–9. Manual 31, Manual 32 y los anexos no se indexaban; el archivo
`MANUAL  FASE 32 AGENTE DE CODIFICACIÓN.md` tenía doble espacio y no coincidía
con `MANUAL N.md`; no existía un gate que detectara BOM, U+FFFD, C1 o doble
codificación. Las citas `Manual 32 §1.3` no podían verificarse.

**Estado.** D-MAN-1/2 ratificadas el 2026-11-19 (opción A): Manual 31/32 se
renombraron a `MANUAL 31.md` y `MANUAL 32.md`; los anexos quedan como material
de apoyo citable, sin número de manual.

**Requisito.** Manual 2 §1.2 (UTF-8 sin BOM); Manual 1 §7.4 (Definition of
Done); Manual 9 §6.2 (validación cruzada en CI).

**Texto literal.** “Todos los archivos fuente deben estar codificados en
**UTF-8 sin BOM**.”

**Implementación.**
- Registrar el conjunto canónico: manuales numerados y anexos de apoyo.
- Renombrar Manual 31/32 a `MANUAL 31.md` y `MANUAL 32.md`, conservando el
  alias histórico en el índice (D-MAN-1 opción A).
- Extender `auditoria/indice_manual.py` para indexar todos los manuales y
  anexos declarados, con `sha256`, secciones y alias de trazabilidad.
- Añadir `auditoria/verificar_manuales.py` (stdlib only, sin red) con
  `--encoding`, `--nombres`, `--indice`, `--citas` y `--todo`, según
  `docs/gobernancia/POLITICA_MANUALES.md`.
- Regenerar `.indice.json` y revisar el diff; no editar el JSON a mano.
- Cablear el gate en pre-commit y CI, sin `--no-verify`.
- Indexar los anexos como apoyo citable sin número de manual (D-MAN-2 opción
  A); no se citan como `Manual N`.

**Oráculo.** `tests/auditoria/test_verificar_manuales.py`: fixture limpio
rc=0; fixture con BOM, U+FFFD, C1, nombre no canónico, índice desactualizado y
cita rota rc=1 con archivo/línea. `python auditoria/verificar_manuales.py
--todo` rc=0 sobre el árbol limpio.

**Depende.** D-MAN-1/2 ratificadas (2026-11-19, opción A).

**Política.** No se renombra ni se mueve un manual de producción sin una
decisión `D-MAN` vigente. No se añade BOM. No se reescribe contenido para
“mejorar” el Markdown.

---

### r272_docs_encoding — P0

**Deficiencia.** `docs/auditorias/AUDITORIA_ALINEACION_MANUALES.md` tenía
corrupción real por triple codificación (miles de secuencias U+00C3/U+00C2 y
controles C1). `docs/reportes/R205.md` y `MEMORIA_PROYECTO.md` conservaban
ejemplos literales de mojibake. La consola de Windows muestra un carácter de
reemplazo (U+FFFD) sobre UTF-8 correcto y ha inducido a “reparar” archivos
sanos.

**Requisito.** Manual 2 §1.2; Manual 1 §7.4.

**Texto literal.** “El lexer rechazará cualquier archivo que contenga
caracteres no válidos en UTF‑8.”

**Implementación.**
- Reparar la auditoría con decodificación iterativa controlada, preservando
  líneas y contenido; escribir UTF-8 sin BOM.
- Reescribir los ejemplos históricos como notación U+00C2/U+00C3, sin perder
  el significado.
- Añadir la cabecera “documento informativo” a los documentos que aún no la
  tengan, empezando por la auditoría y los reportes históricos.
- Verificar con bytes, no con `Get-Content` sin `-Encoding UTF8`.
- No tocar manuales de producción: ya son UTF-8 válido.

**Oráculo.** `python auditoria/verificar_manuales.py --encoding --docs`
rc=0; la auditoría conserva 1.275 líneas; scan de `AUDITORIA`, `R205` y
`MEMORIA` con 0 U+FFFD, 0 C1 y 0 patrones de doble codificación; `git diff`
solo de encoding.

**Depende.** r271 (gate) o un script temporal equivalente.

**Política.** No se usa `Set-Content`/`Out-File` de PowerShell 5.1 para
normalizar; no se añade BOM; no se “corrigen” manuales sanos.

---

### r273_installer_modelo_grande — P0

**Deficiencia.** `test_installer_opensyn` falla por timeout de 10 s: el
instalador tarda unos 16.3 s verificando un GGUF local de 873 MB. El test es
preexistente y ajeno, pero bloquea la certificación de release y oculta si el
instalador funciona o solo es lento.

**Requisito.** Manual 9 §5.3 (descarga y verificación SHA‑256); Manual 9 §5.5
(prueba de humo); Manual 9 §6.1 (instalador probado en sistemas limpios);
Manual 7 §6.1 (instalación de un solo clic).

**Texto literal.** “El modelo se descarga desde Hugging Face o Axon Hub, y se
verifica su integridad mediante SHA‑256.”

**Implementación.**
- Verificar por streaming con buffer acotado; no cargar el GGUF completo en
  memoria.
- Aceptar un manifiesto de checksum firmado o cacheado para no rehashear
  873 MB en cada arranque; si no hay manifiesto, hashear una vez y cachear el
  resultado con ruta, tamaño y mtime.
- Medir y reportar el tiempo de verificación; distinguir “lento” de “colgado”
  con timeout configurable y mensaje honesto.
- No falsear el resultado ni saltarse la verificación.
- Probar con un archivo disperso grande y con el GGUF real local.

**Oráculo.** Test nuevo
`tests/integration/test_installer_modelo_grande.py` (no modifica el test
existente): verifica streaming, caché, timeout y rc; el test existente debe
pasar o quedar registrado como deuda ambiental con causa medida.

**Depende.** — (bloquea r275/r276/r279).

**Política.** No se modifica el test existente sin aprobación. No se descarga
nada en el gate; el E2E real es opt-in y local.

---

### r274_gates_independientes — P0

**Deficiencia.** El sello del bootstrap vivía solo dentro de `build.py` y del
job de CI (H-R252-2: “un gate que solo vive dentro de un script de build no es
un gate”). Antes, el CI pasaba `--sin-oraculos` y el hook solo ejecutaba
oráculos con una variable que nadie definía (H-CONTROL-1/2/3). Un exe stale
puede “verificar” un binario viejo.

**Requisito.** Manual 9 §6.2 (validación cruzada en CI/CD); Manual 9 §6.1
(checklist final); Manual 1 §7.4 (DoD).

**Texto literal.** “La verificación del bootstrap (diff 0 bytes).”

**Implementación.**
- Inventariar los gates críticos: bootstrap, alineación, contratos, firma,
  instalador, encoding.
- Cada gate tiene un oráculo ejecutable e independiente, invocado por
  pre-commit y CI; no se acepta un gate que solo exista dentro de otro script.
- Fallar si el oráculo se salta, devuelve vacío o no produce una marca
  verificable.
- Guard de frescura de binarios: hash/fecha contra la etapa 2.
- Prueba de mutación: romper a propósito el sello y comprobar que el gate
  falla; restaurar.

**Oráculo.** `tests/auditoria/test_gates_independientes.py` con fixtures de
mutación; `contrastar` y `alineacion` ejecutan sus oráculos por defecto; CI
sin `--sin-oraculos`; rc=1 cuando falta un gate.

**Depende.** r270.

**Política.** No se debilita un test para que pase; no se usa `--no-verify`.

---

## 3. MEs P1

### r275_opensyn_e2e_bench — P1

**Deficiencia.** Hay dobles de LLM y fixtures GGUF, pero no un E2E de chat +
tools + validación contra `llama-server` real ni un benchmark medido contra
los umbrales de Manual 7 §7.2. Sin eso, “OpenSyn funciona” es una afirmación
no verificada.

**Requisito.** Manual 7 §7.2 (rendimiento); Manual 7 §7.3 (privacidad y
seguridad); Manual 7 §8 (flujo completo); Manual 9 §5.5 (prueba de humo).

**Texto literal.** “Latencia de inferencia: < 1s para prompts cortos (modelo
7B en GPU).” / “Cero telemetría: Verificado con monitoreo de red (sin
conexiones salientes).”

**Implementación.**
- E2E opt-in (`OPENSYN_E2E=1` y ruta a GGUF) que arranca `llama-server` local,
  ejecuta chat, una tool con aprobación y validación con `synapse check`.
- Benchmark reproducible: latencia, tokens/s y VRAM; reporte con máquina,
  modelo, cuantización y fecha.
- En CI sin modelo, el test se marca `skip` con causa explícita; no se finge
  verde.
- Monitoreo de red local: cero conexiones salientes fuera de `localhost`.

**Oráculo.** `tests/integration/test_opensyn_e2e_local.py` (E2E real opt-in) +
`tests/integration/test_opensyn_sin_red.py` (sin salidas); reporte
`docs/reportes/R<ME>.md` con umbrales medidos.

**Depende.** r273.

**Política.** Nada de nube, telemetría, MCP ni multi-proveedor. El modelo y
los datos no salen del hardware del usuario (Manual 1 §5.7).

---

### r276_multiplataforma_release — P1

**Deficiencia.** Existen instaladores Linux/macOS y una matriz de CI, pero no
hay evidencia de ejecución reciente ni de firma/checksum por plataforma. La
VM Windows limpia sigue pendiente. El release no puede declararse “industrial”
sin eso.

**Requisito.** Manual 9 §2.4 (script Linux/macOS); Manual 9 §2.5 (Inno Setup);
Manual 9 §6.1 (instalador limpio); Manual 9 §6.2 (matriz CI); Manual 9 §6.3
(firma Ed25519).

**Texto literal.** “Instalador unificado: probado en sistemas limpios (sin
instalación previa) y funciona correctamente.”

**Implementación.**
- Ejecutar la matriz real en runners limpios (Windows, Linux, macOS; ARM si
  aplica).
- Instalar, ejecutar `synapse --version`, compilar y ejecutar un programa,
  arrancar OpenSyn local y verificar firma/checksum.
- Publicar logs y hashes por plataforma; fallar si falta un artefacto o una
  firma.
- Documentar limitaciones reales (p. ej. toolchain) sin prometer de más.

**Oráculo.** Job de CI con artefactos verificables; script
`scripts/verificar_release_limpio.py` (nuevo) que valida firma, checksum y
smoke; informe `docs/reportes/R<ME>.md`.

**Depende.** r270, r273.

**Política.** Ed25519 y offline-first; Authenticode no es requisito central.
No se publica un release sin SBOM y firma.

---

### r277_contracts_audit — P1

**Deficiencia.** `r253_contracts_audit` quedó parcial: `verificar_alineacion`
da 0 brechas, pero no existe una auditoría “0 funciones públicas sin
`requiere`/`garantiza`” con oráculo propio. Los contratos son una promesa
central del lenguaje y no se están midiendo.

**Requisito.** Manual 2 §5.1 (semántica formal); Manual 2 §12 (pruebas
obligatorias).

**Texto literal.** “Todas las expresiones deben ser booleanas.” / “100%
pass.”

**Implementación.**
- Escáner estático de funciones públicas en `nucleo/`, `std/`, `opensyn/` y
  `runtime/` que reporte las que no tienen ambos contratos.
- Excepciones explícitas para FFI y bindings, citando la sección del manual
  que las permite; nada de excepciones genéricas.
- Tests de comportamiento de contratos (precondición, postcondición,
  `_resultado_`).
- Corregir solo lo que el manual exige; no inventar contratos.

**Oráculo.** `auditoria/verificar_contratos.py` rc=0 con 0 funciones públicas
sin contrato; `pytest tests/integration/test_contracts.py -v` 100% pass;
excepciones listadas y justificadas.

**Depende.** —.

**Política.** No se añaden contratos a funciones FFI si el manual dice que
son externas sin precondición; se cita la excepción.

---

### r278_ide_debugger — P1

**Deficiencia.** `r240_vscode_ai` y `r241_debugger` están parciales. Hay
comandos declarados en `package.json`, pero faltan E2E de la extensión y del
debugger time-travel; los métodos LSP pueden seguir en skip.

**Requisito.** Manual 8 §2.3 (comandos de la paleta); Manual 8 §3.1–§3.5
(debugger); Manual 8 §1.4 (métodos LSP); Manual 8 §5.1 (comandos IA).

**Texto literal.** “Synapse/Syquex incluye un debugger nativo que soporta
**time-travel debugging** (grabación y reproducción de la ejecución) y
**breakpoints reversibles** (retroceder la ejecución).”

**Implementación.**
- Completar los métodos LSP que aún devuelven error o están en skip.
- E2E de la extensión: comando → LSP → respuesta JSON-RPC válida → código
  validado con `--check`.
- Debugger: avanzar, retroceder, snapshots, breakpoint y persistencia;
  integración VS Code.
- Sin GUI nueva fuera de VS Code (Manual 32 §1.3).

**Oráculo.** `tests/integration/test_ai_commands_opensyn.py` sin skips;
test de extensión (harness local) y test LSP de time-travel; 0 fallos.

**Depende.** r275.

**Política.** No se añade una GUI de escritorio; la extensión es la interfaz
permitida.

---

### r279_suite_rapida — P1

**Deficiencia.** La suite de integración completa tarda más de 2 h y tiene
fallos ambientales/prexistentes. Un gate que tarda horas se ejecuta tarde o
se salta; los fallos ambientales se confunden con regresiones.

**Requisito.** Manual 1 §7.2 (pruebas); Manual 9 §6.2 (suite completa en cada
target).

**Texto literal.** “La suite de tests completa en cada target.”

**Implementación.**
- Separar marked `slow`, `e2e`, `network` (estos últimos opt-in) y correr por
  shards en CI.
- Fixtures deterministas y caché de compilación; nada de red en unit.
- Medir y publicar tiempos por suite; objetivo acordado con el Arquitecto.
- No cambiar aserciones para acelerar; solo infraestructura de tests.

**Oráculo.** Run cronometrado con el mismo número de passed/skipped/failed
que la línea base; 0 skips nuevos; informe de tiempos.

**Depende.** r273, r274.

**Política.** Tests inmutables salvo infraestructura aprobada. No se oculta un
fallo con `-k` o `--ignore`.

---

### r280_codigo_encoding — P1

**Deficiencia.** Hay U+FFFD y controles C1 en comentarios/cadenas de
producción: `runtime/core/axon.h` (6), `runtime/core/concurrency.c` (8),
`runtime/core/debug.c` (10 C1), `std/texto.syn` (5),
`tests/validate_distillation.c` (2), `axon/axon_rt.c` (2 secuencias) y
`nucleo/generator.syn` / `nucleo/generador/monomorfizacion.syn` (1 cada uno).
No es solo cosmético: puede romper mensajes y citas.

**Requisito.** Manual 2 §1.2; Manual 1 §7.4.

**Texto literal.** “Todos los archivos fuente deben estar codificados en
**UTF-8 sin BOM**.”

**Implementación.**
- Corregir la fuente de verdad: `nucleo/generador/*` y luego regenerar
  `nucleo/generator.syn` (lección H-R180-2); no editar el unity a mano.
- Corregir comentarios y cadenas en runtime/std con UTF-8 real.
- Mantener el comportamiento; si un mensaje cambia, actualizar su test de
  comportamiento.
- Recompilar y ejecutar regresión dirigida.

**Oráculo.** Scan repo-wide con 0 U+FFFD, 0 C1 y 0 patrones de doble
codificación; `build.py` rc=0; tests dirigidos verdes.

**Depende.** r271.

**Política.** No se toca `nucleo/generator.syn` directamente; se regenera.
No se cambia semántica para “limpiar” texto.

---

## 4. MEs P2

### r281_d9_dead_code — P2

**Deficiencia.** Hay módulos >1200 líneas que requieren D-9 y duplicados
conocidos (H-R196-2: 12 funciones duplicadas en `std/texto.syn`). El código
muerto y la duplicación encarecen cada cambio y esconden regresiones.

**Requisito.** Manual 1 §7.4; Manual 2 §12.

**Implementación.**
- Medir módulos >1200 líneas y actualizar `docs/decisiones/MODULOS_D9.md`.
- Eliminar duplicados con paridad de comportamiento y tests.
- Retirar símbolos/archivos sin uso real; justificar lo que se conserva.
- No refactorizar por estética: cada corte debe tener oráculo.

**Oráculo.** `auditoria/verificar_modulos.py` (nuevo) rc=0; duplicados = 0;
tests de `std/texto.syn` verdes; D-9 al día.

**Depende.** r279.

**Política.** No se borra código con uso dinámico/FFI sin evidencia; se
pregunta si hay duda.

---

### r282_docs_informativos — P2

**Deficiencia.** `docs/book2-desarrollo/`, reportes y bitácoras repiten
reglas y pueden contradecir los manuales. No llevan una marca de vigencia
uniforme. Un lector puede tomar un reporte histórico como ley.

**Requisito.** Manual 1 §7.4; Manual 9 §6.1 (documentación versionada).

**Texto literal.** “Documentación: todos los manuales versionados y
empaquetados (incluyendo el Manual 31).”

**Implementación.**
- Aplicar la política a `docs/book2-desarrollo/` en un **barrido único**
  (D-MAN-3 opción A, 2026-11-19); el resto de documentos informativos queda
  congelado hasta este ME.
- Añadir cabecera “Documento informativo; la ley es `docs/manuales/`” a los
  documentos que no la tengan.
- Mapear cada documento a las secciones canónicas que resume.
- Corregir contradicciones y marcar lo histórico como histórico.
- No duplicar el texto del manual; enlazar a la sección.
- No tocar manuales en este ME.

**Oráculo.** `python auditoria/verificar_manuales.py --docs` rc=0; muestra
de 50 documentos con cabecera y sin contradicciones conocidas; enlaces
resolubles.

**Depende.** r271.

**Política.** Los reportes históricos no se reescriben salvo encoding/nota de
vigencia.

---

### r283_manual_versioning — P2

**Deficiencia.** No hay changelog de manuales, versión semántica ni política
de deprecación. Una sección puede cambiar de número y romper citas sin aviso;
el índice guarda un SHA pero no explica el cambio.

**Requisito.** Manual 1 §7.4; Manual 9 §6.1.

**Implementación.**
- `docs/manuales/CHANGELOG.md` con fecha, sección, cambio y aprobación.
- `docs/manuales/VERSION_MANUALES` (semver) y regla de compatibilidad de
  citas.
- Política de deprecación: una sección no se borra sin redirección y aviso.
- Índice schema v2 con alias y versión; el gate falla si un manual cambió sin
  changelog/versión.

**Oráculo.** `verificar_manuales.py --version` rc=0; cambio simulado sin
changelog rc=1; índice con versión y alias.

**Depende.** r271, r282.

**Política.** Cambiar una regla exige aprobación del Arquitecto; el changelog
no sustituye la aprobación.

---

### r284_observabilidad_local — P2 (opcional)

**Deficiencia.** No hay diagnóstico local estructurado para soporte; si se
añade sin política, el primer atajo será telemetría o un endpoint remoto, que
los manuales prohíben.

**Requisito.** Manual 1 §5.7 (cero telemetría); Manual 7 §7.3 (privacidad);
Manual 32 §1.3 (sin cloud/telemetría/gateway).

**Texto literal.** “Los binarios compilados y las herramientas del ecosistema
no realizan ninguna conexión en red oculta, recolección de datos de uso ni
analíticas.”

**Implementación.**
- Log local opt-in, por defecto desactivado, con retención y redacción de
  rutas/datos personales.
- Exportación manual a un archivo que el usuario elige; nada se envía solo.
- Cero endpoints remotos y cero identificadores estables de usuario.
- Documentar qué se registra y cómo se borra.

**Oráculo.** Test de no-salida de red; test de opt-in por defecto off; test de
redacción; revisión de que no hay URLs ni telemetría.

**Depende.** —.

**Política.** Cualquier propuesta de telemetría, crash reporting remoto o
registry central se rechaza por Manual 1 §5.7 y Manual 32 §1.3.

---

## 5. Trazabilidad con los hallazgos

| Hallazgo/deuda | ME |
|---|---|
| H-R252-1 bootstrap no cierra | r270 |
| H-R252-2 gate solo dentro del build | r274 |
| H-CONTROL-1/2/3 gates falsos verdes | r274 |
| Manual 31/32 fuera del índice; nombre no canónico | r271 |
| Corrupción de la auditoría y ejemplos de mojibake | r272 |
| Timeout del instalador con GGUF de 873 MB | r273 |
| Frentes E (E2E, benchmark, cobertura) | r275, r279 |
| Frentes F (limpia, multiplataforma, release) | r276 |
| r253 contratos | r277 |
| r240/r241 VS Code y debugger | r278 |
| U+FFFD/C1 en código | r280 |
| H-R196-2 duplicados; D-9 | r281 |
| Documentación informativa desfasada | r282, r283 |
| Riesgo de telemetría al instrumentar | r284 |

---

## 6. Secuencia recomendada

1. **Ola H1 (release):** r270, r271, r272, r273, r274.
2. **Ola H2 (producto):** r275, r276, r277, r278.
3. **Ola H3 (sostenibilidad):** r279, r280, r281, r282, r283.
4. **Ola H4 (opcional):** r284.

Cada ola cierra con `verificar_alineacion` 0 brechas, `contrastar` verde en
los planes MTS, `verificar_manuales --todo` rc=0 (cuando exista) y un reporte
con métricas antes/después. No se abre la ola siguiente con un P0 abierto.

---

## 7. Lo que NO se hace en este frente

- No se toca `nucleo/lsp_v3.syn` ni artefactos de otro agente sin coordinar.
- No se modifican tests existentes sin aprobación explícita.
- No se añaden MCP, cloud, multi-proveedor, telemetría ni gateway externo
  (Manual 32 §1.3).
- No se “arregla” un test para que pase; si el test y el manual discrepan, se
  detiene y se pregunta.
- No se declara un módulo “reparado” solo porque compila: exige test de
  comportamiento y retiro del baseline.
- No se renombra ni se mueve un manual de producción sin una decisión `D-MAN`
  vigente.

---

*Plan vivo. Se actualiza con cada ola y con cada decisión del Arquitecto. La
fuente de verdad sigue siendo `docs/manuales/`; este documento solo ordena cómo
cerrar sus brechas.*
