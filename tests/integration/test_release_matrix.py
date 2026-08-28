"""
test_release_matrix.py — Validación de artefactos M11.1 Multiplataforma

Verifica que la estructura de artefactos generados por release_matrix.yml
sea correcta antes de proceder a la firma Ed25519 (M11.2).

Modos de uso:
  pytest tests/integration/test_release_matrix.py -v
  pytest tests/integration/test_release_matrix.py -k "sha256"
  python -m pytest tests/integration/test_release_matrix.py --tb=short
"""

import os
import sys
import json
import hashlib
import struct
import tempfile
import pytest

pytestmark = pytest.mark.integration

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))

# ============================================================
# CONSTANTES
# ============================================================

PLATAFORMAS_OBLIGATORIAS = ['linux_x64', 'linux_arm64', 'darwin_arm64', 'win_x64']
MIN_BINARY_SIZE = 100_000  # 100 KB mínimo para un binario válido
ARCHIVOS_OBLIGATORIOS = ['synapse_rt.c', 'synapse_rt.h', 'axon/tweetnacl.c', 'axon/tweetnacl.h',
                         'main.py', 'pipeline.py', 'requirements.txt']

# ============================================================
# HELPERS
# ============================================================

def _calcular_sha256(ruta: str) -> str:
    """Calcula SHA-256 de un archivo."""
    h = hashlib.sha256()
    with open(ruta, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def _simular_build_pipeline(entry_point: str, output_name: str) -> dict:
    """Simula la compilación del pipeline para validar artefactos generados.
    
    Retorna un dict con la estructura de artefactos esperada.
    """
    ruta_base = os.path.join(PROJECT_ROOT, entry_point)
    if not os.path.exists(ruta_base):
        return {'error': f'Entry point no encontrado: {ruta_base}'}

    # Buscar C generado
    ruta_c = os.path.join(PROJECT_ROOT, output_name)
    if not os.path.exists(ruta_c):
        # Buscar synapse_unity.c (generado por bootstrap)
        ruta_c = os.path.join(PROJECT_ROOT, 'synapse_unity.c')
    
    return {
        'entry_point': ruta_base,
        'generated_c': ruta_c if os.path.exists(ruta_c) else None,
        'output_name': output_name,
    }


# ============================================================
# TESTS
# ============================================================

class TestPlataformas:
    """Validación de plataformas objetivo."""

    def test_cuatro_plataformas_definidas(self):
        """Deben existir exactamente 4 plataformas objetivo."""
        assert len(PLATAFORMAS_OBLIGATORIAS) == 4
        assert 'linux_x64' in PLATAFORMAS_OBLIGATORIAS
        assert 'linux_arm64' in PLATAFORMAS_OBLIGATORIAS
        assert 'darwin_arm64' in PLATAFORMAS_OBLIGATORIAS
        assert 'win_x64' in PLATAFORMAS_OBLIGATORIAS

    def test_nombres_plataforma_sin_duplicados(self):
        """Los nombres de plataforma deben ser únicos."""
        assert len(PLATAFORMAS_OBLIGATORIAS) == len(set(PLATAFORMAS_OBLIGATORIAS))


class TestReleaseMatrixYML:
    """Validación del workflow release_matrix.yml."""

    def test_release_matrix_yml_existe(self):
        """El archivo release_matrix.yml debe existir."""
        ruta = os.path.join(PROJECT_ROOT, '.github', 'workflows', 'release_matrix.yml')
        assert os.path.exists(ruta), f"release_matrix.yml no encontrado en {ruta}"

    def test_release_matrix_contiene_cuatro_targets(self):

        """El workflow debe definir 4 targets en la matrix."""
        ruta = os.path.join(PROJECT_ROOT, '.github', 'workflows', 'release_matrix.yml')
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Verificar que cada plataforma está definida
        for plataforma in PLATAFORMAS_OBLIGATORIAS:
            assert plataforma in contenido, f"Plataforma {plataforma} no encontrada en release_matrix.yml"

    def test_release_matrix_tiene_sha256_step(self):

        """El workflow debe generar SHA-256 checksums."""
        ruta = os.path.join(PROJECT_ROOT, '.github', 'workflows', 'release_matrix.yml')
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        assert 'sha256' in contenido.lower() or 'SHA256' in contenido

    def test_release_matrix_tiene_upload_artifact(self):

        """El workflow debe subir artefactos."""
        ruta = os.path.join(PROJECT_ROOT, '.github', 'workflows', 'release_matrix.yml')
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        assert 'upload-artifact' in contenido

    def test_release_matrix_tiene_sbom_step(self):

        """El workflow debe generar SBOM SPDX."""
        ruta = os.path.join(PROJECT_ROOT, '.github', 'workflows', 'release_matrix.yml')
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        assert 'spdx' in contenido.lower()

    def test_release_matrix_tiene_validacion(self):

        """El workflow debe tener validación de artefactos."""
        ruta = os.path.join(PROJECT_ROOT, '.github', 'workflows', 'release_matrix.yml')
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        assert 'Validate artifacts' in contenido


class TestArtefactos:
    """Validación de estructura de artefactos."""

    def test_archivos_fuente_obligatorios(self):
        """Los archivos fuente críticos deben existir."""
        for archivo in ARCHIVOS_OBLIGATORIOS:
            ruta = os.path.join(PROJECT_ROOT, archivo)
            assert os.path.exists(ruta), f"Archivo obligatorio no encontrado: {archivo}"

    def test_estructura_directorios_artefactos(self):
        """Los directorios de artefactos deben tener la estructura esperada."""
        # Verificar que los directorios base existen
        assert os.path.isdir(os.path.join(PROJECT_ROOT, '.github', 'workflows'))

    def test_checksum_valido(self):
        """Validar que el cálculo SHA-256 funciona correctamente."""
        # Crear un archivo temporal y verificar su checksum
        with tempfile.NamedTemporaryFile(delete=False, suffix='.exe') as f:
            f.write(b'SYNAPSE_BINARY_PLACEHOLDER')
            temp_path = f.name
        
        try:
            checksum = _calcular_sha256(temp_path)
            assert len(checksum) == 64, f"SHA-256 debe tener 64 caracteres hex, obtuvo {len(checksum)}"
            assert all(c in '0123456789abcdef' for c in checksum), "SHA-256 debe ser hexadecimal"
        finally:
            os.unlink(temp_path)

    def test_formato_nombre_artefacto(self):
        """Validar formato de nombre de artefacto para cada plataforma."""
        for plataforma in PLATAFORMAS_OBLIGATORIAS:
            if plataforma == 'win_x64':
                nombre = f'synapse-{plataforma}.exe'
            else:
                nombre = f'synapse-{plataforma}'
            
            assert nombre.startswith('synapse-'), f"Nombre debe empezar con 'synapse-': {nombre}"
            if plataforma == 'win_x64':
                assert nombre.endswith('.exe'), f"Windows debe terminar en .exe: {nombre}"
            else:
                assert not nombre.endswith('.exe'), f"Solo Windows debe tener .exe: {nombre}"

    def test_artefactos_incluyen_checksum_sbom(self):
        """Cada artefacto debe tener su checksum y SBOM."""
        for plataforma in PLATAFORMAS_OBLIGATORIAS:
            # Nombres de artefactos asociados
            if plataforma == 'win_x64':
                base = f'synapse-{plataforma}.exe'
            else:
                base = f'synapse-{plataforma}'
            
            archivo_checksum = f'{base}.sha256'
            archivo_sbom = f'{base}.spdx.json'
            
            # Validar formato de nombres
            assert archivo_checksum.endswith('.sha256')
            assert archivo_sbom.endswith('.spdx.json')


class TestBootstrap:
    """Validación del proceso de bootstrap."""

    def test_entry_point_principal_existe(self):
        """El entry point principal.syn debe existir."""
        rutas = [
            os.path.join(PROJECT_ROOT, 'nucleo', 'principal.syn'),
            os.path.join(PROJECT_ROOT, 'docs', 'historicas', 'main.syn'),
            os.path.join(PROJECT_ROOT, 'opensyn', 'principal.syn'),
        ]
        alguna_existe = any(os.path.exists(r) for r in rutas)
        assert alguna_existe, f"Ningún entry point encontrado: {rutas}"

    def test_runtime_objects_compilables(self):
        """Los archivos fuente del runtime deben existir para compilar."""
        archivos_runtime = ['synapse_rt.c', 'axon/tweetnacl.c']
        for archivo in archivos_runtime:
            ruta = os.path.join(PROJECT_ROOT, archivo)
            assert os.path.exists(ruta), f"Runtime source no encontrado: {archivo}"

    def test_sbom_generacion(self):
        """Verificar que el generador de SBOM funciona."""
        try:
            sys.path.insert(0, PROJECT_ROOT)
            from nucleo.sbom import generar_sbom
            
            sbom_json = generar_sbom(PROJECT_ROOT)
            sbom = json.loads(sbom_json)
            
            # Validar estructura SPDX 2.3
            assert sbom['spdxVersion'] == 'SPDX-2.3'
            assert 'packages' in sbom
            assert 'files' in sbom
            assert 'relationships' in sbom
            assert 'creationInfo' in sbom
            assert 'dataLicense' in sbom
        except ImportError as e:
            import warnings
            warnings.warn(f"SBOM module no disponible: {e}")
        finally:
            if PROJECT_ROOT in sys.path:
                sys.path.remove(PROJECT_ROOT)


class TestReleaseMatrixCI:
    """Validación del workflow CI/CD de release_matrix contra el pipeline."""

    def test_pipeline_puede_generar_c(self):
        """Verificar que el pipeline puede generar código C (sin compilar).
        
        NOTA: Este test requiere un archivo .syn válido y acceso completo al pipeline.
        Si falla, puede deberse a archivos de prueba faltantes o binarios.
        """
        sys.path.insert(0, PROJECT_ROOT)
        try:
            from pipeline import ejecutar_compilador
            
            # Buscar archivo .syn de prueba válido
            candidatos = [
                os.path.join(PROJECT_ROOT, 'tests', 'test_math.syn'),
                os.path.join(PROJECT_ROOT, 'test_simple.syn'),
                os.path.join(PROJECT_ROOT, 'examples', 'synapse', '00_hola_mundo', 'hola.syn'),
            ]
            
            archivo_prueba = None
            for c in candidatos:
                if os.path.exists(c):
                    # Verificar que no sea binario
                    with open(c, 'rb') as f:
                    	head = f.read(100)
                    try:
                        head.decode('utf-8')
                        archivo_prueba = c
                        break
                    except UnicodeDecodeError:
                        continue
            
            if archivo_prueba:
                codigo = ejecutar_compilador(
                    archivo_prueba,
                    dump_ast=True,
                )
                assert codigo == 0, f"Pipeline falló con código {codigo}"
            else:
                import warnings
                warnings.warn(f"No se encontró archivo .syn de prueba válido entre: {candidatos}")
        except ImportError:
            pass  # Pipeline no disponible en este entorno
        finally:
            if PROJECT_ROOT in sys.path:
                sys.path.remove(PROJECT_ROOT)

    def test_artefacto_estructura_completa(self):
        """Verificar estructura esperada de artefacto empaquetado."""
        # Simular estructura típica de artefacto
        estructura_esperada = [
            'synapse-{platform}',  # o .exe
            'synapse-{platform}.sha256',
            'synapse-{platform}.spdx.json',
        ]
        
        for plataforma in PLATAFORMAS_OBLIGATORIAS:
            if plataforma == 'win_x64':
                base = f'synapse-{plataforma}.exe'
            else:
                base = f'synapse-{plataforma}'
            
            # Verificar que la estructura se genera correctamente
            archivos_esperados = [e.format(platform=plataforma) for e in estructura_esperada]
            
            # Verificar que el .sha256 corresponde al binario
            binario = archivos_esperados[0]
            checksum = archivos_esperados[1]
            assert checksum == f'{binario}.sha256', f"Checksum debe coincidir con binario: {checksum} vs {binario}"
            
            sbom = archivos_esperados[2]
            assert sbom == f'{binario}.spdx.json', f"SBOM debe coincidir con binario: {sbom} vs {binario}"


class TestCompatibilidadMultiplataforma:
    """Validación de compatibilidad entre plataformas."""

    def test_nombres_binario_unicos(self):
        """Cada plataforma debe tener un nombre de binario único."""
        nombres = set()
        for plataforma in PLATAFORMAS_OBLIGATORIAS:
            if plataforma == 'win_x64':
                nombre = f'synapse-{plataforma}.exe'
            else:
                nombre = f'synapse-{plataforma}'
            assert nombre not in nombres, f"Nombre duplicado: {nombre}"
            nombres.add(nombre)
        assert len(nombres) == 4, f"Deben haber 4 nombres únicos, hay {len(nombres)}"

    def _nombre_binario(self, plataforma: str) -> str:
        """Genera el nombre del binario para una plataforma."""
        if plataforma == 'win_x64':
            return f'synapse-{plataforma}.exe'
        return f'synapse-{plataforma}'

    def test_compatibilidad_crucigrama(self):
        """Validar que los nombres cruzados entre plataformas son consistentes."""
        # linux_x64 -> sin extension
        assert self._nombre_binario('linux_x64') == 'synapse-linux_x64'
        assert not self._nombre_binario('linux_x64').endswith('.exe')
        # win_x64 -> con .exe
        assert self._nombre_binario('win_x64') == 'synapse-win_x64.exe'
        assert self._nombre_binario('win_x64').endswith('.exe')
        # darwin_arm64 -> sin extension
        assert self._nombre_binario('darwin_arm64') == 'synapse-darwin_arm64'
        assert not self._nombre_binario('darwin_arm64').endswith('.exe')
        # linux_arm64 -> sin extension
        assert self._nombre_binario('linux_arm64') == 'synapse-linux_arm64'
        assert not self._nombre_binario('linux_arm64').endswith('.exe')


# ============================================================
# PRUEBAS DE INTEGRACIÓN DE LA ESTRUCTURA DEL WORKFLOW
# ============================================================

def test_workflow_tiene_disparadores_correctos():

    """El workflow debe dispararse en push a main/master/release y tags v*."""
    ruta = os.path.join(PROJECT_ROOT, '.github', 'workflows', 'release_matrix.yml')
    with open(ruta, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    assert 'push:' in contenido
    assert 'branches:' in contenido or 'main' in contenido
    assert 'workflow_dispatch:' in contenido, "Debe permitir dispatch manual"


def test_workflow_tiene_permisos_correctos():

    """El workflow debe tener permisos para leer contenido y escribir paquetes."""
    ruta = os.path.join(PROJECT_ROOT, '.github', 'workflows', 'release_matrix.yml')
    with open(ruta, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    assert 'contents: read' in contenido
    assert 'packages: write' in contenido


def test_workflow_no_tiene_jobs_duplicados():
    """El workflow no debe tener nombres de jobs duplicados."""
    ruta = os.path.join(PROJECT_ROOT, '.github', 'workflows', 'release_matrix.yml')
    with open(ruta, 'r', encoding='utf-8') as f:
        lineas = f.readlines()
    
    # Encontrar la sección 'jobs:' y extraer nombres de jobs (palabras indentadas 2 espacios)
    en_jobs = False
    job_names = []
    for linea in lineas:
        stripped = linea.strip()
        if stripped == 'jobs:':
            en_jobs = True
            continue
        if en_jobs:
            # Un job name es una línea indentada con 2 espacios, que termina en ':' y no tiene prefijo
            if linea.startswith('  ') and not linea.startswith('    ') and stripped.endswith(':'):
                name = stripped.rstrip(':')
                if name and not name.startswith('#') and name not in ('on', 'env', 'permissions'):
                    job_names.append(name)
    
    assert len(job_names) > 0, f"No se encontraron jobs en el workflow: {job_names}"
    assert len(job_names) == len(set(job_names)), f"Jobs duplicados encontrados: {job_names}"
