"""
test_toml_raii.py — Verifica que el generador inyecte destructores RAII
para NodoToml y que el pipeline Synapse→C→ejecutable funcione correctamente.
"""
import os, sys, subprocess, tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from compilador.ast_nodes import (
    Programa, Parametro,
    DefinicionFuncion, DefinicionEstructura,
    AsignacionVariable, SentenciaExpr, LogLlamada,
    LlamadaFuncion, Identificador, LiteralCadena, LiteralNumero,
    OpBinaria, ExprAccesoCampo, SentenciaSi, SentenciaRetornar,
    ExprCrearCanal, SentenciaEnviarCanal, ExprRecibirCanal,
    DeclaracionExterna,
)
from compilador.generator import GeneradorC

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SYNAPSE_RT_C = os.path.join(PROJECT_ROOT, 'synapse_rt.c')


def build_toml_ast() -> Programa:
    """Construye un programa Synapse que usa std.toml y verifica RAII."""

    def cs(name: str) -> str:
        return name

    def lit_str(v: str):
        return LiteralCadena(valor=v)

    def ident(n: str):
        return Identificador(nombre=n)

    def call(nombre: str, *args):
        return LlamadaFuncion(nombre=nombre, argumentos=list(args))

    def acceso(objeto, campo: str):
        return ExprAccesoCampo(objeto=objeto, nombre_campo=campo)

    def cmp_op(izq, op: str, der):
        return OpBinaria(izquierdo=izq, operador=op, derecho=der)

    def var_asig(nombre: str, expr):
        return AsignacionVariable(nombre=nombre, expresion=expr)

    def log(*args):
        return LogLlamada(argumentos=list(args))

    def si(cond, cuerpo, sino=None):
        return SentenciaSi(condicion=cond, cuerpo=cuerpo, cuerpo_sino=sino or [])

    def retorno(expr=None):
        return SentenciaRetornar(expr=expr)

    def expr_stmt(expr):
        return SentenciaExpr(expr=expr)

    # --- Struct definitions (same as std/toml.syn) ---
    struct_par = DefinicionEstructura(
        nombre='ParToml',
        campos=[
            Parametro(nombre='clave', tipo='texto'),
            Parametro(nombre='valor', tipo='NodoToml'),
        ]
    )
    struct_nodo = DefinicionEstructura(
        nombre='NodoToml',
        campos=[
            Parametro(nombre='tipo', tipo='entero'),
            Parametro(nombre='valor_str', tipo='texto'),
            Parametro(nombre='pares', tipo='ParToml'),
            Parametro(nombre='longitud', tipo='entero'),
        ]
    )

    # --- Extern declarations ---
    extern_parse = DeclaracionExterna(
        nombre='_toml_parse',
        parametros=[Parametro(nombre='entrada', tipo='texto')],
        tipo_retorno='NodoToml'
    )
    extern_liberar = DeclaracionExterna(
        nombre='_toml_nodo_liberar',
        parametros=[Parametro(nombre='n', tipo='NodoToml')],
        tipo_retorno='nulo'
    )
    extern_get = DeclaracionExterna(
        nombre='_toml_object_get',
        parametros=[
            Parametro(nombre='nodo', tipo='NodoToml'),
            Parametro(nombre='clave', tipo='texto'),
        ],
        tipo_retorno='NodoToml'
    )

    # --- desde_texto wrapper ---
    func_desde_texto = DefinicionFuncion(
        nombre='desde_texto',
        parametros=[Parametro(nombre='entrada', tipo='cadena')],
        tipo_retorno='NodoToml',
        cuerpo=[
            retorno(call('_toml_parse', ident('entrada')))
        ]
    )

    # --- obtener_campo wrapper ---
    func_obtener_campo = DefinicionFuncion(
        nombre='obtener_campo',
        parametros=[
            Parametro(nombre='nodo', tipo='NodoToml'),
            Parametro(nombre='clave', tipo='cadena'),
        ],
        tipo_retorno='NodoToml',
        cuerpo=[
            retorno(call('_toml_object_get', ident('nodo'), ident('clave')))
        ]
    )

    # --- principal: test RAII ---
    # El test crea un arbol TOML, extrae valores y termina.
    # RAII debe liberar todo automaticamente.
    cuerpo_principal = []

    # doc = desde_texto(...)
    cuerpo_principal.append(var_asig('doc', call('desde_texto', lit_str(
        '[proyecto]\n'
        'nombre = "Synapse"\n'
        'version = "1.5.0"\n'
        'punto_entrada = "src/main.syn"\n'
    ))))

    # seccion = obtener_campo(doc, "proyecto")
    cuerpo_principal.append(var_asig('seccion',
        call('obtener_campo', ident('doc'), lit_str('proyecto'))))

    # nom = obtener_campo(seccion, "nombre")
    cuerpo_principal.append(var_asig('nom',
        call('obtener_campo', ident('seccion'), lit_str('nombre'))))

    # si nom.tipo == 2: log("OK")
    cuerpo_principal.append(si(
        cmp_op(acceso(ident('nom'), 'tipo'), '==', LiteralNumero(valor=2)),
        [log(lit_str("campo nombre OK"))],
        [log(lit_str("FALLO campo nombre"))],
    ))

    # pe = obtener_campo(seccion, "punto_entrada")
    cuerpo_principal.append(var_asig('pe',
        call('obtener_campo', ident('seccion'), lit_str('punto_entrada'))))

    # si pe.tipo == 2: log("punto_entrada OK")
    cuerpo_principal.append(si(
        cmp_op(acceso(ident('pe'), 'tipo'), '==', LiteralNumero(valor=2)),
        [log(lit_str("punto_entrada OK"))],
        [log(lit_str("FALLO punto_entrada"))],
    ))

    # Campo faltante
    cuerpo_principal.append(var_asig('faltante',
        call('obtener_campo', ident('seccion'), lit_str('no_existe'))))
    cuerpo_principal.append(si(
        cmp_op(acceso(ident('faltante'), 'tipo'), '==', LiteralNumero(valor=0)),
        [log(lit_str("campo faltante devuelve Nulo OK"))],
        [log(lit_str("FALLO campo faltante"))],
    ))

    # No se llama liberar_nodo - RAII debe hacerlo automaticamente
    cuerpo_principal.append(log(lit_str("FIN RAII OK")))

    func_principal = DefinicionFuncion(
        nombre='principal',
        parametros=[],
        tipo_retorno='nulo',
        cuerpo=cuerpo_principal
    )

    return Programa(sentencias=[
        struct_par, struct_nodo,
        extern_parse, extern_liberar, extern_get,
        func_desde_texto, func_obtener_campo,
        func_principal,
    ])


