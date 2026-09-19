#!/usr/bin/env python3
# ============================================================================
# alineacion.py — Gate de alineación manual↔código (rediseño del control)
# ============================================================================
# Reemplaza el control declarativo ("registré que leí Manual 7") por un control
# verificable en tres piezas:
#
#   1. LECTURA (antes de codificar) — `--leer`: imprime las oraciones
#      normativas LITERALES de las secciones que el mapa exige para los
#      archivos que vas a tocar, y deja un sello en .git/alineacion/.
#   2. EXPEDIENTE (el cambio) — `docs/alineacion/<ME>.md`: por archivo, anclas
#      con (manual, sección, CITA TEXTUAL verificada contra el manual vigente),
#      tipo de requisito, estado CUMPLE/DESVIACION, evidencia archivo:línea y
#      oráculo ejecutable. `--nuevo` lo pre-genera; el agente lo completa.
#   3. VERIFICACIÓN (después de codificar) — `--verificar`: valida el
#      expediente contra el diff real, contra el manual vigente y contra el
#      código; ejecuta los oráculos y deja evidencia en
#      `auditoria/evidencia/<cambio_hash>.json`.
#
# Reglas duras que impone (cierran los agujeros del gate anterior):
#   - Cita textual literal: no se puede declarar una lectura sin citar texto
#     que exista en la sección del manual vigente (anti-fabricación real).
#   - Atado al cambio: cambio_hash = sha256 de (ruta, blob) de los archivos de
#     producción del diff. No hay "lecturas de hoy" ni cobertura global.
#   - CUMPLE exige comentario `// cumple Manual X §Y` en la línea de evidencia.
#   - DESVIACION exige corrección que toque líneas del diff o decisión D-*
#     ratificada: no existe "lo reviso después".
#   - Oráculos se EJECUTAN (modo release); SKIP/xfail/sin-test no es evidencia.
#   - Si el cambio toca los manuales, revalida las citas vivas del repo.
#
# Sin dependencias externas (stdlib + git en modo lectura).
# ============================================================================

import argparse
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import indice_manual as im  # noqa: E402  (mismo directorio)

EXPEDIENTES_DIR = RAIZ / "docs" / "alineacion"
EVIDENCIA_DIR = RAIZ / "auditoria" / "evidencia"
MAPA_ALINEACION = RAIZ / "docs" / "gobernancia" / "mapa_alineacion.md"
MAPA_LEGACY = RAIZ / "docs" / "gobernancia" / "mapa_manuales.md"
SELLO_DIR = RAIZ / ".git" / "alineacion"
BITACORA = RAIZ / "docs" / "auditorias" / "AUDITORIA_ALINEACION_MANUALES.md"
MEMORIA = RAIZ / "MEMORIA_PROYECTO.md"

EXCLUIDOS = (
    "tests/*", "docs/*", "auditoria/*", "scripts/*", "benchmarks/*",
    "examples/*", "vscode-synapse/*", ".github/*", ".kilo/*", "vendor/*",
)
EXTENSIONES = (".syn", ".syq", ".c", ".h", ".py")
TIPOS = ("contrato", "comportamiento", "seguridad", "rendimiento")
ESTADOS = ("CUMPLE", "DESVIACION", "PENDIENTE")

RE_CITA = re.compile(r"cumple\s+Manual\s+(\d+)\s*(?:§\s*)?(\d+(?:\.\d+){0,3})?",
                     re.IGNORECASE)
RE_EVIDENCIA = re.compile(r"^(?P<archivo>[^\s:]+):(?P<l1>\d+)(?:\s*-\s*(?P<l2>\d+))?$")
RE_HUNK = re.compile(r"^@@\s*-\d+(?:,\d+)?\s*\+(\d+)(?:,(\d+))?\s*@@")
RE_MAPA_JSON = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL)


# ---------------------------------------------------------------------------
# Utilidades git / sistema
# ---------------------------------------------------------------------------
def _run(cmd):
    """Ejecuta un comando y devuelve (stdout, rc). Nunca lanza."""
    try:
        res = subprocess.run(cmd, cwd=str(RAIZ), capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=600)
        return res.stdout or "", res.returncode
    except Exception as e:  # noqa: BLE001 - gate defensivo
        return f"[error de ejecucion: {e}]", 1


def es_produccion(ruta):
    r = ruta.replace("\\", "/").lstrip("./")
    if Path(r).name.startswith("_"):
        return False
    for pat in EXCLUIDOS:
        if fnmatch.fnmatch(r, pat):
            return False
    return Path(r).suffix.lower() in EXTENSIONES


def archivos_cambio(desde=None):
    """Archivos de producción del cambio.

    Sin `desde`: index (staged) — alcance local, no bloquea por trabajo ajeno.
    Con `desde`: diff `desde...HEAD` — mismo cálculo que hace el CI.
    """
    if desde:
        out, rc = _run(["git", "diff", "--name-only", "--diff-filter=ACMR",
                        f"{desde}...HEAD"])
    else:
        out, rc = _run(["git", "diff", "--cached", "--name-only",
                        "--diff-filter=ACMR"])
    if rc != 0:
        return []
    return [f.replace("\\", "/").strip() for f in out.splitlines() if f.strip()]


def blob_sha(ruta, desde=None):
    """sha del blob en el index (o en HEAD si se compara contra una base)."""
    ref = f"{desde}:{ruta}" if desde else f":{ruta}"
    out, rc = _run(["git", "rev-parse", ref])
    return out.strip() if rc == 0 else ""


