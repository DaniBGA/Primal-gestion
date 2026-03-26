$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host 'Rebuild de la version actual (sin cambiar version)...'
Write-Host '1) Generando ejecutable...'
.\build_windows.ps1

Write-Host '2) Generando instalador...'
.\build_installer.ps1

Write-Host 'Listo: se recompilo la version actual sin modificar APP_VERSION/AppVersion/latest.json.'
