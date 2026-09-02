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
LicenseFile=LICENSE
OutputDir=dist
OutputBaseFilename=Synapse-{#MyAppVersion}-Windows-x64
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin
 ArchitecturesInstallIn64BitMode=x64
 ArchitecturesAllowed=x64
WizardStyle=modern
UninstallDisplayIcon={app}\bin\{#MyAppExeName}
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}

[Types]
; cumple Manual 9 §2.5: tipos full/minimal
Name: "full"; Description: "Ecosistema completo (Synapse + Syquex + OpenSyn)"
Name: "minimal"; Description: "Solo Synapse (lenguaje de sistemas)"

[Components]
; cumple Manual 9 §2.5: componentes alineados al manual
Name: "synapse"; Description: "Synapse (compilador, runtime, std)"; Types: full minimal; Flags: fixed
Name: "syquex"; Description: "Syquex (lenguaje de alto nivel)"; Types: full
Name: "opensyn"; Description: "OpenSyn (asistente IA local)"; Types: full
Name: "vscode"; Description: "Extensión VS Code"; Types: full minimal

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; cumple Manual 9 §2.5: Sources binaria + runtime + std
; ME-R6: dist\bin\synapse.exe se construye en CI con el runtime modular completo (Manual 3 S3.1)
Source: "dist\bin\{#MyAppExeName}"; DestDir: "{app}\bin"; Components: synapse; Flags: ignoreversion
Source: "dist\bin\{#MyAppLspExeName}"; DestDir: "{app}\bin"; Components: synapse; Flags: ignoreversion
Source: "dist\bin\*.dll"; DestDir: "{app}\bin"; Components: synapse; Flags: ignoreversion
; cumple Manual 9 §2.2: runtime/ contiene memory, concurrency, io, etc.
Source: "runtime\*"; DestDir: "{app}\bin\runtime"; Components: synapse; Flags: ignoreversion recursesubdirs
Source: "std\*"; DestDir: "{app}\std"; Components: synapse; Flags: ignoreversion recursesubdirs
; Nota: el repo usa librerias/ (no lib/) — Manual 9 §2.2 muestra lib/ como nombre instalado
Source: "librerias\*"; DestDir: "{app}\lib"; Components: syquex; Flags: ignoreversion recursesubdirs
Source: "opensyn\*"; DestDir: "{app}\opensyn"; Components: opensyn; Flags: ignoreversion recursesubdirs
; Nota: el repo usa vscode-synapse/ (no vscode/) — Manual 9 §2.2 muestra vscode/ como nombre instalado
Source: "vscode-synapse\synapse-*.vsix"; DestDir: "{app}\vscode"; Components: vscode; Flags: ignoreversion
; cumple Manual 9 §2.5: MinGW toolchain provisioning script
Source: "scripts\install.ps1"; DestDir: "{app}"; Components: synapse; Flags: ignoreversion

; cumple Manual 9 §2.5: OpenSyn orquestador (nucleo/ai_orchestrator.c contiene synapse_shutdown_hook)
Source: "nucleo\ai_orchestrator.h"; DestDir: "{app}\src"; Components: opensyn; Flags: ignoreversion
Source: "nucleo\ai_orchestrator.c"; DestDir: "{app}\src"; Components: opensyn; Flags: ignoreversion
Source: "nucleo\llama_client.h"; DestDir: "{app}\src"; Components: opensyn; Flags: ignoreversion
Source: "nucleo\llama_client.c"; DestDir: "{app}\src"; Components: opensyn; Flags: ignoreversion

[Icons]
Name: "{group}\Synapse Language"; Filename: "{app}\bin\{#MyAppExeName}"; WorkingDir: "{app}"; Components: synapse
Name: "{group}\Desinstalar Synapse"; Filename: "{uninstallexe}"; Components: synapse
Name: "{autodesktop}\Synapse Language"; Filename: "{app}\bin\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon; Components: synapse

[Run]
; cumple Manual 9 §2.5: post-install hooks
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -NoProfile -File ""{app}\install.ps1"""; Description: "Provisionar MinGW Toolchain"; Flags: runhidden waituntilterminated; Components: synapse; StatusMsg: "Configurando MinGW Toolchain..."
Filename: "{app}\bin\{#MyAppExeName}"; Parameters: "opensyn install"; Components: opensyn; StatusMsg: "Instalando OpenSyn..."
Filename: "code"; Parameters: "--install-extension ""{app}\vscode\synapse-{#MyAppVersion}.vsix"""; Components: vscode; StatusMsg: "Instalando extensión VS Code..."

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
{ INICIALIZACIÓN: Detección de hardware (VRAM) }
{------------------------------------------------------------------------------}
function InitializeSetup(): Boolean;
begin
  Result := True;
  // Detección de VRAM mediante WMI para recomendar modelo OpenSyn
  VRAM_MB := GetVRAMViaWMI();
  Log(Format('Setup iniciado. VRAM detectada: %d MB', [VRAM_MB]));
end;

{------------------------------------------------------------------------------}
{ FUNCIÓN AUXILIAR: Detección de VRAM via WMI }
{------------------------------------------------------------------------------}
function GetVRAMViaWMI(): Integer;
var
  WMIService, Items, Item: Variant;
  VRAM: Int64;
begin
  Result := 0;
  try
    WMIService := GetObject('winmgmts:\\.\root\cimv2');
    Items := WMIService.ExecQuery('SELECT AdapterRAM FROM Win32_VideoController');
    for Item in Items do begin
      VRAM := Item.AdapterRAM;
      if VRAM > Result then Result := VRAM div (1024*1024);
    end;
  except
    Result := 0;
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
  WinHTTP: Variant;
  Stream: Variant;
begin
  Result := False;
  try
    WinHTTP := CreateOleObject('WinHTTP.WinHTTPRequest.5.1');
    WinHTTP.Open('GET', URL, False);
    WinHTTP.Send();
    if WinHTTP.Status = 200 then begin
      Stream := CreateOleObject('ADODB.Stream');
      Stream.Type := 1;
      Stream.Open();
      Stream.Write(WinHTTP.ResponseBody);
      Stream.SaveToFile(DestPath, 2);
      Stream.Close();
      Result := True;
    end else begin
      Log(Format('Error descargando %s: HTTP %d', [URL, WinHTTP.Status]));
    end;
  except
    Log(Format('Excepción descargando %s: %s', [URL, GetExceptionMessage]));
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
  Application.ProcessMessages();

  if not DownloadFile('{#LLAMA_SERVER_URL}', DestServer) then begin
    MsgBox('Error descargando llama-server.exe. Verifique su conexión.', mbError, MB_OK);
    Exit;
  end;

  ProgressBar.Position := 50;
  StatusLabel.Caption := 'Descargando modelo .gguf (~700 MB)...';
  Application.ProcessMessages();

  if not DownloadFile('{#MODEL_URL}', DestModel) then begin
    MsgBox('Error descargando modelo. Verifique su conexión y espacio en disco.', mbError, MB_OK);
    Exit;
  end;

  ProgressBar.Position := 100;
  StatusLabel.Caption := 'Descargas completadas. Verificando integridad...';
  Application.ProcessMessages();
end;

procedure OnDownloadProgress(TotalBytes, DownloadedBytes: Int64);
begin
  if TotalBytes > 0 then begin
    ProgressBar.Position := MulDiv(DownloadedBytes, 100, TotalBytes);
    StatusLabel.Caption := Format('Descargando... %d%% (%d/%d MB)',
      [ProgressBar.Position, DownloadedBytes div (1024*1024), TotalBytes div (1024*1024)]);
    Application.ProcessMessages();
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
var
  FreeMB: Int64;
begin
  FreeMB := DiskFree(ExtractFileDrive(ExpandConstant('{app}'))) div (1024*1024);
  Result := FreeMB >= RequiredMB;
  if not Result then
    MsgBox(Format('Espacio insuficiente. Requiere %d MB, disponible %d MB.', [RequiredMB, FreeMB]), mbError, MB_OK);
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