def cambio_hash(archivos, desde=None):
    """Huella del cambio: ata el expediente a ESTE conjunto de contenido.

    Igual local (blobs staged) y en CI (blobs de HEAD), por lo que sirve para
    castigar un commit hecho con `--no-verify`: sin expediente/evidencia que
    corresponda a esta huella, el merge se bloquea.
    """
    partes = []
    for f in sorted(archivos):
        partes.append(f"{f}\0{blob_sha(f, desde)}")
    return hashlib.sha256("\n".join(partes).encode("utf-8")).hexdigest()[:16]


def rangos_cambiados(archivos, desde=None):
    """{ruta: [(inicio, fin)]} en numeración del archivo NUEVO."""
    cmd = ["git", "diff", "-U0"]
    cmd += [f"{desde}...HEAD"] if desde else ["--cached"]
    cmd += ["--"] + list(archivos)
    out, _ = _run(cmd)
    rangos, actual = {}, None
    for linea in out.splitlines():
        if linea.startswith("+++ "):
            actual = linea[6:].strip()
            if actual.startswith("b/"):
                actual = actual[2:]
            rangos.setdefault(actual, [])
            continue
        m = RE_HUNK.match(linea)
        if m and actual:
            ini = int(m.group(1))
            largo = int(m.group(2)) if m.group(2) else 1
            rangos[actual].append((ini, ini + max(largo, 1) - 1))
    return rangos


def indice_desactualizado(indice):
    """True si un manual cambió respecto del sha256 guardado en el índice.

    Sin esto, validar contra el índice sería validar contra un manual viejo:
    el agente podría "citar" una sección que ya no dice eso.
    """
    for datos in indice.get("manuales", {}).values():
        path = RAIZ / datos.get("archivo", "")
        if not path.exists():
            return True
        texto = path.read_text(encoding="utf-8", errors="replace")
        sha = hashlib.sha256(texto.encode("utf-8")).hexdigest()[:16]
        if sha != datos.get("sha256"):
            return True
    return False


def contiene_linea(ruta, linea, patron, margen=3):
    """True si alguna línea en ±margen cumple el regex (ancla real en el código)."""
    try:
        texto = (RAIZ / ruta).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    lineas = texto.splitlines()
    lo = max(0, linea - 1 - margen)
    hi = min(len(lineas), linea + margen)
    return any(patron.search(l) for l in lineas[lo:hi])


# ---------------------------------------------------------------------------
# Mapas de requisitos
# ---------------------------------------------------------------------------
def cargar_mapa(path):
    """Extrae el bloque ```json del mapa y devuelve {patrón: [citas]}."""
    if not path.exists():
        return {}
    m = RE_MAPA_JSON.search(path.read_text(encoding="utf-8", errors="replace"))
    if not m:
        return {}
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return {}


def parsear_cita(cita):
    """'Manual 6 §1.3' -> ('6', '1.3'). Sin §N -> ('6', '')."""
    m = re.search(r"manual\s*(\d+)", cita, re.IGNORECASE)
    if not m:
        return None
    s = re.search(r"§\s*(\d+(?:\.\d+){0,3})", cita)
    return (m.group(1), s.group(1) if s else "")


def _especificidad(patron):
    """Cuán específico es un patrón (independiente del orden del JSON).

    Más caracteres literales = más específico; a igualdad de literales, menos
    comodines = más específico. Así `opensyn/router.syn` gana sobre
    `opensyn/*` sin depender del orden de inserción en el mapa.
    """
    literales = len(re.sub(r"[*?\[\]]", "", patron))
    comodines = patron.count("*") + patron.count("?")
    return (literales, -comodines)


def requisitos_archivo(ruta, mapa_alineacion, mapa_legacy):
    """[(manual, seccion)] exigidos para un archivo de producción.

    1º mapa puntual (mapa_alineacion.md); 2º fallback al mapa legacy para que
    ningún archivo quede sin requisito (sección '' = cualquier sección real de
    ese manual, misma semántica que el gate anterior). Gana el patrón MÁS
    ESPECÍFICO que coincida (no el primero).
    """
    r = ruta.replace("\\", "/")
    for origen in (mapa_alineacion, mapa_legacy):
        coincidencias = [(p, c) for p, c in origen.items() if fnmatch.fnmatch(r, p)]
        if coincidencias:
            _, citas = max(coincidencias, key=lambda pc: _especificidad(pc[0]))
            return [parsear_cita(c) for c in citas if parsear_cita(c)]
    return []


def cubre(req, ancla_manual, ancla_seccion):
    """¿El ancla cubre el requisito? (leer §2.4 cubre §2; §2 no cubre §2.4)."""
    manual, seccion = req
    if manual != ancla_manual:
        return False
    if not seccion:
        return bool(ancla_seccion)   # requisito de manual entero
    return ancla_seccion == seccion or ancla_seccion.startswith(seccion + ".")


# ---------------------------------------------------------------------------
# Expediente
# ---------------------------------------------------------------------------
def ruta_expediente(me):
    return EXPEDIENTES_DIR / f"{me}.md"


