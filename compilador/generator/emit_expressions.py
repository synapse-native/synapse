"""
Generación de código C para expresiones y tipos.
Contiene expr_a_c, tipo_de_expr, builtin emitters, log, formato.
"""

from typing import Optional
from compilador.ast_nodes import (
    Nodo, Identificador, LiteralNumero, LiteralDecimal, LiteralCadena,
    LiteralBooleano, OpBinaria, OpUnaria, LlamadaFuncion,
    ExprAccesoCampo, ExprTensor, ExprIndice, ArgumentoTransferido,
    ExprObtenerDireccion, ExprDereferencia, ExprAsm,
    ExprCrearCanal, ExprRecibirCanal, AsignacionVariable,
    DeclaracionVariable, SentenciaEnviarCanal,
    LogLlamada, BloqueInseguro, DefinicionFuncion,
    SentenciaRetornar, SentenciaLanzar, SentenciaRecuperar,
    SentenciaEscuchar, AsignacionCampo,
    StmtConstante, DeclaracionExterna, ImportarC, NodoCoincidir,
)
from .context import GeneratorContext


# ================================================================
# Type inference
# ================================================================

def tipo_de_expr(ctx: GeneratorContext, nodo: Optional[Nodo]) -> str:
    """Infiere el tipo C de una expresión Synapse."""
    if nodo is None:
        return 'void'

    if isinstance(nodo, LiteralNumero):
        return 'int'
    if isinstance(nodo, LiteralDecimal):
        return 'float'
    if isinstance(nodo, LiteralCadena):
        return 'CadenaSegura'
    if isinstance(nodo, LiteralBooleano):
        return 'int'

    if isinstance(nodo, Identificador):
        nombre = nodo.nombre
        if nombre in ctx._variables:
            return ctx._variables[nombre]
        if nombre in ctx._const_types:
            return ctx._const_types[nombre]
        # Builtin lookup
        if nombre in ctx._BUILTINS:
            return ctx.traducir_tipo_c(ctx._BUILTINS[nombre])
        if nombre in ctx._func_return_types:
            return ctx.traducir_tipo_c(ctx._func_return_types[nombre])
        return 'int'

    if isinstance(nodo, ExprTensor):
        return 'Tensor'
    if isinstance(nodo, ExprCrearCanal):
        return 'CanalConcurrencia*'
    if isinstance(nodo, ExprRecibirCanal):
        return 'void*'

    if isinstance(nodo, ExprAccesoCampo):
        obj_tipo = tipo_de_expr(ctx, nodo.objeto).rstrip('*')
        if obj_tipo.startswith('struct '):
            nombre_struct = obj_tipo[7:]
            info = ctx._estructuras.get(nombre_struct)
            if info:
                for c_nombre, c_tipo in info.get('campos', []):
                    if c_nombre == nodo.nombre_campo:
                        es_pointer_field = (
                            c_nombre in info.get('campos_pointer', set())
                        )
                        base_tipo = ctx.traducir_tipo_c(c_tipo)
                        if es_pointer_field:
                            return f"{base_tipo}*"
                        return base_tipo
        return 'int'

    if isinstance(nodo, OpBinaria):
        # Operadores lógicos retornan int
        op_val = getattr(nodo, 'operador', None)
        if op_val in ('y', 'o', 'no', '==', '!=', '<', '>', '<=', '>='):
            return 'int'
        izq_tipo = tipo_de_expr(ctx, nodo.izquierdo)
        der_tipo = tipo_de_expr(ctx, nodo.derecho)
        if izq_tipo == 'float' or der_tipo == 'float':
            return 'float'
        return izq_tipo

    if isinstance(nodo, OpUnaria):
        return tipo_de_expr(ctx, nodo.expr)

    if isinstance(nodo, LlamadaFuncion):
        nombre = nodo.nombre
        if nombre in ctx._BUILTINS:
            return ctx.traducir_tipo_c(ctx._BUILTINS[nombre])
        if nombre in ctx._func_return_types:
            return ctx.traducir_tipo_c(ctx._func_return_types[nombre])
        # Struct constructor call: ResultadoEtapa() -> struct ResultadoEtapa
        if nombre in ctx._estructuras:
            return f"struct {nombre}"
        return 'int'

    if isinstance(nodo, ExprIndice):
        obj_tipo = tipo_de_expr(ctx, nodo.expr)
        if obj_tipo == 'Tensor':
            return 'float'
        return 'int'

    if isinstance(nodo, ExprObtenerDireccion):
        base_tipo = tipo_de_expr(ctx, nodo.expr)
        return f"{base_tipo}*"

    if isinstance(nodo, ExprDereferencia):
        base_tipo = tipo_de_expr(ctx, nodo.expr)
        if base_tipo.endswith('*'):
            return base_tipo[:-1]
        return base_tipo

    if isinstance(nodo, ArgumentoTransferido):
        return tipo_de_expr(ctx, nodo.expr)

    if isinstance(nodo, ExprAsm):
        return 'void'

    return 'int'


