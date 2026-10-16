"""Archivo: taller.py
Descripción: agente LangGraph de atención para el ecommerce simulado EcoMarket.
Autores: Fabio Durán, Gustavo Reyes y Ezequiel Muñoz
Fecha de creación: 2026-10-15 21:08
Última modificación: 2026-10-15 22:19

TALLER · Generador de Recetas para el ecommerce "EcoMarket".

Tu agente atiende clientes del supermercado por chat. Debe saber:
  1. Recomendar RECETAS con productos de la tienda (tools simuladas)
  2. Informar el ESTADO de un PEDIDO
  3. Responder HORARIOS de despacho
  4. CONVERSAR 
  5. BONUS: un flujo nuevo inventado por ti

COMO TRABAJAR (detalle completo en la pestana Docs):
  A. Descarga El notebook o copiar el codigo de aca y pegarlo en un archivo.py dentro de visual studio.
  B. Corre Celda por celda del notebook.
  C. Completa TODO 1, 2 y 3 imitando el nodo `conversar`. Cada uno trae PISTA.
  D. Prueba cada flujo con la pestana Preguntas y mira el diagrama.
  E. Entrega: un .zip con el notebook (nombres de integrantes, prompts pegados en la celda
     ENTREGA y TODO el codigo corriendo), mas plan.json y la carpeta .opencode/.

FLUJO IMPLEMENTADO
===================
START
  ↓
router (clasifica con salida estructurada Ruta)
  ├── receta    → buscar_recetas + productos_y_precios → respuesta → END
  ├── pedido    → extraer número + estado_pedido → respuesta → END
  ├── horarios  → horarios_despacho → respuesta → END
  ├── ofertas   → ofertas_semana → respuesta → END  [BONUS]
  └── conversar → historial + LLM → respuesta → END

El router nunca responde el contenido por sí mismo: solo decide la ruta.
Cada nodo especializado usa la información verificada por sus tools antes de
redactar la respuesta. La ejecución automática puede procesar una consulta o
los cinco ejemplos y registra cada resultado en taller/ejecuciones.log.
"""
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import TypedDict, Literal
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END

# PASO 0 · SALIDA: evita errores de caracteres Unicode en Windows.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()


def asegurar_logs():
    """Crea los dos archivos de log si todavía no existen."""
    carpeta_logs = Path("taller")
    carpeta_logs.mkdir(parents=True, exist_ok=True)
    for nombre in ("ejecuciones_py.log", "ejecuciones_ipynb.log"):
        (carpeta_logs / nombre).touch(exist_ok=True)


asegurar_logs()


def mostrar_ayuda():
    """Explica cómo ejecutar y evaluar el taller desde el archivo Python."""
    print(
        """
TALLER ECOMARKET · GUÍA DE USO
==============================

El programa atiende cinco flujos mediante LangGraph:
  1. Recetas       → tools de recetas y precios.
  2. Pedido        → consulta el estado de un pedido.
  3. Horarios      → consulta horarios de despacho.
  4. Conversación  → responde usando el asistente.
  5. Ofertas       → bonus con promociones simuladas.
  Si preguntas por el grafo, diagrama, flujo o nodos, se muestra el Mermaid
  oficial generado por app.get_graph().draw_mermaid(), sin llamar al modelo.

FORMAS DE EJECUCIÓN
--------------------

1) Modo interactivo:
   python taller/taller.py --consulta
   Abre un menú con opciones del 1 al 7 y permite varias consultas.
   En la opción 4, escribe /volver para regresar al menú.
   La opción 7 genera grafo_ecomarket.png en la raíz del proyecto.
   Elige 0 para salir.

2) Modo automático: ejecuta los cinco ejemplos:
   python taller/taller.py --automatico

3) Ayuda:
   python taller/taller.py --ayuda

NOTEBOOK
--------
Abre taller/taller.ipynb con el kernel Python 3.12 (.venv).
Ejecuta la primera celda, revisa los ejemplos en la segunda y selecciona
MODO/USER_INPUT en la tercera.

LOGS
----
Las ejecuciones del .py se guardan en taller/ejecuciones_py.log.
Las ejecuciones del notebook se guardan en taller/ejecuciones_ipynb.log.
Cada bloque registra modo, inicio, fin, duración, ruta y respuesta.
"""
    )


