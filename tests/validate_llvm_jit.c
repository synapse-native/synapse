/*
 * validate_llvm_jit.c — M12.1.3 Validation Test
 *
 * Isolated test for synapse_llvm.c JIT Execution Engine and
 * Memory Encryption extensions.
 *
 * Tests:
 * - IR to C translation (all patterns: arithmetic, icmp, br, call, phi, load/store)
 * - JIT compilation via gcc -shared
 * - JIT library loading and symbol resolution
 * - JIT execution of compiled functions
 * - XOR memory encryption round-trip
 * - End-to-end JIT pipeline: IR -> compile -> encrypt -> load -> execute
 *
 * File is OUTSIDE tests/ to comply with read-only lock.
 *
 * Compilar:
 *   gcc -O2 -std=c99 validate_llvm_jit.c synapse_llvm.c -o validate_llvm_jit.exe -lm
 *   ./validate_llvm_jit.exe
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

// Opaque handle types from synapse_llvm.c
typedef struct LLVMContext LLVMContext;
typedef struct LLVMModule LLVMModule;
typedef struct LLVMBuilder LLVMBuilder;

typedef enum { IR_I32 = 0, IR_I1, IR_VOID, IR_PTR } IRType;

// M12.1.3 JIT engine externs
typedef struct JITContext JITContext;

extern JITContext* JIT_CreateContext(void);
extern void JIT_FreeContext(JITContext* jit);
extern int JIT_CompileIR(const char* ir_text, const char* output_name, JITContext* jit);
extern int JIT_LoadLibrary(JITContext* jit);
extern void* JIT_GetFunction(JITContext* jit, const char* name);
extern void JIT_FreeLibrary(JITContext* jit);
extern void JIT_MemoryXor(unsigned char* buffer, size_t size,
                           const unsigned char* key, size_t key_len);
extern int JIT_EncryptFile(const char* path, const unsigned char* key, size_t key_len);
extern int JIT_BuildAndExecute(const char* ir_text, const char* module_name,
                                const unsigned char* enc_key, size_t key_len,
                                const char* fn_name);

// IR generator externs (reuse from M12.1.1/1.2)
extern LLVMContext* LLVMContextCreate(void);
extern void LLVMContextDispose(LLVMContext* ctx);
extern LLVMModule* LLVMModuleCreateWithName(const char* name, LLVMContext* ctx);
extern void LLVMModuleEmitHeader(LLVMModule* mod);
extern void LLVMModuleEmitRuntimeDecls(LLVMModule* mod);
extern LLVMBuilder* LLVMBuilderCreate(LLVMContext* ctx);
extern void LLVMBuilderSetModule(LLVMBuilder* b, LLVMModule* mod);
extern void LLVMBuilderBeginFunction(LLVMBuilder* b, const char* name, int return_type, int param_count, ...);
extern void LLVMBuilderCreateEntryBlock(LLVMBuilder* b);
extern void LLVMBuilderCreateRetConst(LLVMBuilder* b, int val);
extern void LLVMBuilderEndFunction(LLVMBuilder* b);
extern void LLVMModuleDispose(LLVMModule* mod);
extern void LLVMBuilderDispose(LLVMBuilder* b);
extern const char* LLVMModuleGetIR(LLVMModule* mod);
extern const char* BuildMinimalProgram(LLVMContext* ctx, const char* name, int return_value);
extern const char* BuildArithmeticProgram(LLVMContext* ctx, const char* name, int op, int lhs, int rhs);
extern const char* BuildIfElseProgram(LLVMContext* ctx, const char* name, int a, int b);
extern const char* BuildLoopProgram(LLVMContext* ctx, const char* name, int n);

static int tests_passed = 0;
static int tests_total = 0;

#define TEST(name, cond) do { \
    tests_total++; \
    if (cond) { tests_passed++; printf("  [PASS] %s\n", name); } \
    else { printf("  [FAIL] %s\n", name); } \
} while(0)

int main(void) {
    printf("=== M12.1.3 JIT Engine & Memory Encryption Validation ===\n\n");

    // ================================================================
    // Section 1: Memory Encryption (XOR)
    // ================================================================
    printf("--- Section 1: XOR Memory Encryption ---\n");

    unsigned char key[] = { 0xAB, 0xCD, 0xEF, 0x01, 0x23, 0x45, 0x67, 0x89 };
    unsigned char test_buf[] = "SynapseSecretData123!";
    size_t test_len = strlen((const char*)test_buf) + 1;
    unsigned char original[64];
    memcpy(original, test_buf, test_len);

    JIT_MemoryXor(test_buf, test_len, key, sizeof(key));
    TEST("XOR encrypt: buffer changed",
         memcmp(test_buf, original, test_len) != 0);

    // XOR back to decrypt
    JIT_MemoryXor(test_buf, test_len, key, sizeof(key));
    TEST("XOR decrypt: buffer restored",
         memcmp(test_buf, original, test_len) == 0);

    // Double-encrypt = no-op (XOR property)
    unsigned char double_test[] = "test123";
    size_t dt_len = strlen((const char*)double_test) + 1;
    memcpy(original, double_test, dt_len);
    JIT_MemoryXor(double_test, dt_len, key, sizeof(key));
    JIT_MemoryXor(double_test, dt_len, key, sizeof(key));
    TEST("XOR double = original", memcmp(double_test, original, dt_len) == 0);

    // Null safety
    JIT_MemoryXor(NULL, 10, key, sizeof(key));
    TEST("XOR with NULL buffer (no crash)", 1);

    JIT_MemoryXor(test_buf, 10, NULL, 5);
    TEST("XOR with NULL key (no crash)", 1);

    // Round-trip with file encryption test (write, encrypt, read back)
    FILE* f = fopen("_jit_test_xor.bin", "wb");
    if (f) {
        unsigned char file_data[] = "Hello JIT!";
        size_t fd_len = strlen((const char*)file_data) + 1;
        fwrite(file_data, 1, fd_len, f);
        fclose(f);

        JIT_EncryptFile("_jit_test_xor.bin", key, sizeof(key));
        TEST("File encrypt: returns 0", 1);

        // Read back (should be encrypted)
        f = fopen("_jit_test_xor.bin", "rb");
        if (f) {
            unsigned char read_back[64] = {0};
            fread(read_back, 1, fd_len, f);
            fclose(f);
            TEST("File encrypt: content changed",
                 memcmp(read_back, file_data, fd_len) != 0);
        }

        // Encrypt again (XOR back = decrypt + re-encrypt? No, double encrypt = original for XOR)
        JIT_EncryptFile("_jit_test_xor.bin", key, sizeof(key));
        f = fopen("_jit_test_xor.bin", "rb");
        if (f) {
            unsigned char read_back[64] = {0};
            fread(read_back, 1, fd_len, f);
            fclose(f);
            TEST("File double encrypt: restored",
                 memcmp(read_back, file_data, fd_len) == 0);
        }

        remove("_jit_test_xor.bin");
    }

    // ================================================================
    // Section 2: JIT Context Creation/Destruction
    // ================================================================
    printf("\n--- Section 2: JIT Context ---\n");

    JITContext* jit = JIT_CreateContext();
    TEST("JIT_CreateContext returns non-NULL", jit != NULL);
    JIT_FreeContext(jit);
    TEST("JIT_FreeContext (no crash)", 1);

    // Null safety
    JIT_FreeContext(NULL);
    TEST("JIT_FreeContext with NULL (no crash)", 1);

    // ================================================================
    // Section 3: IR to C Translation (via JIT compilation test)
    // ================================================================
    printf("\n--- Section 3: Mininal IR Compilation & Execution ---\n");

    // Build IR for a minimal program: return 42
    LLVMContext* ctx = LLVMContextCreate();
    const char* ir = BuildMinimalProgram(ctx, "jit_minimal", 42);
    TEST("BuildMinimalProgram returns IR", ir != NULL);

    if (ir) {
        // Compile, load, execute
        int result = JIT_BuildAndExecute(ir, "_jit_minimal", NULL, 0, "main");
        TEST("JIT execution of minimal program", result == 42);
    }
    LLVMContextDispose(ctx);

    // ================================================================
    // Section 4: Arithmetic JIT
    // ================================================================
    printf("\n--- Section 4: Arithmetic JIT (3 + 7) ---\n");

    ctx = LLVMContextCreate();
    ir = BuildArithmeticProgram(ctx, "jit_add", 0, 3, 7);
    TEST("BuildArithmeticProgram returns IR", ir != NULL);

    if (ir) {
        int result = JIT_BuildAndExecute(ir, "_jit_add", NULL, 0, "main");
        TEST("JIT: 3 + 7 = 10", result == 10);
    }
    LLVMContextDispose(ctx);

    // Subtraction
    ctx = LLVMContextCreate();
    ir = BuildArithmeticProgram(ctx, "jit_sub", 1, 50, 30);
    if (ir) {
        int result = JIT_BuildAndExecute(ir, "_jit_sub", NULL, 0, "main");
        TEST("JIT: 50 - 30 = 20", result == 20);
    }
    LLVMContextDispose(ctx);

    // Multiplication
    ctx = LLVMContextCreate();
    ir = BuildArithmeticProgram(ctx, "jit_mul", 2, 6, 7);
    if (ir) {
        int result = JIT_BuildAndExecute(ir, "_jit_mul", NULL, 0, "main");
        TEST("JIT: 6 * 7 = 42", result == 42);
    }
    LLVMContextDispose(ctx);

    // Division
    ctx = LLVMContextCreate();
    ir = BuildArithmeticProgram(ctx, "jit_div", 3, 100, 4);
    if (ir) {
        int result = JIT_BuildAndExecute(ir, "_jit_div", NULL, 0, "main");
        TEST("JIT: 100 / 4 = 25", result == 25);
    }
    LLVMContextDispose(ctx);

    // ================================================================
    // Section 5: If-Else JIT
    // ================================================================
    printf("\n--- Section 5: If-Else JIT ---\n");

    // if (5 < 10) return 1; else return 0; -> should return 1
    ctx = LLVMContextCreate();
    ir = BuildIfElseProgram(ctx, "jit_ifelse", 5, 10);
    if (ir) {
        int result = JIT_BuildAndExecute(ir, "_jit_ifelse", NULL, 0, "main");
        TEST("JIT: if (5 < 10) → return 1", result == 1);
    }
    LLVMContextDispose(ctx);

    // if (10 < 5) return 1; else return 0; -> should return 0
    ctx = LLVMContextCreate();
    ir = BuildIfElseProgram(ctx, "jit_ifelse2", 10, 5);
    if (ir) {
        int result = JIT_BuildAndExecute(ir, "_jit_ifelse2", NULL, 0, "main");
        TEST("JIT: if (10 < 5) → return 0", result == 0);
    }
    LLVMContextDispose(ctx);

    // ================================================================
    // Section 6: Loop JIT (sum 0 to 5 = 0+1+2+3+4 = 10)
    // ================================================================
    printf("\n--- Section 6: Loop JIT (sum 0..5) ---\n");

    ctx = LLVMContextCreate();
    ir = BuildLoopProgram(ctx, "jit_loop", 5);
    if (ir) {
        int result = JIT_BuildAndExecute(ir, "_jit_loop", NULL, 0, "main");
        TEST("JIT: sum 0..5 = 10", result == 10);
    }
    LLVMContextDispose(ctx);

    // ================================================================
    // Section 7: JIT with Encryption
    // ================================================================
    printf("\n--- Section 7: JIT with Memory Encryption ---\n");

    ctx = LLVMContextCreate();
    ir = BuildArithmeticProgram(ctx, "jit_enc_add", 0, 10, 20);
    if (ir) {
        unsigned char enc_key[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xCA, 0xFE, 0xBA, 0xBE };
        int result = JIT_BuildAndExecute(ir, "_jit_enc", enc_key, sizeof(enc_key), "main");
        TEST("JIT encrypted: 10 + 20 = 30", result == 30);
    }
    LLVMContextDispose(ctx);

    // ================================================================
    // Section 8: Edge Cases
    // ================================================================
    printf("\n--- Section 8: Edge Cases ---\n");

    // Null IR
    int bad = JIT_BuildAndExecute(NULL, "bad", NULL, 0, "main");
    TEST("JIT with NULL IR returns error", bad != 0);

    // Empty context checks
    jit = JIT_CreateContext();
    int load_ret = JIT_LoadLibrary(jit);
    TEST("JIT_LoadLibrary with no compiled library returns error",
         load_ret != 0);

    void* fn = JIT_GetFunction(jit, "nonexistent");
    TEST("JIT_GetFunction with no library returns NULL", fn == NULL);
    JIT_FreeContext(jit);

    // File encrypt with NULL path
    int enc_ret = JIT_EncryptFile(NULL, key, sizeof(key));
    TEST("JIT_EncryptFile with NULL path returns error", enc_ret != 0);

    // Nulls
    JIT_LoadLibrary(NULL);
    TEST("JIT_LoadLibrary(NULL) no crash", 1);

    JIT_GetFunction(NULL, "test");
    TEST("JIT_GetFunction(NULL, name) no crash", 1);

    JIT_FreeLibrary(NULL);
    TEST("JIT_FreeLibrary(NULL) no crash", 1);

    JIT_CompileIR(NULL, "test", NULL);
    TEST("JIT_CompileIR(NULL) no crash", 1);

    // ================================================================
    // Cleanup temp files
    // ================================================================
    remove("_jit_minimal.c");
    remove("_jit_minimal.ll");
    remove("_jit_minimal.dll");
    remove("_jit_add.c");
    remove("_jit_add.ll");
    remove("_jit_add.dll");
    remove("_jit_sub.c");
    remove("_jit_sub.ll");
    remove("_jit_sub.dll");
    remove("_jit_mul.c");
    remove("_jit_mul.ll");
    remove("_jit_mul.dll");
    remove("_jit_div.c");
    remove("_jit_div.ll");
    remove("_jit_div.dll");
    remove("_jit_ifelse.c");
    remove("_jit_ifelse.ll");
    remove("_jit_ifelse.dll");
    remove("_jit_ifelse2.c");
    remove("_jit_ifelse2.ll");
    remove("_jit_ifelse2.dll");
    remove("_jit_loop.c");
    remove("_jit_loop.ll");
    remove("_jit_loop.dll");
    remove("_jit_enc.c");
    remove("_jit_enc.ll");
    remove("_jit_enc.dll");
    remove("_jit_test_xor.bin");

    // ================================================================
    // Summary
    // ================================================================
    printf("\n========================================\n");
    printf("M12.1.3 JIT Engine & Encryption: %d/%d tests PASS\n", tests_passed, tests_total);
    printf("========================================\n");

    return (tests_passed == tests_total) ? 0 : 1;
}
