param(
    [Parameter(Mandatory = $true)]
    [string]$FilePath,
    [Parameter(Mandatory = $true)]
    [string]$PfxPath,
    [Parameter(Mandatory = $true)]
    [string]$PfxPassword,
    [string]$TimestampUrl = "http://timestamp.digicert.com"
)

$ErrorActionPreference = 'Stop'

if (!(Test-Path $FilePath)) {
    throw "No se encontro archivo para firmar: $FilePath"
}
if (!(Test-Path $PfxPath)) {
    throw "No se encontro certificado PFX: $PfxPath"
}

$signTool = Get-ChildItem "C:\Program Files (x86)\Windows Kits\10\bin","C:\Program Files\Windows Kits\10\bin" -Filter signtool.exe -Recurse -ErrorAction SilentlyContinue |
    Sort-Object FullName -Descending |
    Select-Object -First 1 -ExpandProperty FullName

if (-not $signTool) {
    throw "No se encontro signtool.exe. Instala Windows SDK / Signing Tools."
}

& $signTool sign /fd SHA256 /f $PfxPath /p $PfxPassword /tr $TimestampUrl /td SHA256 $FilePath
if ($LASTEXITCODE -ne 0) {
    throw "Fallo la firma digital de $FilePath"
}

Write-Host "Archivo firmado correctamente: $FilePath"