if "--ayuda" in sys.argv or "-ayuda" in sys.argv:
    mostrar_ayuda()
    raise SystemExit(0)

if "--consulta" in sys.argv and "--automatico" in sys.argv:
    print("Usa solo uno de los modos: --consulta o --automatico.")
    raise SystemExit(2)

ZONA_HORARIA = ZoneInfo("America/Santiago")

# Ejecutor local: el proyecto usa directamente el entorno virtual.
def texto(respuesta):
    """Convierte una respuesta de LangChain en texto imprimible."""
    contenido = getattr(respuesta, "content", respuesta)
    if isinstance(contenido, str):
        return contenido
    if isinstance(contenido, list):
        return "".join(
            str(bloque.get("text", ""))
            if isinstance(bloque, dict)
            else str(bloque)
            for bloque in contenido
        )
    return str(contenido)


def trazar(app, inicial, responder_desde="respuesta"):
    """Ejecuta el grafo localmente y muestra su respuesta final."""
    final = app.invoke(inicial)
    print(f"[local] ruta: {final.get('ruta', '')}")
    print(final.get(responder_desde, ""))
    return final

# PASO 1 · CONFIGURACIÓN: la key viene de .env — NUNCA del código.
if not os.environ.get("GOOGLE_API_KEY"):
    print(" Falta **GOOGLE_API_KEY**. Agrégala en el panel *API keys* y vuelve a ejecutar.")
    raise SystemExit(0)

llm = ChatGoogleGenerativeAI(model=os.environ.get("GEMINI_FLASH_LITE_MODEL", "gemini-flash-lite-latest"))

# PASO 2 · ENTREGA: integrantes y prompts finales.
# ═══════════════════════ ENTREGA · OBLIGATORIO PARA LA EVALUACIÓN ═══════════════════════
# EQUIPO: Fabio Durán · Gustavo Reyes · Ezequiel Muñoz
# 1. Escribe los nombres REALES de los integrantes del equipo.
# 2. Pega aquí tus prompts finales. En el notebook NO existen variables externas de Prompts:
#    si los dejas vacíos, el agente no rutea ni cocina y la evaluación falla.
# 3. Antes de enviar: Kernel → Restart & Run All. TODO el notebook debe correr sin errores.
# 4. Se entrega UN .zip (apellido_nombre.zip) con: este notebook, plan.json y la carpeta .opencode/ (spec.md e implementador.md).
INTEGRANTES = ["Fabio Durán", "Gustavo Reyes", "Ezequiel Muñoz"]

PROMPT_ROUTER_ENTREGA = """
Eres el router de EcoMarket. Clasifica cada mensaje en exactamente una ruta:
"receta" si pide recomendar una receta o productos para cocinar; "pedido" si
pregunta por el estado de un pedido; "horarios" si pregunta por despacho,
comuna u horarios de entrega; "ofertas" si pregunta por promociones o
descuentos; y "conversar" para saludos, preguntas generales o cualquier caso
que no corresponda a las rutas anteriores. No respondas al cliente: devuelve
solo la intención que corresponde.
""".strip()
PROMPT_CHEF_ENTREGA = """
Eres el chef virtual de EcoMarket. Recomienda una receta de la tienda usando
las opciones y precios entregados por las herramientas. Responde en español,
indica ingredientes disponibles, tiempo, precios relevantes y enlace cuando
exista. No inventes recetas, productos ni precios fuera de los datos recibidos.
""".strip()
PROMPT_ASISTENTE_ENTREGA = """
Eres el asistente de atención de EcoMarket. Conversa con cordialidad y
responde de forma clara usando el historial y el mensaje del cliente. Si la
consulta requiere buscar recetas, pedidos, horarios u ofertas, no inventes la
información: el router debe enviarla al flujo correspondiente.
""".strip()

