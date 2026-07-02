; EDUcador - Inno Setup Script
; Compile com Inno Setup (https://jrsoftware.org/isinfo.php)

[Setup]
AppName=EDUcador - Nex-Tutor
AppVersion=1.0
AppPublisher=EDUcador Team
DefaultDirName={autopf}\EDUcador
DefaultGroupName=EDUcador
DisableProgramGroupPage=yes
OutputDir=.\Output
OutputBaseFilename=EDUcador_Setup
UninstallDisplayIcon={app}\EDUcador.exe
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
MinVersion=10.0.17763
WizardStyle=modern
UsePreviousAppDir=yes

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: ".\dist\EDUcador\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: ".\models\gemma3-4b\*"; DestDir: "{userappdata}\.ollama\models\gemma3-4b"; Flags: external recursesubdirs createallsubdirs
Source: ".\models\phi4-mini\*"; DestDir: "{userappdata}\.ollama\models\phi4-mini"; Flags: external recursesubdirs createallsubdirs
Source: ".\models\llama3.2-vision\*"; DestDir: "{userappdata}\.ollama\models\llama3.2-vision"; Flags: external recursesubdirs createallsubdirs
Source: ".\scripts\verify_ollama.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\EDUcador"; Filename: "{app}\EDUcador.exe"
Name: "{group}\{cm:UninstallProgram,EDUcador}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\EDUcador"; Filename: "{app}\EDUcador.exe"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\EDUcador"; Filename: "{app}\EDUcador.exe"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\EDUcador.exe"; Description: "{cm:LaunchProgram,EDUcador}"; Flags: nowait postinstall skipifsilent

[Registry]
Root: HKCU; Subkey: "Software\EDUcador"; Flags: createvalueifdoesntexist
Root: HKCU; Subkey: "Software\EDUcador"; ValueType: string; ValueName: "InstallDir"; ValueData: "{app}"

[Code]
function InitializeSetup(): Boolean;
var
  ErrorCode: Integer;
begin
  if not DirExists(ExpandConstant('{userappdata}\.ollama')) then
    CreateDir(ExpandConstant('{userappdata}\.ollama'));

  if not GetSpaceOnDisk(ExpandConstant('{app}'), ErrorCode) then
  begin
    MsgBox('Nao foi possivel verificar espaco em disco.', mbError, MB_OK);
    Result := True;
    Exit;
  end;

  if ErrorCode < 8589934592 then
  begin
    if MsgBox('O EDUcador requer pelo menos 8 GB de espaco livre em disco. Continuar mesmo assim?', mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False;
      Exit;
    end;
  end;

  Result := True;
end;
