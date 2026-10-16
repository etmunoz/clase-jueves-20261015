# Guía de implementación y validación

## Patrón usado

El taller sigue el mismo patrón de los agentes del directorio `src/`:

1. Un estado explícito.
2. Un nodo por responsabilidad.
3. Prompts separados de la lógica de flujo.
4. Salida estructurada para enrutar.
5. Aristas condicionales hacia nodos especializados.
6. Cada flujo especializado termina en `END`.

## Correspondencia con `taller.py`

- `router`: usa `llm.with_structured_output(Ruta)`.
- `receta`: llama dos tools y luego redacta con el LLM.
- `pedido`: extrae el número, consulta la tool y redacta.
- `horarios`: consulta la tool con el mensaje completo y redacta.
- `conversar`: conserva el historial recibido en `CHAT_HISTORY`.
- `ofertas`: consulta la tool bonus y redacta.

## Checklist de entrega

- [x] Nombres reales del equipo pegados en `INTEGRANTES`.
- [x] Prompt del router pegado en `PROMPT_ROUTER_ENTREGA`.
- [x] Prompt del chef pegado en `PROMPT_CHEF_ENTREGA`.
- [x] Prompt del asistente pegado en `PROMPT_ASISTENTE_ENTREGA`.
- [x] TODO 1 completado.
- [x] TODO 2 completado.
- [x] TODO 3 completado.
- [x] Bonus de ofertas implementado.
- [x] `plan.json` creado.
- [x] Carpeta `.opencode/` creada.
- [x] `taller/taller.ipynb` generado a partir de `taller.py`.
- [ ] Ejecutar `Kernel → Restart and Run All` en el notebook/plataforma.
- [ ] Probar las cinco consultas de `plan.json` y revisar el diagrama.
- [ ] Crear el ZIP final con `taller.py`, `plan.json` y `.opencode/`.

## Pruebas manuales

Usar estas entradas:

```text
Quiero una receta con palta
¿Dónde está mi pedido 1042?
¿Cuáles son los horarios de despacho en Providencia?
¿Qué ofertas tienen esta semana?
Hola, ¿qué sabes hacer?
```

Para cada caso comprobar que el router elige, respectivamente,
`receta`, `pedido`, `horarios`, `ofertas` y `conversar`, y que la respuesta
usa los datos de la tool correspondiente.

## Nota sobre la plataforma

El archivo depende de `plataforma` para `chat`, `texto` y `trazar`, por lo que
la validación completa debe hacerse dentro del notebook o entorno del taller,
con `GOOGLE_API_KEY` configurada en el panel de API keys.