# En el sistema de evaluación pueden configurarse prompts externos; en el notebook,
# se usan los prompts pegados arriba.
PROMPT_ROUTER = os.environ.get("PROMPT_ROUTER") or PROMPT_ROUTER_ENTREGA        # Router
PROMPT_CHEF = os.environ.get("PROMPT_CHEF") or PROMPT_CHEF_ENTREGA              # Recetas
PROMPT_ASISTENTE = os.environ.get("PROMPT_ASISTENTE") or PROMPT_ASISTENTE_ENTREGA  # Conversacion

_faltan = [n for n, v in (("INTEGRANTES", INTEGRANTES == ["Nombre Apellido 1", "Nombre Apellido 2"]),
                          ("PROMPT_ROUTER", "PEGA AQUÍ" in PROMPT_ROUTER), ("PROMPT_CHEF", "PEGA AQUÍ" in PROMPT_CHEF),
                          ("PROMPT_ASISTENTE", "PEGA AQUÍ" in PROMPT_ASISTENTE)) if v]
if _faltan:
    print("⚠️  ENTREGA INCOMPLETA: falta completar " + ", ".join(_faltan) + ". Sin esto el taller NO se evalúa.")
else:
    print("✅ Entrega: " + ", ".join(INTEGRANTES) + " · prompts cargados")

## 
os.environ["CHAT_HISTORY"] = "[]"


# PASO 3 · DATOS: catálogo, pedidos, horarios y ofertas simulados.
# ═══════════════ DATOS SIMULADOS DE ECOMARKET (no los edites) ══════════════
RECETAS = [
    {"nombre": "Pasta al pesto con palta", "url": "https://recetas.ecomarket.cl/pasta-pesto-palta",
     "ingredientes": ["pasta", "palta", "albahaca", "queso"], "minutos": 20},
    {"nombre": "Tacos veganos de quinoa", "url": "https://recetas.ecomarket.cl/tacos-quinoa",
     "ingredientes": ["quinoa", "tortillas", "palta", "tomate"], "minutos": 25},
    {"nombre": "Pan con palta de campeonato", "url": "https://recetas.ecomarket.cl/pan-palta",
     "ingredientes": ["pan", "palta", "limon", "sal de mar"], "minutos": 5},
    {"nombre": "Salmon al horno con quinoa", "url": "https://recetas.ecomarket.cl/salmon-quinoa",
     "ingredientes": ["salmon", "quinoa", "limon", "eneldo"], "minutos": 35},
    {"nombre": "Ensalada de tomate y albahaca", "url": "https://recetas.ecomarket.cl/ensalada-caprese",
     "ingredientes": ["tomate", "albahaca", "queso", "aceite de oliva"], "minutos": 10},
]
CATALOGO = {"pasta": 1490, "palta": 3990, "albahaca": 990, "queso": 4590, "quinoa": 3290,
            "tortillas": 2190, "tomate": 1890, "pan": 1990, "limon": 1290, "sal de mar": 890,
            "salmon": 8990, "eneldo": 790, "aceite de oliva": 5990}
PEDIDOS = {
    "1042": {"estado": "en reparto", "detalle": "sale hoy entre 16:00 y 18:00", "items": 8},
    "1043": {"estado": "preparando", "detalle": "en bodega, despacho manana", "items": 3},
    "2001": {"estado": "entregado", "detalle": "recibido ayer 19:24 por J. Perez", "items": 12},
}
HORARIOS = {
    "providencia": "lun-sab 10:00-20:00, mismo dia si compras antes de las 14:00",
    "nunoa": "lun-sab 10:00-20:00, mismo dia si compras antes de las 14:00",
    "maipu": "lun-vie 12:00-21:00, despacho al dia siguiente",
    "las condes": "todos los dias 9:00-22:00, express en 90 minutos",
}
OFERTAS = [
    {"nombre": "Pack pasta + salsa de tomate", "descuento": "20%", "vigencia": "esta semana"},
    {"nombre": "2 kg de quinoa", "descuento": "$5.490", "vigencia": "hasta agotar stock"},
    {"nombre": "Envío gratis sobre $25.000", "descuento": "costo de despacho $0", "vigencia": "lunes a viernes"},
]

