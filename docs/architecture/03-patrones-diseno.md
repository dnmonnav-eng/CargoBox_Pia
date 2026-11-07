# Patrones de diseño

Cada patrón se eligió por un problema concreto de CargoBox. La tabla resume dónde está en el código y qué problema resuelve; abajo se justifica cada uno.

| Patrón | Dónde | Problema que resuelve |
|---|---|---|
| Arquitectura en capas (Clean Architecture) | `src/api`, `src/application`, `src/domain`, `src/infrastructure` | Que las reglas del negocio no dependan de FastAPI ni de la base de datos |
| Aggregate Root | `Paquete` | Que nadie modifique el estado del paquete saltándose sus reglas |
| Value Object | `GuiaUnica` | Que la guía no cambie durante el recorrido |
| State Machine | Métodos de `Paquete` y `validar_transicion()` | Que el paquete solo avance por transiciones permitidas |
| Specification | Reglas de límites físicos y de evidencia POD | Expresar cada regla como un predicado que se puede probar por separado |
| Domain Events | `PaqueteRecibido`, `PaqueteEntregado`, `PaqueteDevuelto`, `PerdidaDeclarada` | Dejar constancia de hechos del negocio para el rastreo (RN-05) |
| Service Layer | `CargoBoxService` | Concentrar los casos de uso en un solo lugar |
| Repository | `PaqueteRepositoryMemoria`, `PaqueteModel` + sesión | Aislar cómo se guardan y recuperan los paquetes |
| Dependency Injection | `Depends(get_db)` en FastAPI; `db` como parámetro del servicio | Cambiar la base real por una en memoria en las pruebas |
| DTO | `RegistroPaqueteRequest`, `EntregaRequest`, `IncidenciaRequest` | Validar la entrada HTTP antes de que llegue al negocio |

## Arquitectura en capas

CargoBox cambia de reglas con frecuencia (límites de peso, número de intentos, tipos de incidencia), pero el framework web y la base de datos no deberían cambiar por eso. Separar en capas permite modificar una regla en `domain/` o `application/` sin tocar los endpoints, y probar el dominio sin levantar un servidor. Ver [ADR-001](adr/ADR-001-arquitectura-en-capas.md).

## Aggregate Root: `Paquete`

El paquete es la unidad que el negocio rastrea; todos los cambios relevantes (estado, intentos, evidencia) le pertenecen. Al hacerlo raíz del agregado, la única forma de cambiar su estado es por sus métodos, y cada método verifica su precondición. Ver [ADR-002](adr/ADR-002-agregado-paquete-ddd.md).

## Value Object: `GuiaUnica`

La guía es la referencia que el cliente usa para rastrear y no debe cambiar nunca. Al ser un `dataclass(frozen=True)`, cualquier intento de modificarla lanza un error, y su validación (`__post_init__`) impide crear una guía vacía.

## State Machine

El BRD exige una progresión secuencial (RN-03) con un catálogo cerrado de estados (RN-04). Cada transición es un método con una precondición explícita: por ejemplo, `iniciar_reparto()` solo funciona desde `CENTRO_DESTINO`. Los saltos inválidos lanzan `InvalidStateTransition`, que la API traduce a HTTP 409. En la capa de aplicación, `validar_transicion()` aplica la misma secuencia sobre los registros persistidos. El diagrama completo está en [02-diagramas-uml.md](02-diagramas-uml.md#3-máquina-de-estados-del-paquete).

## Specification

Las reglas de aceptación del negocio se escriben como predicados independientes que responden "sí o no" sobre un paquete:

- **Límite físico:** `0 < peso_kg ≤ 30` y `0 < dimensión_máxima ≤ 1.5`.
- **Evidencia válida:** `evidencia` no es nula y `evidencia.strip()` no está vacía.
- **Puede reintentar:** `intentos_entrega < 2` y estado `EN_REPARTO`.

Hoy estos predicados viven dentro de `Paquete.__post_init__`, `Paquete.completar_entrega()`, `Paquete.registrar_intento_fallido()` y `CargoBoxService.registrar_envio()`. Separarlos en clases con `is_satisfied_by()` y operadores `and/or/not` es el siguiente paso registrado en [05-decisiones-tecnicas.md](05-decisiones-tecnicas.md#deuda-técnica-conocida).

## Domain Events

RN-05 pide que cada movimiento produzca información de rastreo. En lugar de que el dominio escriba en una bitácora, el agregado registra eventos (`PaqueteRecibido`, `PaqueteEntregado`, etc.) y la capa externa los extrae con `pull_events()`. Esto mantiene al dominio sin dependencias y deja la puerta abierta a notificar al cliente o a soporte.

## Service Layer: `CargoBoxService`

La API no contiene reglas: cada endpoint llama a un método del servicio y traduce las excepciones a códigos HTTP. Así, el mismo caso de uso se puede ejecutar desde una prueba o desde otro canal sin duplicar lógica.

## Repository

`PaqueteRepositoryMemoria` ofrece `guardar`, `obtener_por_guia` y `listar_todos` sobre un diccionario, útil para pruebas del dominio. La persistencia real usa `PaqueteModel` con una sesión de SQLAlchemy. Ver [ADR-004](adr/ADR-004-persistencia-sqlalchemy-sqlite.md).

## Dependency Injection

FastAPI inyecta la sesión con `Depends(get_db)`, y el servicio recibe `db` como parámetro en vez de crearla. Por eso las pruebas usan una base SQLite en memoria (`sqlite:///:memory:`) sin cambiar el código de producción.

## DTO

Los modelos Pydantic validan la forma de los datos en la frontera: medidas mayores que 0 (`gt=0`) y teléfono de exactamente 10 dígitos (`^\d{10}$`). Las reglas de negocio (30 kg, 1.5 m) se validan después, en el servicio y en el dominio.