# ================================================================
# Expression → C code
# ================================================================

def expr_a_c(ctx: GeneratorContext, nodo: Optional[Nodo]) -> str:
    """Traduce un nodo expresión a código C."""
    if nodo is None:
        return ""

    if isinstance(nodo, LiteralNumero):
        return str(nodo.valor)

    if isinstance(nodo, LiteralDecimal):
        return f"{nodo.valor}f"

    if isinstance(nodo, LiteralBooleano):
        return "1" if nodo.valor else "0"

    if isinstance(nodo, LiteralCadena):
        # Escapar la cadena y crear CadenaSegura literal
        val = nodo.valor.replace('\\', '\\\\').replace('"', '\\"')
        return (
            f"(CadenaSegura){{ .longitud = (int)strlen(\"{val}\"),"
            f" .datos = \"{val}\" }}"
        )

    if isinstance(nodo, Identificador):
        nombre = nodo.nombre
        if ctx._func_param_types and nombre in ctx._externas:
            return nombre
        return nombre

    if isinstance(nodo, OpBinaria):
        izq = expr_a_c(ctx, nodo.izquierdo)
        der = expr_a_c(ctx, nodo.derecho)
        op_map = {
            '+': '+', '-': '-', '*': '*', '/': '/', '%': '%',
            'y': '&&', 'o': '||',
            '==': '==', '!=': '!=', '<': '<', '>': '>',
            '<=': '<=', '>=': '>=',
        }
        op = getattr(nodo, 'operador', '+')
        c_op = op_map.get(op, op)
        return f"({izq} {c_op} {der})"

    if isinstance(nodo, OpUnaria):
        expr = expr_a_c(ctx, nodo.expr)
        op_map = {'-': '-', 'no': '!', '!': '!'}
        op = getattr(nodo, 'operador', '-')
        c_op = op_map.get(op, op)
        return f"({c_op}{expr})"

    if isinstance(nodo, LlamadaFuncion):
        args = []
        if nodo.argumentos:
            for a in nodo.argumentos:
                args.append(expr_a_c(ctx, a))
        tipo = tipo_de_expr(ctx, nodo)
        nombre = nodo.nombre
        args_str = ", ".join(args)

        # Coercion for functions expecting CadenaSegura
        if nombre in ctx._FUNCIONES_ESPERAN_TEXTO:
            return f"{nombre}({args_str})"

        # Check if we need .datos for C function calls
        if nombre in ctx._C_FUNCTIONS_NEED_DATOS:
            expected_types = ctx._C_FUNCTIONS_NEED_DATOS[nombre]
            adjusted = []
            for i, a in enumerate(args):
                if i < len(expected_types) and expected_types[i] == 'char*':
                    adjusted.append(f"{a}.datos")
                else:
                    adjusted.append(a)
            return f"{nombre}({', '.join(adjusted)})"

        return f"{nombre}({args_str})"

    if isinstance(nodo, ExprAccesoCampo):
        obj = expr_a_c(ctx, nodo.objeto)
        obj_tipo = tipo_de_expr(ctx, nodo.objeto)
        es_puntero = obj_tipo.endswith('*')
        sep = '->' if es_puntero else '.'
        nombre_struct = ''
        if not es_puntero and obj_tipo.startswith('struct '):
            nombre_struct = obj_tipo[7:]
        es_adt = bool(ctx._estructuras.get(nombre_struct, {}).get('es_adt'))
        if es_adt and nodo.nombre_campo != 'tag':
            return f"{obj}{sep}dato.{nodo.nombre_campo}"
        return f"{obj}{sep}{nodo.nombre_campo}"

    if isinstance(nodo, ExprTensor):
        filas = expr_a_c(ctx, nodo.filas)
        cols = expr_a_c(ctx, nodo.columnas)
        return f"crear_tensor({filas}, {cols})"

    if isinstance(nodo, ExprIndice):
        obj = expr_a_c(ctx, nodo.expr)
        idx = expr_a_c(ctx, nodo.indice)
        return f"{obj}.datos[{idx}]"

    if isinstance(nodo, ExprObtenerDireccion):
        return f"&({expr_a_c(ctx, nodo.expr)})"

    if isinstance(nodo, ExprDereferencia):
        return f"*({expr_a_c(ctx, nodo.expr)})"

    if isinstance(nodo, ArgumentoTransferido):
        return expr_a_c(ctx, nodo.expr)

    if isinstance(nodo, ExprAsm):
        return nodo.instruccion

    if isinstance(nodo, ExprCrearCanal):
        cap = expr_a_c(ctx, nodo.capacidad) if nodo.capacidad else "10"
        return f"canal_crear({cap})"

    if isinstance(nodo, ExprRecibirCanal):
        canal = expr_a_c(ctx, nodo.expr_canal) if hasattr(nodo, 'expr_canal') else "NULL"
        return f"canal_recibir({canal})"

    return "0"