def leer_expediente(path, desde_commit=False):
    """Lee el expediente desde el árbol o desde HEAD (modo CI)."""
    if desde_commit:
        out, rc = _run(["git", "show", f"HEAD:{path.relative_to(RAIZ).as_posix()}"])
        return out if rc == 0 else ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def parsear_expediente(texto):
    """Parsea el expediente a {cambio_hash, base, archivos: {ruta: [anclas]}}."""
    exp = {"cambio_hash": "", "base": "", "archivos": {}}
    actual = None
    ancla = None
    for cruda in texto.splitlines():
        linea = cruda.rstrip()
        m = re.match(r"^cambio_hash:\s*(\S+)", linea)
        if m:
            valor = m.group(1)
            exp["cambio_hash"] = "" if valor.startswith("#") else valor
            continue
        m = re.match(r"^base:\s*(\S+)", linea)
        if m:
            exp["base"] = m.group(1)
            continue
        m = re.match(r"^##\s+(\S+)\s*$", linea)
        if m:
            actual = m.group(1).replace("\\", "/")
            exp["archivos"].setdefault(actual, [])
            ancla = None
            continue
        m = re.match(r"^-\s*manual:\s*(\d+)\s*$", linea, re.IGNORECASE)
        if m and actual:
            ancla = {"manual": m.group(1)}
            exp["archivos"][actual].append(ancla)
            continue
        m = re.match(r"^\s+([a-z_]+):\s*(.*)$", linea)
        if m and ancla is not None:
            clave, valor = m.group(1).lower(), m.group(2).strip()
            if len(valor) >= 2 and valor[0] == valor[-1] == '"':
                valor = valor[1:-1]
            ancla[clave] = valor
    return exp


def scaffold_expediente(me, archivos, requisitos, indice):
    """Genera el expediente con las anclas y una cita candidata ya extraída."""
    lineas = [
        f"# Expediente de alineación {me}",
        "",
        f"base: HEAD  # commit sobre el que se leyó el manual",
"cambio_hash:",
        "",
        "> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.",
        "> CUMPLE exige `evidencia: archivo:linea` con el comentario",
        "> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.",
        "> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff",
        "> (o `decision: D-xxx` ratificada en la bitácora).",
        "",
    ]
    for ruta in archivos:
        lineas.append(f"## {ruta}")
        reqs = requisitos.get(ruta, [])
        if not reqs:
            lineas += ["- manual: 0   # sin requisito en el mapa: añadilo a",
                       "             # docs/gobernancia/mapa_alineacion.md", ""]
            continue
        for manual, seccion in reqs:
            oraciones = im.oraciones_citables(indice, manual, seccion)
            cita = oraciones[0]["texto"] if oraciones else "(sin oraciones indexadas)"
            lineas += [
                f"- manual: {manual}",
                f"  seccion: {seccion or '?'}",
                f"  cita: \"{cita}\"",
                "  tipo: comportamiento",
                "  estado: PENDIENTE",
                "  evidencia:",
                "  oraculo:",
                "",
            ]
    return "\n".join(lineas) + "\n"


# ---------------------------------------------------------------------------
# Oráculos
# ---------------------------------------------------------------------------
def ejecutar_oraculo(ruta, modo="auto"):
    """Ejecuta un oráculo y devuelve evidencia. SKIP/sin-test NO es PASS."""
    ruta_abs = RAIZ / ruta
    if not ruta_abs.exists():
        return {"oraculo": ruta, "ok": False, "rc": None,
                "motivo": "no existe en el sistema de archivos"}
    if modo == "auto":
        nombre = ruta_abs.name
        modo = "pytest" if (nombre.startswith("test_") or "oracle" in nombre) \
            else "script"
    env = dict(os.environ, SYNAPSE_BUILD_MODE="release")
    if modo == "pytest":
        cmd = [sys.executable, "-m", "pytest", ruta, "-q", "--no-header",
               "-p", "no:cacheprovider"]
    else:
        cmd = [sys.executable, ruta]
    try:
        res = subprocess.run(cmd, cwd=str(RAIZ), capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=900,
                             env=env)
        salida, rc = (res.stdout or "") + (res.stderr or ""), res.returncode
    except subprocess.TimeoutExpired:
        return {"oraculo": ruta, "modo": modo, "ok": False, "rc": None,
                "motivo": "timeout"}
    bajo = salida.lower()
    motivo = ""
    if rc != 0:
        motivo = f"rc={rc}"
    elif "no tests ran" in bajo or "collected 0 items" in bajo:
        motivo = "no colectó ningún test"
    elif "skip" in bajo:
        motivo = "el oráculo se saltó (SKIP) — no cuenta como evidencia"
    elif modo == "script" and "skip" not in bajo and "ok:" not in bajo \
            and "pass" not in bajo:
        motivo = "script sin marca explícita de PASS (OK:/PASS)"
    elif any(x in bajo for x in (" xfail", "failed", "fallo")):
        motivo = "resultado con fallos/xfail"
    ok = motivo == ""
    return {"oraculo": ruta, "modo": modo, "ok": ok, "rc": rc,
            "motivo": motivo, "salida_sha256":
                hashlib.sha256(salida.encode("utf-8", "replace")).hexdigest()[:16],
            "extracto": salida.strip().splitlines()[-1][:160] if salida.strip() else ""}