# PASO 4 · TOOLS: funciones que consultan los datos simulados.
# ═══════════════ TOOLS (ya listas: solo tienes que USARLAS) ════════════════
@tool
def buscar_recetas(ingrediente: str) -> str:
    """Busca recetas que usen un ingrediente. Devuelve nombre, link, ingredientes y tiempo."""
    ing = ingrediente.lower()
    encontradas = [r for r in RECETAS if any(ing in i or i in ing for i in r["ingredientes"])]
    if not encontradas:
        encontradas = RECETAS[:2]  # sugerencias por defecto
    return "\n".join(f"- {r['nombre']} ({r['minutos']} min) | {r['url']} | usa: {', '.join(r['ingredientes'])}"
                     for r in encontradas)

@tool
def productos_y_precios() -> str:
    """Catalogo de la tienda con precios en CLP."""
    return "\n".join(f"- {p}: ${v:,}".replace(",", ".") for p, v in CATALOGO.items())

@tool
def estado_pedido(numero: str) -> str:
    """Estado de un pedido por su numero (ej: 1042)."""
    p = PEDIDOS.get(str(numero).strip())
    if not p:
        return f"No existe el pedido {numero}. Pide al cliente verificar el numero."
    return f"Pedido {numero}: {p['estado']} ({p['detalle']}). {p['items']} productos."

@tool
def horarios_despacho(comuna: str) -> str:
    """Horarios de despacho para una comuna."""
    c = comuna.lower()
    for nombre, horario in HORARIOS.items():
        if nombre in c or c in nombre:
            return f"Despacho en {nombre.title()}: {horario}"
    return "Comunas con despacho: " + ", ".join(n.title() for n in HORARIOS) + ". Pregunta por una de ellas."

@tool
def ofertas_semana() -> str:
    """Promociones simuladas vigentes de EcoMarket."""
    return "\n".join(
        f"- {oferta['nombre']}: {oferta['descuento']} ({oferta['vigencia']})"
        for oferta in OFERTAS
    )

# PASO 5 · ESTADO Y ROUTER: clasificación estructurada de la intención.
# ═══════════════ ESTADO Y ROUTER (ya listos) ═══════════════════════════════
class Estado(TypedDict):
    entrada: str
    ruta: str
    respuesta: str

class Ruta(BaseModel):
    destino: Literal["receta", "pedido", "horarios", "ofertas", "conversar"] = Field(
        description="Flujo que atiende el mensaje del cliente.")

def router(estado: Estado):
    """El supervisor: clasifica la intencion y delega (Demo 9)."""
    d = llm.with_structured_output(Ruta).invoke(
        f"{PROMPT_ROUTER}\n\nMensaje del cliente: {estado['entrada']}").destino
    print(f"[router] ruta: {d}")
    return {"ruta": d}

# PASO 6 · NODOS: cada nodo atiende una responsabilidad.
# ═══════════════ NODO MODELO (LISTO) — imita este patron ═══════════════════
def conversar(estado: Estado):
    """FLUJO CONVERSACIONAL: responde con memoria del chat.

    El entorno de ejecución inyecta el historial en CHAT_HISTORY: pasárselo al LLM
    es lo que convierte respuestas sueltas en una CONVERSACION."""
    historial = os.environ.get("CHAT_HISTORY", "[]")
    r = llm.invoke(f"{PROMPT_ASISTENTE}\n\nHistorial de la conversacion: {historial}\n"
                   f"Cliente: {estado['entrada']}")
    return {"respuesta": texto(r)} # Ejemplo del TODO 4

