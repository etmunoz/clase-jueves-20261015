"""Punto de entrada para ejecutar agentes del proyecto."""

from __future__ import annotations

import argparse
import importlib
import os
import sys
from collections.abc import Iterator
from typing import Any

from dotenv import load_dotenv


def _mensajes_de(actualizacion: Any) -> list[Any]:
    if not isinstance(actualizacion, dict):
        return []
    mensajes = actualizacion.get("messages", [])
    return mensajes if isinstance(mensajes, list) else [mensajes]


def _texto_contenido(contenido: Any) -> str:
    """Convierte contenido simple o bloques de contenido de Gemini a texto."""
    if isinstance(contenido, str):
        return contenido
    if isinstance(contenido, list):
        partes = []
        for bloque in contenido:
            if isinstance(bloque, dict) and bloque.get("text"):
                partes.append(str(bloque["text"]))
            elif isinstance(bloque, str):
                partes.append(bloque)
        return "".join(partes)
    return str(contenido) if contenido else ""


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
        texto = _texto_contenido(contenido)
        if texto and getattr(mensaje, "type", None) == "ai":
            return texto
    return "El agente no devolvió una respuesta."


def ejecutar(nombre_agente: str, consulta: str, mostrar_saltos: bool) -> None:
    modulo = importlib.import_module(f"src.{nombre_agente}.graph")
    graph = modulo.graph
    crear_estado = getattr(modulo, "initial_state", None)
    estado = (
        crear_estado(consulta)
        if crear_estado
        else {"messages": [{"role": "user", "content": consulta}]}
    )

    if mostrar_saltos:
        estado_actual: dict[str, Any] = dict(estado)
        nodos_paralelos = set(getattr(modulo, "PARALLEL_NODES", ()))
        nodo_fan_in = getattr(modulo, "FAN_IN_NODE", None)
        paso_paralelo: int | None = None
        for numero, actualizacion in enumerate(
            graph.stream(estado, stream_mode="updates"), start=1
        ):
            for nodo, datos in actualizacion.items():
                numero_visible = numero
                if nodo in nodos_paralelos:
                    paso_paralelo = paso_paralelo or numero
                    numero_visible = paso_paralelo
                elif nodo == nodo_fan_in and paso_paralelo is not None:
                    numero_visible = paso_paralelo + 1
                if isinstance(datos, dict):
                    for clave, valor in datos.items():
                        if clave == "messages" and isinstance(valor, list):
                            estado_actual[clave] = [
                                *estado_actual.get(clave, []),
                                *valor,
                            ]
                        else:
                            estado_actual[clave] = valor
                render_salto = getattr(modulo, "render_jump", None)
                detalle = render_salto(nodo, datos, numero) if render_salto else None
                _mostrar_salto(nodo, datos, numero_visible)
                if detalle:
                    print(detalle)
        print("\nResumen:\n")
        render_resultado = getattr(modulo, "render_result", None)
        print(
            render_resultado(estado_actual)
            if render_resultado
            else _respuesta_final(estado_actual)
        )
        return

    resultado = graph.invoke(estado)
    render_resultado = getattr(modulo, "render_result", None)
    print(render_resultado(resultado) if render_resultado else _respuesta_final(resultado))


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
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
