; instalador_synapse.iss — Instalador Maestro Modular para Synapse Language
; Genera el instalador .exe para Windows con embudo de decisiones modular
; Compilar con: iscc instalador_synapse.iss

#define MyAppName "Synapse Language"
#define MyAppVersion "2.2.2"
#define MyAppPublisher "Synapse Language Team"
#define MyAppURL "https://github.com/synapse-lang/synapse"
#define MyAppExeName "synapse.exe"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName=C:\Synapse
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=LICENSE.txt
OutputDir=dist
OutputBaseFilename=Synapse-{#MyAppVersion}-Windows-x64
Compression=lzma/ultra64
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64
WizardStyle=modern
SetupIconFile=assets\synapse.ico
UninstallDisplayIcon={app}\synapse.exe
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}

[Types]
; Embudo de decisiones modular - el usuario elige qué instalar
Name: "core_only"; Description: "Synapse Core (Ligero - Solo Lenguaje, MinGW y VSIX)"; Flags: iscustom
Name: "opensyn_full"; Description: "OpenSyn (Completo - Lenguaje + IA Local Autónoma)"; Flags: iscustom

[Components]
; Componente base obligatorio
Name: "core"; Description: "Compilador Synapse, MinGW Toolchain, Extensión VS Code"; Types: core_only opensyn_full; Flags: fixed

; Componente IA Local (opcional, solo en opensyn_full)
Name: "ai_engine"; Description: "Motor IA Local (llama-server.exe + modelo .gguf + orchestrador C)"; Types: opensyn_full; Flags: 

; Sub-componentes del motor IA
Name: "ai_engine\llama_server"; Description: "llama-server.exe (binario servidor inferencia)"; Types: opensyn_full; Flags: 
Name: "ai_engine\model"; Description: "Modelo .gguf (Llama-3.2-1B-Instruct-Q4_K_M, ~700MB)"; Types: opensyn_full; Flags: 

[Files]
; --- CORE (Siempre) ---
Source: "dist\bin\synapse.exe"; DestDir: "{app}\bin"; Components: core; Flags: ignoreversion
Source: "dist\bin\*.dll"; DestDir: "{app}\bin"; Components: core; Flags: ignoreversion
Source: "dist\lib\*"; DestDir: "{app}\lib"; Components: core; Flags: ignoreversion recursesubdirs
Source: "dist\include\*"; DestDir: "{app}\include"; Components: core; Flags: ignoreversion recursesubdirs
Source: "dist\axon.toml"; DestDir: "{app}"; Components: core; Flags: ignoreversion
Source: "dist\synapse_rt.h"; DestDir: "{app}"; Components: core; Flags: ignoreversion
Source: "vscode-synapse\synapse-vscode-v2.2.2.vsix"; DestDir: "{app}\vscode"; Components: core; Flags: ignoreversion
Source: "synapse_rt.c"; DestDir: "{app}\src"; Components: core; Flags: ignoreversion
Source: "tweetnacl.h"; DestDir: "{app}\src"; Components: core; Flags: ignoreversion
Source: "tweetnacl.c"; DestDir: "{app}\src"; Components: core; Flags: ignoreversion

; --- AI ENGINE (Solo en opensyn_full) ---
Source: "dist\ia\llama-server.exe"; DestDir: "{app}\ia"; Components: ai_engine\llama_server; Flags: ignoreversion
Source: "dist\ia\model.gguf"; DestDir: "{app}\ia"; Components: ai_engine\model; Flags: ignoreversion
Source: "nucleo\ai_orchestrator.h"; DestDir: "{app}\include"; Components: ai_engine; Flags: ignoreversion
Source: "nucleo\ai_orchestrator.c"; DestDir: "{app}\src"; Components: ai_engine; Flags: ignoreversion
Source: "nucleo\llama_client.h"; DestDir: "{app}\include"; Components: ai_engine; Flags: ignoreversion
Source: "nucleo\llama_client.c"; DestDir: "{app}\src"; Components: ai_engine; Flags: ignoreversion

[Icons]
Name: "{group}\Synapse Language"; Filename: "{app}\bin\synapse.exe"; WorkingDir: "{app}"; Components: core
Name: "{group}\Desinstalar Synapse"; Filename: "{uninstallexe}"; Components: core

[Run]
; Paso final: ejecutar install.ps1 para aprovisionar MinGW (Fase 1)
; Solo si el componente core está instalado
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -NoProfile -File ""{app}\install.ps1"""; Description: "Provisionar MinGW Toolchain"; Flags: runhidden waituntilterminated; Components: core; StatusMsg: "Configurando MinGW Toolchain..."

; Regenerar embedded_libs.h tras instalación
Filename: "cmd.exe"; Parameters: "/c python ""{app}\tests\_gen_embedded.py"""; Description: "Regenerando librerías embebidas"; Components: core; Flags: runhidden waituntilterminated

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

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
var
  DxDiagPath: String;
  ResultCode: Integer;
begin
  Result := True;
  
  { Detección de VRAM mediante WMI/DXDiag para recomendar modelo }
  { TODO: Implementar consulta WMI a Win32_VideoController }
  { VRAM_MB := GetVRAMViaWMI(); }
  VRAM_MB := 0; { Placeholder }
  
  { Log para depuración }
  Log(Format('Setup iniciado. VRAM detectada: %d MB', [VRAM_MB]));
