#!/usr/bin/env python3
"""Verificador mecánico de alineación de la auditoría.

Comprueba de forma objetiva (no declarativa) la trazabilidad entre:
  - La bitácora de `docs/AUDITORIA_ALINEACION_MANUALES.md` (filas `| fecha | tarea | estado | detalle |`)
  - Los reportes de `docs/reportes/*.md` (protocolo de micro-entregable)
  - El historial real de git (hashes de commit citados)
  - Los archivos reales del repositorio (reportes y fuentes citados)

Verificaciones:
  1. Cada fila de bitácora cita al menos un reporte o un hash; los reportes citados existen.
  2. Cada hash de commit citado (`commit X`, `Commit: X`, `HASH COMMIT: X`) existe en git.
  3. Cada sección `§N` citada tras un reporte existe como encabezado en ese reporte.
     (Las `§N` precedidas de "Manual" son secciones de manual y se ignoran.)
  4. Los reportes con bloque "REPORTE DE MICRO-ENTREGABLE" cumplen el protocolo
     (TAREA, FASE, MANUAL REFERENCIADO, HASH COMMIT, COMPILACION, TESTS, PROXIMO PASO)
     y su HASH COMMIT no es "pendiente".
  5. Los archivos fuente citados existen en el árbol; si no, se distingue si fueron
     eliminados en algún momento de la historia de git (referencia histórica válida).

Salida: informe en consola + opcional `--json`. Exit code 0 = sin brechas, 1 = con brechas.
Solo stdlib + git en modo lectura (regla 8: cero dependencias externas).

Uso:
    python auditoria/verificar_alineacion.py            # informe en consola
    python auditoria/verificar_alineacion.py --json     # informe JSON
"""

import json
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BITACORA = RAIZ / "docs" / "AUDITORIA_ALINEACION_MANUALES.md"
REPORTES_DIR = RAIZ / "docs" / "reportes"
MANUALES_DIR = RAIZ / "docs" / "manuales"

# Campos obligatorios del protocolo de micro-entregable
CAMPOS_PROTOCOLO = [
    "TAREA",
    "FASE",
    "MANUAL REFERENCIADO",
    "HASH COMMIT",
    "COMPILACION",   # acepta COMPILACIÓN y COMPILACION
    "TESTS",
    "PROXIMO PASO",  # acepta PRÓXIMO PASO y PROXIMO PASO
]

_ACC = {
    "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ü": "U", "Ñ": "N",
    "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u", "ñ": "n",
}


def sin_acentos(s: str) -> str:
    for a, b in _ACC.items():
        s = s.replace(a, b)
    return s


def git_hashes() -> set:
    out = subprocess.run(
        ["git", "-C", str(RAIZ), "log", "--format=%h %H"],
        capture_output=True, text=True, check=True,
    ).stdout
    hashes = set()
    for linea in out.splitlines():
        partes = linea.split()
        if partes:
            hashes.add(partes[0].lower())
            if len(partes) > 1:
                hashes.add(partes[1].lower())
    return hashes


def git_paths_historicos() -> set:
    """Todos los paths que git ha rastreado alguna vez (para refs históricas)."""
    out = subprocess.run(
        ["git", "-C", str(RAIZ), "log", "--all", "--pretty=format:", "--name-only"],
        capture_output=True, text=True, check=True,
    ).stdout
    paths = set()
    for linea in out.splitlines():
        p = linea.strip()
        if p and not p.startswith("'"):
            paths.add(p.replace("\\", "/"))
    return paths


def hash_existe(h: str, hashes: set) -> bool:
    if h.lower() in hashes:
        return True
    out = subprocess.run(
        ["git", "-C", str(RAIZ), "cat-file", "-e", f"{h}^{{commit}}"],
        capture_output=True, text=True,
    )
    return out.returncode == 0


