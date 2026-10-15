"""Prompts del agente planificador."""

PLAN_PROMPT = """
Convierte la consulta del usuario en un plan práctico y ordenado.
Devuelve únicamente los pasos necesarios para alcanzar el objetivo.
Cada paso debe ser concreto, accionable y suficientemente independiente para
que otro agente pueda explicar cómo ejecutarlo.
""".strip()

RECOMMENDATION_PROMPT = """
Explica cómo llevar a cabo el siguiente paso de forma práctica.
Incluye acciones concretas, herramientas o recursos útiles y cualquier
precaución relevante. No desarrolles otros pasos ni inventes información.

Paso:
{paso}
""".strip()
