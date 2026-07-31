MANUAL 9: BOOTSTRAP, PRUEBAS Y ASEGURAMIENTO DE CALIDAD — COMPLETO (con adiciones 9.8 y 9.9)

Archivo: 09\_BOOTSTRAP\_Y\_CALIDAD.md

Versión: 5.1.1-industrial

Propósito: Especificar el proceso de bootstrap (self-hosting), las suites de pruebas, fuzzing, sanitizadores, el protocolo de seguridad, la validación estricta del determinismo, SBOM/SLSA y el proceso de certificación final.



9.1 Proceso de Bootstrap (3 Etapas + Verificación)

Etapa 0 (Semilla): Compilador Python (legacy) o binario bootstrap precompilado.



Etapa 1 (Stage1): python main.py nucleo/principal.syn -o synapse\_v1.exe



Etapa 2 (Stage2): ./synapse\_v1.exe nucleo/principal.syn -o synapse\_v2.exe



Etapa 3 (Stage3): ./synapse\_v2.exe nucleo/principal.syn -o synapse\_v3.exe



Verificación de equivalencia (CONTRATO OBLIGATORIO): diff synapse\_v2.exe synapse\_v3.exe → debe dar 0 bytes de diferencia. Esta validación se ejecuta automáticamente en la CI después de cada merge a main.



Interpretación: Si Stage2 y Stage3 son idénticos, el compilador es auto-hospedado, determinista y libre de dependencias externas.



Prerrequisito para pasar la verificación:



Todos los mapas/diccionarios internos (tablas de símbolos, dependencias, generación de código) deben iterar en orden lexicográfico.



La caché incremental debe ordenar las dependencias alfabéticamente antes de calcular el hash.



El backend C/LLVM debe emitir funciones y variables globales en orden alfabético.



9.2 Componentes del Runtime (Tamaños)

Archivo	Tamaño (aprox)	Función

runtime/core/memory.c	35 KB .o	Pool allocator con TLC, watchdog.

runtime/core/concurrency.c	40 KB .o	Canales, mutexes, hilos.

runtime/core/io.c	20 KB .o	E/S de archivos y sockets base.

runtime/net/http.c	30 KB .o	Cliente/servidor HTTP.

runtime/quantum/matrix.c	25 KB .o	Simulación cuántica.

runtime/ml/gguf.c	50 KB .o	Carga de modelos locales.

runtime/federated/aggregator.c	30 KB .o	Algoritmos FedAvg.

axon/axon\_rt.c	166 KB .o	HTTP, TAR, Ed25519, SemVer.

tweetnacl.c	19 KB .o	Criptografía.

Total	< 415 KB	Runtime completo modular.

9.3 Suites de Pruebas (Estructura)

Directorio	Tipo	Número	Alcance

tests/unit/	Unitarias (Python)	184+	Lexer, Parser, Semántico, Generador C, Caché.

tests/integration/	Integración (Python)	17 archivos	End-to-end, LSP, Axon, Cluster.

tests/	Nativas (C)	38 archivos	Validación de módulos core + LLVM, ATP, Federated, Quantum.

tests/fuzz/	Fuzzing	7 estrategias	Entradas corruptas/maliciosas.

tests/stress/	Estrés	10,000 hilos	Concurrencia, deadlocks, fugas.

Nuevos grupos de validación nativa (C):



Grupo	Archivos	Validación

LLVM Backend	validate\_llvm\_backend.c, validate\_llvm\_control\_flow.c, validate\_llvm\_jit.c	Generación de IR, JIT, CFG.

ATP Engine	validate\_atp\_engine.c, validate\_formal\_proof.c, validate\_symbolic\_exec.c	Verificación de contratos, terminación, ejecución simbólica.

Aprendizaje Federado	validate\_federated.c, validate\_dist\_orchestrator.c, validate\_distillation.c, validate\_fine\_tuning.c	FedAvg, orquestación, destilación, fine‑tuning.

Computación Cuántica	validate\_quantum\_memory.c, validate\_quantum\_err\_corr.c, validate\_quantum\_runtime.c, validate\_surface\_code.c	T1/T2, QEC, surface codes, puertas.

9.4 Fuzzing Destructivo (7 Estrategias)

Estrategia	Peso	Descripción

Sintaxis válida	10%	Programas Synapse válidos mínimos.

Semi-válido	20%	Errores comunes (faltan :, indentación rota).

Aleatorio	25%	Caracteres imprimibles + control.

Cadenas malformadas	20%	Comillas sin cerrar, keywords sueltos.

Indentación rota	10%	3/5/7 espacios (no múltiplos de 4).

Unicode corrupto	10%	Zero-width, BOM, combining accents.

Binario simulado	5%	Bytes crudos no UTF-8.

Ejecución: python tests/fuzz/fuzz\_engine.py --iterations 500 → 0 crashes.



9.5 Sanitizadores (Obligatorios en CI)

Sanitizador	Flag GCC	Propósito	Criterio de aceptación

AddressSanitizer	-fsanitize=address	Detectar fugas y accesos inválidos.	0 fugas, 0 errores.

UndefinedBehaviorSanitizer	-fsanitize=undefined	Detectar overflow, shift inválido.	0 errores.

ThreadSanitizer	-fsanitize=thread	Detectar data races.	0 data races.

