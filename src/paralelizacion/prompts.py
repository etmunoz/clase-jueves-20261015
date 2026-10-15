"""Prompts independientes de las ramas paralelas y de la fusión."""

EXTRACT_PROMPT = """
Extrae del pedido de viaje estos datos estructurados: destino, origen y número
de días. Si un dato no aparece, usa una cadena vacía o 0. No planifiques aún.

Pedido:
{consulta}
""".strip()

FLIGHTS_PROMPT = """
Eres la rama de vuelos de un planificador de viajes.
Con los datos del viaje, propone una opción simulada de vuelo de ida y vuelta,
incluyendo horarios plausibles y precio aproximado. No consultes APIs ni
afirmes que los datos son reales: indica claramente que son simulados.

Viaje: {viaje}
""".strip()

HOTEL_PROMPT = """
Eres la rama de alojamiento de un planificador de viajes.
Propón exactamente 2 opciones simuladas de alojamiento, indicando zona y
precio aproximado por noche. No consultes APIs ni afirmes que existen plazas
reales: indica claramente que los datos son simulados.

Viaje: {viaje}
""".strip()

ACTIVITIES_PROMPT = """
Eres la rama de actividades de un planificador de viajes.
Arma un plan simulado para cada día del viaje, con lugares para visitar y una
opción de dónde comer. No consultes APIs ni afirmes que hay reservas reales.

Viaje: {viaje}
""".strip()

MERGE_PROMPT = """
Eres el nodo final de un planificador de viajes.
Fusiona las tres propuestas simuladas en un itinerario día por día. Incluye
vuelos de ida y vuelta, alojamiento, actividades y comidas. Mantén visibles
las dos opciones de hotel y señala que precios y horarios son aproximados y
simulados. No inventes datos fuera de las propuestas recibidas.

Datos del viaje: {viaje}

Vuelos:
{vuelos}

Hoteles:
{hotel}

Actividades:
{actividades}
""".strip()
