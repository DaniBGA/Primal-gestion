# Primal Gestion - Guia de estructura y funciones

Este documento explica que contiene cada carpeta del proyecto, que hace cada archivo y como se conecta todo dentro de la aplicacion.

## 1. Que es esta aplicacion

Primal Gestion es una app de escritorio para gestion de gimnasio hecha con PyQt6.

Funciones principales:
- Gestion de alumnos (socios).
- Registro y seguimiento de pagos.
- Temporizador de entrenamientos con sonidos.
- Reportes de facturacion mensual en PDF.
- Autoactualizacion desde GitHub Releases.
- Build de ejecutable e instalador para Windows.

## 2. Flujo general de la app

1. `main.py` inicia la UI y la base de datos.
2. `db/database.py` crea conexion SQLite en `%LOCALAPPDATA%/PrimalGestion/data/gym.sqlite3`.
3. Los modulos de `modules/` muestran pestanas de negocio:
   - `socios`
   - `pagos`
   - `training`
   - `facturacion`
4. `core/auto_update.py` consulta `update/latest.json` remoto y compara versiones.
5. Si hay update, descarga el setup nuevo y lo ejecuta.

## 3. Estructura de carpetas

### 3.1 Raiz del proyecto

Archivos principales:

- `main.py`
  - Punto de entrada de la aplicacion.
  - Crea ventana principal, tabs, menu Ayuda y check de actualizaciones.
  - Define el tema visual global (stylesheet).

- `requirements.txt`
  - Dependencias de runtime:
    - PyQt6
    - SQLAlchemy
    - reportlab

- `requirements-build.txt`
  - Dependencias de empaquetado/build:
    - pyinstaller
    - Pillow

- `build_windows.ps1`
  - Build del `Primal.exe` con PyInstaller.
  - Regenera icono ICO desde PNG.
  - Limpia `build/` y `dist/`.
  - Firma digitalmente el exe si hay variables de entorno de certificado.

- `build_installer.ps1`
  - Compila el instalador con Inno Setup (`ISCC.exe`).
  - Toma `dist/Primal.exe` y genera setup en `dist/installer/`.
  - Firma digitalmente el setup si hay certificado.

- `release.ps1`
  - Flujo completo de release:
    1. Actualiza version y metadata (`tools/bump_release.py`).
    2. Genera exe.
    3. Genera instalador.

- `rebuild_same_version.ps1`
  - Recompila exe + setup sin cambiar version.
  - Util para hotfixes o cambios visuales.

- `Primal.spec`
  - Configuracion de PyInstaller (entrypoint, assets, icono, version file).

- `version.txt`
  - Metadatos de version de archivo para Windows (`FileVersion`, `ProductVersion`).

- `BUILD_WINDOWS.md`
  - Guia operativa de build, firma y autoactualizacion.

- `__init__.py`
  - Marca la carpeta como paquete Python.


### 3.2 `core/`

Responsabilidad: infraestructura comun (config, rutas, update).

- `core/app_info.py`
  - Constantes de aplicacion:
    - nombre app
    - version actual
    - repo/branch de GitHub para updates
    - URL manual alternativa para metadata

- `core/paths.py`
  - Resuelve rutas segun modo desarrollo o ejecutable empaquetado.
  - Maneja rutas de datos del usuario en LocalAppData.
  - Expone helpers para:
    - recursos (`assets/...`)
    - planillas medicas
    - Desktop

- `core/auto_update.py`
  - Lector de metadata de actualizacion (JSON remoto).
  - Compara version remota vs local.
  - Descarga instalador actualizado en `%TEMP%/PrimalGestionUpdates`.
  - Define errores de update (`UpdateCheckError`, `UpdateInstallError`).

- `core/__init__.py`
  - Inicializacion del paquete.


### 3.3 `db/`

Responsabilidad: persistencia y modelo de datos.

- `db/database.py`
  - Configura engine SQLAlchemy para SQLite.
  - Crea `SessionLocal`.
  - Define `Base` declarativa.
  - `init_db()` crea tablas.

- `db/models.py`
  - Entidades de negocio:
    - `Socio`: alumno del gym.
    - `Pago`: cuota/pago de socio.
    - `Ejercicio`: entrenamiento base con duracion.
    - `SesionEntrenamiento`: ejecucion real de un ejercicio.
  - Define relaciones y cascadas.

- `db/__init__.py`
  - Inicializacion del paquete.


### 3.4 `modules/`

Responsabilidad: UI funcional por area del negocio.

#### `modules/socios/`

- `modules/socios/widget.py`
  - Pestana Socios.
  - CRUD de alumnos.
  - Busqueda por nombre o telefono.
  - Carga de planilla medica (pdf/imagen).
  - Copia planillas al almacenamiento de la app.
  - Dialogo de revision con preview de planilla.
  - Emite `socios_changed` para refrescar otros modulos.

- `modules/socios/__init__.py`
  - Inicializacion del paquete.

