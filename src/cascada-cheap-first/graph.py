"""Cascada de modelos: enrutador barato y ejecución de un único camino."""

from __future__ import annotations

import os
from typing import Literal, TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from .prompts import REASONING_PROMPT, ROUTER_PROMPT, SIMPLE_PROMPT, WRITING_PROMPT


class DecisionRuta(BaseModel):
    camino: Literal["simple", "compleja", "larga"]
    motivo: str = Field(description="Por qué la consulta requiere ese camino.")


class CascadaState(TypedDict):
    consulta: str
    decision: DecisionRuta | None
    respuesta: str
    modelo_respuesta: str


def _modelo(variable: str, valor_por_defecto: str) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=os.getenv(variable, valor_por_defecto),
        temperature=0,
    )


def _texto(respuesta: object) -> str:
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


def enrutador(state: CascadaState) -> dict:
    """Decide el camino con flash-lite y responde si la consulta es simple."""
    modelo_nombre = os.getenv("GEMINI_FLASH_LITE_MODEL", "gemini-flash-lite-latest")
    modelo = _modelo("GEMINI_FLASH_LITE_MODEL", "gemini-flash-lite-latest")
    decision: DecisionRuta = modelo.with_structured_output(DecisionRuta).invoke(
        f"{ROUTER_PROMPT}\n\nConsulta:\n{state['consulta']}"
    )
    resultado = {
        "decision": decision,
        "modelo_respuesta": "",
        "respuesta": "",
    }
    if decision.camino == "simple":
        resultado["respuesta"] = _texto(
            modelo.invoke(SIMPLE_PROMPT.format(consulta=state["consulta"]))
        )
        resultado["modelo_respuesta"] = modelo_nombre
    return resultado


def razonamiento(state: CascadaState) -> dict:
    """Resuelve consultas complejas con el modelo flash medio."""
    modelo_nombre = os.getenv("GEMINI_FLASH_MODEL", "gemini-3.8-flash")
    respuesta = _modelo("GEMINI_FLASH_MODEL", "gemini-3.8-flash").invoke(
        REASONING_PROMPT.format(consulta=state["consulta"])
    )
    return {"respuesta": _texto(respuesta), "modelo_respuesta": modelo_nombre}


def redaccion(state: CascadaState) -> dict:
    """Redacta documentos largos con el modelo pro caro."""
    modelo_nombre = os.getenv("GEMINI_PRO_MODEL", "gemini-3.1-pro-preview")
    respuesta = _modelo("GEMINI_PRO_MODEL", "gemini-3.1-pro-preview").invoke(
        WRITING_PROMPT.format(consulta=state["consulta"])
    )
    return {"respuesta": _texto(respuesta), "modelo_respuesta": modelo_nombre}


def siguiente_camino(state: CascadaState) -> Literal["simple", "razonamiento", "redaccion"]:
    """Deriva a un solo camino; el enrutador nunca se repite."""
    if state["decision"] is None:
        raise ValueError("No existe una decisión de enrutamiento.")
    return {
        "simple": "simple",
        "compleja": "razonamiento",
        "larga": "redaccion",
    }[state["decision"].camino]


workflow = StateGraph(CascadaState)
workflow.add_node("enrutador", enrutador)
workflow.add_node("razonamiento", razonamiento)
workflow.add_node("redaccion", redaccion)
workflow.add_edge(START, "enrutador")
workflow.add_conditional_edges(
    "enrutador",
    siguiente_camino,
    path_map={
        "simple": END,
        "razonamiento": "razonamiento",
        "redaccion": "redaccion",
    },
)
workflow.add_edge("razonamiento", END)
workflow.add_edge("redaccion", END)

graph = workflow.compile()


def initial_state(consulta: str) -> CascadaState:
    return {"consulta": consulta, "decision": None, "respuesta": "", "modelo_respuesta": ""}


def render_jump(nodo: str, datos: object, _numero: int) -> str | None:
    if nodo != "enrutador" or not isinstance(datos, dict):
        return None
    decision = datos.get("decision")
    if decision is None:
        return None
    destino = {"simple": "simple/END", "compleja": "razonamiento", "larga": "redaccion"}[decision.camino]
    modelo = datos.get("modelo_respuesta") or {
        "compleja": os.getenv("GEMINI_FLASH_MODEL", "gemini-3.8-flash"),
        "larga": os.getenv("GEMINI_PRO_MODEL", "gemini-3.1-pro-preview"),
    }.get(decision.camino, "pendiente")
    return (
        f"    camino elegido: {destino}\n"
        f"    motivo: {decision.motivo}\n"
        f"    modelo: {modelo}"
    )


def render_result(resultado: CascadaState) -> str:
    decision = resultado["decision"]
    camino = decision.camino if decision else "desconocido"
    motivo = decision.motivo if decision else "sin motivo"
    return (
        f"Camino: {camino}\nMotivo: {motivo}\n"
        f"Modelo: {resultado['modelo_respuesta']}\n\n"
        f"Respuesta:\n{resultado['respuesta']}"
    )
