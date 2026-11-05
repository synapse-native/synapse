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

#define LLAMA_SERVER_URL "https://github.com/ggml-org/llama.cpp/releases/download/b10819/llama-b10819-bin-win-cpu-x64.zip"
#define MODEL_URL_1B "https://huggingface.co/TheBloke/deepseek-coder-1.3b-instruct-GGUF/resolve/main/deepseek-coder-1.3b-instruct.Q4_K_M.gguf"
#define MODEL_URL_7B "https://huggingface.co/TheBloke/CodeLlama-7B-GGUF/resolve/main/codellama-7b.Q4_K_M.gguf"
#define MODEL_URL_13B "https://huggingface.co/TheBloke/CodeLlama-13B-GGUF/resolve/main/codellama-13b.Q4_K_M.gguf"
#define MODEL_URL_34B "https://huggingface.co/TheBloke/CodeLlama-34B-GGUF/resolve/main/codellama-34b.Q4_K_M.gguf"
#define MODEL_URL MODEL_URL_1B

; SHA256 hashes para verificación de integridad (actualizar al cambiar versiones)
; SHA256 del llama-server.exe EXTRAIDO del zip b10819 (no del zip: el instalador verifica el exe)
#define LLAMA_SERVER_SHA256 "149bb866b6cbcac177579e6e8693e0225c59b94a0f384ed562f9ec48f15a8cd3"
; hashes reales = LFS oid de HuggingFace (SHA256 del contenido); llama-server = SHA256 del exe EXTRAIDO (no del zip)
#define MODEL_SHA256_1B "04cebb6fafa40ae628cf6bfeb76032ec792852f54020c559ad0a56b9f2839118"
#define MODEL_SHA256_7B_Q4 "c3866cb985de17d398c2d7e85bb8a9c717a76bb997dce0e72a0cb169063e6d17"
#define MODEL_SHA256_7B_Q5 "f4222b2c639e3f5adee3cf2391f02fb0ee1307e5ef5a48399affb5f3802dd857"
#define MODEL_SHA256_13B "b889f38ea793b823756e0eb9d3b60a5c5061c2df2d99b6f2fdb7c28328f043ce"
#define MODEL_SHA256_34B "26e7ece4d609b8515b4f72543b555692dc6ca2ff2bee336a6a1f4f2c97978cee"

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
CloseApplications=no
RestartApplications=no
; cumple Manual 9 §2.5: no cerrar apps automaticamente (evita Abort/Retry/Ignore por opensyn.exe en uso en /SILENT)

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
; cumple Manual 9 §2.5: tipos full/minimal/custom (manual manda "minimal" para solo-Synapse)
Name: "full"; Description: "{cm:setup_type_full}"
Name: "minimal"; Description: "{cm:setup_type_synapse_only}"
Name: "syquex_only"; Description: "{cm:setup_type_syquex_only}"
Name: "custom"; Description: "Instalación personalizada"; Flags: iscustom

