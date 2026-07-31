MANUAL 9: BOOTSTRAP, PRUEBAS Y ASEGURAMIENTO DE CALIDAD
Archivo: 09_BOOTSTRAP_Y_CALIDAD.md
Versión: 5.1.1-industrial
Propósito: Especificar el proceso de bootstrap (self-hosting), las suites de pruebas, fuzzing, sanitizadores y el protocolo de seguridad.

9.1 Proceso de Bootstrap (3 Etapas + Verificación)
Etapa 0 (Semilla): Compilador Python (legacy) o binario bootstrap precompilado.

Etapa 1 (Stage1):

bash
python main.py nucleo/principal.syn -o synapse_v1.exe
Etapa 2 (Stage2):

bash
./synapse_v1.exe nucleo/principal.syn -o synapse_v2.exe
Etapa 3 (Stage3):

bash
./synapse_v2.exe nucleo/principal.syn -o synapse_v3.exe
Verificación de equivalencia (REQUISITO DE CERTIFICACIÓN):

bash
diff synapse_v2.exe synapse_v3.exe   # Debe dar 0 bytes de diferencia.
Interpretación: Si Stage2 y Stage3 son idénticos, el compilador es auto-hospedado, determinista y libre de dependencias externas.

9.2 Componentes del Runtime (Tamaños)
Archivo	Tamaño (aprox)	Función
synapse_rt.c	107 KB .o	Canales, SIMD, SHA-256, JSON, TOML, Hilos, Sockets, GGUF, AI.
axon_rt.c	166 KB .o	HTTP, TAR, Ed25519, SemVer, lockfile, TOML parser.
tweetnacl.c	19 KB .o	Ed25519 firmas/verificación.
Total	< 300 KB	Runtime completo.
9.3 Suites de Pruebas (Estructura)
Directorio	Tipo	Número	Alcance
tests/unit/	Unitarias (Python)	184+	Lexer, Parser, Semántico, Generador C, Caché.
tests/integration/	Integración (Python)	17 archivos	End-to-end, LSP, Axon, Cluster.
tests/	Nativas (C)	34 archivos	Validación de módulos core (validate_*.c).
tests/fuzz/	Fuzzing	7 estrategias	Entradas corruptas/maliciosas.
tests/stress/	Estrés	10,000 hilos	Concurrencia, deadlocks, fugas.
Ejecución completa:

bash
python -m pytest tests/ -v
# Resultado: 184 passed, 0 failed

python scripts/run_native_tests.py
# Resultado: 34/34 PASS
9.4 Fuzzing Destructivo (7 Estrategias)
Estrategia	Peso	Descripción
Sintaxis válida	10%	Programas Synapse válidos mínimos.
Semi-válido	20%	Errores comunes (faltan :, indentación rota).
Aleatorio	25%	Caracteres imprimibles + control.
Cadenas malformadas	20%	Comillas sin cerrar, keywords sueltos.
Indentación rota	10%	3/5/7 espacios (no múltiplos de 4).
Unicode corrupto	10%	Zero-width, BOM, combining accents.
Binario simulado	5%	Bytes crudos no UTF-8.
Ejecución:

bash
python tests/fuzz/fuzz_engine.py --iterations 500
# Resultado: 0 crashes, 0 errores no controlados.
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

Plazos de respuesta:

Etapa	Plazo	Acción
Diagnóstico	24h	Confirmar exploit.
Parche	48h	Desarrollar parche en rama privada.
Publicación	72h	Lanzamiento de parche de emergencia.
Post-mortem	1 semana	Informe detallado + mejora del proceso de QA.
9.7 Checklist de "Definition of Done" (v5.0)
□ Compilación: python main.py nucleo/principal.syn produce 0 errores GCC.
□ Bootstrap: diff synapse_v2.exe synapse_v3.exe = 0 bytes.
□ Tests: pytest tests/ → 184/184 PASS.
□ Fuzzing: fuzz_engine.py --iterations 500 → 0 crashes.
□ Memoria: synapse test --auditar-memoria → 0 leaks.
□ Concurrencia: test_canales_stress → 0 deadlocks, 0 data races.
□ LSP: pytest tests/integration/test_lsp_native.py → 5/5 PASS.
□ Axon: python tests/test_axon_e2e.py → 19/19 PASS.
□ Documentación: 9 manuales actualizados y versionados.
FIN DE LOS 9 MANUALES TÉCNICOS DE INGENIERÍA — SYNAPSE v5.0

