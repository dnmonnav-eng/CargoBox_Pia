# Documento de decisiones técnicas

## Stack tecnológico

| Componente | Tecnología | Motivo |
|---|---|---|
| Lenguaje | Python 3.10 (CI y Docker) | El curso trabaja en Python y el equipo ya lo domina |
| API REST | FastAPI + Uvicorn | Genera OpenAPI y Swagger UI automáticamente; valida con Pydantic |
| Validación de entrada | Pydantic | Restricciones declarativas (`gt=0`, patrón de 10 dígitos) |
| Persistencia | SQLAlchemy + SQLite | ORM estándar; SQLite no requiere servidor y se puede usar en memoria para pruebas |
| Pruebas | pytest + pytest-cov + httpx | Fixtures, parametrización con los CSV oficiales y medición de cobertura |
| CI | GitHub Actions (`.github/workflows/ci.yaml`) | Corre las pruebas en cada push y pull request a `main` |
| Contenedores | Dockerfile (`python:3.10-slim`) + `docker-compose.yml` | Mismo entorno en cualquier máquina |

Las decisiones de mayor peso están registradas como ADR en [adr/](adr/).

## Configuración (12-Factor)

La configuración se separa del código con variables de entorno. `.env.example` documenta las variables sin valores secretos:

| Variable | Uso | Valor por defecto |
|---|---|---|
| `APP_ENV` | Entorno de ejecución (`development` / `production`) | `development` |
| `PORT` | Puerto del servidor | `8000` |
| `DATABASE_URL` | Cadena de conexión que lee `src/infrastructure/database.py` | `sqlite:///./cargobox.db` |

## Manejo de errores

Cada regla rota tiene una excepción de dominio con nombre del negocio, y la API la traduce a un código HTTP consistente:

| Excepción | Código HTTP | Ejemplo |
|---|---|---|
| Validación Pydantic | 422 | Teléfono con 9 dígitos |
| `LimiteFisicoExcedido` | 422 | Paquete de 35 kg |
| `LimiteReintentosExcedido` | 422 | Tercer intento de entrega |
| `SinEvidenciaPOD` | 422 | Entregar con evidencia vacía |
| `InvalidStateTransition` | 409 | Clasificar un paquete que ya está en tránsito |
| Guía inexistente (`ValueError`) | 404 | Consultar `CBX-NOEXISTE` |
| Incidencia no reconocida | 400 | `tipo_incidencia = "robo"` |

## Calidad

- **Suite:** 140 pruebas en PASSED (`tests/test_cargobox.py`, `tests/test_casos_csv.py`, `tests/test_repositorio.py`).
- **Cobertura total de `src/`:** 91% (dominio 94%, servicio 91%), por encima del mínimo de 80%.
- **Datos oficiales:** `tests/datos/` contiene los CSV de la FIME (actores, catálogo, operaciones, casos y transiciones de prueba).
- **CI:** el workflow falla si la cobertura de `src/application` baja de 80% (`--cov-fail-under=80`).

## Deuda técnica conocida

Se registra para que el equipo la atienda y para responder con transparencia en la defensa:

1. **Dos versiones de la máquina de estados.** El agregado `Paquete` usa `EN_PUNTO_RECOLECCION` y `DEVUELTO`, mientras que `CargoBoxService` guarda `PUNTO_RECOLECCION` y `DEVUELTO_CANCELADO` directamente en `PaqueteModel`. Lo ideal es que el servicio reconstruya un `Paquete` desde el modelo, invoque su método y persista el resultado, para que exista una sola fuente de verdad.
2. **Specification como clases.** Las reglas ya son predicados aislados, pero falta extraerlas a clases `Specification` componibles (`and`, `or`, `not`).
3. **Pruebas de la API.** `tests/test_api.py` está vacío; conviene agregar pruebas con `TestClient` para los códigos 404, 409 y 422.
4. **Repositorio con interfaz.** `PaqueteRepositoryMemoria` no comparte una interfaz abstracta con la persistencia SQL; definir `PaqueteRepository` (ABC) permitiría intercambiarlas.
5. **Docker Compose.** El archivo levanta solo la API; falta agregar los servicios de base de datos y de pruebas que pide la rúbrica, y quitar la clave `container_port`, que no es válida en Compose.
6. **CI.** Medir la cobertura de todo `src/` en lugar de solo `src/application`.
