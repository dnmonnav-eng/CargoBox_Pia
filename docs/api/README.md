# Especificación de la API (OpenAPI)

`openapi.json` es la especificación OpenAPI 3.1 de la CargoBox API 1.0.0. Se generó directamente desde la aplicación FastAPI (`src/api/api.py`), así que coincide con lo que muestra Swagger UI.

Para verla de forma interactiva, levanta el servidor y abre `http://127.0.0.1:8000/docs`, o pega el contenido de `openapi.json` en <https://editor.swagger.io>.

Para regenerarla después de cambiar la API:

```bash
python -c "import json; from src.api.api import app; json.dump(app.openapi(), open('docs/api/openapi.json','w'), ensure_ascii=False, indent=2)"
```

## Endpoints

| Método | Ruta | Acción del negocio | Respuestas de error |
|---|---|---|---|
| GET | `/` | Mensaje de bienvenida | — |
| POST | `/paquetes/` | Registrar paquete y generar guía `CBX-XXXXXXXX` | 422 límite físico o datos inválidos |
| POST | `/paquetes/{guia}/clasificar` | RECIBIDO → CLASIFICADO | 404 guía inexistente, 409 transición inválida |
| POST | `/paquetes/{guia}/despachar-transito` | CLASIFICADO → EN_TRANSITO | 404, 409 |
| POST | `/paquetes/{guia}/centro-destino` | EN_TRANSITO → CENTRO_DESTINO | 404, 409 |
| POST | `/paquetes/{guia}/iniciar-reparto` | CENTRO_DESTINO → EN_REPARTO (reinicia intentos) | 404, 409 |
| POST | `/paquetes/{guia}/intentos-fallidos` | Registrar visita fallida (máx. 2) | 404, 409, 422 límite de intentos |
| POST | `/paquetes/{guia}/incidencias` | `direccion_incorrecta`, `paquete_danado`, `perdida` o `rechazo` | 400 incidencia no válida, 404 |
| POST | `/paquetes/{guia}/entregar` | EN_REPARTO → ENTREGADO con evidencia POD | 404, 409, 422 sin evidencia |

## Ejemplo de registro

```json
POST /paquetes/
{
  "peso_kg": 15.0,
  "largo_m": 1.0,
  "ancho_m": 0.5,
  "alto_m": 0.5,
  "telefono_cliente": "8112345678"
}
```

Respuesta:

```json
{ "mensaje": "Paquete recibido con éxito, guía única generada: CBX-1A2B3C4D." }
```
