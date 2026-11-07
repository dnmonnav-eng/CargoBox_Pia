# ADR-005: API REST con FastAPI y documentación OpenAPI

- **Estado:** Aceptada
- **Fecha:** 2026-11-05
- **Equipo:** Equipo 14 — CargoBox

## Contexto

La rúbrica exige una API REST documentada con Swagger UI/OpenAPI activo en la demostración. Los usuarios internos (sucursal, centro de distribución, repartidores, soporte) necesitan operaciones claras y mensajes comprensibles.

## Decisión

- Implementar la API con FastAPI en `src/api/api.py`, con un endpoint por acción del negocio (`/paquetes/`, `/clasificar`, `/despachar-transito`, `/centro-destino`, `/iniciar-reparto`, `/intentos-fallidos`, `/incidencias`, `/entregar`).
- Validar la entrada con modelos Pydantic.
- Traducir excepciones de dominio a códigos HTTP consistentes (404, 409, 422, 400).
- Publicar la especificación generada en `docs/api/openapi.json` y servir Swagger UI en `/docs`.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Flask + extensión de Swagger | La documentación se mantiene a mano y se desincroniza del código |
| Django REST Framework | Demasiado para un solo agregado; trae su propio ORM |
| Un único endpoint `PATCH /paquetes/{guia}` con el estado deseado | Oculta las acciones del negocio y deja la validación de transiciones en el cliente |

## Consecuencias

- **Positivas:** Swagger UI y OpenAPI salen del mismo código, así que no se desincronizan; cada endpoint coincide con una acción del BPMN; los mensajes de respuesta están en español y orientados al usuario.
- **Negativas:** todas las acciones usan `POST`; no hay todavía un `GET /paquetes/{guia}` para consultar el rastreo ni autenticación (fuera de alcance según el BRD).
