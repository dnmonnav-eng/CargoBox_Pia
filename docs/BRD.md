# Business Requirements Document (BRD) - CargoBox
**Proyecto:** Sistema de Gestión Logística y Trazabilidad (CargoBox)  
**Equipo:** Equipo 14 | **Grupo:** 003  

---

## 1. Resumen de la Empresa
CargoBox es una empresa dedicada a la paquetería y mensajería con cobertura nacional, cuyo modelo de negocio consiste en cobrar por cada envío según las dimensiones, el peso, el destino y el nivel de servicio elegido, asignando a cada paquete una guía única que permite identificarlo a lo largo de todo el proceso operativo. El presente documento establece los requerimientos de negocio, funcionales y técnicos necesarios para la modernización y automatización de la trazabilidad logística mediante el desarrollo de una API REST robusta sustentada en Clean Architecture, Domain-Driven Design (DDD), un motor de Máquina de Estados (State Machine) y persistencia segura en SQLite.

---

## 2. Introducción y Oportunidad de Negocio
Actualmente, la operación física de CargoBox funciona mediante una recepción inicial en sucursal donde el paquete es pesado y medido para generar su guía, seguido de un tránsito a través de diversos centros de distribución hasta llegar a su destino final. Sin embargo, la empresa presenta problemas críticos relacionados con la visibilidad y el seguimiento de los envíos:
* Los clientes realizan constantes llamadas debido a la falta de actualizaciones en la información de rastreo.
* La información de los registros operativos se encuentra incompleta o dispersa.
* No existe un control automatizado estricto ante excepciones operativas como direcciones incorrectas, destinatarios ausentes, segundos intentos de entrega, paquetes dañados, pérdidas o rechazos.

**Oportunidad de Negocio:** Mejorar radicalmente la gestión y trazabilidad de los paquetes mediante un sistema digital centralizado que automatice los cambios de estado, valide las restricciones físicas de los envíos, gestione de forma inteligente las incidencias operativas y centralice las evidencias digitales de entrega (POD).

---

## 3. Actores y Stakeholders del Sistema

* **Remitente / Usuario:** Solicita el envío y proporciona la información detallada del paquete (peso, dimensiones tridimensionales) y el teléfono móvil de contacto del destinatario.
* **Empleado de Sucursal:** Recibe, pesa y mide el paquete en sucursal, ejecuta la validación de umbrales físicos, genera la Guía Única e inicia formalmente el ciclo logístico.
* **Centro de Distribución (Origen / Destino):** Responsable de clasificar los paquetes (`CLASIFICADO`), despacharlos en tránsito (`EN_TRANSITO`) y recibirlos en destino (`CENTRO_DESTINO`), además de fungir como base de reevaluación para incidencias de dirección o daños.
* **Repartidor:** Carga la unidad de reparto (`EN_REPARTO`), registra las visitas ausentes o intentos fallidos, y ejecuta la entrega exitosa capturando la evidencia digital requerida.
* **Destinatario:** Recibe el paquete en su domicilio, proporciona el teléfono de validación y otorga la evidencia de recepción (firma o fotografía).
* **Soporte y Atención al Cliente:** Consulta información centralizada del rastreo y gestiona el escalamiento de incidencias operativas para ofrecer respuestas oportunas en plazos menores a cuatro horas.

---

## 4. Alcance del Sistema (Scope)

### Alcance Incluido (In-Scope)
* **Registro de Envíos y Guía Única:** Captura obligatoria de peso, dimensiones independientes ($largo$, $ancho$, $alto$ en metros) y teléfono a 10 dígitos, generando un identificador único infalible (`CBX-XXXXXXXX`).
* **Máquina de Estados Secuencial:** Control estricto de la progresión logística (`RECIBIDO` ➔ `CLASIFICADO` ➔ `EN_TRANSITO` ➔ `CENTRO_DESTINO` ➔ `EN_REPARTO` ➔ `ENTREGADO`).
* **Gestión de Intentos y Resguardo:** Conteo automatizado de hasta 2 intentos fallidos de entrega, desencadenando la transferencia automática a resguardo en el `PUNTO_RECOLECCION` y reiniciando el ciclo si el paquete vuelve a ruta.
* **Manejo Avanzado de Incidencias:** Automatización de excepciones de negocio (Dirección incorrecta, Paquete dañado, Pérdida y Rechazo) con retrocesos controlados de estado y mensajes personalizados.
* **Evidencias de Entrega (POD):** Registro digital de comprobantes (Firma digital o Fotografía en puerta).
* **Exposición y Persistencia:** API REST documentada en Swagger UI (`/docs`) y persistencia estructurada localmente en SQLite (`cargobox.db`).

### Fuera de Alcance (Out-of-Scope)
* Cálculo dinámico de tarifas de envío y procesamiento de pagos bancarios en línea.
* Integración con geolocalización satelital en tiempo real mediante mapas GPS externos.
* Políticas de seguridad con esquemas de autenticación OAuth2 corporativos avanzados.

---

