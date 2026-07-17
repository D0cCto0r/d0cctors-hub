# Migración desde d0cctor-modpack

Antes de archivar o eliminar `D0cCto0r/d0cctor-modpack`:

1. Crear el repositorio `D0cCto0r/d0cctors-hub`.
2. Subir el contenido de este paquete.
3. Copiar `servers.dat` del repositorio anterior a `remote/servers.dat`.
4. Migrar el ZIP `ShibuyaSMPModpack.zip` a una Release con tag `ShibuyaSMP-Modpack-1.0`.
5. Migrar `launcher.exe` a una Release con tag `v0.3-2026.3`.
6. Comprobar las URLs raw de `remote/servers.json`, `remote/news.json` y `remote/version.txt`.
7. Probar instalación, noticias, inicio de Minecraft, Steam y autoactualización.
8. Archivar primero el repositorio anterior. Borrarlo solamente después de comprobar todo.
