"""TALLER · Generador de Recetas para el ecommerce "EcoMarket".

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
"""
import os
import re
from typing import TypedDict, Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END

load_dotenv()

# Ejecutor local: el proyecto usa el entorno virtual y no depende de
# `plataforma`, que solo existe en el entorno privado del taller.
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

# ── La key viene del panel API keys (o backend/.env) — NUNCA del código ────
if not os.environ.get("GOOGLE_API_KEY"):
    print(" Falta **GOOGLE_API_KEY**. Agrégala en el panel *API keys* y vuelve a ejecutar.")
    raise SystemExit(0)

llm = ChatGoogleGenerativeAI(model=os.environ.get("GEMINI_FLASH_LITE_MODEL", "gemini-flash-lite-latest"))

# %%
# ═══════════════════════ ENTREGA · OBLIGATORIO PARA LA EVALUACIÓN ═══════════════════════
# EQUIPO: Fabio Durán · Gustavo Reyes · Ezequiel Muñoz
# 1. Escribe los nombres REALES de los integrantes del equipo.
# 2. Pega aquí tus prompts finales. En el notebook NO existen las variables de la pestaña Prompts
#    de la plataforma: si los dejas vacíos, el agente no rutea ni cocina y la evaluación falla.
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

# En la plataforma mandan los de la pestaña Prompts; en el notebook, los que pegaste arriba.
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


# %%
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

# %%
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

# %%
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

# %%
# ═══════════════ NODO MODELO (LISTO) — imita este patron ═══════════════════
def conversar(estado: Estado):
    """FLUJO CONVERSACIONAL: responde con memoria del chat.

    La plataforma inyecta el historial en CHAT_HISTORY: pasarselo al LLM
    es lo que convierte respuestas sueltas en una CONVERSACION."""
    historial = os.environ.get("CHAT_HISTORY", "[]")
    r = llm.invoke(f"{PROMPT_ASISTENTE}\n\nHistorial de la conversacion: {historial}\n"
                   f"Cliente: {estado['entrada']}")
    return {"respuesta": texto(r)} # Ejemplo del TODO 4

# %%
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
# ═══════════════ EL GRAFO (ya cableado) ════════════════════════════════════
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
# ═══════════════ EJECUCION ═════════════════════════════════════════════════
user_input = os.environ.get("USER_INPUT", "hola, que sabes hacer?")

inicial = {"entrada": user_input, "ruta": "", "respuesta": ""}
final = trazar(app, inicial, responder_desde="respuesta")
