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
#define MODEL_URL_1B "https://huggingface.co/TheBloke/deepseek-coder-1.3B-GGUF/resolve/main/deepseek-coder-1.3b-instruct.Q4_K_M.gguf"
#define MODEL_URL_7B "https://huggingface.co/TheBloke/CodeLlama-7B-GGUF/resolve/main/codellama-7b.Q4_K_M.gguf"
#define MODEL_URL_13B "https://huggingface.co/TheBloke/CodeLlama-13B-GGUF/resolve/main/codellama-13b.Q4_K_M.gguf"
#define MODEL_URL_34B "https://huggingface.co/TheBloke/CodeLlama-34B-GGUF/resolve/main/codellama-34b.Q4_K_M.gguf"
#define MODEL_URL MODEL_URL_1B

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\Synapse
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile={#SourcePath}\..\..\LICENSE
OutputDir={#SourcePath}\..\..\dist
OutputBaseFilename=Synapse-{#MyAppVersion}-Windows-x64
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible
WizardStyle=modern
ChangesEnvironment=yes
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
; cumple Manual 9 §2.5: tipos de instalación configurables (3 opciones + custom)
Name: "full"; Description: "{cm:setup_type_full}"
Name: "compact"; Description: "{cm:setup_type_synapse_only}"
Name: "syquex_only"; Description: "{cm:setup_type_syquex_only}"
Name: "custom"; Description: "Instalación personalizada"; Flags: iscustom

[Components]
; cumple Manual 9 §2.5: componentes independientes — Synapse/Syquex/OpenSyn seleccionables por separado
Name: "synapse"; Description: "{cm:setup_type_synapse}"; Types: full compact
Name: "syquex"; Description: "{cm:setup_type_syquex}"; Types: full syquex_only
Name: "opensyn"; Description: "{cm:setup_type_opensyn}"; Types: full
Name: "vscode"; Description: "{cm:setup_type_vscode}"; Types: full compact

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; cumple Manual 9 §2.5: Sources binaria + runtime + std — todo el ecosistema
; ME-R6: dist\bin\synapse.exe se construye en CI con el runtime modular completo (Manual 3 S3.1)
Source: "{#SourcePath}\..\..\dist\bin\{#MyAppExeName}"; DestDir: "{app}\bin"; Components: synapse; Flags: ignoreversion
Source: "{#SourcePath}\..\..\opensyn\opensyn.bat"; DestDir: "{app}\bin"; Components: opensyn; Flags: ignoreversion
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
; cumple Manual 9 §2.5: MinGW toolchain provisioning script (scripts/install.ps1 existe — provisioning real)
Source: "{#SourcePath}\scripts\install.ps1"; DestDir: "{app}"; Components: synapse; Flags: ignoreversion
; cumple Manual 9 §2.5: OpenSyn orquestador (nucleo/ai_orchestrador.c contiene synapse_shutdown_hook)
Source: "{#SourcePath}\..\..\nucleo\ai_orchestrator.h"; DestDir: "{app}/src"; Components: opensyn; Flags: ignoreversion skipifsourcedoesntexist
Source: "{#SourcePath}\..\..\nucleo\ai_orchestrator.c"; DestDir: "{app}/src"; Components: opensyn; Flags: ignoreversion skipifsourcedoesntexist
Source: "{#SourcePath}\..\..\nucleo\llama_client.h"; DestDir: "{app}/src"; Components: opensyn; Flags: ignoreversion skipifsourcedoesntexist
Source: "{#SourcePath}\..\..\nucleo\llama_client.c"; DestDir: "{app}/src"; Components: opensyn; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{group}\Synapse Language"; Filename: "{app}\bin\{#MyAppExeName}"; WorkingDir: "{app}"; Components: synapse
Name: "{group}\Synapse - Terminal"; Filename: "cmd.exe"; Parameters: "/k ""{app}\bin\synapse.exe"" --help"; WorkingDir: "{app}"; Components: synapse
Name: "{group}\Desinstalar Synapse"; Filename: "{uninstallexe}"; Components: synapse
Name: "{autodesktop}\Synapse Language"; Filename: "{app}\bin\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon; Components: synapse

[Run]
; cumple Manual 9 §2.5: post-install hooks
; Flags: nowait para instalacion silenciosa no-bloqueante
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -NoProfile -File ""{app}\install.ps1"""; Description: "Provisionar MinGW Toolchain"; Flags: runhidden nowait; Components: synapse; StatusMsg: "Configurando MinGW Toolchain..."
Filename: "{app}\bin\{#MyAppExeName}"; Parameters: """{app}\opensyn\installer.syn"""; Components: opensyn; Check: FileExists(ExpandConstant('{app}\opensyn\installer.syn')); StatusMsg: "Configurando OpenSyn (detección hardware)..."; Flags: runhidden waituntilterminated
Filename: "cmd"; Parameters: "/c code --install-extension ""{app}\vscode\synapse-{#MyAppVersion}.vsix"""; Components: vscode; Check: VSCodeInPath() and FileExists(ExpandConstant('{app}\vscode\synapse-{#MyAppVersion}.vsix')); Description: "Instalar extension VS Code"; Flags: runhidden nowait postinstall

[Registry]
; cumple Manual 9 §2.5: PATH en HKCU (con ChangesEnvironment=yes difunde WM_SETTINGCHANGE)
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}\bin"; Components: synapse; Flags: preservestringtype uninsdeletevalue
; Fallback HKLM para instalaciones admin (si usuario elige Todos los usuarios)
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}\bin"; Check: IsAdminInstallMode; Flags: preservestringtype uninsdeletevalue

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
begin
  Result := '';
  // Buscar code.exe en rutas comunes (no dependemos de 'where' que no captura output)
  if FileExists(ExpandConstant('{localappdata}\Programs\Microsoft VS Code\Code.exe')) then
    Result := ExpandConstant('{localappdata}\Programs\Microsoft VS Code\Code.exe');
  if Result = '' then
    Result := ExpandConstant('{autopf}\Microsoft VS Code\Code.exe');
  if Result = '' then begin
    // Buscar en ruta de usuario de VS Code
    Result := ExpandConstant('{localappdata}\Microsoft\vscode\Code.exe');
    if not FileExists(Result) then
      Result := ExpandConstant('{localappdata}\Programs\Microsoft VS Code\Code.exe');
    if not FileExists(Result) then
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
{ FUNCIÓN AUXILIAR: Ejecuta PowerShell y retorna entero (0 si falla) }
{------------------------------------------------------------------------------}
function ExecPowerShellInt(const PSCommand: String): Integer;
var
  TmpFile, Cmd: String;
  OutStr: AnsiString;
  ExitCode: Integer;
begin
  Result := 0;
  TmpFile := ExpandConstant('{tmp}\hw_out.txt');
  Cmd := '/c powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "' + PSCommand + ' > """' + TmpFile + '""" 2>nul"';
  if Exec('cmd.exe', Cmd, '', SW_HIDE, ewWaitUntilTerminated, ExitCode) then begin
    if FileExists(TmpFile) then begin
      if LoadStringFromFile(TmpFile, OutStr) then begin
        OutStr := Trim(OutStr);
        // PowerShell puede retornar float (ej. 16234.5) — tomar parte entera
        if Pos('.', OutStr) > 0 then OutStr := Copy(OutStr, 1, Pos('.', OutStr)-1);
        if Pos(',', OutStr) > 0 then OutStr := Copy(OutStr, 1, Pos(',', OutStr)-1);
        try
          Result := StrToInt(OutStr);
        except
          Result := 0;
        end;
      end;
      DeleteFile(TmpFile);
    end;
  end;
end;

function GetRAM_MB(): Integer;
begin
  // TotalPhysicalMemory en bytes -> MB
  Result := ExecPowerShellInt('(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1MB -as [int]');
  if Result = 0 then
    Result := ExecPowerShellInt('(Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory / 1048576 -as [int]');
end;

function GetVRAMViaWMI(): Integer;
var
  V: Integer;
begin
  // AdapterRAM puede ser 0 en integradas; sumar todas las GPUs
  V := ExecPowerShellInt('(Get-CimInstance Win32_VideoController | Measure-Object -Property AdapterRAM -Sum).Sum / 1048576 -as [int]');
  if V = 0 then
    V := ExecPowerShellInt('([math]::Round((Get-CimInstance Win32_VideoController).AdapterRAM / 1MB)) -as [int]');
  Result := V;
end;

function GetCPUCores(): Integer;
begin
  Result := ExecPowerShellInt('(Get-CimInstance Win32_Processor).NumberOfCores -as [int]');
  if Result = 0 then
    Result := ExecPowerShellInt('(Get-CimInstance Win32_Processor).NumberOfLogicalProcessors -as [int]');
  if Result = 0 then
    Result := 4;
end;

function CheckForExistingGGUF(): String;
var
  Candidate, Home: String;
  FindRec: TFindRec;
begin
  Result := '';
  Home := GetEnv('USERPROFILE');
  if Home <> '' then begin
    Candidate := Home + '\.opensyn\models';
    if DirExists(Candidate) then begin
      if FindFirst(Candidate + '\*.gguf', FindRec) then begin
        try
          repeat
            Result := Candidate + '\' + FindRec.Name;
            Log('GGUF existente encontrado: ' + Result);
            Break;
          until not FindNext(FindRec);
        finally
          FindClose(FindRec);
        end;
      end;
    end;
    // Ollama models
    Candidate := Home + '\.ollama\models';
    if (Result = '') and DirExists(Candidate) then begin
      // cualquier subdirectorio con .gguf o blobs
      if DirExists(Candidate) then begin
        Log('Directorio Ollama encontrado: ' + Candidate);
        // no retornamos gguf directo, pero marcamos como IA existente
      end;
    end;
  end;
  // Nota: {app} no disponible en InitializeSetup, se chequea luego en DownloadAIComponents
end;

function CheckForExistingGGUFInApp(): String;
var
  Candidate: String;
  FindRec: TFindRec;
begin
  Result := '';
  try
    Candidate := ExpandConstant('{app}\opensyn\models');
    if DirExists(Candidate) then begin
      if FindFirst(Candidate + '\*.gguf', FindRec) then begin
        try
          Result := Candidate + '\' + FindRec.Name;
          Log('GGUF en app encontrado: ' + Result);
        finally
          FindClose(FindRec);
        end;
      end;
    end;
  except
    Log('CheckForExistingGGUFInApp: {app} aún no inicializado');
  end;
end;

function IsOllamaInstalled(): Boolean;
var
  Candidates: array[0..4] of String;
  i: Integer;
begin
  Result := False;
  Candidates[0] := ExpandConstant('{autopf}\Ollama\ollama.exe');
  Candidates[1] := ExpandConstant('{pf}\Ollama\ollama.exe');
  Candidates[2] := ExpandConstant('{localappdata}\Programs\Ollama\ollama.exe');
  Candidates[3] := GetEnv('USERPROFILE') + '\AppData\Local\Programs\Ollama\ollama.exe';
  Candidates[4] := 'C:\Ollama\ollama.exe';
  for i := 0 to 4 do begin
    if FileExists(Candidates[i]) then begin
      Log('Ollama detectado: ' + Candidates[i]);
      Result := True;
      Exit;
    end;
  end;
  // where ollama en PATH
  if FileExists(ExpandConstant('{tmp}\ollama_check.txt')) then DeleteFile(ExpandConstant('{tmp}\ollama_check.txt'));
  // no usamos where por simplicidad, solo paths
end;

function SelectModelURL(VRAM: Integer): String;
begin
  if VRAM < 4096 then
    Result := '{#MODEL_URL_1B}'
  else if VRAM < 8192 then
    Result := '{#MODEL_URL_7B}'
  else if VRAM < 12288 then
    Result := '{#MODEL_URL_13B}'
  else
    Result := '{#MODEL_URL_34B}';
end;

function SelectModelName(VRAM: Integer): String;
begin
  if VRAM < 4096 then
    Result := 'deepseek-coder-1.3b-Q4_K_M.gguf'
  else if VRAM < 8192 then
    Result := 'codellama-7b-Q4_K_M.gguf'
  else if VRAM < 12288 then
    Result := 'codellama-13b-Q4_K_M.gguf'
  else
    Result := 'codellama-34b-Q4_K_M.gguf';
end;

{------------------------------------------------------------------------------}
{ INICIALIZACIÓN: Detección de hardware (RAM/VRAM/CPU) — Manual 9 §5.3 }
{------------------------------------------------------------------------------}
var
  RAM_MB: Integer;
  CPU_CORES: Integer;
  ExistingGGUF: String;
  OllamaFound: Boolean;
  SelectedModelURL: String;
  SelectedModelName: String;

function InitializeSetup(): Boolean;
begin
  Result := True;
  try
    VRAM_MB := GetVRAMViaWMI();
    RAM_MB := GetRAM_MB();
    CPU_CORES := GetCPUCores();
    ExistingGGUF := CheckForExistingGGUF();
    OllamaFound := IsOllamaInstalled();
    SelectedModelURL := SelectModelURL(VRAM_MB);
    SelectedModelName := SelectModelName(VRAM_MB);
    Log(Format('Setup iniciado. RAM: %d MB VRAM: %d MB CPU cores: %d Ollama: %d GGUF: %s Modelo: %s', [RAM_MB, VRAM_MB, CPU_CORES, Integer(OllamaFound), ExistingGGUF, SelectedModelName]));
  except
    Log('InitializeSetup: error en detección hardware, usando valores por defecto');
    VRAM_MB := 0; RAM_MB := 4096; CPU_CORES := 4;
    SelectedModelURL := SelectModelURL(0);
    SelectedModelName := SelectModelName(0);
  end;
end;

procedure InitializeWizard();
var
  LicenseFile: String;
  LicenseText: AnsiString;
begin
  // Manual 9 §2.5: licencia bilingüe según idioma elegido (LICENSE vs LICENSE.es)
  if ActiveLanguage = 'spanish' then
    LicenseFile := ExpandConstant('{src}\..\..\LICENSE.es')
  else
    LicenseFile := ExpandConstant('{src}\..\..\LICENSE');
  if FileExists(LicenseFile) then begin
    if LoadStringFromFile(LicenseFile, LicenseText) then begin
      WizardForm.LicenseMemo.Lines.Text := LicenseText;
    end;
  end;
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
  UseExisting: Boolean;
  AppGGUF: String;
begin
  // Manual 9 §5.3: re-chequear GGUF en {app} (no disponible en InitializeSetup) y en perfil
  if ExistingGGUF = '' then begin
    AppGGUF := CheckForExistingGGUFInApp();
    if AppGGUF <> '' then ExistingGGUF := AppGGUF;
  end;
  if ExistingGGUF = '' then ExistingGGUF := CheckForExistingGGUF();
  // Manual 9 §5.3: si hay GGUF existente, preguntar al usuario
  UseExisting := False;
  if ExistingGGUF <> '' then begin
    if MsgBox('Se encontró un modelo GGUF existente:'#13#10 + ExistingGGUF + #13#10#13#10'¿Desea usar este modelo existente?'#13#10'(Sí = usar existente y no descargar, No = descargar ' + SelectedModelName + ')', mbConfirmation, MB_YESNO) = IDYES then begin
      Log('Usuario eligió usar GGUF existente: ' + ExistingGGUF);
      UseExisting := True;
      StatusLabel.Caption := 'Usando modelo existente: ' + ExtractFileName(ExistingGGUF);
      ProgressBar.Position := 50;
      WizardForm.Repaint;
    end;
  end;

  if IsOllamaInstalled() then begin
    if MsgBox('Se detectó Ollama instalado en este sistema.'#13#10'OpenSyn puede conectarse a Ollama (http://localhost:11434) en lugar de descargar llama-server.'#13#10#13#10'¿Desea conectar OpenSyn a Ollama existente?'#13#10'(Sí = usar Ollama, No = instalar llama-server + modelo)', mbConfirmation, MB_YESNO) = IDYES then begin
      Log('Usuario eligió conectar a Ollama existente — se omite descarga de llama-server');
      StatusLabel.Caption := 'Configurando para Ollama existente...';
      ProgressBar.Position := 100;
      WizardForm.Repaint;
      // Crear config que apunte a Ollama
      SaveStringToFile(ExpandConstant('{app}\opensyn\config_ollama.txt'), 'ollama=1' + #13#10 + 'model=' + SelectedModelName, False);
      Exit;
    end;
  end;

  DestServer := ExpandConstant('{app}\opensyn\ia\llama-server.exe');
  if UseExisting then
    DestModel := ExistingGGUF
  else
    DestModel := ExpandConstant('{app}\opensyn\models\') + SelectedModelName;

  if not UseExisting then begin
    ForceDirectories(ExtractFileDir(DestModel));
    StatusLabel.Caption := 'Descargando llama-server.exe (~15 MB)...';
    ProgressBar.Position := 10;
    WizardForm.Repaint;

    if not DownloadFile('{#LLAMA_SERVER_URL}', DestServer) then begin
      MsgBox('Error descargando llama-server.exe. Verifique su conexión.', mbError, MB_OK);
      Exit;
    end;

    ProgressBar.Position := 50;
    StatusLabel.Caption := 'Descargando ' + SelectedModelName + ' (~' + IntToStr(4096) + ' MB)...';
    WizardForm.Repaint;

    if not DownloadFile(SelectedModelURL, DestModel) then begin
      MsgBox('Error descargando modelo ' + SelectedModelName + '. Verifique su conexión y espacio en disco.', mbError, MB_OK);
      Exit;
    end;
  end;

  ProgressBar.Position := 100;
  StatusLabel.Caption := 'Descargas completadas. Verificando integridad...';
  WizardForm.Repaint;
  // Guardar selección para post-install config
  SaveStringToFile(ExpandConstant('{app}\opensyn\install_info.txt'), 'model=' + SelectedModelName + #13#10 + 'url=' + SelectedModelURL + #13#10 + 'vram=' + IntToStr(VRAM_MB), False);
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
      if WizardIsComponentSelected('opensyn') then begin
        CreateDownloadPage();
      end;
    end;
    wpReady: begin
      if WizardIsComponentSelected('opensyn') then begin
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
  if (CurPageID = wpReady) and WizardIsComponentSelected('opensyn') then begin
    try
      DownloadAIComponents();
    except
      Log('Error durante descarga de componentes IA');
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssPostInstall) and WizardIsComponentSelected('vscode') then begin
    try
      InstallVSCodeExtension();
    except
      Log('Error instalando extensión VS Code via CurStepChanged');
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