# PASO 7 · FLUJO DE RECETAS: tools + modelo.
# ═══════════════ TODO 1 · FLUJO DE RECETAS ═════════════════════════════════
def receta(estado: Estado):
    """Recomienda una receta con productos y precios de la tienda.

    PISTA — son 3 pasos (las tools se llaman con .invoke):
      opciones = buscar_recetas.invoke({"ingrediente": estado["entrada"]})
      precios = productos_y_precios.invoke({})
      ...arma un prompt con PROMPT_CHEF + opciones + precios + el pedido
         del cliente, invoca el llm y devuelve {"respuesta": texto(...)}
    """
    opciones = buscar_recetas.invoke({"ingrediente": estado["entrada"]})
    precios = productos_y_precios.invoke({})
    prompt = (
        f"{PROMPT_CHEF}\n\nPedido del cliente: {estado['entrada']}\n\n"
        f"Opciones de recetas:\n{opciones}\n\nPrecios del catálogo:\n{precios}"
    )
    return {"respuesta": texto(llm.invoke(prompt))}

# PASO 8 · FLUJO DE PEDIDOS: extraer número + tool + respuesta.
# ═══════════════ TODO 2 · FLUJO ESTADO DE PEDIDOS ══════════════════════════
def pedido(estado: Estado):
    """Informa el estado de un pedido.

    PISTA — extrae el numero y usa la tool:
      encontrado = re.search(r"\\d+", estado["entrada"])
      numero = encontrado.group() if encontrado else ""
      info = estado_pedido.invoke({"numero": numero})
      ...pasale `info` al llm para redactar la respuesta al cliente
         (o devuelve `info` directo, y compara cual queda mejor).
    """
    encontrado = re.search(r"\d+", estado["entrada"])
    numero = encontrado.group() if encontrado else ""
    info = estado_pedido.invoke({"numero": numero})
    prompt = (
        f"{PROMPT_ASISTENTE}\n\nRedacta una respuesta breve sobre el estado del pedido.\n"
        f"Mensaje del cliente: {estado['entrada']}\nInformación verificada: {info}"
    )
    return {"respuesta": texto(llm.invoke(prompt))}

# PASO 9 · FLUJO DE HORARIOS: tool + respuesta.
# ═══════════════ TODO 3 · FLUJO DE HORARIOS ════════════════════════════════
def horarios(estado: Estado):
    """Responde horarios de despacho de la comuna que mencione el cliente.

    PISTA — la tool acepta el mensaje completo (ella busca la comuna):
      info = horarios_despacho.invoke({"comuna": estado["entrada"]})
    """
    info = horarios_despacho.invoke({"comuna": estado["entrada"]})
    prompt = (
        f"{PROMPT_ASISTENTE}\n\nResponde únicamente la consulta de horarios.\n"
        f"Mensaje del cliente: {estado['entrada']}\nInformación verificada: {info}"
    )
    return {"respuesta": texto(llm.invoke(prompt))}


def ofertas(estado: Estado):
    """BONUS: informa promociones simuladas verificadas por una tool."""
    info = ofertas_semana.invoke({})
    prompt = (
        f"{PROMPT_ASISTENTE}\n\nInforma las ofertas de forma clara y breve.\n"
        f"Mensaje del cliente: {estado['entrada']}\nOfertas verificadas:\n{info}"
    )
    return {"respuesta": texto(llm.invoke(prompt))}

# %%
# PASO 10 · GRAFO: router → un nodo especializado → END.
# ═══════════════ EL GRAFO (ya cableado) ════════════════════════════════════
FLUJO_GRAFO = """Flujo del grafo:

    START -> router -> receta    -> END
                   -> pedido    -> END
                   -> horarios  -> END
                   -> ofertas   -> END
                   -> conversar -> END

La arista condicional usa el valor estructurado ``ruta`` para activar una y
solo una rama por consulta.
"""
grafo = StateGraph(Estado)
grafo.add_node("router", router)
grafo.add_node("receta", receta)
grafo.add_node("pedido", pedido)
grafo.add_node("horarios", horarios)
grafo.add_node("ofertas", ofertas)
grafo.add_node("conversar", conversar)

