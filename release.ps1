param(
    [Parameter(Mandatory = $true)]
    [string]$Version,
    [Parameter(Mandatory = $true)]
    [string]$Repo,
    [string]$Notes = "Release"
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
$pythonExe = (Get-Command python -ErrorAction Stop).Source

Write-Host "Actualizando versionado a $Version..."
& $pythonExe .\tools\bump_release.py --version $Version --repo $Repo --notes $Notes

Write-Host 'Generando ejecutable...'
.\build_windows.ps1

Write-Host 'Generando instalador...'
.\build_installer.ps1

Write-Host "Release local listo para $Version"
Write-Host "Siguiente: subir dist\\installer\\PrimalGestionSetup_$Version.exe a GitHub Releases (tag: $Version)."
