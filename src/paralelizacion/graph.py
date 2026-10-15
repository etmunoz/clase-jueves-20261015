"""Planificador de viajes con fan-out y fan-in en LangGraph."""

from __future__ import annotations

import json
import os
from typing import TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from .prompts import (
    ACTIVITIES_PROMPT,
    EXTRACT_PROMPT,
    FLIGHTS_PROMPT,
    HOTEL_PROMPT,
    MERGE_PROMPT,
)


class DatosViaje(BaseModel):
    destino: str = Field(description="Ciudad o destino del viaje.")
    origen: str = Field(description="Ciudad de origen del viaje.")
    dias: int = Field(ge=0, description="Número de días del viaje.")


class ParalelizacionState(TypedDict):
    consulta: str
    viaje: DatosViaje | None
    vuelos: str
    hotel: str
    actividades: str
    itinerario: str


llm = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
    temperature=0,
)
extractor_llm = llm.with_structured_output(DatosViaje)


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


def extraer(state: ParalelizacionState) -> dict:
    """Nodo inicial: extrae destino, origen y días."""
    viaje: DatosViaje = extractor_llm.invoke(
        EXTRACT_PROMPT.format(consulta=state["consulta"])
    )
    return {"viaje": viaje}


def _viaje_json(state: ParalelizacionState) -> str:
    if state["viaje"] is None:
        raise ValueError("Las ramas necesitan la salida del nodo extraer.")
    return json.dumps(state["viaje"].model_dump(), ensure_ascii=False)


def vuelos(state: ParalelizacionState) -> dict:
    """Rama independiente de vuelos simulados."""
    respuesta = llm.invoke(FLIGHTS_PROMPT.format(viaje=_viaje_json(state)))
    return {"vuelos": _texto(respuesta)}


def hotel(state: ParalelizacionState) -> dict:
    """Rama independiente de alojamiento simulado."""
    respuesta = llm.invoke(HOTEL_PROMPT.format(viaje=_viaje_json(state)))
    return {"hotel": _texto(respuesta)}


def actividades(state: ParalelizacionState) -> dict:
    """Rama independiente de actividades y comidas simuladas."""
    respuesta = llm.invoke(ACTIVITIES_PROMPT.format(viaje=_viaje_json(state)))
    return {"actividades": _texto(respuesta)}


def fusionar(state: ParalelizacionState) -> dict:
    """Fan-in: espera las tres ramas y crea el itinerario final."""
    if state["viaje"] is None:
        raise ValueError("Fusionar necesita la salida del nodo extraer.")
    respuesta = llm.invoke(
        MERGE_PROMPT.format(
            viaje=_viaje_json(state),
            vuelos=state["vuelos"],
            hotel=state["hotel"],
            actividades=state["actividades"],
        )
    )
    return {"itinerario": _texto(respuesta)}


workflow = StateGraph(ParalelizacionState)
workflow.add_node("extraer", extraer)
workflow.add_node("vuelos", vuelos)
workflow.add_node("hotel", hotel)
workflow.add_node("actividades", actividades)
workflow.add_node("fusionar", fusionar)
workflow.add_edge(START, "extraer")
# Fan-out: las tres ramas se ejecutan en el mismo superstep.
workflow.add_edge("extraer", "vuelos")
workflow.add_edge("extraer", "hotel")
workflow.add_edge("extraer", "actividades")
# Fan-in: fusionar se activa cuando las tres ramas terminaron.
workflow.add_edge("vuelos", "fusionar")
workflow.add_edge("hotel", "fusionar")
workflow.add_edge("actividades", "fusionar")
workflow.add_edge("fusionar", END)

graph = workflow.compile()

# Usado por main.py para representar el mismo superstep en --saltos.
PARALLEL_NODES = {"vuelos", "hotel", "actividades"}
FAN_IN_NODE = "fusionar"


def initial_state(consulta: str) -> ParalelizacionState:
    return {
        "consulta": consulta,
        "viaje": None,
        "vuelos": "",
        "hotel": "",
        "actividades": "",
        "itinerario": "",
    }


def render_result(resultado: ParalelizacionState) -> str:
    viaje = (
        json.dumps(resultado["viaje"].model_dump(), ensure_ascii=False, indent=2)
        if resultado["viaje"]
        else "{}"
    )
    return f"Viaje extraído:\n{viaje}\n\nItinerario:\n{resultado['itinerario']}"
