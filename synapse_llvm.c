/*
 * synapse_llvm.c — Synapse LLVM IR Backend (M12.1.1)
 *
 * Generates LLVM IR assembly (.ll) from Synapse AST nodes.
 * Portable: no LLVM library dependency — emits human-readable IR text.
 *
 * Architecture:
 *   LLVMContext  → holds module state and error tracking
 *   LLVMModule   → contains global definitions and functions
 *   LLVMBuilder  → appends IR instructions to current function
 *
 * When LLVM tools (llc, opt) are available, the emitted .ll files
 * can be compiled to native code via:
 *   llc synapse_output.ll -o synapse_output.s
 *   gcc synapse_output.s -o synapse_output
 *
 * Compilar como objeto:
 *   gcc -O2 -std=c99 -c synapse_llvm.c -o synapse_llvm.o
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <stdint.h>
#include <ctype.h>

// ============================================================
// LLVM IR Text Emitter — Forward declarations
// ============================================================

// Opaque handle types
typedef struct LLVMContext LLVMContext;
typedef struct LLVMModule LLVMModule;
typedef struct LLVMBuilder LLVMBuilder;

// IR value types
typedef enum {
    IR_I32,      // i32
    IR_I1,       // i1 (boolean)
    IR_VOID,     // void
    IR_PTR,      // pointer
} IRType;

// ============================================================
// LLVMContext
// ============================================================
struct LLVMContext {
    int error_count;
    char error_msg[1024];
    int next_temp_id;       // for generating unique SSA names
};

LLVMContext* LLVMContextCreate(void) {
    LLVMContext* ctx = (LLVMContext*)calloc(1, sizeof(LLVMContext));
    if (!ctx) return NULL;
    ctx->next_temp_id = 0;
    return ctx;
}

void LLVMContextDispose(LLVMContext* ctx) {
    if (ctx) free(ctx);
}

void LLVMContextSetError(LLVMContext* ctx, const char* fmt, ...) {
    if (!ctx) return;
    va_list args;
    va_start(args, fmt);
    ctx->error_count++;
    vsnprintf(ctx->error_msg, sizeof(ctx->error_msg), fmt, args);
    va_end(args);
}

int LLVMContextGetErrorCount(LLVMContext* ctx) {
    return ctx ? ctx->error_count : -1;
}

const char* LLVMContextGetError(LLVMContext* ctx) {
    return ctx ? ctx->error_msg : "";
}

// Generate a unique temporary name for SSA values
static void _gen_temp_name(LLVMContext* ctx, char* buf, size_t buf_size) {
    snprintf(buf, buf_size, "%%t%d", ctx->next_temp_id++);
}

// ============================================================
// LLVMModule
// ============================================================
struct LLVMModule {
    char name[256];
    char* ir_buffer;           // accumulated IR text
    size_t ir_capacity;
    size_t ir_length;
    LLVMContext* context;
    int has_main_decl;         // track if main function declared
};

LLVMModule* LLVMModuleCreateWithName(const char* name, LLVMContext* ctx) {
    if (!ctx || !name) return NULL;
    LLVMModule* mod = (LLVMModule*)calloc(1, sizeof(LLVMModule));
    if (!mod) return NULL;
    snprintf(mod->name, sizeof(mod->name), "%s", name);
    mod->context = ctx;
    mod->ir_capacity = 4096;
    mod->ir_buffer = (char*)malloc(mod->ir_capacity);
    if (!mod->ir_buffer) { free(mod); return NULL; }
    mod->ir_length = 0;
    mod->has_main_decl = 0;
    return mod;
}

static void _mod_append(LLVMModule* mod, const char* fmt, ...) {
    if (!mod || !mod->ir_buffer) return;
    va_list args;
    va_start(args, fmt);
    int needed = vsnprintf(NULL, 0, fmt, args);
    va_end(args);
    if (needed < 0) return;

    size_t new_len = mod->ir_length + (size_t)needed + 1;
    if (new_len > mod->ir_capacity) {
        mod->ir_capacity = new_len * 2;
        char* new_buf = (char*)realloc(mod->ir_buffer, mod->ir_capacity);
        if (!new_buf) return;
        mod->ir_buffer = new_buf;
    }

    va_start(args, fmt);
    vsnprintf(mod->ir_buffer + mod->ir_length,
              mod->ir_capacity - mod->ir_length, fmt, args);
    va_end(args);
    mod->ir_length += (size_t)needed;
}

void LLVMModuleDispose(LLVMModule* mod) {
    if (mod) {
        free(mod->ir_buffer);
        free(mod);
    }
}

const char* LLVMModuleGetIR(LLVMModule* mod) {
    return mod ? mod->ir_buffer : NULL;
}

size_t LLVMModuleGetIRLength(LLVMModule* mod) {
    return mod ? mod->ir_length : 0;
}

// Write the module header (target triple, data layout)
void LLVMModuleEmitHeader(LLVMModule* mod) {
    if (!mod) return;
    _mod_append(mod, "; ModuleID = '%s'\n", mod->name);
    _mod_append(mod, "target triple = \"x86_64-pc-windows-msvc\"\n");
    _mod_append(mod, "target datalayout = \"e-m:w-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128\"\n");
    _mod_append(mod, "\n");
}

// Declare external runtime functions
void LLVMModuleEmitRuntimeDecls(LLVMModule* mod) {
    if (!mod) return;
    _mod_append(mod, "; Runtime declarations\n");
    _mod_append(mod, "declare i32 @putchar(i32)\n");
    _mod_append(mod, "declare i32 @printf(i8*, ...)\n");
    _mod_append(mod, "\n");
}

// ============================================================
// LLVMBuilder — emits IR instructions into the current function
// ============================================================
struct LLVMBuilder {
    LLVMContext* context;
    LLVMModule* current_module;
    char current_function[256];  // name of function being built
    int has_entry_block;         // entry block created
    int indent_level;            // for pretty printing
};

LLVMBuilder* LLVMBuilderCreate(LLVMContext* ctx) {
    if (!ctx) return NULL;
    LLVMBuilder* b = (LLVMBuilder*)calloc(1, sizeof(LLVMBuilder));
    if (!b) return NULL;
    b->context = ctx;
    b->current_module = NULL;
    b->current_function[0] = '\0';
    b->has_entry_block = 0;
    b->indent_level = 0;
    return b;
}

void LLVMBuilderDispose(LLVMBuilder* b) {
    if (b) free(b);
}

void LLVMBuilderSetModule(LLVMBuilder* b, LLVMModule* mod) {
    if (b) b->current_module = mod;
}

// Append a line of IR with proper indentation
static void _b_emit(LLVMBuilder* b, const char* fmt, ...) {
    if (!b || !b->current_module) return;
    va_list args;
    va_start(args, fmt);
    int needed = vsnprintf(NULL, 0, fmt, args);
    va_end(args);
    if (needed < 0) return;

    // Build the formatted string
    char* line = (char*)malloc((size_t)needed + 1);
    if (!line) return;
    va_start(args, fmt);
    vsnprintf(line, (size_t)needed + 1, fmt, args);
    va_end(args);

    // Indent
    for (int i = 0; i < b->indent_level; i++) {
        _mod_append(b->current_module, "  ");
    }
    _mod_append(b->current_module, "%s", line);
    free(line);
}

// Begin a new function definition
void LLVMBuilderBeginFunction(LLVMBuilder* b, const char* name,
                              IRType return_type, int param_count, ...) {
    if (!b || !b->current_module || !name) return;
    snprintf(b->current_function, sizeof(b->current_function), "%s", name);
    b->has_entry_block = 0;
    b->indent_level = 0;

    const char* ret_str = "i32";
    if (return_type == IR_VOID) ret_str = "void";
    else if (return_type == IR_I1) ret_str = "i1";

    _mod_append(b->current_module, "define %s @%s(", ret_str, name);

    va_list args;
    va_start(args, param_count);
    for (int i = 0; i < param_count; i++) {
        IRType pt = (IRType)va_arg(args, int);
        if (i > 0) _mod_append(b->current_module, ", ");
        if (pt == IR_I32) _mod_append(b->current_module, "i32 %%p%d", i);
        else if (pt == IR_I1) _mod_append(b->current_module, "i1 %%p%d", i);
        else _mod_append(b->current_module, "i32 %%p%d", i);
    }
    va_end(args);

    _mod_append(b->current_module, ") {\n");
    b->indent_level = 1;
}

// Create the entry basic block
void LLVMBuilderCreateEntryBlock(LLVMBuilder* b) {
    if (!b || b->has_entry_block) return;
    _b_emit(b, "entry:\n");
    b->indent_level = 2;
    b->has_entry_block = 1;
}

// Emit 'ret' instruction
void LLVMBuilderCreateRet(LLVMBuilder* b, const char* value) {
    if (!b) return;
    if (value) {
        _b_emit(b, "ret i32 %s\n", value);
    } else {
        _b_emit(b, "ret void\n");
    }
}

// Emit 'ret i32 <const>'
void LLVMBuilderCreateRetConst(LLVMBuilder* b, int val) {
    if (!b) return;
    _b_emit(b, "ret i32 %d\n", val);
}

// Emit an integer constant string into a caller-provided buffer
void LLVMBuilderConstInt(int val, char* out, size_t out_size) {
    if (out && out_size > 0) {
        snprintf(out, out_size, "%d", val);
    }
}

// Emit a boolean constant: "true" (i1 1) or "false" (i1 0)
void LLVMBuilderConstBool(int val, char* out, size_t out_size) {
    if (out && out_size > 0) {
        snprintf(out, out_size, "%s", val ? "true" : "false");
    }
}

// Emit: <result> = add i32 <a>, <b>
// Writes the SSA result name into out_result buffer
void LLVMBuilderCreateAdd(LLVMBuilder* b, const char* a, const char* b_op,
                           char* out_result, size_t out_size) {
    if (!b || !a || !b_op) { if (out_result && out_size > 0) *out_result = '\0'; return; }
    _gen_temp_name(b->context, out_result, out_size);
    _b_emit(b, "%s = add i32 %s, %s\n", out_result, a, b_op);
}

// Emit: <result> = sub i32 <a>, <b>
void LLVMBuilderCreateSub(LLVMBuilder* b, const char* a, const char* b_op,
                           char* out_result, size_t out_size) {
    if (!b || !a || !b_op) { if (out_result && out_size > 0) *out_result = '\0'; return; }
    _gen_temp_name(b->context, out_result, out_size);
    _b_emit(b, "%s = sub i32 %s, %s\n", out_result, a, b_op);
}

// Emit: <result> = mul i32 <a>, <b>
void LLVMBuilderCreateMul(LLVMBuilder* b, const char* a, const char* b_op,
                           char* out_result, size_t out_size) {
    if (!b || !a || !b_op) { if (out_result && out_size > 0) *out_result = '\0'; return; }
    _gen_temp_name(b->context, out_result, out_size);
    _b_emit(b, "%s = mul i32 %s, %s\n", out_result, a, b_op);
}

// Emit: <result> = sdiv i32 <a>, <b>
void LLVMBuilderCreateSDiv(LLVMBuilder* b, const char* a, const char* b_op,
                            char* out_result, size_t out_size) {
    if (!b || !a || !b_op) { if (out_result && out_size > 0) *out_result = '\0'; return; }
    _gen_temp_name(b->context, out_result, out_size);
    _b_emit(b, "%s = sdiv i32 %s, %s\n", out_result, a, b_op);
}

// Emit alloca for a local variable
// Writes the SSA result name into out_result buffer
void LLVMBuilderCreateAlloca(LLVMBuilder* b, IRType type, const char* name,
                              char* out_result, size_t out_size) {
    if (!b || !name || !out_result || out_size == 0) return;
    if (out_size > 0) *out_result = '\0';
    _gen_temp_name(b->context, out_result, out_size);
    const char* type_str = (type == IR_I32) ? "i32" : "i32";
    _b_emit(b, "%s = alloca %s, align 4\n", out_result, type_str);
}

// Emit: store i32 <val>, i32* <ptr>
void LLVMBuilderCreateStore(LLVMBuilder* b, const char* val, const char* ptr) {
    if (!b || !val || !ptr) return;
    _b_emit(b, "store i32 %s, i32* %s, align 4\n", val, ptr);
}

// Emit: <result> = load i32, i32* <ptr>
// Writes the SSA result name into out_result buffer
void LLVMBuilderCreateLoad(LLVMBuilder* b, const char* ptr,
                            char* out_result, size_t out_size) {
    if (!b || !ptr || !out_result || out_size == 0) return;
    if (out_size > 0) *out_result = '\0';
    _gen_temp_name(b->context, out_result, out_size);
    _b_emit(b, "%s = load i32, i32* %s, align 4\n", out_result, ptr);
}

// Close the current function
void LLVMBuilderEndFunction(LLVMBuilder* b) {
    if (!b) return;
    b->indent_level = 0;
    _mod_append(b->current_module, "}\n\n");
    b->current_function[0] = '\0';
    b->has_entry_block = 0;
}

// ============================================================
// Synapse AST → LLVM IR mapping helpers
// ============================================================

// Emit IR for a simple expression: return an integer literal
void LLVMEmitIntLiteral(LLVMBuilder* b, int value) {
    if (!b) return;
    LLVMBuilderCreateRetConst(b, value);
}

// Emit IR for a binary arithmetic expression.
// op: 0=add, 1=sub, 2=mul, 3=div
void LLVMEmitBinaryOp(LLVMBuilder* b, int op, int lhs, int rhs) {
    if (!b) return;
    char l_buf[32], r_buf[32], result_buf[64];
    LLVMBuilderConstInt(lhs, l_buf, sizeof(l_buf));
    LLVMBuilderConstInt(rhs, r_buf, sizeof(r_buf));
    switch (op) {
        case 0: LLVMBuilderCreateAdd(b, l_buf, r_buf, result_buf, sizeof(result_buf)); break;
        case 1: LLVMBuilderCreateSub(b, l_buf, r_buf, result_buf, sizeof(result_buf)); break;
        case 2: LLVMBuilderCreateMul(b, l_buf, r_buf, result_buf, sizeof(result_buf)); break;
        case 3: LLVMBuilderCreateSDiv(b, l_buf, r_buf, result_buf, sizeof(result_buf)); break;
        default: snprintf(result_buf, sizeof(result_buf), "0"); break;
    }
    LLVMBuilderCreateRet(b, result_buf);
}

// ============================================================
// High-level API: Build a complete Synapse program as LLVM IR
// ============================================================

// Build IR for a minimal valid program: returns a constant integer
// Returns the IR string (owned by module)
const char* BuildMinimalProgram(LLVMContext* ctx, const char* module_name,
                                int return_value) {
    if (!ctx || !module_name) return NULL;

    LLVMModule* mod = LLVMModuleCreateWithName(module_name, ctx);
    if (!mod) { LLVMContextSetError(ctx, "Failed to create module"); return NULL; }

    LLVMBuilder* builder = LLVMBuilderCreate(ctx);
    if (!builder) { LLVMModuleDispose(mod); return NULL; }
    LLVMBuilderSetModule(builder, mod);

    // Emit module header and runtime declarations
    LLVMModuleEmitHeader(mod);
    LLVMModuleEmitRuntimeDecls(mod);

    // Build the main function
    LLVMBuilderBeginFunction(builder, "main", IR_I32, 0);
    LLVMBuilderCreateEntryBlock(builder);
    LLVMEmitIntLiteral(builder, return_value);
    LLVMBuilderEndFunction(builder);

    LLVMBuilderDispose(builder);
    return LLVMModuleGetIR(mod);
}

// Build IR for a simple arithmetic expression
// Returns the IR string (owned by module)
const char* BuildArithmeticProgram(LLVMContext* ctx, const char* module_name,
                                   int op, int lhs, int rhs) {
    if (!ctx || !module_name) return NULL;

    LLVMModule* mod = LLVMModuleCreateWithName(module_name, ctx);
    if (!mod) { LLVMContextSetError(ctx, "Failed to create module"); return NULL; }

    LLVMBuilder* builder = LLVMBuilderCreate(ctx);
    if (!builder) { LLVMModuleDispose(mod); return NULL; }
    LLVMBuilderSetModule(builder, mod);

    LLVMModuleEmitHeader(mod);
    LLVMModuleEmitRuntimeDecls(mod);

    LLVMBuilderBeginFunction(builder, "main", IR_I32, 0);
    LLVMBuilderCreateEntryBlock(builder);
    LLVMEmitBinaryOp(builder, op, lhs, rhs);
    LLVMBuilderEndFunction(builder);

    LLVMBuilderDispose(builder);
    return LLVMModuleGetIR(mod);
}

// Clean up a built module (must be called when done with IR string)
void LLVMDisposeBuiltModule(LLVMModule* mod) {
    LLVMModuleDispose(mod);
}

// ============================================================
// Debug: print IR to stderr
// ============================================================
void LLVMModuleDump(LLVMModule* mod) {
    if (!mod || !mod->ir_buffer) return;
    fprintf(stderr, "%s", mod->ir_buffer);
}
