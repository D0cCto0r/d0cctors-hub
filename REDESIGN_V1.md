# Rediseño visual V1

Esta versión conserva la lógica existente del launcher y aplica una primera capa visual tipo dashboard:

- Ventana adaptable de 1400x850.
- Sidebar más ancha y moderna.
- Navegación con estado activo.
- Hero principal con llamadas a acción.
- Tarjetas compactas de servidores.
- Sección de noticias destacadas.
- Paleta azul/violeta oscura.

## Estado

Es una primera iteración visual para pruebas. Todavía no es la versión final del instalador.

## Probar

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe launcher_qt.py
```

## Compilar

```powershell
.\.venv\Scripts\python.exe -m pip install pyinstaller
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
.\.venv\Scripts\python.exe -m PyInstaller --onefile --windowed --name updater updater.py
```
