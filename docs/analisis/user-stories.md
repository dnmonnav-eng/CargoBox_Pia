# User Stories y criterios de aceptación (Gherkin)

Las 17 historias de usuario son las de la Unidad 2 (`docs/analisis/User_Stories_Equipo14_CLNEG.pdf`). Para el PIA les agregamos escenarios en Gherkin derivados de sus criterios de aceptación y la columna de implementación, que liga cada historia con el código.

| ID | Historia | Implementación | Estado |
|---|---|---|---|
| US-01 | Registrar paquete | POST /paquetes/ · registrar_envio() | Implementada |
| US-02 | Generar guía | GuiaUnica · guía generada en POST /paquetes/ | Implementada |
| US-03 | Registrar recepción | Paquete.__post_init__ · evento PaqueteRecibido | Implementada |
| US-04 | Clasificar paquete | POST /paquetes/{guia}/clasificar · clasificar() | Implementada |
| US-05 | Registrar salida hacia tránsito | POST /paquetes/{guia}/despachar-transito · despachar_a_transito() | Implementada |
| US-06 | Registrar llegada al centro destino | POST /paquetes/{guia}/centro-destino · llegar_a_centro_destino() | Implementada |
| US-07 | Registrar paquete en reparto | POST /paquetes/{guia}/iniciar-reparto · iniciar_reparto() | Implementada |
| US-08 | Consultar rastreo | obtener_paquete() (servicio); falta GET /paquetes/{guia} | Parcial |
| US-09 | Registrar entrega | POST /paquetes/{guia}/entregar · completar_entrega() | Implementada |
| US-10 | Registrar evidencia de entrega | evidencia_pod · SinEvidenciaPOD (RN-06) | Implementada |
| US-11 | Registrar destinatario ausente | POST /paquetes/{guia}/intentos-fallidos · registrar_intento_fallido() | Implementada |
| US-12 | Registrar segundo intento | POST /paquetes/{guia}/intentos-fallidos · LimiteReintentosExcedido | Implementada |
| US-13 | Registrar dirección incorrecta | POST /paquetes/{guia}/incidencias · procesar_incidencia() | Implementada |
| US-14 | Registrar paquete dañado | POST /paquetes/{guia}/incidencias · procesar_incidencia() | Implementada |
| US-15 | Consultar incidencias | Estado actual en la respuesta de /incidencias; falta historial de incidencias | Parcial |
| US-16 | Escalar incidencia | Diseñada en U3 (IncidenciaService.escalarIncidencia) | Pendiente |
| US-17 | Detectar falta de actualización | Paquete.verificar_tiempo_transito() | Implementada |

## Relación con las necesidades del BRD

| Necesidad | User Stories |
|---|---|
| NB-01 | US-03, US-04, US-05, US-06, US-07, US-08, US-09 |
| NB-02 | US-01, US-05, US-08 |
| NB-03 | US-03, US-04, US-05, US-06, US-07, US-09 |
| NB-04 | US-09, US-10 |
| NB-05 | US-11, US-12, US-13, US-14, US-16, US-17 |
| NB-06 | US-08, US-15, US-16, US-17 |
| NB-07 | US-08, US-10, US-15 |
| NB-08 | US-11, US-12, US-13, US-14, US-16, US-17 |

## Historias y escenarios

### US-01 · Registrar paquete

Como empleado de sucursal, quiero registrar un nuevo paquete con sus datos, peso y dimensiones, para iniciar correctamente su proceso de envío.

**Criterios de aceptación (U2):**
- El empleado puede capturar los datos requeridos del paquete.
- El peso y las dimensiones quedan registrados.
- El paquete queda asociado a una guía.

```gherkin
# language: es
Característica: Registrar paquete

  Escenario: US-01
    Dado un paquete de 15 kg y 1.0 × 0.5 × 0.5 m con teléfono 8112345678
    Cuando el empleado lo registra en sucursal
    Entonces el peso y las dimensiones quedan guardados
    Y el paquete queda asociado a una guía
```

### US-02 · Generar guía

Como empleado de sucursal, quiero generar una guía única para cada paquete, para identificarlo durante todo su recorrido.

**Criterios de aceptación (U2):**
- Cada paquete obtiene una guía.
- La guía identifica de manera única al paquete.
- La guía puede utilizarse para consultar el envío.

```gherkin
# language: es
Característica: Generar guía

  Escenario: US-02
    Dado un paquete válido
    Cuando se registra
    Entonces el sistema genera una guía con formato CBX-XXXXXXXX
    Y ningún otro paquete tiene esa guía
```