# ================================================================
# Log
# ================================================================

def visitar_log(ctx: GeneratorContext, nodo: LogLlamada):
    """Genera código C para log()."""
    partes = []
    for a in nodo.argumentos:
        tipo_a = tipo_de_expr(ctx, a)
        if tipo_a == 'CadenaSegura':
            partes.append(f"{expr_a_c(ctx, a)}.datos")
        elif tipo_a == 'float':
            partes.append(expr_a_c(ctx, a))
        else:
            partes.append(expr_a_c(ctx, a))
    fmt_parts = []
    arg_parts = []
    for a in nodo.argumentos:
        tipo_a = tipo_de_expr(ctx, a)
        if tipo_a == 'CadenaSegura':
            fmt_parts.append("%s")
            arg_parts.append(f"{expr_a_c(ctx, a)}.datos")
        elif tipo_a == 'float':
            fmt_parts.append("%f")
            arg_parts.append(expr_a_c(ctx, a))
        elif tipo_a == 'int':
            fmt_parts.append("%d")
            arg_parts.append(expr_a_c(ctx, a))
        else:
            fmt_parts.append("%p")
            arg_parts.append(expr_a_c(ctx, a))
    fmt_str = " ".join(fmt_parts)
    args_str = ", ".join(arg_parts)
    if args_str:
        ctx.write_line(f'printf("{fmt_str}\\\n", {args_str});')
    else:
        ctx.write_line(f'printf("{fmt_str}\\\n");')


def formato_espec(ctx: GeneratorContext, tipo: str) -> str:
    """Retorna el especificador de formato printf para un tipo C."""
    if tipo == 'CadenaSegura':
        return "%.*s"
    if tipo == 'float':
        return "%f"
    if tipo == 'int':
        return "%d"
    return "%p"


# ================================================================
# Builtin function C code emitters
# ================================================================

def emitir_reserva(ctx: GeneratorContext, nodo: DefinicionFuncion):
    ctx.write_line("Tensor reserva(int tamano) {")
    ctx.inc_indent()
    ctx.write_line("Tensor _bloque;")
    ctx.write_line("_bloque.filas = tamano;")
    ctx.write_line("_bloque.columnas = 1;")
    ctx.write_line(f"_bloque.datos = {ctx.syn_pool_alloc('tamano')};")
    ctx.write_line("return _bloque;")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")

def emitir_libera(ctx: GeneratorContext, nodo: DefinicionFuncion):
    ctx.write_line("void libera(Tensor bloque) {")
    ctx.inc_indent()
    ctx.write_line("if (bloque.datos) {")
    ctx.inc_indent()
    ctx.write_line(f"{ctx.syn_pool_free('bloque.datos')};")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")

