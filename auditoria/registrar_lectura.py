#!/usr/bin/env python3
# ============================================================================
# registrar_lectura.py — Gate de lectura previa de manuales (regla 1)
# ============================================================================
# Mecaniza la regla "antes de codificar, LEE el manual correspondiente":
#
#   1. docs/mapa_manuales.md mapea rutas de producción -> secciones exigidas.
#   2. El agente registra su lectura con --registrar (cita + puntos clave);
#      el script valida que las secciones citadas EXISTEN en los manuales
#      (anti-fabricación) antes de aceptar el registro.
#   3. --verificar (invocado por scripts/githooks/pre-commit) bloquea el
#      commit si hay archivos productivos modificados sin lectura registrada
#      HOY, o si un archivo modificado no está mapeado.
#
# Registro: auditoria/lecturas.jsonl (una entrada JSON por línea).
# Sin dependencias externas (stdlib only).
# ============================================================================

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MAPA_MD = RAIZ / "docs" / "mapa_manuales.md"
MANUALES_DIR = RAIZ / "docs" / "manuales"
LECTURAS_JSONL = RAIZ / "auditoria" / "lecturas.jsonl"

# Rutas exentas: no son código de producción especificado por manuales.
EXCLUIDOS = (
    "tests/*", "docs/*", "auditoria/*", "scripts/*", "benchmarks/*",
    "examples/*", "vscode-synapse/*", ".github/*", ".kilo/*",
)

RE_MANUAL = re.compile(r"manual\s*(\d+)", re.IGNORECASE)
RE_SECCION = re.compile(r"\u00a7\s*(\d+(?:\.\d+)?)")


def sin_acentos(s):
    reemplazos = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
                  "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U"}
    for k, v in reemplazos.items():
        s = s.replace(k, v)
    return s


def cargar_mapa():
    """Extrae el bloque ```json del mapa y retorna dict patrón->[citas]."""
    texto = MAPA_MD.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"```json\s*\n(.*?)\n```", texto, flags=re.DOTALL)
    if not m:
        raise SystemExit(f"[FALTA] bloque ```json en {MAPA_MD}")
    mapa = json.loads(m.group(1))
    if not isinstance(mapa, dict) or not mapa:
        raise SystemExit("[FALTA] mapa vacío o con formato inválido")
    return mapa


def es_produccion(ruta):
    r = ruta.replace("\\", "/")
    if r.startswith("./"):
        r = r[2:]
    for pat in EXCLUIDOS:
        if fnmatch.fnmatch(r, pat):
            return False
    ext = Path(r).suffix.lower()
    return ext in (".syn", ".syq", ".c", ".h", ".py")


def archivos_cambiados():
    """Archivos modificados/agregados vs HEAD (tracked + untracked)."""
    out = set()
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain"], cwd=str(RAIZ),
            capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace")
        for linea in res.stdout.splitlines():
            if len(linea) < 4:
                continue
            estado, ruta = linea[:2], linea[3:].strip()
            if estado.startswith("D"):
                continue  # borrados no requieren lectura
            if " -> " in ruta:
                ruta = ruta.split(" -> ", 1)[1]
            out.add(ruta.replace("\\", "/"))
    except Exception as e:  # noqa: BLE001 - gate defensivo
        raise SystemExit(f"[FALTA] git status falló: {e}")
    return sorted(out)


def resolver_requisitos(cambiados, mapa):
    """Retorna ({ruta: [citas]}, pendientes_mapeo). Primera coincidencia gana."""
    reqs = {}
    sin_mapa = []
    for ruta in cambiados:
        if not es_produccion(ruta):
            continue
        asignado = None
        for patron, citas in mapa.items():
            if fnmatch.fnmatch(ruta, patron):
                asignado = citas
                break
        if asignado is None:
            sin_mapa.append(ruta)
        else:
            reqs[ruta] = list(asignado)
    return reqs, sin_mapa


def parsear_cita(cita):
    """'Manual 6 §1.3; Manual 3 §11.2' -> [('6', ['1.3']), ('3', ['11.2'])].

    Una mención 'Manual X' sin §N se retorna con lista vacía (= manual entero).
    """
    resultado = []
    trozos = [t.strip() for t in cita.split(";") if t.strip()]
    for trozo in trozos:
        mm = RE_MANUAL.search(trozo)
        if not mm:
            raise ValueError(f"cita sin 'Manual N': {trozo!r}")
        num = mm.group(1)
        secciones = RE_SECCION.findall(trozo)
        resultado.append((num, secciones))
    return resultado


def validar_cita(cita):
    """Valida formato y existencia real de manuales/secciones citadas.

    Retorna lista de errores (vacía si la cita es legítima).
    """
    errores = []
    try:
        pares = parsear_cita(cita)
    except ValueError as e:
        return [str(e)]
    for num, secciones in pares:
        path_manual = MANUALES_DIR / f"MANUAL {num}.md"
        if not path_manual.exists():
            errores.append(f"manual inexistente: MANUAL {num}.md")
            continue
        if not secciones:
            continue
        texto = path_manual.read_text(encoding="utf-8", errors="replace")
        encabezados = set()
        for linea in texto.splitlines():
            mh = re.match(r"^#{2,4}\s*(\d+(?:\.\d+)?)[\.\:\s]", linea)
            if mh:
                encabezados.add(mh.group(1))
        for sec in secciones:
            if sec not in encabezados:
                errores.append(
                    f"seccion fabricada: Manual {num} \u00a7{sec} no existe "
                    f"(encabezados disponibles en el manual)")
    return errores


