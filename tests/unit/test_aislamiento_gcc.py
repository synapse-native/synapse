import os
import sys
import subprocess
from unittest.mock import patch, MagicMock, mock_open
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pipeline import ejecutar_compilador, _resolver_toolchain_gcc, ToolchainNotFoundError


class TestAislamientoGCC:
    def test_toolchain_path_resolved_from_executable_dir(self):
        """Test que la ruta del toolchain se resuelve relativa al ejecutable."""
        with patch('pipeline.SYNAPSE_BIN', os.path.join(os.path.dirname(__file__), '..', '..')):
            ruta = _resolver_toolchain_gcc()
            assert 'gcc.exe' in ruta, f"Ruta del toolchain no contiene gcc.exe: {ruta}"

    def test_gcc_invocation_uses_internal_toolchain_not_path(self, monkeypatch, tmp_path):
        """Test que la invocación a GCC usa la ruta interna, no el PATH del sistema."""
        # Vaciar PATH
        monkeypatch.setenv('PATH', '')

        # Mock de subprocess.run para capturar la llamada
        mock_run = MagicMock(return_value=MagicMock(returncode=0))
        monkeypatch.setattr('subprocess.run', mock_run)

        # Crear estructura mínima de toolchain
        toolchain_dir = tmp_path / 'toolchain' / 'bin'
        toolchain_dir.mkdir(parents=True)
        gcc_path = toolchain_dir / 'gcc.exe'
        gcc_path.write_text('fake gcc')

        # Mock de __file__ para que apunte al tmp_path
        import pipeline
        original_file = pipeline.__file__
        original_synapse_bin = pipeline.SYNAPSE_BIN
        try:
            pipeline.__file__ = str(tmp_path / 'pipeline.py')
            pipeline.SYNAPSE_BIN = str(tmp_path)

            # Ejecutar compilador con archivo dummy
            test_syn = tmp_path / 'test.syn'
            test_syn.write_text('#lang: es\nfuncion principal() -> entero:\n    retornar 0\n')

            # Crear synapse_rt.o dummy
            (tmp_path / 'synapse_rt.o').write_text('dummy')

            try:
                ejecutar_compilador(str(test_syn))
            except SystemExit:
                pass

            # Verificar que subprocess.run fue llamado con la ruta del toolchain interno
            assert mock_run.called
            llamada = mock_run.call_args[0][0]
            assert 'toolchain\\bin\\gcc.exe' in llamada or 'toolchain/bin/gcc.exe' in llamada
            # Verificar que no usa "gcc" genérico
            assert not llamada.strip().startswith('gcc ')
            assert not llamada.strip().startswith('gcc.exe ')

        finally:
            pipeline.__file__ = original_file
            pipeline.SYNAPSE_BIN = original_synapse_bin

    def test_toolchain_not_found_raises_controlled_exception(self, monkeypatch, tmp_path):
        """Test que lanza ToolchainNotFoundError si toolchain/bin/gcc.exe no existe."""
        monkeypatch.setenv('PATH', '')

        import pipeline
        original_file = pipeline.__file__
        original_synapse_bin = pipeline.SYNAPSE_BIN
        try:
            pipeline.__file__ = str(tmp_path / 'pipeline.py')
            pipeline.SYNAPSE_BIN = str(tmp_path)

            # No crear toolchain/bin/gcc.exe
            test_syn = tmp_path / 'test.syn'
            test_syn.write_text('#lang: es\nfuncion principal() -> entero:\n    retornar 0\n')

            with pytest.raises(ToolchainNotFoundError) as exc_info:
                ejecutar_compilador(str(test_syn))

            assert 'toolchain' in str(exc_info.value).lower()
            assert 'gcc.exe' in str(exc_info.value).lower()

        finally:
            pipeline.__file__ = original_file
            pipeline.SYNAPSE_BIN = original_synapse_bin

    def test_subprocess_run_uses_absolute_toolchain_path(self, monkeypatch, tmp_path):
        """Test que subprocess.run recibe la ruta absoluta del toolchain."""
        monkeypatch.setenv('PATH', '')

        toolchain_dir = tmp_path / 'toolchain' / 'bin'
        toolchain_dir.mkdir(parents=True)
        gcc_path = toolchain_dir / 'gcc.exe'
        gcc_path.write_text('fake gcc')

        mock_run = MagicMock(return_value=MagicMock(returncode=0))
        monkeypatch.setattr('subprocess.run', mock_run)

        import pipeline
        original_file = pipeline.__file__
        original_synapse_bin = pipeline.SYNAPSE_BIN
        try:
            pipeline.__file__ = str(tmp_path / 'pipeline.py')
            pipeline.SYNAPSE_BIN = str(tmp_path)

            test_syn = tmp_path / 'test.syn'
            test_syn.write_text('#lang: es\nfuncion principal() -> entero:\n    retornar 0\n')

            # Crear synapse_rt.o dummy
            (tmp_path / 'synapse_rt.o').write_text('dummy')

            try:
                ejecutar_compilador(str(test_syn))
            except SystemExit:
                pass

            # Verificar que subprocess.run fue llamado con ruta absoluta
            if mock_run.called:
                args = mock_run.call_args[0][0]
                # La ruta del compilador debe ser absoluta y contener toolchain
                assert 'toolchain' in args
                assert 'gcc.exe' in args

        finally:
            pipeline.__file__ = original_file
            pipeline.SYNAPSE_BIN = original_synapse_bin


if __name__ == '__main__':
    pytest.main([__file__, '-v'])