Ejecución integrada:



bash

synapse test --auditar-memoria   # ASan + LSan

synapse test --auditar-hilos     # TSan

9.6 Protocolo de Seguridad (Incidentes)

Canal de reporte: seguridad@synapse-lang.org (PGP cifrado).



Prohibido: Reportar vulnerabilidades en issues públicos.



Etapa	Plazo	Acción

Diagnóstico	24h	Confirmar exploit.

Parche	48h	Desarrollar parche en rama privada.

Publicación	72h	Lanzamiento de parche de emergencia.

Post-mortem	1 semana	Informe detallado + mejora del proceso de QA.

9.7 Checklist de "Definition of Done" (v5.1.1-industrial)

□ Compilación: python main.py nucleo/principal.syn produce 0 errores GCC.

□ Bootstrap: diff synapse\_v2.exe synapse\_v3.exe = 0 bytes (verificado en CI).

□ Determinismo del código intermedio: synapse build --debug test.syn ejecutado dos veces produce el mismo hash SHA-256 en el archivo .c generado.

□ Tests: pytest tests/ -v → 184/184 PASS.

□ Fuzzing: fuzz\_engine.py --iterations 500 → 0 crashes.

□ Memoria: synapse test --auditar-memoria → 0 leaks.

□ Concurrencia: test\_canales\_stress → 0 deadlocks, 0 data races.

□ LSP: pytest tests/integration/test\_lsp\_native.py → 5/5 PASS.

□ Axon: python tests/test\_axon\_e2e.py → 19/19 PASS.

□ Validación Avanzada:

□ ATP: validate\_atp\_engine --test prove\_tautology → PASS.

□ ATP Timeout: validate\_atp\_engine --test timeout --timeout 1 → Captura ERR\_ATP\_TIMEOUT.

□ LLVM JIT: validate\_llvm\_jit --test run\_fibonacci → PASS.

□ Federated Learning: validate\_federated --rounds 3 --clients 2 → 0 leaks, 0 crashes.

□ Quantum: validate\_quantum\_runtime --test surface\_code → PASS.

□ Documentación: 9 manuales actualizados y versionados.

9.8 SBOM y SLSA Level 3 (Cadena de Suministro) — Adición v5.1.1-industrial

La versión industrial de Synapse genera automáticamente un SBOM (Software Bill of Materials) en formato SPDX 2.3 y una attestación SLSA Level 3 para cada artefacto liberado.



9.8.1 Generación de SBOM

Herramienta: nucleo/sbom.py (invocada en CI/CD).



El SBOM incluye:



Todos los archivos fuente .syn, .c, .h y .py del compilador y runtime.



Dependencias externas: libpthread, libm, libc, libLLVM, libseccomp.



Hashes SHA-256 de cada archivo.



Licencias (SPDX identifiers).



Salida: synapse.spdx.json (firmado con Ed25519).



9.8.2 Attestación SLSA Level 3

El pipeline de CI/CD genera una attestación que certifica:



Origen del código (repo + commit).



Comandos de build exactos.



Hashes de los artefactos de entrada y salida.



La attestación se firma con la misma clave Ed25519 del proyecto.



9.8.3 Validación

bash

\# Test de generación de SBOM

python nucleo/sbom.py --output synapse.spdx.json

\# Validar contra esquema SPDX

python -c "import json; assert json.load(open('synapse.spdx.json'))\['spdxVersion'] == 'SPDX-2.3'"

9.9 Certificación de Producción y Hardening Final (v5.1.1-industrial) — Adición v5.1.1-industrial

Esta fase se ejecuta al final del ciclo de release y garantiza que todos los artefactos están listos para despliegue en entornos de producción.



9.9.1 Empaquetado Multi‑target

Generación de instaladores para Windows x64, Linux x64, macOS ARM y WASM.



Cada instalador incluye:



Binario synapse.exe o synapse.



Runtime modular (core, net, quantum, ml, federated).



Librería estándar (std/\*.syn).



Extensión VS Code empaquetada (.vsix).



9.9.2 Validación Cruzada en CI/CD

Ejecución de toda la suite de tests (184 Python + 34 C nativos + fuzzing) en los 4 targets.



Verificación del bootstrap en cada target (diff 0 bytes entre Stage 2 y Stage 3).



Comprobación de que los sanitizadores (ASan, UBSan, TSan) no reportan errores.



9.9.3 Sellado Criptográfico Definitivo

Cada artefacto se firma con Ed25519 (clave privada del proyecto).



Se genera una attestación SLSA Level 3 y el SBOM SPDX 2.3.



Todos los archivos de firma (.sig) y los checksums (.sha256) se suben al repositorio de releases junto con los binarios.



9.9.4 Verificación Final (Checklist)

□ Todos los artefactos compilados sin errores en los 4 targets.

□ Bootstrap exitoso en cada target.

□ 184/184 tests Python pasan.

□ 34/34 tests C nativos pasan.

□ Fuzzing: 500+ iteraciones, 0 crashes.

□ ASan/UBSan/TSan: 0 errores.

□ SBOM y SLSA attestations generados y firmados.

□ Documentación (9 manuales) versionada y empaquetada.

FIN DE LOS TEXTOS COMPLETOS ACTUALIZADOS (MANUAL 3 Y 9)

