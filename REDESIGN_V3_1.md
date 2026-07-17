# Rediseño visual V3.1

Corrección de estabilidad para Windows:

- Se elimina `Qt.WA_TranslucentBackground`, que podía provocar un cierre nativo de Qt sin traceback.
- Se conserva el aspecto redondeado mediante estilos internos estables.
- Se restaura el layout raíz sin margen transparente externo.

Esta versión sigue siendo de desarrollo.
