$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
$pythonExe = (Get-Command python -ErrorAction Stop).Source

Write-Host 'Generando icono .ico...'
& $pythonExe .\tools\make_icon.py

Write-Host 'Limpiando build anterior...'
if (Test-Path .\build) { Remove-Item .\build -Recurse -Force }
if (Test-Path .\dist) { Remove-Item .\dist -Recurse -Force }

Write-Host 'Compilando Primal.exe con PyInstaller...'
& $pythonExe -m PyInstaller --noconfirm --clean --windowed --onefile --name Primal --icon .\assets\icons\PrimalLogo.ico --version-file .\version.txt --add-data "assets;assets" .\main.py

if ($LASTEXITCODE -ne 0) {
	throw 'PyInstaller fallo. Revisa el log anterior.'
}

if ($env:SIGN_PFX_PATH -and $env:SIGN_PFX_PASSWORD) {
	Write-Host 'Firmando digitalmente Primal.exe...'
	.\tools\sign_file.ps1 -FilePath .\dist\Primal.exe -PfxPath $env:SIGN_PFX_PATH -PfxPassword $env:SIGN_PFX_PASSWORD
}

Write-Host 'Build finalizado: dist\\Primal.exe'
