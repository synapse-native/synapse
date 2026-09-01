; =========================================================================
; synapse.iss — Script Inno Setup para Synapse Ecosystem
; =========================================================================
; Manual 9 §4.1: Distribución para Windows
; Opciones: "Solo Synapse" vs "Ecosistema completo"
; =========================================================================

[Setup]
AppName=Synapse Ecosystem
AppVersion=8.1.0
AppPublisher=Synapse Labs
DefaultDirName={autopf}\Synapse
DefaultGroupName=Synapse
OutputBaseFilename=synapse-setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Languages\English.isl"

[Components]
Name: "synapse"; Description: "Synapse Core (Compilador y Runtime)"; Types: full custom; Flags: fixed
Name: "syquex"; Description: "Syquex (Lenguaje de Alto Nivel)"; Types: full
Name: "opensyn"; Description: "OpenSyn (Asistente IA Local)"; Types: full
Name: "lib"; Description: "Biblioteca Estándar"; Types: full

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Archivos base de Synapse (siempre se instalan)
Source: "..\..\build\bin\synapse.exe"; DestDir: "{app}\bin"; Flags: ignoreversion
Source: "..\..\nucleo\*"; DestDir: "{app}\nucleo"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\std\*"; DestDir: "{app}\std"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\runtime\*"; DestDir: "{app}\runtime"; Flags: ignoreversion recursesubdirs createallsubdirs

; Syquex (opcional)
Source: "..\..\syquex\*"; DestDir: "{app}\syquex"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist; Components: syquex

; OpenSyn (opcional)
Source: "..\..\opensyn\*"; DestDir: "{app}\opensyn"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist; Components: opensyn

; Biblioteca estándar (opcional)
Source: "..\..\lib\*"; DestDir: "{app}\lib"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist; Components: lib

[Icons]
Name: "{group}\Synapse"; Filename: "{app}\bin\synapse.exe"
Name: "{group}\{cm:UninstallProgram,Synapse}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Synapse"; Filename: "{app}\bin\synapse.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\bin\synapse.exe"; Description: "Iniciar Synapse"; Flags: nowait postinstall skipifsilent
