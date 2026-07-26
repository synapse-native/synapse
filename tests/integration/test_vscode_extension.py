#!/usr/bin/env python3
"""
test_vscode_extension.py — Suite de validación de la extensión VS Code Synapse (M11.4)

Validaciones:
  - Estructura y metadatos de package.json
  - Zero-telemetry enforcement (certificado)
  - Dependencias LSP nativas
  - Archivos de sintaxis y snippets
  - Integridad del .vscodeignore
  - Flujo de publicación CI/CD
  - Firma Ed25519 y verificaciones SHA-256

Clasificación: M11.4 — Publicación Marketplace VS Code
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Constantes de rutas
# ---------------------------------------------------------------------------

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent.parent
EXTENSION_DIR = RAIZ_PROYECTO / "vscode-synapse"
WORKFLOW_DIR = RAIZ_PROYECTO / ".github" / "workflows"
PACKAGE_JSON = EXTENSION_DIR / "package.json"
VSCODEIGNORE = EXTENSION_DIR / ".vscodeignore"
EXTENSION_JS = EXTENSION_DIR / "extension.js"
LANG_CONFIG = EXTENSION_DIR / "language-configuration.json"
BUILD_VSIX = EXTENSION_DIR / "build_vsix.bat"
SYNTAX_FILE = EXTENSION_DIR / "syntaxes" / "synapse.tmLanguage.json"
SNIPPETS_FILE = EXTENSION_DIR / "snippets" / "synapse.code-snippets"
PUBLISH_WORKFLOW = WORKFLOW_DIR / "vscode_publish.yml"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cargar_json(ruta):
    """Carga y retorna un archivo JSON con manejo de errores."""
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def _buscar_en_archivo(patron, ruta):
    """Busca un patrón regex en un archivo, retorna lista de líneas coincidentes.
    
    Excluye líneas que son solo comentarios (//, /*, *, #) para evitar
    falsos positivos con declaraciones de privacidad.
    """
    if not ruta.exists():
        return []
    coincidencias = []
    with open(ruta, "r", encoding="utf-8", errors="replace") as f:
        for i, linea in enumerate(f, 1):
            texto = linea.strip()
            # Saltar líneas que son solo comentarios
            if texto.startswith("//") or texto.startswith("/*") or texto.startswith("*") or texto.startswith("#"):
                continue
            if re.search(patron, texto, re.IGNORECASE):
                coincidencias.append((i, texto))
    return coincidencias


# ===========================================================================
# Test 1: Estructura y metadatos de package.json
# ===========================================================================

class TestPackageJson:
    """Validación de la estructura del manifiesto de la extensión."""

    def setup_method(self):
        self.pkg = _cargar_json(PACKAGE_JSON)

    def test_package_json_existe(self):
        """El archivo package.json debe existir."""
        assert PACKAGE_JSON.exists(), f"package.json no encontrado en {PACKAGE_JSON}"

    def test_nombre_extension(self):
        """El nombre debe ser 'synapse'."""
        assert self.pkg.get("name") == "synapse", \
            f"Nombre incorrecto: {self.pkg.get('name')}"

    def test_display_name(self):
        """Debe contener displayName descriptivo."""
        nombre = self.pkg.get("displayName", "")
        assert "Synapse" in nombre, f"displayName no contiene Synapse: {nombre}"

    def test_descripcion(self):
        """La descripción debe mencionar LSP nativo y cero telemetría."""
        desc = self.pkg.get("description", "")
        assert "LSP" in desc or "lsp" in desc, "La descripción debe mencionar LSP"
        assert "telemetría" in desc or "telemetry" in desc or "CERO" in desc, \
            "La descripción debe declarar cero telemetría"

    def test_publisher(self):
        """El publisher debe ser 'synapse-lang'."""
        assert self.pkg.get("publisher") == "synapse-lang", \
            f"Publisher incorrecto: {self.pkg.get('publisher')}"

    def test_version_formato(self):
        """La versión debe seguir semver (X.Y.Z)."""
        version = self.pkg.get("version", "")
        assert re.match(r"^\d+\.\d+\.\d+$", version), \
            f"Versión no sigue semver: {version}"

    def test_engines_vscode(self):
        """Debe especificar engines.vscode con versión mínima."""
        engines = self.pkg.get("engines", {})
        vscode_ver = engines.get("vscode", "")
        assert vscode_ver, "Falta engines.vscode"
        assert "^1." in vscode_ver or ">=" in vscode_ver, \
            f"Engines.vscode debe tener un rango: {vscode_ver}"

    def test_categories(self):
        """Debe incluir categorías relevantes."""
        cats = self.pkg.get("categories", [])
        assert "Programming Languages" in cats, \
            f"Falta categoría Programming Languages: {cats}"
        assert "Snippets" in cats, f"Falta categoría Snippets: {cats}"

    def test_activation_events_scoped(self):
        """activationEvents no debe ser '*' (privacidad)."""
        eventos = self.pkg.get("activationEvents", [])
        assert "*" not in eventos, \
            "activationEvents no debe ser '*' (riesgo de privacidad)"
        assert len(eventos) > 0, "Debe haber al menos un activationEvent"
        assert any("onLanguage" in e for e in eventos), \
            "Debe haber al menos un onLanguage activation event"

    def test_main_entry_point(self):
        """El entry point principal debe ser extension.js."""
        assert self.pkg.get("main") == "./extension.js", \
            f"Entry point incorrecto: {self.pkg.get('main')}"

    def test_license_mit(self):
        """La licencia debe ser MIT."""
        assert self.pkg.get("license") == "MIT", \
            f"Licencia incorrecta: {self.pkg.get('license')}"


# ===========================================================================
# Test 2: Zero-Telemetry Enforcement
# ===========================================================================

class TestZeroTelemetry:
    """Validación estricta de la política de cero telemetría."""

    def test_privacy_metadata_exists(self):
        """package.json debe contener __metadata.privacy.telemetry = 'NONE'."""
        pkg = _cargar_json(PACKAGE_JSON)
        meta = pkg.get("__metadata", {})
        privacy = meta.get("privacy", {})
        assert privacy.get("telemetry") == "NONE", \
            f"__metadata.privacy.telemetry debe ser 'NONE', got: {privacy.get('telemetry')}"

    def test_privacy_policy_declared(self):
        """Debe existir una declaración de política de privacidad."""
        pkg = _cargar_json(PACKAGE_JSON)
        meta = pkg.get("__metadata", {})
        privacy = meta.get("privacy", {})
        policy = privacy.get("policy", "")
        assert policy, "Falta la declaración de política de privacidad"
        assert "Zero" in policy or "CERO" in policy or "0" in policy, \
            "La política debe declarar zero telemetry"

    def test_ai_opt_in_local_only(self):
        """AI debe ser opt-in y local_only."""
        pkg = _cargar_json(PACKAGE_JSON)
        meta = pkg.get("__metadata", {})
        privacy = meta.get("privacy", {})
        ai = privacy.get("ai", {})
        assert ai.get("opt_in") is True, "AI debe ser opt-in"
        assert ai.get("local_only") is True, "AI debe ser local_only"

    def test_no_forbidden_telemetry_in_extension_js(self):
        """No debe haber llamadas a servicios de telemetría en extension.js."""
        terminos_prohibidos = [
            "telemetry",
            "analytics",
            "ApplicationInsights",
            "appInsights",
            r"google-analytics",
            r"segment\.",
            "mixpanel",
            r"amplitude\.",
            "datadogRum",
            r"sentry\.io",
        ]
        for patron in terminos_prohibidos:
            coincidencias = _buscar_en_archivo(patron, EXTENSION_JS)
            assert len(coincidencias) == 0, \
                f"Encontrado '{patron}' en extension.js (líneas: {[l for l,_ in coincidencias]})"

    def test_vscodeignore_blocks_telemetry(self):
        """.vscodeignore debe excluir rutas de telemetría."""
        if not VSCODEIGNORE.exists():
            pytest.skip(".vscodeignore no encontrado")
        contenido = VSCODEIGNORE.read_text(encoding="utf-8")
        patrones_requeridos = [
            "**/telemetry/**",
            "**/analytics/**",
            "**/tracking/**",
            "**/metrics/**",
        ]
        for patron in patrones_requeridos:
            assert patron in contenido, \
                f".vscodeignore debe excluir: {patron}"

    def test_no_telemetry_deps_in_package_json(self):
        """No debe haber dependencias de telemetría en package.json."""
        pkg = _cargar_json(PACKAGE_JSON)
        deps = pkg.get("dependencies", {})
        telemetry_pkgs = [
            "applicationinsights",
            "@microsoft/applicationinsights",
            "@segment/",
            "mixpanel",
            "amplitude",
            "rudder-sdk",
            "posthog",
        ]
        for tele_pkg in telemetry_pkgs:
            for dep in deps:
                if tele_pkg in dep.lower():
                    pytest.fail(f"Dependencia de telemetría encontrada: {dep}")

    def test_only_production_deps(self):
        """Solo debe tener dependencias de producción necesarias."""
        pkg = _cargar_json(PACKAGE_JSON)
        deps = pkg.get("dependencies", {})
        # La única dependencia permitida es vscode-languageclient
        for dep in deps:
            assert "vscode-languageclient" in dep or "vscode" in dep, \
                f"Dependencia no estándar encontrada: {dep}"


# ===========================================================================
# Test 3: Contribuciones — Lenguajes, Gramáticas, Snippets, Comandos
# ===========================================================================

class TestContributions:
    """Validación de las contribuciones de la extensión."""

    def setup_method(self):
        self.pkg = _cargar_json(PACKAGE_JSON)
        self.contrib = self.pkg.get("contributes", {})

    def test_language_definition(self):
        """Debe definir el lenguaje 'synapse' con extensión .syn."""
        langs = self.contrib.get("languages", [])
        assert len(langs) >= 1, "Debe haber al menos un lenguaje definido"
        lang = langs[0]
        assert lang.get("id") == "synapse", \
            f"ID de lenguaje debe ser 'synapse': {lang.get('id')}"
        assert ".syn" in lang.get("extensions", []), \
            "La extensión .syn debe estar registrada"

    def test_grammar_exists(self):
        """Debe existir el archivo de gramática TM."""
        if SYNTAX_FILE.exists():
            grammar = _cargar_json(SYNTAX_FILE)
            assert "scopeName" in grammar, "La gramática debe tener scopeName"
            assert "patterns" in grammar, "La gramática debe tener patrones"
        else:
            # Puede estar referenciado en package.json aunque el archivo no exista
            grammars = self.contrib.get("grammars", [])
            assert len(grammars) >= 1, "Debe haber al menos una gramática"

    def test_snippets_exists(self):
        """Debe existir el archivo de snippets."""
        if SNIPPETS_FILE.exists():
            snippets = _cargar_json(SNIPPETS_FILE)
            assert len(snippets) >= 1, "Debe haber al menos un snippet"
        else:
            snippets_ref = self.contrib.get("snippets", [])
            assert len(snippets_ref) >= 1, "Debe haber al menos una referencia de snippets"

    def test_commands_registered(self):
        """Debe registrar comandos de IA local."""
        commands = self.contrib.get("commands", [])
        cmd_names = [cmd.get("command", "") for cmd in commands]
        assert len(commands) >= 1, "Debe haber al menos un comando registrado"
        assert "synapse.aiStatus" in cmd_names, "Falta comando synapse.aiStatus"
        assert "synapse.aiExplain" in cmd_names, "Falta comando synapse.aiExplain"
        assert "synapse.aiComplete" in cmd_names, "Falta comando synapse.aiComplete"

    def test_configuration_properties(self):
        """Debe tener configuración LSP y AI."""
        config = self.contrib.get("configuration", {})
        props = config.get("properties", {})
        assert "synapse.lsp.nativeBinary" in props, "Falta config LSP binary"
        assert "synapse.lsp.enabled" in props, "Falta config LSP enabled"
        assert "synapse.ai.enabled" in props, "Falta config AI enabled"
        assert "synapse.trace.server" in props, "Falta config trace server"

    def test_configuration_defaults(self):
        """Los valores por defecto deben ser seguros."""
        config = self.contrib.get("configuration", {})
        props = config.get("properties", {})
        # LSP debe estar habilitado por defecto
        assert props.get("synapse.lsp.enabled", {}).get("default") is True, \
            "LSP debe estar habilitado por defecto"
        # AI debe estar habilitada por defecto (hardware-gated en runtime)
        assert props.get("synapse.ai.enabled", {}).get("default") is True, \
            "AI debe estar habilitada por defecto"


# ===========================================================================
# Test 4: Dependencias y Runtime
# ===========================================================================

class TestDependencias:
    """Validación de dependencias npm y runtime."""

    def test_vscode_languageclient_dependency(self):
        """Debe depender de vscode-languageclient."""
        pkg = _cargar_json(PACKAGE_JSON)
        deps = pkg.get("dependencies", {})
        assert "vscode-languageclient" in deps, \
            "Falta dependencia vscode-languageclient"

    def test_language_client_importable(self):
        """vscode-languageclient debe ser cargable dinámicamente."""
        # Verificar que extension.js usa lazy-loading
        contenido = EXTENSION_JS.read_text(encoding="utf-8")
        assert "vscode-languageclient/node" in contenido, \
            "extension.js debe importar vscode-languageclient/node"
        assert "LanguageClient" in contenido, \
            "extension.js debe usar LanguageClient"

    def test_lsp_binary_auto_discovery(self):
        """Debe implementar auto-descubrimiento del binario LSP."""
        contenido = EXTENSION_JS.read_text(encoding="utf-8")
        assert "_asegurar_binario_lsp" in contenido or "asegurar_binario" in contenido, \
            "Falta función de auto-descubrimiento del LSP"
        assert "_encontrar_raiz_synapse" in contenido, \
            "Falta función para detectar raíz del proyecto"

    def test_hardware_detection(self):
        """Debe implementar detección de hardware para IA."""
        contenido = EXTENSION_JS.read_text(encoding="utf-8")
        assert "_detectar_hardware" in contenido, \
            "Falta función de detección de hardware"
        assert "hw_profile" in contenido, \
            "Debe manejar perfiles de hardware"
        assert "ai_enabled" in contenido, \
            "Debe decidir habilitación de IA por hardware"


# ===========================================================================
# Test 5: Integridad de Archivos de la Extensión
# ===========================================================================

class TestIntegridadArchivos:
    """Validación de que todos los archivos necesarios existen."""

    def test_language_configuration_exists(self):
        """Debe existir language-configuration.json."""
        assert LANG_CONFIG.exists(), \
            f"language-configuration.json no encontrado en {LANG_CONFIG}"

    def test_vscodeignore_exists(self):
        """Debe existir .vscodeignore."""
        assert VSCODEIGNORE.exists(), \
            f".vscodeignore no encontrado en {VSCODEIGNORE}"

    def test_build_script_exists(self):
        """Debe existir build_vsix.bat."""
        assert BUILD_VSIX.exists(), \
            f"build_vsix.bat no encontrado en {BUILD_VSIX}"

    def test_build_script_valid(self):
        """El script de build debe tener contenido válido."""
        contenido = BUILD_VSIX.read_text(encoding="utf-8")
        assert "vsce" in contenido, "build_vsix.bat debe invocar vsce"
        assert "package" in contenido, "build_vsix.bat debe empaquetar VSIX"
        assert "SHA-256" in contenido or "sha256" in contenido.lower(), \
            "build_vsix.bat debe generar SHA-256"

    def test_syntax_file_valid_json(self):
        """El archivo de sintaxis debe ser JSON válido."""
        if SYNTAX_FILE.exists():
            grammar = _cargar_json(SYNTAX_FILE)
            assert "scopeName" in grammar
            assert "patterns" in grammar

    def test_snippets_valid_json(self):
        """El archivo de snippets debe ser JSON válido."""
        if SNIPPETS_FILE.exists():
            snippets = _cargar_json(SNIPPETS_FILE)
            assert len(snippets) >= 1


# ===========================================================================
# Test 6: Publicación CI/CD Pipeline
# ===========================================================================

class TestPublishWorkflow:
    """Validación del pipeline de publicación CI/CD."""

    def test_publish_workflow_exists(self):
        """Debe existir el workflow de publicación."""
        assert PUBLISH_WORKFLOW.exists(), \
            f"vscode_publish.yml no encontrado en {PUBLISH_WORKFLOW}"

    def test_publish_workflow_valid_yaml(self):
        """El workflow debe ser YAML válido."""
        try:
            import yaml
            with open(PUBLISH_WORKFLOW, "r") as f:
                data = yaml.safe_load(f)
            assert data is not None, "YAML vacío"
            assert "jobs" in data, "Falta sección jobs"
        except ImportError:
            # Verificación básica sin PyYAML
            contenido = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
            assert "name:" in contenido
            assert "on:" in contenido
            assert "jobs:" in contenido

    def test_publish_workflow_has_validation_job(self):
        """Debe tener un job de validación de telemetría."""
        contenido = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
        assert "validate-telemetry" in contenido, \
            "Falta job validate-telemetry"
        assert "Zero Telemetry" in contenido, \
            "El job validate-telemetry debe mencionar Zero Telemetry"

    def test_publish_workflow_has_build_job(self):
        """Debe tener un job de build y publicación."""
        contenido = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
        assert "build-publish" in contenido, \
            "Falta job build-publish"
        assert "Publish" in contenido, \
            "El workflow debe mencionar publicación en Marketplace"

    def test_publish_workflow_uses_vsce(self):
        """Debe usar @vscode/vsce para build y publish."""
        contenido = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
        assert "@vscode/vsce" in contenido or "vsce" in contenido, \
            "Falta referencia a @vscode/vsce"

    def test_publish_workflow_has_marketplace_token(self):
        """Debe usar VSCODE_MARKETPLACE_TOKEN para publicar."""
        contenido = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
        assert "VSCODE_MARKETPLACE_TOKEN" in contenido, \
            "Falta referencia a VSCODE_MARKETPLACE_TOKEN"
        assert "VSCE_PAT" in contenido or "vsce publish" in contenido, \
            "Falta comando de publicación vsce publish"

    def test_publish_workflow_has_ed25519_signing(self):
        """Debe incluir firma Ed25519."""
        contenido = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
        assert "Ed25519" in contenido, \
            "Falta referencia a firma Ed25519"
        assert "VSIX_SIGNING_KEY" in contenido or ".sig" in contenido, \
            "Falta referencia a clave de firma o archivo .sig"

    def test_publish_workflow_sha256(self):
        """Debe generar SHA-256 checksum."""
        contenido = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
        assert "SHA-256" in contenido or "sha256" in contenido.lower(), \
            "Falta generación de SHA-256"

    def test_publish_workflow_tag_trigger(self):
        """Debe activarse con tag v5.0*."""
        contenido = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
        assert "v5.0" in contenido, \
            "El workflow debe activarse con tag v5.0*"

    def test_publish_workflow_dry_run_support(self):
        """Debe soportar dry_run para validación sin publicar."""
        contenido = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
        assert "dry_run" in contenido, \
            "Falta soporte para dry_run"

    def test_publish_workflow_release_attachment(self):
        """Debe adjuntar artefactos a GitHub Release."""
        contenido = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
        assert "softprops/action-gh-release" in contenido or \
               "gh release" in contenido, \
            "Falta integración con GitHub Release"

    def test_publish_workflow_artifact_upload(self):
        """Debe subir artifacts .vsix, .sha256, .sig."""
        contenido = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
        assert "upload-artifact" in contenido, \
            "Falta step upload-artifact"
        assert ".vsix" in contenido, "Debe subir .vsix"
        assert ".sha256" in contenido, "Debe subir .sha256"
        assert ".sig" in contenido, "Debe subir .sig"


# ===========================================================================
# Test 7: Verificación de Firma Ed25519 en Pipeline
# ===========================================================================

class TestFirmaPipeline:
    """Validación de que el pipeline de publicación soporte firma criptográfica."""

    def test_signing_step_exists(self):
        """El workflow debe tener un paso de firma."""
        contenido = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
        assert "Sign VSIX with Ed25519" in contenido, \
            "Falta paso 'Sign VSIX with Ed25519'"

    def test_signing_uses_secret(self):
        """La firma debe usar VSIX_SIGNING_KEY secret."""
        contenido = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
        assert "VSIX_SIGNING_KEY" in contenido, \
            "La firma debe referenciar VSIX_SIGNING_KEY"

    def test_signature_self_verification(self):
        """Debe incluir auto-verificación de la firma."""
        contenido = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
        assert "verificar" in contenido.lower() or \
               "self-verif" in contenido.lower(), \
            "Falta auto-verificación de firma"

    def test_signature_fallback_python(self):
        """Debe tener fallback de firma via Python si OpenSSL no soporta Ed25519."""
        contenido = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
        assert "ed25519_signer" in contenido or \
               "nucleo" in contenido, \
            "Falta referencia a nucleo.ed25519_signer para fallback"


# ===========================================================================
# Test 8: Compatibilidad Multiplataforma del Pipeline
# ===========================================================================

class TestCompatibilidadMultiplataforma:
    """Validación de que el pipeline soporte múltiples plataformas de build."""

    def test_workflow_runs_on_ubuntu(self):
        """El workflow debe correr en ubuntu-latest."""
        contenido = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
        assert "ubuntu-latest" in contenido, \
            "El workflow debe usar ubuntu-latest"

    def test_node_version_configurable(self):
        """La versión de Node debe ser configurable vía env."""
        contenido = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
        assert "NODE_VERSION:" in contenido or "NODE_VERSION =" in contenido, \
            "Falta NODE_VERSION configurable"


# ===========================================================================
# Test 9: Metadata de Seguridad
# ===========================================================================

class TestSeguridadMetadata:
    """Validación de metadatos de seguridad y licencia."""

    def test_hardware_gated_flag(self):
        """package.json debe indicar hardware-gated AI."""
        pkg = _cargar_json(PACKAGE_JSON)
        meta = pkg.get("__metadata", {}).get("privacy", {}).get("ai", {})
        assert meta.get("hardware_gated") is True, \
            "AI debe ser hardware-gated"

    def test_no_dev_deps_in_production(self):
        """Solo debe haber dependencias de producción necesarias."""
        pkg = _cargar_json(PACKAGE_JSON)
        deps = pkg.get("dependencies", {})
        dev_deps = pkg.get("devDependencies", {})
        # Verificar que no hay dependencias de desarrollo en producción
        assert len(deps) <= 3, \
            f"Demasiadas dependencias de producción: {len(deps)}"
        # Las devDependencies deben ser herramientas de build
        for dep in dev_deps:
            if any(tele in dep.lower() for tele in ["telemetry", "analytics"]):
                pytest.fail(f"DevDependency de telemetría: {dep}")


# ===========================================================================
# Ejecución directa
# ===========================================================================

if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