def emitir_abrir(ctx: GeneratorContext, nodo: DefinicionFuncion):
    ctx.write_line("Canal abrir(CadenaSegura ruta, CadenaSegura modo) {")
    ctx.inc_indent()
    ctx.write_line("Canal _c = {0};")
    ctx.write_line("_c.es_virtual = 0;")
    for lib in ['ast_nodes', 'lexer', 'parser', 'generator']:
        ctx.write_line(
            f'if (strcmp(ruta.datos, "librerias/compiler/{lib}.syn") == 0) {{'
        )
        ctx.inc_indent()
        ctx.write_line(f'_c.es_virtual = 1; _c.virtual_data = LIB_{lib.upper()};')
        ctx.write_line(f'_c.virtual_len = (int)strlen(LIB_{lib.upper()});')
        ctx.write_line("_c.es_valido = 1; return _c;")
        ctx.dec_indent()
        ctx.write_line("}")
    for lib in ['io', 'mem', 'math', 'fs', 'sys']:
        ctx.write_line(
            f'if (strcmp(ruta.datos, "librerias/std/{lib}.syn") == 0) {{'
        )
        ctx.inc_indent()
        ctx.write_line(f'_c.es_virtual = 1; _c.virtual_data = LIB_{lib.upper()};')
        ctx.write_line(f'_c.virtual_len = (int)strlen(LIB_{lib.upper()});')
        ctx.write_line("_c.es_valido = 1; return _c;")
        ctx.dec_indent()
        ctx.write_line("}")
    ctx.write_line("_c.stream = fopen(ruta.datos, modo.datos);")
    ctx.write_line("_c.es_valido = (_c.stream != NULL) ? 1 : 0;")
    ctx.write_line("if (!_c.es_valido) {")
    ctx.inc_indent()
    ctx.write_line('fprintf(stderr, "Error: No se pudo abrir el archivo\\\\n");')
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("return _c;")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")

def emitir_leer(ctx: GeneratorContext, nodo: DefinicionFuncion):
    ctx.write_line("CadenaSegura leer(Canal canal) {")
    ctx.inc_indent()
    ctx.write_line('if (!canal.es_valido) { return (CadenaSegura){0,""}; }')
    ctx.write_line("if (canal.es_virtual) {")
    ctx.inc_indent()
    ctx.write_line("char* _buf = (char*)malloc(canal.virtual_len + 1);")
    ctx.write_line('if (!_buf) { return (CadenaSegura){0,""}; }')
    ctx.write_line("memcpy(_buf, canal.virtual_data, canal.virtual_len);")
    ctx.write_line("_buf[canal.virtual_len] = 0;")
    ctx.write_line("return (CadenaSegura){canal.virtual_len, _buf};")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("fseek(canal.stream, 0, SEEK_END);")
    ctx.write_line("long _tam = ftell(canal.stream);")
    ctx.write_line("rewind(canal.stream);")
    ctx.write_line("char* _buf = (char*)malloc(_tam + 1);")
    ctx.write_line('if (!_buf) { return (CadenaSegura){0,""}; }')
    ctx.write_line("size_t _leido = fread(_buf, 1, _tam, canal.stream);")
    ctx.write_line("_buf[_leido] = 0;")
    ctx.write_line("return (CadenaSegura){(int)_leido, _buf};")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")

def emitir_escribir(ctx: GeneratorContext, nodo: DefinicionFuncion):
    ctx.write_line("void escribir(CadenaSegura contenido) {")
    ctx.inc_indent()
    ctx.write_line("fwrite(contenido.datos, 1, contenido.longitud, stdout);")
    ctx.write_line("fflush(stdout);")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")

def emitir_escribir_linea(ctx: GeneratorContext, nodo: DefinicionFuncion):
    ctx.write_line("void escribir_linea(CadenaSegura contenido) {")
    ctx.inc_indent()
    ctx.write_line("fwrite(contenido.datos, 1, contenido.longitud, stdout);")
    ctx.write_line('fwrite("\\n", 1, 1, stdout);')
    ctx.write_line("fflush(stdout);")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")

