// cumple Manual 1 §5: backend LLVM
// cumple Manual 8 §4.2: target LLVM
// =============================================================================
// synapse_llvm.h — LLVM IR text emitter API (M12.1.1)
//
// Declaraciones para la API de generación de LLVM IR de texto (sin libLLVM).
// Implementación: synapse_llvm.c (C99 estándar, cero dependencias externas).
//
// Referencias: Manual 1 §5 (Generador) y §6 (Backend -> LLVM: IR, optimización, JIT)
// =============================================================================
#ifndef SYNAPSE_LLVM_H
#define SYNAPSE_LLVM_H

#include "synapse_rt_types.h"

// --- LLVMContext ---
typedef struct { int error_count; char error_msg[512]; } LLVMContext;
LLVMContext* LLVMContextCreate(void);
void LLVMContextDispose(LLVMContext* ctx);
int LLVMContextGetErrorCount(LLVMContext* ctx);
CadenaSegura LLVMContextGetError(LLVMContext* ctx);

// --- LLVMModule ---
typedef struct {
    LLVMContext* ctx;
    char nombre[128];
    char* ir_buffer;
    int ir_len;
    int ir_cap;
} LLVMModule;

LLVMModule* LLVMModuleCreateWithName(CadenaSegura nombre, LLVMContext* ctx);
void LLVMModuleDispose(LLVMModule* mod);
CadenaSegura LLVMModuleGetIR(LLVMModule* mod);
int LLVMModuleGetIRLength(LLVMModule* mod);
void LLVMModuleEmitHeader(LLVMModule* mod);
void LLVMModuleEmitRuntimeDecls(LLVMModule* mod);

// --- LLVMBuilder ---
typedef struct {
    LLVMModule* mod;
    int indent;
    char nombre_func_actual[128];
} LLVMBuilder;

LLVMBuilder* LLVMBuilderCreate(LLVMContext* ctx);
void LLVMBuilderDispose(LLVMBuilder* b);
void LLVMBuilderSetModule(LLVMBuilder* b, LLVMModule* mod);
void LLVMBuilderBeginFunction(LLVMBuilder* b, CadenaSegura nombre,
    int tipo_retorno, int param_count);
void LLVMBuilderEndFunction(LLVMBuilder* b);
void LLVMBuilderCreateEntryBlock(LLVMBuilder* b);
void LLVMBuilderCreateRetConst(LLVMBuilder* b, int val);
void LLVMBuilderEmitLabel(LLVMBuilder* b, CadenaSegura nombre);
void LLVMBuilderCreateBr(LLVMBuilder* b, CadenaSegura destino);
void LLVMBuilderCreateCondBr(LLVMBuilder* b, CadenaSegura cond,
    CadenaSegura etiqueta_true, CadenaSegura etiqueta_false);

// --- Constructores de alto nivel ---
CadenaSegura BuildMinimalProgram(LLVMContext* ctx, CadenaSegura nombre_modulo,
    int valor_retorno);
CadenaSegura BuildArithmeticProgram(LLVMContext* ctx, CadenaSegura nombre_modulo,
    int op, int lhs, int rhs);
CadenaSegura BuildIfElseProgram(LLVMContext* ctx, CadenaSegura nombre_modulo,
    int a, int b);
CadenaSegura BuildLoopProgram(LLVMContext* ctx, CadenaSegura nombre_modulo,
    int n);
CadenaSegura BuildCallProgram(LLVMContext* ctx, CadenaSegura nombre_modulo,
    int valor);

#endif /* SYNAPSE_LLVM_H */
