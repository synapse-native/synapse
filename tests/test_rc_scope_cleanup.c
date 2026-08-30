// TDD — D-1.2 (Manual 4 §5.2; Manual 4 §3.2; Manual 4 §3.3; Manual 2 §4.3):
// emisión nativa del decremento rc/arc al cierre de scope.
// Verifica que el decremento de refcount a 0 (el código que el codegen nativo
// emite en gen_cerrar_bloque_c para vars de clase rc/arc) dispara el destructor
// exactamente 1 vez por instancia al "salir de scope".
#include <stdio.h>
#include <stdlib.h>

extern void* _syn_rc_crear(void* data, void (*dtor)(void*));
extern void  _syn_rc_decrement(void* p);
extern void* _syn_arc_crear(void* data, void (*dtor)(void*));
extern void  _syn_arc_decrement(void* p);

static int g_dtor = 0;
static void dtor(void* d) { g_dtor++; free(d); }

int main(void) {
    // --- scope 1: una var rc, decremento al cierre ---
    {
        int* p = (int*)malloc(sizeof(int));
        void* rc = _syn_rc_crear(p, dtor);
        _syn_rc_decrement(rc);   // <= lo que emite gen_cerrar_bloque_c (clase rc)
    }
    if (g_dtor != 1) { printf("RC_SCOPE_FAIL dtor=%d\n", g_dtor); return 1; }

    // --- scopes anidados: 2 vars rc, decremento en cada cierre ---
    {
        int* a = (int*)malloc(sizeof(int)); void* r1 = _syn_rc_crear(a, dtor);
        {
            int* b = (int*)malloc(sizeof(int)); void* r2 = _syn_rc_crear(b, dtor);
            _syn_rc_decrement(r2);   // cierre de scope interno
        }
        _syn_rc_decrement(r1);       // cierre de scope externo
    }
    if (g_dtor != 3) { printf("RC_SCOPE_FAIL dtor=%d\n", g_dtor); return 1; }

    // --- arc: decremento fuerte a 0 dispara destructor 1 vez ---
    {
        int* q = (int*)malloc(sizeof(int)); void* arc = _syn_arc_crear(q, dtor);
        _syn_arc_decrement(arc);
    }
    if (g_dtor != 4) { printf("RC_SCOPE_FAIL dtor=%d\n", g_dtor); return 1; }

    printf("RC_SCOPE_OK\n");
    return 0;
}
