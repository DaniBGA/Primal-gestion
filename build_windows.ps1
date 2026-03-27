$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$venvCandidates = @(
	(Join-Path $root ".venv\Scripts\python.exe"),
	(Join-Path (Split-Path -Parent $root) ".venv\Scripts\python.exe")
)
$venvPython = $venvCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($venvPython) {
	$pythonExe = $venvPython
} else {
	$pythonExe = (Get-Command python -ErrorAction Stop).Source
}

Write-Host "Usando Python: $pythonExe"

& $pythonExe -c "import reportlab"
if ($LASTEXITCODE -ne 0) {
	throw "Falta reportlab en el Python usado para build. Instala dependencias con: & '$pythonExe' -m pip install -r .\\requirements.txt"
}

Write-Host 'Generando icono .ico...'
& $pythonExe .\tools\make_icon.py

Write-Host 'Limpiando build anterior...'
if (Test-Path .\build) { Remove-Item .\build -Recurse -Force }
if (Test-Path .\dist) { Remove-Item .\dist -Recurse -Force }

Write-Host 'Compilando Primal.exe con PyInstaller...'
& $pythonExe -m PyInstaller --noconfirm --clean --windowed --onefile --name Primal --icon .\assets\icons\PrimalLogo.ico --version-file .\version.txt --add-data "assets;assets" --hidden-import=reportlab --hidden-import=reportlab.lib --hidden-import=reportlab.pdfgen .\main.py

if ($LASTEXITCODE -ne 0) {
	throw 'PyInstaller fallo. Revisa el log anterior.'
}

if ($env:SIGN_PFX_PATH -and $env:SIGN_PFX_PASSWORD) {
	Write-Host 'Firmando digitalmente Primal.exe...'
	.\tools\sign_file.ps1 -FilePath .\dist\Primal.exe -PfxPath $env:SIGN_PFX_PATH -PfxPassword $env:SIGN_PFX_PASSWORD
}

Write-Host 'Build finalizado: dist\\Primal.exe'