def emitir_leer_linea(ctx: GeneratorContext, nodo: DefinicionFuncion):
    ctx.write_line("CadenaSegura leer_linea() {")
    ctx.inc_indent()
    ctx.write_line("char _buf[4096];")
    ctx.write_line("if (fgets(_buf, 4096, stdin)) {")
    ctx.inc_indent()
    ctx.write_line("int _len = (int)strlen(_buf);")
    ctx.write_line("if (_len > 0 && _buf[_len-1] == '\\n') { _buf[_len-1]=0; _len--; }")
    ctx.write_line("char* _dup = (char*)malloc(_len + 1);")
    ctx.write_line('if (!_dup) { return (CadenaSegura){0,""}; }')
    ctx.write_line("memcpy(_dup, _buf, _len + 1);")
    ctx.write_line("return (CadenaSegura){_len, _dup};")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line('return (CadenaSegura){0,""};')
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")

def emitir_cerrar(ctx: GeneratorContext, nodo: DefinicionFuncion):
    ctx.write_line("void cerrar(Canal canal) {")
    ctx.inc_indent()
    ctx.write_line("if (canal.es_virtual) return;")
    ctx.write_line("if (canal.stream) fclose(canal.stream);")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")

def emitir_suma(ctx: GeneratorContext, nodo: DefinicionFuncion):
    ctx.write_line("Tensor suma(Tensor a, Tensor b) {")
    ctx.inc_indent()
    ctx.write_line("if (a.filas != b.filas || a.columnas != b.columnas) {")
    ctx.inc_indent()
    ctx.write_line('fprintf(stderr, "Error: Dimensiones incompatibles\\\\n");')
    ctx.write_line("return (Tensor){0,0,NULL};")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("Tensor r; r.filas = a.filas; r.columnas = a.columnas;")
    ctx.write_line(f"r.datos = {ctx.syn_pool_alloc('r.filas*r.columnas*sizeof(float)')};")
    ctx.write_line("for (int _i=0; _i<r.filas*r.columnas; _i++)")
    ctx.write_line("    r.datos[_i] = a.datos[_i] + b.datos[_i];")
    ctx.write_line(f"{ctx.syn_pool_free('a.datos')};")
    ctx.write_line(f"{ctx.syn_pool_free('b.datos')};")
    ctx.write_line("return r;")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")

def emitir_producto(ctx: GeneratorContext, nodo: DefinicionFuncion):
    ctx.write_line("Tensor producto(Tensor a, Tensor b) {")
    ctx.inc_indent()
    ctx.write_line("if (a.columnas != b.filas) {")
    ctx.inc_indent()
    ctx.write_line('fprintf(stderr, "Error: Dimensiones incompatibles\\\\n");')
    ctx.write_line("return (Tensor){0,0,NULL};")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("Tensor r; r.filas=a.filas; r.columnas=b.columnas;")
    _calloc = ctx.syn_calloc('r.filas*r.columnas', 'sizeof(float)')
    ctx.write_line(f"r.datos = (float*){_calloc};")
    ctx.write_line("for(int _i=0;_i<r.filas;_i++) for(int _j=0;_j<r.columnas;_j++){")
    ctx.write_line("float _sum=0;")
    ctx.write_line("for(int _k=0;_k<a.columnas;_k++)")
    ctx.write_line("    _sum+=a.datos[_i*a.columnas+_k]*b.datos[_k*b.columnas+_j];")
    ctx.write_line("r.datos[_i*r.columnas+_j]=_sum;}")
    ctx.write_line(f"{ctx.syn_pool_free('a.datos')}; {ctx.syn_pool_free('b.datos')};")
    ctx.write_line("return r;")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")

def emitir_relu(ctx: GeneratorContext, nodo: DefinicionFuncion):
    ctx.write_line("Tensor relu(Tensor a) {")
    ctx.inc_indent()
    ctx.write_line("Tensor r; r.filas=a.filas; r.columnas=a.columnas;")
    ctx.write_line(f"r.datos={ctx.syn_pool_alloc('a.filas*a.columnas*sizeof(float)')};")
    ctx.write_line("for(int _i=0;_i<a.filas*a.columnas;_i++)")
    ctx.write_line("    r.datos[_i]=(a.datos[_i]>0)?a.datos[_i]:0.0f;")
    ctx.write_line(f"{ctx.syn_pool_free('a.datos')};")
    ctx.write_line("return r;")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")

