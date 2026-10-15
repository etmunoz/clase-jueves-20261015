"""Workflow lineal de extracción, clasificación y redacción de correos."""

from __future__ import annotations

import json
import os
from typing import Literal, TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from .prompts import CLASSIFY_PROMPT, EXTRACT_PROMPT, WRITE_PROMPT


class DatosClave(BaseModel):
    nombre_cliente: str = Field(description="Nombre del cliente o cadena vacía.")
    producto_servicio: str = Field(
        description="Producto o servicio mencionado o cadena vacía."
    )
    fecha: str = Field(description="Fecha mencionada o cadena vacía.")
    peticion: str = Field(description="Qué pide exactamente el cliente.")


class Clasificacion(BaseModel):
    tipo: Literal["reclamo", "consulta", "solicitud"]
    prioridad: Literal["alta", "media", "baja"]
    motivo: str = Field(description="Motivo breve de la clasificación.")


class WorkflowState(TypedDict):
    correo: str
    datos: DatosClave | None
    clasificacion: Clasificacion | None
    respuesta: str


llm = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
    temperature=0,
)
extractor_llm = llm.with_structured_output(DatosClave)
clasificador_llm = llm.with_structured_output(Clasificacion)


def extraer(state: WorkflowState) -> dict:
    """Nodo 1: extrae únicamente los cuatro datos clave del correo."""
    datos: DatosClave = extractor_llm.invoke(
        EXTRACT_PROMPT.format(correo=state["correo"])
    )
    return {"datos": datos}


def clasificar(state: WorkflowState) -> dict:
    """Nodo 2: clasifica tipo y prioridad, explicando el motivo."""
    datos = state["datos"]
    if datos is None:
        raise ValueError("El nodo clasificar necesita la salida del nodo extraer.")
    clasificacion: Clasificacion = clasificador_llm.invoke(
        CLASSIFY_PROMPT.format(datos=json.dumps(datos.model_dump(), ensure_ascii=False))
    )
    return {"clasificacion": clasificacion}


def redactar(state: WorkflowState) -> dict:
    """Nodo 3: redacta según el tipo y prioridad producidos por clasificar."""
    datos = state["datos"]
    clasificacion = state["clasificacion"]
    if datos is None or clasificacion is None:
        raise ValueError("El nodo redactar necesita extracción y clasificación.")
    respuesta = llm.invoke(
        WRITE_PROMPT.format(
            tipo=clasificacion.tipo,
            prioridad=clasificacion.prioridad,
            motivo=clasificacion.motivo,
            datos=json.dumps(datos.model_dump(), ensure_ascii=False),
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
    return {"respuesta": str(contenido)}


workflow = StateGraph(WorkflowState)
workflow.add_node("extraer", extraer)
workflow.add_node("clasificar", clasificar)
workflow.add_node("redactar", redactar)
workflow.add_edge(START, "extraer")
workflow.add_edge("extraer", "clasificar")
workflow.add_edge("clasificar", "redactar")
workflow.add_edge("redactar", END)

graph = workflow.compile()


def initial_state(consulta: str) -> WorkflowState:
    return {"correo": consulta, "datos": None, "clasificacion": None, "respuesta": ""}


def render_result(resultado: WorkflowState) -> str:
    datos = resultado["datos"]
    clasificacion = resultado["clasificacion"]
    datos_json = json.dumps(
        datos.model_dump() if datos else {}, ensure_ascii=False, indent=2
    )
    clasificacion_json = json.dumps(
        clasificacion.model_dump() if clasificacion else {},
        ensure_ascii=False,
        indent=2,
    )
    return (
        f"Datos extraídos (JSON):\n{datos_json}\n\n"
        f"Clasificación (JSON):\n{clasificacion_json}\n\n"
        f"Respuesta redactada:\n{resultado['respuesta']}"
    )
