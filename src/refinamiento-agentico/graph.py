"""Grafo de generación y evaluación iterativa de un correo."""

from __future__ import annotations

import os
from typing import Literal, TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from .prompts import EVALUATOR_PROMPT, GENERATOR_PROMPT


class Evaluacion(BaseModel):
    nota: int = Field(ge=1, le=10, description="Nota global del correo, de 1 a 10.")
    criterios_fallidos: list[str] = Field(
        description="Criterios que fallan: claridad, tono, longitud o completitud."
    )
    observacion: str = Field(
        description="Una observación concreta para corregir el correo."
    )


class RefinamientoState(TypedDict):
    encargo: str
    texto: str
    evaluacion: Evaluacion | None
    vuelta: int


llm = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
    temperature=0,
)
evaluador_llm = llm.with_structured_output(Evaluacion)


def generador(state: RefinamientoState) -> dict:
    """Crea o mejora el correo según las reglas del nodo generador."""
    evaluacion = state["evaluacion"]
    observacion = evaluacion.observacion if evaluacion else "Primera redacción."
    texto_actual = state["texto"] or "(No existe un texto previo.)"
    respuesta = llm.invoke(
        GENERATOR_PROMPT.format(
            encargo=state["encargo"],
            texto_actual=texto_actual,
            observacion=observacion,
        )
    )
    contenido = respuesta.content
    if isinstance(contenido, list):
        contenido = "".join(
            str(bloque.get("text", ""))
            if isinstance(bloque, dict)
            else str(bloque)
            for bloque in contenido
        )
    return {"texto": str(contenido), "vuelta": state["vuelta"] + 1}


def evaluador(state: RefinamientoState) -> dict:
    """Califica el correo exclusivamente con los cuatro criterios definidos."""
    resultado: Evaluacion = evaluador_llm.invoke(
        EVALUATOR_PROMPT.format(
            encargo=state["encargo"],
            texto=state["texto"],
        )
    )
    return {"evaluacion": resultado}


def siguiente_nodo(
    state: RefinamientoState,
) -> Literal["generador", "__end__"]:
    """Detiene con nota suficiente o en la tercera vuelta; si no, refina."""
    evaluacion = state["evaluacion"]
    if evaluacion and (evaluacion.nota >= 8 or state["vuelta"] >= 3):
        return END
    return "generador"


workflow = StateGraph(RefinamientoState)
workflow.add_node("generador", generador)
workflow.add_node("evaluador", evaluador)
workflow.add_edge(START, "generador")
workflow.add_edge("generador", "evaluador")
workflow.add_conditional_edges(
    "evaluador",
    siguiente_nodo,
    path_map={"generador": "generador", END: END},
)

graph = workflow.compile()


def initial_state(consulta: str) -> RefinamientoState:
    return {"encargo": consulta, "texto": "", "evaluacion": None, "vuelta": 0}


def render_result(resultado: RefinamientoState) -> str:
    evaluacion = resultado["evaluacion"]
    if evaluacion is None:
        return resultado["texto"]
    criterios = ", ".join(evaluacion.criterios_fallidos) or "ninguno"
    return (
        f"Texto final (vuelta {resultado['vuelta']}):\n\n{resultado['texto']}\n\n"
        f"Evaluación: {evaluacion.nota}/10\n"
        f"Criterios fallidos: {criterios}\n"
        f"Observación: {evaluacion.observacion}"
    )