def emitir_crear_tensor(ctx: GeneratorContext, nodo: DefinicionFuncion):
    ctx.write_line("Tensor crear_tensor(int filas, int columnas) {")
    ctx.inc_indent()
    ctx.write_line("Tensor r; r.filas=filas; r.columnas=columnas;")
    ctx.write_line(f"r.datos={ctx.syn_pool_alloc('filas*columnas*sizeof(float)')};")
    ctx.write_line("memset(r.datos,0,filas*columnas*sizeof(float));")
    ctx.write_line("return r;")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")

def emitir_suma_tensor(ctx: GeneratorContext, nodo: DefinicionFuncion):
    ctx.write_line("Tensor suma_tensor(Tensor a, Tensor b) {")
    ctx.inc_indent()
    ctx.write_line("if (a.filas!=b.filas||a.columnas!=b.columnas){")
    ctx.inc_indent()
    ctx.write_line('fprintf(stderr,"Error: Dimensiones\\\\n");')
    ctx.write_line("return (Tensor){0,0,NULL};")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("Tensor r; r.filas=a.filas; r.columnas=a.columnas;")
    ctx.write_line(f"r.datos={ctx.syn_pool_alloc('r.filas*r.columnas*sizeof(float)')};")
    ctx.write_line("for(int _i=0;_i<r.filas*r.columnas;_i++)")
    ctx.write_line("    r.datos[_i]=a.datos[_i]+b.datos[_i];")
    ctx.write_line(f"{ctx.syn_pool_free('a.datos')}; {ctx.syn_pool_free('b.datos')};")
    ctx.write_line("return r;")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")

def emitir_producto_punto(ctx: GeneratorContext, nodo: DefinicionFuncion):
    ctx.write_line("Tensor producto_punto(Tensor a, Tensor b) {")
    ctx.inc_indent()
    ctx.write_line("if (a.columnas!=b.filas){")
    ctx.inc_indent()
    ctx.write_line('fprintf(stderr,"Error: Dimensiones\\\\n");')
    ctx.write_line("return (Tensor){0,0,NULL};")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("Tensor r; r.filas=a.filas; r.columnas=b.columnas;")
    _calloc = ctx.syn_calloc('r.filas*r.columnas', 'sizeof(float)')
    ctx.write_line(f"r.datos=(float*){_calloc};")
    ctx.write_line("for(int _i=0;_i<r.filas;_i++)for(int _j=0;_j<r.columnas;_j++){")
    ctx.write_line("float _sum=0;")
    ctx.write_line("for(int _k=0;_k<a.columnas;_k++)")
    ctx.write_line("    _sum+=a.datos[_i*a.columnas+_k]*b.datos[_k*b.columnas+_j];")
    ctx.write_line("r.datos[_i*r.columnas+_j]=_sum;}")
    ctx.write_line(f"{ctx.syn_pool_free('a.datos')};{ctx.syn_pool_free('b.datos')};")
    ctx.write_line("return r;")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")

