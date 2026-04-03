param(
    [Parameter(Mandatory = $true)]
    [string]$Version,
    [Parameter(Mandatory = $true)]
    [string]$Repo,
    [string]$Notes = "Release",
    [string]$TagPrefix = "v",
    [switch]$SkipBuild,
    [switch]$CreateGitTag
)

$ErrorActionPreference = 'Stop'

function Get-PythonForRelease([string]$RootPath) {
    $candidates = @(
        (Join-Path $RootPath ".venv\Scripts\python.exe"),
        (Join-Path (Split-Path -Parent $RootPath) ".venv\Scripts\python.exe")
    )

    $venvPython = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($venvPython) {
        return $venvPython
    }

    return (Get-Command python -ErrorAction Stop).Source
}

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    throw "Version invalida: '$Version'. Usa formato semantico, por ejemplo 1.0.10"
}

$pythonExe = Get-PythonForRelease -RootPath $root
Write-Host "Usando Python: $pythonExe"
Write-Host "Actualizando versionado a $Version..."

& $pythonExe .\tools\bump_release.py --version $Version --repo $Repo --notes $Notes
if ($LASTEXITCODE -ne 0) {
    throw "Fallo tools/bump_release.py"
}

# Normaliza latest.json para evitar 404 por diferencia de tag (ej: v1.0.10 vs 1.0.10)
$latestPath = Join-Path $root "update\latest.json"
if (!(Test-Path $latestPath)) {
    throw "No se encontro $latestPath"
}

$latest = Get-Content -Raw $latestPath | ConvertFrom-Json
$tag = "$TagPrefix$Version"
$latest.version = $Version
$latest.download_url = "https://github.com/$Repo/releases/download/$tag/PrimalGestionSetup_$Version.exe"
$latest.notes = $Notes

$json = $latest | ConvertTo-Json -Depth 8
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($latestPath, ($json + "`n"), $utf8NoBom)

if (-not $SkipBuild) {
    Write-Host "Generando ejecutable..."
    .\build_windows.ps1
    if ($LASTEXITCODE -ne 0) {
        throw "Fallo build_windows.ps1"
    }

    Write-Host "Generando instalador..."
    .\build_installer.ps1
    if ($LASTEXITCODE -ne 0) {
        throw "Fallo build_installer.ps1"
    }
}

$setupPath = Join-Path $root "dist\installer\PrimalGestionSetup_$Version.exe"
if (Test-Path $setupPath) {
    Write-Host "Instalador generado: $setupPath"
} else {
    Write-Warning "No se encontro el instalador esperado: $setupPath"
}

if ($CreateGitTag) {
    $gitTag = "$TagPrefix$Version"
    $existingTag = git tag -l $gitTag
    if (-not $existingTag) {
        git tag $gitTag
        git push origin $gitTag
        Write-Host "Tag publicado: $gitTag"
    } else {
        Write-Host "El tag ya existe: $gitTag"
    }
}

Write-Host "Release local lista para $Version"
Write-Host "Siguiente paso: subir dist\\installer\\PrimalGestionSetup_$Version.exe a GitHub Releases (tag: $TagPrefix$Version)."
