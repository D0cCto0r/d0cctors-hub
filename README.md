# D0cCtor's Hub

Launcher de escritorio para la comunidad D0cCtor, desarrollado con Python y PySide6.

## Funciones actuales

- Lista remota de servidores y noticias.
- Instalación y actualización de modpacks.
- Integración con Minecraft Launcher, Forge, Fabric y Steam.
- Configuración de RAM y rutas.
- Autoactualización mediante GitHub Releases.

## Ejecutar en desarrollo

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python launcher_qt.py
```

## Compilar

```powershell
.\scripts\build.ps1
```

El ejecutable se genera en `dist/launcher.exe`.

## Archivos remotos

La carpeta `remote/` contiene los archivos consumidos por el launcher:

- `servers.json`
- `news.json`
- `version.txt`
- `servers.dat` (debe migrarse antes de eliminar el repositorio anterior)
- `assets/`

## Importante

No se debe subir `config.json`, ya que es una configuración local de cada usuario. Se incluye `config.example.json` como referencia.