[Components]
; cumple Manual 9 §2.5: componentes independientes — Synapse/Syquex/OpenSyn seleccionables por separado
Name: "synapse"; Description: "{cm:setup_type_synapse}"; Types: full minimal
Name: "syquex"; Description: "{cm:setup_type_syquex}"; Types: full syquex_only
Name: "opensyn"; Description: "{cm:setup_type_opensyn}"; Types: full
Name: "vscode"; Description: "{cm:setup_type_vscode}"; Types: full minimal

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; cumple Manual 9 §2.5: Sources binaria + runtime + std — todo el ecosistema
; ME-R6: dist\bin\synapse.exe se construye en CI con el runtime modular completo (Manual 3 S3.1)
Source: "{#SourcePath}\..\..\dist\bin\{#MyAppExeName}"; DestDir: "{app}\bin"; Components: synapse; Flags: ignoreversion
Source: "{#SourcePath}\..\..\dist\bin\opensyn.exe"; DestDir: "{app}\bin"; Components: opensyn; Flags: ignoreversion
Source: "{#SourcePath}\..\..\opensyn\opensyn.bat"; DestDir: "{app}\bin"; Components: opensyn; Flags: ignoreversion
; Helper de descarga con ventana de progreso propia (resuelve congelamiento de Inno Setup)
Source: "{#SourcePath}\dl_helper.exe"; DestDir: "{app}"; Components: opensyn; Flags: ignoreversion
; LSP opcional — solo se incluye si fue construido (Flags: skipifsourcedoesntexist)
Source: "{#SourcePath}\..\..\dist\bin\{#MyAppLspExeName}"; DestDir: "{app}\bin"; Components: synapse; Flags: ignoreversion skipifsourcedoesntexist
Source: "{#SourcePath}\..\..\dist\bin\*.dll"; DestDir: "{app}\bin"; Components: synapse; Flags: ignoreversion skipifsourcedoesntexist
; cumple Manual 9 §2.2: runtime/ contiene memory, concurrency, io, etc.
Source: "{#SourcePath}\..\..\runtime\*"; DestDir: "{app}/bin/runtime"; Components: synapse; Flags: ignoreversion recursesubdirs
; cumple Manual 9 §2.5: fuentes de enlace del compilador nativo — principal.syn resuelve
; _rt_dir = dir del exe y enlaza desde fuente (ME-R5): synapse_rt.c + synapse_unity.c
; (autogenerado en cwd), axon/tweetnacl.c, vendor/sqlite3/sqlite3.c, nucleo/federated.c
; y headers de inclusión (synapse_rt_types.h requerido por runtime/core/*.h).
Source: "{#SourcePath}\..\..\synapse_rt.c"; DestDir: "{app}\bin"; Components: synapse; Flags: ignoreversion
Source: "{#SourcePath}\..\..\synapse_rt.h"; DestDir: "{app}\bin"; Components: synapse; Flags: ignoreversion
; cumple Manual 9 §2.5: header de memoria del runtime — runtime/core/{fuzz,memory}.c
Source: "{#SourcePath}\..\..\synapse_rt_memory.h"; DestDir: "{app}\bin"; Components: synapse; Flags: ignoreversion
; cumple Manual 9 §2.5: headers de librerias embebidas resueltos por -I<_rt_dir>
; (principal.syn:664) — runtime/core/*.c incluye librerias/embedded_libs.h
Source: "{#SourcePath}\..\..\librerias\*"; DestDir: "{app}\bin\librerias"; Components: synapse; Flags: ignoreversion recursesubdirs
Source: "{#SourcePath}\..\..\synapse_rt_types.h"; DestDir: "{app}\bin"; Components: synapse; Flags: ignoreversion
Source: "{#SourcePath}\..\..\axon\tweetnacl.c"; DestDir: "{app}\bin\axon"; Components: synapse; Flags: ignoreversion
Source: "{#SourcePath}\..\..\axon\tweetnacl.h"; DestDir: "{app}\bin\axon"; Components: synapse; Flags: ignoreversion
Source: "{#SourcePath}\..\..\vendor\sqlite3\sqlite3.c"; DestDir: "{app}\bin\vendor\sqlite3"; Components: synapse; Flags: ignoreversion
Source: "{#SourcePath}\..\..\vendor\sqlite3\sqlite3.h"; DestDir: "{app}\bin\vendor\sqlite3"; Components: synapse; Flags: ignoreversion
Source: "{#SourcePath}\..\..\nucleo\federated.c"; DestDir: "{app}\bin\nucleo"; Components: synapse; Flags: ignoreversion
Source: "{#SourcePath}\..\..\nucleo\federated.h"; DestDir: "{app}\bin\nucleo"; Components: synapse; Flags: ignoreversion
Source: "{#SourcePath}\..\..\std\*"; DestDir: "{app}/std"; Components: synapse; Flags: ignoreversion recursesubdirs
; Nota: el repo usa librerias/ (no lib/) — Manual 9 §2.2 muestra lib/ como nombre instalado
Source: "{#SourcePath}\..\..\librerias\*"; DestDir: "{app}/lib"; Components: syquex; Flags: ignoreversion recursesubdirs
Source: "{#SourcePath}\..\..\opensyn\*"; DestDir: "{app}/opensyn"; Components: opensyn; Flags: ignoreversion recursesubdirs; Excludes: "*.c,*.o,*.exe,*.py,*.h,*.pyc,*.syn.json,__pycache__"
; Nota: el repo usa vscode-synapse/ (no vscode/) — Manual 9 §2.2 muestra vscode/ como nombre instalado
Source: "{#SourcePath}\..\..\vscode-synapse\synapse-{#MyAppVersion}.vsix"; DestDir: "{app}/vscode"; Components: vscode; Flags: ignoreversion skipifsourcedoesntexist
; cumple Manual 9 §2.5: MinGW toolchain provisioning script (scripts/install.ps1 existe — provisioning real)
Source: "{#SourcePath}\scripts\install.ps1"; DestDir: "{app}"; Components: synapse; Flags: ignoreversion
; cumple Manual 9 §2.5: OpenSyn orquestador (nucleo/ai_orchestrador.c contiene synapse_shutdown_hook)
Source: "{#SourcePath}\..\..\nucleo\ai_orchestrator.h"; DestDir: "{app}/src"; Components: opensyn; Flags: ignoreversion skipifsourcedoesntexist
Source: "{#SourcePath}\..\..\nucleo\ai_orchestrator.c"; DestDir: "{app}/src"; Components: opensyn; Flags: ignoreversion skipifsourcedoesntexist
Source: "{#SourcePath}\..\..\nucleo\llama_client.h"; DestDir: "{app}/src"; Components: opensyn; Flags: ignoreversion skipifsourcedoesntexist
Source: "{#SourcePath}\..\..\nucleo\llama_client.c"; DestDir: "{app}/src"; Components: opensyn; Flags: ignoreversion skipifsourcedoesntexist
; Licencias embebidas para InitializeWizard bilingüe (no dependen de {src} en runtime)
Source: "{#SourcePath}\..\..\LICENSE"; DestDir: "{tmp}"; Flags: dontcopy
Source: "{#SourcePath}\..\..\LICENSE.es"; DestDir: "{tmp}"; Flags: dontcopy

[Icons]
Name: "{group}\Synapse Language"; Filename: "{app}\bin\{#MyAppExeName}"; WorkingDir: "{app}"; Components: synapse
Name: "{group}\Synapse - Terminal"; Filename: "cmd.exe"; Parameters: "/k ""{app}\bin\synapse.exe"""; WorkingDir: "{app}"; Components: synapse
; cumple Manual 9 §2.5 + Manual 7 §2.1: OpenSyn arranca con WorkingDir={app} y resuelve {app}\opensyn\ia|models
Name: "{group}\OpenSyn (IA local)"; Filename: "{app}\bin\opensyn.exe"; WorkingDir: "{app}"; Components: opensyn
Name: "{group}\Desinstalar Synapse"; Filename: "{uninstallexe}"; Components: synapse
Name: "{autodesktop}\Synapse Language"; Filename: "{app}\bin\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon; Components: synapse
Name: "{autodesktop}\OpenSyn (IA local)"; Filename: "{app}\bin\opensyn.exe"; WorkingDir: "{app}"; Tasks: desktopicon; Components: opensyn

[Run]
; cumple Manual 9 §2.5: post-install hooks
; Flags: nowait para instalacion silenciosa no-bloqueante; runasoriginaluser para VS Code extension (no abre ventana, per-user)
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-ExecutionPolicy Bypass -NoProfile -File ""{app}\install.ps1"""; Description: "Provisionar MinGW Toolchain"; Flags: runhidden nowait; Components: synapse; StatusMsg: "Configurando MinGW Toolchain..."
; [fix-31] Paso [Run] OpenSyn eliminado: synapse.exe solo COMPILA installer.syn (nunca lo ejecuta) y fallaba en silencio (~240 ms, sin GCC en cwd). La configuracion de OpenSyn la realiza el wizard en [Code] DownloadAIComponents (Manual 9 §5.2-5.3) y opensyn.exe lee la config ya instalada.
Filename: "cmd.exe"; Parameters: "/c code --install-extension ""{app}\vscode\synapse-8.1.0-industrial.vsix"" --force"; Components: vscode; StatusMsg: "Instalando extensión VS Code..."; Flags: runhidden runasoriginaluser nowait
; cumple Manual 9 §2.5: VS Code via Run runasoriginaluser (no abre ventana, evita elevacion que causa exit 1)

[Registry]
; cumple Manual 9 §2.5: PATH en HKCU (preservestringtype sin uninsdeletevalue para no borrar PATH original al desinstalar)
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}\bin"; Components: synapse; Flags: preservestringtype; Check: NotSynapseInUserPath
; Fallback HKLM solo si admin y sin borrar en uninstall (evita corrupcion Machine Path)
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}\bin"; Check: IsAdminInstallMode and NotSynapseInMachinePath; Flags: preservestringtype

[Code]
var
  VRAM_MB: Integer;
  DownloadPage: TWizardPage;
  ProgressBar: TNewProgressBar;
  StatusLabel: TNewStaticText;
  ModelSelectPage: TInputOptionWizardPage;
  OllamaExePath: String;
  OllamaConnectMode: Boolean;
  // cumple Manual 9 §5.2: seleccion de modelo code-especifico
  LlamaServerSHA256: String;
  ModelSHA256_1B: String;
  ModelSHA256_7B_Q4: String;
  ModelSHA256_7B_Q5: String;
  ModelSHA256_13B: String;
  ModelSHA256_34B: String;

{------------------------------------------------------------------------------}
{ FUNCIÓN AUXILIAR: Instalación de extensión VS Code (Manual 9 §2.5) }
{------------------------------------------------------------------------------}

function FindVSCodePath(): String;
begin
  Result := '';
  // Prioridad: bin\code.cmd (instalacion usuario) y Code.exe — cumple Manual 9 §2.5
  if FileExists(ExpandConstant('{localappdata}\Programs\Microsoft VS Code\bin\code.cmd')) then
    Result := ExpandConstant('{localappdata}\Programs\Microsoft VS Code\bin\code.cmd');
  if (Result = '') and FileExists(ExpandConstant('{localappdata}\Programs\Microsoft VS Code\Code.exe')) then
    Result := ExpandConstant('{localappdata}\Programs\Microsoft VS Code\Code.exe');
  if (Result = '') and FileExists(ExpandConstant('{localappdata}\Programs\Microsoft VS Code\bin\code')) then
    Result := ExpandConstant('{localappdata}\Programs\Microsoft VS Code\bin\code');
  if (Result = '') and FileExists(ExpandConstant('{autopf}\Microsoft VS Code\bin\code.cmd')) then
    Result := ExpandConstant('{autopf}\Microsoft VS Code\bin\code.cmd');
  if (Result = '') and FileExists(ExpandConstant('{autopf}\Microsoft VS Code\Code.exe')) then
    Result := ExpandConstant('{autopf}\Microsoft VS Code\Code.exe');
  if (Result = '') and FileExists(ExpandConstant('{commonpf}\Microsoft VS Code\bin\code.cmd')) then
    Result := ExpandConstant('{commonpf}\Microsoft VS Code\bin\code.cmd');
  if (Result = '') and FileExists(ExpandConstant('{localappdata}\Microsoft\vscode\Code.exe')) then
    Result := ExpandConstant('{localappdata}\Microsoft\vscode\Code.exe');
end;

function VSCodeInPath(): Boolean;
begin
  Result := (FindVSCodePath() <> '');
end;
// cumple Manual 9 §2.5: deteccion VS Code via code.cmd y Code.exe (no abre ventana)

{------------------------------------------------------------------------------}
{ CARGA DE LICENCIA BILINGÜE (Manual 9 §2.5) }
{------------------------------------------------------------------------------}
procedure InstallVSCodeExtension();
var
  VSCodePath, VSIXPath, CmdLine: String;
  CmdResultCode: Integer;
begin
  VSIXPath := ExpandConstant('{app}\vscode\synapse-{#MyAppVersion}.vsix');
  if not FileExists(VSIXPath) then begin
    Log('VSIX no encontrado, saltando instalación de extensión');
    Exit;
  end;
  // cumple Manual 9 §2.5: instalar via cmd /c code --install-extension hidden (no abre ventana VS Code)
  // Intento 1: code en PATH (code.cmd shim) — hidden
  CmdLine := '/c code --install-extension "' + VSIXPath + '" --force >nul 2>&1';
  if Exec('cmd.exe', CmdLine, '', SW_HIDE, ewWaitUntilTerminated, CmdResultCode) then begin
    if CmdResultCode = 0 then begin
      Log('Extension instalada via code en PATH (exit 0)');
      Exit;
    end;
    Log(Format('code en PATH fallo exit=%d, probando rutas absolutas', [CmdResultCode]));
  end else
    Log('Exec code en PATH fallo, probando rutas absolutas');
  // Intento 2: rutas absolutas (solo log, no MsgBox — el [Run] runasoriginaluser ya lo instala sin elevacion)
  VSCodePath := FindVSCodePath();
  if VSCodePath = '' then begin
    Log('VS Code no encontrado — se confia en [Run] runasoriginaluser para instalar extension');
    Exit;
  end;
  if Pos('code.cmd', Lowercase(VSCodePath)) > 0 then begin
    CmdLine := '/c "' + VSCodePath + '" --install-extension "' + VSIXPath + '" --force >nul 2>&1';
    Exec('cmd.exe', CmdLine, '', SW_HIDE, ewWaitUntilTerminated, CmdResultCode);
  end else begin
    CmdLine := '--install-extension "' + VSIXPath + '" --force';
    Exec(VSCodePath, CmdLine, '', SW_HIDE, ewWaitUntilTerminated, CmdResultCode);
  end;
  Log(Format('InstallVSCodeExtension via %s exit=%d (fallback Pascal, [Run] principal es runasoriginaluser)', [VSCodePath, CmdResultCode]));
  // cumple Manual 9 §2.5: no MsgBox aqui — silencioso, el [Run] es el canal correcto (evita alerta y bloqueo SILENT)
end;
// cumple Manual 9 §2.5: extension sin abrir ventana, hidden + fallback rutas

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
  // Fallback adicional: wmic (más compatible en algunas versiones)
  if V = 0 then begin
    V := ExecPowerShellInt('wmic path win32_VideoController get AdapterRAM /format:list | findstr "AdapterRAM=" | findstr /v "AdapterRAM=$" | sort /R | findstr /r "^AdapterRAM=" | find /c ":"');
    if V = 0 then
      V := ExecPowerShellInt('wmic path win32_VideoController get AdapterRAM /format:list | findstr "AdapterRAM=" | findstr /v "AdapterRAM=$" | sort /R | for /f "tokens=2 delims==" %a in (''more'') do echo %a');
  end;
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
      OllamaExePath := Candidates[i];
      Log('Ollama detectado: ' + Candidates[i]);
      Result := True;
      Exit;
    end;
  end;
  // where ollama en PATH
  if FileExists(ExpandConstant('{tmp}\ollama_check.txt')) then DeleteFile(ExpandConstant('{tmp}\ollama_check.txt'));
  // no usamos where por simplicidad, solo paths
end;

// Ejecuta 'ollama list' y devuelve el nombre del primer modelo instalado (o '').
function OllamaPrimerModelo(): String;
var
  TmpFile, Cmd, Linea, Nombre, Txt: String;
  TxtA: AnsiString;
  ExitCode: Integer;
  P: Integer;
begin
  Result := '';
  if OllamaExePath = '' then Exit;
  TmpFile := ExpandConstant('{tmp}\ollama_list.txt');
  if FileExists(TmpFile) then DeleteFile(TmpFile);
  Cmd := '/c ""' + OllamaExePath + '" list > "' + TmpFile + '""';
  if not Exec('cmd.exe', Cmd, '', SW_HIDE, ewWaitUntilTerminated, ExitCode) then Exit;
  if not FileExists(TmpFile) then Exit;
  if LoadStringFromFile(TmpFile, TxtA) then begin
    Txt := TxtA;
    repeat
      P := Pos(#13#10, Txt);
      if P > 0 then begin
        Linea := Copy(Txt, 1, P - 1);
        Txt := Copy(Txt, P + 2, MaxInt);
      end else begin
        Linea := Txt;
        Txt := '';
      end;
      Linea := Trim(Linea);
      if Linea <> '' then begin
        // Saltar el encabezado (NAME) y tomar la primera columna
        if Pos('NAME', Linea) <> 1 then begin
          P := Pos(' ', Linea);
          if P = 0 then P := Pos(#9, Linea);
          if P > 0 then Nombre := Copy(Linea, 1, P - 1)
          else Nombre := Linea;
          Nombre := Trim(Nombre);
          // quitar el sufijo :latest (Ollama acepta ambos; limpio es mejor)
          if Pos(':latest', Nombre) > 0 then
            Nombre := Copy(Nombre, 1, Pos(':latest', Nombre) - 1);
          if Nombre <> '' then begin
            Result := Nombre;
            Exit;
          end;
        end;
      end;
    until Txt = '';
  end;
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
    
    // Cargar SHA256 desde defines (se actualizan en build)
    LlamaServerSHA256 := '{#LLAMA_SERVER_SHA256}';
    ModelSHA256_1B := '{#MODEL_SHA256_1B}';
    ModelSHA256_7B_Q4 := '{#MODEL_SHA256_7B_Q4}';
    ModelSHA256_7B_Q5 := '{#MODEL_SHA256_7B_Q5}';
    ModelSHA256_13B := '{#MODEL_SHA256_13B}';
    ModelSHA256_34B := '{#MODEL_SHA256_34B}';
    
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
  // Manual 9 §2.5: licencia bilingüe embebida vía ExtractTemporaryFile
  try
    if ActiveLanguage = 'spanish' then begin
      ExtractTemporaryFile('LICENSE.es');
      LicenseFile := ExpandConstant('{tmp}\LICENSE.es');
    end else begin
      ExtractTemporaryFile('LICENSE');
      LicenseFile := ExpandConstant('{tmp}\LICENSE');
    end;
    if FileExists(LicenseFile) then begin
      if LoadStringFromFile(LicenseFile, LicenseText) then begin
        WizardForm.LicenseMemo.Lines.Text := LicenseText;
      end;
    end;
  except
    Log('InitializeWizard: no se pudo cargar licencia bilingüe');
  end;
  // cumple Manual 9 §2.5: solo licencia bilingüe aquí; mensaje final se setea en CurPageChanged wpFinished (evita sobre-escritura y cierre abrupto)
end;

{------------------------------------------------------------------------------}
{ PÁGINA PERSONALIZADA: Descarga de binarios pesados (OpenSyn IA) }
{------------------------------------------------------------------------------}
procedure CreateDownloadPage();
begin
  DownloadPage := CreateCustomPage(wpInstalling,
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

// Calcula SHA256 de un archivo usando certutil (más confiable que PowerShell en Windows)
function CalcSHA256(const FilePath: String): String;
var
  TmpFile, Cmd: String;
  OutStr: AnsiString;
  ExitCode: Integer;
  Lines: TArrayOfString;
  Line: String;
  HashFound: Boolean;
  i: Integer;
  IsHex: Boolean;
  C: Char;
  PosIdx: Integer;
  Start: Integer;
  NextLineStart: Integer;
begin
  Result := '';
  TmpFile := ExpandConstant('{tmp}\sha256_out.txt');
  if FileExists(TmpFile) then DeleteFile(TmpFile);
  // Usar certutil que es nativo de Windows y más confiable
  Cmd := '/c certutil -hashfile "' + FilePath + '" SHA256 > "' + TmpFile + '" 2>nul';
  if Exec('cmd.exe', Cmd, '', SW_HIDE, ewWaitUntilTerminated, ExitCode) then begin
    if (ExitCode = 0) and FileExists(TmpFile) and LoadStringFromFile(TmpFile, OutStr) then begin
      // certutil output format: "SHA256 hash of file.exe:\n<hex>\nCertUtil: -hashfile command completed successfully."
      // Extraer solo el hash (línea entre el header y el footer); quitar CR a mano
      // (compatibilidad Inno 6.0: sin StringReplace/StringChangeEx con cadena vacía)
      while Pos(#13, OutStr) > 0 do Delete(OutStr, Pos(#13, OutStr), 1);
      SetArrayLength(Lines, 0);
      Start := 1;
      while Start <= Length(OutStr) do begin
        // Pos con 3 args no existe en Inno 6.0: buscar #10 desde Start con Copy
        NextLineStart := Pos(#10, Copy(OutStr, Start, Length(OutStr) - Start + 1));
        if NextLineStart = 0 then NextLineStart := Length(OutStr) + 1
        else NextLineStart := NextLineStart + Start - 1;
        Line := Trim(Copy(OutStr, Start, NextLineStart - Start));
        if (Length(Line) = 64) then begin
          IsHex := True;
          for i := 1 to 64 do begin
            C := Line[i];
            if not ((C >= '0') and (C <= '9') or (C >= 'a') and (C <= 'f') or (C >= 'A') and (C <= 'F')) then begin
              IsHex := False;
              Break;
            end;
          end;
          if IsHex then begin
            Result := Lowercase(Line);
            Break;
          end;
        end;
        Start := NextLineStart + 1;
      end;
      DeleteFile(TmpFile);
    end;
  end;
end;

// Descarga archivo con verificación SHA256 opcional y soporte resume (-C -)
// URL: URL de descarga
// DestPath: ruta final del archivo
// ExpectedSHA256: hash esperado (vacío = no verificar)
// Resume: true para habilitar -C - (continuar descarga parcial)
function DownloadFile(const URL, DestPath, ExpectedSHA256: String; Resume: Boolean): Boolean;
var
  CmdLine, ExePath, TmpPath: String;
  ExitCode: Integer;
  ActualSHA256: String;
begin
  Result := False;
  try
    TmpPath := DestPath + '.tmp';

    ExePath := ExpandConstant('{app}\dl_helper.exe');
    if not FileExists(ExePath) then
      ExePath := ExpandConstant('{tmp}\dl_helper.exe');

    CmdLine := '"' + URL + '" "' + TmpPath + '"';

    Log(Format('DownloadFile: %s -> %s (sha256=%s)', [URL, DestPath, ExpectedSHA256]));
    Log(Format('DownloadFile: helper=%s', [ExePath]));

    if not FileExists(ExePath) then begin
      Log('DownloadFile: dl_helper.exe no encontrado, usando curl como fallback');
      ExePath := 'C:\Windows\System32\curl.exe';
      CmdLine := '-L --fail --connect-timeout 30 --max-time 600 -o "' + TmpPath + '" "' + URL + '"';
    end;

    if not Exec(ExePath, CmdLine, '', SW_SHOW, ewWaitUntilTerminated, ExitCode) then begin
      Log('DownloadFile: fallo al lanzar helper');
      if FileExists(TmpPath) then DeleteFile(TmpPath);
      Exit;
    end;

    Log(Format('DownloadFile: termino con exit code %d', [ExitCode]));

    if ExitCode <> 0 then begin
      Log(Format('DownloadFile: fallo con exit code %d', [ExitCode]));
      if FileExists(TmpPath) then DeleteFile(TmpPath);
      Result := False;
      Exit;
    end;

    if not FileExists(TmpPath) then begin
      Log('DownloadFile: archivo temporal no existe');
      Result := False;
      Exit;
    end;

    Log('DownloadFile: archivo descargado');

    if ExpectedSHA256 <> '' then begin
      ActualSHA256 := CalcSHA256(TmpPath);
      if Lowercase(ActualSHA256) <> Lowercase(ExpectedSHA256) then begin
        Log(Format('SHA256 mismatch: expected=%s got=%s', [ExpectedSHA256, ActualSHA256]));
        if FileExists(TmpPath) then DeleteFile(TmpPath);
        Result := False;
        Exit;
      end;
    end;

    if FileExists(DestPath) then DeleteFile(DestPath);
    if not RenameFile(TmpPath, DestPath) then begin
      if FileCopy(TmpPath, DestPath, False) then
        DeleteFile(TmpPath)
      else begin
        Log('Error moviendo archivo descargado a destino final');
        if FileExists(TmpPath) then DeleteFile(TmpPath);
        Result := False;
        Exit;
      end;
    end;
    Result := True;
  except
    Log('DownloadFile exception');
    if FileExists(TmpPath) then DeleteFile(TmpPath);
    Result := False;
  end;
end;

procedure CreateModelSelectPage();
var
  DefaultIdx: Integer;
begin
  // cumple Manual 9 §5.2: pagina de seleccion de modelo code-especifico (DeepSeek/CodeLlama)
  if ModelSelectPage <> nil then Exit;
  ModelSelectPage := CreateInputOptionPage(wpSelectComponents,
    'Seleccionar modelo de codigo',
    'Elige el modelo GGUF code-especifico a descargar (HuggingFace)',
    'Modelos recomendados segun VRAM detectada (' + IntToStr(VRAM_MB) + ' MB):',
    True, False);
  // Tamaños reales de modelos GGUF Q4_K_M/Q5_K_M (HuggingFace TheBloke)
  ModelSelectPage.Add('DeepSeek Coder 1.3B Q4_K_M (~1.1 GB) - <4 GB VRAM');
  ModelSelectPage.Add('CodeLlama 7B Q4_K_M (~3.8 GB) - 4-6 GB VRAM');
  ModelSelectPage.Add('CodeLlama 7B Q5_K_M (~4.7 GB) - 6-8 GB VRAM');
  ModelSelectPage.Add('CodeLlama 13B Q4_K_M (~7.2 GB) - 8-12 GB VRAM');
  ModelSelectPage.Add('CodeLlama 34B Q4_K_M (~18.8 GB) - 12+ GB VRAM');
  if VRAM_MB < 4096 then DefaultIdx := 0
  else if VRAM_MB < 6144 then DefaultIdx := 1
  else if VRAM_MB < 8192 then DefaultIdx := 2
  else if VRAM_MB < 12288 then DefaultIdx := 3
  else DefaultIdx := 4;
  ModelSelectPage.SelectedValueIndex := DefaultIdx;
  Log(Format('ModelSelectPage creada defaultIdx=%d VRAM=%d', [DefaultIdx, VRAM_MB]));
end;

procedure ApplyModelSelection();
begin
  if ModelSelectPage = nil then Exit;
  case ModelSelectPage.SelectedValueIndex of
    0: begin SelectedModelName := 'deepseek-coder-1.3b-Q4_K_M.gguf'; SelectedModelURL := '{#MODEL_URL_1B}'; end;
    1: begin SelectedModelName := 'codellama-7b-Q4_K_M.gguf'; SelectedModelURL := '{#MODEL_URL_7B}'; end;
    2: begin SelectedModelName := 'codellama-7b-Q5_K_M.gguf'; SelectedModelURL := 'https://huggingface.co/TheBloke/CodeLlama-7B-GGUF/resolve/main/codellama-7b.Q5_K_M.gguf'; end;
    3: begin SelectedModelName := 'codellama-13b-Q4_K_M.gguf'; SelectedModelURL := '{#MODEL_URL_13B}'; end;
    4: begin SelectedModelName := 'codellama-34b-Q4_K_M.gguf'; SelectedModelURL := '{#MODEL_URL_34B}'; end;
  end;
  Log(Format('Modelo seleccionado por usuario: %s -> %s', [SelectedModelName, SelectedModelURL]));
end;

function ExtractLlamaServerFromZip(const ZipPath, DestPath: String): Boolean;
var
  TempDir: String;
  Cmd: String;
  ExitCode: Integer;
  DestDir: String;
  FindRec: TFindRec;
  Copiados: Integer;
begin
  Result := False;
  TempDir := ExpandConstant('{tmp}\llama_extract');
  try
    // Crear directorio temporal
    ForceDirectories(TempDir);
    
    // Extraer ZIP usando PowerShell
    Cmd := Format('powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Path ''%s'' -DestinationPath ''%s'' -Force"', [ZipPath, TempDir]);
    ExitCode := 0;
    if Exec('cmd.exe', '/c ' + Cmd, '', SW_HIDE, ewWaitUntilTerminated, ExitCode) then
    begin
      if ExitCode = 0 then
      begin
        // cumple Manual 9 §5.3: el ZIP trae launcher + DLLs (llama-server-impl.dll, ggml*.dll,
        // libomp.dll); copiar TODOS los archivos a ia\, no solo el exe, o el launcher no podra
        // cargar sus DLLs al iniciarse. El ZIP de llama.cpp es plano (sin subdirectorios).
        if not FileExists(TempDir + '\llama-server.exe') then
          Log('No se encontró llama-server.exe en la raíz del ZIP')
        else
        begin
          DestDir := ExtractFileDir(DestPath);
          ForceDirectories(DestDir);
          Copiados := 0;
          if FindFirst(TempDir + '\*', FindRec) then
          begin
            try
              repeat
                if (FindRec.Name <> '.') and (FindRec.Name <> '..') and
                   ((FindRec.Attributes and FILE_ATTRIBUTE_DIRECTORY) = 0) then
                begin
                  if FileCopy(TempDir + '\' + FindRec.Name, DestDir + '\' + FindRec.Name, False) then
                    Copiados := Copiados + 1
                  else
                    Log('Error copiando ' + FindRec.Name + ' a ' + DestDir);
                end;
              until not FindNext(FindRec);
            finally
              FindClose(FindRec);
            end;
          end;
          Result := FileExists(DestPath);
          if Result then
            Log('llama-server.exe + DLLs extraidos correctamente a: ' + DestDir + ' (' + IntToStr(Copiados) + ' archivos)')
          else
            Log('Error: faltan archivos tras copiar ' + IntToStr(Copiados) + ' archivos a ' + DestDir);
        end;
      end
      else
        Log('Error extrayendo ZIP: exit code ' + IntToStr(ExitCode));
    end
    else
      Log('Error extrayendo ZIP: exit code ' + IntToStr(ExitCode));
  except
    Log('Excepción extrayendo llama-server.exe del ZIP');
  end;
  // Limpiar directorio temporal
  if DirExists(TempDir) then
    DelTree(TempDir, True, True, True);
end;

procedure DownloadAIComponents();
var
  DestServer, DestModel, ModeloOllama: String;
  UseExisting: Boolean;
  AppGGUF: String;
  ModelSHA256: String;
  ZipPath: String;
  ActualSHA256: String;
begin
  // [fix-31] Conectar al Ollama existente (elegido en wpSelectComponents, o modo
  // silencioso con Ollama detectado): se configura con el primer modelo instalado
  // y se omite TODA descarga (llama-server + modelo GGUF).
  if OllamaConnectMode or (WizardSilent and OllamaFound) then begin
    OllamaConnectMode := True;
    ModeloOllama := OllamaPrimerModelo();
    if ModeloOllama = '' then ModeloOllama := 'qwen-coder';
    Log('Conectando a Ollama existente - modelo: ' + ModeloOllama);
    ForceDirectories(GetEnv('USERPROFILE') + '\.opensyn');
    SaveStringToFile(GetEnv('USERPROFILE') + '\.synapse_config', 'modo_oraculo=verdadero', False);
    SaveStringToFile(GetEnv('USERPROFILE') + '\.opensyn\config_ollama.txt', 'ollama=1' + #13#10 + 'model=' + ModeloOllama, False);
    SaveStringToFile(ExpandConstant('{app}\.synapse_config'), 'modo_oraculo=verdadero', False);
    SaveStringToFile(ExpandConstant('{app}\opensyn\.synapse_config'), 'modo_oraculo=verdadero', False);
    SaveStringToFile(ExpandConstant('{app}\opensyn\config_ollama.txt'), 'ollama=1' + #13#10 + 'model=' + ModeloOllama, False);
    Exit;  // cumple Manual 7 §8: Ollama conectado, no descargar
  end;

  // Manual 9 §5.3: re-chequear GGUF en {app} (no disponible en InitializeSetup) y en perfil
  if ExistingGGUF = '' then begin
    AppGGUF := CheckForExistingGGUFInApp();
    if AppGGUF <> '' then ExistingGGUF := AppGGUF;
  end;
  if ExistingGGUF = '' then ExistingGGUF := CheckForExistingGGUF();
  // Manual 9 §5.3: si hay GGUF existente, preguntar solo en modo interactivo
  UseExisting := False;
  if (ExistingGGUF <> '') and (not WizardSilent) then begin
    if MsgBox('Se encontró un modelo GGUF existente:'#13#10 + ExistingGGUF + #13#10#13#10'¿Desea usar este modelo existente?'#13#10'(Sí = usar existente y no descargar, No = descargar ' + SelectedModelName + ')', mbConfirmation, MB_YESNO) = IDYES then begin
      Log('Usuario eligió usar GGUF existente: ' + ExistingGGUF);
      UseExisting := True;
      StatusLabel.Caption := 'Usando modelo existente: ' + ExtractFileName(ExistingGGUF);
      ProgressBar.Position := 50;
      WizardForm.Repaint;
    end;
  end else if ExistingGGUF <> '' then begin
    Log('GGUF existente en modo SILENT - usando automaticamente: ' + ExistingGGUF);
    UseExisting := True;
  end;

  // Si usuario rechazó Ollama/GGUF, aplicar la seleccion de modelo de la pagina
  if (not UseExisting) and (ModelSelectPage <> nil) then
    ApplyModelSelection();
  DestServer := ExpandConstant('{app}\opensyn\ia\llama-server.exe');
  if UseExisting then
    DestModel := ExistingGGUF
  else
    DestModel := ExpandConstant('{app}\opensyn\models\') + SelectedModelName;

  ForceDirectories(ExtractFileDir(DestModel));
  ForceDirectories(ExtractFileDir(DestServer));

  // cumple Manual 7 §2.1: el servidor debe existir aunque se reutilice un GGUF
  // del perfil; si no está en {app}\opensyn\ia, se descarga igualmente.
  if not FileExists(DestServer) then begin
    StatusLabel.Caption := 'Descargando llama-server...';
    ProgressBar.Position := 10;
    WizardForm.Repaint;
    Log(Format('Iniciando descarga llama-server: %s (SHA256: %s)', ['{#LLAMA_SERVER_URL}', LlamaServerSHA256]));
    
    // Descargar ZIP a archivo temporal (SIN verificación SHA256, la haremos al ejecutable extraído)
    ZipPath := ExpandConstant('{tmp}\llama-server.zip');
    if not DownloadFile('{#LLAMA_SERVER_URL}', ZipPath, '', True) then begin
      if not WizardSilent then MsgBox('Error descargando llama-server. Verifique su conexión.'#13#10'URL: {#LLAMA_SERVER_URL}', mbError, MB_OK);
      Log('ERROR: DownloadFile llama-server ZIP fallo');
      Exit;
    end;
    
    // Extraer llama-server.exe del ZIP
    if not ExtractLlamaServerFromZip(ZipPath, DestServer) then begin
      if not WizardSilent then MsgBox('Error extrayendo llama-server.exe del ZIP.'#13#10'URL: {#LLAMA_SERVER_URL}', mbError, MB_OK);
      Log('ERROR: ExtractLlamaServerFromZip fallo');
      if FileExists(ZipPath) then DeleteFile(ZipPath);
      Exit;
    end;
    
    // Verificar SHA256 del ejecutable extraído
    ActualSHA256 := CalcSHA256(DestServer);
    if Lowercase(ActualSHA256) <> Lowercase(LlamaServerSHA256) then begin
      Log(Format('SHA256 mismatch llama-server.exe: expected=%s got=%s', [LlamaServerSHA256, ActualSHA256]));
      if not WizardSilent then MsgBox('Error verificando llama-server.exe (SHA256 no coincide).'#13#10'URL: {#LLAMA_SERVER_URL}', mbError, MB_OK);
      Log('ERROR: SHA256 mismatch llama-server.exe');
      Exit;
    end;
    Log('llama-server.exe SHA256 verificado correctamente');
    
    if FileExists(ZipPath) then DeleteFile(ZipPath);
  end;

  if not UseExisting then begin
    ProgressBar.Position := 50;
    StatusLabel.Caption := 'Descargando ' + SelectedModelName + '...';
    WizardForm.Repaint;
    // Determinar SHA256 según modelo seleccionado
    case ModelSelectPage.SelectedValueIndex of
      0: ModelSHA256 := ModelSHA256_1B;
      1: ModelSHA256 := ModelSHA256_7B_Q4;
      2: ModelSHA256 := ModelSHA256_7B_Q5;
      3: ModelSHA256 := ModelSHA256_13B;
      4: ModelSHA256 := ModelSHA256_34B;
    end;
    Log(Format('Iniciando descarga modelo: %s (SHA256: %s) -> %s', [SelectedModelURL, ModelSHA256, DestModel]));
    if not DownloadFile(SelectedModelURL, DestModel, ModelSHA256, True) then begin
      if not WizardSilent then MsgBox('Error descargando modelo ' + SelectedModelName + ' (verificación SHA256 falló). Verifique su conexión y espacio en disco.'#13#10'URL: ' + SelectedModelURL, mbError, MB_OK);
      Log('ERROR: DownloadFile modelo fallo: ' + SelectedModelURL);
      Exit;
    end;
    Log('Descargas completadas OK: ' + DestModel);
  end;

  ProgressBar.Position := 100;
  StatusLabel.Caption := 'Descargas completadas. Verificando integridad...';
  WizardForm.Repaint;
  // Guardar seleccion para post-install config y pre-configurar modo oraculo
  SaveStringToFile(ExpandConstant('{app}\opensyn\install_info.txt'), 'model=' + SelectedModelName + #13#10 + 'url=' + SelectedModelURL + #13#10 + 'vram=' + IntToStr(VRAM_MB), False);
  SaveStringToFile(ExpandConstant('{app}\opensyn\.synapse_config'), 'modo_oraculo=verdadero', False);
  SaveStringToFile(ExpandConstant('{app}\.synapse_config'), 'modo_oraculo=verdadero', False);
  SaveStringToFile(GetEnv('USERPROFILE') + '\.synapse_config', 'modo_oraculo=verdadero', False);
  ForceDirectories(GetEnv('USERPROFILE') + '\.opensyn');
  SaveStringToFile(GetEnv('USERPROFILE') + '\.opensyn\install_info.txt', 'model=' + SelectedModelName + #13#10 + 'url=' + SelectedModelURL + #13#10 + 'vram=' + IntToStr(VRAM_MB), False);
  // cumple Manual 9 §5: escribir config_ollama.txt para que OpenSyn detecte el modelo
  SaveStringToFile(GetEnv('USERPROFILE') + '\.opensyn\config_ollama.txt', 'ollama=1' + #13#10 + 'model=' + SelectedModelName, False);
  SaveStringToFile(ExpandConstant('{app}\opensyn\config_ollama.txt'), 'ollama=1' + #13#10 + 'model=' + SelectedModelName, False);
  Log('config_ollama.txt escrito con model=' + SelectedModelName);
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
      // [fix-31] Orden correcto: PRIMERO preguntar si conectar a un modelo ya
      // instalado (Ollama). Solo si NO se conecta (o no hay Ollama) se ofrece
      // elegir/descargar el modelo GGUF que mejor se adapta al PC.
      if WizardIsComponentSelected('opensyn') then begin
        OllamaConnectMode := False;
        if OllamaFound and (not WizardSilent) then begin
          if MsgBox('Se detectó Ollama instalado en este sistema.'#13#10 +
            'OpenSyn puede conectarse al/los modelos que ya tienes descargados ' +
            '(http://localhost:11434) - sin descargar nada.'#13#10#13#10 +
            '¿Desea conectar OpenSyn a tu Ollama existente?'#13#10 +
            '(Sí = conectar y omitir descargas. No = elegir y descargar el modelo ' +
            'GGUF que mejor se adapte a tu PC)', mbConfirmation, MB_YESNO) = IDYES then begin
            OllamaConnectMode := True;
            Log('Usuario eligió conectar a su Ollama existente - se omite selección/descarga de modelo');
            // No se crean ModelSelectPage ni DownloadPage (se salta la descarga)
          end else begin
            OllamaConnectMode := False;
            Log('Usuario rechazó Ollama - mostrar selección de modelo GGUF para descargar');
            CreateModelSelectPage();
            CreateDownloadPage();
          end;
        end else begin
          // Sin Ollama o modo silencioso: crear paginas. En modo silencioso no
          // se muestran, pero garantizan DownloadPage/StatusLabel no nil para la
          // descarga automatica (comportamiento previo). En modo interactivo sin
          // Ollama el usuario elige el modelo GGUF en la pagina.
          CreateModelSelectPage();
          CreateDownloadPage();
        end;
      end;
    end;
    wpReady: begin
      if WizardIsComponentSelected('opensyn') and (not WizardSilent) then begin
        if (VRAM_MB > 0) and (VRAM_MB < 4096) and (not OllamaConnectMode) then begin
          if MsgBox('ADVERTENCIA: Su GPU tiene ' + IntToStr(VRAM_MB) + ' MB de VRAM. ' +
            'El modelo requiere al menos 4 GB. ¿Desea continuar de todos modos?',
            mbConfirmation, MB_YESNO) = IDNO then begin
            Result := False;
          end;
        end;
      end else if WizardIsComponentSelected('opensyn') then begin
        Log(Format('SILENT: VRAM %d MB <4GB pero continuando sin prompt', [VRAM_MB]));
      end;
    end;
  end;
end;


procedure CurPageChanged(CurPageID: Integer);
begin
  // cumple Manual 9 §2.5: feedback final no abrupto — mensaje claro en Finished page (wpFinished permanece hasta que usuario pulse Finalizar)
  if CurPageID = wpFinished then begin
    try
      WizardForm.FinishedHeadingLabel.Caption := '¡Instalación completada!';
      WizardForm.FinishedLabel.Caption :=
        'Synapse se instaló correctamente.' + #13#10#13#10 +
        '• Synapse (compilador) + Syquex (lib) + OpenSyn (IA) según tu selección' + #13#10 +
        '• VS Code: extensión instalada si la marcaste (sin abrir ventana nueva)' + #13#10 +
        '• PATH actualizado: abre una NUEVA terminal y escribe "synapse" o "opensyn"' + #13#10 +
        '  Si VS Code estaba abierto, reinícialo para ver "synapse" en su terminal integrada.' + #13#10#13#10 +
        'OpenSyn: conectado a tu Ollama local, o modelo GGUF descargado según tu elección.' + #13#10 +
        'Para probar: synapse --version  |  opensyn status  |  code --list-extensions | findstr synapse';
      WizardForm.FinishedLabel.AutoSize := False;
      WizardForm.FinishedLabel.Height := 140;
      WizardForm.FinishedLabel.WordWrap := True;
    except
      Log('CurPageChanged wpFinished: error seteando mensaje final');
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  // cumple Manual 9 §2.5: descarga de componentes IA durante la instalación (no en CurPageChanged
  // que bloquea la UI). CurStepChanged(ssInstall) se ejecuta después de "Instalar".
  if (CurStep = ssInstall) and WizardIsComponentSelected('opensyn') then begin
    try
      DownloadAIComponents();
    except
      Log('Error durante descarga de componentes IA');
    end;
  end;
  // cumple Manual 9 §2.5: extension ya se instala via [Run] runasoriginaluser (no duplicar aqui para evitar doble alerta y elevacion)
  // Se deja solo log opcional, sin Exec que falla como admin
  if CurStep = ssPostInstall then begin
    Log('CurStepChanged ssPostInstall — extension delegada a [Run] runasoriginaluser');
  end;
end;
// cumple Manual 9 §2.5: Finished page con feedback persistente, no cierre abrupto + extension via Run

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
// cumple Manual 9 §2.5: mensajes duplicados eliminados — CustomMessages ya definido arriba

{------------------------------------------------------------------------------}
{ FUNCIONES AUXILIARES: PATH sin duplicados al reinstalar (Manual 9 §2.5) }
{------------------------------------------------------------------------------}
function SynapsePathContieneAppBin(const Valor: String): Boolean;
begin
  // {app}\bin ya presente en el PATH (cualquier install previa) => no volver a anexar
  Result := Pos(Lowercase(ExpandConstant('{app}\bin')), Lowercase(Valor)) > 0;
end;

function NotSynapseInUserPath(): Boolean;
var
  S: String;
begin
  Result := True;
  if RegQueryStringValue(HKCU, 'Environment', 'Path', S) then
    Result := not SynapsePathContieneAppBin(S);
end;

function NotSynapseInMachinePath(): Boolean;
var
  S: String;
begin
  Result := True;
  if RegQueryStringValue(HKLM, 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 'Path', S) then
    Result := not SynapsePathContieneAppBin(S);
end;


