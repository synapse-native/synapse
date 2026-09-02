// cumple Manual 1 5: backend LLVM
// cumple Manual 8 4.2: target LLVM
// =============================================================================
// synapse_llvm.c — LLVM IR text emitter (M12.1.1)
//
// Genera LLVM IR de texto (.ll) sin dependencias externas (sin libLLVM).
// Implementa la API declarada en synapse_llvm.h / std/llvm.syn.
//
// Referencias: Manual 1 §5 ("Traduce AST a C, LLVM IR o WAT"), §6 (Backend LLVM)
// =============================================================================
#include "synapse_llvm.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

// --- Buffer dinámico simple ---
typedef struct {
    char* buf;
    int len;
    int cap;
} BufDinamico;

static void _buf_init(BufDinamico* b) {
    b->cap = 4096;
    b->len = 0;
    b->buf = (char*)malloc(b->cap);
    b->buf[0] = '\0';
}

static void _buf_append(BufDinamico* b, const char* fmt, ...) {
    if (b->len + 512 >= b->cap) {
        while (b->len + 512 >= b->cap) b->cap *= 2;
        b->buf = (char*)realloc(b->buf, b->cap);
    }
    va_list ap;
    va_start(ap, fmt);
    b->len += vsnprintf(b->buf + b->len, b->cap - b->len, fmt, ap);
    va_end(ap);
}

static void _mod_append(LLVMModule* mod, const char* fmt, ...) {
    if (mod->ir_len + 512 >= mod->ir_cap) {
        mod->ir_cap = (mod->ir_cap == 0) ? 4096 : mod->ir_cap * 2;
        mod->ir_buffer = (char*)realloc(mod->ir_buffer, mod->ir_cap);
    }
    va_list ap;
    va_start(ap, fmt);
    mod->ir_len += vsnprintf(mod->ir_buffer + mod->ir_len,
        mod->ir_cap - mod->ir_len, fmt, ap);
    va_end(ap);
}

static void _builder_indent(LLVMBuilder* b) {
    for (int i = 0; i < b->indent; i++)
        _mod_append(b->mod, "  ");
}

LLVMContext* LLVMContextCreate(void) {
    LLVMContext* ctx = (LLVMContext*)calloc(1, sizeof(LLVMContext));
    return ctx;
}

void LLVMContextDispose(LLVMContext* ctx) {
    if (ctx) free(ctx);
}

int LLVMContextGetErrorCount(LLVMContext* ctx) {
    return ctx ? ctx->error_count : 0;
}

CadenaSegura LLVMContextGetError(LLVMContext* ctx) {
    CadenaSegura cs;
    cs.longitud = ctx ? (int)strlen(ctx->error_msg) : 0;
    cs.datos = ctx ? ctx->error_msg : "(null)";
    return cs;
}

LLVMModule* LLVMModuleCreateWithName(CadenaSegura nombre, LLVMContext* ctx) {
    LLVMModule* mod = (LLVMModule*)calloc(1, sizeof(LLVMModule));
    mod->ctx = ctx;
    if (nombre.datos) {
        strncpy(mod->nombre, nombre.datos, sizeof(mod->nombre) - 1);
    }
    return mod;
}

void LLVMModuleDispose(LLVMModule* mod) {
    if (!mod) return;
    if (mod->ir_buffer) free(mod->ir_buffer);
    free(mod);
}

CadenaSegura LLVMModuleGetIR(LLVMModule* mod) {
    CadenaSegura cs;
    cs.longitud = mod ? mod->ir_len : 0;
    cs.datos = mod ? mod->ir_buffer : "";
    return cs;
}

int LLVMModuleGetIRLength(LLVMModule* mod) {
    return mod ? mod->ir_len : 0;
}

void LLVMModuleEmitHeader(LLVMModule* mod) {
    _mod_append(mod, "; ModuleID = '%s'\n", mod->nombre);
    _mod_append(mod, "source_filename = \"%s\"\n", mod->nombre);
    _mod_append(mod, "target datalayout = \"e-m:w-i666-32-n32\"\n");
    _mod_append(mod, "target triple = \"unknown-pc-win32\"\n\n");
}

