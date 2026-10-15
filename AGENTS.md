# Instrucciones del proyecto

## Estructura de agentes

Cada agente debe vivir en su propio directorio bajo `src/`:

```text
src/
└── {{nombre_agente}}/
    ├── graph.py
    ├── prompts.py
    └── tools.py
```

- `graph.py`: define y compila el grafo de LangGraph.
- `prompts.py`: contiene los prompts del agente.
- `tools.py`: contiene las herramientas que puede utilizar el agente.

El punto de entrada está en la raíz del proyecto y se ejecuta así:

```bash
python main.py {{nombre_agente}}
```

## Modelo y secretos

- Se usará una API de Google Gemini mediante la variable de entorno configurada en `.env`.
- Nunca incluir claves API, tokens u otros secretos directamente en el código.
- `.env` debe mantenerse fuera del control de versiones; usar `.env.example` para documentar las variables necesarias sin valores reales.
- Cargar las variables de entorno desde `.env` al iniciar la aplicación.

## Observabilidad del grafo

`main.py` debe aceptar estos flags:

### `--saltos`

Al ejecutar:

```bash
python main.py {{nombre_agente}} --saltos
```

Mostrar los saltos realizados por el agente durante la ejecución de LangGraph, incluyendo:

- Los nodos visitados.
- Las herramientas ejecutadas.
- El orden de cada salto.

La instrumentación debe registrar los eventos sin cambiar el comportamiento normal del agente.

### `--diagrama`

Al ejecutar:

```bash
python main.py {{nombre_agente}} --diagrama
```

Imprimir únicamente el diagrama Mermaid obtenido con:

```python
graph.get_graph().draw_mermaid()
```

Este modo debe mostrar el diagrama sin ejecutar el agente, sus nodos ni sus herramientas.
