# Taller EcoMarket

Agente de atención al cliente construido con LangGraph para el ecommerce
simulado **EcoMarket**.

## Autores

- Fabio Durán
- Gustavo Reyes
- Ezequiel Muñoz

## Funcionalidades

El router clasifica cada consulta y deriva a un único flujo:

```text
START → router
          ├── receta    → END
          ├── pedido    → END
          ├── horarios  → END
          ├── ofertas   → END
          └── conversar → END
```

### Recetas

Consulta recetas simuladas y productos/precios del catálogo mediante tools.

### Pedidos

Extrae el número de pedido y consulta su estado en los datos simulados.

### Horarios

Consulta los horarios de despacho según la comuna.

### Conversación

El nodo recibe el mensaje y el valor actual de `CHAT_HISTORY`. El programa lo
inicializa como `[]` al comenzar y no agrega automáticamente los turnos del
loop, por lo que no existe memoria acumulativa entre mensajes.

### Ofertas

Flujo bonus que consulta promociones simuladas de EcoMarket.

## Preparación

Desde la raíz del proyecto, instala las dependencias con `uv`:

```bash
uv sync
```

Después activa el entorno virtual usando el script correspondiente a tu
sistema operativo. Todos los comandos siguientes deben ejecutarse desde la
raíz del proyecto.

### Activación por sistema operativo

**Windows PowerShell** (el punto inicial conserva la activación en la sesión):

```powershell
. .\scripts\activar_windows.ps1
```

**Windows CMD**:

```bat
scripts\activar_windows.bat
```

**macOS/Linux** (usa `source` para conservar la activación en la sesión):

```bash
source scripts/activar_macos_linux.sh
```

También puedes ejecutar comandos sin activar manualmente el entorno:

```bash
uv run python taller/taller.py --consulta
```

Los scripts disponibles son:

- `scripts/activar_windows.ps1`: PowerShell.
- `scripts/activar_windows.bat`: CMD.
- `scripts/activar_macos_linux.sh`: macOS y Linux.

Configura `.env`:

```env
GOOGLE_API_KEY=tu_clave_de_Gemini
GEMINI_FLASH_LITE_MODEL=gemini-flash-lite-latest
```

## Uso con `taller.py`

### Ayuda

```powershell
python taller/taller.py --ayuda
```

### Modo interactivo

```powershell
python taller/taller.py --consulta
```

El modo conversacional inicia directamente en el chat. Escribe `/opciones`
para mostrar el menú estructurado:

1. Recomendar recetas.
2. Consultar estado de pedido.
3. Consultar horarios de despacho.
4. Conversar con el asistente.
5. Consultar ofertas.
6. Escribir una consulta libre.
7. Mostrar Mermaid y generar PNG del grafo.

Escribe `/salir` para terminar la conversación.

También puedes escribir consultas directamente sin seleccionar una opción.
Si eliges `1` a `5`, el programa conserva una etiqueta para el registro de la
siguiente consulta y muestra un ejemplo, pero la intención se vuelve a
clasificar con el router. Una línea vacía no ejecuta el agente; solicita
un mensaje, `/opciones` o `/salir`. La opción `6` representa una consulta
libre, aunque el valor `6` se procesa como cualquier mensaje normal. La
opción `7` muestra el diagrama y genera el PNG sin llamar al modelo.

Además, `/exit` y `/quit` funcionan como alias de `/salir`. Si el texto de la
consulta contiene `grafo`, `diagrama`, `flujo`, `nodos` o `langgraph`, se
imprime Mermaid y no se invoca el modelo.

Cada consulta atendida muestra dos trazas antes de la respuesta:

```text
[router] ruta: ofertas
[local] ruta: ofertas
```

La primera corresponde a la clasificación estructurada y la segunda confirma
el nodo local que ejecutó el flujo. Las rutas posibles son `receta`, `pedido`,
`horarios`, `ofertas` y `conversar`. Cada ruta especializada consulta primero
sus datos simulados mediante tools y luego usa el modelo para redactar la
respuesta; `conversar` usa el prompt del asistente y `CHAT_HISTORY`.

La opción 7 imprime en pantalla el Mermaid oficial usando
`app.get_graph().draw_mermaid()` y genera el archivo
`grafo_ecomarket.png` en la raíz usando `app.get_graph().draw_mermaid_png()`.

Si preguntas por el grafo, el flujo, los nodos o el diagrama, se muestra en
la terminal el Mermaid oficial producido por:

```text
app.get_graph().draw_mermaid()
```

Se pueden realizar varias consultas en una misma ejecución; el menú solo
aparece cuando escribes `/opciones`.

### Modo automático

Ejecuta los cinco ejemplos documentados y compara la ruta obtenida con la
ruta esperada:

```powershell
python taller/taller.py --automatico
```

## Uso con `taller.ipynb`

Abre `taller/taller.ipynb` usando el kernel:

```text
Python 3.12 (.venv) clase-jueves-20261015
```

El notebook tiene cuatro celdas:

1. **Configuración:** define tools, estado, nodos y grafo.
2. **Diagrama Mermaid:** genera el gráfico oficial con `app.get_graph().draw_mermaid()`.
3. **Ejemplos:** muestra las consultas disponibles y sus rutas esperadas.
4. **Ejecución:** permite elegir entre una consulta o todos los ejemplos.

El notebook conserva la misma definición de estado, prompts, tools, router,
nodos y grafo que `taller.py`, pero su punto de entrada es distinto: no abre
el loop de terminal ni interpreta `/opciones` o `/salir`. La cuarta celda
ejecuta una consulta mediante `USER_INPUT` o ejecuta los cinco ejemplos con
`MODO = "ejemplos"`; sus resultados se registran en
`taller/ejecuciones_ipynb.log`.

Para una consulta individual, edita la cuarta celda:

```python
MODO = "consulta"
USER_INPUT = "¿Qué recetas tienen palta?"
```

Para ejecutar todos los ejemplos:

```python
MODO = "ejemplos"
```

Ejecuta las celdas en orden. Si el notebook ya estaba abierto, reinicia el
kernel antes de ejecutar todo nuevamente.

## Logs

Cada ejecución registra un bloque de texto legible con:

- Modo: `automatico` o `consulta`.
- Inicio y fin.
- Duración.
- Zona horaria `America/Santiago`.
- Consulta.
- Ruta obtenida y ruta esperada.
- Respuesta.
- Error, si ocurre.

En modo conversacional, cada mensaje que llega al agente se registra como una
consulta independiente, incluyendo su ruta y respuesta.

Los archivos son independientes:

```text
taller/ejecuciones_py.log
taller/ejecuciones_ipynb.log
```

Los logs están excluidos de Git porque pueden contener consultas de clientes.

## Entrega

La entrega contiene:

- `taller/taller.py`
- `taller/taller.ipynb`
- `plan.json`
- `.opencode/spec.md`
- `.opencode/implementador.md`

También está disponible:

```text
entrega-fabio-duran-gustavo-reyes-ezequiel-munoz.zip
```