void LLVMModuleEmitRuntimeDecls(LLVMModule* mod) {
    _mod_append(mod, "; === Runtime declarations ===\n");
    _mod_append(mod, "declare void @escribir_linea(i32)\n");
    _mod_append(mod, "\n");
}

LLVMBuilder* LLVMBuilderCreate(LLVMContext* ctx) {
    (void)ctx;
    LLVMBuilder* b = (LLVMBuilder*)calloc(1, sizeof(LLVMBuilder));
    return b;
}

void LLVMBuilderDispose(LLVMBuilder* b) {
    if (b) free(b);
}

void LLVMBuilderSetModule(LLVMBuilder* b, LLVMModule* mod) {
    b->mod = mod;
}

void LLVMBuilderBeginFunction(LLVMBuilder* b, CadenaSegura nombre,
    int tipo_retorno, int param_count) {
    (void)tipo_retorno;
    (void)param_count;
    strncpy(b->nombre_func_actual, nombre.datos, sizeof(b->nombre_func_actual) - 1);
    b->indent = 1;
    _mod_append(b->mod, "define i32 @%s(i32* %%params) {\n", nombre.datos);
    b->indent = 2;
    _mod_append(b->mod, "entry:\n");
}

void LLVMBuilderEndFunction(LLVMBuilder* b) {
    _mod_append(b->mod, "}\n\n");
}

void LLVMBuilderCreateEntryBlock(LLVMBuilder* b) {
    _mod_append(b->mod, "entry:\n");
}

void LLVMBuilderCreateRetConst(LLVMBuilder* b, int val) {
    _builder_indent(b);
    _mod_append(b->mod, "ret i32 %d\n", val);
}

void LLVMBuilderEmitLabel(LLVMBuilder* b, CadenaSegura nombre) {
    _mod_append(b->mod, "%s:\n", nombre.datos);
}

void LLVMBuilderCreateBr(LLVMBuilder* b, CadenaSegura destino) {
    _builder_indent(b);
    _mod_append(b->mod, "br label %%%s\n", destino.datos);
}

void LLVMBuilderCreateCondBr(LLVMBuilder* b, CadenaSegura cond,
    CadenaSegura etiqueta_true, CadenaSegura etiqueta_false) {
    _builder_indent(b);
    _mod_append(b->mod, "br i1 %s, label %%%s, label %%%s\n",
        cond.datos, etiqueta_true.datos, etiqueta_false.datos);
}

// --- Constructores de alto nivel ---

CadenaSegura BuildMinimalProgram(LLVMContext* ctx, CadenaSegura nombre_modulo,
    int valor_retorno) {
    (void)ctx;
    BufDinamico b;
    _buf_init(&b);
    const char* name = nombre_modulo.datos ? nombre_modulo.datos : "main";
    _buf_append(&b, "; ModuleID = '%s'\n", name);
    _buf_append(&b, "source_filename = \"%s\"\n", name);
    _buf_append(&b, "target datalayout = \"e-m:w-i666-32-n32\"\n");
    _buf_append(&b, "target triple = \"unknown-pc-win32\"\n\n");
    _buf_append(&b, "define i32 @main() {\n");
    _buf_append(&b, "entry:\n");
    _buf_append(&b, "  ret i32 %d\n", valor_retorno);
    _buf_append(&b, "}\n");
    CadenaSegura result;
    result.longitud = b.len;
    result.datos = b.buf;
    return result;
}

CadenaSegura BuildArithmeticProgram(LLVMContext* ctx, CadenaSegura nombre_modulo,
    int op, int lhs, int rhs) {
    BufDinamico b;
    _buf_init(&b);
    const char* name = nombre_modulo.datos ? nombre_modulo.datos : "main";
    _buf_append(&b, "; ModuleID = '%s'\n", name);
    _buf_append(&b, "source_filename = \"%s\"\n", name);
    _buf_append(&b, "define i32 @main() {\n");
    _buf_append(&b, "entry:\n");
    const char* opcode = "add";
    if (op == 1) opcode = "sub";
    else if (op == 2) opcode = "mul";
    else if (op == 3) opcode = "sdiv";
    else if (op == 4) opcode = "udiv";
    else if (op == 5) opcode = "srem";
    _buf_append(&b, "  %lhs = add i32 %d, 0\n", lhs);
    _buf_append(&b, "  %rhs = add i32 %d, 0\n", rhs);
    _buf_append(&b, "  %%res = %s i32 %%lhs, %%rhs\n", opcode);
    _buf_append(&b, "  ret i32 %%res\n");
    _buf_append(&b, "}\n");
    (void)ctx;
    CadenaSegura result;
    result.longitud = b.len;
    result.datos = b.buf;
    return result;
}

