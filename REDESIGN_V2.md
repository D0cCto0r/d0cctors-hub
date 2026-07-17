# Rediseño visual V2 — Corrección de layout

Esta revisión corrige los problemas encontrados al abrir Inicio por primera vez:

- Inicio ahora usa desplazamiento vertical y ya no comprime sus bloques.
- La primera página se activa después de que Qt termina de montar la ventana.
- Se fuerza un recálculo seguro del layout al volver a Inicio.
- Las tarjetas de servidores usan selectores exclusivos; los textos ya no heredan bordes.
- El hero tiene altura controlada y título adaptable.
- La noticia destacada ocupa el ancho disponible sin forzar un mínimo antiguo.
- El footer tiene altura fija y no invade el contenido.
- La animación de cambio de página es más suave y no se usa durante el primer render.

## Probar

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe launcher_qt.py
```

No publicar una Release hasta validar visualmente esta revisión.
