"""Grafo ReAct del agente de noticias."""

import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

from .prompts import SYSTEM_PROMPT
from .tools import buscar_noticias


model = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    temperature=0,
)

graph = create_react_agent(
    model=model,
    tools=[buscar_noticias],
    prompt=SYSTEM_PROMPT,
)
