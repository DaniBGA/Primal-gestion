# Build Windows - Primal Gestion

## 1) Instalar dependencias

```powershell
pip install -r requirements.txt
pip install -r requirements-build.txt
```

## 2) Generar ejecutable

```powershell
.\build_windows.ps1
```

Resultado: `dist\\Primal.exe`

## 3) Generar instalador (opcional)

Instala Inno Setup 6: https://jrsoftware.org/isdl.php

Luego ejecuta:

```powershell
.\build_installer.ps1
```

Resultado: `dist\\installer\\PrimalGestionSetup.exe`

## Firma digital (opcional pero recomendada)

Antes de ejecutar los scripts de build, define variables de entorno con tu certificado:

```powershell
$env:SIGN_PFX_PATH = "C:\ruta\tu_certificado.pfx"
$env:SIGN_PFX_PASSWORD = "tu_clave"
```

Con eso, se firma automaticamente:

- `dist\\Primal.exe`
- `dist\\installer\\PrimalGestionSetup.exe`

Si no defines esas variables, el build funciona igual pero sin firma digital.

## Autoactualizacion

Configura la URL del manifiesto en `core/app_info.py`, variable `UPDATE_METADATA_URL`.

Tambien puedes hacerlo directo por GitHub sin URL manual:

- En `core/app_info.py`, configura `GITHUB_REPO = "usuario/repositorio"`
- Opcional: `GITHUB_BRANCH` (por defecto `main`)
- La app leera automaticamente: `https://raw.githubusercontent.com/usuario/repositorio/main/update/latest.json`

Formato JSON esperado en esa URL:

```json
{
	"version": "1.0.1",
	"download_url": "https://tuservidor.com/PrimalGestionSetup.exe",
	"notes": "Mejoras de rendimiento y correcciones"
}
```

La app verifica actualizaciones al iniciar y tambien desde menu `Ayuda > Buscar actualizaciones`.

Si aceptas actualizar, la app descarga el setup nuevo y lo abre automaticamente.

## Flujo recomendado con GitHub Push

1. Genera instalador nuevo (`dist\\installer\\PrimalGestionSetup.exe`).
2. Sube ese setup como asset de una Release en GitHub.
3. Actualiza `update/latest.json` con nueva version y URL del setup.
4. Haz push de `update/latest.json` al branch configurado.
5. En los clientes, Primal detecta la nueva version y ofrece actualizar.

## Comportamiento del instalador

- Permite elegir carpeta de instalación.
- Crea acceso directo de menú inicio.
- Puede crear acceso directo de escritorio.
- Ejecuta `Primal.exe` (no `main.py`).
- El icono en escritorio y barra de tareas es el logo de Primal.