grafo.add_edge(START, "router")
grafo.add_conditional_edges("router", lambda e: e["ruta"],
                            {"receta": "receta", "pedido": "pedido",
                             "horarios": "horarios", "ofertas": "ofertas",
                             "conversar": "conversar"})
for nodo_final in ("receta", "pedido", "horarios", "ofertas", "conversar"):
    grafo.add_edge(nodo_final, END)

app = grafo.compile()


def ejecutar_consulta(
    consulta: str,
    origen="py",
    modo="consulta",
    nombre="consulta",
    ruta_esperada=None,
):
    """Ejecuta una consulta, muestra la respuesta y registra el resultado."""
    if solicita_grafo(consulta):
        return ejecutar_grafo_texto(consulta, origen, modo)
    return ejecutar_y_registrar(
        consulta,
        nombre=nombre,
        ruta_esperada=ruta_esperada,
        origen=origen,
        modo=modo,
    )


def solicita_grafo(consulta: str) -> bool:
    """Detecta si el usuario pide ver el grafo o el flujo del agente."""
    palabras = ("grafo", "diagrama", "flujo", "nodos", "langgraph")
    return any(palabra in consulta.lower() for palabra in palabras)


def grafo_en_texto() -> str:
    """Devuelve el diagrama oficial Mermaid generado por LangGraph."""
    return app.get_graph().draw_mermaid()


def ejecutar_grafo_texto(consulta: str, origen="py", modo="consulta"):
    """Muestra y registra el diagrama solicitado sin llamar al modelo."""
    inicio = datetime.now(ZONA_HORARIA)
    respuesta = grafo_en_texto()
    print(f"[local] ruta: grafo · modo: {modo}")
    print(respuesta)
    fin = datetime.now(ZONA_HORARIA)
    registrar_log(
        "consulta_grafo",
        consulta,
        {"ruta": "grafo", "respuesta": respuesta},
        inicio,
        fin,
        origen,
        modo,
    )
    return {"ruta": "grafo", "respuesta": respuesta}


def ejecutar_grafo_png():
    """Genera el PNG oficial del grafo en la raíz del proyecto."""
    inicio = datetime.now(ZONA_HORARIA)
    try:
        try:
            raiz = Path(__file__).resolve().parents[1]
        except NameError:
            raiz = Path.cwd()
        destino = raiz / "grafo_ecomarket.png"
        destino.write_bytes(app.get_graph().draw_mermaid_png())
        respuesta = f"PNG generado en: {destino}"
        print(f"\n🖼️ {respuesta}")
        resultado = {"ruta": "grafo_png", "respuesta": respuesta}
        error = None
    except Exception as exc:
        respuesta = f"No se pudo generar el PNG: {exc}"
        print(f"\n❌ {respuesta}")
        resultado = {"ruta": "grafo_png", "respuesta": respuesta}
        error = repr(exc)
    fin = datetime.now(ZONA_HORARIA)
    registrar_log(
        "generar_grafo_png",
        "Generar imagen PNG del grafo EcoMarket",
        resultado,
        inicio,
        fin,
        "py",
        "consulta",
        error=error,
    )
    return resultado