def emitir_tokenizar(ctx: GeneratorContext, nodo: DefinicionFuncion):
    ctx.write_line("int tokenizar(CadenaSegura fuente) {")
    ctx.inc_indent()
    ctx.write_line("int _i=0, _linea=1, _columna=1, _token_count=0;")
    ctx.write_line("while (_i < fuente.longitud) {")
    ctx.inc_indent()
    ctx.write_line("char _c = fuente.datos[_i];")
    ctx.write_line("if (_c==' '||_c=='\\t'){_i++;_columna++;continue;}")
    ctx.write_line("if (_c=='\\r'){_i++;continue;}")
    ctx.write_line("if (_c=='\\n'){_i++;_linea++;_columna=1;continue;}")
    ctx.write_line("if (_c=='/'&&_i+1<fuente.longitud&&fuente.datos[_i+1]=='/'){")
    ctx.inc_indent()
    ctx.write_line("while(_i<fuente.longitud&&fuente.datos[_i]!='\\n')_i++;continue;")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line(
        "if(_c=='\\\"'||_c=='\\''){char _q=_c;int _st=_i;_i++;_columna++;"
        "while(_i<fuente.longitud&&fuente.datos[_i]!=_q)"
        "{_i++;_columna++;}"
        "if(_i>=fuente.longitud){fprintf(stderr,\"  TOKEN STRING_UNCLOSED"
        " L%d:%d\\n\",_linea,_columna);break;}"
        "_i++;_columna++;_token_count++;"
        "fprintf(stderr,\"  TOKEN STRING L%d:%d\\n\",_linea,_columna);}"
    )
    ctx.write_line(
        "else if(_c>='0'&&_c<='9'){int _st=_i;"
        "while(_i<fuente.longitud&&fuente.datos[_i]>='0'&&"
        "fuente.datos[_i]<='9')_i++;"
        "_columna+=_i-_st;_token_count++;"
        "fprintf(stderr,\"  TOKEN NUMBER L%d:%d\\n\",_linea,_columna);}"
    )
    ctx.write_line(
        "else if((_c>='a'&&_c<='z')||(_c>='A'&&_c<='Z')||_c=='_'){"
        "int _st=_i;"
        "while(_i<fuente.longitud&&((fuente.datos[_i]>='a'&&"
        "fuente.datos[_i]<='z')||(fuente.datos[_i]>='A'&&"
        "fuente.datos[_i]<='Z')||(fuente.datos[_i]>='0'&&"
        "fuente.datos[_i]<='9')||fuente.datos[_i]=='_'))_i++;"
        "_columna+=_i-_st;_token_count++;"
        "fprintf(stderr,\"  TOKEN IDENTIFIER L%d:%d\\n\",_linea,_columna);}"
    )
    ctx.write_line(
        "else{_i++;_columna++;_token_count++;"
        "fprintf(stderr,\"  TOKEN CHAR(%c)L%d:%d\\n\",_c,_linea,_columna);}"
    )
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("fprintf(stderr,\"  TOKENS: %d\\n\",_token_count);")
    ctx.write_line("return _token_count;")
    ctx.dec_indent()
    ctx.write_line("}")
    ctx.write_line("")

def emitir_token_defs(ctx: GeneratorContext):
    """Emite las definiciones de tokens del generador embebido."""
    if ctx._gen_defs_emitido:
        return
    ctx._gen_defs_emitido = True
    ctx.write_line("// --- Token IDs ---")
    tokens = [
        ("T_IF",1),("T_ELSE",2),("T_FUNC",3),("T_RET",4),
        ("T_SPAWN",5),("T_RECOVER",6),("T_LISTEN",7),("T_WHILE",8),
        ("T_IMPORT",9),("T_BREAK",10),("T_CONTINUE",11),("T_DOT",12),
        ("T_IDENT",13),("T_NUM",14),("T_STR",15),("T_GT",16),
        ("T_LT",17),("T_EQ",18),("T_NE",19),("T_LE",20),("T_GE",21),
        ("T_ASSIGN",22),("T_PLUS",23),("T_MINUS",24),("T_MUL",25),
        ("T_DIV",26),("T_MOD",27),("T_ARROW",28),("T_LPAREN",29),
        ("T_RPAREN",30),("T_COLON",31),("T_COMMA",32),("T_NL",33),
        ("T_INDENT",34),("T_DEDENT",35),("T_EOF",36),("T_STRUCT",37),
        ("T_AND",38),("T_OR",39),("T_NOT",40),("T_TRUE",41),
        ("T_FALSE",42),("T_INSEGURO",43),("T_IMPORTAR_C",44),
        ("T_AMPERSAND",45),("T_EXTERNO",46),
    ]
    for name, val in tokens:
        ctx.write_line(f"#define {name} {val}")
    ctx.write_line("")
    ctx.write_line("#define MAX_TOKS 16384")
    ctx.write_line(
        "typedef struct { int tipo; int linea; int col; "
        "char val[256]; } _P_Token;"
    )
    ctx.write_line("_P_Token _P_tks[MAX_TOKS];")
    ctx.write_line("int _P_ntks = 0, _P_tpos = 0, _P_p_err = 0;")
    ctx.write_line("")
