// cumple Manual 1 §5: backend WASM
// cumple Manual 8 §4.2: target WASM
// =============================================================================
// synapse_wasm.c — WebAssembly WAT text emitter (M12.1.2)
//
// Genera WAT de texto (.wat) sin dependencias externas (sin emcc/wasm-ld).
// Implementa la API declarada en synapse_wasm.h / std/wasm.syn.
//
// Referencias: Manual 1 §5 ("Traduce AST a C, LLVM IR o WAT"), §6 (Backend WASM)
// =============================================================================
#include "synapse_wasm.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

// --- Buffer dinámico ---
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

static void _mod_append(WasmModule* mod, const char* fmt, ...) {
    if (mod->wat_len + 512 >= mod->wat_cap) {
        mod->wat_cap = (mod->wat_cap == 0) ? 4096 : mod->wat_cap * 2;
        mod->wat_buffer = (char*)realloc(mod->wat_buffer, mod->wat_cap);
    }
    va_list ap;
    va_start(ap, fmt);
    mod->wat_len += vsnprintf(mod->wat_buffer + mod->wat_len,
        mod->wat_cap - mod->wat_len, fmt, ap);
    va_end(ap);
}

static void _builder_indent(WasmBuilder* b) {
    for (int i = 0; i < b->indent; i++)
        _mod_append(b->mod, "  ");
}

// --- Module ---

WasmModule* WasmModuleCreate(CadenaSegura nombre) {
    WasmModule* mod = (WasmModule*)calloc(1, sizeof(WasmModule));
    if (nombre.datos)
        strncpy(mod->nombre, nombre.datos, sizeof(mod->nombre) - 1);
    return mod;
}

void WasmModuleDispose(WasmModule* mod) {
    if (!mod) return;
    if (mod->wat_buffer) free(mod->wat_buffer);
    free(mod);
}

CadenaSegura WasmModuleGetWAT(WasmModule* mod) {
    CadenaSegura cs;
    cs.longitud = mod ? mod->wat_len : 0;
    cs.datos = mod ? mod->wat_buffer : "";
    return cs;
}

int WasmModuleGetWATLength(WasmModule* mod) {
    return mod ? mod->wat_len : 0;
}

void WasmModuleEmitHeader(WasmModule* mod) {
    _mod_append(mod, "(module\n");
}

void WasmModuleEmitRuntimeDecls(WasmModule* mod) {
    _mod_append(mod, "  ;; runtime declarations\n");
}

// --- Builder ---

WasmBuilder* WasmBuilderCreate(WasmModule* mod) {
    WasmBuilder* b = (WasmBuilder*)calloc(1, sizeof(WasmBuilder));
    b->mod = mod;
    b->indent = 1;
    return b;
}

void WasmBuilderDispose(WasmBuilder* b) {
    if (b) free(b);
}

void WasmBuilderBeginFunction(WasmBuilder* b, CadenaSegura nombre,
    int num_params, int num_results) {
    _builder_indent(b);
    _mod_append(b->mod, "(func $%s", nombre.datos);
    for (int i = 0; i < num_params; i++)
        _mod_append(b->mod, " (param i32)");
    for (int i = 0; i < num_results; i++)
        _mod_append(b->mod, " (result i32)");
    _mod_append(b->mod, "\n");
    b->indent = 2;
}

void WasmBuilderEndFunction(WasmBuilder* b) {
    _mod_append(b->mod, "  )\n");
}

// --- Instrucciones ---

void WasmEmitI32Const(WasmBuilder* b, int val) {
    _builder_indent(b);
    _mod_append(b->mod, "i32.const %d\n", val);
}

void WasmEmitI32Add(WasmBuilder* b) {
    _builder_indent(b);
    _mod_append(b->mod, "i32.add\n");
}

void WasmEmitI32Sub(WasmBuilder* b) {
    _builder_indent(b);
    _mod_append(b->mod, "i32.sub\n");
}

void WasmEmitI32Mul(WasmBuilder* b) {
    _builder_indent(b);
    _mod_append(b->mod, "i32.mul\n");
}

void WasmEmitI32DivS(WasmBuilder* b) {
    _builder_indent(b);
    _mod_append(b->mod, "i32.div_s\n");
}

void WasmEmitReturn(WasmBuilder* b) {
    _builder_indent(b);
    _mod_append(b->mod, "return\n");
}

void WasmEmitCall(WasmBuilder* b, CadenaSegura nombre) {
    _builder_indent(b);
    _mod_append(b->mod, "call $%s\n", nombre.datos);
}

void WasmEmitLocalGet(WasmBuilder* b, CadenaSegura nombre) {
    _builder_indent(b);
    _mod_append(b->mod, "local.get $%s\n", nombre.datos);
}

void WasmEmitLocalSet(WasmBuilder* b, CadenaSegura nombre) {
    _builder_indent(b);
    _mod_append(b->mod, "local.set $%s\n", nombre.datos);
}

void WasmEmitLocalDecl(WasmBuilder* b, CadenaSegura nombre) {
    _builder_indent(b);
    _mod_append(b->mod, "(local $%s i32)\n", nombre.datos);
}

void WasmEmitIf(WasmBuilder* b) {
    _builder_indent(b);
    _mod_append(b->mod, "if\n");
}

void WasmEmitElse(WasmBuilder* b) {
    _builder_indent(b);
    _mod_append(b->mod, "else\n");
}

