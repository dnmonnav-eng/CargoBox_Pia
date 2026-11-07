# ADR-003: Límite de dos intentos de entrega y evidencia POD obligatoria

- **Estado:** Aceptada
- **Fecha:** 2026-11-05
- **Equipo:** Equipo 14 — CargoBox

## Contexto

Los clientes reclamaban paquetes que el sistema mostraba como entregados sin prueba, y los repartidores hacían visitas repetidas a domicilios donde nadie recibía. El BRD define que una entrega no puede cerrarse sin evidencia (RN-06) y que después de dos visitas fallidas el paquete se resguarda en un punto de recolección (sección 7.2).

## Decisión

- **Intentos:** `registrar_intento_fallido()` incrementa `intentos_entrega`. En el segundo intento el estado pasa a punto de recolección, y un tercero lanza `LimiteReintentosExcedido` (HTTP 422). Si el paquete vuelve a reparto tras corregir la dirección, el contador se reinicia a 0.
- **POD:** `completar_entrega(evidencia)` exige que la evidencia no sea nula ni solo espacios; si no, lanza `SinEvidenciaPOD` (HTTP 422). La evidencia se guarda sin espacios sobrantes y genera el evento `PaqueteEntregado`.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Intentos ilimitados controlados por el repartidor | Es justo el problema que reportaba la operación |
| Tres intentos | Aumenta el costo de ruta; el BRD fija dos |
| POD opcional con advertencia | No resuelve las disputas: una advertencia no es una prueba |

## Consecuencias

- **Positivas:** cada entrega tiene una evidencia consultable; se reducen visitas inútiles; ambas reglas tienen pruebas de éxito, error y límite.
- **Negativas:** el sistema valida que exista una evidencia, no que la fotografía o la firma sean auténticas. Validar el archivo queda fuera del alcance actual.
