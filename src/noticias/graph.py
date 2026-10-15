"""Flujo ReAct explícito del agente de noticias."""

import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from .prompts import SYSTEM_PROMPT
from .tools import buscar_noticias


model = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
    temperature=0,
).bind_tools([buscar_noticias])


def llamar_modelo(state: MessagesState) -> dict[str, list]:
    """Ejecuta el modelo y permite que solicite una herramienta."""
    mensajes = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
    respuesta = model.invoke(mensajes)
    return {"messages": [respuesta]}


# Flujo ReAct:
# START -> agent -> (tools si hay tool_call, END si la respuesta está lista)
#          tools -> agent
workflow = StateGraph(MessagesState)
workflow.add_node("agent", llamar_modelo)
workflow.add_node("tools", ToolNode([buscar_noticias]))
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", tools_condition)
workflow.add_edge("tools", "agent")

graph = workflow.compile()