# ---------------------------------------------------------------------------
# Verificación
# ---------------------------------------------------------------------------
def verificar(archivos, desde=None, me=None, modo="block", con_oraculos=True,
              ci=False, exigir_sello=False):
    """Corre todos los chequeos. Devuelve (errores, avisos, detalle)."""
    errores, avisos, detalle = [], [], {}
    prod = [f for f in archivos if es_produccion(f)]
    detalle["archivos_produccion"] = prod
    if not prod:
        return errores, avisos, detalle

    indice = im.cargar_indice()
    if indice_desactualizado(indice):
        errores.append(
            "el índice de manuales está desactualizado respecto de "
            "docs/manuales/ (la ley cambió): regenerá con "
            "python auditoria/alineacion.py --indice")
    mapa_alineacion = cargar_mapa(MAPA_ALINEACION)
    mapa_legacy = cargar_mapa(MAPA_LEGACY)
    ch = cambio_hash(prod, desde)
    detalle["cambio_hash"] = ch

    # --- expediente: explícito (--me) o autodetectado por huella/archivos ---
    elegido, contenido = None, ""
    if me:
        cand = ruta_expediente(me)
        texto = leer_expediente(cand, desde_commit=ci)
        if texto.strip():
            elegido, contenido = cand, texto
    else:
        # ENDURECIMIENTO (H-R150-SELLO): elegir el expediente por huella EXACTA
        # primero; si ninguna coincide, el de MAYOR solapamiento con el cambio.
        # Antes: el primer .md alfabético con 1 archivo compartido elegía el
        # expediente de un ME anterior (r149 compartía cli.py con r150) y el
        # gate acusaba brechas del expediente equivocado → bloqueo falso del hook.
        candidatas = []
        for cand in sorted(EXPEDIENTES_DIR.glob("*.md")):
            if cand.name == "DEUDA.md":
                continue
            texto = leer_expediente(cand, desde_commit=ci)
            exp = parsear_expediente(texto)
            if exp["cambio_hash"] == ch:
                elegido, contenido = cand, texto
                break
            interseccion = len(set(prod) & set(exp["archivos"]))
            if interseccion > 0:
                candidatas.append((interseccion, cand, texto))
        if elegido is None and candidatas:
            candidatas.sort(key=lambda t: (-t[0], t[1].name))
            _, elegido, contenido = candidatas[0]
    if elegido is None:
        errores.append(
            "falta el expediente de alineación para este cambio "
            f"(cambio_hash={ch}). Generá con: python auditoria/alineacion.py "
            "--nuevo --me <ME>")
        return errores, avisos, detalle
    detalle["expediente"] = elegido.relative_to(RAIZ).as_posix()
    exp = parsear_expediente(contenido)

    # (1) el expediente cubre EXACTAMENTE el cambio
    faltan = [f for f in prod if f not in exp["archivos"]]
    sobran = [f for f in exp["archivos"] if f not in prod]
    if faltan:
        errores.append("el expediente no tiene bloque para: " + ", ".join(faltan))
    if sobran:
        errores.append("el expediente declara archivos que no están en el "
                       "cambio: " + ", ".join(sobran))
    if exp["cambio_hash"] and exp["cambio_hash"] != ch:
        # ENDURECIMIENTO (era solo aviso): la huella del expediente debe
        # corresponder a ESTE contenido. Sin esto, un expediente verificado
        # una vez quedaba "válido" aunque el código cambiara después — la
        # evidencia quedaba desanclada del código real.
        errores.append(
            f"cambio_hash del expediente ({exp['cambio_hash']}) no coincide "
            f"con el actual ({ch}) — re-ejecutá --verificar para re-sellar "
            f"(la evidencia debe estar atada al contenido que se integra)")

    # (2) sello de lectura previa. Bloqueante SOLO en los gates reales
    # (pre-commit pasa --exigir-sello); en modo diagnóstico queda como aviso
    # para no romper usos herméticos. En CI la garantía equivalente es la
    # evidencia comiteada (evidencia_ci_ok).
    if not ci:
        sello = SELLO_DIR / f"{elegido.stem}.antes.json"
        if not sello.exists():
            msg = (f"no hay sello de lectura previa ({sello.name}): la lectura "
                   "no puede probarse anterior al código. Ejecutá --leer antes "
                   "de codificar.")
            if exigir_sello:
                errores.append(msg)
            else:
                avisos.append(msg)
        else:
            # Frescura del sello: siempre se valida si existe (expiración,
            # fecha futura, sello emitido sobre código ya existente).
            errores.extend(sello_previo_a_cambio(sello, prod))
    else:
        # CI: la evidencia del cambio (oráculos ejecutados, expediente, huella)
        # debe estar COMITEADA en HEAD y corresponder a este cambio_hash.
        errores.extend(evidencia_ci_ok(ch))

    # (3) citas muertas: `cumple Manual X §Y` cuya sección ya no existe.
    #        - si el diff toca los manuales -> revalida TODO el repo (la ley cambió)
    #        - si no -> solo los archivos del diff (la deuda heredada va a DEUDA.md)
    manual_tocado = [f for f in archivos
                     if f.startswith("docs/manuales/") or f.endswith(".indice.json")]
    muertas = {}
    if manual_tocado:
        for c in citas_muertas_repo(indice):
            muertas[(c["archivo"], c["linea"])] = c
    else:
        for ruta in prod:
            for c in citas_de_archivo(ruta):
                if not im.buscar_seccion(indice, c["manual"], c["seccion"]):
                    muertas[(ruta, c["linea"])] = c
    if muertas:
        por_archivo = {}
        for (arch, num), c in sorted(muertas.items()):
            por_archivo.setdefault(arch, []).append((num, c))
        afectados = [a for a in por_archivo if a in prod]
        # Toda cita muerta en un archivo DEL CAMBIO debe quedar declarada.
        for arch in afectados:
            declarada = any(a.get("estado", "").upper() == "DESVIACION"
                            and (a.get("correccion") or a.get("decision"))
                            for a in exp["archivos"].get(arch, []))
            if not declarada:
                ejemplo = por_archivo[arch][0]
                errores.append(
                    f"{arch}: {len(por_archivo[arch])} cita(s) `cumple Manual` a "
                    f"secciones inexistentes en el manual vigente (ej. línea "
                    f"{ejemplo[0]} → Manual {ejemplo[1]['manual']} "
                    f"§{ejemplo[1]['seccion'] or '?'}). Re-anclá la cita a una "
                    "sección real o declarala como DESVIACION con "
                    "correccion:/decision:")
        if manual_tocado:
            fuera = [a for a in por_archivo if a not in prod]
            if fuera:
                detalle["citas_muertas_repo"] = len(muertas)
                avisos.append(
                    f"los manuales cambiaron: {len(muertas)} cita(s) del repo "
                    f"quedaron sin sección. {len(afectados)} en archivos de este "
                    f"cambio (bloqueantes) y {sum(len(por_archivo[a]) for a in fuera)} "
                    "en archivos no tocados (deuda heredada, ver "
                    "docs/alineacion/DEUDA.md)")

    rangos = rangos_cambiados(prod, desde) if not ci else {}

    # --- chequeos por ancla ---
    oraculos_pedidos = {}
    for ruta, anclas in exp["archivos"].items():
        if ruta not in prod:
            continue
        for req in requisitos_archivo(ruta, mapa_alineacion, mapa_legacy):
            if not any(cubre(req, a.get("manual", ""), a.get("seccion", ""))
                       for a in anclas):
                errores.append(
                    f"{ruta}: falta ancla para Manual {req[0]} "
                    f"§{req[1] or '(manual entero)'} (exigido por "
                    f"{MAPA_ALINEACION if mapa_alineacion else MAPA_LEGACY})")
        for a in anclas:
            manual, seccion = a.get("manual", ""), a.get("seccion", "")
            estado = a.get("estado", "").upper()
            tipo = (a.get("tipo") or "comportamiento").lower()
            etiqueta = f"{ruta} → Manual {manual} §{seccion or '?'}"
            if estado not in ESTADOS:
                errores.append(f"{etiqueta}: estado inválido {estado!r} "
                               f"(usar {'/'.join(ESTADOS)})")
                continue
            if estado == "PENDIENTE":
                errores.append(f"{etiqueta}: ancla sin completar (estado PENDIENTE)")
                continue
            if tipo not in TIPOS:
                errores.append(f"{etiqueta}: tipo inválido {tipo!r} (usar {'/'.join(TIPOS)})")
                continue
            # (4) la cita debe existir LITERALMENTE en el manual vigente
            ok_cita, msg = im.validar_cita_textual(indice, manual, seccion,
                                                  a.get("cita", ""))
            if not ok_cita:
                errores.append(f"{etiqueta}: {msg}")
            elif a.get("oracion"):
                oid = im.id_de_cita(indice, manual, seccion, a.get("cita", ""))
                if oid and a["oracion"] != oid:
                    errores.append(f"{etiqueta}: oracion_id {a['oracion']} no "
                                   f"corresponde a la cita (esperado {oid})")

            if estado == "CUMPLE":
                # (5) evidencia real en el código
                m = RE_EVIDENCIA.match(a.get("evidencia", ""))
                if not m:
                    errores.append(f"{etiqueta}: CUMPLE sin `evidencia: "
                                   "archivo:linea` válida")
                else:
                    arch_ev = m.group("archivo").replace("\\", "/")
                    linea = int(m.group("l1"))
                    _seccion_pat = re.escape(seccion) if seccion else r'\d'
                    patron = re.compile(
                        rf"cumple\s+Manual\s+{re.escape(manual)}\s*(?:§\s*)?"
                        rf"{_seccion_pat}", re.I)
                    if not (RAIZ / arch_ev).exists():
                        errores.append(f"{etiqueta}: la evidencia apunta a "
                                       f"{arch_ev}, que no existe")
                    elif not contiene_linea(arch_ev, linea, patron):
                        errores.append(
                            f"{etiqueta}: no hay `cumple Manual {manual} "
                            f"§{seccion}` en {arch_ev} ±3 líneas de la línea "
                            f"{linea} (CUMPLE declarado sin ancla en el código)")
                # (6) oráculo obligatorio salvo contrato
                if tipo != "contrato" and not a.get("oraculo"):
                    errores.append(f"{etiqueta}: tipo {tipo} exige `oraculo:`")
                if a.get("oraculo"):
                    oraculos_pedidos[a["oraculo"]] = a.get("ejecucion") or "auto"
            elif estado == "DESVIACION":
                # (7) desviación cerrada: corrección en el diff o decisión D-*
                if a.get("correccion"):
                    m = RE_EVIDENCIA.match(a["correccion"])
                    if not m:
                        errores.append(f"{etiqueta}: `correccion:` inválida "
                                       "(formato archivo:linea o archivo:l1-l2)")
                    else:
                        arch_c = m.group("archivo").replace("\\", "/")
                        l1 = int(m.group("l1"))
                        l2 = int(m.group("l2") or l1)
                        solapa = any(not (l2 < i or l1 > f)
                                     for i, f in rangos.get(arch_c, []))
                        if not solapa:
                            errores.append(
                                f"{etiqueta}: la corrección en {arch_c}:{l1}-{l2} "
                                "no toca ninguna línea del cambio (la desviación "
                                "sigue abierta)")
                elif a.get("decision"):
                    if not _decision_existe(a["decision"]):
                        errores.append(f"{etiqueta}: la decisión {a['decision']} "
                                       "no está ratificada en la bitácora/MEMORIA")
                else:
                    errores.append(f"{etiqueta}: DESVIACION sin `correccion:` "
                                   "ni `decision:` — corregila o registrá la "
                                   "decisión del Arquitecto")

    # (9) oráculos: se ejecutan, no se declaran
    ejecutados = []
    if con_oraculos and oraculos_pedidos:
        detalle["oraculos"] = {}
        for ruta, modo_o in sorted(oraculos_pedidos.items()):
            res = ejecutar_oraculo(ruta, modo_o)
            ejecutados.append(res)
            detalle["oraculos"][ruta] = res["ok"]
            if not res["ok"]:
                errores.append(f"oráculo {ruta}: {res.get('motivo') or 'falló'} "
                               f"({res.get('extracto', '')})")
    elif oraculos_pedidos:
        avisos.append("oráculos declarados pero NO ejecutados (--sin-oraculos)")

    detalle["expediente_ok"] = not errores
    return errores, avisos, detalle


