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

Responde usando el historial configurado en `CHAT_HISTORY`.

### Ofertas

Flujo bonus que consulta promociones simuladas de EcoMarket.

## Preparación

Desde la raíz del proyecto:

```powershell
.venv\Scripts\Activate.ps1
```

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

El menú permite seleccionar:

1. Recomendar recetas.
2. Consultar estado de pedido.
3. Consultar horarios de despacho.
4. Conversar con el asistente.
5. Consultar ofertas.
6. Escribir una consulta libre.
0. Salir.

Si preguntas por el grafo, el flujo, los nodos o el diagrama, se muestra en
ASCII directamente en la terminal sin consumir una llamada al modelo:

```text
START → ROUTER
          ├── RECETA    → END
          ├── PEDIDO    → END
          ├── HORARIOS  → END
          ├── OFERTAS   → END
          └── CONVERSAR → END
```

Se pueden realizar varias consultas en una misma ejecución.

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

El notebook tiene tres celdas:

1. **Configuración:** define tools, estado, nodos y grafo.
2. **Ejemplos:** muestra las consultas disponibles y sus rutas esperadas.
3. **Ejecución:** permite elegir entre una consulta o todos los ejemplos.

Para una consulta individual, edita la tercera celda:

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
