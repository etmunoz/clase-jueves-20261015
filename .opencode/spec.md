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

Usa `CHAT_HISTORY` y el prompt del asistente para mantener el contexto.

### Ofertas (bonus)

Consulta `ofertas_semana` y redacta únicamente con las promociones simuladas.

## Restricciones

- No incluir `GOOGLE_API_KEY` ni secretos en el código.
- Usar datos simulados del archivo; no modificarlos para resolver las tareas.
- Mantener los prompts finales pegados en la sección `ENTREGA`.
- Ejecutar el archivo completo desde cero antes de entregar.
