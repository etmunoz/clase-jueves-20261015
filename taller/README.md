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

La segunda celda imprime los cinco ejemplos disponibles y sus rutas esperadas.
En la tercera celda puedes elegir:

```python
MODO = "consulta"   # una sola consulta
MODO = "ejemplos"   # ejecuta los cinco casos automáticamente
```