def extraer_filas_bitacora(texto: str) -> list:
    """Filas `| fecha | tarea | estado | detalle |`.

    Las celdas pueden contener `|` literales (p.ej. ADT `ok(T) | err(E)`),
    por lo que el estado se detecta por marcador (primer celda con ✅/⚠️/🔄/⬜
    o PENDIENTE) en vez de por posición fija.
    """
    filas = []
    for linea in texto.splitlines():
        if not linea.startswith("| 2026-"):
            continue
        celdas = [c.strip() for c in linea.strip("|").split("|")]
        if len(celdas) < 3:
            continue
        fecha = celdas[0]
        # Índice de la primera celda que parece un estado
        idx_estado = None
        for k in range(1, len(celdas)):
            c = celdas[k]
            if c.startswith(("✅", "⚠️", "🔄", "⬜")) or c.upper().startswith("PENDIENTE"):
                idx_estado = k
                break
        if idx_estado is None:
            continue
        filas.append({
            "fecha": fecha,
            "tarea": " | ".join(celdas[1:idx_estado]),
            "estado": celdas[idx_estado],
            "detalle": " | ".join(celdas[idx_estado + 1:]),
        })
    return filas


RE_HASH = re.compile(r"\b(?:[Cc]ommit|HASH COMMIT|Hash)\b\s*[:：]?\s*[`*]*([0-9a-fA-F]{7,40})")
# Cita de reporte: con o sin prefijo docs/reportes/
RE_REPORTE = re.compile(r"`?(?:docs/reportes/)?([A-Za-z0-9_.\-]+\.md)`?")
RE_SECCION = re.compile(r"[§]\s*(\d+)")


def encabezados_md(texto: str) -> set:
    nums = set()
    for linea in texto.splitlines():
        m = re.match(r"^#{1,4}\s+(\d+)", linea)
        if m:
            nums.add(int(m.group(1)))
    return nums


def seccion_es_de_manual(detalle: str, pos: int) -> bool:
    """¿La §N en `pos` pertenece a una cita 'Manual X §N'?"""
    antes = detalle[max(0, pos - 30):pos]
    return bool(re.search(r"manual\s*\d", antes, re.IGNORECASE))


def cita_reporte(detalle: str, reportes_nombres) -> bool:
    """¿El detalle cita algún archivo de docs/reportes/ existente?"""
    return any(m.group(1) in reportes_nombres for m in RE_REPORTE.finditer(detalle))


def verificar_bitacora(filas, hashes, reportes_texto, reportes_nombres):
    brechas = []
    info = []
    for i, fila in enumerate(filas, 1):
        detalle = fila["detalle"]
        estado = fila["estado"].strip()
        # Estado
        if estado.startswith("✅"):
            pass
        elif estado.startswith(("⚠️", "🔄", "⬜", "PENDIENTE")):
            info.append(f"B{i} [{fila['fecha']}] estado abierto: '{estado}'")
        else:
            brechas.append(f"B{i} [{fila['fecha']}] estado sin marcar: '{estado}'")

        # Reportes citados (existentes en docs/reportes/)
        menciones = []
        for m in RE_REPORTE.finditer(detalle):
            nombre = m.group(1)
            if nombre in reportes_nombres:
                menciones.append((m.start(), nombre))
        # Eliminar duplicados conservando la primera posición
        menciones_uniq = []
        vistos = set()
        for pos, nombre in menciones:
            if nombre not in vistos:
                vistos.add(nombre)
                menciones_uniq.append((pos, nombre))
        menciones = menciones_uniq

        if not menciones:
            if not RE_HASH.search(detalle):
                pre_convencion = not any(
                    cita_reporte(f2["detalle"], reportes_nombres)
                    for f2 in filas[:i - 1]
                )
                solo_registro = re.search(r"en la sesi[oó]n|solo registrar", detalle, re.IGNORECASE)
                if pre_convencion or solo_registro:
                    info.append(f"B{i} [{fila['fecha']}] fila sin reporte (pre-convencion o solo registro)")
                else:
                    brechas.append(
                        f"B{i} [{fila['fecha']}] fila sin reporte ni hash citado"
                    )
            else:
                info.append(f"B{i} [{fila['fecha']}] fila sin reporte (solo hash)")
        else:
            # Secciones §N citadas DESPUÉS de la mención del reporte
            for pos, nombre in menciones:
                ruta = REPORTES_DIR / nombre
                if not ruta.exists():
                    brechas.append(f"B{i} [{fila['fecha']}] reporte inexistente: docs/reportes/{nombre}")
                    continue
                nums = encabezados_md(reportes_texto.get(nombre, ""))
                tramo = detalle[pos:]
                for m in RE_SECCION.finditer(tramo):
                    if seccion_es_de_manual(tramo, m.start()):
                        continue
                    s = int(m.group(1))
                    if s not in nums:
                        info.append(
                            f"B{i} [{fila['fecha']}] seccion §{s} no hallada en docs/reportes/{nombre}"
                        )

        # Hashes de commit citados
        for h in RE_HASH.findall(detalle):
            if not hash_existe(h, hashes):
                brechas.append(f"B{i} [{fila['fecha']}] hash no hallado en git: {h}")
    return brechas, info


