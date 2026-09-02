// cumple Manual 1 5: backend WASM
// cumple Manual 8 4.2: target WASM
// =============================================================================
// synapse_wasm.h — WebAssembly WAT text emitter API (M12.1.2)
//
// Declaraciones para la API de generación de WAT de texto (sin emcc/wasm-ld).
// Implementación: synapse_wasm.c (C99 estándar, cero dependencias externas).
//
// Referencias: Manual 1 §5 ("Traduce AST a C, LLVM IR o WAT"), §6 (Backend WASM)
// =============================================================================
#ifndef SYNAPSE_WASM_H
#define SYNAPSE_WASM_H

#include "synapse_rt_types.h"

// --- WasmModule ---
typedef struct {
    char nombre[128];
    char* wat_buffer;
    int wat_len;
    int wat_cap;
} WasmModule;

WasmModule* WasmModuleCreate(CadenaSegura nombre);
void WasmModuleDispose(WasmModule* mod);
CadenaSegura WasmModuleGetWAT(WasmModule* mod);
int WasmModuleGetWATLength(WasmModule* mod);
void WasmModuleEmitHeader(WasmModule* mod);
void WasmModuleEmitRuntimeDecls(WasmModule* mod);

// --- WasmBuilder ---
typedef struct {
    WasmModule* mod;
    int indent;
} WasmBuilder;

WasmBuilder* WasmBuilderCreate(WasmModule* mod);
void WasmBuilderDispose(WasmBuilder* b);
void WasmBuilderBeginFunction(WasmBuilder* b, CadenaSegura nombre,
    int num_params, int num_results);
void WasmBuilderEndFunction(WasmBuilder* b);

// --- Instrucciones WASM ---
void WasmEmitI32Const(WasmBuilder* b, int val);
void WasmEmitI32Add(WasmBuilder* b);
void WasmEmitI32Sub(WasmBuilder* b);
void WasmEmitI32Mul(WasmBuilder* b);
void WasmEmitI32DivS(WasmBuilder* b);
void WasmEmitReturn(WasmBuilder* b);
void WasmEmitCall(WasmBuilder* b, CadenaSegura nombre);
void WasmEmitLocalGet(WasmBuilder* b, CadenaSegura nombre);
void WasmEmitLocalSet(WasmBuilder* b, CadenaSegura nombre);
void WasmEmitLocalDecl(WasmBuilder* b, CadenaSegura nombre);
void WasmEmitIf(WasmBuilder* b);
void WasmEmitElse(WasmBuilder* b);
void WasmEmitEnd(WasmBuilder* b);
void WasmEmitBrIf(WasmBuilder* b, CadenaSegura etiqueta);
void WasmEmitBr(WasmBuilder* b, CadenaSegura etiqueta);
void WasmEmitDrop(WasmBuilder* b);

// --- Comparaciones ---
void WasmEmitI32Eq(WasmBuilder* b);
void WasmEmitI32Ne(WasmBuilder* b);
void WasmEmitI32LtS(WasmBuilder* b);
void WasmEmitI32GtS(WasmBuilder* b);

// --- Constructores de alto nivel ---
CadenaSegura WasmBuildMinimalProgram(CadenaSegura nombre_modulo,
    int valor_retorno);
CadenaSegura WasmBuildArithmeticProgram(CadenaSegura nombre_modulo,
    int op, int lhs, int rhs);
CadenaSegura WasmBuildIfElseProgram(CadenaSegura nombre_modulo,
    int a, int b);
CadenaSegura WasmBuildCallProgram(CadenaSegura nombre_modulo,
    int a, int b);

#endif /* SYNAPSE_WASM_H */
