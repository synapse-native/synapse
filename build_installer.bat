@echo off
REM build_installer.bat - wrapper raiz (ME-R3)
REM Referenciado por .github/workflows/build-installer.yml y cross-compile.yml
REM (if [ -f build_installer.bat ]). Delega en el script real en scripts/.
call "%~dp0scripts\build_installer.bat"
exit /b %errorlevel%