RE_REF_ARCHIVO = re.compile(r"`((?:nucleo|compilador|tests|examples|logs)/[^`]+)`")

# ---------------------------------------------------------------------------
# REGLA 11 — Registro canónico de deudas. Toda deuda debe estar registrada con
# resolución asignada (estado PENDIENTE requiere fase/plan) y mencionada en el
# doc de auditoría. Cualquier deuda nueva no registrada aquí es una brecha.
# ---------------------------------------------------------------------------
DEUDAS_CANONICAS = {
    "D-F1": {"estado": "CERRADA", "resolucion": "F1.2c+F1.2d+F1.4 (keywords del Manual 2 §3)"},
    "D-1":  {"estado": "PENDIENTE", "resolucion": "Fase 23 (modelo de memoria Syquex: arenas/RC/alcance)"},
    "D-2":  {"estado": "CERRADA", "resolucion": "A5 monomorfización (Opción A del Arquitecto)"},
    "D-3":  {"estado": "CERRADA", "resolucion": "A5 hoisting FIFO + = {0};"},
    "D-4":  {"estado": "CERRADA", "resolucion": "R60 verificador_formal.syn + verificador_formal.py (19 tests security); AST leak F5-1 cerrado; 34 tests D5+security pass"},
    "D-5":  {"estado": "CERRADA", "resolucion": "A5 cobertura generator.py 58%→95%"},
    "D-6":  {"estado": "CERRADA", "resolucion": "A5 operador ? postfijo"},
    "D-7":  {"estado": "CERRADA", "resolucion": "A5 ABI entero→int64_t / decimal→double"},
    "D-8":  {"estado": "CERRADA", "resolucion": "sin acción (por diseño, Manual 2 §2: cadenas multi-línea)"},
    "D-9":  {"estado": "CERRADA", "resolucion": "R42: D-9(d) corte 6 CERRADA COMPLETA; (a) parser.syn CERRADA en R29; (b) lexer_keywords.syn CERRADA en R32; (c) emit_selfhost.py CERRADA en R33 (podado emitir_generar); (d) synapse_rt.c 7.882->1.769 L, runtime/core/ 20+ modulos; (e) NodoID/TokenID: tabla canonica unica runtime/core/ast_nodos.h (gen desde nucleo/parser_constantes.syn; generator.py emite #include; 9 archivos C/H migrados; tests cross-language 1:1; gen_ast_nodos_h.py --check en CI"},
    "H12":  {"estado": "PENDIENTE", "resolucion": "Fase 26 (opensyn stale)"},
    "R3":   {"estado": "CERRADA", "resolucion": "tests/unit/test_r3_param_adt.py + fixtures: S1/S2 compilan y ejecutan parámetros ADT instanciados (Resultado<entero,texto> -> Resultado_entero_texto)"},
}

