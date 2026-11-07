# Principios SOLID

| Principio | Cómo se aplica | Evidencia en el código |
|---|---|---|
| **S** — Responsabilidad única | Cada módulo tiene una sola razón para cambiar | `api.py` traduce HTTP, `service.py` coordina casos de uso, `domain/` guarda las reglas, `database.py` configura la conexión, `models.py` define la tabla |
| **O** — Abierto/cerrado | Se agregan casos nuevos extendiendo, no modificando | Nuevos errores de negocio heredan de `CargoBoxDomainError`; nuevos eventos heredan de `DomainEvent`; la API ya captura la clase base |
| **L** — Sustitución de Liskov | Las subclases funcionan donde se espera la clase base | Cualquier excepción de dominio puede capturarse como `CargoBoxDomainError`, y cualquier evento se trata como `DomainEvent` en `pull_events()` |
| **I** — Segregación de interfaces | Cada cliente recibe solo lo que necesita | Un DTO por operación (`RegistroPaqueteRequest`, `EntregaRequest`, `IncidenciaRequest`) en vez de un modelo con todos los campos |
| **D** — Inversión de dependencias | Lo de alto nivel no crea sus dependencias | El servicio recibe la sesión `db` por parámetro; FastAPI la inyecta con `Depends(get_db)`; las pruebas inyectan SQLite en memoria |

## S — Responsabilidad única

Si cambia un mensaje de respuesta, solo se toca `api.py`. Si cambia el límite de peso, solo se tocan el dominio y el servicio. Si se cambia SQLite por PostgreSQL, basta con la variable `DATABASE_URL` que lee `database.py`.

## O — Abierto/cerrado

En `api.py`, cada endpoint captura `CargoBoxDomainError` como respaldo. Si mañana se agrega, por ejemplo, `PaqueteRetenidoEnAduana(CargoBoxDomainError)`, la API ya responde con un error controlado sin que haya que modificar ese bloque.

## L — Sustitución de Liskov

`LimiteFisicoExcedido`, `LimiteReintentosExcedido`, `SinEvidenciaPOD` e `InvalidStateTransition` no alteran el comportamiento de `CargoBoxDomainError`: solo especializan el motivo. Por eso se pueden usar indistintamente en `except CargoBoxDomainError`.

## I — Segregación de interfaces

El repartidor que entrega solo envía `evidencia`; quien reporta una incidencia solo envía `tipo_incidencia`. Ningún cliente de la API está obligado a mandar campos que no usa.

## D — Inversión de dependencias

`CargoBoxService` no sabe qué base de datos hay detrás: trabaja con la sesión que le pasan. En `tests/test_cargobox.py` la fixture `db_session` crea un motor `sqlite:///:memory:` y se lo inyecta al servicio, mientras que en producción FastAPI inyecta la sesión de `cargobox.db`.