def registrar_log(
    nombre,
    consulta,
    resultado,
    inicio,
    fin,
    origen,
    modo,
    ruta_esperada=None,
    error=None,
):
    """Añade una ejecución al log en formato humano, sin sobrescribir anteriores."""
    ruta_obtenida = resultado.get("ruta", "")
    correcto = ruta_esperada is None or ruta_obtenida == ruta_esperada
    estado = "✅ correcto" if correcto else "⚠️ revisar ruta"
    duracion = round((fin - inicio).total_seconds(), 3)
    separador = "═" * 72
    lineas = [
        "",
        f"╔{separador}╗",
        "║ 🛒 ECO MARKET · REGISTRO DE EJECUCIÓN",
        f"║ {estado} · ejemplo: {nombre} · origen: {origen}",
        f"║ 🎛️ Modo de ejecución: {modo}",
        f"║ 🕐 Inicio Santiago: {inicio.strftime('%Y-%m-%d %H:%M:%S %z')}",
        f"║ 🏁 Fin Santiago:    {fin.strftime('%Y-%m-%d %H:%M:%S %z')}",
        f"║ ⏱️ Duración:         {duracion} segundos",
        f"║ 🧭 Ruta obtenida:    {ruta_obtenida or '(sin ruta)'}",
    ]
    if ruta_esperada:
        lineas.append(f"║ 🎯 Ruta esperada:    {ruta_esperada}")
    lineas.extend(
        [
            "║",
            f"║ 💬 Consulta: {consulta}",
            "║",
            "║ 🤖 Respuesta:",
        ]
    )
    lineas.extend(f"║   {linea}" for linea in resultado.get("respuesta", "").splitlines())
    if error:
        lineas.extend(["║", f"║ ❌ Error: {error}"])
    lineas.append(f"╚{separador}╝")
    nombre_log = {
        "py": "ejecuciones_py.log",
        "ipynb": "ejecuciones_ipynb.log",
    }.get(origen, f"ejecuciones_{origen}.log")
    ruta_log = Path("taller") / nombre_log
    ruta_log.parent.mkdir(parents=True, exist_ok=True)
    with ruta_log.open("a", encoding="utf-8") as archivo:
        archivo.write("\n".join(lineas) + "\n")


def ejecutar_y_registrar(
    consulta: str,
    nombre="consulta",
    ruta_esperada=None,
    origen="py",
    modo="consulta",
):
    """Crea el estado inicial, recorre el grafo, muestra y registra la respuesta."""
    consulta = consulta.strip()
    if not consulta:
        raise ValueError("La consulta no puede estar vacía.")
    inicio = datetime.now(ZONA_HORARIA)
    inicial = {"entrada": consulta, "ruta": "", "respuesta": ""}
    try:
        resultado = trazar(app, inicial, responder_desde="respuesta")
    except Exception as error:
        fin = datetime.now(ZONA_HORARIA)
        registrar_log(
            nombre,
            consulta,
            {},
            inicio,
            fin,
            origen,
            modo,
            ruta_esperada,
            error=repr(error),
        )
        raise
    fin = datetime.now(ZONA_HORARIA)
    registrar_log(nombre, consulta, resultado, inicio, fin, origen, modo, ruta_esperada)
    return resultado


def ejecutar_ejemplos(origen="py", modo="automatico"):
    """Ejecuta automáticamente los cinco casos de prueba documentados."""
    resultados = {}
    for nombre, ejemplo in EJEMPLOS_PRUEBA.items():
        print(f"\n=== EJEMPLO: {nombre} ===")
        print(f"Consulta: {ejemplo['entrada']}")
        resultado = ejecutar_y_registrar(
            ejemplo["entrada"],
            nombre=nombre,
            ruta_esperada=ejemplo["ruta_esperada"],
            origen=origen,
            modo=modo,
        )
        resultados[nombre] = resultado
        ruta = resultado.get("ruta")
        esperada = ejemplo["ruta_esperada"]
        print(f"Ruta obtenida: {ruta} | Ruta esperada: {esperada}")
    return resultados