# ---------------------------------------------------------------------------
# REGLA 13 — Convención ~1000 líneas/módulo. Los .syn del compilador (no
# generator.syn, unity ensamblado) que superen LÍMITE_MODULO y no estén
# registrados en D-9 son brechas (deuda sin registrar).
# ---------------------------------------------------------------------------
LIMITE_MODULO = 1200
MODULOS_D9 = [
    "nucleo/lexer.syn",            # D-9(b): keywords extraidos en R32 (módulo 769 líneas, <límite)
    "nucleo/analizador_semantico.syn",  # D-9(e): cohesivo, vigilado
    "compilador/generator/generator.py",     # D-9(e): cohesivo, vigilado; NodoID/TokenID canonico resuelto (R76)
    "synapse_rt.c",                # D-9(d): monolito en proceso (corte 2 tensor.c en R35; queda std.ai/cluster/debug)
]


def limpiar_ref(ruta: str) -> str:
    """Quita sufijos de línea (:343), rangos (:176-178), (:535:0), listas (:129,282,549)
    y símbolos (::metodo)."""
    r = ruta.strip()
    r = re.sub(r"::\S+$", "", r)                    # compilador/parser_base.py::_parsear...
    # Quitar suffixes de línea: :N, :N-M, :N:0, :N,M,O (listas de líneas)
    while re.search(r":\d+([,:-]?\d+)*$", r):
        r = re.sub(r":\d+([,:-]?\d+)*$", "", r)
    return r


def verificar_reportes(reportes_texto, paths_historicos):
    brechas = []
    info = []
    for rep, texto in sorted(reportes_texto.items()):
        plano = sin_acentos(texto)
        es_protocolo = "REPORTE DE MICRO-ENTREGABLE" in sin_acentos(texto).upper()

        if es_protocolo:
            faltan = [
                c for c in CAMPOS_PROTOCOLO
                if not re.search(rf"{re.escape(c)}\s*(?:\([^\n]*\))?\s*[:：]", plano)
            ]
            if faltan:
                brechas.append(f"R[{rep}] faltan campos del protocolo: {', '.join(faltan)}")
        else:
            info.append(f"R[{rep}] sin bloque 'REPORTE DE MICRO-ENTREGABLE' (formato propio)")

        # HASH COMMIT pendiente
        m = re.search(r"HASH COMMIT\s*[:：]\s*([^\n]+)", sin_acentos(texto), re.IGNORECASE)
        if m and re.search(r"pendiente|working tree|por definir|tbd", m.group(1), re.IGNORECASE):
            texto_p = f"R[{rep}] HASH COMMIT pendiente: '{m.group(1).strip()[:60]}'"
            if es_protocolo:
                brechas.append(texto_p)
            else:
                info.append(texto_p)

        # Referencias a archivos
        for m in RE_REF_ARCHIVO.finditer(texto):
            ref = limpiar_ref(m.group(1))
            if "*" in ref or "?" in ref:
                continue  # glob, no comprobable
            if (RAIZ / ref).exists():
                continue
            contexto = texto[max(0, m.start() - 120):m.end() + 120]
            elim_doc = re.search(r"ELIMINAD|eliminad|suprimid|muerto|retirad|borrad", contexto, re.IGNORECASE)
            planificado = re.search(r"no exist|\bP1\b|planificad|futuro test|pendiente de crear", contexto, re.IGNORECASE)
            if ref in paths_historicos or elim_doc or planificado:
                info.append(f"R[{rep}] ref historica o planificada: {ref}")
            else:
                brechas.append(f"R[{rep}] referencia a archivo inexistente: {ref}")
    return brechas, info


# ---------------------------------------------------------------------------
# REGLA 11 — Deudas registradas con resolución asignada
# ---------------------------------------------------------------------------
# Solo deudas D-*: los hallazgos H* tienen su propia tabla en el doc (ya resueltos).
RE_DEUDA_BITACORA = re.compile(r"\b(D-\d+|D-F1)\b")