def test_raii_destructors_in_c_output():
    """Verifica que el C generado contenga llamadas a _toml_nodo_liberar."""
    prog = build_toml_ast()
    gen = GeneradorC(prog)
    c_code = gen.generar()

    # Verificar registros RAII
    assert 'NodoToml' in gen._destructor_map, "NodoToml debe estar en destructor_map"
    assert gen._destructor_map['NodoToml'] == '_toml_nodo_liberar', \
        "Destructor de NodoToml debe ser _toml_nodo_liberar"

    # Verificar que el C generado contenga _toml_nodo_liberar (RAII)
    # El generador emite destructores al final de la funcion principal
    # para todas las variables registradas (doc, seccion, nom, pe, faltante)
    count = c_code.count('_toml_nodo_liberar')
    print(f"Llamadas a _toml_nodo_liberar en C generado: {count}")
    assert count >= 3, (
        f"RAII debe emitir al menos 3 destructores, pero solo encontro {count}"
    )
    print("RAII: destructores inyectados correctamente")

    # Verificar que NO haya llamadas manuales a liberar_nodo
    assert 'liberar_nodo' not in c_code, \
        "No debe haber llamadas manuales a liberar_nodo() - RAII debe ser automatico"

    print("RAII: no hay llamadas manuales a liberar - correcto")


def test_toml_compile_and_run():
    """Compila y ejecuta el C generado para verificar funcionamiento."""
    prog = build_toml_ast()
    gen = GeneradorC(prog)
    c_code = gen.generar()

    # Escribir C generado a archivo temporal
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.c', delete=False, dir=PROJECT_ROOT
    ) as f:
        f.write(c_code)
        tmp_c = f.name

    try:
        exe_path = tmp_c.replace('.c', '.exe')

        # Compilar
        compile_cmd = [
            'gcc', '-Wall', '-Wextra', '-O0',
            tmp_c, SYNAPSE_RT_C,
            '-o', exe_path,
            '-lpthread', '-lws2_32'
        ]
        result = subprocess.run(
            compile_cmd, capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            print("STDERR:", result.stderr)
            print("STDOUT:", result.stdout)
            raise RuntimeError(
                f"Compilacion fallo con codigo {result.returncode}\n"
                f"{result.stderr}"
            )

        # Ejecutar
        run_result = subprocess.run(
            [exe_path], capture_output=True, text=True, timeout=10
        )
        output = run_result.stdout
        print("Salida del programa:\n" + output)

        assert 'FALLO' not in output, "Alguna asercion fallo en el test"
        assert 'FIN RAII OK' in output, "El programa no llego al final"
        print("RAII: programa compilo y ejecuto correctamente")

    finally:
        # Limpiar
        if os.path.exists(tmp_c):
            os.remove(tmp_c)
        if 'exe_path' in locals() and os.path.exists(exe_path):
            os.remove(exe_path)


if __name__ == '__main__':
    print("=== Test RAII: Verificacion de Destructores en C generado ===")
    test_raii_destructors_in_c_output()
    print()
    print("=== Test RAII: Compilacion y ejecucion ===")
    test_toml_compile_and_run()
    print()
    print("=== TODOS LOS TESTS RAII PASARON ===")
