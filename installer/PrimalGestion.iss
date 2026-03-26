; Inno Setup script para Primal Gestion

#define MyAppVersion "1.0.7"

[Setup]
AppId={{A5D4F8AF-3CA5-49EE-A2C2-8A1A0F6E2D91}
AppName=Primal Gestion
AppVersion={#MyAppVersion}
AppPublisher=Primal
DefaultDirName={autopf}\Primal Gestion
DefaultGroupName=Primal Gestion
DisableProgramGroupPage=yes
OutputDir=..\dist\installer
OutputBaseFilename=PrimalGestionSetup_{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\icons\PrimalLogo.ico
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked

[Files]
Source: "..\dist\Primal.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Primal Gestion"; Filename: "{app}\Primal.exe"; IconFilename: "{app}\Primal.exe"
Name: "{autodesktop}\Primal Gestion"; Filename: "{app}\Primal.exe"; Tasks: desktopicon; IconFilename: "{app}\Primal.exe"

[Run]
Filename: "{app}\Primal.exe"; Description: "Abrir Primal Gestion"; Flags: nowait postinstall skipifsilent

[Code]
var
	RemoveUserData: Boolean;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
	DataDir: string;
begin
	if CurUninstallStep = usUninstall then
	begin
		RemoveUserData := (MsgBox(
			'Deseas eliminar tambien todos los datos guardados (base de datos y planillas medicas)?' + #13#10 + #13#10 +
			'Si eliges No, los datos quedaran guardados para una futura reinstalacion.',
			mbConfirmation,
			MB_YESNO
		) = IDYES);
	end;

	if CurUninstallStep = usPostUninstall then
	begin
		if RemoveUserData then
		begin
			DataDir := ExpandConstant('{localappdata}\PrimalGestion');
			if DirExists(DataDir) then
				DelTree(DataDir, True, True, True);
		end;
	end;
end;