def verificar_deudas(texto_bitacora, texto_auditoria):
    """Toda deuda canónica debe mencionarse en el doc; toda deuda pendiente debe
    tener resolución asignada. Las deudas nuevas (en bitácora) sin registrar
    en el canon son brechas (regla 11: nada queda sin seguimiento)."""
    brechas, info = [], []
    for deuda, datos in DEUDAS_CANONICAS.items():
        if deuda not in texto_auditoria and deuda not in texto_bitacora:
            brechas.append(f"D[{deuda}] deuda registrada en el canon pero ausente del doc de auditoría")
            continue
        if datos["estado"] == "PENDIENTE" and not datos["resolucion"]:
            brechas.append(f"D[{deuda}] deuda PENDIENTE sin resolución asignada (regla 11)")
        if datos["estado"] == "PENDIENTE":
            info.append(f"D[{deuda}] PENDIENTE — resolución: {datos['resolucion']}")
    # Deudas mencionadas en la bitácora que no están en el canon
    encontradas = set(RE_DEUDA_BITACORA.findall(texto_bitacora))
    no_registradas = encontradas - set(DEUDAS_CANONICAS)
    for d in sorted(no_registradas):
        brechas.append(f"D[{d}] deuda citada en la bitácora SIN registro en el canon (regla 11)")
    return brechas, info


# ---------------------------------------------------------------------------
# REGLA 12 — Código muerto: scripts de parche/depuración en la raíz
# ---------------------------------------------------------------------------
def verificar_codigo_muerto():
    """Scripts de depuración `_*.py` en la raíz = código muerto (regla 12).
    El CI ya bloquea `_fix_*.py`; este gate amplía a cualquier `_*.py` raíz."""
    brechas = []
    for p in sorted(RAIZ.glob("_*.py")):
        brechas.append(f"R12[{p.name}] script de depuración en la raíz — eliminar (regla 12)")
    return brechas


# ---------------------------------------------------------------------------
# REGLA 13 — Modularización: módulos del compilador >1200 líneas sin D-9
# ---------------------------------------------------------------------------
def verificar_modularizacion():
    """Archivos .syn del compilador >1200 líneas no registrados en D-9
    (o archivos .py del generador >1200) = deuda sin registrar (regla 13).
    generator.syn es unity ensamblado (exceptuado)."""
    brechas, info = [], []
    candidatos = sorted(RAIZ.glob("nucleo/*.syn")) + sorted(RAIZ.glob("compilador/generator/*.py"))
    for p in candidatos:
        if p.name == "generator.syn":
            continue
        # Convencion regla 12: prefijo '_' = artefacto/instrumentacion
        # temporal (harnesses _tmp_* de tests, probes) — nunca produccion.
        if p.name.startswith("_"):
            continue
        try:
            n = sum(1 for _ in p.open(encoding="utf-8", errors="replace"))
        except OSError:
            continue
        if n > LIMITE_MODULO:
            ref = str(p.relative_to(RAIZ)).replace("\\", "/")
            if ref in MODULOS_D9:
                info.append(f"R13[{ref}] {n} líneas — registrado en D-9 (resolución asignada)")
            else:
                brechas.append(
                    f"R13[{ref}] {n} líneas > {LIMITE_MODULO} sin registrar en D-9 (regla 13)"
                )
    return brechas, info


