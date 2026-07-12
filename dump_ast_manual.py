import sys
sys.path.insert(0, '.')
from lexer import Lexer
from parser import Parser
from diagnostics import DiagnosticManager

src = open('tests/estres_concurrencia.syn', encoding='utf-8').read()
lineas = src.splitlines()
diag = DiagnosticManager(idioma='es', fuente_lineas=lineas)
lex = Lexer(src)
tokens = lex.tokenizar()
p = Parser(tokens, diag)
prog = p.parsear()

def dump(nodo, nivel=0):
    pad = '  ' * nivel
    nombre = type(nodo).__name__
    if hasattr(nodo, '__dataclass_fields__'):
        print(pad + nombre + ':')
        for campo in nodo.__dataclass_fields__:
            val = getattr(nodo, campo)
            if isinstance(val, list):
                if val:
                    print(pad + '  [' + campo + ']:')
                    for item in val:
                        if hasattr(item, '__dataclass_fields__'):
                            dump(item, nivel+2)
                        else:
                            print(pad + '    ' + repr(item))
                else:
                    print(pad + '  [' + campo + ']: []')
            elif hasattr(val, '__dataclass_fields__'):
                print(pad + '  ' + campo + ':')
                dump(val, nivel+2)
            else:
                print(pad + '  ' + campo + ' = ' + repr(val))
    else:
        print(pad + repr(nodo))

for stmt in prog.sentencias:
    dump(stmt)
    print()
