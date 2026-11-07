# Diagramas UML y de arquitectura

Todos los diagramas corresponden a clases, métodos y endpoints que existen en `src/`.

## 1. Diagrama de componentes (capas)

```mermaid
flowchart TB
    subgraph API["src/api — Presentación"]
        A1["api.py<br/>FastAPI app<br/>RegistroPaqueteRequest<br/>EntregaRequest<br/>IncidenciaRequest"]
    end
    subgraph APP["src/application — Casos de uso"]
        S1["service.py<br/>CargoBoxService<br/>validar_transicion()"]
    end
    subgraph DOM["src/domain — Núcleo de negocio"]
        D1["Paquete · GuiaUnica<br/>EstadoPaquete<br/>Eventos de dominio<br/>Excepciones de dominio"]
    end
    subgraph INF["src/infrastructure — Detalles técnicos"]
        I1["database.py<br/>engine · SessionLocal · get_db"]
        I2["models.py<br/>PaqueteModel"]
        I3["repository.py<br/>PaqueteRepositoryMemoria"]
    end
    A1 -->|"Depends(get_db)"| I1
    A1 --> S1
    S1 --> D1
    S1 --> I2
    I2 --> I1
    I3 -.-> D1
    I1 --> DB[("SQLite")]
```

## 2. Diagrama de clases de aplicación e infraestructura

```mermaid
classDiagram
    class CargoBoxService {
        +registrar_envio(db, codigo_guia, peso_kg, largo_m, ancho_m, alto_m, telefono_cliente) PaqueteModel
        +obtener_paquete(db, guia) PaqueteModel
        +avanzar_estado(db, guia, nuevo_estado) PaqueteModel
        +registrar_intento_entrega(db, guia) PaqueteModel
        +procesar_incidencia(db, guia, tipo_incidencia) PaqueteModel
        +completar_entrega_paquete(db, guia, evidencia) PaqueteModel
    }
    class PaqueteModel {
        <<SQLAlchemy>>
        +str guia PK
        +float peso_kg
        +float largo_m
        +float ancho_m
        +float alto_m
        +str telefono_cliente
        +str estado
        +int intentos_entrega
        +str evidencia_pod
    }
    class PaqueteRepositoryMemoria {
        -dict _almacen
        +guardar(paquete)
        +obtener_por_guia(codigo)
        +listar_todos()
    }
    class RegistroPaqueteRequest {
        <<Pydantic>>
        +float peso_kg
        +float largo_m
        +float ancho_m
        +float alto_m
        +str telefono_cliente
    }
    class EntregaRequest {
        <<Pydantic>>
        +str evidencia
    }
    class IncidenciaRequest {
        <<Pydantic>>
        +str tipo_incidencia
    }
    class Paquete {
        <<AggregateRoot>>
    }
    CargoBoxService ..> PaqueteModel : persiste
    CargoBoxService ..> EstadoPaquete : usa
    CargoBoxService ..> CargoBoxDomainError : lanza
    PaqueteRepositoryMemoria o-- Paquete
    RegistroPaqueteRequest ..> CargoBoxService : entrada de
    EntregaRequest ..> CargoBoxService : entrada de
    IncidenciaRequest ..> CargoBoxService : entrada de
```

## 3. Máquina de estados del paquete

```mermaid
stateDiagram-v2
    [*] --> RECIBIDO : registrar (≤30 kg, ≤1.5 m)
    RECIBIDO --> CLASIFICADO : clasificar()
    CLASIFICADO --> EN_TRANSITO : despachar_a_transito()
    EN_TRANSITO --> CENTRO_DESTINO : llegar_a_centro_destino()
    EN_TRANSITO --> PERDIDO : más de 24 h sin movimiento
    CENTRO_DESTINO --> EN_REPARTO : iniciar_reparto()
    EN_REPARTO --> EN_REPARTO : 1.er intento fallido
    EN_REPARTO --> EN_PUNTO_RECOLECCION : 2.º intento fallido
    EN_REPARTO --> ENTREGADO : completar_entrega(POD)
    EN_REPARTO --> CENTRO_DESTINO : incidencia (dirección incorrecta / dañado)
    CENTRO_DESTINO --> EN_PUNTO_RECOLECCION : enviar_a_punto_recoleccion()
    EN_PUNTO_RECOLECCION --> DEVUELTO : iniciar_devolucion()
    EN_REPARTO --> DEVUELTO : iniciar_devolucion() / rechazo
    CENTRO_DESTINO --> DEVUELTO : iniciar_devolucion()
    ENTREGADO --> [*]
    DEVUELTO --> [*]
    PERDIDO --> [*]
    note right of ENTREGADO
        No puede declararse PERDIDO
        y requiere evidencia POD
    end note
```