def _decision_existe(codigo):
    """True si D-xxx aparece en la bitácora o en la memoria."""
    for path in (BITACORA, MEMORIA):
        if path.exists() and codigo in path.read_text(encoding="utf-8",
                                                      errors="replace"):
            return True
    return False


def sello_previo_a_cambio(ruta_sello, archivos_prod):
    """El sello debe ser ANTERIOR al código: expira al día siguiente de
    emitirse y debe preceder a la mtime de los archivos del cambio.

    Cierra el hueco del sello eterno: sin esto, un --leer de hace semanas
    (o re-emitido post-hoc) "probaba" la lectura de código escrito después.
    Devuelve lista de errores (vacía = sello creíble).
    """
    errores = []
    try:
        datos = json.loads(ruta_sello.read_text(encoding="utf-8",
                                                errors="replace"))
        fecha_sello = date.fromisoformat(str(datos.get("fecha", ""))[:10])
    except Exception:
        return [f"sello de lectura previa ILEGIBLE o corrupto: {ruta_sello.name}"]
    hoy = date.today()
    if (hoy - fecha_sello).days > 1:
        errores.append(
            f"sello de lectura previa EXPIRADO ({ruta_sello.name}, fecha "
            f"{fecha_sello.isoformat()}): re-ejecutá --leer antes de codificar")
    elif fecha_sello > hoy:
        errores.append(
            f"sello de lectura previa con fecha FUTURA ({ruta_sello.name}) — "
            "no puede probar una lectura anterior")
    else:
        base = str(datos.get("base", "")).strip()
        if base and len(base) >= 7:
            out, rc = _run(["git", "show", "-s", "--format=%ct", base])
            if rc == 0 and out.strip().isdigit():
                t_base = int(out.strip())
                mas_nuevo = None
                for f in archivos_prod:
                    p = RAIZ / f
                    if p.exists():
                        t_arch = int(p.stat().st_mtime)
                        if t_arch < t_base and (mas_nuevo is None
                                                or t_arch < mas_nuevo):
                            mas_nuevo = t_arch
                if mas_nuevo is not None:
                    errores.append(
                        f"sello emitido DESPUÉS de que el código existía "
                        f"({ruta_sello.name} selló sobre base {base[:7]}, pero "
                        "hay archivos del cambio más viejos que ese commit) — "
                        "la lectura no puede probarse anterior al código")
    return errores


