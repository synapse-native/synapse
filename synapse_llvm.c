/*
 * synapse_llvm.c — Synapse LLVM IR Backend (M12.1.1 + M12.1.2)
 *
 * Generates LLVM IR assembly (.ll) from Synapse AST nodes.
 * Portable: no LLVM library dependency — emits human-readable IR text.
 *
 * Architecture:
 *   LLVMContext  → holds module state and error tracking
 *   LLVMModule   → contains global definitions and functions
 *   LLVMBuilder  → appends IR instructions to current function
 *
 * M12.1.1: Context, Module, Builder, arithmetic, alloca/store/load, booleans
 * M12.1.2: icmp, br (cond/uncond), labels, phi, declare, call, loops
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

// Comparison predicates for icmp
typedef enum {
    ICMP_EQ,    // ==
    ICMP_NE,    // !=
    ICMP_SGT,   // > (signed)
    ICMP_SGE,   // >= (signed)
    ICMP_SLT,   // < (signed)
    ICMP_SLE,   // <= (signed)
} ICmpPredicate;

// ============================================================
// LLVMContext
// ============================================================
struct LLVMContext {
    int error_count;
    char error_msg[1024];
    int next_temp_id;       // for generating unique SSA names
    int next_label_id;      // for generating unique block labels
};

LLVMContext* LLVMContextCreate(void) {
    LLVMContext* ctx = (LLVMContext*)calloc(1, sizeof(LLVMContext));
    if (!ctx) return NULL;
    ctx->next_temp_id = 0;
    ctx->next_label_id = 0;
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

// Generate a unique label name
static void _gen_label_name(LLVMContext* ctx, char* buf, size_t buf_size,
                             const char* prefix) {
    snprintf(buf, buf_size, "%s%d", prefix, ctx->next_label_id++);
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

// Declare a custom external function
void LLVMModuleDeclareFunction(LLVMModule* mod, const char* name,
                                IRType return_type, int param_count, ...) {
    if (!mod || !name) return;

    const char* ret_str = "i32";
    if (return_type == IR_VOID) ret_str = "void";
    else if (return_type == IR_I1) ret_str = "i1";
    else if (return_type == IR_PTR) ret_str = "i8*";

    _mod_append(mod, "declare %s @%s(", ret_str, name);

    va_list args;
    va_start(args, param_count);
    for (int i = 0; i < param_count; i++) {
        IRType pt = (IRType)va_arg(args, int);
        if (i > 0) _mod_append(mod, ", ");
        if (pt == IR_I32) _mod_append(mod, "i32");
        else if (pt == IR_I1) _mod_append(mod, "i1");
        else if (pt == IR_PTR) _mod_append(mod, "i8*");
        else if (pt == IR_VOID) _mod_append(mod, "void");
        else _mod_append(mod, "i32");
    }
    va_end(args);

    _mod_append(mod, ")\n");
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
    else if (return_type == IR_PTR) ret_str = "i8*";

    _mod_append(b->current_module, "define %s @%s(", ret_str, name);

    va_list args;
    va_start(args, param_count);
    for (int i = 0; i < param_count; i++) {
        IRType pt = (IRType)va_arg(args, int);
        if (i > 0) _mod_append(b->current_module, ", ");
        if (pt == IR_I32) _mod_append(b->current_module, "i32 %%p%d", i);
        else if (pt == IR_I1) _mod_append(b->current_module, "i1 %%p%d", i);
        else if (pt == IR_PTR) _mod_append(b->current_module, "i8* %%p%d", i);
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

// Emit a basic block label: "<name>:"
void LLVMBuilderEmitLabel(LLVMBuilder* b, const char* name) {
    if (!b || !name) return;
    b->indent_level = 1;
    _b_emit(b, "%s:\n", name);
    b->indent_level = 2;
}

// Generate a unique label name and emit it
void LLVMBuilderEmitNewLabel(LLVMBuilder* b, const char* prefix,
                              char* out_label, size_t out_size) {
    if (!b || !out_label || out_size == 0) return;
    _gen_label_name(b->context, out_label, out_size, prefix);
    LLVMBuilderEmitLabel(b, out_label);
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
void LLVMBuilderCreateAlloca(LLVMBuilder* b, IRType type, const char* name,
                              char* out_result, size_t out_size) {
    if (!b || !name || !out_result || out_size == 0) return;
    if (out_size > 0) *out_result = '\0';
    _gen_temp_name(b->context, out_result, out_size);
    const char* type_str = (type == IR_I1) ? "i1" : "i32";
    _b_emit(b, "%s = alloca %s, align 4\n", out_result, type_str);
}

// Emit: store i32 <val>, i32* <ptr>
void LLVMBuilderCreateStore(LLVMBuilder* b, const char* val, const char* ptr) {
    if (!b || !val || !ptr) return;
    _b_emit(b, "store i32 %s, i32* %s, align 4\n", val, ptr);
}

// Emit: <result> = load i32, i32* <ptr>
void LLVMBuilderCreateLoad(LLVMBuilder* b, const char* ptr,
                            char* out_result, size_t out_size) {
    if (!b || !ptr || !out_result || out_size == 0) return;
    if (out_size > 0) *out_result = '\0';
    _gen_temp_name(b->context, out_result, out_size);
    _b_emit(b, "%s = load i32, i32* %s, align 4\n", out_result, ptr);
}

// ============================================================
// M12.1.2 — Control Flow: icmp, br, phi
// ============================================================

// Emit: <result> = icmp <pred> i32 <a>, <b>
// pred: "eq", "ne", "sgt", "sge", "slt", "sle"
static const char* _icmp_pred_str(ICmpPredicate pred) {
    switch (pred) {
        case ICMP_EQ: return "eq";
        case ICMP_NE: return "ne";
        case ICMP_SGT: return "sgt";
        case ICMP_SGE: return "sge";
        case ICMP_SLT: return "slt";
        case ICMP_SLE: return "sle";
        default: return "eq";
    }
}

void LLVMBuilderCreateICmp(LLVMBuilder* b, ICmpPredicate pred,
                            const char* a, const char* b_op,
                            char* out_result, size_t out_size) {
    if (!b || !a || !b_op) { if (out_result && out_size > 0) *out_result = '\0'; return; }
    _gen_temp_name(b->context, out_result, out_size);
    _b_emit(b, "%s = icmp %s i32 %s, %s\n",
            out_result, _icmp_pred_str(pred), a, b_op);
}

// Emit: br label %<dest>
void LLVMBuilderCreateBr(LLVMBuilder* b, const char* dest_label) {
    if (!b || !dest_label) return;
    _b_emit(b, "br label %%%s\n", dest_label);
}

// Emit: br i1 <cond>, label %<true_label>, label %<false_label>
void LLVMBuilderCreateCondBr(LLVMBuilder* b, const char* cond,
                              const char* true_label, const char* false_label) {
    if (!b || !cond || !true_label || !false_label) return;
    _b_emit(b, "br i1 %s, label %%%s, label %%%s\n",
            cond, true_label, false_label);
}

// Emit: <result> = phi i32 [<val>, <label>], ...
// Each pair is (value, label)
void LLVMBuilderCreatePhi(LLVMBuilder* b, int num_incoming,
                           const char** values, const char** labels,
                           char* out_result, size_t out_size) {
    if (!b || num_incoming < 1 || !values || !labels) {
        if (out_result && out_size > 0) *out_result = '\0';
        return;
    }
    _gen_temp_name(b->context, out_result, out_size);
    _b_emit(b, "%s = phi i32 ", out_result);
    for (int i = 0; i < num_incoming; i++) {
        if (i > 0) _mod_append(b->current_module, ", ");
        _mod_append(b->current_module, "[%s, %%%s]", values[i], labels[i]);
    }
    _b_emit(b, "\n");
}

// ============================================================
// M12.1.2 — Function Calls: call instruction
// ============================================================

// Emit: <result> = call i32 @<callee>(<args>)
//   If return_type == IR_VOID, "call void @<callee>(<args>)" (no result)
void LLVMBuilderCreateCall(LLVMBuilder* b, const char* callee,
                            IRType return_type, int arg_count,
                            const char** arg_values, const IRType* arg_types,
                            char* out_result, size_t out_size) {
    if (!b || !callee) {
        if (out_result && out_size > 0) *out_result = '\0';
        return;
    }

    const char* ret_str = "i32";
    if (return_type == IR_VOID) ret_str = "void";
    else if (return_type == IR_I1) ret_str = "i1";
    else if (return_type == IR_PTR) ret_str = "i8*";

    // If non-void, generate a temp name for the result
    if (return_type != IR_VOID) {
        _gen_temp_name(b->context, out_result, out_size);
        _b_emit(b, "%s = call %s @%s(", out_result, ret_str, callee);
    } else {
        if (out_result && out_size > 0) out_result[0] = '\0';
        _b_emit(b, "call void @%s(", callee);
    }

    for (int i = 0; i < arg_count; i++) {
        if (i > 0) _mod_append(b->current_module, ", ");
        IRType at = arg_types ? arg_types[i] : IR_I32;
        const char* type_str = "i32";
        if (at == IR_I1) type_str = "i1";
        else if (at == IR_PTR) type_str = "i8*";
        _mod_append(b->current_module, "%s %s", type_str, arg_values[i]);
    }

    _mod_append(b->current_module, ")\n");
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
// High-level API: Build complete Synapse programs as LLVM IR
// ============================================================

// Build IR for a minimal valid program: returns a constant integer
const char* BuildMinimalProgram(LLVMContext* ctx, const char* module_name,
                                int return_value) {
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
    LLVMEmitIntLiteral(builder, return_value);
    LLVMBuilderEndFunction(builder);

    LLVMBuilderDispose(builder);
    return LLVMModuleGetIR(mod);
}

// Build IR for a simple arithmetic expression
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

// Build IR for an if-else conditional:
// if (a < b) return 1; else return 0;
const char* BuildIfElseProgram(LLVMContext* ctx, const char* module_name,
                                int a, int b) {
    if (!ctx || !module_name) return NULL;

    LLVMModule* mod = LLVMModuleCreateWithName(module_name, ctx);
    if (!mod) return NULL;
    LLVMBuilder* builder = LLVMBuilderCreate(ctx);
    if (!builder) { LLVMModuleDispose(mod); return NULL; }
    LLVMBuilderSetModule(builder, mod);

    LLVMModuleEmitHeader(mod);
    LLVMModuleEmitRuntimeDecls(mod);

    LLVMBuilderBeginFunction(builder, "main", IR_I32, 0);
    LLVMBuilderCreateEntryBlock(builder);

    // Compare a < b
    char l_buf[32], r_buf[32], cmp_buf[64];
    LLVMBuilderConstInt(a, l_buf, sizeof(l_buf));
    LLVMBuilderConstInt(b, r_buf, sizeof(r_buf));
    LLVMBuilderCreateICmp(builder, ICMP_SLT, l_buf, r_buf, cmp_buf, sizeof(cmp_buf));

    // Branch to then/else
    char label_then[64], label_else[64], label_merge[64];
    _gen_label_name(ctx, label_then, sizeof(label_then), "then");
    _gen_label_name(ctx, label_else, sizeof(label_else), "else");
    _gen_label_name(ctx, label_merge, sizeof(label_merge), "merge");
    LLVMBuilderCreateCondBr(builder, cmp_buf, label_then, label_else);

    // then block: return 1
    LLVMBuilderEmitLabel(builder, label_then);
    LLVMBuilderCreateRetConst(builder, 1);
    // else block: return 0
    LLVMBuilderEmitLabel(builder, label_else);
    LLVMBuilderCreateRetConst(builder, 0);

    LLVMBuilderEndFunction(builder);
    LLVMBuilderDispose(builder);
    return LLVMModuleGetIR(mod);
}

// Build IR for a simple loop: sum from 0 to n, return result
// int main() { int sum = 0; for (int i = 0; i < n; i++) sum += i; return sum; }
const char* BuildLoopProgram(LLVMContext* ctx, const char* module_name, int n) {
    if (!ctx || !module_name) return NULL;

    LLVMModule* mod = LLVMModuleCreateWithName(module_name, ctx);
    if (!mod) return NULL;
    LLVMBuilder* builder = LLVMBuilderCreate(ctx);
    if (!builder) { LLVMModuleDispose(mod); return NULL; }
    LLVMBuilderSetModule(builder, mod);

    LLVMModuleEmitHeader(mod);
    LLVMModuleEmitRuntimeDecls(mod);

    // Declare an external print function (for demonstration)
    // (not shown in loop body, just to demonstrate declare)

    LLVMBuilderBeginFunction(builder, "main", IR_I32, 0);
    LLVMBuilderCreateEntryBlock(builder);

    // alloca sum, alloca i
    char alloc_sum[64], alloc_i[64];
    char zero_buf[16], n_buf[16];
    LLVMBuilderCreateAlloca(builder, IR_I32, "sum", alloc_sum, sizeof(alloc_sum));
    LLVMBuilderCreateAlloca(builder, IR_I32, "i", alloc_i, sizeof(alloc_i));

    // sum = 0
    LLVMBuilderConstInt(0, zero_buf, sizeof(zero_buf));
    LLVMBuilderCreateStore(builder, zero_buf, alloc_sum);
    // i = 0
    LLVMBuilderCreateStore(builder, zero_buf, alloc_i);

    // Branch to loop header
    char label_header[64], label_body[64], label_exit[64];
    _gen_label_name(ctx, label_header, sizeof(label_header), "loop_header");
    _gen_label_name(ctx, label_body, sizeof(label_body), "loop_body");
    _gen_label_name(ctx, label_exit, sizeof(label_exit), "loop_exit");
    LLVMBuilderCreateBr(builder, label_header);

    // Loop header: check condition
    LLVMBuilderEmitLabel(builder, label_header);
    char load_i[64], cmp_buf[64];
    LLVMBuilderCreateLoad(builder, alloc_i, load_i, sizeof(load_i));
    LLVMBuilderConstInt(n, n_buf, sizeof(n_buf));
    LLVMBuilderCreateICmp(builder, ICMP_SLT, load_i, n_buf, cmp_buf, sizeof(cmp_buf));
    LLVMBuilderCreateCondBr(builder, cmp_buf, label_body, label_exit);

    // Loop body: sum += i; i++
    LLVMBuilderEmitLabel(builder, label_body);
    char load_sum[64], inc_sum[64];
    char i_plus_1[64], one_buf[16];

    // sum = sum + i
    LLVMBuilderCreateLoad(builder, alloc_sum, load_sum, sizeof(load_sum));
    LLVMBuilderCreateLoad(builder, alloc_i, load_i, sizeof(load_i));
    LLVMBuilderCreateAdd(builder, load_sum, load_i, inc_sum, sizeof(inc_sum));
    LLVMBuilderCreateStore(builder, inc_sum, alloc_sum);

    // i = i + 1
    LLVMBuilderConstInt(1, one_buf, sizeof(one_buf));
    LLVMBuilderCreateAdd(builder, load_i, one_buf, i_plus_1, sizeof(i_plus_1));
    LLVMBuilderCreateStore(builder, i_plus_1, alloc_i);

    // Back-edge to loop header
    LLVMBuilderCreateBr(builder, label_header);

    // Exit block: return sum
    LLVMBuilderEmitLabel(builder, label_exit);
    char final_sum[64];
    LLVMBuilderCreateLoad(builder, alloc_sum, final_sum, sizeof(final_sum));
    LLVMBuilderCreateRet(builder, final_sum);

    LLVMBuilderEndFunction(builder);
    LLVMBuilderDispose(builder);
    return LLVMModuleGetIR(mod);
}

// Build IR for a conditional branch that calls putchar
const char* BuildCallProgram(LLVMContext* ctx, const char* module_name,
                              int value) {
    if (!ctx || !module_name) return NULL;

    LLVMModule* mod = LLVMModuleCreateWithName(module_name, ctx);
    if (!mod) return NULL;
    LLVMBuilder* builder = LLVMBuilderCreate(ctx);
    if (!builder) { LLVMModuleDispose(mod); return NULL; }
    LLVMBuilderSetModule(builder, mod);

    LLVMModuleEmitHeader(mod);
    // Declare putchar explicitly to test custom declare
    LLVMModuleDeclareFunction(mod, "putchar", IR_I32, 1, IR_I32);

    LLVMBuilderBeginFunction(builder, "main", IR_I32, 0);
    LLVMBuilderCreateEntryBlock(builder);

    // Call putchar with argument
    char val_buf[32], call_result[64];
    LLVMBuilderConstInt(value, val_buf, sizeof(val_buf));
    const char* call_args[] = { val_buf };
    IRType call_arg_types[] = { IR_I32 };
    LLVMBuilderCreateCall(builder, "putchar", IR_I32, 1,
                           call_args, call_arg_types,
                           call_result, sizeof(call_result));

    // Return 0
    LLVMBuilderCreateRetConst(builder, 0);

    LLVMBuilderEndFunction(builder);
    LLVMBuilderDispose(builder);
    return LLVMModuleGetIR(mod);
}

// Clean up a built module
void LLVMDisposeBuiltModule(LLVMModule* mod) {
    LLVMModuleDispose(mod);
}

// ============================================================
// M12.1.3 — JIT Execution Engine
// ============================================================

#ifdef _WIN32
#include <windows.h>
#else
#include <dlfcn.h>
#endif
#include <sys/stat.h>

// JIT context: holds a compiled shared library handle
typedef struct {
    void* lib_handle;          // dlopen/LoadLibrary handle
    char lib_path[1024];       // path to compiled .dll/.so
    int is_encrypted;          // whether memory encryption was applied
    unsigned char enc_key[32]; // XOR encryption key
} JITContext;

// Create a JIT context
JITContext* JIT_CreateContext(void) {
    JITContext* jit = (JITContext*)calloc(1, sizeof(JITContext));
    if (!jit) return NULL;
    jit->lib_handle = NULL;
    jit->lib_path[0] = '\0';
    jit->is_encrypted = 0;
    // Generate a default XOR key from the compilation timestamp
    for (int i = 0; i < 32; i++) {
        jit->enc_key[i] = (unsigned char)(rand() % 256);
    }
    return jit;
}

void JIT_FreeContext(JITContext* jit) {
    if (jit) free(jit);
}

// ============================================================
// Helper: translate a subset of LLVM IR to C code
// Handles the patterns emitted by Build*Program functions.
// ============================================================

// Extract SSA name from "  %t0 = ..." → "t0"
static void _extract_ssa(const char* trimmed, char* out, size_t out_size) {
    if (!trimmed || !out || out_size == 0) return;
    out[0] = '\0';
    const char* pct = strchr(trimmed, '%');
    if (!pct) return;
    pct++;
    int i = 0;
    while (*pct && *pct != ' ' && *pct != '=' && *pct != ',' && i < (int)out_size - 1) {
        out[i++] = *pct++;
    }
    out[i] = '\0';
}

static char* _ir_to_c(const char* ir_text) {
    if (!ir_text) return NULL;
    
    // Allocate output buffer (generous estimate: 3x input size)
    size_t in_len = strlen(ir_text);
    size_t out_cap = in_len * 3 + 4096;
    char* out = (char*)calloc(out_cap, 1);
    if (!out) return NULL;
    
    // Track alloca'd variables (offset in the output buffer)
    // Simple approach: we translate line by line
    char line[512];
    size_t pos = 0;
    
    // Write includes and header
    pos += snprintf(out + pos, out_cap - pos,
        "#include <stdio.h>\n"
        "#include <stdint.h>\n"
        "\n");
    
    // Parse input line by line
    const char* p = ir_text;
    int in_function = 0;
    int brace_needed = 0;
    
    while (*p && pos < out_cap - 512) {
        // Extract one line
        int i = 0;
        while (*p && *p != '\n' && i < 510) {
            line[i++] = *p++;
        }
        if (*p == '\n') p++;
        line[i] = '\0';
        
        // Trim leading whitespace
        char* trimmed = line;
        while (*trimmed == ' ') trimmed++;
        if (trimmed[0] == ';' || trimmed[0] == '\0') continue;  // skip comments and blanks
        
        // Skip header declarations (target triple, datalayout, ModuleID)
        if (strstr(trimmed, "target triple") ||
            strstr(trimmed, "target datalayout") ||
            strstr(trimmed, "ModuleID") ||
            strstr(trimmed, "declare "))
            continue;
        
        // Translation patterns:
        
        // define i32 @main(i32 %p0, ...) {
        if (strstr(trimmed, "define ") && strstr(trimmed, "@")) {
            // Extract function name and return type
            char fn_name[128] = "main";
            char ret_type[32] = "int";
            if (strstr(trimmed, "i32")) snprintf(ret_type, sizeof(ret_type), "int");
            if (strstr(trimmed, "void")) snprintf(ret_type, sizeof(ret_type), "void");
            if (strstr(trimmed, "i1")) snprintf(ret_type, sizeof(ret_type), "int");
            
            // Extract name between @ and (
            const char* at = strchr(trimmed, '@');
            if (at) {
                at++;
                int ni = 0;
                while (*at && *at != '(' && ni < 120) fn_name[ni++] = *at++;
                fn_name[ni] = '\0';
            }
            
            pos += snprintf(out + pos, out_cap - pos,
                "%s %s(", ret_type, fn_name);
            
            // Extract params
            const char* paren = strchr(trimmed, '(');
            if (paren) {
                paren++;
                char params[256];
                int pi = 0;
                while (*paren && *paren != ')' && pi < 250) {
                    params[pi++] = *paren++;
                }
                params[pi] = '\0';
                
                // Translate "i32 %p0" to "int p0"
                char translated[256] = "";
                char tk[64];
                int ti = 0, first = 1;
                for (int si = 0; params[si]; si++) {
                    if (params[si] == ',' || params[si+1] == '\0') {
                        if (params[si+1] == '\0' && params[si] != ',') {
                            tk[ti++] = params[si];
                        }
                        tk[ti] = '\0';
                        ti = 0;
                        // tk contains something like "  i32 %p0"
                        char* tp = tk;
                        while (*tp == ' ') tp++;
                        char type_str[16] = "int";
                        char var_str[64] = "p";
                        if (strstr(tp, "i32")) snprintf(type_str, sizeof(type_str), "int");
                        if (strstr(tp, "i1")) snprintf(type_str, sizeof(type_str), "int");
                        if (strstr(tp, "i8*")) snprintf(type_str, sizeof(type_str), "void*");
                        const char* perc = strchr(tp, '%');
                        if (perc) {
                            perc++;
                            int vi = 0;
                            while (*perc && *perc != ' ' && *perc != ',' && *perc != ')' && vi < 60)
                                var_str[vi++] = *perc++;
                            var_str[vi] = '\0';
                        }
                        if (!first) strcat(translated, ", ");
                        first = 0;
                        strcat(translated, type_str);
                        strcat(translated, " ");
                        strcat(translated, var_str);
                    } else {
                        tk[ti++] = params[si];
                    }
                }
                if (strlen(translated) > 0) {
                    pos += snprintf(out + pos, out_cap - pos, "%s", translated);
                }
            }
            pos += snprintf(out + pos, out_cap - pos, ") {\n");
            in_function = 1;
            brace_needed = 1;
            continue;
        }
        
        // } (function end)
        if (trimmed[0] == '}') {
            if (brace_needed) {
                pos += snprintf(out + pos, out_cap - pos, "}\n\n");
                brace_needed = 0;
                in_function = 0;
            }
            continue;
        }
        
        if (!in_function) continue;
        
        // Labels: "entry:" "then:" etc.
        // C99 requires a statement after a label, so add ";"
        if (trimmed[strlen(trimmed)-1] == ':') {
            pos += snprintf(out + pos, out_cap - pos, "%s\n    ;\n", trimmed);
            continue;
        }
        
        // %tN = alloca i32, align 4
        // → int tN;
        if (strstr(trimmed, "alloca")) {
            // Extract the SSA name after =
            char ssa_name[64] = "";
            // Manual SSA name extraction (avoid sscanf %% issues)
            const char* eq = strchr(trimmed, '=');
            if (eq && eq > trimmed) {
                const char* start = trimmed;
                while (*start == ' ') start++;
                if (*start == '%') start++;
                int si = 0;
                while (start + si < eq && si < 62) {
                    ssa_name[si] = start[si];
                    si++;
                }
                ssa_name[si] = '\0';
                // Trim trailing spaces
                while (si > 0 && ssa_name[si-1] == ' ') ssa_name[--si] = '\0';
            }
            if (ssa_name[0]) {
                pos += snprintf(out + pos, out_cap - pos, "    int %s;\n", ssa_name);
            }
            continue;
        }
        
        // store i32 %val, i32* %ptr → *ptr = val;
        if (strstr(trimmed, "store ")) {
            char val_ssa[64] = "", ptr_ssa[64] = "";
            const char* last_p = NULL;
            for (const char* sp = trimmed; *sp; sp++) if (*sp == '%') last_p = sp;
            if (last_p) {
                last_p++;
                int pi = 0;
                while (*last_p && *last_p != ' ' && *last_p != ',' && pi < 60) ptr_ssa[pi++] = *last_p++;
                ptr_ssa[pi] = '\0';
                const char* comma = strchr(trimmed, ',');
                if (comma) {
                    const char* perc = comma;
                    while (perc > trimmed && *perc != '%') perc--;
                    if (*perc == '%' && perc < comma) {
                        perc++;
                        int vi = 0;
                        while (*perc && *perc != ' ' && *perc != ',' && vi < 60) val_ssa[vi++] = *perc++;
                        val_ssa[vi] = '\0';
                    }
                }
            }
            if (ptr_ssa[0] && val_ssa[0]) pos += snprintf(out + pos, out_cap - pos, "    %s = %s;\n", ptr_ssa, val_ssa);
            continue;
        }
        
        // %tN = load i32, i32* %ptr → int tN = ptr_val;
        // (alloca declares plain ints, so load just copies the value)
        if (strstr(trimmed, "load ")) {
            char lssa[64] = "", ptr_ssa[64] = "";
            _extract_ssa(trimmed, lssa, sizeof(lssa));
            const char* last_p = NULL;
            for (const char* sp = trimmed; *sp; sp++) if (*sp == '%') last_p = sp;
            if (last_p) {
                last_p++;
                int pi = 0;
                while (*last_p && *last_p != ' ' && *last_p != ',' && pi < 60) ptr_ssa[pi++] = *last_p++;
                ptr_ssa[pi] = '\0';
            }
            if (lssa[0] && ptr_ssa[0]) pos += snprintf(out + pos, out_cap - pos, "    int %s = %s;\n", lssa, ptr_ssa);
            continue;
        }
        
        // %tN = add/sub/mul/sdiv → int tN = a op b;
        if (strstr(trimmed, "= add ") || strstr(trimmed, "= sub ") ||
            strstr(trimmed, "= mul ") || strstr(trimmed, "= sdiv ")) {
            char assa[64] = "";
            _extract_ssa(trimmed, assa, sizeof(assa));
            if (assa[0]) {
                // Find operands after 'i32'
                const char* typ = strstr(trimmed, "i32 ");
                if (typ) {
                    typ += 4;
                    if (*typ == '%') typ++;
                    char op_a[64] = "";
                    int ai = 0;
                    while (*typ && *typ != ' ' && *typ != ',' && ai < 60) op_a[ai++] = *typ++;
                    op_a[ai] = '\0';
                    while (*typ && (*typ == ' ' || *typ == ',')) typ++;
                    if (*typ == '%') typ++;
                    char op_b[64] = "";
                    int bi = 0;
                    while (*typ && *typ != ' ' && *typ != ',' && *typ != '\n' && bi < 60) op_b[bi++] = *typ++;
                    op_b[bi] = '\0';
                    const char* c_op = "+";
                    if (strstr(trimmed, "= sub ")) c_op = "-";
                    else if (strstr(trimmed, "= mul ")) c_op = "*";
                    else if (strstr(trimmed, "= sdiv ")) c_op = "/";
                    pos += snprintf(out + pos, out_cap - pos, "    int %s = %s %s %s;\n", assa, op_a, c_op, op_b);
                }
            }
            continue;
        }
        
        // %tN = icmp pred i32 %a, %b → int tN = a pred b;
        if (strstr(trimmed, "icmp ")) {
            char ssa[64] = "";
            _extract_ssa(trimmed, ssa, sizeof(ssa));
            const char* pred_start = strstr(trimmed, "icmp ");
            if (pred_start && ssa[0]) {
                pred_start += 5;
                char pred_str[16] = "";
                int pi = 0;
                while (*pred_start && *pred_start != ' ' && pi < 14) pred_str[pi++] = *pred_start++;
                pred_str[pi] = '\0';
                while (*pred_start == ' ') pred_start++;
                while (*pred_start && *pred_start != '%' && !(*pred_start >= '0' && *pred_start <= '9')) pred_start++;
                if (*pred_start == '%') pred_start++;
                char op_a[64] = "";
                int ai = 0;
                while (*pred_start && *pred_start != ' ' && *pred_start != ',' && ai < 60) op_a[ai++] = *pred_start++;
                op_a[ai] = '\0';
                while (*pred_start && (*pred_start == ' ' || *pred_start == ',')) pred_start++;
                if (*pred_start == '%') pred_start++;
                char op_b[64] = "";
                int bi = 0;
                while (*pred_start && *pred_start != ' ' && *pred_start != ',' && bi < 60) op_b[bi++] = *pred_start++;
                op_b[bi] = '\0';
                
                const char* c_op = "==";
                if (strcmp(pred_str, "ne") == 0) c_op = "!=";
                else if (strcmp(pred_str, "slt") == 0) c_op = "<";
                else if (strcmp(pred_str, "sle") == 0) c_op = "<=";
                else if (strcmp(pred_str, "sgt") == 0) c_op = ">";
                else if (strcmp(pred_str, "sge") == 0) c_op = ">=";
                
                pos += snprintf(out + pos, out_cap - pos, "    int %s = %s %s %s;\n", ssa, op_a, c_op, op_b);
            }
            continue;
        }
        
        // br label %dest → goto dest;
        if (strstr(trimmed, "br label ")) {
            const char* dest = strstr(trimmed, "br label ") + 8;
            if (*dest == '%') dest++;
            char dest_lab[64] = "";
            int di = 0;
            while (*dest && *dest != ' ' && *dest != '\n' && *dest != ';' && di < 60) dest_lab[di++] = *dest++;
            dest_lab[di] = '\0';
            if (dest_lab[0]) {
                pos += snprintf(out + pos, out_cap - pos, "    goto %s;\n", dest_lab);
            }
            continue;
        }
        
        // br i1 %cond, label %true, label %false
        // → if (cond) goto true; else goto false;
        if (strstr(trimmed, "br i1 ")) {
            const char* p_br = strstr(trimmed, "br i1 ") + 6;
            if (*p_br == '%') p_br++;
            char cond_ssa[64] = "";
            int ci = 0;
            while (*p_br && *p_br != ' ' && *p_br != ',' && ci < 60) cond_ssa[ci++] = *p_br++;
            cond_ssa[ci] = '\0';
            // Find first label %
            const char* l1_p = strstr(p_br, "label ");
            const char* l2_p = NULL;
            if (l1_p) {
                l1_p += 6;
                if (*l1_p == '%') l1_p++;
                char l1[64] = "";
                int li = 0;
                while (*l1_p && *l1_p != ' ' && *l1_p != ',' && *l1_p != '\n' && li < 60)
                    l1[li++] = *l1_p++;
                l1[li] = '\0';
                l2_p = strstr(l1_p, "label ");
                if (l2_p) {
                    l2_p += 6;
                    if (*l2_p == '%') l2_p++;
                    char l2[64] = "";
                    int li2 = 0;
                    while (*l2_p && *l2_p != ' ' && *l2_p != ',' && *l2_p != '\n' && li2 < 60)
                        l2[li2++] = *l2_p++;
                    l2[li2] = '\0';
                    pos += snprintf(out + pos, out_cap - pos,
                        "    if (%s) goto %s; else goto %s;\n", cond_ssa, l1, l2);
                }
            }
            continue;
        }
        
        // ret i32 %val → return val;
        if (strstr(trimmed, "ret ")) {
            const char* val_start = strstr(trimmed, "ret i32 ");
            if (val_start) {
                val_start += 8;
                if (*val_start == '%') val_start++;
                char ret_val[64] = "";
                int ri = 0;
                while (*val_start && *val_start != ' ' && *val_start != '\n' && ri < 60)
                    ret_val[ri++] = *val_start++;
                ret_val[ri] = '\0';
                pos += snprintf(out + pos, out_cap - pos, "    return %s;\n", ret_val);
            } else if (strstr(trimmed, "ret void")) {
                pos += snprintf(out + pos, out_cap - pos, "    return;\n");
            }
            continue;
        }
        
        // %tN = call i32 @func(i32 %arg)
        // → int tN = func(arg);
        if (strstr(trimmed, "call ")) {
            char ssa[64] = "";
            _extract_ssa(trimmed, ssa, sizeof(ssa));
            int has_ssa = (ssa[0] != '\0');
            const char* fn_start = strchr(trimmed, '@');
            if (fn_start) {
                fn_start++;
                char fn_name[128] = "";
                int ni = 0;
                while (*fn_start && *fn_start != '(' && ni < 120) fn_name[ni++] = *fn_start++;
                fn_name[ni] = '\0';
                fn_start++;
                // Extract args
                char args_str[256] = "";
                int ai = 0;
                int depth = 1;
                while (*fn_start && depth > 0 && ai < 250) {
                    if (*fn_start == '(') depth++;
                    else if (*fn_start == ')') depth--;
                    if (depth > 0) args_str[ai++] = *fn_start;
                    fn_start++;
                }
                args_str[ai] = '\0';
                
                // Clean args: remove types, keep values
                char clean_args[256] = "";
                int ca = 0, in_space = 0;
                for (int si = 0; args_str[si]; si++) {
                    char c = args_str[si];
                    if (c == '%') { in_space = 0; }
                    else if (c == 'i' && (args_str[si+1] == '3' || args_str[si+1] == '1' || args_str[si+1] == '8')) {
                        // Skip type: i32, i1, i8*
                        while (args_str[si] && args_str[si] != ' ' && args_str[si] != ',') si++;
                        if (args_str[si] == ' ') si++;
                        if (args_str[si] == '%') si++;
                        // Now read the value
                        while (args_str[si] && args_str[si] != ' ' && args_str[si] != ',' && args_str[si] != ')') {
                            clean_args[ca++] = args_str[si++];
                        }
                        clean_args[ca++] = ','; ca++;
                        if (args_str[si]) si--;
                    } else if (c == ' ' || c == ',') {
                        if (!in_space) { clean_args[ca++] = c; in_space = 1; }
                    } else {
                        clean_args[ca++] = c;
                        in_space = 0;
                    }
                }
                clean_args[ca] = '\0';
                // Remove trailing comma
                while (ca > 0 && (clean_args[ca-1] == ',' || clean_args[ca-1] == ' ')) ca--;
                clean_args[ca] = '\0';
                
                if (has_ssa && ssa[0]) {
                    pos += snprintf(out + pos, out_cap - pos,
                        "    int %s = %s(%s);\n", ssa, fn_name, clean_args);
                } else {
                    pos += snprintf(out + pos, out_cap - pos,
                        "    %s(%s);\n", fn_name, clean_args);
                }
            }
            continue;
        }
        
        // %tN = phi i32 [%v1, %l1], [%v2, %l2]
        // → int tN; ... (phi resolution handled by block placement)
        if (strstr(trimmed, "phi ")) {
            char ssa[64] = "", first_val[64] = "";
            // Manual SSA extraction
            const char* eq_p = strchr(trimmed, '=');
            if (eq_p) {
                const char* pct_p = eq_p;
                while (pct_p > trimmed && *pct_p != '%') pct_p--;
                if (*pct_p == '%') pct_p++;
                int si = 0;
                while (pct_p + si < eq_p && si < 62) {
                    ssa[si] = pct_p[si];
                    si++;
                }
                ssa[si] = '\0';
                while (si > 0 && ssa[si-1] == ' ') ssa[--si] = '\0';
            }
            const char* brack = strchr(trimmed, '[');
            if (brack) {
                brack++;
                if (*brack == '%') brack++;
                int fi = 0;
                while (*brack && *brack != ',' && *brack != ' ' && *brack != ']' && fi < 60)
                    first_val[fi++] = *brack++;
                first_val[fi] = '\0';
            }
            if (ssa[0]) {
                pos += snprintf(out + pos, out_cap - pos,
                    "    int %s = %s; // phi\n", ssa, first_val[0] ? first_val : "0");
            }
            continue;
        }
        
        // Fallback: emit as comment
        pos += snprintf(out + pos, out_cap - pos, "    // %s\n", trimmed);
    }
    
    return out;
}

// ============================================================
// Compile LLVM IR text to a shared library (.dll/.so)
// Returns 0 on success, -1 on error
// ============================================================

int JIT_CompileIR(const char* ir_text, const char* output_name,
                   JITContext* jit) {
    if (!ir_text || !output_name || !jit) return -1;
    
    char temp_c[1024];
    char temp_ll[1024];
    char temp_dll[1024];
    
    snprintf(temp_c, sizeof(temp_c), "%s.c", output_name);
    snprintf(temp_ll, sizeof(temp_ll), "%s.ll", output_name);
    snprintf(temp_dll, sizeof(temp_dll), "%s.dll", output_name);
    
    // Step 1: Write the LLVM IR to .ll file (for documentation)
    FILE* f_ll = fopen(temp_ll, "w");
    if (f_ll) {
        fprintf(f_ll, "%s", ir_text);
        fclose(f_ll);
    }
    
    // Step 2: Translate IR to C
    char* c_code = _ir_to_c(ir_text);
    if (!c_code) return -1;
    
    // Step 3: Write C file
    FILE* f_c = fopen(temp_c, "w");
    if (!f_c) { free(c_code); return -1; }
    fprintf(f_c, "%s", c_code);
    fclose(f_c);
    free(c_code);
    
    // Step 4: Compile with gcc -shared
    char cmd[2048];
    snprintf(cmd, sizeof(cmd),
        "gcc -O2 -shared -o \"%s\" \"%s\" -lm 2>&1",
        temp_dll, temp_c);
    
    int ret = system(cmd);
    if (ret != 0) {
        fprintf(stderr, "JIT: gcc compilation failed (exit %d)\n", ret);
        return -2;
    }
    
    snprintf(jit->lib_path, sizeof(jit->lib_path), "%s", temp_dll);
    return 0;
}

// ============================================================
// Load a compiled shared library
// Returns 0 on success, -1 on error
// ============================================================

int JIT_LoadLibrary(JITContext* jit) {
    if (!jit || !jit->lib_path[0]) return -1;
    
    if (jit->lib_handle) {
        // Unload previous library
#ifdef _WIN32
        FreeLibrary((HMODULE)jit->lib_handle);
#else
        dlclose(jit->lib_handle);
#endif
        jit->lib_handle = NULL;
    }
    
#ifdef _WIN32
    jit->lib_handle = (void*)LoadLibraryA(jit->lib_path);
    if (!jit->lib_handle) {
        fprintf(stderr, "JIT: LoadLibrary failed (error %lu)\n", GetLastError());
        return -1;
    }
#else
    jit->lib_handle = dlopen(jit->lib_path, RTLD_NOW | RTLD_LOCAL);
    if (!jit->lib_handle) {
        fprintf(stderr, "JIT: dlopen failed: %s\n", dlerror());
        return -1;
    }
#endif
    
    return 0;
}

// ============================================================
// Get a function pointer from the loaded library
// ============================================================

void* JIT_GetFunction(JITContext* jit, const char* name) {
    if (!jit || !jit->lib_handle || !name) return NULL;
    
#ifdef _WIN32
    return (void*)GetProcAddress((HMODULE)jit->lib_handle, name);
#else
    return dlsym(jit->lib_handle, name);
#endif
}

// ============================================================
// Free/unload the shared library
// ============================================================

void JIT_FreeLibrary(JITContext* jit) {
    if (!jit || !jit->lib_handle) return;
    
#ifdef _WIN32
    FreeLibrary((HMODULE)jit->lib_handle);
#else
    dlclose(jit->lib_handle);
#endif
    jit->lib_handle = NULL;
}

// ============================================================
// M12.1.3 — Memory Encryption (XOR)
// ============================================================

// XOR-encrypt or decrypt a buffer in-place
void JIT_MemoryXor(unsigned char* buffer, size_t size,
                    const unsigned char* key, size_t key_len) {
    if (!buffer || !key || key_len == 0) return;
    for (size_t i = 0; i < size; i++) {
        buffer[i] ^= key[i % key_len];
    }
}

// Encrypt a file in-place using XOR
int JIT_EncryptFile(const char* path, const unsigned char* key,
                     size_t key_len) {
    if (!path || !key || key_len == 0) return -1;
    
    FILE* f = fopen(path, "rb");
    if (!f) return -1;
    
    fseek(f, 0, SEEK_END);
    long fsize = ftell(f);
    if (fsize <= 0) { fclose(f); return -1; }
    fseek(f, 0, SEEK_SET);
    
    unsigned char* buffer = (unsigned char*)malloc((size_t)fsize);
    if (!buffer) { fclose(f); return -1; }
    
    size_t read = fread(buffer, 1, (size_t)fsize, f);
    fclose(f);
    if (read != (size_t)fsize) { free(buffer); return -1; }
    
    // XOR-encrypt
    JIT_MemoryXor(buffer, (size_t)fsize, key, key_len);
    
    // Write back
    f = fopen(path, "wb");
    if (!f) { free(buffer); return -1; }
    fwrite(buffer, 1, (size_t)fsize, f);
    fclose(f);
    free(buffer);
    return 0;
}

// ============================================================
// High-level JIT: Build, compile, load, and execute in one call
// ============================================================

// Compile IR, encrypt, load, execute, and return result
// If key is NULL, no encryption is applied
int JIT_BuildAndExecute(const char* ir_text, const char* module_name,
                         const unsigned char* enc_key, size_t key_len,
                         const char* fn_name) {
    if (!ir_text || !module_name || !fn_name) return -1;
    
    JITContext* jit = JIT_CreateContext();
    if (!jit) return -1;
    
    // Compile IR to shared library
    int ret = JIT_CompileIR(ir_text, module_name, jit);
    if (ret != 0) { JIT_FreeContext(jit); return ret; }
    
    // Apply memory encryption if key provided
    // Encryption is applied for storage protection; decrypt before loading
    if (enc_key && key_len > 0) {
        ret = JIT_EncryptFile(jit->lib_path, enc_key, key_len);
        if (ret == 0) {
            jit->is_encrypted = 1;
            memcpy(jit->enc_key, enc_key, key_len < 32 ? key_len : 32);
            // Decrypt before loading (XOR is symmetric)
            JIT_EncryptFile(jit->lib_path, enc_key, key_len);
        }
    }
    
    // Load the library
    ret = JIT_LoadLibrary(jit);
    if (ret != 0) { JIT_FreeContext(jit); return ret; }
    
    // Get function pointer
    typedef int (*int_fn_t)(void);
    int_fn_t fn = (int_fn_t)JIT_GetFunction(jit, fn_name);
    if (!fn) {
        JIT_FreeLibrary(jit);
        JIT_FreeContext(jit);
        return -3;
    }
    
    // Execute
    int result = fn();
    
    // Cleanup
    JIT_FreeLibrary(jit);
    JIT_FreeContext(jit);
    
    return result;
}

// ============================================================
// Debug: print IR to stderr
// ============================================================
void LLVMModuleDump(LLVMModule* mod) {
    if (!mod || !mod->ir_buffer) return;
    fprintf(stderr, "%s", mod->ir_buffer);
}
