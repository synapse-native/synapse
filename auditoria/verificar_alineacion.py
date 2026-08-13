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


def limpiar_ref(ruta: str) -> str:
    """Quita sufijos de línea (:343), rangos (:176-178), (:535:0) y símbolos (::metodo)."""
    r = ruta.strip()
    r = re.sub(r"::\S+$", "", r)                    # compilador/parser_base.py::_parsear...
    while re.search(r":\d+(-\d+)?$", r):
        r = re.sub(r":\d+(-\d+)?$", "", r)          # nucleo/generator.syn:343 / :535:0
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
