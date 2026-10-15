"""Punto de entrada para ejecutar agentes del proyecto."""

from __future__ import annotations

import argparse
import importlib
import os
from collections.abc import Iterator
from typing import Any

from dotenv import load_dotenv


def _mensajes_de(actualizacion: Any) -> list[Any]:
    if not isinstance(actualizacion, dict):
        return []
    mensajes = actualizacion.get("messages", [])
    return mensajes if isinstance(mensajes, list) else [mensajes]


def _mostrar_salto(nodo: str, actualizacion: Any, numero: int) -> None:
    print(f"[{numero}] nodo: {nodo}")
    for mensaje in _mensajes_de(actualizacion):
        nombre = getattr(mensaje, "name", None)
        tipo = getattr(mensaje, "type", None)
        if nombre and (tipo == "tool" or nodo == "tools"):
            print(f"    herramienta: {nombre}")
        for llamada in getattr(mensaje, "tool_calls", []) or []:
            print(f"    herramienta: {llamada.get('name', 'desconocida')}")


def _respuesta_final(actualizacion: Any) -> str:
    mensajes = _mensajes_de(actualizacion)
    for mensaje in reversed(mensajes):
        contenido = getattr(mensaje, "content", None)
        if contenido and getattr(mensaje, "type", None) == "ai":
            return str(contenido)
    return "El agente no devolvió una respuesta."


def ejecutar(nombre_agente: str, consulta: str, mostrar_saltos: bool) -> None:
    modulo = importlib.import_module(f"src.{nombre_agente}.graph")
    graph = modulo.graph
    estado = {"messages": [{"role": "user", "content": consulta}]}

    if mostrar_saltos:
        ultima_actualizacion: Any = {}
        for numero, actualizacion in enumerate(
            graph.stream(estado, stream_mode="updates"), start=1
        ):
            ultima_actualizacion = actualizacion
            for nodo, datos in actualizacion.items():
                _mostrar_salto(nodo, datos, numero)
        print("\nResumen:\n")
        print(_respuesta_final(ultima_actualizacion))
        return

    resultado = graph.invoke(estado)
    print(_respuesta_final(resultado))


def main() -> None:
    load_dotenv()
    if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]
    parser = argparse.ArgumentParser(description="Ejecuta un agente LangGraph.")
    parser.add_argument("nombre_agente", help="Nombre del agente dentro de src/")
    parser.add_argument(
        "consulta", nargs="*", help="Consulta opcional para el agente"
    )
    parser.add_argument(
        "--saltos", action="store_true", help="Muestra nodos y herramientas visitados"
    )
    parser.add_argument(
        "--diagrama", action="store_true", help="Imprime el diagrama Mermaid"
    )
    args = parser.parse_args()

    modulo = importlib.import_module(f"src.{args.nombre_agente}.graph")
    if args.diagrama:
        print(modulo.graph.get_graph().draw_mermaid())
        return

    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        parser.error("Configura GOOGLE_API_KEY (o GEMINI_API_KEY) en .env")

    consulta = " ".join(args.consulta).strip() or (
        "Busca las noticias más relevantes de hoy y prepara un resumen."
    )
    ejecutar(args.nombre_agente, consulta, args.saltos)


if __name__ == "__main__":
    main()
