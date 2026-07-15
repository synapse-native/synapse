# OpenSyn v1.1.0 — Orquestador Autónomo de Código

> **Prompt → Inferencia Nativa → AST → Auto-Corrección → Binario.**
> Sin Python en producción. Sin VM. Sin dependencias.

OpenSyn es el primer orquestador autónomo que cierra el ciclo: un LLM escribe código Synapse, el compilador lo audita nativamente en C, y si hay errores, el bucle retroalimenta al modelo para que se corrija a sí mismo. El producto final es siempre un binario nativo.

---

### ⚡ Interruptor de Soberanía (v1.1.0)

**La IA es 100% Opt-In.** En la primera ejecución, OpenSyn muestra un menú para elegir entre:

| Modo | Descripción |
|------|-------------|
| **Lenguaje Puro** | Compilador Synapse standalone. Sin IA, sin GPU, sin descargas. Ideal para C/Rust developers. |
| **Oráculo (IA Local)** | Orquestador autónomo con LLM local. Genera y corrige código por ti. Requiere modelo GGUF. |

La preferencia se guarda en `.synapse_config`. Para cambiar, elimina el archivo y re-ejecuta.

> **Synapse no consume recursos en segundo plano.** Sin IA a menos que tú lo decidas.

---

## Diagrama de flujo

```
┌─────────────────────────────────────────────────────────────────┐
│                         opensyn/principal.syn                     │
│  "Escribe un programa que abra reporte.txt y escriba 'SD'"       │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    std.oraculo: generar_codigo()                  │
│  ┌─────────────┐   ┌──────────────┐   ┌────────────────────┐   │
│  │ LLM (GGUF)  │   │ Extraer      │   │ Compilador interno │   │
│  │ genera texto│──►│ bloque ```   │──►│ (Lex→Parse→Sem→C)  │   │
│  │ con BPE +   │   │ synapse ```  │   │ vía _compilar_     │   │
│  │ transformer │   │              │   │ helper.py          │   │
│  └─────────────┘   └──────────────┘   └────────┬───────────┘   │
│                                                  │              │
│                    ┌─────────────────────────────┘              │
│                    │ ¿Error?                                     │
│                    ▼ Sí                                          │
│              ┌──────────┐                                       │
│              │ Re-      │────────────────────────────────────┐  │
│              │ intentar │  retroalimentación con msg error   │  │
│              │ (max 3)  │◄──────────────────────────────────┘  │
│              └──────────┘                                       │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  ✅ Binario Nativo   │
                    │  generado.syn (.exe) │
                    └─────────────────────┘
```

---

## Cómo compilar

### Requisitos

- **GCC** (MinGW-w64 en Windows, gcc en Linux/macOS)
- **Python 3.10+** (solo para el helper de compilación interna)
- **Un modelo GGUF** (ej. Qwen2.5-Coder-0.5B) como `modelo_synapse.gguf`

### Compilar el runtime

```bash
gcc -c synapse_rt.c -o synapse_rt.o -lpthread -lm -lws2_32
```

### Compilar un programa Synapse

```bash
python main.py programa.syn
# Genera: programa.c + programa.exe
```

### Compilar el orquestador OpenSyn

```bash
gcc -o opensyn/principal.exe opensyn/principal.c synapse_rt.c \
    -std=c99 -Wall -Wextra -lws2_32
```

### Ejecutar el orquestador

```bash
cd opensyn
# Coloca modelo_synapse.gguf aquí
./principal.exe
```

Salida esperada:

```
=== OpenSyn: Orquestador Autonomo ===
[OK] Modelo cargado exitosamente.
[Oráculo] Generando código... (Intento 1/3)
[Compilador] Error detectado: Re-inyectando contexto...
[Oráculo] Generando código... (Intento 2/3)
[Compilador] Éxito. Binario generado.
[OK] Código generado y compilado exitosamente.
[OK] Código fuente guardado en 'generado.syn'
```

---

## Arquitectura del repositorio

```
opensyn/
├── principal.syn          # Orquestador (código fuente Synapse)
├── principal.c            # Generado por el compilador
├── principal.exe          # Binario final

librerias/
├── std/
│   ├── oraculo.syn        # Bucle del Oráculo
│   ├── modelo.syn         # Inferencia del LLM
│   ├── io.syn             # E/S de consola
│   ├── json.syn           # Parseo JSON
│   ├── sistema.syn        # Comandos del sistema
│   ├── net.syn            # Sockets TCP
│   └── ...                # 15 módulos estándar
├── embedded_libs.h        # Librerías incrustadas para self-hosting

synapse_rt.c               # Runtime C (pool, tensores, GGUF, BPE, oráculo)
_compilar_helper.py         # Helper de compilación interna (vía JSON)
main.py                     # Compilador Synapse (Lexer + Parser + GeneradorC)
generator.py                # Traductor Synapse → C
```

---

## Librería Estándar (15 módulos)

| Módulo | Funcionalidad |
|--------|---------------|
| `std.io` | `escribir`, `escribir_linea`, `leer_linea`, `abrir`, `leer`, `cerrar` |
| `std.mem` | `reserva`, `libera` |
| `std.math` | `crear_tensor`, `suma_tensor`, `producto_punto`, `relu` |
| `std.tensor` | `rmsnorm`, `silu`, `rope`, `softmax_escalado`, `multiplicar_matrices` |
| `std.modelo` | `cargar_modelo`, `evaluar`, `generar_token`, `decodificar_token`, `codificar` |
| `std.oraculo` | `generar_codigo`, `compilar_codigo`, `extraer_bloque_codigo`, `generar_texto` |
| `std.ai` | `cargar_gguf`, `obtener_tensor`, `obtener_metadato`, `argmax` |
| `std.json` | `desde_texto`, `obtener_elemento`, `obtener_campo` |
| `std.toml` | `desde_texto`, `obtener_campo` |
| `std.net` | `iniciar_red`, `crear_socket`, `conectar`, `enviar_datos`, `recibir_datos` |
| `std.http` | `iniciar_servidor`, `leer_peticion`, `responder` |
| `std.cripto` | `sha256_texto` |
| `std.tiempo` | `ahora_ms`, `dormir_ms` |
| `std.sistema` | `ejecutar_comando`, `escribir_archivo`, `leer_archivo` |
| `std.err` | ADT `Resultado<T,E>` y `Opcion<T>` |

---

## Licencia

Este proyecto se distribuye bajo una licencia de código abierto. Consulte el archivo de licencia para más detalles.

---

**OpenSyn v1.0.0** — *Soberanía Digital. Sin intermediarios.*
