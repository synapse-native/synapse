# OpenSyn: El Orquestador Autónomo

**OpenSyn** es el orquestador autónomo que cierra el ciclo de vida del desarrollo de software: un LLM genera código Synapse, el compilador nativo lo audita, y si hay errores, el bucle retroalimenta al modelo para que se corrija a sí mismo — todo sin intervención humana.

```
Prompt ──► LLM ──► Código ──► Compilador ──► ✅ Binario
  ▲                      │         │
  └── retroalimentación ◄┘         └── ❌ Error → reformular prompt
```

## Filosofía

OpenSyn descansa sobre tres principios:

| Principio | Implicación |
|-----------|-------------|
| **Auto-corrección** | El sistema no falla en el primer error; reformula el prompt con el diagnóstico del compilador y lo reintenta hasta `MAX_INTENTOS` (3) veces. |
| **Sin intermediarios** | No se necesita un humano leyendo errores de compilación. El LLM lee el error Synapse directamente y lo resuelve. |
| **Soberanía del binario** | El producto final es un `.exe` nativo de C, sin runtime, sin VM, sin dependencias. |

## Arquitectura

```
┌──────────────────────────────────────────────────────────┐
│                   opensyn/principal.syn                   │
│  (punto de entrada: main → principal)                     │
└──────────────────┬───────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────┐
│               std.oraculo: generar_codigo()               │
│  (bucle principal con telemetría)                         │
└──┬───────────────┬──────────────────┬────────────────────┘
   │               │                  │
   ▼               ▼                  ▼
┌────────┐   ┌───────────┐   ┌──────────────┐
│ modelo │   │ extraer   │   │ compilar     │
│ .syn   │   │ bloque    │   │ helper       │
│ infer. │   │ código    │   │ .py          │
└────────┘   └───────────┘   └──────────────┘
```

## Flujo detallado

1. **Carga del modelo**: `_syn_modelo_cargar("modelo_synapse.gguf")` abre y mapea en memoria un transformer completo.
2. **Construcción del prompt**: Se inyecta `SYSTEM_PROMPT` (reglas del lenguaje Synapse) + instrucción del usuario.
3. **Generación de texto**: El transformer produce tokens autoregresivamente con muestreo top-k / top-p.
4. **Extracción de código**: `_syn_extraer_bloque_codigo()` extrae el contenido entre marcadores `` ```synapse ``` ``.
5. **Compilación interna**: `_syn_compilar_codigo()` escribe un archivo temporal, invoca `_compilar_helper.py` vía `_popen`, y parsea el JSON de resultado.
6. **Retroalimentación**: Si falla, se concatena el error de línea al prompt y se reintenta (hasta 3 veces).

## Binario generado

```c
// principal.c — generado por Synapse
int main(int argc, char** argv) {
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    principal();
    synapse_esperar_hilos();
    return 0;
}
```
