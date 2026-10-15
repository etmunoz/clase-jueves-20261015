"""Herramientas para consultar noticias públicas mediante RSS."""

from __future__ import annotations

import html
import re
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from langchain_core.tools import tool


def _texto_limpio(valor: str | None) -> str:
    """Elimina etiquetas HTML y espacios innecesarios de un texto RSS."""
    if not valor:
        return ""
    sin_html = re.sub(r"<[^>]+>", " ", html.unescape(valor))
    return re.sub(r"\s+", " ", sin_html).strip()


@tool
def buscar_noticias(tema: str = "", max_resultados: int = 8) -> str:
    """Busca noticias recientes en Google News RSS.

    Args:
        tema: Tema o consulta de búsqueda. Vacío devuelve las noticias principales.
        max_resultados: Número máximo de resultados, entre 1 y 15.
    """
    max_resultados = max(1, min(max_resultados, 15))
    if tema.strip():
        url = (
            "https://news.google.com/rss/search?q="
            f"{quote_plus(tema.strip())}&hl=es-419&gl=MX&ceid=MX:es-419"
        )
    else:
        url = "https://news.google.com/rss?hl=es-419&gl=MX&ceid=MX:es-419"

    request = Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; AgenteNoticias/1.0)"},
    )
    try:
        with urlopen(request, timeout=15) as response:
            contenido = response.read()
        raiz = ElementTree.fromstring(contenido)
    except Exception as exc:
        return f"No fue posible consultar las noticias: {exc}"

    resultados: list[str] = []
    for item in raiz.findall("./channel/item")[:max_resultados]:
        def campo(nombre: str) -> str:
            elemento = item.find(nombre)
            return _texto_limpio(elemento.text if elemento is not None else "")

        titulo = campo("title")
        enlace = campo("link")
        fecha = campo("pubDate")
        descripcion = campo("description")
        fuente = campo("source")
        resultados.append(
            "\n".join(
                parte
                for parte in (
                    f"Título: {titulo}",
                    f"Fuente: {fuente}" if fuente else "",
                    f"Fecha: {fecha}" if fecha else "",
                    f"Resumen de fuente: {descripcion}" if descripcion else "",
                    f"Enlace: {enlace}",
                )
                if parte
            )
        )

    if not resultados:
        return "No se encontraron noticias para esa consulta."
    return "\n\n---\n\n".join(resultados)
