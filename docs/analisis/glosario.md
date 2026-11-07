# Glosario de dominio

Glosario de la Unidad 2 (`docs/analisis/Glosario_Dominio_Equipo14_CLNEG.pdf`) con una columna que indica dónde aparece cada término en el código.

| Término | Definición | En el código |
|---|---|---|
| Alerta automática de retraso | Notificación que se activa cuando pasan más de 8 horas (Express) o 24 horas (Estándar) sin actualización entre eventos de rastreo. | verificar_tiempo_transito() (24 h) |
| Atención al cliente / Soporte técnico | Rol que resuelve incidencias, corrige datos de contacto en menos de 4 horas hábiles, reprograma entregas y gestiona compensaciones. | Mensaje de /incidencias con teléfono |
| Centro de distribución (CD) | Instalación que clasifica paquetes, los despacha en tránsito, procesa reintentos y evalúa daños con el supervisor de calidad. | CLASIFICADO, EN_TRANSITO, CENTRO_DESTINO |
| Compensación por pérdida | Pago equivalente al valor declarado (hasta $15,000 MXN sin seguro) cuando un envío pasa 72 horas sin actualización y sin explicación. | Fuera de alcance |
| Declaración de valor | Monto que el remitente asigna al contenido al momento de la admisión; base para compensaciones. | Fuera de alcance |
| Destinatario | Persona física o moral designada como receptor final en la dirección de entrega. | telefono_cliente |
| Devolución a origen | Retorno del paquete al remitente tras agotar intentos, vencer el resguardo o registrarse un rechazo. | iniciar_devolucion(), DEVUELTO |
| Empleado de sucursal | Rol que recibe el paquete, verifica límites físicos (30 kg y 1.5 m por lado), cobra la tarifa y genera la guía única. | registrar_envio() |
| Empaque y embalaje | Contenedor físico que protege el contenido y debe cumplir los límites de peso y dimensiones. | LimiteFisicoExcedido |
| Evidencia de recepción (POD) | Firma digital del destinatario o fotografía del paquete entregado con el nombre del receptor. | evidencia_pod, SinEvidenciaPOD |
| Guía única | Identificador alfanumérico exclusivo asignado en el registro para seguir todo el trayecto. | GuiaUnica, CBX-XXXXXXXX |
| Incidencia | Situación no planificada que interrumpe la entrega: dirección incorrecta, destinatario ausente, paquete dañado, pérdida o rechazo. | procesar_incidencia() |
| Nivel de servicio (SLA) | Tiempos garantizados: Mismo Día, Express (24-48 h) y Estándar (3-5 días hábiles). | Pendiente |
| Punto de recolección | Localidad alternativa (OXXO o sucursal) donde se resguarda el paquete tras el segundo intento fallido. | EN_PUNTO_RECOLECCION |
| Rastreo en tiempo real | Seguimiento digital de los cambios de estado del paquete mediante su guía. | Eventos de dominio, obtener_paquete() |
| Rechazo de paquete | El destinatario no acepta el envío; el paquete regresa al CD y se notifica al remitente. | Incidencia rechazo |
| Remitente / Usuario | Cliente que entrega el paquete, declara su valor y autoriza reenvío o devolución. | — |
| Repartidor | Personal que ejecuta la entrega, reporta inconsistencias de dirección y registra la evidencia POD. | /intentos-fallidos, /entregar |
| Segundo intento de entrega | Nueva visita al día siguiente tras un primer intento fallido por destinatario ausente. | intentos_entrega ≤ 2 |
| Supervisor de calidad | Rol del CD que evalúa daños, autoriza reparación del embalaje y determina si el paquete se entrega o se clasifica como pérdida. | Incidencia paquete_danado |