def evidencia_ci_ok(cambio_hash):
    """En CI, la evidencia del cambio debe estar COMITEADA en HEAD.

    Endurece la cadena contra --no-verify: el expediente ya se lee de HEAD
    (--ci); aquí se exige además que auditoria/evidencia/<cambio_hash>.json
    exista en HEAD, con el mismo cambio_hash, y sin oráculos fallidos.
    """
    if not cambio_hash:
        return ["cambio_hash vacío: no se puede atar la evidencia del cambio"]
    rel = f"auditoria/evidencia/{cambio_hash}.json"
    out, rc = _run(["git", "show", f"HEAD:{rel}"])
    if rc != 0:
        return [
            f"falta la evidencia COMITEADA del cambio: {rel} — "
            "ejecutá --verificar en local (escribe la evidencia) y commiteala "
            "con el PR"]
    try:
        ev = json.loads(out)
    except json.JSONDecodeError:
        return [f"evidencia comiteada ILEGIBLE: {rel}"]
    errores = []
    if ev.get("cambio_hash") != cambio_hash:
        errores.append(
            f"la evidencia comiteada ({rel}) corresponde a otro cambio_hash "
            f"({ev.get('cambio_hash')}) — re-ejecutá --verificar y commiteala")
    fallidos = [r for r, ok in (ev.get("oraculos") or {}).items() if not ok]
    if fallidos:
        errores.append(
            f"la evidencia comiteada ({rel}) registra oráculos FALLIDOS: "
            + ", ".join(fallidos))
    return errores


def citas_de_archivo(ruta):
    """[(manual, seccion, linea)] de los comentarios `cumple Manual` del archivo."""
    try:
        texto = (RAIZ / ruta).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    salida = []
    for i, linea in enumerate(texto.splitlines(), start=1):
        for m in RE_CITA.finditer(linea):
            salida.append({"manual": m.group(1),
                           "seccion": m.group(2) or "", "linea": i})
    return salida


def citas_muertas_repo(indice):
    """Citas `cumple Manual X §Y` de TODO el repo cuyo § ya no existe."""
    out, _ = _run(["git", "grep", "-n", "-I", "-E", r"cumple +Manual"])
    muertas = []
    for linea in out.splitlines():
        partes = linea.split(":", 2)
        if len(partes) < 3:
            continue
        archivo, num, texto = partes[0], partes[1], partes[2]
        if not es_produccion(archivo):
            continue
        for m in RE_CITA.finditer(texto):
            if not im.buscar_seccion(indice, m.group(1), m.group(2) or ""):
                muertas.append({"archivo": archivo, "linea": int(num),
                                "manual": m.group(1),
                                "seccion": m.group(2) or ""})
    return muertas


