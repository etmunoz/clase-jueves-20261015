"""Flujo de planificación y recomendaciones paso a paso."""

from __future__ import annotations

import os
from typing import Literal, TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from .prompts import PLAN_PROMPT, RECOMMENDATION_PROMPT


class Plan(BaseModel):
    pasos: list[str] = Field(description="Lista de los pasos a ejecutar.")


class PlanificadorState(TypedDict):
    consulta: str
    pasos: list[str]
    indice: int
    recomendaciones: list[str]


llm = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
    temperature=0,
)
plan_llm = llm.with_structured_output(Plan)


def _texto(respuesta: AIMessage | str | object) -> str:
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


def planificador(state: PlanificadorState) -> dict:
    """Genera los pasos estructurados a partir de la consulta."""
    resultado: Plan = plan_llm.invoke(
        f"{PLAN_PROMPT}\n\nConsulta del usuario:\n{state['consulta']}"
    )
    pasos = [paso.strip() for paso in resultado.pasos if paso.strip()]
    return {"pasos": pasos, "indice": 0, "recomendaciones": []}


def recomendador(state: PlanificadorState) -> dict:
    """Recomienda cómo ejecutar solamente el paso actual."""
    paso = state["pasos"][state["indice"]]
    respuesta = llm.invoke(RECOMMENDATION_PROMPT.format(paso=paso))
    return {
        "recomendaciones": [*state["recomendaciones"], _texto(respuesta)],
        "indice": state["indice"] + 1,
    }


def siguiente_nodo(
    state: PlanificadorState,
) -> Literal["recomendador", "__end__"]:
    """Vuelve al recomendador para el siguiente paso o finaliza el grafo."""
    if state["indice"] < len(state["pasos"]):
        return "recomendador"
    return END


workflow = StateGraph(PlanificadorState)
workflow.add_node("planificador", planificador)
workflow.add_node("recomendador", recomendador)
workflow.add_edge(START, "planificador")
workflow.add_edge("planificador", "recomendador")
workflow.add_conditional_edges(
    "recomendador",
    siguiente_nodo,
    path_map={
        "recomendador": "recomendador",  # ciclo: procesa pasos[indice]
        END: END,
    },
)

graph = workflow.compile()


def initial_state(consulta: str) -> PlanificadorState:
    """Crea el estado inicial usado por main.py."""
    return {
        "consulta": consulta,
        "pasos": [],
        "indice": 0,
        "recomendaciones": [],
    }


def render_result(resultado: PlanificadorState) -> str:
    """Renderiza el plan completo con su recomendación correspondiente."""
    if not resultado["pasos"]:
        return "No se generaron pasos para esta consulta."
    bloques = ["Plan completo:"]
    for numero, (paso, recomendacion) in enumerate(
        zip(resultado["pasos"], resultado["recomendaciones"]), start=1
    ):
        bloques.append(f"\n{numero}. {paso}\n   Recomendación: {recomendacion}")
    return "\n".join(bloques)