## 5. Lista de Necesidades de Negocio (Business Needs)

* **NB-01 Trazabilidad de Paquetes:** CargoBox necesita conocer con precisión el estado y el recorrido histórico de cada paquete durante todo su ciclo de envío.
* **NB-02 Identificación Única:** Cada paquete procesado debe poder identificarse de forma unívoca mediante una guía infalible.
* **NB-03 Actualización de Eventos:** Los movimientos operativos relevantes deben generar automáticamente información de rastreo auditable.
* **NB-04 Evidencia de Entrega:** El proceso de entrega final debe contar obligatoriamente con una evidencia digital que confirme la recepción por parte del destinatario.
* **NB-05 Gestión de Incidencias:** El negocio necesita registrar, rastrear y dar seguimiento formal a situaciones excepcionales que interrumpan el flujo normal de entrega.
* **NB-06 Atención al Cliente:** El personal de soporte debe poder consultar información centralizada y suficiente para responder solicitudes de los usuarios en tiempos óptimos.
* **NB-07 Información Centralizada:** Las evidencias, los datos de contacto y los eventos de envío deben mantenerse organizados en una base de datos persistente para evitar la dispersión.
* **NB-08 Seguimiento de Excepciones:** El sistema debe contemplar y resolver escenarios complejos como direcciones incorrectas, destinatarios ausentes, segundos intentos, daños físicos, pérdidas, rechazos y falta prolongada de actualización.

---

## 6. Reglas de Negocio (Business Rules)

* **RN-01 Generación de Identificador:** Cada paquete registrado debe contener obligatoriamente una guía única de seguimiento.
* **RN-02 Factores de Costo:** El precio del envío se determina en función de las dimensiones volumétricas, el peso, el destino y el nivel de servicio seleccionado.
* **RN-03 Progresión de Estados:** Un paquete cambia de estado de manera secuencial conforme avanza a través de la cadena logística.
* **RN-04 Catálogo de Estados Oficiales:** Los estados válidos reconocidos por el sistema son: `RECIBIDO`, `CLASIFICADO`, `EN_TRANSITO`, `CENTRO_DESTINO`, `EN_REPARTO` y `ENTREGADO` (más los estados de excepción).
* **RN-05 Auditoría de Movimientos:** Cada movimiento operativo ejecutado en la API debe producir información de rastreo persistente.
* **RN-06 Requisito de Cierre:** Ninguna entrega puede completarse sin la adjunción previa de una evidencia de recepción digital (POD).
* **RN-07 Tratamiento de Excepciones:** El sistema debe integrar mecanismos automatizados para absorber incidencias operativas y redirigir el flujo del paquete hacia áreas de soporte o devolución.

---

## 7. Anexo Técnico: Implementación y Arquitectura del Sistema

### 7.1 Arquitectura y Patrones de Diseño
* **Clean Architecture:** Separación estricta de responsabilidades en capas (`src/api`, `src/application`, `src/domain`, `src/infrastructure`), garantizando que la lógica de negocio permanezca aislada de frameworks externos o detalles de base de datos.
* **Domain-Driven Design (DDD):** Modelado del dominio centrado en entidades y excepciones de negocio puras (`LimiteFisicoExcedido`, `LimiteReintentosExcedido`, `SinEvidenciaPOD`, `InvalidStateTransition`).
* **Patrón Specification:** Validación encapsulada de reglas físicas y restricciones de transición en los servicios de aplicación.

### 7.2 Máquina de Estados (State Machine) y Control de Intentos
* El flujo valida estrictamente que no existan saltos arbitrarios entre etapas no consecutivas.
* **Control de Intentos Fallidos:** El repartidor cuenta con un límite estricto de 2 intentos. Al registrarse la segunda visita sin éxito, el estado cambia automáticamente a `PUNTO_RECOLECCION` (resguardo en sucursal). Si el paquete es devuelto al centro para corrección y vuelve a salir a reparto, los intentos se reinician a cero (`0`).

### 7.3 Validación de Límites Físicos
* El sistema valida mediante Pydantic y lógica de dominio que ningún paquete supere un peso mayor a 30 kg o que ninguna de sus dimensiones tridimensionales independientes (largo, ancho, alto) exceda 1.5 m. Su incumplimiento genera un rechazo inmediato HTTP 422.

### 7.4 Gestión Avanzada de Incidencias Operativas
* **Dirección Incorrecta (DI):** El paquete regresa al Centro de Distribución de Destino (`CENTRO_DESTINO`), permitiendo a soporte contactar al cliente a su teléfono móvil a 10 dígitos en un plazo menor a 4 horas para corregir datos y reprogramar.
* **Paquete Dañado:** El paquete retrocede a `CENTRO_DESTINO` para que el Supervisor de Calidad documente el reporte físico y evalúe el proceso de compensación.
* **Pérdida / Rechazo:** Se procesa la cancelación inmediata y el estado pasa a `DEVUELTO_CANCELADO`, finalizando el ciclo operativo con devoluciones o cargos por manejo.