| Desde | Acción | Hacia | Si no se cumple |
|---|---|---|---|
| — | Registrar con peso ≤ 30 kg y dimensión ≤ 1.5 m | RECIBIDO | `LimiteFisicoExcedido` (HTTP 422) |
| RECIBIDO | `clasificar()` | CLASIFICADO | `InvalidStateTransition` (HTTP 409) |
| CLASIFICADO | `despachar_a_transito()` | EN_TRANSITO | `InvalidStateTransition` |
| EN_TRANSITO | `llegar_a_centro_destino()` | CENTRO_DESTINO | `InvalidStateTransition` |
| CENTRO_DESTINO | `iniciar_reparto()` | EN_REPARTO | `InvalidStateTransition` |
| EN_REPARTO | 1.er intento fallido | EN_REPARTO (intentos = 1) | — |
| EN_REPARTO | 2.º intento fallido | EN_PUNTO_RECOLECCION | — |
| EN_PUNTO_RECOLECCION | 3.er intento | — | `LimiteReintentosExcedido` (HTTP 422) |
| EN_REPARTO | `completar_entrega(POD)` | ENTREGADO | `SinEvidenciaPOD` (HTTP 422) |
| EN_TRANSITO | Más de 24 h sin movimiento | PERDIDO | — |

## 4. Secuencia: registrar un paquete

```mermaid
sequenceDiagram
    actor E as Empleado de sucursal
    participant API as POST /paquetes/
    participant P as Pydantic
    participant S as CargoBoxService
    participant DB as SQLite (SQLAlchemy)
    E->>API: peso, largo, ancho, alto, teléfono
    API->>P: validar RegistroPaqueteRequest
    alt teléfono sin 10 dígitos o medida ≤ 0
        P-->>E: 422 Unprocessable Entity
    end
    API->>API: generar guía CBX-XXXXXXXX
    API->>S: registrar_envio(...)
    alt peso > 30 kg o lado > 1.5 m
        S-->>API: LimiteFisicoExcedido
        API-->>E: 422 "excede los límites permitidos"
    else datos válidos
        S->>DB: add + commit (estado RECIBIDO)
        DB-->>S: PaqueteModel
        S-->>API: paquete
        API-->>E: 200 "guía única generada: CBX-..."
    end
```

## 5. Secuencia: entrega con evidencia POD

```mermaid
sequenceDiagram
    actor R as Repartidor
    participant API as POST /paquetes/{guia}/entregar
    participant S as CargoBoxService
    participant DB as SQLite
    R->>API: evidencia (firma o foto)
    API->>S: completar_entrega_paquete(guia, evidencia)
    alt evidencia vacía o solo espacios
        S-->>API: SinEvidenciaPOD
        API-->>R: 422 "sin la evidencia requerida"
    else evidencia válida
        S->>DB: buscar paquete por guía
        alt guía inexistente
            S-->>API: ValueError
            API-->>R: 404
        end
        S->>S: validar_transicion(estado, ENTREGADO)
        S->>DB: estado = ENTREGADO, evidencia_pod, commit
        API-->>R: 200 "¡Entrega exitosa!"
    end
```

## 6. Secuencia: intentos fallidos

```mermaid
sequenceDiagram
    actor R as Repartidor
    participant API as POST /paquetes/{guia}/intentos-fallidos
    participant S as CargoBoxService
    participant DB as SQLite
    R->>API: registrar visita fallida
    API->>S: registrar_intento_entrega(guia)
    alt intentos ya en 2
        S->>DB: estado = PUNTO_RECOLECCION
        S-->>API: LimiteReintentosExcedido
        API-->>R: 422 "ya se encuentra en resguardo"
    else intentos < 2
        S->>DB: intentos += 1
        opt intentos llega a 2
            S->>DB: estado = PUNTO_RECOLECCION
        end
        API-->>R: 200 "Intento n de 2"
    end
```

## 7. Despliegue

```mermaid
flowchart LR
    Dev[Desarrollador] -->|git push| GH[GitHub]
    GH -->|on: push / pull_request| CI[GitHub Actions<br/>Python 3.10<br/>pytest + cobertura ≥ 80%]
    GH --> IMG[Dockerfile<br/>python:3.10-slim]
    IMG --> C[Contenedor cargobox-api<br/>uvicorn :8000]
    C --> V[(cargobox.db)]
    U[Usuario] -->|http://host:8000/docs| C
```