### US-03 · Registrar recepción

Como empleado de sucursal, quiero registrar que un paquete fue recibido, para iniciar formalmente su trazabilidad.

**Criterios de aceptación (U2):**
- El paquete queda registrado como recibido.
- Se genera un evento de rastreo.
- El evento queda asociado a la guía.

```gherkin
# language: es
Característica: Registrar recepción

  Escenario: US-03
    Dado un paquete recién registrado
    Cuando se crea en el sistema
    Entonces su estado es RECIBIDO
    Y se genera el evento PaqueteRecibido con su guía
```

### US-04 · Clasificar paquete

Como empleado del centro de distribución, quiero registrar la clasificación de un paquete, para dirigirlo hacia su siguiente destino.

**Criterios de aceptación (U2):**
- El paquete puede identificarse mediante su guía.
- Se registra la clasificación.
- El estado del paquete cambia a clasificado.

```gherkin
# language: es
Característica: Clasificar paquete

  Escenario: US-04
    Dado un paquete RECIBIDO
    Cuando el empleado lo clasifica usando su guía
    Entonces su estado cambia a CLASIFICADO
```

### US-05 · Registrar salida hacia tránsito

Como empleado del centro de distribución, quiero registrar que un paquete inicia su traslado, para mantener actualizado su recorrido.

**Criterios de aceptación (U2):**
- Se registra el movimiento.
- El paquete cambia al estado en tránsito.
- El movimiento aparece en el historial de rastreo.

```gherkin
# language: es
Característica: Registrar salida hacia tránsito

  Escenario: US-05
    Dado un paquete CLASIFICADO
    Cuando el empleado registra su salida
    Entonces su estado cambia a EN_TRANSITO
```

### US-06 · Registrar llegada al centro destino

Como empleado del centro de distribución, quiero registrar la llegada del paquete al centro destino, para mantener actualizada su ubicación dentro del proceso.

**Criterios de aceptación (U2):**
- El paquete queda asociado al centro destino.
- Se genera un evento de rastreo.
- El estado cambia a centro destino.

```gherkin
# language: es
Característica: Registrar llegada al centro destino

  Escenario: US-06
    Dado un paquete EN_TRANSITO
    Cuando el empleado registra su llegada
    Entonces su estado cambia a CENTRO_DESTINO
```

### US-07 · Registrar paquete en reparto

Como repartidor, quiero registrar que recibí un paquete para realizar su entrega, para indicar que se encuentra en proceso de reparto.

**Criterios de aceptación (U2):**
- El paquete queda asociado al proceso de reparto.
- Se registra el movimiento.
- El estado cambia a en reparto.

```gherkin
# language: es
Característica: Registrar paquete en reparto

  Escenario: US-07
    Dado un paquete en CENTRO_DESTINO
    Cuando el repartidor lo carga a su unidad
    Entonces su estado cambia a EN_REPARTO
    Y sus intentos de entrega quedan en 0
```

### US-08 · Consultar rastreo

Como remitente, quiero consultar el estado de mi paquete mediante su guía, para conocer el avance de mi envío.

**Criterios de aceptación (U2):**
- El usuario puede introducir la guía.
- El sistema muestra el estado actual.
- El sistema muestra los movimientos registrados.

```gherkin
# language: es
Característica: Consultar rastreo

  Escenario: US-08
    Dado un paquete registrado con guía CBX-1A2B3C4D
    Cuando el remitente consulta esa guía
    Entonces el sistema muestra su estado actual
```

### US-09 · Registrar entrega

Como repartidor, quiero registrar el resultado de una entrega, para actualizar el estado final del paquete.

**Criterios de aceptación (U2):**
- El repartidor puede indicar que la entrega fue realizada.
- Se genera un evento de rastreo.
- El paquete cambia a entregado cuando corresponde.

```gherkin
# language: es
Característica: Registrar entrega

  Escenario: US-09
    Dado un paquete EN_REPARTO
    Cuando el repartidor registra la entrega con evidencia
    Entonces su estado cambia a ENTREGADO
    Y se genera el evento PaqueteEntregado
```

### US-10 · Registrar evidencia de entrega

Como repartidor, quiero registrar la evidencia de recepción del paquete, para demostrar que la entrega fue realizada.

**Criterios de aceptación (U2):**
- La evidencia queda asociada a la guía.
- La evidencia puede ser consultada posteriormente.
- La entrega queda relacionada con su evidencia.

```gherkin
# language: es
Característica: Registrar evidencia de entrega

  Escenario: US-10
    Dado un paquete EN_REPARTO
    Cuando el repartidor intenta entregarlo con evidencia vacía o solo espacios
    Entonces el sistema responde 422
    Y el paquete no se marca como entregado
```

