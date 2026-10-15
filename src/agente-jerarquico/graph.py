"""Supervisor jerárquico que deriva cada consulta a un solo sub-agente."""

from __future__ import annotations

import os
from typing import TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from .prompts import SUBAGENTS, SUPERVISOR_PROMPT


class DecisionSupervisor(BaseModel):
    nombre_subagente: str = Field(description="Nombre exacto del sub-agente elegido.")
    motivo: str = Field(description="Motivo breve de la elección.")


class JerarquicoState(TypedDict):
    consulta: str
    decision: DecisionSupervisor | None
    respuesta: str


llm = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
    temperature=0,
)
supervisor_llm = llm.with_structured_output(DecisionSupervisor)
subagents_by_name = {subagent["nombre"]: subagent for subagent in SUBAGENTS}


def supervisor(state: JerarquicoState) -> dict:
    """Elige un único sub-agente; nunca responde la consulta."""
    catalogo = "\n".join(
        f"- {subagent['nombre']}: {subagent['descripcion']}"
        for subagent in SUBAGENTS
    )
    decision: DecisionSupervisor = supervisor_llm.invoke(
        SUPERVISOR_PROMPT.format(catalogo=catalogo, consulta=state["consulta"])
    )
    if decision.nombre_subagente not in subagents_by_name:
        raise ValueError(
            f"El supervisor eligió un sub-agente inexistente: "
            f"{decision.nombre_subagente}"
        )
    return {"decision": decision}


def _crear_nodo_subagente(config: dict[str, str]):
    """Crea un nodo usando exclusivamente la entrada del catálogo."""

    def ejecutar(state: JerarquicoState) -> dict:
        respuesta = llm.invoke(
            f"{config['prompt']}\n\nConsulta del usuario:\n{state['consulta']}"
        )
        contenido = respuesta.content
        if isinstance(contenido, list):
            contenido = "".join(
                str(bloque.get("text", ""))
                if isinstance(bloque, dict)
                else str(bloque)
                for bloque in contenido
            )
        return {"respuesta": str(contenido)}

    ejecutar.__name__ = config["nombre"]
    return ejecutar


def seleccionar_subagente(state: JerarquicoState) -> str:
    """Devuelve el nombre elegido para dirigir el flujo a un solo nodo."""
    if state["decision"] is None:
        raise ValueError("No existe una decisión del supervisor.")
    return state["decision"].nombre_subagente


workflow = StateGraph(JerarquicoState)
workflow.add_node("supervisor", supervisor)
for subagent in SUBAGENTS:
    workflow.add_node(subagent["nombre"], _crear_nodo_subagente(subagent))
workflow.add_edge(START, "supervisor")
workflow.add_conditional_edges(
    "supervisor",
    seleccionar_subagente,
    path_map={subagent["nombre"]: subagent["nombre"] for subagent in SUBAGENTS},
)
for subagent in SUBAGENTS:
    workflow.add_edge(subagent["nombre"], END)

graph = workflow.compile()


def initial_state(consulta: str) -> JerarquicoState:
    return {"consulta": consulta, "decision": None, "respuesta": ""}


def render_jump(nodo: str, datos: object, _numero: int) -> str | None:
    """Añade al modo --saltos la decisión del supervisor."""
    if nodo != "supervisor" or not isinstance(datos, dict):
        return None
    decision = datos.get("decision")
    if decision is None:
        return None
    return (
        f"    sub-agente elegido: {decision.nombre_subagente}\n"
        f"    motivo: {decision.motivo}"
    )


def render_result(resultado: JerarquicoState) -> str:
    decision = resultado["decision"]
    eleccion = decision.nombre_subagente if decision else "desconocido"
    motivo = decision.motivo if decision else "sin motivo"
    return (
        f"Sub-agente elegido: {eleccion}\n"
        f"Motivo: {motivo}\n\n"
        f"Respuesta:\n{resultado['respuesta']}"
    )
