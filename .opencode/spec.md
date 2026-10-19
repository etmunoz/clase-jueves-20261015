# Especificación · Taller EcoMarket

## Equipo

- Fabio Durán
- Gustavo Reyes
- Ezequiel Muñoz

## Objetivo

Construir un agente de atención para el ecommerce simulado EcoMarket. El
router clasifica cada mensaje y lo deriva a un único nodo especializado.

## Flujo de LangGraph

```text
START → router → receta   → END
              → pedido    → END
              → horarios  → END
              → ofertas   → END
              → conversar→ END
```

El estado es:

```python
class Estado(TypedDict):
    entrada: str
    ruta: str
    respuesta: str
```

`Ruta` es la salida estructurada del router y solo permite `receta`, `pedido`,
`horarios`, `ofertas` y `conversar`.

## Flujo conversacional de terminal

`python taller/taller.py --consulta` inicia directamente el chat, sin mostrar
el menú. Cada mensaje normal se envía al router y muestra las trazas:

```text
[router] ruta: <ruta clasificada>
[local] ruta: <nodo ejecutado>
```

`/opciones` muestra el menú estructurado. Las opciones `1` a `5` guardan una
etiqueta para el registro y muestran un ejemplo, pero no fuerzan la ruta: la
siguiente consulta vuelve a pasar por el router. `6` se procesa como texto
normal, `7` imprime Mermaid y genera `grafo_ecomarket.png`. Las consultas
siguientes continúan en el mismo loop y `/salir`, `/exit` o `/quit` finalizan
la sesión. Las líneas vacías no ejecutan el grafo. Las palabras `grafo`,
`diagrama`, `flujo`, `nodos` y `langgraph` muestran Mermaid sin llamar al
modelo.

## Reglas de los nodos

### Router

Clasifica la intención y no responde el contenido del cliente. Debe elegir
`receta` para cocina, `pedido` para seguimiento, `horarios` para despacho,
`ofertas` para promociones y `conversar` para el resto.

### Receta

Debe llamar a `buscar_recetas` y `productos_y_precios`, y pasar ambas salidas
al modelo junto con el pedido del cliente.

### Pedido

Extrae el primer número del mensaje con una expresión regular, consulta
`estado_pedido` y usa la información verificada para redactar.

### Horarios

Pasa el mensaje completo a `horarios_despacho`, que identifica la comuna, y
redacta usando solamente el resultado de la tool.

### Conversar

Usa el valor actual de `CHAT_HISTORY` y el prompt del asistente. El programa
lo inicializa como `[]` y no agrega automáticamente los turnos del loop, por
lo que no hay memoria acumulativa entre mensajes.

### Ofertas (bonus)

Consulta `ofertas_semana` y redacta únicamente con las promociones simuladas.

## Restricciones

- No incluir `GOOGLE_API_KEY` ni secretos en el código.
- Usar datos simulados del archivo; no modificarlos para resolver las tareas.
- Mantener los prompts finales pegados en la sección `ENTREGA`.
- Ejecutar el archivo completo desde cero antes de entregar.
