$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$candidates = @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
)

$inno = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $inno) {
    throw "No se encontro Inno Setup. Instala Inno Setup 6 y vuelve a ejecutar este script."
}

if (!(Test-Path .\dist\Primal.exe)) {
    throw "No se encontro dist\\Primal.exe. Ejecuta primero .\\build_windows.ps1"
}

& $inno .\installer\PrimalGestion.iss
if ($LASTEXITCODE -ne 0) {
    throw 'Fallo la compilacion del instalador. Revisa el log de Inno Setup.'
}

if ($env:SIGN_PFX_PATH -and $env:SIGN_PFX_PASSWORD) {
    Write-Host 'Firmando digitalmente PrimalGestionSetup.exe...'
    .\tools\sign_file.ps1 -FilePath .\dist\installer\PrimalGestionSetup.exe -PfxPath $env:SIGN_PFX_PATH -PfxPassword $env:SIGN_PFX_PASSWORD
}

Write-Host 'Instalador generado en dist\\installer\\PrimalGestionSetup.exe'
