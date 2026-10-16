# Taller EcoMarket

Equipo: Fabio Durán, Gustavo Reyes y Ezequiel Muñoz.

La implementación está en `taller.py` y también en `taller.ipynb`. La
planificación y especificación se encuentran en `../plan.json` y
`../.opencode/`.

El grafo usa el patrón:

```text
router → flujo especializado → END
```

Antes de entregar, ejecutar todo el notebook desde cero en la plataforma y
probar las consultas indicadas en `.opencode/implementador.md`.

En `taller.ipynb`, escribe la consulta en la segunda celda, en la variable
`USER_INPUT`, y ejecuta esa celda:

```python
USER_INPUT = "¿Qué recetas tienen palta?"
```

La segunda celda genera el diagrama Mermaid oficial con
`app.get_graph().draw_mermaid()`. La tercera celda imprime los cinco ejemplos
disponibles y sus rutas esperadas. En la cuarta celda puedes elegir:

```python
MODO = "consulta"   # una sola consulta
MODO = "ejemplos"   # ejecuta los cinco casos automáticamente
```

Para ejecutar el archivo Python:

```powershell
# Menú interactivo
python taller/taller.py --consulta

# Ejecuta automáticamente los cinco ejemplos
python taller/taller.py --automatico
```

El menú interactivo permite elegir recetas, pedidos, horarios, conversación,
ofertas o una consulta libre, y continuar atendiendo consultas hasta elegir
`0. Salir`.

La opción 4 mantiene un loop conversacional. Escribe varios mensajes y usa
`/volver` para regresar al menú principal.

Cada ejecución se agrega con un formato de texto legible y visual, incluyendo
modo (`automatico` o `consulta`), inicio, fin, duración, consulta, ruta,
resultado y respuesta. Si falla, también
guarda el error. Los archivos son independientes:

- `taller/ejecuciones_py.log`: ejecuciones de `taller.py`.
- `taller/ejecuciones_ipynb.log`: ejecuciones del notebook.

Ambos están excluidos de Git porque pueden contener consultas de clientes.