def ejecutar_interactivo():
    """Muestra un menú y permite atender varias consultas desde la terminal."""
    opciones = {
        "1": ("recetas", EJEMPLOS_PRUEBA["recetas"]["entrada"]),
        "2": ("pedido", EJEMPLOS_PRUEBA["pedido"]["entrada"]),
        "3": ("horarios", EJEMPLOS_PRUEBA["horarios"]["entrada"]),
        "4": ("conversar", EJEMPLOS_PRUEBA["conversar"]["entrada"]),
        "5": ("ofertas_bonus", EJEMPLOS_PRUEBA["ofertas_bonus"]["entrada"]),
    }
    print("\n=== EcoMarket · modo interactivo ===")
    print("Selecciona una opción y escribe tu consulta.")
    while True:
        print("\n1. Recomendar recetas")
        print("2. Consultar estado de pedido")
        print("3. Consultar horarios de despacho")
        print("4. Conversar con el asistente")
        print("5. Consultar ofertas")
        print("6. Escribir una consulta libre")
        print("7. Generar PNG del grafo en la raíz del proyecto")
        print("0. Salir")
        try:
            opcion = input("Opción: ").strip()
        except EOFError:
            print("\nEntrada finalizada.")
            break
        if opcion == "0":
            print("Hasta luego.")
            break
        if opcion == "6":
            consulta = input("Escribe tu consulta: ").strip()
            nombre = "interactivo_libre"
        elif opcion == "7":
            ejecutar_grafo_png()
            continue
        elif opcion == "4":
            print("\n=== Conversación EcoMarket ===")
            print("Escribe /volver para regresar al menú principal.")
            while True:
                try:
                    consulta = input("Tú: ").strip()
                except EOFError:
                    print("\nEntrada finalizada.")
                    return
                if consulta.lower() == "/volver":
                    print("Regresando al menú principal.")
                    break
                if not consulta:
                    print("Escribe un mensaje o /volver para salir.")
                    continue
                ejecutar_consulta(
                    consulta,
                    nombre="interactivo_conversacion",
                    origen="py",
                    modo="consulta",
                )
            continue
        elif opcion in opciones:
            nombre, ejemplo = opciones[opcion]
            consulta = input(
                f"Escribe tu consulta (Enter usa el ejemplo: {ejemplo}): "
            ).strip() or ejemplo
        else:
            print("Opción no válida. Elige un número del 0 al 7.")
            continue
        ejecutar_consulta(
            consulta,
            nombre=f"interactivo_{nombre}",
            origen="py",
            modo="consulta",
        )

# ═══════════════ EJEMPLOS DE PRUEBA ═════════════════════════════════════════
# Copia cualquiera de estas entradas en USER_INPUT para probar cada flujo.
EJEMPLOS_PRUEBA = {
    "recetas": {
        "entrada": "Quiero una receta con palta y tomate",
        "ruta_esperada": "receta",
    },
    "pedido": {
        "entrada": "¿Cuál es el estado de mi pedido 1042?",
        "ruta_esperada": "pedido",
    },
    "horarios": {
        "entrada": "¿Cuáles son los horarios de despacho en Providencia?",
        "ruta_esperada": "horarios",
    },
    "conversar": {
        "entrada": "Hola, ¿qué sabes hacer?",
        "ruta_esperada": "conversar",
    },
    "ofertas_bonus": {
        "entrada": "¿Qué promociones tienen esta semana?",
        "ruta_esperada": "ofertas",
    },
}

# El mapa estático oficial de LangGraph, como imagen en el chat:
#print(app.get_graph().draw_mermaid_png())

# ═══════════════ TODO 5 (BONUS) · OFERTAS IMPLEMENTADO ═════════════════════
# Inventa un flujo nuevo (ofertas de la semana, reclamos, calcular el
# presupuesto de una receta, vinos que maridan...). Necesitas tocar 4 cosas:
#   1. una tool nueva (o datos simulados nuevos)
#   2. un nodo nuevo
#   3. su opcion en el Literal de Ruta (y una pista en PROMPT_ROUTER)
#   4. su entrada en add_conditional_edges + add_edge al END

# %%
# PASO 11 · EJECUCIÓN.
# --consulta abre el menú; --automatico ejecuta los cinco casos.
if "--automatico" in sys.argv:
    final = ejecutar_ejemplos()
elif "--consulta" in sys.argv:
    final = ejecutar_interactivo()
else:
    print("Debes indicar un modo: --consulta, --automatico o --ayuda.")
    raise SystemExit(2)