### US-11 · Registrar destinatario ausente

Como repartidor, quiero registrar cuando el destinatario está ausente, para dejar constancia de que la entrega no pudo completarse.

**Criterios de aceptación (U2):**
- El intento de entrega queda registrado.
- El sistema conserva el evento asociado al paquete.
- El paquete no se marca como entregado.

```gherkin
# language: es
Característica: Registrar destinatario ausente

  Escenario: US-11
    Dado un paquete EN_REPARTO sin intentos
    Cuando el repartidor registra que el destinatario está ausente
    Entonces queda registrado el intento 1 de 2
    Y el paquete no se marca como entregado
```

### US-12 · Registrar segundo intento

Como repartidor, quiero registrar un segundo intento de entrega, para mantener el historial completo de los intentos realizados.

**Criterios de aceptación (U2):**
- El segundo intento queda registrado.
- El evento se relaciona con la guía.
- El historial muestra los intentos realizados.

```gherkin
# language: es
Característica: Registrar segundo intento

  Escenario: US-12
    Dado un paquete con 1 intento fallido
    Cuando el repartidor registra el segundo intento fallido
    Entonces intentos_entrega queda en 2
    Y el paquete pasa a resguardo en punto de recolección
    Y un tercer intento responde 422
```

### US-13 · Registrar dirección incorrecta

Como repartidor, quiero registrar una dirección incorrecta, para informar que existe una incidencia que impide continuar con la entrega.

**Criterios de aceptación (U2):**
- La incidencia queda asociada al paquete.
- Se registra el momento del evento.
- El paquete no se marca como entregado.

```gherkin
# language: es
Característica: Registrar dirección incorrecta

  Escenario: US-13
    Dado un paquete EN_REPARTO
    Cuando el repartidor registra la incidencia direccion_incorrecta
    Entonces el paquete regresa a CENTRO_DESTINO
    Y sus intentos se reinician
    Y la respuesta incluye el teléfono del cliente para soporte
```

### US-14 · Registrar paquete dañado

Como empleado de centro de distribución, quiero registrar que un paquete está dañado, para que la incidencia pueda ser identificada y atendida.

**Criterios de aceptación (U2):**
- Se registra la incidencia.
- La incidencia queda asociada a la guía.
- La información puede ser consultada por atención al cliente.

```gherkin
# language: es
Característica: Registrar paquete dañado

  Escenario: US-14
    Dado un paquete en ruta
    Cuando se registra la incidencia paquete_danado
    Entonces el paquete regresa a CENTRO_DESTINO para valoración del supervisor de calidad
```

### US-15 · Consultar incidencias

Como agente de atención al cliente, quiero consultar las incidencias asociadas a un paquete, para proporcionar información al cliente y dar seguimiento al problema.

**Criterios de aceptación (U2):**
- El agente puede buscar el paquete mediante su guía.
- Puede consultar las incidencias registradas.
- Puede consultar el historial relacionado con la incidencia.

```gherkin
# language: es
Característica: Consultar incidencias

  Escenario: US-15
    Dado un paquete con una incidencia registrada
    Cuando el agente busca su guía
    Entonces el sistema muestra el estado resultante de la incidencia
```

### US-16 · Escalar incidencia

Como agente de atención al cliente, quiero escalar una incidencia que no pueda resolverse directamente, para que sea atendida por el responsable correspondiente.

**Criterios de aceptación (U2):**
- La incidencia puede identificarse como pendiente de atención.
- El escalamiento queda registrado.
- Se puede consultar el estado de la incidencia.

```gherkin
# language: es
Característica: Escalar incidencia

  Escenario: US-16
    Dado una incidencia que no se resolvió
    Cuando el agente la escala
    Entonces queda registrada como escalada con su responsable
```

### US-17 · Detectar falta de actualización

Como agente de atención al cliente, quiero identificar paquetes cuyo rastreo no se ha actualizado durante un periodo determinado, para detectar posibles problemas en el proceso de envío.

**Criterios de aceptación (U2):**
- El sistema identifica paquetes sin actualización.
- El paquete puede ser localizado mediante su guía.
- El caso puede ser revisado por atención al cliente.

```gherkin
# language: es
Característica: Detectar falta de actualización

  Escenario: US-17
    Dado un paquete EN_TRANSITO
    Cuando pasan más de 24 horas sin movimiento
    Entonces el paquete se declara PERDIDO
    Y se genera el evento PerdidaDeclarada
```
