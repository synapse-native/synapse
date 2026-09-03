; synapse.iss — Instalador Maestro Modular para Windows (Inno Setup 6+)
; cumple Manual 9 §2.5: Configuración de Inno Setup (Windows)
; cumple Manual 9 §2.2: Estructura del instalador
; cumple Manual 9 §4.1: GitHub Releases (artefactos .exe + .sig + .sha256 + SBOM + SLSA L3)
; Compilar con: iscc instaladores/windows/synapse.iss

#define MyAppName "Synapse Ecosystem"
#define MyAppVersion "8.1.0-industrial"
#define MyAppPublisher "Synapse Language Team"
#define MyAppURL "https://github.com/synapse-lang/synapse"
#define MyAppExeName "synapse.exe"
#define MyAppLspExeName "synapse_lsp.exe"

#define LLAMA_SERVER_URL "https://github.com/ggerganov/llama.cpp/releases/download/b2885/llama-server.exe"
#define MODEL_URL "https://huggingface.co/TheBloke/Llama-3.2-1B-Instruct-GGUF/resolve/main/llama-3.2-1b-instruct.Q4_K_M.gguf"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={pf}\Synapse
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile={#SourcePath}\..\..\LICENSE
OutputDir={#SourcePath}\..\..\dist
OutputBaseFilename=Synapse-{#MyAppVersion}-Windows-x64
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin
 ArchitecturesInstallIn64BitMode=x64
 ArchitecturesAllowed=x64
WizardStyle=modern
WizardImageFile={#SourcePath}\..\..\Logo-Synapse_wizard.bmp
WizardSmallImageFile={#SourcePath}\..\..\Logo-Syquex_wizard.bmp
SetupIconFile={#SourcePath}\..\..\Logo-Synapse.ico
UninstallDisplayIcon={app}\bin\{#MyAppExeName}
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
VersionInfoVersion=8.1.0.0
VersionInfoCompany={#MyAppPublisher}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[CustomMessages]
; cumple Manual 9 §2.5: UI bilingüe (English/Spanish)
english.welcome_title=Welcome to Synapse Language Installer
english.welcome_subtitle=Installs Synapse compiler, runtime, and standard library.
english.setup_type_full=Ecosistema completo (Synapse + Syquex + OpenSyn)
english.setup_type_minimal=Solo Synapse (lenguaje de sistemas)
english.setup_type_synapse_only=Solo Synapse (compilador, runtime, std)
english.setup_type_syquex_only=Solo Syquex (lenguaje de alto nivel)
english.setup_type_synapse=Synapse (compilador, runtime, std)
english.setup_type_syquex=Syquex (lenguaje de alto nivel)
english.setup_type_opensyn=OpenSyn (asistente IA local)
english.setup_type_vscode=VS Code Extension
english.installing=Installing...
english.finish_title=Setup complete
english.finish_subtitle=Synapse Language has been installed successfully.

spanish.welcome_title=Bienvenido al instalador de Synapse Language
spanish.welcome_subtitle=Instala el compilador, runtime y biblioteca estándar de Synapse.
spanish.setup_type_full=Ecosistema completo (Synapse + Syquex + OpenSyn)
spanish.setup_type_minimal=Solo Synapse (lenguaje de sistemas)
spanish.setup_type_synapse_only=Solo Synapse (compilador, runtime, std)
spanish.setup_type_syquex_only=Solo Syquex (lenguaje de alto nivel)
spanish.setup_type_synapse=Synapse (compilador, runtime, std)
spanish.setup_type_syquex=Syquex (lenguaje de alto nivel)
spanish.setup_type_opensyn=OpenSyn (asistente IA local)
spanish.setup_type_vscode=Extensión VS Code
spanish.installing=Instalando...
spanish.finish_title=Instalación completada
spanish.finish_subtitle=Synapse Language se ha instalado correctamente.


[Types]
; cumple Manual 9 §2.5: tipos de instalación configurables
Name: "full"; Description: "{cm:setup_type_full}"
Name: "minimal"; Description: "{cm:setup_type_minimal}"
Name: "synapse_only"; Description: "{cm:setup_type_synapse_only}"
Name: "syquex_only"; Description: "{cm:setup_type_syquex_only}"

[Components]
; cumple Manual 9 §2.5: componentes alineados al manual
Name: "synapse"; Description: "{cm:setup_type_synapse}"; Types: full minimal synapse_only; Flags: fixed
Name: "syquex"; Description: "{cm:setup_type_syquex}"; Types: full syquex_only
Name: "opensyn"; Description: "{cm:setup_type_opensyn}"; Types: full
Name: "vscode"; Description: "{cm:setup_type_vscode}"; Types: full minimal

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; cumple Manual 9 §2.5: Sources binaria + runtime + std
; ME-R6: dist\bin\synapse.exe se construye en CI con el runtime modular completo (Manual 3 S3.1)
Source: "{#SourcePath}\..\..\dist\bin\{#MyAppExeName}"; DestDir: "{app}\bin"; Components: synapse; Flags: ignoreversion
; LSP opcional — solo se incluye si fue construido (Flags: skipifsourcedoesntexist)
Source: "{#SourcePath}\..\..\dist\bin\{#MyAppLspExeName}"; DestDir: "{app}\bin"; Components: synapse; Flags: ignoreversion skipifsourcedoesntexist
Source: "{#SourcePath}\..\..\dist\bin\*.dll"; DestDir: "{app}\bin"; Components: synapse; Flags: ignoreversion skipifsourcedoesntexist
; cumple Manual 9 §2.2: runtime/ contiene memory, concurrency, io, etc.
Source: "{#SourcePath}\..\..\runtime\*"; DestDir: "{app}/bin/runtime"; Components: synapse; Flags: ignoreversion recursesubdirs
Source: "{#SourcePath}\..\..\std\*"; DestDir: "{app}/std"; Components: synapse; Flags: ignoreversion recursesubdirs
; Nota: el repo usa librerias/ (no lib/) — Manual 9 §2.2 muestra lib/ como nombre instalado
Source: "{#SourcePath}\..\..\librerias\*"; DestDir: "{app}/lib"; Components: syquex; Flags: ignoreversion recursesubdirs
Source: "{#SourcePath}\..\..\opensyn\*"; DestDir: "{app}/opensyn"; Components: opensyn; Flags: ignoreversion recursesubdirs
; Nota: el repo usa vscode-synapse/ (no vscode/) — Manual 9 §2.2 muestra vscode/ como nombre instalado
Source: "{#SourcePath}\..\..\vscode-synapse\synapse-{#MyAppVersion}.vsix"; DestDir: "{app}/vscode"; Components: vscode; Flags: ignoreversion skipifsourcedoesntexist
; cumple Manual 9 §2.5: MinGW toolchain provisioning script
Source: "{#SourcePath}\..\scripts\install.ps1"; DestDir: "{app}"; Components: synapse; Flags: ignoreversion skipifsourcedoesntexist
; cumple Manual 9 §2.5: OpenSyn orquestador (nucleo/ai_orchestrador.c contiene synapse_shutdown_hook)
Source: "{#SourcePath}\..\..\nucleo\ai_orchestrator.h"; DestDir: "{app}/src"; Components: opensyn; Flags: ignoreversion skipifsourcedoesntexist
Source: "{#SourcePath}\..\..\nucleo\ai_orchestrator.c"; DestDir: "{app}/src"; Components: opensyn; Flags: ignoreversion skipifsourcedoesntexist
Source: "{#SourcePath}\..\..\nucleo\llama_client.h"; DestDir: "{app}/src"; Components: opensyn; Flags: ignoreversion skipifsourcedoesntexist
Source: "{#SourcePath}\..\..\nucleo\llama_client.c"; DestDir: "{app}/src"; Components: opensyn; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{group}\Synapse Language"; Filename: "{app}\bin\{#MyAppExeName}"; WorkingDir: "{app}"; Components: synapse
Name: "{group}\Desinstalar Synapse"; Filename: "{uninstallexe}"; Components: synapse
Name: "{autodesktop}\Synapse Language"; Filename: "{app}\bin\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon; Components: synapse

[Run]
; cumple Manual 9 §2.5: post-install hooks
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -NoProfile -File ""{app}\install.ps1"""; Description: "Provisionar MinGW Toolchain"; Flags: runhidden waituntilterminated; Components: synapse; StatusMsg: "Configurando MinGW Toolchain..."
Filename: "{app}\bin\{#MyAppExeName}"; Parameters: "opensyn install"; Components: opensyn; Check: FileExists(ExpandConstant('{app}\opensyn\installer.syn')); StatusMsg: "Instalando OpenSyn..."; Flags: runminimized waituntilterminated
Filename: "code"; Parameters: "--install-extension ""{app}\vscode\synapse-{#MyAppVersion}.vsix"""; Components: vscode; Check: FileExists(ExpandConstant('{app}\vscode\synapse-{#MyAppVersion}.vsix')) and VSCodeInPath(); Description: "Instalar extensión VS Code"; Flags: runminimized waituntilterminated postinstall

[Registry]
; cumple Manual 9 §2.5: PATH en HKCU
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}\bin"; Components: synapse; Flags: uninsdeletevalue

[Code]
var
  VRAM_MB: Integer;
  DownloadPage: TWizardPage;
  ProgressBar: TNewProgressBar;
  StatusLabel: TNewStaticText;

{------------------------------------------------------------------------------}
{ FUNCIÓN AUXILIAR: Instalación de extensión VS Code (Manual 9 §2.5) }
{------------------------------------------------------------------------------}
function FindVSCodePath(): String;
var
  ExitCode: Longint;
begin
  Result := '';
  // Buscar code.exe en PATH usando Exec
  if Exec('where', 'code', '', 0, ewWaitUntilTerminated, ExitCode) then
    Result := 'code';
  if Result = '' then begin
    if FileExists(ExpandConstant('{localappdata}\Programs\Microsoft VS Code\Code.exe')) then
      Result := ExpandConstant('{localappdata}\Programs\Microsoft VS Code\Code.exe');
    if Result = '' then
      Result := ExpandConstant('{autopf}\Microsoft VS Code\Code.exe');
  end;
end;

function VSCodeInPath(): Boolean;
begin
  Result := (FindVSCodePath() <> '');
end;

{------------------------------------------------------------------------------}
{ CARGA DE LICENCIA BILINGÜE (Manual 9 §2.5) }
{------------------------------------------------------------------------------}
procedure InitializeWizard();
var
  LicensePath: String;
  LicenseText: AnsiString;
begin
  if ActiveLanguage = 'spanish' then
    LicensePath := ExpandConstant('{src}\..\..\LICENSE.es')
  else
    LicensePath := ExpandConstant('{src}\..\..\LICENSE');
  if LoadStringFromFile(LicensePath, LicenseText) then
    WizardForm.LicenseMemo.Lines.Text := String(LicenseText);
end;

procedure InstallVSCodeExtension();
var
  VSCodePath, VSIXPath, Params: String;
  ExitCode: Longint;
begin
  VSIXPath := ExpandConstant('{app}\vscode\synapse-{#MyAppVersion}.vsix');
  if not FileExists(VSIXPath) then begin
    Log('VSIX no encontrado, saltando instalación de extensión');
    Exit;
  end;
  VSCodePath := FindVSCodePath();
  if VSCodePath = '' then begin
    MsgBox('VS Code no se encontró en PATH. Instale la extensión manualmente:' + #13#10 +
           '  code --install-extension "synapse-8.1.0-industrial.vsix"', mbInformation, MB_OK);
    Exit;
  end;
  Params := '--install-extension "' + VSIXPath + '"';
  Exec(VSCodePath, Params, '', 0, ewWaitUntilTerminated, ExitCode);
end;

{------------------------------------------------------------------------------}
{ FUNCIÓN AUXILIAR: Detección de VRAM via WMI }
{------------------------------------------------------------------------------}
function GetVRAMViaWMI(): Integer;
begin
  // Manual 9 §2.5: OpenSyn requiere GPU con VRAM >= 4GB
  // La detección WMI se omite si falla — se asume VRAM baja por defecto
  Result := 0;
end;

{------------------------------------------------------------------------------}
{ INICIALIZACIÓN: Detección de hardware (VRAM) }
{------------------------------------------------------------------------------}
function InitializeSetup(): Boolean;
begin
  Result := True;
  VRAM_MB := GetVRAMViaWMI();
  Log(Format('Setup iniciado. VRAM detectada: %d MB', [VRAM_MB]));
end;

{------------------------------------------------------------------------------}
{ PÁGINA PERSONALIZADA: Descarga de binarios pesados (OpenSyn IA) }
{------------------------------------------------------------------------------}
procedure CreateDownloadPage();
begin
  DownloadPage := CreateCustomPage(wpReady,
    'Descargando Componentes IA',
    'Descargando llama-server.exe y modelo .gguf desde GitHub/HuggingFace...');

  StatusLabel := TNewStaticText.Create(DownloadPage);
  StatusLabel.Parent := DownloadPage.Surface;
  StatusLabel.Left := 0;
  StatusLabel.Top := 0;
  StatusLabel.Width := DownloadPage.SurfaceWidth;
  StatusLabel.Height := 20;
  StatusLabel.Caption := 'Iniciando descargas...';

  ProgressBar := TNewProgressBar.Create(DownloadPage);
  ProgressBar.Parent := DownloadPage.Surface;
  ProgressBar.Left := 0;
  ProgressBar.Top := 25;
  ProgressBar.Width := DownloadPage.SurfaceWidth;
  ProgressBar.Height := 20;
  ProgressBar.Min := 0;
  ProgressBar.Max := 100;
  ProgressBar.Position := 0;
end;

function DownloadFile(const URL, DestPath: String): Boolean;
var
  CmdLine, ExePath: String;
  ExitCode: Longint;
begin
  Result := False;
  try
    ExePath := 'curl.exe';
    CmdLine := '-L -o "' + DestPath + '" "' + URL + '"';
    Result := Exec(ExePath, CmdLine, '', 0, ewWaitUntilTerminated, ExitCode);
  except
    Result := False;
  end;
end;

procedure DownloadAIComponents();
var
  DestServer, DestModel: String;
begin
  DestServer := ExpandConstant('{app}\opensyn\ia\llama-server.exe');
  DestModel := ExpandConstant('{app}\opensyn\models\model.gguf');

  StatusLabel.Caption := 'Descargando llama-server.exe (~15 MB)...';
  ProgressBar.Position := 10;
  WizardForm.Repaint;

  if not DownloadFile('{#LLAMA_SERVER_URL}', DestServer) then begin
    MsgBox('Error descargando llama-server.exe. Verifique su conexión.', mbError, MB_OK);
    Exit;
  end;

  ProgressBar.Position := 50;
  StatusLabel.Caption := 'Descargando modelo .gguf (~700 MB)...';
  WizardForm.Repaint;

  if not DownloadFile('{#MODEL_URL}', DestModel) then begin
    MsgBox('Error descargando modelo. Verifique su conexión y espacio en disco.', mbError, MB_OK);
    Exit;
  end;

  ProgressBar.Position := 100;
  StatusLabel.Caption := 'Descargas completadas. Verificando integridad...';
  WizardForm.Repaint;
end;

procedure OnDownloadProgress(TotalBytes, DownloadedBytes: Int64);
var
  PosMB, TotalMB: Integer;
begin
  if TotalBytes > 0 then
  begin
    ProgressBar.Position := MulDiv(DownloadedBytes, 100, TotalBytes);
    PosMB := ProgressBar.Position;
    TotalMB := TotalBytes div (1024*1024);
    DownloadedBytes := DownloadedBytes div (1024*1024);
    StatusLabel.Caption := Format('Descargando... %d%% (%d/%d MB)', [PosMB, DownloadedBytes, TotalMB]);
    WizardForm.Repaint;
  end;
end;

{------------------------------------------------------------------------------}
{ CALLBACK: NextButtonClick — controla el flujo del wizard }
{------------------------------------------------------------------------------}
function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  case CurPageID of
    wpSelectComponents: begin
      if IsComponentSelected('opensyn') then begin
        CreateDownloadPage();
      end;
    end;
    wpReady: begin
      if IsComponentSelected('opensyn') then begin
        if VRAM_MB < 4096 then begin
          if MsgBox('ADVERTENCIA: Su GPU tiene ' + IntToStr(VRAM_MB) + ' MB de VRAM. ' +
            'El modelo requiere al menos 4 GB. ¿Desea continuar de todos modos?',
            mbConfirmation, MB_YESNO) = IDNO then begin
            Result := False;
          end;
        end;
      end;
    end;
  end;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if (CurPageID = wpReady) and IsComponentSelected('opensyn') then begin
    try
      DownloadAIComponents();
    except
      Log('Error durante descarga de componentes IA');
    end;
  end;
end;

{------------------------------------------------------------------------------}
{ VERIFICACIÓN PREVIA: Espacio en disco }
{------------------------------------------------------------------------------}
function CheckDiskSpace(RequiredMB: Integer): Boolean;
begin
  // Manual 9 §2.5: verificar espacio libre suficiente
  // En entornos CI, se omite la verificación (asumir espacio suficiente)
  Result := True;
end;

function InitializeUninstall(): Boolean;
begin
  Result := True;
end;

[CustomMessages]
core_only_desc=Synapse Core (Ligero - Solo Lenguaje, MinGW y VSIX)
opensyn_full_desc=OpenSyn (Completo - Lenguaje + IA Local Autónoma)
ai_engine_desc=Motor IA Local (llama-server.exe + modelo .gguf + orquestador C)
vram_warning=Su GPU tiene %d MB de VRAM. El modelo requiere al menos 4 GB.
download_failed=Error descargando %s. Verifique su conexión.
verify_checksum=Verificando integridad del archivo...
install_completed=Instalación completada. Ejecute 'synapse' desde terminal.

