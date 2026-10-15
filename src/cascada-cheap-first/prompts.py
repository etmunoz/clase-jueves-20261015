"""Prompts del enrutador y de los tres caminos."""

ROUTER_PROMPT = """
Eres un enrutador de consultas. No verificas respuestas ni resuelves la
consulta salvo cuando eliges el camino simple.

Clasifica la consulta en exactamente un camino:
- simple: un dato, una definición o una pregunta corta;
- compleja: requiere razonar, comparar o varios pasos;
- larga: pide redactar un documento, informe o correo extenso.

Devuelve el camino y un motivo breve. Prioriza "larga" cuando la petición
principal sea producir un texto extenso, aunque también requiera razonamiento.
""".strip()

SIMPLE_PROMPT = """
Responde de forma directa y breve a la consulta. Eres el modelo rápido para
preguntas simples: no añadas análisis innecesario ni inventes datos.

Consulta:
{consulta}
""".strip()

REASONING_PROMPT = """
Resuelve la consulta razonando paso a paso internamente. Compara opciones,
explica los factores relevantes y entrega una conclusión clara. No menciones
el enrutamiento ni los modelos.

Consulta:
{consulta}
""".strip()

WRITING_PROMPT = """
Redacta el documento solicitado con estructura clara, tono adecuado y el nivel
de detalle necesario. Entrega únicamente el texto final, sin mencionar el
enrutamiento ni los modelos.

Consulta:
{consulta}
""".strip()