end;

{------------------------------------------------------------------------------}
{ PÁGINA PERSONALIZADA: Descarga de binarios pesados }
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

{------------------------------------------------------------------------------}
{ LÓGICA DE DESCARGA: Se ejecuta en hilo separado }
{------------------------------------------------------------------------------}
function DownloadFile(const URL, DestPath: String; var Progress: Integer): Boolean;
var
  WinHTTP: Variant;
  Stream: Variant;
  HTTP: Variant;
begin
  Result := False;
  try
    { Usar WinHTTP para descarga robusta con progreso }
    WinHTTP := CreateOleObject('WinHTTP.WinHTTPRequest.5.1');
    WinHTTP.Open('GET', URL, False);
    WinHTTP.Send();
    
    if WinHTTP.Status = 200 then begin
      Stream := CreateOleObject('ADODB.Stream');
      Stream.Type := 1; { adTypeBinary }
      Stream.Open();
      Stream.Write(WinHTTP.ResponseBody);
      Stream.SaveToFile(DestPath, 2); { adSaveCreateOverWrite }
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
const
  LLAMA_SERVER_URL = 'https://github.com/ggerganov/llama.cpp/releases/download/bXXXX/llama-server.exe';
  MODEL_URL = 'https://huggingface.co/TheBloke/Llama-3.2-1B-Instruct-GGUF/resolve/main/llama-3.2-1b-instruct.Q4_K_M.gguf';
var
  DestServer, DestModel: String;
begin
  DestServer := ExpandConstant('{app}\ia\llama-server.exe');
  DestModel := ExpandConstant('{app}\ia\model.gguf');
  
  StatusLabel.Caption := 'Descargando llama-server.exe (~15 MB)...';
  ProgressBar.Position := 10;
  Application.ProcessMessages();
  
  if not DownloadFile(LLAMA_SERVER_URL, DestServer, ProgressBar.Position) then begin
    MsgBox('Error descargando llama-server.exe. Verifique su conexión.', mbError, MB_OK);
    Exit;
  end;
  
  ProgressBar.Position := 50;
  StatusLabel.Caption := 'Descargando modelo .gguf (~700 MB)...';
  Application.ProcessMessages();
  
  if not DownloadFile(MODEL_URL, DestModel, ProgressBar.Position) then begin
    MsgBox('Error descargando modelo. Verifique su conexión y espacio en disco.', mbError, MB_OK);
    Exit;
  end;
  
  ProgressBar.Position := 100;
  StatusLabel.Caption := 'Descargas completadas. Verificando integridad...';
  Application.ProcessMessages();
  
  { TODO: Verificar checksums SHA256 }
end;

{------------------------------------------------------------------------------}
{ CALLBACK: NextButtonClick - Controla el flujo del wizard }
{------------------------------------------------------------------------------}
function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  
  case CurPageID of
    wpSelectComponents: begin
      { Si se selecciona ai_engine, mostrar página de descarga }
      if IsComponentSelected('ai_engine') then begin
        CreateDownloadPage();
        { La descarga real se hará en CurPageChanged cuando se llegue a wpReady }
      end;
    end;
    
    wpReady: begin
      { Página final antes de instalar }
      if IsComponentSelected('ai_engine') then begin
        { Verificar VRAM si se selecciona IA }
        if VRAM_MB > 0 then begin
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
end;

{------------------------------------------------------------------------------}
{ CALLBACK: CurPageChanged - Ejecuta lógica al cambiar de página }
{------------------------------------------------------------------------------}
procedure CurPageChanged(CurPageID: Integer);
begin
  if (CurPageID = wpReady) and IsComponentSelected('ai_engine') then begin
    { Mostrar página de descarga personalizada }
    { La descarga se ejecuta aquí antes de la instalación real }
    try
      DownloadAIComponents();
    except
      Log('Error durante descarga de componentes IA');
    end;
  end;
end;

{------------------------------------------------------------------------------}
{ CALLBACK: OnDownloadProgress - Actualiza barra de progreso }
{------------------------------------------------------------------------------}
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
      if VRAM > Result then Result := VRAM div (1024*1024); { Convertir a MB }
    end;
  except
    Result := 0;
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

{------------------------------------------------------------------------------}
{ EVENTO: Antes de la instalación }
{------------------------------------------------------------------------------}
function InitializeUninstall(): Boolean;
begin
  { Detener llama-server.exe si está corriendo }
  { TODO: Terminar proceso antes de desinstalar }
  Result := True;
end;

{------------------------------------------------------------------------------}
{ SECCIÓN [CustomMessages] para internacionalización futura }
{------------------------------------------------------------------------------}
[CustomMessages]
core_only_desc=Synapse Core (Ligero - Solo Lenguaje, MinGW y VSIX)
opensyn_full_desc=OpenSyn (Completo - Lenguaje + IA Local Autónoma)
ai_engine_desc=Motor IA Local (llama-server.exe + modelo .gguf + orchestrador C)
vram_warning=Su GPU tiene %d MB de VRAM. El modelo requiere al menos 4 GB.
download_failed=Error descargando %s. Verifique su conexión.
verify_checksum=Verificando integridad del archivo...
install_completed=Instalación completada. Ejecute 'synapse' desde terminal.