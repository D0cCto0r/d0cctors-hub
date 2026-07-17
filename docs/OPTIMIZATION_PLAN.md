# Plan de optimización

## Primera etapa: medición y arranque

- Mostrar la ventana antes de finalizar las consultas remotas.
- Medir tiempos de inicio por sección.
- Añadir timeouts y fallback local a las solicitudes HTTP.
- Evitar descargar recursos ya almacenados.

## Segunda etapa: estructura

- Separar la interfaz, servicios remotos, Minecraft, Steam y actualización.
- Centralizar URLs y constantes.
- Añadir logging controlado.
- Evitar recrear páginas al navegar.

## Tercera etapa: distribución

- Comparar PyInstaller `onefile` y `onedir`.
- Automatizar la compilación con GitHub Actions.
- Publicar ejecutables mediante GitHub Releases.
