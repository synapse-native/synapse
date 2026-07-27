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
// Debug: print IR to stderr
// ============================================================
void LLVMModuleDump(LLVMModule* mod) {
    if (!mod || !mod->ir_buffer) return;
    fprintf(stderr, "%s", mod->ir_buffer);
}