# ---------------------------------------------------------------------------
# Comandos
# ---------------------------------------------------------------------------
def _requisitos_de(archivos, indice):
    mapa_alineacion = cargar_mapa(MAPA_ALINEACION)
    mapa_legacy = cargar_mapa(MAPA_LEGACY)
    return {f: requisitos_archivo(f, mapa_alineacion, mapa_legacy)
            for f in archivos}


def cmd_explain(args):
    """Muestra las oraciones normativas que el mapa exige (lectura dirigida)."""
    archivos = [a.strip() for a in args.archivos.split(",") if a.strip()] \
        if args.archivos else archivos_cambio()
    prod = [f for f in archivos if es_produccion(f)]
    if not prod:
        print("[OK] sin archivos de producción: nada que leer")
        return 0
    indice = im.cargar_indice()
    requisitos = _requisitos_de(prod, indice)
    for ruta in prod:
        reqs = requisitos[ruta]
        if not reqs:
            print(f"[FALTA] {ruta} no está en ningún mapa: agregalo a "
                  "docs/gobernancia/mapa_alineacion.md")
            continue
        print(f"\n=== {ruta} ===")
        for manual, seccion in reqs:
            sec = im.buscar_seccion(indice, manual, seccion)
            if not sec:
                print(f"  [FALTA] Manual {manual} §{seccion} no existe en el "
                      "manual vigente (mapa desactualizado)")
                continue
            print(f"  Manual {manual} §{seccion} — {sec['titulo']}")
            for o in im.oraciones_citables(indice, manual, seccion)[:12]:
                print(f"    [{o['id']}] {o['texto']}")
    print("\nCita LITERAL una de estas oraciones en el expediente "
          "(`cita:`), corregí lo que no cumpla y marcá CUMPLE/DESVIACION.")
    return 0