#### `modules/pagos/`

- `modules/pagos/widget.py`
  - Pestana Pagos.
  - Registro de pagos con fechas (pago y proximo pago).
  - Muestra ultimo pago por socio.
  - Calcula estado:
    - Al dia
    - Proximo a vencer
    - Vencido
  - Filtros por estado.
  - Tabla con anchos fijos para estabilidad visual.

- `modules/pagos/__init__.py`
  - Inicializacion del paquete.

#### `modules/training/`

- `modules/training/widget.py`
  - Pestana Training.
  - Alta y borrado de ejercicios.
  - Temporizador (iniciar, pausar, reiniciar).
  - Sonido de inicio y aviso de cuenta regresiva.
  - Guarda sesion completada en base de datos.

- `modules/training/__init__.py`
  - Inicializacion del paquete.

#### `modules/facturacion/`

- `modules/facturacion/widget.py`
  - Pestana Facturacion.
  - Resume montos por mes/anio.
  - Genera PDF detallado por alumno:
    - cuotas pagadas
    - monto total
  - Guarda reportes en Desktop.

- `modules/facturacion/__init__.py`
  - Inicializacion del paquete.


### 3.5 `assets/`

Responsabilidad: recursos visuales y multimedia.

#### `assets/icons/`

- `PrimalLogo.png`: logo base del proyecto.
- `PrimalLogo.ico`: icono Windows usado en exe/instalador.
- `spin_up.svg`: flecha de incremento para spinboxes.
- `spin_down.svg`: flecha de decremento para spinboxes.

#### `assets/sounds/`

- `Air Horn Sound Effect.mp3`: sonido al iniciar entrenamiento.
- `3 Seconds Timer #shorts #youtubeshorts #countdown.mp3`: sonido de aviso final.

#### `assets/medical_files/`

- Archivos medicos almacenados localmente para socios.
- Se generan por uso de la app.
- No son codigo fuente.


### 3.6 `installer/`

Responsabilidad: empaquetado instalable en Windows.

- `installer/PrimalGestion.iss`
  - Script de Inno Setup.
  - Define:
    - metadatos de instalador
    - accesos directos
    - arquitectura
    - iconos
  - Incluye logica de desinstalacion con opcion:
    - borrar datos de `%LOCALAPPDATA%/PrimalGestion`
    - o conservarlos para reinstalacion.


### 3.7 `tools/`

Responsabilidad: automatizacion auxiliar de build/release.

- `tools/make_icon.py`
  - Convierte `PrimalLogo.png` a `PrimalLogo.ico` con multiples tamanios.

- `tools/sign_file.ps1`
  - Firma archivos (`.exe`) usando certificado PFX + signtool.
  - Usa timestamp para validacion de firma en el tiempo.

- `tools/bump_release.py`
  - Actualiza version en archivos clave de forma automatica:
    - `core/app_info.py`
    - `version.txt`
    - `installer/PrimalGestion.iss`
    - `update/latest.json`
  - Evita inconsistencias de version entre componentes.


### 3.8 `update/`

Responsabilidad: manifiesto de actualizacion remota.

- `update/latest.json`
  - Archivo que consulta el cliente para saber si hay nueva version.
  - Campos:
    - `version`
    - `download_url`
    - `notes`


### 3.9 Carpetas generadas por build o runtime

- `data/`
  - Puede contener BD local en desarrollo (`gym.sqlite3`).
  - En instalacion final se usa LocalAppData del usuario.

- `build/`
  - Archivos temporales/intermedios de PyInstaller.
  - Se puede borrar y regenerar.

- `dist/`
  - Artefactos finales:
    - `Primal.exe`
    - instalador en `dist/installer/...`

- `__pycache__/` y subcarpetas `__pycache__/`
  - Bytecode de Python (`.pyc`).
  - Generado automaticamente por ejecucion.


## 4. Como se conectan los modulos entre si

- `main.py` crea todas las pestanas y las agrega al `QTabWidget`.
- Cuando cambia algo en socios, `socios_changed` refresca datos de pagos.
- `db/models.py` define estructura comun para todos los modulos.
- `core/paths.py` unifica donde se guardan archivos y recursos.
- `core/auto_update.py` se invoca desde menu Ayuda y al inicio silencioso.


## 5. Flujo de release recomendado

1. Ejecutar `release.ps1 -Version X.Y.Z -Repo usuario/repo -Notes "..."`.
2. Subir instalador generado en `dist/installer/` a GitHub Releases.
3. Confirmar que `update/latest.json` en el repo remoto apunta al asset correcto.
4. En clientes, la app detecta update y ofrece instalacion.


## 6. Nota sobre carpetas que no son fuente

No deberias editar manualmente como parte del codigo de negocio:
- `build/`
- `dist/`
- `__pycache__/`
- contenido generado dentro de `assets/medical_files/`

Estas carpetas son salida de compilacion, cache o datos de uso.