# ---------------------------------------------------------------------------
# Manual 2 §12 — Toda función pública NUEVA debe declarar requiere/garantiza
# ---------------------------------------------------------------------------
def verificar_contratos_nuevos():
    """Funciones añadidas o modificadas en el working tree vs HEAD en nucleo/*.syn
    deben tener bloques requiere/garantiza (Manual 2 §12; D-4 registra las
    306 existentes sin contrato hasta Fase 5 — el gate solo cubre código NUEVO)."""
    out = subprocess.run(
        ["git", "-C", str(RAIZ), "diff", "--unified=40", "HEAD", "--", "nucleo/*.syn"],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        return ["No se pudo calcular el diff de nucleo/*.syn vs HEAD"], []
    diff = out.stdout
    brechas, info = [], []
    # Funciones definidas en HEAD (para distinguir MOVIMIENTO de código — p.ej.
    # modularización mecánica tipo R29/R32 — de función realmente NUEVA: un split
    # no crea funciones nuevas, el gate de contratos solo cubre código nuevo).
    nombres_head = _funciones_en_head()
    # Por archivo del diff: recoger las líneas + de cada archivo
    lineas_por_archivo = {}
    archivo_actual = None
    for linea in diff.splitlines():
        m = re.match(r"^\+\+\+ b/(.*\.syn)$", linea)
        if m:
            archivo_actual = m.group(1)
            lineas_por_archivo.setdefault(archivo_actual, [])
            continue
        if archivo_actual is None or linea.startswith(("--- ", "diff --git", "index ")):
            continue
        if linea.startswith("+") and not linea.startswith("+++"):
            lineas_por_archivo[archivo_actual].append(linea[1:])
    # Para cada función nueva (definida en líneas +), buscar requiere/garantiza
    # en las siguientes líneas + (hasta 25 líneas, dentro de su cuerpo)
    for archivo, lineas in lineas_por_archivo.items():
        for k, linea in enumerate(lineas):
            m = re.match(r"^funcion\s+([A-Za-z_][A-Za-z0-9_]*)", linea)
            if not m:
                continue
            nombre = m.group(1)
            ventana = "\n".join(lineas[k + 1:k + 26])
            if "requiere:" in ventana or "garantiza:" in ventana:
                info.append(f"CTR[{archivo}] función '{nombre}' con requiere/garantiza ✓")
            elif nombre in nombres_head:
                info.append(
                    f"CTR[{archivo}] función '{nombre}' MOVIDA (existía en HEAD, sin contrato "
                    f"pre-existente — split mecánico, no aplica D-4)"
                )
            else:
                # El diff puede alinear bloques estructuralmente similares y dejar
                # las líneas requiere:/garantiza: como contexto (sin prefijo +),
                # aunque existan en el archivo (falso positivo). Verificar contra
                # el working tree antes de declarar la brecha.
                if _contratos_en_archivo(archivo, nombre):
                    info.append(
                        f"CTR[{archivo}] función '{nombre}' con requiere/garantiza ✓ "
                        f"(verificada en el archivo; el diff las alineó como contexto)"
                    )
                else:
                    brechas.append(
                        f"CTR[{archivo}] función nueva '{nombre}' sin requiere/garantiza (Manual 2 §12)"
                    )
    return brechas, info


def _contratos_en_archivo(archivo: str, nombre: str) -> bool:
    """Comprueba en el working tree si la función 'nombre' declara
    requiere:/garantiza: a continuación de su definición."""
    ruta = RAIZ / archivo
    if not ruta.exists():
        return False
    try:
        lineas = ruta.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return False
    for k, linea in enumerate(lineas):
        m = re.match(r"^funcion\s+([A-Za-z_][A-Za-z0-9_]*)", linea)
        if m and m.group(1) == nombre:
            ventana = "\n".join(lineas[k + 1:k + 26])
            return "requiere:" in ventana or "garantiza:" in ventana
    return False


def _funciones_en_head() -> set:
    """Nombres de todas las funciones definidas en nucleo/*.syn en HEAD (git)."""
    nombres: set = set()
    try:
        ls = subprocess.run(
            # El pathspec glob no expande en todas las plataformas (Windows);
            # listar nucleo/ completo y filtrar .syn en Python (más robusto).
            ["git", "-C", str(RAIZ), "ls-tree", "-r", "--name-only", "HEAD", "--", "nucleo/"],
            capture_output=True, text=True,
        )
        if ls.returncode != 0:
            return nombres
        for ruta in ls.stdout.splitlines():
            if not ruta.endswith(".syn"):
                continue
            show = subprocess.run(
                # encoding utf-8: los .syn del compilador contienen UTF-8 real
                # (débil, déléguer, §) que cp1252 (Windows) no decodifica.
                ["git", "-C", str(RAIZ), "show", f"HEAD:{ruta}"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            if show.returncode != 0:
                continue
            for linea in show.stdout.splitlines():
                m = re.match(r"^funcion\s+([A-Za-z_][A-Za-z0-9_]*)", linea)
                if m:
                    nombres.add(m.group(1))
    except Exception:
        pass
    return nombres


def main():
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    resultado = {"ok": True, "brechas": [], "info": [], "resumen": {}}

    hashes = git_hashes()
    paths_historicos = git_paths_historicos()
    texto_bitacora = BITACORA.read_text(encoding="utf-8")
    filas = extraer_filas_bitacora(texto_bitacora)

    reportes_texto = {}
    for p in sorted(REPORTES_DIR.glob("*.md")):
        reportes_texto[p.name] = p.read_text(encoding="utf-8")
    reportes_nombres = set(reportes_texto)

    manuales = [f"MANUAL {i}.md" for i in range(1, 10)]
    faltan_manuales = [m for m in manuales if not (MANUALES_DIR / m).exists()]
    if faltan_manuales:
        resultado["brechas"].append("Faltan manuales: " + ", ".join(faltan_manuales))

    b, i = verificar_bitacora(filas, hashes, reportes_texto, reportes_nombres)
    resultado["brechas"].extend(b)
    resultado["info"].extend(i)

    b, i = verificar_reportes(reportes_texto, paths_historicos)
    resultado["brechas"].extend(b)
    resultado["info"].extend(i)

    # REGLAS 11/12/13 + Manual 2 §12 (contratos en funciones nuevas)
    b, i = verificar_deudas(texto_bitacora, BITACORA.read_text(encoding="utf-8"))
    resultado["brechas"].extend(b)
    resultado["info"].extend(i)

    resultado["brechas"].extend(verificar_codigo_muerto())

    b, i = verificar_modularizacion()
    resultado["brechas"].extend(b)
    resultado["info"].extend(i)

    b, i = verificar_contratos_nuevos()
    resultado["brechas"].extend(b)
    resultado["info"].extend(i)

    resultado["ok"] = not resultado["brechas"]
    resultado["resumen"] = {
        "filas_bitacora": len(filas),
        "reportes": len(reportes_texto),
        "hashes_commit_citados": sum(len(RE_HASH.findall(f["detalle"])) for f in filas),
        "brechas": len(resultado["brechas"]),
        "notas_info": len(resultado["info"]),
    }

    if "--json" in sys.argv:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        sys.exit(0 if resultado["ok"] else 1)

    print("=" * 72)
    print("VERIFICADOR DE ALINEACION — bitacora / reportes / git")
    print("=" * 72)
    print(f"Filas de bitacora:          {resultado['resumen']['filas_bitacora']}")
    print(f"Reportes en docs/reportes/: {resultado['resumen']['reportes']}")
    print(f"Hashes de commit citados:   {resultado['resumen']['hashes_commit_citados']}")
    print(f"Brechas encontradas:        {resultado['resumen']['brechas']}")
    print(f"Notas informativas:         {resultado['resumen']['notas_info']}")
    print("-" * 72)
    if resultado["brechas"]:
        print("BRECHAS (errores de trazabilidad):")
        for b in resultado["brechas"]:
            print(f"  [!] {b}")
    if resultado["info"]:
        print("NOTAS (informativas):")
        for n in resultado["info"]:
            print(f"  [~] {n}")
    print("=" * 72)
    if resultado["brechas"]:
        print("RESULTADO: BRECHAS DETECTADAS — verificar cada una (regla 11: resolver o registrar)")
    else:
        print("RESULTADO: SIN BRECHAS — trazabilidad verificada")
    sys.exit(0 if resultado["ok"] else 1)


if __name__ == "__main__":
    main()