def cmd_leer(args):
    """Fase ANTES: lectura dirigida + sello de lectura previa."""
    rc = cmd_explain(args)
    if rc != 0:
        return rc
    archivos = [a.strip() for a in args.archivos.split(",") if a.strip()] \
        if args.archivos else archivos_cambio()
    prod = [f for f in archivos if es_produccion(f)]
    if not args.me:
        print("[FALTA] --leer exige --me <ME> para sellar la lectura")
        return 1
    SELLO_DIR.mkdir(parents=True, exist_ok=True)
    base, _ = _run(["git", "rev-parse", "HEAD"])
    sello = {"me": args.me, "fecha": date.today().isoformat(),
             "base": base.strip(), "archivos": prod,
             "requisitos": {f: [f"Manual {m} §{s}" for m, s in reqs]
                            for f, reqs in
                            _requisitos_de(prod, im.cargar_indice()).items()}}
    ruta = SELLO_DIR / f"{args.me}.antes.json"
    ruta.write_text(json.dumps(sello, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    print(f"\n[OK] sello de lectura previa: {ruta.name} "
          f"({len(prod)} archivo(s), base {base.strip()[:7]})")
    return 0


def cmd_nuevo(args):
    """Genera el expediente a completar por el agente."""
    if not args.me:
        print("[FALTA] --nuevo exige --me <ME>")
        return 1
    archivos = [a.strip() for a in args.archivos.split(",") if a.strip()] \
        if args.archivos else archivos_cambio()
    prod = [f for f in archivos if es_produccion(f)]
    if not prod:
        print("[OK] sin archivos de producción: no hace falta expediente")
        return 0
    EXPEDIENTES_DIR.mkdir(parents=True, exist_ok=True)
    indice = im.cargar_indice()
    contenido = scaffold_expediente(args.me, prod, _requisitos_de(prod, indice),
                                    indice)
    ruta = ruta_expediente(args.me)
    if ruta.exists() and not args.forzar:
        print(f"[FALTA] {ruta.relative_to(RAIZ)} ya existe (usá --forzar para regenerar)")
        return 1
    ruta.write_text(contenido, encoding="utf-8")
    print(f"[OK] expediente creado: {ruta.relative_to(RAIZ).as_posix()}")
    print("     Completá por ancla: cita literal, tipo, estado, evidencia y oráculo.")
    print(f"     Verificá con: python auditoria/alineacion.py --verificar --me {args.me}")
    return 0


def cmd_baseline(args):
    """Congela la deuda heredada: citas muertas y archivos sin mapa."""
    indice = im.cargar_indice()
    muertas = citas_muertas_repo(indice)
    out, _ = _run(["git", "ls-files"])
    sin_mapa = []
    mapa_alineacion = cargar_mapa(MAPA_ALINEACION)
    mapa_legacy = cargar_mapa(MAPA_LEGACY)
    for f in out.splitlines():
        f = f.replace("\\", "/").strip()
        if es_produccion(f) and not requisitos_archivo(f, mapa_alineacion, mapa_legacy):
            sin_mapa.append(f)
    EXPEDIENTES_DIR.mkdir(parents=True, exist_ok=True)
    lineas = [
        "# DEUDA DE ALINEACIÓN (baseline) — no empeorar",
        "",
        f"Generado: {date.today().isoformat()}",
        "",
        "El gate de alineación solo bloquea lo que el cambio TOCA. Esta lista es",
        "la deuda heredada: no cuenta como brecha, pero ningún cambio nuevo puede",
        "agregar entradas aquí sin declararlas como DESVIACION.",
        "",
        f"## Citas `cumple Manual` a secciones inexistentes ({len(muertas)})",
        "",
    ]
    for c in muertas:
        lineas.append(f"- `{c['archivo']}:{c['linea']}` → Manual {c['manual']} "
                      f"§{c['seccion'] or '?'}")
    lineas += ["", f"## Archivos de producción sin requisito en el mapa "
                   f"({len(sin_mapa)})", ""]
    for f in sin_mapa:
        lineas.append(f"- `{f}`")
    ruta = EXPEDIENTES_DIR / "DEUDA.md"
    ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"[OK] baseline escrito: {ruta.relative_to(RAIZ).as_posix()}")
    print(f"     citas muertas={len(muertas)} archivos sin mapa={len(sin_mapa)}")
    return 0


def cmd_verificar(args):
    """Fase DESPUÉS: valida el cambio contra manual, código y oráculos."""
    if args.archivos:
        archivos = [a.strip().replace("\\", "/")
                    for a in args.archivos.split(",") if a.strip()]
    else:
        archivos = archivos_cambio(args.desde)
    if not archivos:
        print("[OK] sin cambios que verificar")
        return 0
    errores, avisos, detalle = verificar(
        archivos, desde=args.desde, me=args.me, modo=args.modo,
        con_oraculos=not args.sin_oraculos, ci=args.ci,
        exigir_sello=args.exigir_sello)
    for a in avisos:
        print(f"[aviso] {a}")
    if not detalle.get("archivos_produccion"):
        print("[OK] sin cambios de producción: gate de alineación no aplica")
        return 0
    print(f"[i] archivos de producción: {len(detalle['archivos_produccion'])}, "
          f"cambio_hash={detalle.get('cambio_hash')}, "
          f"expediente={detalle.get('expediente', '(ninguno)')}")

    if errores:
        print(f"\n[FALTA] alineación manual↔código: {len(errores)} brecha(s)")
        for e in errores:
            print(f"  - {e}")
        print("\nCorregí el código (o el expediente) y volvé a verificar:")
        print("  python auditoria/alineacion.py --explain   # qué dice el manual")
        print("  python auditoria/alineacion.py --verificar"
              + (f" --me {args.me}" if args.me else ""))
        if args.modo == "warn":
            print("[warn] modo warn: no bloquea")
            return 0
        return 1

    # Evidencia del cambio (solo si pasó o si es warn, para dejar rastro)
    EVIDENCIA_DIR.mkdir(parents=True, exist_ok=True)
    ev_path = EVIDENCIA_DIR / f"{detalle['cambio_hash']}.json"
    ev_path.write_text(json.dumps({
        "cambio_hash": detalle["cambio_hash"],
        "expediente": detalle.get("expediente"),
        "fecha": date.today().isoformat(),
        "archivos": detalle["archivos_produccion"],
        "oraculos": detalle.get("oraculos", {}),
        "citas_muertas_repo": detalle.get("citas_muertas_repo"),
        "modo": args.modo,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    # El expediente se re-sella para que su huella quede atada al contenido
    if args.me:
        ruta = ruta_expediente(args.me)
        if ruta.exists():
            texto = ruta.read_text(encoding="utf-8", errors="replace")
            texto = re.sub(r"^cambio_hash:.*$", f"cambio_hash: {detalle['cambio_hash']}",
                           texto, count=1, flags=re.M)
            ruta.write_text(texto, encoding="utf-8")
    print(f"[OK] alineación verificada: {len(detalle['archivos_produccion'])} "
          f"archivo(s), citas textuales verificadas, "
          f"oráculos={len(detalle.get('oraculos', {}))} ejecutados")
    print(f"[OK] evidencia: {ev_path.relative_to(RAIZ).as_posix()}")
    return 0


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001 - consolas Windows cp1252
        pass
    ap = argparse.ArgumentParser(
        description="Gate de alineación manual↔código (lectura, expediente, verificación)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--indice", action="store_true", help="regenera el índice de manuales")
    g.add_argument("--baseline", action="store_true", help="congela la deuda heredada")
    g.add_argument("--explain", action="store_true", help="muestra los requisitos literales")
    g.add_argument("--leer", action="store_true", help="lectura dirigida + sello (fase ANTES)")
    g.add_argument("--nuevo", action="store_true", help="genera el expediente a completar")
    g.add_argument("--verificar", action="store_true", help="verifica el cambio (fase DESPUÉS)")
    ap.add_argument("--me", default="", help="id del micro-entregable (ME-7, ME-Q1, ...)")
    ap.add_argument("--archivos", default="", help="rutas separadas por coma")
    ap.add_argument("--desde", default="", help="ref git para el diff (modo CI: <base>...HEAD)")
    ap.add_argument("--modo", default="block", choices=["block", "warn"])
    ap.add_argument("--ci", action="store_true",
                    help="lee expediente/evidencia desde HEAD (gate de servidor)")
    ap.add_argument("--sin-oraculos", action="store_true",
                    help="no ejecuta oráculos (solo diagnóstico)")
    ap.add_argument("--exigir-sello", action="store_true",
                    help="BLOQUEA si no hay sello de lectura previa (usado por el "
                         "pre-commit para garantizar leer ANTES de codificar)")
    ap.add_argument("--forzar", action="store_true", help="regenera el expediente")
    args = ap.parse_args()

    if args.indice:
        ind = im.construir_indice()
        path = im.guardar_indice(ind)
        print(f"[OK] índice regenerado: {path.relative_to(RAIZ).as_posix()}")
        return 0
    if args.baseline:
        return cmd_baseline(args)
    if args.explain:
        return cmd_explain(args)
    if args.leer:
        return cmd_leer(args)
    if args.nuevo:
        return cmd_nuevo(args)
    return cmd_verificar(args)


if __name__ == "__main__":
    sys.exit(main())