void WasmEmitEnd(WasmBuilder* b) {
    _builder_indent(b);
    _mod_append(b->mod, "end\n");
}

void WasmEmitBrIf(WasmBuilder* b, CadenaSegura etiqueta) {
    _builder_indent(b);
    _mod_append(b->mod, "br_if $%s\n", etiqueta.datos);
}

void WasmEmitBr(WasmBuilder* b, CadenaSegura etiqueta) {
    _builder_indent(b);
    _mod_append(b->mod, "br $%s\n", etiqueta.datos);
}

void WasmEmitDrop(WasmBuilder* b) {
    _builder_indent(b);
    _mod_append(b->mod, "drop\n");
}

// --- Comparaciones ---

void WasmEmitI32Eq(WasmBuilder* b) {
    _builder_indent(b);
    _mod_append(b->mod, "i32.eq\n");
}

void WasmEmitI32Ne(WasmBuilder* b) {
    _builder_indent(b);
    _mod_append(b->mod, "i32.ne\n");
}

void WasmEmitI32LtS(WasmBuilder* b) {
    _builder_indent(b);
    _mod_append(b->mod, "i32.lt_s\n");
}

void WasmEmitI32GtS(WasmBuilder* b) {
    _builder_indent(b);
    _mod_append(b->mod, "i32.gt_s\n");
}

// --- Constructores de alto nivel ---

CadenaSegura WasmBuildMinimalProgram(CadenaSegura nombre_modulo,
    int valor_retorno) {
    BufDinamico b;
    _buf_init(&b);
    _buf_append(&b, "; Module: %s\n", nombre_modulo.datos ? nombre_modulo.datos : "wasm");
    _buf_append(&b, "(module\n");
    _buf_append(&b, "  (func $main (result i32)\n");
    _buf_append(&b, "    i32.const %d\n", valor_retorno);
    _buf_append(&b, "    return\n");
    _buf_append(&b, "  )\n");
    _buf_append(&b, ")\n");
    CadenaSegura result;
    result.longitud = b.len;
    result.datos = b.buf;
    return result;
}

CadenaSegura WasmBuildArithmeticProgram(CadenaSegura nombre_modulo,
    int op, int lhs, int rhs) {
    BufDinamico b;
    _buf_init(&b);
    const char* instr = "i32.add";
    if (op == 1) instr = "i32.sub";
    else if (op == 2) instr = "i32.mul";
    else if (op == 3) instr = "i32.div_s";
    _buf_append(&b, "; Module: %s\n", nombre_modulo.datos ? nombre_modulo.datos : "wasm");
    _buf_append(&b, "(module\n");
    _buf_append(&b, "  (func $main (result i32)\n");
    _buf_append(&b, "    i32.const %d\n", lhs);
    _buf_append(&b, "    i32.const %d\n", rhs);
    _buf_append(&b, "    %s\n", instr);
    _buf_append(&b, "    return\n");
    _buf_append(&b, "  )\n");
    _buf_append(&b, ")\n");
    CadenaSegura result;
    result.longitud = b.len;
    result.datos = b.buf;
    return result;
}

CadenaSegura WasmBuildIfElseProgram(CadenaSegura nombre_modulo,
    int a, int b) {
    BufDinamico buf;
    _buf_init(&buf);
    _buf_append(&buf, "; Module: %s\n", nombre_modulo.datos ? nombre_modulo.datos : "wasm");
    _buf_append(&buf, "(module\n");
    _buf_append(&buf, "  (func $main (result i32)\n");
    _buf_append(&buf, "    i32.const %d\n", a);
    _buf_append(&buf, "    i32.const %d\n", b);
    _buf_append(&buf, "    i32.lt_s\n");
    _buf_append(&buf, "    if\n");
    _buf_append(&buf, "      i32.const 1\n");
    _buf_append(&buf, "    else\n");
    _buf_append(&buf, "      i32.const 0\n");
    _buf_append(&buf, "    end\n");
    _buf_append(&buf, "    return\n");
    _buf_append(&buf, "  )\n");
    _buf_append(&buf, ")\n");
    CadenaSegura result;
    result.longitud = buf.len;
    result.datos = buf.buf;
    return result;
}

CadenaSegura WasmBuildCallProgram(CadenaSegura nombre_modulo,
    int a, int b) {
    BufDinamico buf;
    _buf_init(&buf);
    _buf_append(&buf, "; Module: %s\n", nombre_modulo.datos ? nombre_modulo.datos : "wasm");
    _buf_append(&buf, "(module\n");
    _buf_append(&buf, "  (func $suma (param i32) (param i32) (result i32)\n");
    _buf_append(&buf, "    local.get $p0\n");
    _buf_append(&buf, "    local.get $p1\n");
    _buf_append(&buf, "    i32.add\n");
    _buf_append(&buf, "    return\n");
    _buf_append(&buf, "  )\n");
    _buf_append(&buf, "  (func $main (result i32)\n");
    _buf_append(&buf, "    i32.const %d\n", a);
    _buf_append(&buf, "    i32.const %d\n", b);
    _buf_append(&buf, "    call $suma\n");
    _buf_append(&buf, "    return\n");
    _buf_append(&buf, "  )\n");
    _buf_append(&buf, ")\n");
    CadenaSegura result;
    result.longitud = buf.len;
    result.datos = buf.buf;
    return result;
}