CadenaSegura BuildIfElseProgram(LLVMContext* ctx, CadenaSegura nombre_modulo,
    int a, int b) {
    BufDinamico buf;
    _buf_init(&buf);
    const char* name = nombre_modulo.datos ? nombre_modulo.datos : "main";
    _buf_append(&buf, "; ModuleID = '%s'\n", name);
    _buf_append(&buf, "source_filename = \"%s\"\n", name);
    _buf_append(&buf, "define i32 @main() {\n");
    _buf_append(&buf, "entry:\n");
    _buf_append(&buf, "  %%cmp = icmp slt i32 %d, %d\n", a, b);
    _buf_append(&buf, "  br i1 %%cmp, label %%then, label %%else\n");
    _buf_append(&buf, "then:\n");
    _buf_append(&buf, "  ret i32 1\n");
    _buf_append(&buf, "else:\n");
    _buf_append(&buf, "  ret i32 0\n");
    _buf_append(&buf, "}\n");
    (void)ctx;
    CadenaSegura result;
    result.longitud = buf.len;
    result.datos = buf.buf;
    return result;
}

CadenaSegura BuildLoopProgram(LLVMContext* ctx, CadenaSegura nombre_modulo,
    int n) {
    BufDinamico buf;
    _buf_init(&buf);
    const char* name = nombre_modulo.datos ? nombre_modulo.datos : "main";
    _buf_append(&buf, "; ModuleID = '%s'\n", name);
    _buf_append(&buf, "define i32 @main() {\n");
    _buf_append(&buf, "entry:\n");
    _buf_append(&buf, "  %%n = add i32 %d, 0\n", n);
    _buf_append(&buf, "  %%acc = add i32 0, 0\n");
    _buf_append(&buf, "  br label %%loop\n");
    _buf_append(&buf, "loop:\n");
    _buf_append(&buf, "  %%i = phi i32 [0, %%entry], [%%next_i, %%loop]\n", n);
    _buf_append(&buf, "  %%done = icmp sge i32 %%i, %%n\n");
    _buf_append(&buf, "  br i1 %%done, label %%end, label %%body\n");
    _buf_append(&buf, "body:\n");
    _buf_append(&buf, "  %%acc_next = add i32 %%acc, %%i\n");
    _buf_append(&buf, "  %%next_i = add i32 %%i, 1\n");
    _buf_append(&buf, "  br label %%loop\n");
    _buf_append(&buf, "end:\n");
    _buf_append(&buf, "  ret i32 %%i\n");
    _buf_append(&buf, "}\n");
    (void)ctx;
    CadenaSegura result;
    result.longitud = buf.len;
    result.datos = buf.buf;
    return result;
}

CadenaSegura BuildCallProgram(LLVMContext* ctx, CadenaSegura nombre_modulo,
    int valor) {
    BufDinamico buf;
    _buf_init(&buf);
    const char* name = nombre_modulo.datos ? nombre_modulo.datos : "main";
    _buf_append(&buf, "; ModuleID = '%s'\n", name);
    _buf_append(&buf, "source_filename = \"%s\"\n", name);
    _buf_append(&buf, "define i32 @suma(i32 %%a, i32 %%b) {\n");
    _buf_append(&buf, "entry:\n");
    _buf_append(&buf, "  %%r = add i32 %%a, %%b\n");
    _buf_append(&buf, "  ret i32 %%r\n");
    _buf_append(&buf, "}\n\n");
    _buf_append(&buf, "define i32 @main() {\n");
    _buf_append(&buf, "entry:\n");
    _buf_append(&buf, "  %%call = call i32 @suma(i32 %d, i32 0)\n", valor);
    _buf_append(&buf, "  ret i32 %%call\n");
    _buf_append(&buf, "}\n");
    (void)ctx;
    CadenaSegura result;
    result.longitud = buf.len;
    result.datos = buf.buf;
    return result;
}