def entradas_hoy():
    if not LECTURAS_JSONL.exists():
        return []
    hoy = date.today().isoformat()
    entradas = []
    for linea in LECTURAS_JSONL.read_text(encoding="utf-8",
                                          errors="replace").splitlines():
        linea = linea.strip()
        if not linea:
            continue
        try:
            e = json.loads(linea)
        except json.JSONDecodeError:
            print(f"[~] lecturas.jsonl: línea corrupta ignorada: {linea[:60]}")
            continue
        if e.get("fecha") == hoy:
            entradas.append(e)
    return entradas


def cobertura(reqs, entradas):
    """True si cada cita requerida está cubierta por alguna lectura de hoy.

    Semántica jerárquica: registrar §11.2 cubre el requisito §11 (leer una
    subsección implica leer su sección contenedora); registrar cualquier
    §N.N cubre el requisito del manual entero.
    """
    leidas = set()  # pares (num_manual, seccion|"" )
    for e in entradas:
        try:
            for num, secs in parsear_cita(e.get("cita", "")):
                if secs:
                    for s in secs:
                        leidas.add((num, s))
                else:
                    leidas.add((num, ""))
        except ValueError:
            continue

    def cubre(num_req, sec_req):
        for num_l, sec_l in leidas:
            if num_l != num_req:
                continue
            if sec_req == "":
                return True
            if sec_l == sec_req or sec_l.startswith(sec_req + "."):
                return True
        return False

    for ruta, citas in sorted(reqs.items()):
        for cita in citas:
            for num, secs in parsear_cita(cita):
                if secs:
                    ok = all(cubre(num, s) for s in secs)
                else:
                    ok = cubre(num, "")
                if not ok:
                    return False, ruta, cita
    return True, None, None


def cmd_registrar(args):
    errores = validar_cita(args.cita)
    if errores:
        for e in errores:
            print(f"[CITA-INVALIDA] {e}")
        print("La lectura NO fue registrada: corrige la cita contra "
              "docs/manuales/.")
        return 1
    if not args.puntos or len(args.puntos.strip()) < 20:
        print("[FALTA] --puntos debe resumir >=20 caracteres de requisitos "
              "extraidos de la seccion (evidencia de lectura real).")
        return 1
    archivos = [a.strip().replace("\\", "/")
                for a in args.archivos.split(",") if a.strip()]
    if not archivos:
        print("[FALTA] --archivos vacío")
        return 1
    entrada = {
        "fecha": date.today().isoformat(),
        "archivos": archivos,
        "cita": args.cita,
        "puntos": args.puntos.strip(),
    }
    with LECTURAS_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entrada, ensure_ascii=False) + "\n")
    print(f"[OK] lectura registrada: {args.cita} para {len(archivos)} archivo(s)")
    return 0


def cmd_verificar(_args, fallo_duro=True):
    mapa = cargar_mapa()
    cambiados = archivos_cambiados()
    reqs, sin_mapa = resolver_requisitos(cambiados, mapa)

    if sin_mapa:
        print("[FALTA] archivos productivos SIN entrada en "
              "docs/mapa_manuales.md (añade el mapeo primero):")
        for r in sin_mapa:
            print(f"  - {r}")
        return 1

    if not reqs:
        print("[OK] sin cambios de producción: gate de lectura no aplica")
        return 0

    entradas = entradas_hoy()
    ok, ruta, cita_faltante = cobertura(reqs, entradas)
    if ok:
        print(f"[OK] lectura previa verificada: {len(reqs)} archivo(s) "
              f"cubierto(s) por {len(entradas)} registro(s) de hoy")
        return 0

    print("[FALTA] lectura previa pendiente — regla 1 de gobernanza:")
    for r, citas in sorted(reqs.items()):
        print(f"  - {r} requiere: {'; '.join(citas)}")
    print("")
    print("Registra tu lectura ANTES del commit:")
    print('  python auditoria/registrar_lectura.py --registrar '
          '--archivos "<archivos>" --cita "<Manual N §S>" '
          '--puntos "<requisitos leidos>"')
    return 1 if fallo_duro else 0


def main():
    ap = argparse.ArgumentParser(
        description="Gate de lectura previa de manuales (regla 1)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--registrar", action="store_true",
                   help="registra una lectura validada")
    g.add_argument("--verificar", action="store_true",
                   help="verifica cobertura de lecturas de hoy (gate commit)")
    g.add_argument("--pendientes", action="store_true",
                   help="lista requisitos pendientes sin fallar")
    ap.add_argument("--archivos", default="",
                    help="rutas separadas por coma a las que aplica la lectura")
    ap.add_argument("--cita", default="",
                    help='cita: "Manual 6 §1.3; Manual 3 §11.2"')
    ap.add_argument("--puntos", default="",
                    help="requisitos clave extraidos (minimo 20 chars)")
    args = ap.parse_args()

    if args.registrar:
        sys.exit(cmd_registrar(args))
    if args.verificar:
        sys.exit(cmd_verificar(args, fallo_duro=True))
    sys.exit(cmd_verificar(args, fallo_duro=False))


if __name__ == "__main__":
    main()
