"""
Emisión de código C para operaciones tensoriales.
Contiene los emisores de builtins de tensor: suma, producto, relu, etc.
"""

from .context import GeneratorContext
from compilador.ast_nodes import DefinicionFuncion


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
